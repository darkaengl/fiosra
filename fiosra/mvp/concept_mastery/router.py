"""Educator-facing endpoints for the per-student concept mastery overlay.

Mounted under the same prefix as the course concept graph, since this is a read (and
rebuild) view over that graph rather than a separate resource.

NOTE: like every other educator router in this codebase (concepts, courses,
evidence_dossier, authoring, assignment_designer), this has no auth yet. It is flagged
in docs/knowledge-graph-mastery-plan.md section 8 as higher-priority to fix than most,
since it exposes individual students' per-concept performance.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from fiosra.mvp.concept_mastery.schemas import (
    CohortConceptMasteryResponse,
    MasteryRebuildResponse,
    StudentConceptMasteryResponse,
)
from fiosra.mvp.concept_mastery.service import concept_mastery_service
from fiosra.mvp.courses.service import course_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses/{course_id}/concept-graph/mastery", tags=["Concept Mastery"])


async def _course_or_404(course_id: UUID):
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    return course


@router.get("/students/{student_id}", response_model=StudentConceptMasteryResponse)
async def get_student_mastery(course_id: UUID, student_id: str) -> StudentConceptMasteryResponse:
    """Return the course concept graph with one student's mastery state on every node."""
    await _course_or_404(course_id)
    overlay = await concept_mastery_service.get_student_overlay(str(course_id), student_id)
    return StudentConceptMasteryResponse(**overlay)


@router.get("/cohort", response_model=CohortConceptMasteryResponse)
async def get_cohort_mastery(course_id: UUID) -> CohortConceptMasteryResponse:
    """Return the course concept graph with cohort-wide mastery distribution per node."""
    await _course_or_404(course_id)
    overlay = await concept_mastery_service.get_cohort_overlay(str(course_id))
    return CohortConceptMasteryResponse(**overlay)


@router.post("/rebuild", response_model=MasteryRebuildResponse)
async def rebuild_course_mastery(course_id: UUID) -> MasteryRebuildResponse:
    """Recompute this course's mastery cache from scratch by replaying graded sessions."""
    await _course_or_404(course_id)
    sessions_replayed, rows_written = await concept_mastery_service.rebuild_course(str(course_id))
    return MasteryRebuildResponse(
        course_id=str(course_id), sessions_replayed=sessions_replayed, rows_written=rows_written
    )
