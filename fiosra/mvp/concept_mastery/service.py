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

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import text

from fiosra.mvp.concepts.service import concept_graph_service
from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.event_store import event_store

logger = logging.getLogger(__name__)

_OUTCOME_SCORE = {"met": 1.0, "partially_met": 0.5, "not_met": 0.0}


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
        return await self._apply_criterion_grades(
            session_info["student_id"], course_id, criterion_grades, concept_ids_by_criterion
        )

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
        return {"course_id": course_id, "student_id": student_id, "nodes": nodes, "edges": graph["edges"]}

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
