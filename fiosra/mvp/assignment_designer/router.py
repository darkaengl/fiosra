from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fiosra.mvp.assignment_designer.deambiguator import scope_deambiguator
from fiosra.mvp.assignment_designer.generator import assignment_generator
from fiosra.mvp.assignment_designer.schemas import (
    AmbiguityDiagnosis,
    ClarifyAndScaffoldRequest,
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
    """
    Evaluates educator prompt ambiguity across temporal boundaries, causal inquiry,
    and curriculum graph anchoring. Returns a 3-question alignment interview if ambiguity > 30%.
    """
    return scope_deambiguator.evaluate_prompt_ambiguity(
        raw_prompt=request.raw_prompt,
        domain=request.domain,
        course_id=request.course_id,
    )


@router.post("/clarify-and-scaffold", response_model=ScaffoldingPlan)
async def clarify_and_generate_scaffolding(request: ClarifyAndScaffoldRequest) -> ScaffoldingPlan:
    """
    Synthesizes a 4-rung Socratic hint ladder (Δ = 0.25) and verifiable NLI rubric rules
    incorporating educator interview answers.
    """
    return await assignment_generator.generate_scaffolding_plan(request)


@router.post("/draft", response_model=QuestionSpec)
async def draft_assignment_question(request: QuestionDraftRequest) -> QuestionSpec:
    """
    Drafts an assignment specification, locks reference solutions in the Answer Vault,
    and stores the draft in the database.
    """
    return await assignment_generator.draft_question(request)


@router.post("/{assignment_id}/publish", response_model=PublishResponse)
async def publish_assignment(
    assignment_id: UUID,
    request: PublishRequest | None = None,
) -> dict[str, Any]:
    """
    Publishes an assignment, binding it to a curriculum module and making it accessible
    to student reasoning canvases.
    """
    module_id = request.module_id if request else None
    try:
        return await assignment_generator.publish_assignment(
            assignment_id=assignment_id,
            module_id=module_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
