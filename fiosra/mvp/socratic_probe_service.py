"""Server-authoritative proactive Socratic probe lifecycle for learner documents."""

import asyncio
import hashlib
import json
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.canvas_scribe_helper import canvas_scribe_helper
from fiosra.mvp.concepts.service import concept_graph_service
from fiosra.mvp.config import settings
from fiosra.mvp.courses.ingestion import syllabus_parser
from fiosra.mvp.event_store import event_store
from fiosra.mvp.learning_document_service import (
    LearningDocumentAccessError,
    LearningDocumentConflictError,
    LearningDocumentValidationError,
    learning_document_service,
)
from fiosra.mvp.llm.orchestrator import GuardedGeneration, llm_orchestrator
from fiosra.mvp.socratic_probe_schemas import (
    DialecticalTurnRequest,
    DialecticalTurnResponse,
    EpistemicClassifyRequest,
    EpistemicClassifyResponse,
    EpistemicToolAction,
    OutlineOption,
    ProbeDispositionResponse,
    ProbeEvaluationRequest,
    ProbeEvaluationResponse,
    ProbeListResponse,
    ProbeTraceRecord,
    SentenceClassification,
    SentenceInquireRequest,
    SentenceInquireResponse,
    SocraticProbeCard,
    SubmitProbeResponseRequest,
)

logger = logging.getLogger(__name__)


class SocraticProbeAccessError(PermissionError):
    """Raised when a probe request does not own the targeted learning session."""


class SocraticProbeConflictError(RuntimeError):
    """Raised when a probe action conflicts with authoritative document/session state."""


class SocraticProbeValidationError(ValueError):
    """Raised when a probe action violates a learning workflow invariant."""


class SocraticModelUnavailableError(RuntimeError):
    """Raised when requested Enquirer assistance has no valid live model result."""


class SocraticProbeService:
    """Offer one bounded question per stable learner-authored paragraph revision."""

    _concept_probe_schema_ready = False
    _concept_probe_schema_lock = asyncio.Lock()

    @classmethod
    async def _ensure_concept_probe_schema(cls) -> None:
        """Apply additive probe columns for existing development databases."""
        if cls._concept_probe_schema_ready:
            return
        async with cls._concept_probe_schema_lock:
            if cls._concept_probe_schema_ready:
                return
            from fiosra.mvp.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("ALTER TABLE socratic_probes ADD COLUMN IF NOT EXISTS concept_id VARCHAR(96);")
                )
                await session.execute(
                    text("ALTER TABLE socratic_probes ADD COLUMN IF NOT EXISTS concept_label VARCHAR(160);")
                )
                await session.commit()
            cls._concept_probe_schema_ready = True

    _CLAIM_RE = re.compile(
        r"\b(?:is|are|was|were|shows?|suggests?|indicates?|supports?|demonstrates?|"
        r"means?|causes?|led|leads?|result(?:s|ed)?|because|therefore|thus|hence)\b",
        re.IGNORECASE,
    )
    _CAUSAL_RE = re.compile(r"\b(?:because|therefore|thus|hence|causes?|led to|results? in)\b", re.IGNORECASE)
    _EVIDENCE_RE = re.compile(
        r"\b(?:source|evidence|report|text|excerpt|observation|detail|shows?|suggests?|indicates?|supports?)\b",
        re.IGNORECASE,
    )
    _ALTERNATIVE_RE = re.compile(r"\b(?:however|although|but|instead|alternative|rather than)\b", re.IGNORECASE)
    _ABSOLUTE_RE = re.compile(r"\b(?:always|never|proves?|clearly|undoubtedly|all|none|only)\b", re.IGNORECASE)
    _FOCUS_QUESTIONS: ClassVar[dict[str, str]] = {
        "direct_observation": "Which specific detail in an approved source could you point to before making this claim?",
        "warrant": "What is the reasoning that connects that detail to your claim?",
        "causal_bridge": "What mechanism would need to connect the condition you describe to that outcome?",
        "alternative_explanation": "What plausible alternative explanation should this paragraph distinguish from your claim?",
        "qualification": "What limitation would keep this claim within what your evidence can actually support?",
    }

    async def _authorized_context(
        self,
        session_id: UUID | str,
        access_token: str | None,
    ) -> tuple[dict[str, Any], Any, Any]:
        if not await event_store.has_session_access(session_id, access_token):
            raise SocraticProbeAccessError("This browser is not authorized to access the requested questions.")
        session_info = await event_store.get_session_details(session_id)
        if not session_info:
            raise SocraticProbeValidationError("The requested learning session no longer exists.")
        if session_info["status"] != "active":
            raise SocraticProbeConflictError("Submitted or completed sessions cannot receive new questions.")
        assignment_id = session_info.get("assignment_id")
        assignment = await assignment_generator.get_public_assignment(assignment_id) if assignment_id else None
        if not assignment or assignment.status != "published":
            raise SocraticProbeValidationError("This session is not linked to an available published assignment.")
        try:
            document = await learning_document_service.get_state(session_id, access_token)
        except LearningDocumentAccessError as error:
            raise SocraticProbeAccessError(str(error)) from error
        except LearningDocumentConflictError as error:
            raise SocraticProbeConflictError(str(error)) from error
        except LearningDocumentValidationError as error:
            raise SocraticProbeValidationError(str(error)) from error
        return session_info, assignment, document

    _PREMATURE_CLOSURE_RE = re.compile(
        r"\b(?:therefore|thus|hence|in conclusion|consequently|it is clear that|proves that)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _select_focus(cls, plaintext: str) -> str | None:
        """Choose one deterministic question focus only for a substantive proposition."""
        normalized = " ".join(plaintext.split())
        if len(normalized) < settings.FIOSRA_PROBE_MIN_MATERIAL_CHARACTERS:
            return None
        if not cls._CLAIM_RE.search(normalized):
            return None
        if cls._PREMATURE_CLOSURE_RE.search(normalized) and not cls._EVIDENCE_RE.search(normalized):
            return "warrant"
        if cls._ABSOLUTE_RE.search(normalized):
            return "qualification"
        if cls._CAUSAL_RE.search(normalized):
            return "causal_bridge"
        if cls._EVIDENCE_RE.search(normalized) and not cls._ALTERNATIVE_RE.search(normalized):
            return "warrant"
        if not cls._ALTERNATIVE_RE.search(normalized):
            return "alternative_explanation"
        return "direct_observation"

    @staticmethod
    def _claim_fingerprint(plaintext: str) -> str:
        return hashlib.sha256(" ".join(plaintext.lower().split()).encode("utf-8")).hexdigest()

    @staticmethod
    def _section_label(assignment: Any, section_id: str | None) -> str:
        if section_id:
            matched = next(
                (section for section in assignment.canvas_sections if section.section_id == section_id),
                None,
            )
            if matched:
                return str(matched.label)
        return "Student writing"

    @staticmethod
    def _metadata(generation: GuardedGeneration) -> dict[str, Any]:
        return generation.metadata.as_dict()

    @staticmethod
    def _parse_metadata(raw: Any) -> dict[str, Any]:
        if isinstance(raw, str):
            return json.loads(raw)
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    async def _assignment_course_id(assignment_id: UUID | str) -> str | None:
        """Resolve the assigned module's course without exposing it to the client."""
        query = text("""
            SELECT module.course_id
            FROM assignments assignment
            JOIN modules module ON module.module_id = assignment.module_id
            WHERE assignment.assignment_id = CAST(:assignment_id AS UUID);
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(query, {"assignment_id": str(assignment_id)})
            course_id = result.scalar()
        return str(course_id) if course_id else None

    async def _concepts_for_claim(
        self,
        assignment_id: UUID | str,
        claim_text: str,
    ) -> list[dict[str, str]]:
        """Retrieve teacher-approved concepts relevant to one saved learner claim."""
        course_id = await self._assignment_course_id(assignment_id)
        if not course_id:
            return []
        try:
            return await concept_graph_service.match_claim_concepts(course_id, claim_text)
        except Exception as error:  # Graph availability must never interrupt drafting.
            logger.info("Concept lookup unavailable for a Socratic probe: %s", error)
            return []

    @classmethod
    def _card(cls, row: Any, section_label: str) -> SocraticProbeCard:
        metadata = cls._parse_metadata(row["generation_metadata"])
        return SocraticProbeCard(
            probe_id=row["probe_id"],
            document_id=row["document_id"],
            block_id=row["block_id"],
            source_block_revision=row["source_block_revision"],
            section_label=section_label,
            focus_type=row["focus_type"],
            question=row["question"],
            concept_id=row.get("concept_id"),
            concept_label=row.get("concept_label"),
            claim_text=row.get("claim_text") or row.get("plaintext"),
            status=row["status"],
            evidence_state="evidence_submitted" if row.get("response_text") else "unverified",
            offered_at=row["offered_at"],
            deferred_until=row.get("deferred_until"),
            response_text=row.get("response_text"),
            responded_at=row.get("responded_at"),
            generation_metadata=metadata,
        )

    @staticmethod
    def _single_live_question(content: str) -> str | None:
        """Accept one compact question from a live response without inventing a fallback."""
        normalized = content.strip()
        if normalized.startswith("{"):
            try:
                payload = json.loads(normalized)
            except json.JSONDecodeError:
                return None
            question_value = payload.get("question") if isinstance(payload, dict) else None
            if not isinstance(question_value, str):
                return None
            normalized = question_value
        normalized = re.sub(r"\s+", " ", normalized).strip()
        match = re.search(r"[^.?!]*\?", normalized)
        if not match:
            return None
        question = match.group(0).strip(" -–—:;\"'")
        if (
            len(question) < 18
            or len(question) > 260
            or question.count("?") != 1
            or not question.endswith("?")
            or re.search(r"\b(?:the answer is|you should conclude|the source proves)\b", question, re.IGNORECASE)
        ):
            return None
        return question

    async def _summary(self, session_id: UUID | str) -> dict[str, int]:
        summary_sql = text("""
            SELECT
                COUNT(*) FILTER (WHERE status IN ('offered', 'deferred')) AS pending_questions,
                COUNT(*) FILTER (WHERE status = 'responded') AS evidence_submitted,
                COUNT(*) FILTER (WHERE status = 'dismissed') AS dismissed_questions,
                COUNT(*) FILTER (WHERE status = 'superseded') AS superseded_questions
            FROM socratic_probes
            WHERE session_id = CAST(:session_id AS UUID);
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(summary_sql, {"session_id": str(session_id)})
            row = result.mappings().one()
        return {key: int(value or 0) for key, value in row.items()}

    async def list_probes(
        self,
        session_id: UUID | str,
        access_token: str | None,
        include_resolved: bool = False,
    ) -> ProbeListResponse:
        """Restore learner-visible current cards after capability and lifecycle checks."""
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        where_status = "status IN ('offered', 'deferred')" if not include_resolved else "status <> 'superseded'"
        query_sql = text(f"""
            SELECT p.*, b.section_id, b.plaintext AS claim_text, r.response_text, r.updated_at AS response_updated_at
            FROM socratic_probes p
            JOIN learning_document_blocks b ON b.block_id = p.block_id
            LEFT JOIN socratic_probe_responses r ON r.probe_id = p.probe_id
            WHERE p.session_id = CAST(:session_id AS UUID) AND {where_status}
            ORDER BY p.offered_at ASC;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_info["session_id"])})
            rows = result.mappings().all()
        cards = [self._card(row, self._section_label(assignment, row["section_id"])) for row in rows]
        return ProbeListResponse(
            document_revision=document.document_revision,
            probes=cards,
            evidence_summary=await self._summary(session_info["session_id"]),
        )

    async def evaluate(
        self,
        session_id: UUID | str,
        access_token: str | None,
        request: ProbeEvaluationRequest,
    ) -> ProbeEvaluationResponse:
        """Evaluate already-saved blocks and create bounded questions only when eligible."""
        await self._ensure_concept_probe_schema()
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        if request.document_revision != document.document_revision:
            raise SocraticProbeConflictError("This document changed before questions could be evaluated. Continue writing and try again.")

        block_sql = text("""
            SELECT block_id, section_id, block_type, plaintext, author_type, revision, updated_at
            FROM learning_document_blocks
            WHERE document_id = CAST(:document_id AS UUID)
              AND block_id = ANY(CAST(:block_ids AS UUID[]))
            ORDER BY position ASC;
        """)
        current_pending_sql = text("""
            SELECT 1 FROM socratic_probes
            WHERE block_id = CAST(:block_id AS UUID)
              AND status IN ('offered', 'deferred')
            LIMIT 1;
        """)
        supersede_sql = text("""
            UPDATE socratic_probes
            SET status = 'superseded', superseded_at = NOW(), updated_at = NOW()
            WHERE block_id = CAST(:block_id AS UUID)
              AND status IN ('offered', 'deferred')
              AND source_block_revision < :block_revision;
        """)
        existing_sql = text("""
            SELECT p.*, r.response_text
            FROM socratic_probes p
            LEFT JOIN socratic_probe_responses r ON r.probe_id = p.probe_id
            WHERE p.block_id = CAST(:block_id AS UUID)
              AND p.source_block_revision = :block_revision
            LIMIT 1;
        """)
        budget_sql = text("""
            SELECT COUNT(*) FROM socratic_probes
            WHERE session_id = CAST(:session_id AS UUID);
        """)
        cooldown_sql = text("""
            SELECT MAX(updated_at) FROM socratic_probes
            WHERE session_id = CAST(:session_id AS UUID)
              AND status IN ('responded', 'deferred', 'dismissed');
        """)
        insert_sql = text("""
            INSERT INTO socratic_probes (
                session_id, document_id, block_id, source_block_revision, claim_fingerprint,
                focus_type, question, concept_id, concept_label, status, generation_metadata
            ) VALUES (
                CAST(:session_id AS UUID), CAST(:document_id AS UUID), CAST(:block_id AS UUID),
                :source_block_revision, :claim_fingerprint, :focus_type, :question,
                :concept_id, :concept_label, 'offered',
                CAST(:generation_metadata AS JSONB)
            ) RETURNING *;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            blocks_result = await session.execute(
                block_sql,
                {"document_id": str(document.document_id), "block_ids": [str(item) for item in request.changed_block_ids]},
            )
            blocks = blocks_result.mappings().all()
            if not blocks:
                raise SocraticProbeValidationError("None of the requested document blocks belong to this session.")
            budget_result = await session.execute(budget_sql, {"session_id": str(session_info["session_id"])})
            remaining_budget = max(0, settings.FIOSRA_PROBE_SESSION_BUDGET - int(budget_result.scalar() or 0))
            cooldown_result = await session.execute(cooldown_sql, {"session_id": str(session_info["session_id"])})
            last_transition = cooldown_result.scalar()
            now = datetime.now(UTC)
            cooldown_active = bool(
                last_transition
                and now - last_transition < timedelta(seconds=settings.FIOSRA_PROBE_COOLDOWN_SECONDS)
            )
            candidates: list[dict[str, Any]] = []
            for block in blocks:
                if block["block_type"] not in ("paragraph", "blockquote") or block["author_type"] != "student":
                    continue
                updated_at = block["updated_at"]
                if updated_at and now - updated_at < timedelta(seconds=settings.FIOSRA_PROBE_QUIET_SECONDS):
                    continue
                focus_type = self._select_focus(block["plaintext"])
                if not focus_type:
                    continue
                await session.execute(
                    supersede_sql,
                    {"block_id": str(block["block_id"]), "block_revision": block["revision"]},
                )
                existing = await session.execute(
                    existing_sql,
                    {"block_id": str(block["block_id"]), "block_revision": block["revision"]},
                )
                if existing.mappings().first():
                    continue
                pending = await session.execute(current_pending_sql, {"block_id": str(block["block_id"])})
                if pending.scalar():
                    continue
                candidates.append(dict(block) | {"focus_type": focus_type})
            await session.commit()

        created: list[SocraticProbeCard] = []
        availability_notice: str | None = None
        if not cooldown_active and remaining_budget:
            for block in candidates[:remaining_budget]:
                concepts = await self._concepts_for_claim(
                    session_info["assignment_id"], block["plaintext"]
                )
                if not concepts:
                    continue
                concept = concepts[0]
                section_label = self._section_label(assignment, block["section_id"])
                generation = await llm_orchestrator.enhance(
                    purpose="socratic_concept_probe",
                    system_prompt=(
                        'Return JSON only in the form {"question":"one concise question?"}. '
                        "Write exactly one concise, answer-blind Socratic question ending in one question mark. "
                        "Ask how or why the causal relationship in the learner's own claim works. Test conceptual "
                        "understanding, never factual recall. Do not name an historical actor not in the learner claim, "
                        "ask for an event's impact, answer, evaluate, grade, give a conclusion, introduce unprovided "
                        "facts, or quote a source. Begin with 'How did' or 'Why did'. Directly name one specific "
                        "mechanism and one outcome from the learner's claim; do not use meta-phrases such as 'the "
                        "stated relationship' or 'relate to the concept'."
                    ),
                    user_prompt=(
                        f"Teacher-approved concept: {concept['label']}\n"
                        f"Learner claim: {block['plaintext'][:900]}\n"
                        f"Conceptual focus: {block['focus_type']}\n"
                        "Ask one how-or-why question about the stated relationship, not about recalling history."
                    ),
                    deterministic_fallback="",
                    pseudonymous_seed=f"probe:{document.document_id}:{block['block_id']}:{block['revision']}",
                    max_characters=260,
                    max_tokens=48,
                    allow_live=True,
                    request_timeout_seconds=12.0,
                    response_format={"type": "json_object"},
                )
                if not generation.metadata.used_live_provider:
                    availability_notice = (
                        "Writing help is temporarily unavailable. Your work was saved; keep drafting and try again later."
                    )
                    continue
                question = self._single_live_question(generation.content)
                if not question:
                    availability_notice = (
                        "Writing help returned an unusable question. Your work was saved; keep drafting and try again later."
                    )
                    continue
                async with AsyncSessionLocal() as session:
                    try:
                        inserted = await session.execute(
                            insert_sql,
                            {
                                "session_id": str(session_info["session_id"]),
                                "document_id": str(document.document_id),
                                "block_id": str(block["block_id"]),
                                "source_block_revision": block["revision"],
                                "claim_fingerprint": self._claim_fingerprint(block["plaintext"]),
                                "focus_type": block["focus_type"],
                                "question": question,
                                "concept_id": concept["concept_id"],
                                "concept_label": concept["label"],
                                "generation_metadata": json.dumps(self._metadata(generation)),
                            },
                        )
                        row = inserted.mappings().one()
                        await session.commit()
                    except Exception as error:  # Database uniqueness resolves concurrent evaluate calls.
                        await session.rollback()
                        if "unique" in str(error).lower():
                            continue
                        raise
                card = self._card(dict(row) | {"claim_text": block["plaintext"]}, section_label)
                created.append(card)
                await event_store.log_event(
                    session_id=session_info["session_id"],
                    student_id=session_info["student_id"],
                    assignment_id=session_info["assignment_id"],
                    question_id=session_info["current_question_id"],
                    event_type="socratic_probe_offered",
                    payload={
                        "probe_id": str(card.probe_id),
                        "document_id": str(card.document_id),
                        "block_id": str(card.block_id),
                        "source_block_revision": card.source_block_revision,
                        "focus_type": card.focus_type,
                        "concept_id": card.concept_id,
                        "generation_metadata": card.generation_metadata.model_dump(),
                    },
                )

        pending = await self.list_probes(session_id, access_token)
        return ProbeEvaluationResponse(
            document_revision=document.document_revision,
            created=created,
            pending=pending.probes,
            evidence_summary=pending.evidence_summary,
            availability_notice=availability_notice,
        )

    async def _get_owned_probe(
        self,
        session_id: UUID | str,
        access_token: str | None,
        probe_id: UUID | str,
    ) -> tuple[dict[str, Any], Any, Any, dict[str, Any]]:
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        probe_sql = text("""
            SELECT p.*, b.section_id, b.plaintext AS claim_text, r.response_text
            FROM socratic_probes p
            JOIN learning_document_blocks b ON b.block_id = p.block_id
            LEFT JOIN socratic_probe_responses r ON r.probe_id = p.probe_id
            WHERE p.probe_id = CAST(:probe_id AS UUID)
              AND p.session_id = CAST(:session_id AS UUID)
              AND p.document_id = CAST(:document_id AS UUID);
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                probe_sql,
                {
                    "probe_id": str(probe_id),
                    "session_id": str(session_info["session_id"]),
                    "document_id": str(document.document_id),
                },
            )
            row = result.mappings().first()
        if not row:
            raise SocraticProbeAccessError("This question does not belong to the requested learning session.")
        return session_info, assignment, document, dict(row)

    async def submit_response(
        self,
        session_id: UUID | str,
        access_token: str | None,
        probe_id: UUID | str,
        request: SubmitProbeResponseRequest,
    ) -> ProbeDispositionResponse:
        """Record a learner-authored response as evidence submitted, not demonstrated mastery."""
        session_info, assignment, _, row = await self._get_owned_probe(session_id, access_token, probe_id)
        if row["status"] not in ("offered", "deferred"):
            raise SocraticProbeConflictError("This question is no longer accepting a learner response.")
        response_text = request.response_text.strip()
        response_sql = text("""
            INSERT INTO socratic_probe_responses (probe_id, response_text)
            VALUES (CAST(:probe_id AS UUID), :response_text)
            ON CONFLICT (probe_id) DO UPDATE
            SET response_text = EXCLUDED.response_text,
                response_revision = socratic_probe_responses.response_revision + 1,
                updated_at = NOW();
        """)
        update_sql = text("""
            UPDATE socratic_probes
            SET status = 'responded', responded_at = NOW(), deferred_until = NULL, updated_at = NOW()
            WHERE probe_id = CAST(:probe_id AS UUID)
            RETURNING *;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(response_sql, {"probe_id": str(probe_id), "response_text": response_text})
            result = await session.execute(update_sql, {"probe_id": str(probe_id)})
            updated = result.mappings().one()
            await session.commit()
        updated = dict(updated) | {"response_text": response_text}
        card = self._card(updated, self._section_label(assignment, row["section_id"]))
        await event_store.log_event(
            session_id=session_info["session_id"],
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="socratic_probe_response_submitted",
            payload={"probe_id": str(card.probe_id), "block_id": str(card.block_id), "evidence_state": "evidence_submitted"},
        )
        return ProbeDispositionResponse(
            probe=card,
            message="Your response was saved as evidence for educator review. It is not an automatic grade.",
        )

    async def defer_probe(
        self,
        session_id: UUID | str,
        access_token: str | None,
        probe_id: UUID | str,
    ) -> ProbeDispositionResponse:
        """Defer an open question without interrupting the learner's document."""
        session_info, assignment, _, row = await self._get_owned_probe(session_id, access_token, probe_id)
        if row["status"] in ("responded", "dismissed", "superseded", "expired"):
            return ProbeDispositionResponse(
                probe=self._card(row, self._section_label(assignment, row["section_id"])),
                message="This question is already closed.",
            )
        deferred_until = datetime.now(UTC) + timedelta(seconds=settings.FIOSRA_PROBE_COOLDOWN_SECONDS)
        update_sql = text("""
            UPDATE socratic_probes
            SET status = 'deferred', deferred_until = :deferred_until, updated_at = NOW()
            WHERE probe_id = CAST(:probe_id AS UUID)
            RETURNING *;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update_sql, {"probe_id": str(probe_id), "deferred_until": deferred_until}
            )
            updated = result.mappings().one()
            await session.commit()
        card = self._card(updated, self._section_label(assignment, row["section_id"]))
        await event_store.log_event(
            session_id=session_info["session_id"],
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="socratic_probe_deferred",
            payload={"probe_id": str(card.probe_id), "block_id": str(card.block_id)},
        )
        return ProbeDispositionResponse(
            probe=card,
            message="Question saved for later. Your document remains fully editable.",
        )

    async def dismiss_probe(
        self,
        session_id: UUID | str,
        access_token: str | None,
        probe_id: UUID | str,
    ) -> ProbeDispositionResponse:
        """Close a question transparently without an automatic grade consequence."""
        session_info, assignment, _, row = await self._get_owned_probe(session_id, access_token, probe_id)
        if row["status"] in ("responded", "dismissed", "superseded", "expired"):
            return ProbeDispositionResponse(
                probe=self._card(row, self._section_label(assignment, row["section_id"])),
                message="This question is already closed.",
            )
        update_sql = text("""
            UPDATE socratic_probes
            SET status = 'dismissed', dismissed_at = NOW(), updated_at = NOW()
            WHERE probe_id = CAST(:probe_id AS UUID)
            RETURNING *;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(update_sql, {"probe_id": str(probe_id)})
            updated = result.mappings().one()
            await session.commit()
        card = self._card(updated, self._section_label(assignment, row["section_id"]))
        await event_store.log_event(
            session_id=session_info["session_id"],
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="socratic_probe_dismissed",
            payload={"probe_id": str(card.probe_id), "block_id": str(card.block_id)},
        )
        return ProbeDispositionResponse(
            probe=card,
            message="Question dismissed. The related claim remains without a response record for review; no automatic penalty is applied.",
        )

    async def trace_records(self, session_id: UUID | str) -> list[ProbeTraceRecord]:
        """Return an internal evaluator projection with question/response content and no model prompts."""
        trace_sql = text("""
            SELECT p.*, b.section_id, b.plaintext AS claim_text, r.response_text
            FROM socratic_probes p
            JOIN learning_document_blocks b ON b.block_id = p.block_id
            LEFT JOIN socratic_probe_responses r ON r.probe_id = p.probe_id
            WHERE p.session_id = CAST(:session_id AS UUID)
            ORDER BY p.offered_at ASC;
        """)
        from fiosra.mvp.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(trace_sql, {"session_id": str(session_id)})
            rows = result.mappings().all()
        return [
            ProbeTraceRecord(
                probe_id=row["probe_id"],
                block_id=row["block_id"],
                section_label=row["section_id"] or "Student writing",
                focus_type=row["focus_type"],
                question=row["question"],
                concept_id=row.get("concept_id"),
                concept_label=row.get("concept_label"),
                status=row["status"],
                evidence_state="evidence_submitted" if row["response_text"] else "unverified",
                offered_at=row["offered_at"],
                response_text=row["response_text"],
                responded_at=row["responded_at"],
                deferred_until=row["deferred_until"],
                generation_metadata=self._parse_metadata(row["generation_metadata"]),
            )
            for row in rows
        ]

    async def classify_sentences(
        self,
        session_id: UUID | str,
        access_token: str | None,
        request: EpistemicClassifyRequest,
    ) -> EpistemicClassifyResponse:
        """Classify each sentence's epistemic function and generate targeted Socratic questions via LLM."""
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        raw_text = request.text.strip()
        if not raw_text:
            return EpistemicClassifyResponse(sentences=[])

        # 1. Segment sentences (split on terminal punctuation followed by space)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_text) if s.strip()]
        if not sentences:
            sentences = [raw_text]

        # 2. Build course source context and task prompt
        task_prompt = ""
        source_excerpts = []
        if assignment and assignment.published:
            if assignment.published.task:
                task_prompt = assignment.published.task.prompt
            if assignment.published.source_pack:
                for source in assignment.published.source_pack:
                    source_excerpts.append(f"- {source.title}: {source.excerpt[:220]}")
        elif assignment and getattr(assignment, "prompt", None):
            task_prompt = assignment.prompt
        source_context = "\n".join(source_excerpts) if source_excerpts else "No specific course source pack."

        # 3. Deterministic fallback classification
        fallback_results: list[SentenceClassification] = []
        has_prior_evidence = False
        for s in sentences:
            s_lower = s.lower()
            is_evidence = bool(
                re.search(r"\b(?:source|evidence|report|study|data|observed|according to)\b", s_lower)
                or re.search(r'[“"”].+?[“"”]', s)
            )
            is_causal = bool(re.search(r"\b(?:because|leads? to|results? in|causes?|mechanism|due to|explains? why)\b", s_lower))
            is_assumption = bool(re.search(r"\b(?:assume|presume|suppose|inherently|naturally|obviously|inevitable)\b", s_lower))
            is_premature = bool(
                re.search(r"\b(?:therefore|thus|hence|in conclusion|consequently|clearly proves?)\b", s_lower)
                and not has_prior_evidence
            )

            if is_evidence:
                has_prior_evidence = True
                fallback_results.append(SentenceClassification(
                    sentence=s,
                    epistemic_type="evidence",
                    confidence=0.95,
                    source_grounded=True,
                ))
            elif is_premature:
                fallback_results.append(SentenceClassification(
                    sentence=s,
                    epistemic_type="premature_closure",
                    confidence=0.92,
                    oracle_probe=f"You conclude '{s[:65]}...', but what specific evidence in your document has already justified this leap?",
                    premature_leap_reason="Conclusion asserted without prior evidence established in this section.",
                ))
            elif is_assumption:
                fallback_results.append(SentenceClassification(
                    sentence=s,
                    epistemic_type="assumption",
                    confidence=0.88,
                    oracle_probe=f"What unstated premise must hold true for '{s[:65]}...', and what happens if that condition fails?",
                ))
            elif is_causal:
                fallback_results.append(SentenceClassification(
                    sentence=s,
                    epistemic_type="reasoning",
                    confidence=0.90,
                    oracle_probe="What specific mechanism or evidence demonstrates that this cause produces the described outcome?",
                ))
            else:
                fallback_results.append(SentenceClassification(
                    sentence=s,
                    epistemic_type="claim",
                    confidence=0.85,
                    oracle_probe=f"What empirical detail connects '{s[:65]}...' to verified evidence, and how would you defend it?",
                ))

        # 4. Attempt LLM Socratic Agent classification & bespoke probe generation
        try:
            prompt_input = json.dumps([{"sentence": s} for s in sentences])
            system_prompt = (
                "You are Socrates, the dialectical Oracle in an elite reasoning academy. "
                "For each sentence, classify its epistemic function into one of:\n"
                "- 'claim': A defensible assertion, thesis, or factual claim requiring warrant.\n"
                "- 'evidence': Direct primary source observation, quotation, data, or empirical citation.\n"
                "- 'reasoning': Causal mechanism or connective warrant connecting evidence to claim.\n"
                "- 'assumption': Implicit presupposition taken for granted (e.g. 'inherently', 'naturally').\n"
                "- 'premature_closure': Reaching a sweeping conclusion without sufficient evidence established in the text.\n\n"
                "SOCRATIC PROBE DIRECTIVES (MANDATORY):\n"
                "1. NEVER use generic boilerplate (e.g. 'What evidence grounds this claim?'). Generic questions are strictly forbidden.\n"
                "2. DIRECTLY QUOTE or INTERROGATE the specific concepts, entities, metrics, or causal relations from the student's exact sentence.\n"
                "   - If the student writes 'The Surrender and Regrant policy achieved immediate peaceful assimilation', ask:\n"
                "     'How does your assertion of immediate peaceful assimilation account for the disinheritance of collateral kinsmen under primogeniture?'\n"
                "   - If the student writes 'Therefore Gaelic resistance was completely broken by 1543', ask:\n"
                "     'Does the submission of individual dynastic lords justify concluding that resistance was broken, or does it overlook clan communal tenures?'\n"
                "3. For non-evidence sentences, provide a sharp, intellectually demanding Socratic question in 'oracle_probe' (one sentence ending with '?').\n"
                "Output strictly a valid JSON array of objects with keys: sentence, epistemic_type, confidence, oracle_probe, source_grounded."
            )
            user_prompt = (
                f"Assignment task prompt: {task_prompt[:400]}\n"
                f"Course primary sources:\n{source_context[:700]}\n"
                f"Sentences to evaluate:\n{prompt_input}"
            )
            generation = await llm_orchestrator.enhance(
                purpose="epistemic_sentence_classification",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                deterministic_fallback=json.dumps([r.model_dump() for r in fallback_results]),
                pseudonymous_seed=f"epistemic:{session_id}:{hashlib.sha256(raw_text.encode()).hexdigest()[:16]}",
                max_characters=4500,
                max_tokens=1200,
                allow_live=True,
            )
            raw_content = generation.content.strip()
            if raw_content.startswith("```"):
                raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)
                raw_content = re.sub(r"\n?```$", "", raw_content)
            parsed = json.loads(raw_content)
            if isinstance(parsed, list) and len(parsed) > 0:
                classified_sentences = []
                for item in parsed:
                    if isinstance(item, dict) and "sentence" in item:
                        classified_sentences.append(SentenceClassification(
                            sentence=str(item.get("sentence", "")),
                            epistemic_type=item.get("epistemic_type", "claim"),
                            confidence=float(item.get("confidence", 0.9)),
                            oracle_probe=item.get("oracle_probe"),
                            source_grounded=bool(item.get("source_grounded", False)),
                        ))
                if classified_sentences:
                    return EpistemicClassifyResponse(sentences=classified_sentences)
        except Exception:
            pass  # Fall back gracefully to deterministic multi-signal classification

        return EpistemicClassifyResponse(sentences=fallback_results)

    async def inquire_sentence(
        self,
        session_id: UUID | str,
        access_token: str | None,
        request: SentenceInquireRequest,
    ) -> SentenceInquireResponse:
        """Execute a bespoke on-demand Socratic Dialectic Agent examination on an individual sentence."""
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        target_sentence = request.sentence.strip()
        surrounding = (request.surrounding_context or "").strip()
        move_type = request.move_type

        # Build assignment & source context
        task_prompt = ""
        source_context = ""
        if assignment and assignment.published:
            if assignment.published.task:
                task_prompt = assignment.published.task.prompt
            if assignment.published.source_pack:
                source_context = "\n".join(
                    f"- {s.title}: {s.excerpt[:240]}" for s in assignment.published.source_pack
                )
        elif assignment and getattr(assignment, "prompt", None):
            task_prompt = assignment.prompt

        try:
            system_prompt = (
                "You are the Socratic Oracle, an elite dialectical tutor examining a student's drafted sentence. "
                "Your objective is to produce a bespoke, intellectually rigorous Socratic inquiry that engages deeply "
                "with the student's exact words, concepts, and logical structure.\n\n"
                "STRICT RULES:\n"
                "- NEVER ask generic questions (e.g. 'What evidence connects this assertion to reality?').\n"
                "- Directly mention and interrogate the specific terms, concepts, metrics, and relationships in the student's sentence.\n"
                "- Tailor the inquiry to the requested move_type:\n"
                "  * 'challenge': Identify the most vulnerable link in the claim and challenge it with an alternative possibility.\n"
                "  * 'why_ladder': Push into the 'why'—demand the missing intermediate causal mechanism.\n"
                "  * 'assumptions': Expose the unspoken assumption the student took for granted and test what happens if it fails.\n"
                "  * 'source': Interrogate how the claim holds up against the assigned course sources.\n"
                "  * 'counterfactual': Pose a concrete counter-scenario where this assertion would be falsified.\n"
                "  * 'creative': Pose a provocative lateral thought experiment, counter-intuitive metaphor, or unexpected analogy to nudge the student into seeing the concept from a fresh angle.\n"
                "- Output strictly a JSON object with keys:\n"
                "  * 'oracle_probe': One sharp, intellectually demanding Socratic question ending with '?'.\n"
                "  * 'targeted_vulnerability': A brief phrase (under 10 words) summarizing the core weakness.\n"
                "  * 'socratic_moves': An array of 3 specific, actionable suggestions for the student to improve the argument."
            )
            user_prompt = (
                f"Assignment Prompt: {task_prompt}\n"
                f"Primary Sources Available:\n{source_context}\n"
                f"Surrounding Paragraph Context: {surrounding}\n"
                f"Student's Exact Sentence: \"{target_sentence}\"\n"
                f"Epistemic Classification: {request.epistemic_type}\n"
                f"Requested Socratic Move: {move_type}\n"
                f"Oracle Pressure Level: {request.oracle_pressure}\n"
            )

            generation = await llm_orchestrator.enhance(
                purpose="socratic_agent_sentence_inquiry",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                deterministic_fallback="",
                pseudonymous_seed=f"inquire:{session_id}:{hashlib.sha256(target_sentence.encode()).hexdigest()[:16]}:{move_type}",
                max_characters=2500,
                max_tokens=600,
                allow_live=True,
                response_format={"type": "json_object"},
            )
            if not generation.metadata.used_live_provider:
                raise SocraticModelUnavailableError("The Socratic Enquirer is unavailable. Your draft has not changed; please try again shortly.")
            raw_content = generation.content.strip()
            if raw_content.startswith("```"):
                raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)
                raw_content = re.sub(r"\n?```$", "", raw_content)
            parsed = json.loads(raw_content)
            if isinstance(parsed, dict) and parsed.get("oracle_probe"):
                return SentenceInquireResponse(
                    sentence=target_sentence,
                    epistemic_type=request.epistemic_type,
                    oracle_probe=str(parsed["oracle_probe"]).strip(),
                    move_type=move_type,
                    socratic_moves=[str(m) for m in parsed.get("socratic_moves", [])],
                    targeted_vulnerability=parsed.get("targeted_vulnerability"),
                )
            raise SocraticModelUnavailableError("The Socratic Enquirer returned an invalid response. Your draft has not changed; please try again shortly.")
        except SocraticModelUnavailableError:
            raise
        except Exception as exc:
            logger.warning("Sentence inquiry model request failed: %s", exc)
            raise SocraticModelUnavailableError("The Socratic Enquirer is unavailable. Your draft has not changed; please try again shortly.") from exc

    async def dialectical_turn(
        self,
        session_id: UUID | str,
        access_token: str | None,
        request: DialecticalTurnRequest,
    ) -> DialecticalTurnResponse:
        """Evaluate student's dialectical defense of a sentence and return Oracle's next inquiry or satisfaction."""
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        target_sentence = request.sentence.strip()
        student_reply = request.student_reply.strip()
        surrounding = (request.surrounding_context or "").strip()
        move_type = request.move_type

        # 1. Build assignment, scope & rubric context
        task_prompt = ""
        task_scope = ""
        rubric_context = ""
        source_context = ""
        target_kcs_info: list[str] = []

        if assignment and assignment.published:
            if assignment.published.task:
                task_prompt = assignment.published.task.prompt
                task_scope = getattr(assignment.published.task, "scope", "") or ""
            if assignment.published.public_rubric:
                rubric_context = "\n".join(
                    f"- Rubric '{r.title}': {r.description}" for r in assignment.published.public_rubric
                )
            if assignment.published.source_pack:
                source_context = "\n".join(
                    f"- Assigned Source '{s.title}': {s.excerpt}" for s in assignment.published.source_pack
                )
        elif assignment and getattr(assignment, "prompt", None):
            task_prompt = assignment.prompt

        # 2. Dynamic pgvector RAG Search across course materials
        course_id = session_info.get("course_id")
        module_id = session_info.get("module_id") or getattr(assignment, "module_id", None)
        if course_id:
            try:
                search_query = f"{target_sentence} {student_reply}"
                rag_results = await syllabus_parser.search_syllabus(
                    course_id=course_id,
                    query=search_query,
                    module_id=module_id,
                    top_k=3,
                )
                if rag_results:
                    rag_lines = [f"- Primary Source '{r.title}': {r.content[:360]}" for r in rag_results]
                    source_context = "\n".join(rag_lines)
            except Exception as e:
                logger.debug("pgvector RAG search notice: %s", e)

        # 3. Dynamic Neo4j Target KC & Prerequisite Traversal
        target_kc_ids: list[str] = []
        if assignment and getattr(assignment, "target_kcs", None):
            target_kc_ids = assignment.target_kcs
        elif assignment and getattr(assignment, "published", None) and getattr(assignment.published, "target_kcs", None):
            target_kc_ids = assignment.published.target_kcs

        if target_kc_ids:
            try:
                from fiosra.mvp.neo4j_client import neo4j_client

                cypher = """
                UNWIND $kc_ids AS kid
                MATCH (k:Concept {concept_id: kid})
                OPTIONAL MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(k)
                RETURN k.label AS label, k.definition AS definition, collect(prereq.label) AS prereqs
                """
                async with neo4j_client.get_session() as g_sess:
                    g_res = await g_sess.run(cypher, {"kc_ids": [str(x) for x in target_kc_ids]})
                    records = await g_res.data()
                    for rec in records:
                        p_str = ", ".join(rec["prereqs"]) if rec["prereqs"] else "None (Foundational)"
                        target_kcs_info.append(f"- Concept '{rec['label']}': {rec['definition']} (Prerequisite: {p_str})")
            except Exception as e:
                logger.debug("Neo4j KC fetch notice: %s", e)

        # 4. Recognize explicit dialogue continuations without substituting a
        # deterministic reply. The learner should receive either a live,
        # context-aware response or the explicit model-unavailable state.
        cleaned_reply = student_reply.strip().lower().rstrip(".!?,")
        requests_continuation = cleaned_reply in {
            "tell me",
            "go on",
            "say more",
            "keep going",
            "explain more",
            "what do you mean",
            "how so",
        }

        # Scope is handled through grounded assistance, not a fixed vocabulary
        # blacklist that only works for one seeded history course.
        is_drift = False

        cmd_text = student_reply.strip().lower()
        brainstorms_structure = bool(
            re.search(
                r"\b(?:brainstorm\w*|high[- ]?level|big[- ]?picture|concept\w*|ponder\w*)\b",
                cmd_text,
            )
            and re.search(r"\b(?:structur\w*|outline\w*|organis\w*|section\w*|plan\w*)\b", cmd_text)
        )
        requests_assignment_structure = bool(
            re.search(
                r"\b(?:start|begin|help|draft\w*|write|build|plan|organis\w*|structure|outline)\b.{0,48}"
                r"\b(?:assignment|essay|paper|response|canvas|draft)\b"
                r"|\b(?:assignment|essay|paper|response|canvas|draft)\b.{0,48}"
                r"\b(?:start|begin|help|draft\w*|write|build|plan|organis\w*|structure|outline)\b",
                cmd_text,
            )
        )
        requests_canvas_update = bool(
            re.search(
                r"\b(?:update|add|put|insert|apply|populate)\b.{0,48}"
                r"\b(?:canvas|assignment|essay|paper|response|draft|outline|section)\b",
                cmd_text,
            )
        )
        asks_for_source_reference = bool(
            re.search(
                r"\b(?:give|show|find|need|want|which|what)\b.{0,36}\b(?:source|sources|reference|references|citation|citations)\b"
                r"|\b(?:source|sources|reference|references|citation|citations)\b.{0,36}\b(?:for|to)\b",
                cmd_text,
            )
            or re.search(
                r"\b(?:any|some)\s+(?:source|sources|reference|references|citation|citations)\b",
                cmd_text,
            )
        )
        is_brainstorm_tool = cmd_text.startswith("/brainstorm")
        permits_canvas_structure = (
            requests_assignment_structure
            or requests_canvas_update
            or cmd_text.startswith("/structure")
        )

        if is_drift:
            return DialecticalTurnResponse(
                oracle_reply=(
                    "How does this idea connect to the assignment’s stated scope and the materials your educator provided?"
                ),
                is_satisfied=False,
                satisfaction_reason="The inquiry needs to reconnect with the assignment scope.",
                current_probe_category="challenge",
                suggested_revision=None,
                epistemic_progress=0.20,
                socratic_moves=["Revisit the task", "Check a provided source"],
                helper_action=None,
                interactive_actions=[],
            )

        if asks_for_source_reference:
            source_titles = []
            if assignment and assignment.published and assignment.published.source_pack:
                source_titles = [source.title for source in assignment.published.source_pack[:3]]
            source_label = ", ".join(source_titles) if source_titles else "the assigned materials"
            return DialecticalTurnResponse(
                oracle_reply=(
                    f"Open {source_label}. Choose a passage that bears on your developing idea, then note what it shows before deciding what it supports."
                ),
                is_satisfied=False,
                satisfaction_reason="The learner asked to inspect course materials.",
                current_probe_category="source",
                suggested_revision=None,
                epistemic_progress=0.1,
                socratic_moves=["Open an assigned source", "Record one observation in your own words"],
                helper_action=None,
                interactive_actions=[
                    EpistemicToolAction(
                        label="Open assigned materials",
                        action_type="cite_source",
                        icon="↗",
                        payload={},
                    )
                ],
            )

        # Build dynamic tool directive based on slash command
        tool_directive = ""
        current_category = "challenge"

        if brainstorms_structure or requests_assignment_structure:
            current_category = "creative"
            tool_directive = (
                "\n\n*** SPECIAL TOOL MODE: ASSIGNMENT STRUCTURE PROPOSAL ***\n"
                f"The learner wants to begin or organize their assignment: '{student_reply.strip()}'.\n"
                "Create exactly two distinct, assignment-specific ways to organize the analysis. Each option must have exactly three short analytical section headings and one brief explanation of the comparison or tension it helps the learner investigate.\n"
                "Stay at the level of analytical concepts and relationships. Do not provide an introduction, conclusion, thesis, summary, historical verdict, or model answer. Do not quote or restate the assignment brief. Use only the supplied assignment context and material excerpts."
            )
        elif requests_canvas_update:
            current_category = "creative"
            tool_directive = (
                "\n\n*** SPECIAL TOOL MODE: CANVAS STRUCTURE PROPOSAL ***\n"
                "The learner wants a canvas update. Propose 2–4 concise, assignment-specific analytical section headings in "
                "'helper_delegation' with action='scaffold_sections'. The canvas helper will create empty sections only after "
                "the learner explicitly accepts the proposal. Do not write factual content, a thesis, or a model answer into the canvas."
            )
        elif requests_continuation:
            current_category = "creative"
            tool_directive = (
                "\n\n*** SPECIAL TOOL MODE: CONTINUE THE CURRENT PLANNING THREAD ***\n"
                "Continue directly from the immediately preceding Fiosra response in the conversation history. "
                "Clarify its most useful analytical choice or tension in two or three concise sentences, then ask "
                "which route the learner would like to develop. Do not reset the conversation, repeat a previous "
                "question verbatim, provide a model answer, or introduce a new factual claim."
            )
        elif is_brainstorm_tool:
            current_category = "creative"
            brainstorm_arg = re.sub(r"^/brainstorm\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = brainstorm_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: BRAINSTORM ***\n"
                f"The learner wants to explore: '{topic}'.\n"
                "Offer two or three distinct course-grounded analytical routes or tensions to investigate, then end with one clear question asking which route the learner wants to pursue. Do not invent facts, sources, conclusions, or a model answer."
            )
        elif cmd_text.startswith("/hint"):
            current_category = "source"
            hint_arg = re.sub(r"^/hint\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = hint_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: EVIDENTIARY HINT ***\n"
                f"The student requested an EVIDENTIARY HINT regarding: '{topic}'.\n"
                "Under answer-blindness, identify the provided material that is most useful to inspect and ask what detail the learner should look for.\n"
                "Do not name material that does not appear in the supplied source context."
            )
        elif cmd_text.startswith("/structure"):
            current_category = "source"
            struct_arg = re.sub(r"^/structure\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = struct_arg or task_prompt
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: ASSIGNMENT STRUCTURE ***\n"
                f"The student requested to STRUCTURE the assignment: '{topic}'.\n"
                "Propose a concise, assignment-specific outline with 2–4 section titles. In 'helper_delegation', set action='scaffold_sections' and include those titles. The learner will see the proposal and must explicitly choose whether to add it to the canvas."
            )
        elif cmd_text.startswith("/assumptions"):
            current_category = "assumptions"
            assump_arg = re.sub(r"^/assumptions\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = assump_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: EXPOSE ASSUMPTIONS ***\n"
                f"The student requested an ASSUMPTION ANALYSIS of: '{topic}'.\n"
                "Identify at most two assumptions or reasoning gaps using neutral language, then ask which one the learner wants to investigate."
            )
        elif cmd_text.startswith("/counter"):
            current_category = "counterfactual"
            counter_arg = re.sub(r"^/counter\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = counter_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: STEELMANNED COUNTER-ARGUMENT ***\n"
                f"The student requested a COUNTER-ARGUMENT against: '{topic}'.\n"
                "Offer one plausible alternative interpretation grounded only in the assignment context, then ask what material could help the learner compare the two interpretations."
            )
        elif cmd_text.startswith("/why"):
            current_category = "why_ladder"
            why_arg = re.sub(r"^/why\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = why_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: WHY-LADDER CAUSAL PROBE ***\n"
                f"The student requested a WHY-LADDER probe on: '{topic}'.\n"
                "Ask one progressive causal question at a time. Start with the immediate connection before moving to deeper mechanisms."
            )
        elif cmd_text.startswith("/falsify"):
            current_category = "challenge"
            falsify_arg = re.sub(r"^/falsify\s*", "", student_reply, flags=re.IGNORECASE).strip()
            topic = falsify_arg or target_sentence
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: FALSIFICATION TEST ***\n"
                f"The student requested a FALSIFICATION TEST for: '{topic}'.\n"
                "Ask what observation or material from the provided sources would make the learner revise their current interpretation."
            )
        elif cmd_text.startswith("/mode"):
            mode_arg = re.sub(r"^/mode\s*", "", student_reply, flags=re.IGNORECASE).strip().lower()
            tool_directive = (
                f"\n\n*** SPECIAL TOOL MODE: SWITCH MODE ***\n"
                f"The student switched the reasoning lens to '{mode_arg}'. Acknowledge the switch and explain how this lens evaluates the current inquiry."
            )

        try:
            formatted_history = "\n".join(
                f"{m.role.capitalize()}: {m.content}" for m in request.history
            )
            if (
                brainstorms_structure
                or requests_assignment_structure
                or requests_canvas_update
                or is_brainstorm_tool
            ):
                if requests_assignment_structure or requests_canvas_update:
                    response_contract = (
                        "a JSON object with section_titles (an array of exactly three distinct, course-specific "
                        "analytical headings) and reasoning_focus (one sentence describing the conceptual tension "
                        "these headings let the learner investigate)"
                    )
                elif brainstorms_structure:
                    response_contract = (
                        "a JSON object with one key, outline_options. Its value must be an array of exactly two "
                        "objects. Each object must contain title (a short course-specific route name), section_titles "
                        "(an array of exactly three course-specific analytical headings), and reasoning_focus (one "
                        "sentence explaining the analytical tension)."
                    )
                else:
                    response_contract = (
                        '{"oracle_reply":"One concise, answer-blind response",'
                        '"helper_delegation":null,"interactive_actions":[]}'
                    )
                system_prompt = (
                    "Help a learner make a concrete next decision about the structure of their own assignment.\n"
                    "Be direct and brief: 120 words maximum. Never give a finished answer, thesis, conclusion, or invented source.\n"
                    "Obey the special tool mode precisely. Never repeat the assignment prompt or explain your role.\n"
                    "Every option and heading must be substantively different. Placeholder labels, generic process "
                    "labels, and copied output-instruction words are invalid.\n\n"
                    f"Return strict JSON only as {response_contract}"
                )
                user_prompt = (
                    f"{tool_directive}\n\n"
                    f"Assignment task: {task_prompt or 'Not yet specified'}\n"
                    f"Scope: {task_scope or 'Not yet specified'}\n"
                    f"Provided materials:\n{source_context}\n"
                    f"Student's Inquiry: \"{student_reply}\"\n"
                )
            else:
                system_prompt = (
                    "You are the Socratic Enquirer: a concise, supportive learning partner helping a learner complete their assignment.\n\n"
                    "OPERATING RULES:\n"
                    "1. Help the learner decide their own argument, evidence, and wording. Never provide a finished answer or write their work for them.\n"
                    "2. Ground every factual suggestion in the supplied assignment and material excerpts. If the material does not support an answer, say what the learner could inspect.\n"
                    f"3. Keep the inquiry within the stated scope: {task_scope or 'the assignment scope'}.\n"
                    "4. Ask one useful next question or offer one small next step. Do not interrogate, score, or require a response.\n"
                    "5. When the learner explicitly asks for an outline, return a helper_delegation with action='scaffold_sections'. It is only a proposal: the learner must explicitly accept it before the canvas changes.\n"
                    "6. Never generate an insert_claim helper_delegation. The learner remains author of their prose.\n"
                    "7. Return at most one optional interactive action, and only when it materially helps the learner.\n\n"
                    "Return strict JSON only in this compact form:\n"
                    "{\n"
                    '  "oracle_reply": "One concise, answer-blind response",\n'
                    '  "helper_delegation": {"action": "scaffold_sections", "section_titles": ["Section one", "Section two"], "target_page": 1} or null,\n'
                    '  "interactive_actions": []\n'
                    "}"
                )
                if requests_continuation:
                    system_prompt += (
                        "\n\nFor the current continuation request, return exactly one concise planning question. "
                        "It must help the learner choose an analytical direction from the immediately preceding "
                        "assistant message. Do not answer that message. Do not state historical facts, explain a "
                        "policy, name an event, or provide a causal conclusion."
                    )
                user_prompt = (
                    f"{tool_directive}\n\n"
                    f"Assignment Prompt: {task_prompt}\n"
                    f"Assignment scope: {task_scope}\n"
                    f"Visible rubric expectations:\n{rubric_context}\n"
                    f"Relevant curriculum concepts:\n{chr(10).join(target_kcs_info) if target_kcs_info else 'No concept map is available.'}\n"
                    f"Provided material excerpts:\n{source_context}\n"
                    f"Draft context: {surrounding}\n"
                    f"Selected text or task: \"{target_sentence}\"\n"
                    f"Conversation so far:\n{formatted_history}\n"
                    f"Learner message: \"{student_reply}\"\n"
                    f"Requested lens: {move_type}\n"
                )

            seed = f"turn:{session_id}:{hashlib.sha256(student_reply.encode()).hexdigest()[:16]}:{len(request.history)}"
            output_token_budget = (
                260
                if (
                    brainstorms_structure
                    or requests_assignment_structure
                    or requests_canvas_update
                    or is_brainstorm_tool
                )
                else 140
                if requests_continuation
                else 180
            )
            parsed: dict[str, Any] | None = None
            requires_response_repair = requests_continuation or is_brainstorm_tool
            for attempt in range(2 if requires_response_repair else 1):
                generation = await llm_orchestrator.enhance(
                    purpose="socratic_agent_dialectical_turn",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    deterministic_fallback="",
                    pseudonymous_seed=f"{seed}:attempt:{attempt + 1}",
                    # JSON framing means a 120-word response can safely exceed the
                    # visible-reply length. Keep the generation short, while allowing
                    # enough room for its required structured envelope.
                    max_characters=1600,
                    max_tokens=output_token_budget,
                    allow_live=True,
                    request_timeout_seconds=25.0,
                    response_format={"type": "json_object"},
                )
                if not generation.metadata.used_live_provider:
                    raise SocraticModelUnavailableError(
                        "The Socratic Enquirer is unavailable. Your draft has not changed; please try again shortly."
                    )
                raw_content = generation.content.strip()
                if raw_content.startswith("```"):
                    raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)
                    raw_content = re.sub(r"\n?```$", "", raw_content)
                try:
                    candidate = json.loads(raw_content)
                except json.JSONDecodeError:
                    candidate = None

                if not requires_response_repair:
                    parsed = candidate
                    break

                candidate_reply = (
                    str(candidate.get("oracle_reply", "")).strip()
                    if isinstance(candidate, dict)
                    else ""
                )
                is_valid_continuation = (
                    requests_continuation
                    and candidate_reply.count("?") == 1
                    and len(candidate_reply) <= 420
                )
                is_valid_brainstorm = (
                    is_brainstorm_tool
                    and 1 <= candidate_reply.count("?") <= 4
                    and candidate_reply.rstrip().endswith("?")
                    and len(candidate_reply) <= 900
                )
                if is_valid_continuation or is_valid_brainstorm:
                    parsed = candidate
                    break
                if attempt == 0:
                    if requests_continuation:
                        logger.info("Repairing an invalid Socratic continuation response before returning it to the learner.")
                        system_prompt += (
                            "\n\nYour prior output did not meet the continuation contract. Correct it now: return valid JSON, "
                            "with exactly one concise planning question in oracle_reply and no explanation or factual answer."
                        )
                    else:
                        logger.info("Repairing an invalid brainstorming response before returning it to the learner.")
                        system_prompt += (
                            "\n\nYour prior output did not meet the brainstorming contract. Correct it now: return valid JSON, "
                            "provide two or three concise analytical routes or tensions, and end oracle_reply with one question asking which route the learner wants to pursue."
                        )
                    continue
                if requests_continuation:
                    raise SocraticModelUnavailableError(
                        "Writing help could not produce a valid follow-up after retrying. Your draft has not changed; please try again shortly."
                    )
                raise SocraticModelUnavailableError(
                    "Writing help could not produce a valid brainstorm after retrying. Your draft has not changed; please try again shortly."
                )

            if not isinstance(parsed, dict):
                raise SocraticModelUnavailableError(
                    "The Socratic Enquirer returned an invalid response. Your draft has not changed; please try again shortly."
                )
            if (requests_assignment_structure or requests_canvas_update) and isinstance(parsed, dict):
                raw_titles = parsed.get("section_titles")
                if not isinstance(raw_titles, list):
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable section proposal. Your draft has not changed; please try again shortly."
                    )
                section_titles = [str(title).strip() for title in raw_titles if str(title).strip()]
                invalid_titles = {
                    "first analytical section",
                    "second analytical section",
                    "third analytical section",
                }
                if (
                    len(section_titles) != 3
                    or len({title.casefold() for title in section_titles}) != 3
                    or any(title.casefold() in invalid_titles for title in section_titles)
                ):
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable section proposal. Your draft has not changed; please try again shortly."
                    )
                helper_action = canvas_scribe_helper.generate_section_blocks(
                    session_id,
                    section_titles=section_titles,
                    target_page=1,
                )
                return DialecticalTurnResponse(
                    oracle_reply=(
                        "I have prepared three empty sections for you to review. "
                        "Nothing changes until you choose Add proposed sections."
                    ),
                    is_satisfied=False,
                    satisfaction_reason="A learner-approved canvas structure is ready for review.",
                    current_probe_category="creative",
                    suggested_revision=None,
                    epistemic_progress=0.2,
                    socratic_moves=["Review the section proposal", "Choose whether to add it"],
                    helper_action=helper_action,
                    interactive_actions=[],
                )
            if isinstance(parsed, dict) and parsed.get("oracle_reply"):
                oracle_reply = str(parsed["oracle_reply"]).strip()
                if requests_continuation and (oracle_reply.count("?") != 1 or len(oracle_reply) > 420):
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable follow-up. Your draft has not changed; please try again shortly."
                    )
                if brainstorms_structure or requests_assignment_structure:
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable outline proposal. Your draft has not changed; please try again shortly."
                    )
                helper_action = None
                delegation = parsed.get("helper_delegation")
                if (
                    permits_canvas_structure
                    and isinstance(delegation, dict)
                    and delegation.get("action")
                ):
                    action_type = delegation["action"]
                    if action_type == "scaffold_sections" and delegation.get("section_titles"):
                        section_titles = [str(title).strip() for title in delegation["section_titles"]]
                        section_titles = [title for title in section_titles if title][:4]
                        if not section_titles:
                            raise SocraticModelUnavailableError("The assistant returned an unusable outline proposal. Your draft has not changed; please try again shortly.")
                        helper_action = canvas_scribe_helper.generate_section_blocks(
                            session_id,
                            section_titles=section_titles,
                            target_page=delegation.get("target_page", 1),
                        )

                interactive_actions: list[EpistemicToolAction] = []
                raw_actions = parsed.get("interactive_actions")
                if not is_brainstorm_tool and isinstance(raw_actions, list):
                    for act in raw_actions:
                        if isinstance(act, dict) and act.get("label") and act.get("action_type"):
                            icon_val = act.get("icon")
                            if not icon_val:
                                at = act.get("action_type")
                                if at == "scaffold_section":
                                    icon_val = "✦"
                                elif at == "explore_prompt":
                                    icon_val = "💡"
                                elif at == "cite_source":
                                    icon_val = "📜"
                                else:
                                    icon_val = "🔍"
                            interactive_actions.append(
                                EpistemicToolAction(
                                    label=str(act["label"]),
                                    action_type=act["action_type"],
                                    icon=icon_val,
                                    payload=act.get("payload") if isinstance(act.get("payload"), dict) else {},
                                )
                            )

                return DialecticalTurnResponse(
                    oracle_reply=oracle_reply,
                    is_satisfied=bool(parsed.get("is_satisfied", False)),
                    satisfaction_reason=str(parsed.get("satisfaction_reason", "Dialectical evaluation complete.")),
                    current_probe_category=parsed.get("current_probe_category", current_category),
                    suggested_revision=parsed.get("suggested_revision"),
                    epistemic_progress=float(parsed.get("epistemic_progress", 0.35)),
                socratic_moves=[str(m) for m in parsed.get("socratic_moves", ["Inspect a provided source", "Develop the reasoning connection"])],
                    helper_action=helper_action,
                    interactive_actions=interactive_actions,
                )
            if (brainstorms_structure or requests_assignment_structure) and isinstance(parsed, dict):
                raw_options = parsed.get("outline_options")
                if not isinstance(raw_options, list) or len(raw_options) != 2:
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable outline proposal. Your draft has not changed; please try again shortly."
                    )
                outline_options = [OutlineOption.model_validate(option) for option in raw_options]
                normalized_titles = [option.title.strip().casefold() for option in outline_options]
                if len(set(normalized_titles)) != 2:
                    raise SocraticModelUnavailableError(
                        "The assistant returned an unusable outline proposal. Your draft has not changed; please try again shortly."
                    )
                for option in outline_options:
                    sections = [title.strip() for title in option.section_titles]
                    placeholder_terms = {
                        "short option name",
                        "short alternative name",
                        "first analytical section",
                        "second analytical section",
                        "third analytical section",
                    }
                    if len(set(title.casefold() for title in sections)) != 3 or any(
                        re.search(r"\b(?:introduction|conclusion|summary)\b", title, re.IGNORECASE)
                        for title in sections
                    ) or option.title.strip().casefold() in placeholder_terms or any(
                        title.casefold() in placeholder_terms for title in sections
                    ) or "materially different comparison" in option.reasoning_focus.casefold():
                        raise SocraticModelUnavailableError(
                            "The assistant returned an unusable outline proposal. Your draft has not changed; please try again shortly."
                        )
                return DialecticalTurnResponse(
                    oracle_reply="Here are two ways to organize the analysis. Which comparison gives you the clearest direction?",
                    is_satisfied=False,
                    satisfaction_reason="The learner has two answer-blind structures to consider.",
                    current_probe_category="creative",
                    suggested_revision=None,
                    epistemic_progress=0.2,
                    socratic_moves=["Choose one structure", "Inspect a provided source"],
                    helper_action=None,
                    interactive_actions=[],
                    outline_options=outline_options,
                )
        except SocraticModelUnavailableError:
            raise
        except Exception as err:
            logger.warning("Error in dialectical turn LLM generation: %s", err)
            raise SocraticModelUnavailableError("The Socratic Enquirer returned an invalid response. Your draft has not changed; please try again shortly.") from err



socratic_probe_service = SocraticProbeService()
