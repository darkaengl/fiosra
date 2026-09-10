from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class HintRung(BaseModel):
    level: int = Field(
        ge=0,
        le=4,
        description="0=metacognitive, 1=conceptual, 2=procedural, 3=worked_analogy, 4=bottom_out",
    )
    hint_type: str
    content: str
    is_locked: bool = False


class ScaffoldingStep(BaseModel):
    step_id: str
    step_prompt: str
    target_kc: str


class ClarificationQuestion(BaseModel):
    question_id: str
    dimension: str
    prompt: str
    options: list[str]
    default_recommendation: str


class AmbiguityDiagnosis(BaseModel):
    raw_prompt: str
    ambiguity_index: float = Field(ge=0.0, le=1.0, description="0.0=crystal clear, 1.0=completely open-ended")
    is_ambiguous: bool
    diagnosed_dimensions: dict[str, str]
    interview_questions: list[ClarificationQuestion]


class ScopeAnalysisRequest(BaseModel):
    raw_prompt: str = Field(..., min_length=3, description="Educator's initial assignment or essay prompt")
    domain: str = Field(default="history", description="Subject domain")
    course_id: UUID | None = Field(default=None, description="Optional grounding course ID")


class ClarifyAndScaffoldRequest(BaseModel):
    raw_prompt: str
    domain: str = "history"
    answers: dict[str, str] = Field(..., description="Educator interview answers by question_id or dimension")
    target_kcs: list[str] = Field(default_factory=list)


class ScaffoldingPlan(BaseModel):
    clarified_prompt: str
    domain: str
    target_kcs: list[str]
    hint_ladder: list[HintRung]
    rubric_rules: list[dict[str, Any]]
    distractor_traps: list[dict[str, Any]]


class QuestionDraftRequest(BaseModel):
    topic: str
    domain: str = "history"
    grade_level: str = "Undergraduate"
    blooms_level: str = "Analyze"
    module_id: UUID | None = None
    created_by: str = "educator_prof_mora"
    raw_prompt: str | None = None
    answers: dict[str, str] | None = None
    clarified_prompt: str | None = None
    target_kcs: list[str] | None = None
    hint_ladder: list[HintRung] | None = None
    rubric_rules: list[dict[str, Any]] | None = None
    reference_solution: str | dict[str, Any] | None = None


class QuestionSpec(BaseModel):
    question_id: str
    assignment_id: str
    prompt: str
    domain: str
    target_kcs: list[str]
    subproblems: list[ScaffoldingStep]
    hint_ladder: list[HintRung]
    rubric_criteria: list[dict[str, Any]]
    vault_token: str
    status: str = "draft"


class PublicQuestionSpec(BaseModel):
    """Student-safe assignment representation that intentionally excludes the vault token."""

    question_id: str
    assignment_id: str
    prompt: str
    domain: str
    target_kcs: list[str]
    subproblems: list[ScaffoldingStep]
    hint_ladder: list[HintRung]
    rubric_criteria: list[dict[str, Any]]
    status: str = "draft"
