from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CANVAS_SECTION_IDS = (
    "working_claim",
    "source_observations",
    "reasoning",
    "alternative_explanation",
    "revision_reflection",
)


def default_canvas_sections() -> list["CanvasSectionDefinition"]:
    """Return a fresh public CER canvas schema for new assignments."""
    return [
        CanvasSectionDefinition(
            section_id="working_claim",
            label="Working claim",
            purpose="State a provisional, bounded answer to the assignment question.",
            completion_guidance="Write one claim that you can test with the assigned source material.",
            position=1,
        ),
        CanvasSectionDefinition(
            section_id="source_observations",
            label="Source observations",
            purpose="Record what the selected course sources directly show or state.",
            completion_guidance="Add specific observations before explaining what they might mean.",
            position=2,
        ),
        CanvasSectionDefinition(
            section_id="reasoning",
            label="Reasoning",
            purpose="Explain how your source observations support, qualify, or challenge your claim.",
            completion_guidance="Connect an observation to your claim and name the inference you are making.",
            position=3,
        ),
        CanvasSectionDefinition(
            section_id="alternative_explanation",
            label="Alternative explanation",
            purpose="Test a reasonable limit, alternative interpretation, or uncertainty.",
            completion_guidance="Describe one explanation that the available evidence does not rule out.",
            position=4,
        ),
        CanvasSectionDefinition(
            section_id="revision_reflection",
            label="Revision reflection",
            purpose="Explain what you strengthened or changed in your reasoning.",
            completion_guidance="Identify the revision you made and why it made your argument more defensible.",
            position=5,
        ),
    ]


class CanvasSectionDefinition(BaseModel):
    """A student-visible section of an assignment's reasoning canvas."""

    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    label: str = Field(min_length=3, max_length=100)
    purpose: str = Field(min_length=3, max_length=400)
    completion_guidance: str = Field(min_length=3, max_length=800)
    required: bool = True
    position: int = Field(ge=1, le=50)
    max_characters: int = Field(default=1800, ge=120, le=8000)
    allowed_suggestion_kinds: list[Literal["writing_frame", "section_question", "source_reminder"]] = (
        Field(default_factory=lambda: ["writing_frame", "section_question", "source_reminder"])
    )


class CanvasSourceReference(BaseModel):
    """A learner-selected, assignment-approved course source reference."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: UUID
    quote: str = Field(default="", max_length=600)
    rationale: str = Field(default="", max_length=500)


class CanvasSectionDraft(BaseModel):
    section_id: str
    text: str = ""
    revision: int = Field(default=0, ge=0)
    author_type: Literal["student", "student_edited_assistance"] | None = None
    source_references: list[CanvasSourceReference] = Field(default_factory=list)
    updated_at: datetime | None = None


class CanvasStateResponse(BaseModel):
    session_id: str
    assignment_id: str
    status: str
    sections: list[CanvasSectionDefinition]
    drafts: list[CanvasSectionDraft]
    suggestions: list["CanvasSuggestion"] = Field(default_factory=list)


class SaveCanvasSectionRequest(BaseModel):
    text: str = Field(default="", max_length=8000)
    base_revision: int = Field(ge=0)
    source_references: list[CanvasSourceReference] = Field(default_factory=list, max_length=12)
    author_type: Literal["student", "student_edited_assistance"] = "student"


class SaveCanvasSectionResponse(CanvasSectionDraft):
    session_id: str


class CreateSuggestionRequest(BaseModel):
    section_id: str
    kind: Literal["writing_frame", "section_question", "source_reminder"] = "writing_frame"
    base_revision: int = Field(ge=0)


class CanvasSuggestion(BaseModel):
    suggestion_id: str
    session_id: str
    section_id: str
    kind: Literal["writing_frame", "section_question", "source_reminder"]
    content: str
    base_revision: int = Field(ge=0)
    status: Literal["offered", "accepted", "dismissed"]
    created_at: datetime


class AcceptSuggestionRequest(BaseModel):
    text: str = Field(default="", max_length=8000)
    source_references: list[CanvasSourceReference] = Field(default_factory=list, max_length=12)


class DismissSuggestionRequest(BaseModel):
    reason: str = Field(default="", max_length=300)


class CanvasActionResponse(BaseModel):
    suggestion: CanvasSuggestion
    draft: CanvasSectionDraft | None = None
