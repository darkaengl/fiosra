"""Server-authoritative proactive Socratic probe lifecycle for learner documents."""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.config import settings
from fiosra.mvp.event_store import event_store
from fiosra.mvp.learning_document_service import (
    LearningDocumentAccessError,
    LearningDocumentConflictError,
    LearningDocumentValidationError,
    learning_document_service,
)
from fiosra.mvp.llm.orchestrator import GuardedGeneration, llm_orchestrator
from fiosra.mvp.socratic_probe_schemas import (
    ProbeDispositionResponse,
    ProbeEvaluationRequest,
    ProbeEvaluationResponse,
    ProbeListResponse,
    ProbeTraceRecord,
    SocraticProbeCard,
    SubmitProbeResponseRequest,
)


class SocraticProbeAccessError(PermissionError):
    """Raised when a probe request does not own the targeted learning session."""


class SocraticProbeConflictError(RuntimeError):
    """Raised when a probe action conflicts with authoritative document/session state."""


class SocraticProbeValidationError(ValueError):
    """Raised when a probe action violates a learning workflow invariant."""


class SocraticProbeService:
    """Offer one bounded question per stable learner-authored paragraph revision."""

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

    @classmethod
    def _select_focus(cls, plaintext: str) -> str | None:
        """Choose one deterministic question focus only for a substantive proposition."""
        normalized = " ".join(plaintext.split())
        if len(normalized) < settings.FIOSRA_PROBE_MIN_MATERIAL_CHARACTERS:
            return None
        if not cls._CLAIM_RE.search(normalized):
            return None
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
            status=row["status"],
            evidence_state="evidence_submitted" if row.get("response_text") else "unverified",
            offered_at=row["offered_at"],
            deferred_until=row.get("deferred_until"),
            response_text=row.get("response_text"),
            responded_at=row.get("responded_at"),
            generation_metadata=metadata,
        )

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
            SELECT p.*, b.section_id, r.response_text, r.updated_at AS response_updated_at
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
                focus_type, question, status, generation_metadata
            ) VALUES (
                CAST(:session_id AS UUID), CAST(:document_id AS UUID), CAST(:block_id AS UUID),
                :source_block_revision, :claim_fingerprint, :focus_type, :question, 'offered',
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
        if not cooldown_active and remaining_budget:
            for block in candidates[:remaining_budget]:
                fallback = self._FOCUS_QUESTIONS[block["focus_type"]]
                section_label = self._section_label(assignment, block["section_id"])
                generation = await llm_orchestrator.enhance(
                    purpose="socratic_probe_rephrase",
                    system_prompt=(
                        "You are a concise Socratic tutor. Output exactly one supportive question ending in a single "
                        "question mark. Rephrase only the supplied server-selected question. Do not answer, explain, "
                        "write, solve, evaluate, quote a source, assign a grade, or introduce any people, events, facts, "
                        "or concepts beyond the supplied public assignment title, heading label, and question."
                    ),
                    user_prompt=(
                        f"Public assignment prompt: {assignment.prompt[:360]}\n"
                        f"Active heading: {section_label}\n"
                        f"Server-selected Socratic question: {fallback}"
                    ),
                    deterministic_fallback=fallback,
                    pseudonymous_seed=f"probe:{document.document_id}:{block['block_id']}:{block['revision']}",
                    max_characters=260,
                    max_tokens=90,
                    allow_live=assignment.grounding_mode == "course_grounded",
                )
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
                                "question": generation.content,
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
                card = self._card(row, section_label)
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
                        "generation_metadata": card.generation_metadata.model_dump(),
                    },
                )

        pending = await self.list_probes(session_id, access_token)
        return ProbeEvaluationResponse(
            document_revision=document.document_revision,
            created=created,
            pending=pending.probes,
            evidence_summary=pending.evidence_summary,
        )

    async def _get_owned_probe(
        self,
        session_id: UUID | str,
        access_token: str | None,
        probe_id: UUID | str,
    ) -> tuple[dict[str, Any], Any, Any, dict[str, Any]]:
        session_info, assignment, document = await self._authorized_context(session_id, access_token)
        probe_sql = text("""
            SELECT p.*, b.section_id, r.response_text
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
            SELECT p.*, b.section_id, r.response_text
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


socratic_probe_service = SocraticProbeService()
