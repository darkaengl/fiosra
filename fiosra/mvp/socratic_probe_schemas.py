"""Typed, learner-safe contracts for proactive Socratic probe workflows."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProbeStatus = Literal["offered", "deferred", "responded", "dismissed", "superseded", "expired"]
ProbeFocusType = Literal[
    "direct_observation",
    "warrant",
    "causal_bridge",
    "alternative_explanation",
    "qualification",
]
EvidenceState = Literal["unverified", "evidence_submitted"]


class ProbeEvaluationRequest(BaseModel):
    """A bounded client request to evaluate canonical, already-saved document blocks."""

    model_config = ConfigDict(extra="forbid")

    document_revision: int = Field(ge=0)
    changed_block_ids: list[UUID] = Field(min_length=1, max_length=20)


class ProbeGenerationMetadata(BaseModel):
    """Prompt-free operational metadata for a single question-generation attempt."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    used_live_provider: bool
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    fallback_reason: str | None = None


class SocraticProbeCard(BaseModel):
    """A student-visible, paragraph-bound question without answer or grading content."""

    probe_id: UUID
    document_id: UUID
    block_id: UUID
    source_block_revision: int = Field(ge=1)
    section_label: str = Field(min_length=1, max_length=120)
    focus_type: ProbeFocusType
    question: str = Field(min_length=1, max_length=260)
    concept_id: str | None = None
    concept_label: str | None = None
    claim_text: str | None = Field(default=None, max_length=50_000)
    status: ProbeStatus
    evidence_state: EvidenceState = "unverified"
    offered_at: datetime
    deferred_until: datetime | None = None
    response_text: str | None = Field(default=None, max_length=6000)
    responded_at: datetime | None = None
    generation_metadata: ProbeGenerationMetadata


class ProbeEvaluationResponse(BaseModel):
    """Results of a server-side eligibility pass after an editor quiet period."""

    document_revision: int = Field(ge=0)
    created: list[SocraticProbeCard] = Field(default_factory=list)
    pending: list[SocraticProbeCard] = Field(default_factory=list)
    evidence_summary: dict[str, int] = Field(default_factory=dict)
    availability_notice: str | None = None


class ProbeListResponse(BaseModel):
    """Current pending/deferred questions plus a small evidence-status summary."""

    document_revision: int = Field(ge=0)
    probes: list[SocraticProbeCard] = Field(default_factory=list)
    evidence_summary: dict[str, int] = Field(default_factory=dict)


class SubmitProbeResponseRequest(BaseModel):
    """A learner-authored explanation in response to one proactive Socratic question."""

    model_config = ConfigDict(extra="forbid")

    response_text: str = Field(min_length=10, max_length=6000)


class ProbeDispositionResponse(BaseModel):
    """Idempotent projection returned after response, defer, or dismissal transitions."""

    probe: SocraticProbeCard
    message: str


class ProbeTraceRecord(BaseModel):
    """Internal evaluation projection of one probe lifecycle without provider prompts."""

    probe_id: UUID
    block_id: UUID
    section_label: str
    focus_type: ProbeFocusType
    question: str
    concept_id: str | None = None
    concept_label: str | None = None
    status: ProbeStatus
    evidence_state: EvidenceState
    offered_at: datetime
    response_text: str | None = None
    responded_at: datetime | None = None
    deferred_until: datetime | None = None
    generation_metadata: ProbeGenerationMetadata


SentenceEpistemicType = Literal["claim", "evidence", "reasoning", "assumption", "premature_closure"]


class SentenceClassification(BaseModel):
    """A single sentence with its epistemic role and targeted Socratic probe."""

    model_config = ConfigDict(extra="ignore")

    sentence: str
    epistemic_type: SentenceEpistemicType
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    oracle_probe: str | None = None
    source_grounded: bool = False
    premature_leap_reason: str | None = None


class EpistemicClassifyRequest(BaseModel):
    """Client request to classify sentences in a paragraph with LLM epistemic reasoning."""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(min_length=1, max_length=12000)
    oracle_pressure: str = Field(default="socratic")


class EpistemicClassifyResponse(BaseModel):
    """Typed response holding LLM-classified sentences and targeted probes."""

    sentences: list[SentenceClassification]


SocraticMoveType = Literal["challenge", "why_ladder", "assumptions", "source", "counterfactual", "creative", "socratic"]


class SentenceInquireRequest(BaseModel):
    """Interactive on-demand request for a bespoke Socratic inquiry on a single sentence."""

    model_config = ConfigDict(extra="ignore")

    sentence: str = Field(min_length=3, max_length=1500)
    epistemic_type: SentenceEpistemicType = Field(default="claim")
    surrounding_context: str | None = Field(default=None, max_length=4000)
    move_type: SocraticMoveType = Field(default="challenge")
    oracle_pressure: str = Field(default="socratic")


class SentenceInquireResponse(BaseModel):
    """Bespoke response generated by the Socratic Agent for the requested sentence."""

    sentence: str
    epistemic_type: SentenceEpistemicType
    oracle_probe: str
    move_type: SocraticMoveType
    socratic_moves: list[str] = Field(default_factory=list)
    targeted_vulnerability: str | None = None


class DialecticalMessage(BaseModel):
    """A single turn in the Socratic chat dialogue between student and Oracle."""

    model_config = ConfigDict(extra="ignore")

    role: Literal["oracle", "student"]
    content: str
    probe_category: SocraticMoveType | None = None
    created_at: str | None = None


class DialecticalTurnRequest(BaseModel):
    """Interactive submission from the student in an active Socratic dialectic chat."""

    model_config = ConfigDict(extra="ignore")

    sentence: str = Field(min_length=3, max_length=1500)
    epistemic_type: SentenceEpistemicType = Field(default="claim")
    history: list[DialecticalMessage] = Field(default_factory=list)
    student_reply: str = Field(min_length=1, max_length=6000)
    surrounding_context: str | None = Field(default=None, max_length=4000)
    move_type: SocraticMoveType = Field(default="challenge")
    oracle_pressure: str = Field(default="socratic")


class HelperCanvasAction(BaseModel):
    """Action delegated by the Socratic Agent to the Canvas Scribe Helper Agent."""

    model_config = ConfigDict(extra="ignore")

    action: Literal["scaffold_sections", "insert_claim", "add_page"]
    summary: str
    target_page: int = 1
    target_section: str | None = None
    blocks: list[dict[str, Any]] = Field(default_factory=list)


class EpistemicToolAction(BaseModel):
    """An interactive action attached to a Socratic response that the student can trigger with one click."""

    model_config = ConfigDict(extra="ignore")

    label: str
    action_type: Literal["scaffold_section", "insert_claim", "explore_prompt", "cite_source"]
    icon: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class OutlineOption(BaseModel):
    """One learner-selectable, answer-blind way to organize an assignment."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    section_titles: list[str] = Field(min_length=3, max_length=3)
    reasoning_focus: str = Field(min_length=12, max_length=280)


class DialecticalTurnResponse(BaseModel):
    """The Oracle's evaluation, follow-up probe or resolution synthesis, and satisfaction state."""

    model_config = ConfigDict(extra="ignore")

    oracle_reply: str
    is_satisfied: bool = False
    satisfaction_reason: str
    current_probe_category: SocraticMoveType = "challenge"
    suggested_revision: str | None = None
    epistemic_progress: float = Field(default=0.25, ge=0.0, le=1.0)
    socratic_moves: list[str] = Field(default_factory=list)
    helper_action: HelperCanvasAction | None = None
    interactive_actions: list[EpistemicToolAction] = Field(default_factory=list)
    outline_options: list[OutlineOption] = Field(default_factory=list)
