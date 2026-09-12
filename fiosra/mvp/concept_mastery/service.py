"""Computes and serves the per-student concept mastery overlay.

Neo4j (fiosra.mvp.concepts) owns topology: Concept nodes and their CONTAINS /
PREREQUISITE_OF edges, teacher-governed and slow-changing. Postgres owns mastery: a
deterministic, event-derived cache keyed on (student_id, course_id, concept_id), never
hand-edited and never a second source of truth — `rebuild_course` regenerates it purely
by replaying `grade_finalised_by_educator` events, per the append-only event store
invariant.

Scoring is deliberately conservative for v1: a concept only ever leaves "unassessed"
when a rubric criterion tagged with that concept id was actually graded (direct
evidence only). No inference across PREREQUISITE_OF edges yet — see
docs/knowledge-graph-mastery-plan.md section 6.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from fiosra.mvp.concepts.service import concept_graph_service
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.event_store import event_store

logger = logging.getLogger(__name__)

_OUTCOME_SCORE = {"met": 1.0, "partially_met": 0.5, "not_met": 0.0}
_MAX_STUDENT_TEXT_CHARS = 6000


def _state_for_score(score: float, evidence_count: int) -> str:
    if evidence_count <= 0:
        return "unassessed"
    if score < 0.4:
        return "weak"
    if score < 0.75:
        return "developing"
    return "strong"


class ConceptMasteryService:
    """Maintains and serves the concept_mastery cache table."""

    async def _course_id_for_assignment(self, assignment_id: UUID | str) -> str | None:
        sql = text("""
            SELECT m.course_id
            FROM assignments a
            JOIN modules m ON a.module_id = m.module_id
            WHERE a.assignment_id = CAST(:assignment_id AS UUID);
        """)
        async with AsyncSessionLocal() as session:
            result = await session.execute(sql, {"assignment_id": str(assignment_id)})
            row = result.first()
        return str(row[0]) if row and row[0] else None

    async def _concept_ids_by_criterion(self, assignment_id: UUID | str) -> dict[str, list[str]]:
        """Teacher-only map from a public rubric criterion id to the concepts it assesses."""
        from fiosra.mvp.assignment_designer.generator import assignment_generator

        assignment = await assignment_generator.get_authoring_assignment(assignment_id)
        if not assignment:
            return {}
        rubric_map = (assignment.get("evaluation_plan") or {}).get("public_rubric_map") or []
        return {
            entry["public_criterion_id"]: list(entry.get("concept_ids") or [])
            for entry in rubric_map
            if entry.get("public_criterion_id")
        }

    async def _apply_criterion_grades(
        self,
        student_id: str,
        course_id: str,
        criterion_grades: list[dict[str, Any]],
        concept_ids_by_criterion: dict[str, list[str]],
    ) -> int:
        rows_written = 0
        async with AsyncSessionLocal() as session:
            for grade in criterion_grades:
                criterion_id = grade.get("criterion_id")
                outcome = grade.get("outcome")
                if outcome not in _OUTCOME_SCORE:
                    continue
                outcome_score = _OUTCOME_SCORE[outcome]
                for concept_id in concept_ids_by_criterion.get(criterion_id, []):
                    existing = await session.execute(
                        text("""
                            SELECT score, evidence_count FROM concept_mastery
                            WHERE student_id = :student_id AND course_id = CAST(:course_id AS UUID)
                              AND concept_id = :concept_id
                            FOR UPDATE;
                        """),
                        {"student_id": student_id, "course_id": course_id, "concept_id": concept_id},
                    )
                    row = existing.first()
                    prior_score, prior_count = (float(row[0]), int(row[1])) if row else (0.0, 0)
                    new_count = prior_count + 1
                    new_score = round((prior_score * prior_count + outcome_score) / new_count, 3)
                    new_state = _state_for_score(new_score, new_count)
                    await session.execute(
                        text("""
                            INSERT INTO concept_mastery (
                                student_id, course_id, concept_id, state, score, evidence_count, last_evidence_at, updated_at
                            ) VALUES (
                                :student_id, CAST(:course_id AS UUID), :concept_id, :state, :score, :evidence_count, NOW(), NOW()
                            )
                            ON CONFLICT (student_id, course_id, concept_id) DO UPDATE SET
                                state = EXCLUDED.state,
                                score = EXCLUDED.score,
                                evidence_count = EXCLUDED.evidence_count,
                                last_evidence_at = NOW(),
                                updated_at = NOW();
                        """),
                        {
                            "student_id": student_id,
                            "course_id": course_id,
                            "concept_id": concept_id,
                            "state": new_state,
                            "score": new_score,
                            "evidence_count": new_count,
                        },
                    )
                    rows_written += 1
            await session.commit()
        return rows_written

    async def recompute_for_session(self, session_id: UUID | str) -> int:
        """Applies the latest grade_finalised_by_educator event's criterion grades, if any."""
        session_info = await event_store.get_session_details(session_id)
        if not session_info or not session_info.get("assignment_id"):
            return 0
        events = await event_store.get_session_events(session_id)
        grade_events = [event for event in events if event.get("event_type") == "grade_finalised_by_educator"]
        if not grade_events:
            return 0
        latest = grade_events[-1]
        criterion_grades = (latest.get("payload") or {}).get("criterion_grades") or []
        if not criterion_grades:
            return 0
        course_id = await self._course_id_for_assignment(session_info["assignment_id"])
        if not course_id:
            logger.warning("Session %s's assignment has no course-linked module; skipping mastery update.", session_id)
            return 0
        concept_ids_by_criterion = await self._concept_ids_by_criterion(session_info["assignment_id"])
        rows_written = await self._apply_criterion_grades(
            session_info["student_id"], course_id, criterion_grades, concept_ids_by_criterion
        )
        try:
            await self._extract_and_store_emergent_concepts(session_id, session_info["student_id"], course_id)
        except Exception:  # noqa: BLE001 - emergent-concept extraction is best-effort and must never block grading.
            logger.exception("Emergent concept extraction failed for session %s; mastery scores were still saved.", session_id)
        return rows_written

    # ------------------------------------------------------------------
    # Emergent concepts ("green nodes"): concepts the student mentions in
    # their own work that are NOT part of the teacher's course graph.
    # LLM-assisted and best-effort - never blocks grading, never written
    # into the shared Neo4j course graph. See migrations/010.
    # ------------------------------------------------------------------

    async def _gather_student_text(self, session_id: UUID | str) -> str:
        """Collects the student's own written work for a session from the two places
        it lives today: dialogue turns (session_events) and canvas section drafts.
        Does not yet read the long-form document editor - a known gap, not silent:
        if a course only uses that surface this will return an empty string and
        extraction will simply find nothing, rather than guessing.
        """
        pieces: list[str] = []
        events = await event_store.get_session_events(session_id)
        for event in events:
            if event.get("event_type") == "student_prompt_submitted":
                text_value = (event.get("payload") or {}).get("student_input")
                if text_value:
                    pieces.append(str(text_value))
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT text FROM canvas_section_drafts WHERE session_id = :session_id AND text <> '';"),
                {"session_id": str(session_id)},
            )
            pieces.extend(row[0] for row in result.all())
        combined = "\n\n".join(piece.strip() for piece in pieces if piece and piece.strip())
        return combined[:_MAX_STUDENT_TEXT_CHARS]

    @staticmethod
    def _emergent_json(content: str) -> list[dict[str, Any]] | None:
        """Forgiving parse for a JSON array, tolerant of prose or markdown fences —
        local models routinely wrap structured output despite instructions not to."""
        candidate = content.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, list) else None
        except json.JSONDecodeError:
            start = candidate.find("[")
            if start == -1:
                return None
            try:
                parsed, _ = json.JSONDecoder().raw_decode(candidate[start:])
                return parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                return None

    async def _extract_emergent_concepts(
        self, student_text: str, existing_labels: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Asks the configured model which concepts the student raised that are not
        in the course's existing concept list. Deliberately minimal schema (a bare
        JSON array, no nested response_format contract) since local models via
        Ollama were observed truncating or wrapping richer schemas in prose."""
        from fiosra.mvp.config import settings
        from fiosra.mvp.llm.contracts import CompletionRequest
        from fiosra.mvp.llm.litellm_provider import LiteLLMProvider

        if not student_text.strip() or not existing_labels:
            return []
        system_prompt = (
            "You read one student's own written work for a course and identify concepts they raised "
            "that are NOT already on the course's tracked concept list. Do not list a concept that is "
            "just a rephrasing of one already tracked. Respond with ONLY a JSON array, nothing else, "
            "no markdown fences, no explanation. Each item: "
            '{"label": "short concept name", "related_to": "the closest tracked concept label, or null", '
            '"note": "one short phrase on why it is relevant"}. '
            "If the student raised nothing beyond the tracked list, respond with exactly []."
        )
        user_prompt = (
            "Tracked course concepts:\n" + "\n".join(f"- {label}" for label in existing_labels.values())
            + "\n\nStudent's written work:\n" + student_text
        )
        request = CompletionRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            purpose="student_emergent_concept_extraction",
            max_tokens=500,
            temperature=0.2,
            timeout_seconds=45.0,
        )
        result = await LiteLLMProvider.from_settings().complete(request)
        parsed = self._emergent_json(result.content)
        if parsed is None:
            logger.info(
                "Emergent concept extraction (%s) returned unparseable output; skipping this pass.",
                settings.FIOSRA_LLM_PROVIDER,
            )
            return []
        label_by_lower = {label.lower(): concept_id for concept_id, label in existing_labels.items()}
        cleaned: list[dict[str, Any]] = []
        for item in parsed:
            if not isinstance(item, dict) or not item.get("label"):
                continue
            label = str(item["label"]).strip()[:200]
            if not label or label.lower() in label_by_lower:
                continue
            related_label = str(item.get("related_to") or "").strip().lower()
            cleaned.append(
                {
                    "label": label,
                    "note": str(item.get("note") or "").strip()[:400],
                    "related_concept_id": label_by_lower.get(related_label),
                }
            )
        return cleaned

    async def _extract_and_store_emergent_concepts(
        self, session_id: UUID | str, student_id: str, course_id: str
    ) -> int:
        student_text = await self._gather_student_text(session_id)
        if not student_text:
            return 0
        graph = await concept_graph_service.get_course_graph(course_id)
        existing_labels = {node["concept_id"]: node["label"] for node in graph["nodes"]}
        candidates = await self._extract_emergent_concepts(student_text, existing_labels)
        if not candidates:
            return 0
        rows_written = 0
        async with AsyncSessionLocal() as session:
            for candidate in candidates:
                await session.execute(
                    text("""
                        INSERT INTO student_emergent_concepts (
                            emergent_id, student_id, course_id, session_id, label, context_snippet, related_concept_id
                        ) VALUES (
                            :emergent_id, :student_id, CAST(:course_id AS UUID), CAST(:session_id AS UUID),
                            :label, :context_snippet, :related_concept_id
                        )
                        ON CONFLICT (student_id, course_id, label) DO UPDATE SET
                            context_snippet = EXCLUDED.context_snippet,
                            related_concept_id = COALESCE(EXCLUDED.related_concept_id, student_emergent_concepts.related_concept_id);
                    """),
                    {
                        "emergent_id": str(uuid4()),
                        "student_id": student_id,
                        "course_id": course_id,
                        "session_id": str(session_id),
                        "label": candidate["label"],
                        "context_snippet": candidate["note"],
                        "related_concept_id": candidate["related_concept_id"],
                    },
                )
                rows_written += 1
            await session.commit()
        return rows_written

    async def rebuild_course(self, course_id: UUID | str) -> tuple[int, int]:
        """Recomputes every student's mastery for a course from scratch by replaying events."""
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("DELETE FROM concept_mastery WHERE course_id = CAST(:course_id AS UUID);"),
                {"course_id": str(course_id)},
            )
            await session.commit()
            sessions_result = await session.execute(
                text("""
                    SELECT s.session_id
                    FROM student_sessions s
                    JOIN assignments a ON s.assignment_id = a.assignment_id
                    JOIN modules m ON a.module_id = m.module_id
                    WHERE m.course_id = CAST(:course_id AS UUID);
                """),
                {"course_id": str(course_id)},
            )
            session_ids = [row[0] for row in sessions_result.all()]
        rows_written = 0
        for session_id in session_ids:
            rows_written += await self.recompute_for_session(session_id)
        return len(session_ids), rows_written

    async def get_student_overlay(self, course_id: str, student_id: str) -> dict[str, Any]:
        graph = await concept_graph_service.get_course_graph(course_id)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT concept_id, state, score, evidence_count, last_evidence_at
                    FROM concept_mastery
                    WHERE course_id = CAST(:course_id AS UUID) AND student_id = :student_id;
                """),
                {"course_id": course_id, "student_id": student_id},
            )
            mastery_by_concept = {
                row.concept_id: {
                    "state": row.state,
                    "score": float(row.score),
                    "evidence_count": row.evidence_count,
                    "last_evidence_at": row.last_evidence_at.isoformat() if row.last_evidence_at else None,
                }
                for row in result.mappings().all()
            }
        nodes = [
            {
                **node,
                **mastery_by_concept.get(
                    node["concept_id"],
                    {"state": "unassessed", "score": 0.0, "evidence_count": 0, "last_evidence_at": None},
                ),
            }
            for node in graph["nodes"]
        ]
        emergent_nodes, emergent_edges = await self._get_emergent_overlay(course_id, student_id)
        return {
            "course_id": course_id,
            "student_id": student_id,
            "nodes": nodes,
            "emergent_nodes": emergent_nodes,
            "edges": graph["edges"] + emergent_edges,
        }

    async def _get_emergent_overlay(self, course_id: str, student_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT emergent_id, label, context_snippet, related_concept_id
                    FROM student_emergent_concepts
                    WHERE course_id = CAST(:course_id AS UUID) AND student_id = :student_id
                    ORDER BY created_at ASC;
                """),
                {"course_id": course_id, "student_id": student_id},
            )
            rows = result.mappings().all()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        for row in rows:
            node_id = f"EMERGENT_{row['emergent_id']}"
            nodes.append(
                {
                    "concept_id": node_id,
                    "label": row["label"],
                    "definition": row["context_snippet"] or "",
                    "concept_type": "emergent",
                    "level": "emergent",
                    "state": "emergent",
                    "related_concept_id": row["related_concept_id"],
                }
            )
            if row["related_concept_id"]:
                edges.append({"source": node_id, "target": row["related_concept_id"], "relation": "MENTIONED_ALONGSIDE"})
        return nodes, edges

    async def get_cohort_overlay(self, course_id: str) -> dict[str, Any]:
        graph = await concept_graph_service.get_course_graph(course_id)
        async with AsyncSessionLocal() as session:
            cohort_result = await session.execute(
                text("SELECT COUNT(*) FROM enrollments WHERE course_id = CAST(:course_id AS UUID);"),
                {"course_id": course_id},
            )
            cohort_size = int(cohort_result.scalar() or 0)
            distribution_result = await session.execute(
                text("""
                    SELECT concept_id, state, COUNT(*) AS student_count
                    FROM concept_mastery
                    WHERE course_id = CAST(:course_id AS UUID)
                    GROUP BY concept_id, state;
                """),
                {"course_id": course_id},
            )
            by_concept: dict[str, dict[str, int]] = {}
            for row in distribution_result.mappings().all():
                by_concept.setdefault(row["concept_id"], {}).update({row["state"]: row["student_count"]})
        nodes = []
        for node in graph["nodes"]:
            counts = by_concept.get(node["concept_id"], {})
            assessed = sum(counts.get(state, 0) for state in ("weak", "developing", "strong"))
            nodes.append(
                {
                    **node,
                    "strong": counts.get("strong", 0),
                    "developing": counts.get("developing", 0),
                    "weak": counts.get("weak", 0),
                    "unassessed": max(cohort_size - assessed, 0),
                    "assessed_student_count": assessed,
                    "cohort_size": cohort_size,
                }
            )
        return {"course_id": course_id, "cohort_size": cohort_size, "nodes": nodes, "edges": graph["edges"]}


concept_mastery_service = ConceptMasteryService()
