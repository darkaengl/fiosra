import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.assignment_designer.schemas import PublicQuestionSpec
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.event_store import event_store
from fiosra.mvp.learning_canvas_schemas import (
    AcceptSuggestionRequest,
    CanvasActionResponse,
    CanvasSectionDefinition,
    CanvasSectionDraft,
    CanvasSourceReference,
    CanvasStateResponse,
    CanvasSuggestion,
    CreateSuggestionRequest,
    DismissSuggestionRequest,
    SaveCanvasSectionRequest,
    SaveCanvasSectionResponse,
)


class CanvasAccessError(PermissionError):
    """Raised when a session capability does not authorize a canvas request."""


class CanvasConflictError(RuntimeError):
    """Raised when a learner attempts to apply an outdated canvas revision."""


class CanvasValidationError(ValueError):
    """Raised for invalid session, section, source, or suggestion actions."""


class LearningCanvasService:
    """Durable, student-owned CER canvas with explicit assistance lifecycle."""

    async def _get_authorized_context(
        self,
        session_id: UUID | str,
        access_token: str | None,
    ) -> tuple[dict[str, Any], PublicQuestionSpec]:
        if not await event_store.has_session_access(session_id, access_token):
            raise CanvasAccessError("This browser is not authorized to access the reasoning canvas.")
        session_info = await event_store.get_session_details(session_id)
        if not session_info or not session_info.get("assignment_id"):
            raise CanvasValidationError("This canvas session is not linked to a published assignment.")
        assignment = await assignment_generator.get_public_assignment(session_info["assignment_id"])
        if not assignment or assignment.status != "published":
            raise CanvasValidationError("The session's published assignment is no longer available.")
        return session_info, assignment

    @staticmethod
    def _section(assignment: PublicQuestionSpec, section_id: str) -> CanvasSectionDefinition:
        for section in assignment.canvas_sections:
            if section.section_id == section_id:
                return section
        raise CanvasValidationError(f"Section '{section_id}' is not part of this assignment canvas.")

    @staticmethod
    def _allowed_chunk_ids(assignment: PublicQuestionSpec) -> set[str]:
        return {str(source.chunk_id) for source in assignment.grounding_sources}

    @classmethod
    def _validate_source_references(
        cls,
        assignment: PublicQuestionSpec,
        source_references: list[CanvasSourceReference],
    ) -> None:
        sources_by_id = {str(source.chunk_id): source for source in assignment.grounding_sources}
        invalid = [str(ref.chunk_id) for ref in source_references if str(ref.chunk_id) not in sources_by_id]
        if invalid:
            raise CanvasValidationError(
                "Every selected source must be one of this assignment's approved grounding sources."
            )
        for reference in source_references:
            excerpt = sources_by_id[str(reference.chunk_id)].excerpt
            if reference.quote and reference.quote.casefold() not in excerpt.casefold():
                raise CanvasValidationError(
                    "A selected quotation must be present in the approved assignment source excerpt."
                )

    @staticmethod
    def _draft_from_row(row: Any, section_id: str) -> CanvasSectionDraft:
        if not row:
            return CanvasSectionDraft(section_id=section_id)
        references = row["source_references"]
        if isinstance(references, str):
            references = json.loads(references)
        return CanvasSectionDraft(
            section_id=section_id,
            text=row["text"],
            revision=row["revision"],
            author_type=row["author_type"],
            source_references=references or [],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _suggestion_from_row(row: Any) -> CanvasSuggestion:
        return CanvasSuggestion(
            suggestion_id=str(row["suggestion_id"]),
            session_id=str(row["session_id"]),
            section_id=row["section_id"],
            kind=row["kind"],
            content=row["content"],
            base_revision=row["base_revision"],
            status=row["status"],
            created_at=row["created_at"],
        )

    async def get_state(self, session_id: UUID | str, access_token: str | None) -> CanvasStateResponse:
        session_info, assignment = await self._get_authorized_context(session_id, access_token)
        query_sql = text("""
            SELECT section_id, text, source_references, author_type, revision, updated_at
            FROM canvas_section_drafts
            WHERE session_id = :session_id;
        """)
        suggestions_sql = text("""
            SELECT suggestion_id, session_id, section_id, kind, content, base_revision, status, created_at
            FROM canvas_suggestions
            WHERE session_id = :session_id AND status = 'offered'
            ORDER BY created_at ASC;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(query_sql, {"session_id": str(session_id)})
            rows = {row["section_id"]: row for row in result.mappings().all()}
            suggestions_result = await session.execute(suggestions_sql, {"session_id": str(session_id)})
            suggestions = [
                self._suggestion_from_row(row) for row in suggestions_result.mappings().all()
            ]
        sections = sorted(assignment.canvas_sections, key=lambda section: section.position)
        drafts = [self._draft_from_row(rows.get(section.section_id), section.section_id) for section in sections]
        return CanvasStateResponse(
            session_id=str(session_id),
            assignment_id=assignment.assignment_id,
            status=session_info["status"],
            sections=sections,
            drafts=drafts,
            suggestions=suggestions,
        )

    async def save_section(
        self,
        session_id: UUID | str,
        section_id: str,
        access_token: str | None,
        request: SaveCanvasSectionRequest,
    ) -> SaveCanvasSectionResponse:
        session_info, assignment = await self._get_authorized_context(session_id, access_token)
        section = self._section(assignment, section_id)
        if session_info["status"] != "active":
            raise CanvasConflictError("Submitted or completed sessions cannot be changed.")
        if len(request.text) > section.max_characters:
            raise CanvasValidationError(
                f"'{section.label}' is limited to {section.max_characters} characters."
            )
        self._validate_source_references(assignment, request.source_references)
        references_json = json.dumps([reference.model_dump(mode="json") for reference in request.source_references])
        select_sql = text("""
            SELECT text, source_references, author_type, revision, updated_at
            FROM canvas_section_drafts
            WHERE session_id = :session_id AND section_id = :section_id
            FOR UPDATE;
        """)
        insert_sql = text("""
            INSERT INTO canvas_section_drafts (
                session_id, section_id, text, source_references, author_type, revision, updated_at
            ) VALUES (
                CAST(:session_id AS UUID), :section_id, :text, CAST(:source_references AS JSONB),
                :author_type, 1, NOW()
            ) RETURNING section_id, text, source_references, author_type, revision, updated_at;
        """)
        update_sql = text("""
            UPDATE canvas_section_drafts
            SET text = :text,
                source_references = CAST(:source_references AS JSONB),
                author_type = :author_type,
                revision = revision + 1,
                updated_at = NOW()
            WHERE session_id = CAST(:session_id AS UUID) AND section_id = :section_id
            RETURNING section_id, text, source_references, author_type, revision, updated_at;
        """)
        async with AsyncSessionLocal() as session:
            current_result = await session.execute(
                select_sql, {"session_id": str(session_id), "section_id": section_id}
            )
            current = current_result.mappings().first()
            current_revision = int(current["revision"]) if current else 0
            if current_revision != request.base_revision:
                raise CanvasConflictError(
                    "This section changed in another tab. Reload the canvas before saving your revision."
                )
            statement = update_sql if current else insert_sql
            result = await session.execute(
                statement,
                {
                    "session_id": str(session_id),
                    "section_id": section_id,
                    "text": request.text.strip(),
                    "source_references": references_json,
                    "author_type": request.author_type,
                },
            )
            row = result.mappings().one()
            await session.commit()
        draft = self._draft_from_row(row, section_id)
        await event_store.log_event(
            session_id=session_id,
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="canvas_section_saved",
            payload={
                "section_id": section_id,
                "revision": draft.revision,
                "author_type": draft.author_type,
                "source_chunk_ids": [str(reference.chunk_id) for reference in draft.source_references],
            },
        )
        return SaveCanvasSectionResponse(session_id=str(session_id), **draft.model_dump())

    @staticmethod
    def _deterministic_suggestion(
        section: CanvasSectionDefinition,
        request: CreateSuggestionRequest,
        assignment: PublicQuestionSpec,
    ) -> str:
        if request.kind == "writing_frame":
            return (
                f"Writing frame: I currently claim that ___. The course evidence I will test is ___. "
                f"{section.completion_guidance}"
            )
        if request.kind == "source_reminder":
            titles = ", ".join(source.title for source in assignment.grounding_sources[:2])
            return f"Return to the approved course source{'s' if len(assignment.grounding_sources) > 1 else ''}: {titles}. What direct observation belongs here?"
        return f"{section.completion_guidance} What is one precise sentence you can write in your own words?"

    async def create_suggestion(
        self,
        session_id: UUID | str,
        access_token: str | None,
        request: CreateSuggestionRequest,
    ) -> CanvasSuggestion:
        session_info, assignment = await self._get_authorized_context(session_id, access_token)
        section = self._section(assignment, request.section_id)
        if session_info["status"] != "active":
            raise CanvasConflictError("Submitted or completed sessions cannot receive canvas suggestions.")
        if request.kind not in section.allowed_suggestion_kinds:
            raise CanvasValidationError("This suggestion type is not permitted for the selected section.")
        revision_sql = text("""
            SELECT revision FROM canvas_section_drafts
            WHERE session_id = :session_id AND section_id = :section_id;
        """)
        pending_suggestion_sql = text("""
            SELECT suggestion_id FROM canvas_suggestions
            WHERE session_id = CAST(:session_id AS UUID)
              AND section_id = :section_id
              AND status = 'offered'
            FOR UPDATE;
        """)
        async with AsyncSessionLocal() as session:
            revision_result = await session.execute(
                revision_sql, {"session_id": str(session_id), "section_id": request.section_id}
            )
            current_revision = int(revision_result.scalar() or 0)
            pending_result = await session.execute(
                pending_suggestion_sql,
                {"session_id": str(session_id), "section_id": request.section_id},
            )
            if pending_result.scalar():
                raise CanvasConflictError(
                    "Resolve or dismiss the existing optional support card before requesting another."
                )
        if current_revision != request.base_revision:
            raise CanvasConflictError("This section changed before the suggestion was prepared. Reload and try again.")
        content = self._deterministic_suggestion(section, request, assignment)
        insert_sql = text("""
            INSERT INTO canvas_suggestions (session_id, section_id, kind, content, base_revision, status)
            VALUES (CAST(:session_id AS UUID), :section_id, :kind, :content, :base_revision, 'offered')
            RETURNING suggestion_id, session_id, section_id, kind, content, base_revision, status, created_at;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                insert_sql,
                {
                    "session_id": str(session_id),
                    "section_id": request.section_id,
                    "kind": request.kind,
                    "content": content,
                    "base_revision": request.base_revision,
                },
            )
            row = result.mappings().one()
            await session.commit()
        suggestion = self._suggestion_from_row(row)
        await event_store.log_event(
            session_id=session_id,
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="canvas_suggestion_offered",
            payload={
                "suggestion_id": suggestion.suggestion_id,
                "section_id": suggestion.section_id,
                "kind": suggestion.kind,
                "base_revision": suggestion.base_revision,
                "generation_metadata": {
                    "provider": "deterministic",
                    "model": "deterministic",
                    "used_live_provider": False,
                },
            },
        )
        return suggestion

    async def accept_suggestion(
        self,
        session_id: UUID | str,
        suggestion_id: UUID | str,
        access_token: str | None,
        request: AcceptSuggestionRequest,
    ) -> CanvasActionResponse:
        session_info, assignment = await self._get_authorized_context(session_id, access_token)
        if session_info["status"] != "active":
            raise CanvasConflictError("Submitted or completed sessions cannot apply canvas suggestions.")
        if not request.text.strip():
            raise CanvasValidationError("Write your own section text before applying the suggestion.")
        suggestion_sql = text("""
            SELECT suggestion_id, session_id, section_id, kind, content, base_revision, status, created_at
            FROM canvas_suggestions
            WHERE suggestion_id = CAST(:suggestion_id AS UUID) AND session_id = CAST(:session_id AS UUID)
            FOR UPDATE;
        """)
        current_draft_sql = text("""
            SELECT revision FROM canvas_section_drafts
            WHERE session_id = CAST(:session_id AS UUID) AND section_id = :section_id
            FOR UPDATE;
        """)
        update_draft_sql = text("""
            INSERT INTO canvas_section_drafts (
                session_id, section_id, text, source_references, author_type, revision, updated_at
            ) VALUES (
                CAST(:session_id AS UUID), :section_id, :text, CAST(:source_references AS JSONB),
                'student_edited_assistance', 1, NOW()
            ) ON CONFLICT (session_id, section_id) DO UPDATE
            SET text = EXCLUDED.text,
                source_references = EXCLUDED.source_references,
                author_type = 'student_edited_assistance',
                revision = canvas_section_drafts.revision + 1,
                updated_at = NOW()
            RETURNING section_id, text, source_references, author_type, revision, updated_at;
        """)
        accept_sql = text("""
            UPDATE canvas_suggestions
            SET status = 'accepted', acted_at = NOW()
            WHERE suggestion_id = CAST(:suggestion_id AS UUID) AND status = 'offered'
            RETURNING suggestion_id, session_id, section_id, kind, content, base_revision, status, created_at;
        """)
        self._validate_source_references(assignment, request.source_references)
        references_json = json.dumps([reference.model_dump(mode="json") for reference in request.source_references])
        async with AsyncSessionLocal() as session:
            suggestion_result = await session.execute(
                suggestion_sql,
                {"suggestion_id": str(suggestion_id), "session_id": str(session_id)},
            )
            suggestion_row = suggestion_result.mappings().first()
            if not suggestion_row:
                raise CanvasValidationError("The requested suggestion does not exist in this canvas session.")
            if suggestion_row["status"] != "offered":
                raise CanvasConflictError("This suggestion has already been handled.")
            section = self._section(assignment, suggestion_row["section_id"])
            if len(request.text) > section.max_characters:
                raise CanvasValidationError(
                    f"'{section.label}' is limited to {section.max_characters} characters."
                )
            draft_result = await session.execute(
                current_draft_sql,
                {"session_id": str(session_id), "section_id": suggestion_row["section_id"]},
            )
            current_revision = int(draft_result.scalar() or 0)
            if current_revision != suggestion_row["base_revision"]:
                raise CanvasConflictError("This section changed after the suggestion was offered. Reload before applying it.")
            draft_result = await session.execute(
                update_draft_sql,
                {
                    "session_id": str(session_id),
                    "section_id": suggestion_row["section_id"],
                    "text": request.text.strip(),
                    "source_references": references_json,
                },
            )
            accepted_result = await session.execute(accept_sql, {"suggestion_id": str(suggestion_id)})
            accepted_row = accepted_result.mappings().first()
            if not accepted_row:
                raise CanvasConflictError("This suggestion was handled in another tab. Reload the canvas.")
            draft_row = draft_result.mappings().one()
            await session.commit()
        suggestion = self._suggestion_from_row(accepted_row)
        draft = self._draft_from_row(draft_row, suggestion.section_id)
        await event_store.log_event(
            session_id=session_id,
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="canvas_suggestion_accepted",
            payload={
                "suggestion_id": suggestion.suggestion_id,
                "section_id": suggestion.section_id,
                "kind": suggestion.kind,
                "base_revision": suggestion.base_revision,
                "result_revision": draft.revision,
                "author_type": draft.author_type,
            },
        )
        return CanvasActionResponse(suggestion=suggestion, draft=draft)

    async def dismiss_suggestion(
        self,
        session_id: UUID | str,
        suggestion_id: UUID | str,
        access_token: str | None,
        request: DismissSuggestionRequest,
    ) -> CanvasActionResponse:
        session_info, _assignment = await self._get_authorized_context(session_id, access_token)
        if session_info["status"] != "active":
            raise CanvasConflictError("Submitted or completed sessions cannot dismiss canvas suggestions.")
        update_sql = text("""
            UPDATE canvas_suggestions
            SET status = 'dismissed', acted_at = NOW()
            WHERE suggestion_id = CAST(:suggestion_id AS UUID)
              AND session_id = CAST(:session_id AS UUID)
              AND status = 'offered'
            RETURNING suggestion_id, session_id, section_id, kind, content, base_revision, status, created_at;
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                update_sql,
                {"suggestion_id": str(suggestion_id), "session_id": str(session_id)},
            )
            row = result.mappings().first()
            if not row:
                raise CanvasConflictError("This suggestion has already been handled or does not exist.")
            await session.commit()
        suggestion = self._suggestion_from_row(row)
        await event_store.log_event(
            session_id=session_id,
            student_id=session_info["student_id"],
            assignment_id=session_info["assignment_id"],
            question_id=session_info["current_question_id"],
            event_type="canvas_suggestion_dismissed",
            payload={
                "suggestion_id": suggestion.suggestion_id,
                "section_id": suggestion.section_id,
                "kind": suggestion.kind,
                "reason": request.reason,
            },
        )
        return CanvasActionResponse(suggestion=suggestion)


learning_canvas_service = LearningCanvasService()
