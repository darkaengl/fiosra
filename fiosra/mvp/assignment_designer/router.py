from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from fiosra.mvp.assignment_designer.deambiguator import scope_deambiguator
from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.assignment_designer.schemas import (
    AmbiguityDiagnosis,
    AssignmentAuthoringUpdate,
    AssignmentReadiness,
    ClarifyAndScaffoldRequest,
    CompletionSupportRequest,
    CompletionSupportResponse,
    PublicQuestionSpec,
    QuestionDraftRequest,
    QuestionSpec,
    ScaffoldingPlan,
    ScopeAnalysisRequest,
)

router = APIRouter(prefix="/assignments", tags=["Assignment Designer & Co-Pilot"])


class PublishRequest(BaseModel):
    module_id: UUID | None = Field(default=None, description="Optional curriculum module ID to bind assignment")


class PublishResponse(BaseModel):
    assignment_id: str
    module_id: str | None
    title: str
    status: str


@router.post("/analyze-scope", response_model=AmbiguityDiagnosis)
async def analyze_assignment_scope(request: ScopeAnalysisRequest) -> AmbiguityDiagnosis:
    """Evaluate an educator prompt and return alignment questions when it is underspecified."""
    return scope_deambiguator.evaluate_prompt_ambiguity(
        raw_prompt=request.raw_prompt,
        domain=request.domain,
        course_id=request.course_id,
        module_id=request.module_id,
    )


@router.post("/clarify-and-scaffold", response_model=ScaffoldingPlan)
async def clarify_and_generate_scaffolding(request: ClarifyAndScaffoldRequest) -> ScaffoldingPlan:
    """Generate an answer-blind four-rung hint ladder and verifiable rubric rules."""
    return await assignment_generator.generate_scaffolding_plan(request)


@router.post("/draft", response_model=QuestionSpec)
async def draft_assignment_question(request: QuestionDraftRequest) -> QuestionSpec:
    """Draft and persist an assignment while storing its reference solution only in the Answer Vault."""
    return await assignment_generator.draft_question(request)


@router.get("", response_model=list[PublicQuestionSpec])
async def list_assignments(
    course_id: Annotated[UUID | None, Query()] = None,
    module_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[PublicQuestionSpec]:
    """List student-safe assignment specifications for a course or module."""
    return await assignment_generator.list_public_assignments(
        course_id=course_id,
        module_id=module_id,
        status=status,
    )


@router.get("/{assignment_id}", response_model=PublicQuestionSpec)
async def get_assignment(assignment_id: UUID) -> PublicQuestionSpec:
    """Fetch a student-safe assignment specification with no reference-solution access material."""
    assignment = await assignment_generator.get_public_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment '{assignment_id}' not found.")
    return assignment


@router.post("/{assignment_id}/support", response_model=CompletionSupportResponse)
async def get_completion_support(
    assignment_id: UUID,
    request: CompletionSupportRequest,
) -> CompletionSupportResponse:
    """Return student-selected, completion-oriented help from the published contract."""
    assignment = await assignment_generator.get_public_assignment(assignment_id)
    if not assignment or assignment.status != "published":
        raise HTTPException(status_code=404, detail="Published assignment not found.")
    try:
        return CompletionSupportResponse(
            **assignment_generator.completion_support(assignment, request.action_id, request.document_excerpt)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{assignment_id}/authoring")
async def get_assignment_authoring(assignment_id: UUID) -> dict[str, Any]:
    """Return the teacher-only public contract, private evaluation plan, and readiness state."""
    assignment = await assignment_generator.get_authoring_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment '{assignment_id}' not found.")
    return assignment


@router.put("/{assignment_id}/authoring")
async def update_assignment_authoring(
    assignment_id: UUID,
    request: AssignmentAuthoringUpdate,
) -> dict[str, Any]:
    """Save teacher-approved public and private assignment contracts."""
    assignment = await assignment_generator.update_authoring_assignment(
        assignment_id,
        request.published,
        request.evaluation_plan,
        request.canvas_sections,
    )
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment '{assignment_id}' not found.")
    return assignment


@router.get("/{assignment_id}/readiness", response_model=AssignmentReadiness)
async def get_assignment_readiness(assignment_id: UUID) -> AssignmentReadiness:
    """Return actionable teacher-facing publication checks."""
    assignment = await assignment_generator.get_authoring_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment '{assignment_id}' not found.")
    return AssignmentReadiness(**assignment["readiness"])


@router.post("/{assignment_id}/publish", response_model=PublishResponse)
async def publish_assignment(
    assignment_id: UUID,
    request: PublishRequest | None = None,
) -> dict[str, Any]:
    """Publish an assignment and optionally bind it to a curriculum module."""
    module_id = request.module_id if request else None
    try:
        return await assignment_generator.publish_assignment(
            assignment_id=assignment_id,
            module_id=module_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
