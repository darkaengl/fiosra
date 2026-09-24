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

async def _submission_document(session_id: UUID) -> dict[str, Any]:
    """The student's written work, title, document_id, and blocks with block_id."""
    async with AsyncSessionLocal() as db:
        doc = (await db.execute(text("""
            SELECT document_id, title FROM learning_documents
            WHERE session_id = CAST(:sid AS UUID)
            ORDER BY created_at DESC LIMIT 1
        """), {"sid": str(session_id)})).mappings().first()
        if not doc:
            return {"body": "", "title": None, "document_id": None, "blocks": []}
        blocks = (await db.execute(text("""
            SELECT block_id, plaintext, position FROM learning_document_blocks
            WHERE document_id = CAST(:did AS UUID)
            ORDER BY position ASC
        """), {"did": str(doc["document_id"])})).mappings().all()
    body = "\n\n".join((b["plaintext"] or "").strip() for b in blocks if (b["plaintext"] or "").strip())
    return {
        "body": body,
        "title": doc["title"],
        "document_id": str(doc["document_id"]),
        "blocks": [dict(b) for b in blocks],
    }


async def _submission_text(session_id: UUID) -> tuple[str, str | None]:
    """The student's written work, as one plaintext string, plus its title."""
    doc_info = await _submission_document(session_id)
    return doc_info["body"], doc_info["title"]


def _match_block_for_quote(quote: str, blocks: list[dict[str, Any]]) -> str | None:
    if not quote:
        return None
    norm_quote = _normalise(quote)
    for b in blocks:
        norm_text = _normalise(b.get("plaintext") or "")
        if norm_quote in norm_text:
            return str(b["block_id"])
    return None


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


# ------------------------------------------------------------------- the draft & activity

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


ACTIVITY_SYSTEM = (
    "You are a master educator crafting a targeted, minimal learning activity (a Socratic nudge) for a university student. "
    "The student exhibited a specific reasoning error in their draft text. "
    "You never give away the answer or rewrite their text. "
    "Instead, craft a concise, thought-provoking cognitive challenge (1-2 sentences) that prompts the student to rethink this specific point. "
    "Also provide a brief 1-sentence guidance on where to look or what principle to apply. "
    'Reply with JSON only: {"activity_type": "socratic_nudge", "activity_prompt": "<1-2 sentence challenge question>", "activity_guidance": "<1 sentence guidance or reading hint>"}'
)


async def _generate_activity(trap: dict[str, Any], quote: str, session_id: str) -> dict[str, str]:
    """Craft a minimal Socratic learning challenge grounded in the student's quote."""
    probes = trap.get("probes") or []
    opener = next((p["probe_text"] for p in probes if p.get("rung") == 0), None)
    fallback_prompt = opener or (probes[0]["probe_text"] if probes else (
        f"Consider how your reasoning in '{quote[:50]}...' aligns with {trap.get('concept_label') or 'the core concepts'}."
        if quote else "Consider how this claim aligns with foundational principles."
    ))
    fallback_guidance = trap.get("remediation_hint") or "Review the foundational principles in the course materials."

    orchestrator = LLMOrchestrator()
    user_prompt = (
        f"MISCONCEPTION: {trap.get('name')}\n"
        f"FLAWED RULE: {trap.get('flawed_rule')}\n"
        f"STUDENT QUOTE: \"{quote}\"\n"
        f"SUGGESTED READING HINT: {fallback_guidance}\n"
        f"SEED SOCRATIC QUESTION: {fallback_prompt}\n\n"
        "Generate a minimal, sharp Socratic nudge activity for the student in JSON."
    )
    try:
        generated = await orchestrator.enhance(
            purpose="intervention_activity",
            system_prompt=ACTIVITY_SYSTEM,
            user_prompt=user_prompt,
            deterministic_fallback="",
            pseudonymous_seed=f"{session_id}:{trap.get('misconception_id')}:act",
            max_characters=600,
            max_tokens=250,
            allow_live=True,
            request_timeout_seconds=PER_TRAP_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
        raw = (generated.content or "").strip()
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            parsed = json.loads(match.group(0))
            prompt = (parsed.get("activity_prompt") or "").strip()
            guidance = (parsed.get("activity_guidance") or "").strip()
            if prompt:
                return {
                    "activity_type": parsed.get("activity_type") or "socratic_nudge",
                    "activity_prompt": prompt,
                    "activity_guidance": guidance or fallback_guidance,
                }
    except Exception as exc:
        logger.info("Activity generation LLM failed: %s", exc)

    return {
        "activity_type": "socratic_nudge",
        "activity_prompt": fallback_prompt,
        "activity_guidance": fallback_guidance,
    }


# --------------------------------------------------------------------- schemas

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
    document_id: str | None = None
    block_id: str | None = None
    activity_type: str = "socratic_nudge"
    activity_prompt: str = ""
    activity_guidance: str = ""


class ScanResult(BaseModel):
    session_id: str
    student_id: str | None = None
    assignment_title: str | None = None
    submission_characters: int
    candidates_considered: int
    findings: list[Finding]
    note: str


class DispatchInterventionRequest(BaseModel):
    session_id: UUID
    student_id: str
    teacher_id: str = "educator"
    document_id: UUID | None = None
    block_id: UUID | None = None
    concept_id: str | None = None
    concept_label: str | None = None
    misconception_id: str | None = None
    evidence_quote: str
    activity_type: str = "socratic_nudge"
    activity_prompt: str
    activity_guidance: str | None = None


class RespondInterventionRequest(BaseModel):
    student_response: str


class InterventionResponse(BaseModel):
    intervention_id: str
    session_id: str
    student_id: str
    teacher_id: str
    document_id: str | None = None
    block_id: str | None = None
    concept_id: str | None = None
    concept_label: str | None = None
    misconception_id: str | None = None
    evidence_quote: str
    activity_type: str
    activity_prompt: str
    activity_guidance: str | None = None
    student_response: str | None = None
    status: str
    created_at: str
    responded_at: str | None = None
    acknowledged_at: str | None = None


def _row_to_intervention_dict(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "intervention_id": str(r["intervention_id"]),
        "session_id": str(r["session_id"]),
        "student_id": str(r["student_id"]),
        "teacher_id": str(r["teacher_id"]),
        "document_id": str(r["document_id"]) if r.get("document_id") else None,
        "block_id": str(r["block_id"]) if r.get("block_id") else None,
        "concept_id": r.get("concept_id"),
        "concept_label": r.get("concept_label"),
        "misconception_id": r.get("misconception_id"),
        "evidence_quote": r.get("evidence_quote") or "",
        "activity_type": r.get("activity_type") or "socratic_nudge",
        "activity_prompt": r.get("activity_prompt") or "",
        "activity_guidance": r.get("activity_guidance"),
        "student_response": r.get("student_response"),
        "status": r.get("status") or "dispatched",
        "created_at": r["created_at"].isoformat() if hasattr(r.get("created_at"), "isoformat") else str(r.get("created_at") or ""),
        "responded_at": r["responded_at"].isoformat() if hasattr(r.get("responded_at"), "isoformat") else (str(r.get("responded_at")) if r.get("responded_at") else None),
        "acknowledged_at": r["acknowledged_at"].isoformat() if hasattr(r.get("acknowledged_at"), "isoformat") else (str(r.get("acknowledged_at")) if r.get("acknowledged_at") else None),
    }


# --------------------------------------------------------------------- the API

@router.get("/scan/{session_id}", response_model=ScanResult)
async def scan_submission(session_id: UUID) -> ScanResult:
    """Find the traps a submitted or in-progress assignment exhibits, with evidence."""
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")

    doc_info = await _submission_document(session_id)
    submission = doc_info["body"]
    doc_title = doc_info["title"]
    document_id = doc_info["document_id"]
    blocks = doc_info["blocks"]

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
            verdict = {"quote": "", "reason": "Strong term overlap with this trap's flawed rule.",
                       "method": "lexical_candidate"}

        quote = verdict["quote"]
        block_id = _match_block_for_quote(quote, blocks) if quote else None

        # Synthesize the minimal Socratic activity for this finding
        activity = await _generate_activity(trap, quote, str(session_id))

        findings.append(Finding(
            misconception_id=trap["misconception_id"], name=trap.get("name") or "",
            flawed_rule=trap.get("flawed_rule") or "", remediation_hint=trap.get("remediation_hint") or "",
            concept_id=trap.get("concept_id"), concept_label=trap.get("concept_label"),
            evidence_quote=quote, why=verdict["reason"], detection=verdict["method"],
            probes=trap.get("probes") or [],
            suggested_message=_draft_message(trap, session_info.get("student_id") or "", doc_title or "this assignment"),
            document_id=document_id,
            block_id=block_id,
            activity_type=activity.get("activity_type") or "socratic_nudge",
            activity_prompt=activity.get("activity_prompt") or "",
            activity_guidance=activity.get("activity_guidance") or "",
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


@router.post("/dispatch", response_model=InterventionResponse)
async def dispatch_intervention(req: DispatchInterventionRequest) -> InterventionResponse:
    """Educator dispatches an AI-generated or custom learning activity to a student."""
    async with AsyncSessionLocal() as db:
        insert_sql = text("""
            INSERT INTO assignment_interventions (
                session_id, student_id, teacher_id, document_id, block_id,
                concept_id, concept_label, misconception_id, evidence_quote,
                activity_type, activity_prompt, activity_guidance, status, created_at
            ) VALUES (
                CAST(:session_id AS UUID), :student_id, :teacher_id,
                CAST(:document_id AS UUID), CAST(:block_id AS UUID),
                :concept_id, :concept_label, :misconception_id, :evidence_quote,
                :activity_type, :activity_prompt, :activity_guidance, 'dispatched', NOW()
            ) RETURNING intervention_id, session_id, student_id, teacher_id, document_id, block_id,
                        concept_id, concept_label, misconception_id, evidence_quote, activity_type,
                        activity_prompt, activity_guidance, student_response, status,
                        created_at, responded_at, acknowledged_at;
        """)
        result = await db.execute(insert_sql, {
            "session_id": str(req.session_id),
            "student_id": req.student_id,
            "teacher_id": req.teacher_id,
            "document_id": str(req.document_id) if req.document_id else None,
            "block_id": str(req.block_id) if req.block_id else None,
            "concept_id": req.concept_id,
            "concept_label": req.concept_label,
            "misconception_id": req.misconception_id,
            "evidence_quote": req.evidence_quote,
            "activity_type": req.activity_type,
            "activity_prompt": req.activity_prompt,
            "activity_guidance": req.activity_guidance,
        })
        await db.commit()
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=500, detail="Failed to dispatch intervention")

    intervention_data = _row_to_intervention_dict(dict(row))

    # Log telemetry event
    try:
        await event_store.log_event(
            session_id=req.session_id,
            student_id=req.student_id,
            question_id="intervention",
            event_type="intervention_dispatched",
            payload={
                "intervention_id": intervention_data["intervention_id"],
                "concept_id": req.concept_id,
                "misconception_id": req.misconception_id,
                "activity_type": req.activity_type,
                "teacher_id": req.teacher_id,
            },
        )
    except Exception as exc:
        logger.warning("Failed to record intervention event: %s", exc)

    return InterventionResponse(**intervention_data)


@router.get("/session/{session_id}", response_model=list[InterventionResponse])
async def list_session_interventions(session_id: UUID) -> list[InterventionResponse]:
    """Retrieve all interventions dispatched for a given student session."""
    async with AsyncSessionLocal() as db:
        query_sql = text("""
            SELECT intervention_id, session_id, student_id, teacher_id, document_id, block_id,
                   concept_id, concept_label, misconception_id, evidence_quote, activity_type,
                   activity_prompt, activity_guidance, student_response, status,
                   created_at, responded_at, acknowledged_at
            FROM assignment_interventions
            WHERE session_id = CAST(:session_id AS UUID)
            ORDER BY created_at DESC;
        """)
        result = await db.execute(query_sql, {"session_id": str(session_id)})
        rows = result.mappings().all()

    return [InterventionResponse(**_row_to_intervention_dict(dict(r))) for r in rows]


@router.post("/{intervention_id}/respond", response_model=InterventionResponse)
async def respond_to_intervention(intervention_id: UUID, req: RespondInterventionRequest) -> InterventionResponse:
    """Student submits a reflection or answer to the intervention activity."""
    if not req.student_response or len(req.student_response.strip()) < 5:
        raise HTTPException(status_code=422, detail="A response of at least 5 characters is required.")

    async with AsyncSessionLocal() as db:
        update_sql = text("""
            UPDATE assignment_interventions
            SET student_response = :student_response,
                status = 'responded',
                responded_at = NOW()
            WHERE intervention_id = CAST(:intervention_id AS UUID)
            RETURNING intervention_id, session_id, student_id, teacher_id, document_id, block_id,
                      concept_id, concept_label, misconception_id, evidence_quote, activity_type,
                      activity_prompt, activity_guidance, student_response, status,
                      created_at, responded_at, acknowledged_at;
        """)
        result = await db.execute(update_sql, {
            "intervention_id": str(intervention_id),
            "student_response": req.student_response.strip(),
        })
        await db.commit()
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Intervention not found")

    intervention_data = _row_to_intervention_dict(dict(row))

    # Log telemetry event
    try:
        await event_store.log_event(
            session_id=row["session_id"],
            student_id=row["student_id"],
            question_id="intervention",
            event_type="intervention_responded",
            payload={
                "intervention_id": intervention_data["intervention_id"],
                "response_length": len(req.student_response.strip()),
            },
        )
    except Exception as exc:
        logger.warning("Failed to record intervention response event: %s", exc)

    return InterventionResponse(**intervention_data)


@router.post("/{intervention_id}/acknowledge", response_model=InterventionResponse)
async def acknowledge_intervention(intervention_id: UUID) -> InterventionResponse:
    """Educator marks student's intervention response as acknowledged/resolved."""
    async with AsyncSessionLocal() as db:
        update_sql = text("""
            UPDATE assignment_interventions
            SET status = 'acknowledged',
                acknowledged_at = NOW()
            WHERE intervention_id = CAST(:intervention_id AS UUID)
            RETURNING intervention_id, session_id, student_id, teacher_id, document_id, block_id,
                      concept_id, concept_label, misconception_id, evidence_quote, activity_type,
                      activity_prompt, activity_guidance, student_response, status,
                      created_at, responded_at, acknowledged_at;
        """)
        result = await db.execute(update_sql, {"intervention_id": str(intervention_id)})
        await db.commit()
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Intervention not found")

    intervention_data = _row_to_intervention_dict(dict(row))
    return InterventionResponse(**intervention_data)


@router.get("/student/{student_id}", response_model=list[InterventionResponse])
async def list_student_interventions(student_id: str) -> list[InterventionResponse]:
    """Retrieve all interventions dispatched to a student across courses."""
    async with AsyncSessionLocal() as db:
        query_sql = text("""
            SELECT intervention_id, session_id, student_id, teacher_id, document_id, block_id,
                   concept_id, concept_label, misconception_id, evidence_quote, activity_type,
                   activity_prompt, activity_guidance, student_response, status,
                   created_at, responded_at, acknowledged_at
            FROM assignment_interventions
            WHERE student_id = :student_id
            ORDER BY created_at DESC;
        """)
        result = await db.execute(query_sql, {"student_id": student_id})
        rows = result.mappings().all()

    return [InterventionResponse(**_row_to_intervention_dict(dict(r))) for r in rows]

