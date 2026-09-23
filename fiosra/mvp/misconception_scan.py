"""Read a submitted assignment, find the cognitive traps it exhibits, and draft
an intervention the educator can send.

The pieces this joins up already existed separately: the traps and their
Socratic probe ladders live in Neo4j, the student's written work lives in
learning_document_blocks, and the LLM orchestrator knows how to talk to
whichever provider is configured. Nothing here decides a grade.

Design, in three steps:

1. RETRIEVE, not scan-everything. A course can hold a thousand traps; sending
   all of them to a model per submission would be slow and imprecise. Traps are
   ranked by distinctive-term overlap with the submission and only the strongest
   handful go to the model.

2. VERIFY with evidence. The model is asked one question per candidate trap and
   must return a VERBATIM quote from the submission. A quote that does not
   appear in the text, character for character, is discarded and the finding
   with it. This is the attribution guard: the system may report what the
   student wrote, never what the system imagines they wrote.

3. DRAFT, never send. The output is a subject line and a body the educator
   reads, edits and sends themselves. There is no mail transport here on
   purpose - nothing is dispatched without a person deciding to dispatch it.

The drafted message points the student at a section of the textbook and asks
one question from the trap's probe ladder. It does not tell them what is wrong
or what to write instead, which would hand over the answer the assignment is
asking them to reach.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.event_store import event_store
from fiosra.mvp.llm.orchestrator import LLMOrchestrator
from fiosra.mvp.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interventions", tags=["Misconception Interventions"])

# How many ranked candidates reach the model. Each is a separate round trip, so
# this is the main lever on how long a scan takes. Four covers an assignment's
# authored trap set while keeping the wait tolerable on a local model.
MAX_CANDIDATES = 4

# One slow trap must not hold up the whole scan.
PER_TRAP_TIMEOUT_SECONDS = 45.0

STOPWORDS = frozenset("""
a about above after again against all am an and any are as at be because been before being below between both but by
can cannot could did do does doing down during each few for from further had has have having he her here hers him his
how i if in into is it its itself just me more most my no nor not of off on once only or other our out over own same
she should so some such than that the their them then there these they this those through to too under until up very
was we were what when where which while who whom why will with you your
""".split())

WORD = re.compile(r"[a-z][a-z'-]{2,}")


# --------------------------------------------------------------------- sources

async def _submission_text(session_id: UUID) -> tuple[str, str | None]:
    """The student's written work, as one plaintext string, plus its title."""
    async with AsyncSessionLocal() as db:
        doc = (await db.execute(text("""
            SELECT document_id, title FROM learning_documents
            WHERE session_id = CAST(:sid AS UUID)
            ORDER BY created_at DESC LIMIT 1
        """), {"sid": str(session_id)})).mappings().first()
        if not doc:
            return "", None
        blocks = (await db.execute(text("""
            SELECT plaintext FROM learning_document_blocks
            WHERE document_id = CAST(:did AS UUID)
            ORDER BY position ASC
        """), {"did": str(doc["document_id"])})).mappings().all()
    body = "\n\n".join((b["plaintext"] or "").strip() for b in blocks if (b["plaintext"] or "").strip())
    return body, doc["title"]


async def _course_for_session(session_info: dict[str, Any]) -> str | None:
    assignment_id = session_info.get("assignment_id")
    if not assignment_id:
        return None
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("""
            SELECT m.course_id FROM assignments a
            JOIN modules m ON m.module_id = a.module_id
            WHERE a.assignment_id = CAST(:aid AS UUID)
        """), {"aid": str(assignment_id)})).mappings().first()
    return str(row["course_id"]) if row else None


TRAPS_FOR_COURSE = """
MATCH (c:Concept {course_id: $course_id})-[:ASSOCIATED_WITH]->(t:Misconception)
WHERE coalesce(t.status, 'approved') <> 'superseded'
  AND coalesce(c.status, 'approved') <> 'superseded'
OPTIONAL MATCH (t)-[:PROBED_BY]->(p:SocraticProbe)
WHERE coalesce(p.status, 'approved') <> 'superseded'
WITH t, c, p ORDER BY p.rung ASC
RETURN t.misconception_id AS misconception_id,
       t.name            AS name,
       t.flawed_rule     AS flawed_rule,
       t.remediation_hint AS remediation_hint,
       c.concept_id      AS concept_id,
       c.label           AS concept_label,
       collect(DISTINCT {rung: p.rung, probe_text: p.probe_text}) AS probes
"""


async def _traps_for_course(course_id: str) -> list[dict[str, Any]]:
    async with neo4j_client.get_session() as session:
        result = await session.run(TRAPS_FOR_COURSE, {"course_id": course_id})
        rows = [dict(record) async for record in result]
    for row in rows:
        row["probes"] = sorted(
            [p for p in (row.get("probes") or []) if p.get("probe_text")],
            key=lambda p: (p.get("rung") if p.get("rung") is not None else 9),
        )
    return rows


# --------------------------------------------------------------------- ranking

def _terms(s: str) -> set[str]:
    return {w for w in WORD.findall((s or "").lower()) if w not in STOPWORDS}


def _rank(traps: list[dict[str, Any]], submission: str) -> list[tuple[dict[str, Any], float]]:
    """Rank traps by IDF-weighted term overlap with the submission.

    A term shared by every trap says nothing about which one applies, so terms
    are weighted by inverse document frequency. IDF is used rather than fixed
    thresholds because it behaves the same whether a course has five traps or
    fifteen hundred - the scale adapts to the corpus instead of assuming one.
    """
    present = _terms(submission)
    document_frequency: dict[str, int] = {}
    per_trap: list[set[str]] = []
    for trap in traps:
        t = _terms(f"{trap.get('name', '')} {trap.get('flawed_rule', '')}")
        per_trap.append(t)
        for term in t:
            document_frequency[term] = document_frequency.get(term, 0) + 1

    total = max(1, len(traps))
    scored: list[tuple[dict[str, Any], float]] = []
    for trap, trap_terms in zip(traps, per_trap):
        score = sum(
            math.log(total / document_frequency.get(term, 1)) + 0.1
            for term in trap_terms & present
        )
        scored.append((trap, round(score, 2)))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    # Retrieval favours recall: anything with a signal is a candidate, and the
    # model does the discriminating. Only zero-overlap traps are dropped.
    return [(trap, score) for trap, score in scored if score > 0]


# ---------------------------------------------------------------- verification

VERIFY_SYSTEM = (
    "You judge whether a piece of student writing exhibits one specific reasoning error. "
    "You are given the error and the student's full text. Answer only about that error. "
    "You never grade, never rewrite the student's work, and never state what the student should have written. "
    'Reply with JSON only: {"exhibits": true|false, "quote": "<verbatim sentence from the text, or empty>", '
    '"reason": "<at most 25 words naming what the quote shows>"}. '
    "The quote must be copied character for character from the student's text. "
    "If the text does not clearly exhibit the error, answer false with an empty quote."
)


def _normalise(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _quote_is_real(quote: str, submission: str) -> bool:
    """The attribution guard: a quote the student did not write is not evidence."""
    q = _normalise(quote)
    return bool(q) and len(q) >= 20 and q in _normalise(submission)


async def _verify(trap: dict[str, Any], submission: str, session_id: str) -> dict[str, Any] | None:
    orchestrator = LLMOrchestrator()
    user_prompt = (
        f"THE REASONING ERROR\nName: {trap.get('name')}\n"
        f"The flawed rule: {trap.get('flawed_rule')}\n\n"
        f"THE STUDENT'S TEXT\n\"\"\"\n{submission}\n\"\"\"\n\n"
        "Does the text exhibit that specific error? JSON only."
    )
    try:
        generated = await orchestrator.enhance(
            purpose="misconception_scan",
            system_prompt=VERIFY_SYSTEM,
            user_prompt=user_prompt,
            deterministic_fallback="",
            pseudonymous_seed=f"{session_id}:{trap.get('misconception_id')}",
            max_characters=800,
            max_tokens=300,
            allow_live=True,
            request_timeout_seconds=PER_TRAP_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
        raw = (generated.content or "").strip()
    except Exception as exc:
        logger.info("LLM verification unavailable for %s: %s", trap.get("misconception_id"), exc)
        return None

    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        verdict = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if not verdict.get("exhibits"):
        return None
    quote = (verdict.get("quote") or "").strip()
    if not _quote_is_real(quote, submission):
        # The model asserted the trap but could not ground it in the text.
        # Report nothing rather than an unevidenced claim about a student.
        logger.info("Discarded ungrounded finding for %s", trap.get("misconception_id"))
        return None
    return {"quote": quote, "reason": (verdict.get("reason") or "").strip()[:200], "method": "llm_verified"}


# ------------------------------------------------------------------- the draft

def _draft_message(trap: dict[str, Any], student_id: str, assignment_title: str) -> dict[str, str]:
    """A note that points at the reading and asks a question. No answer in it."""
    probes = trap.get("probes") or []
    opener = next((p["probe_text"] for p in probes if p.get("rung") == 0), None)
    question = opener or (probes[0]["probe_text"] if probes else "")
    hint = trap.get("remediation_hint") or ""

    body = (
        f"Hello,\n\n"
        f"I have read your submission for {assignment_title}, and there is one part of the reasoning "
        f"I would like you to look at again before we discuss it.\n\n"
        f"Where to look: {hint}\n\n"
        f"A question to take with you: {question}\n\n"
        f"You do not need to rewrite anything yet. Read that section, sit with the question, and bring "
        f"me your answer.\n\n"
        f"Best wishes"
    )
    return {
        "to_student_id": student_id,
        "subject": f"A question about your {assignment_title} submission",
        "body": body,
    }


# --------------------------------------------------------------------- the API

class Finding(BaseModel):
    misconception_id: str
    name: str
    flawed_rule: str
    remediation_hint: str = ""
    concept_id: str | None = None
    concept_label: str | None = None
    evidence_quote: str = Field(description="Verbatim from the submission; verified present before returning")
    why: str = ""
    detection: str = Field(description="llm_verified, or lexical_candidate when no model was available")
    probes: list[dict[str, Any]] = []
    suggested_message: dict[str, str] = {}


class ScanResult(BaseModel):
    session_id: str
    student_id: str | None = None
    assignment_title: str | None = None
    submission_characters: int
    candidates_considered: int
    findings: list[Finding]
    note: str


@router.get("/scan/{session_id}", response_model=ScanResult)
async def scan_submission(session_id: UUID) -> ScanResult:
    """Find the traps a submitted assignment exhibits, with evidence."""
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")

    submission, doc_title = await _submission_text(session_id)
    if len(submission.strip()) < 120:
        return ScanResult(
            session_id=str(session_id), student_id=session_info.get("student_id"),
            assignment_title=doc_title, submission_characters=len(submission),
            candidates_considered=0, findings=[],
            note="Too little written work to analyse.",
        )

    course_id = await _course_for_session(session_info)
    if not course_id:
        raise HTTPException(status_code=409, detail="This session is not linked to a course.")

    traps = await _traps_for_course(course_id)
    ranked = _rank(traps, submission)[:MAX_CANDIDATES]

    # The candidates are independent questions, so ask them at once. Sequentially
    # this is four round trips of dead time; concurrently it is one.
    verdicts = await asyncio.gather(
        *(_verify(trap, submission, str(session_id)) for trap, _ in ranked),
        return_exceptions=True,
    )

    findings: list[Finding] = []
    llm_used = False
    for (trap, score), verdict in zip(ranked, verdicts):
        if isinstance(verdict, BaseException):
            logger.info("Verification failed for %s: %s", trap.get("misconception_id"), verdict)
            verdict = None
        if verdict:
            llm_used = True
        elif not ranked or score < 0.6 * ranked[0][1]:
            continue
        else:
            # No model available, but the lexical signal is strong. Report it as
            # a candidate for the educator to judge, clearly labelled as such.
            verdict = {"quote": "", "reason": "Strong term overlap with this trap's flawed rule.",
                       "method": "lexical_candidate"}
        findings.append(Finding(
            misconception_id=trap["misconception_id"], name=trap.get("name") or "",
            flawed_rule=trap.get("flawed_rule") or "", remediation_hint=trap.get("remediation_hint") or "",
            concept_id=trap.get("concept_id"), concept_label=trap.get("concept_label"),
            evidence_quote=verdict["quote"], why=verdict["reason"], detection=verdict["method"],
            probes=trap.get("probes") or [],
            suggested_message=_draft_message(trap, session_info.get("student_id") or "", doc_title or "this assignment"),
        ))

    note = (
        "Findings are evidence of what the student wrote, not a judgement of what they believe. "
        "Every quote was checked against the submission before being shown."
        if llm_used else
        "No live language model was available, so these are lexical candidates only - read the quotes yourself."
    )
    return ScanResult(
        session_id=str(session_id), student_id=session_info.get("student_id"),
        assignment_title=doc_title, submission_characters=len(submission),
        candidates_considered=len(ranked), findings=findings, note=note,
    )
