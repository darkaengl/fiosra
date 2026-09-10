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


class GroundingSource(BaseModel):
    """Teacher-visible provenance for an instructional recommendation."""

    chunk_id: str
    title: str
    kc_id: str | None = None
    excerpt: str


class LLMGenerationMetadata(BaseModel):
    """Prompt-free provider telemetry for educator and operational audit trails."""

    provider: str
    model: str
    used_live_provider: bool
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    fallback_reason: str | None = None


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
    module_id: UUID | None = Field(default=None, description="Optional grounding module ID")


class ClarifyAndScaffoldRequest(BaseModel):
    raw_prompt: str
    domain: str = "history"
    answers: dict[str, str] = Field(default_factory=dict, description="Educator interview answers by question ID")
    target_kcs: list[str] = Field(default_factory=list)
    course_id: UUID | None = None
    module_id: UUID | None = None


class ScaffoldingPlan(BaseModel):
    clarified_prompt: str
    domain: str
    target_kcs: list[str]
    hint_ladder: list[HintRung]
    rubric_rules: list[dict[str, Any]]
    distractor_traps: list[dict[str, Any]]
    grounding_mode: str = Field(default="generic", description="course_grounded or generic")
    grounding_sources: list[GroundingSource] = Field(default_factory=list)
    generation_metadata: LLMGenerationMetadata | None = None


class QuestionDraftRequest(BaseModel):
    topic: str
    domain: str = "history"
    grade_level: str = "Undergraduate"
    blooms_level: str = "Analyze"
    course_id: UUID | None = None
    module_id: UUID | None = None
    created_by: str = "educator_prof_mora"
    raw_prompt: str | None = None
    answers: dict[str, str] | None = None
    clarified_prompt: str | None = None
    target_kcs: list[str] | None = None
    hint_ladder: list[HintRung] | None = None
    rubric_rules: list[dict[str, Any]] | None = None
    grounding_mode: str = "generic"
    grounding_sources: list[GroundingSource] = Field(default_factory=list)
    generation_metadata: LLMGenerationMetadata | None = None
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
    grounding_mode: str = "generic"
    grounding_sources: list[GroundingSource] = Field(default_factory=list)
    generation_metadata: LLMGenerationMetadata | None = None


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
    grounding_mode: str = "generic"
    grounding_sources: list[GroundingSource] = Field(default_factory=list)
