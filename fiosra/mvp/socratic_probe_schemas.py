"""Typed, learner-safe contracts for proactive Socratic probe workflows."""

from datetime import datetime
from typing import Literal
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
    status: ProbeStatus
    evidence_state: EvidenceState
    offered_at: datetime
    response_text: str | None = None
    responded_at: datetime | None = None
    deferred_until: datetime | None = None
    generation_metadata: ProbeGenerationMetadata
