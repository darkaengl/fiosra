"""Typed contracts for the protected long-form student document API."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DocumentBlockType = Literal["heading", "paragraph", "blockquote", "bullet_list", "ordered_list"]
DocumentAuthorType = Literal["student", "student_edited_assistance"]


class DocumentBlockInput(BaseModel):
    """One top-level ProseMirror/Tiptap document block supplied by the learner client."""

    model_config = ConfigDict(extra="forbid")

    block_id: UUID
    block_type: DocumentBlockType
    content: dict[str, Any]
    position: int = Field(ge=1, le=100_000)
    section_id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]{2,63}$")
    author_type: DocumentAuthorType = "student"


class DocumentBlockResponse(DocumentBlockInput):
    revision: int = Field(ge=1)
    updated_at: datetime
    plaintext: str


class LearningDocumentState(BaseModel):
    """Authorized, student-visible state of one session-bound long-form document."""

    document_id: UUID
    session_id: UUID
    assignment_id: UUID
    title: str
    status: Literal["active", "submitted", "completed"]
    schema_version: int = 1
    document_revision: int = Field(ge=0)
    blocks: list[DocumentBlockResponse]


class SyncLearningDocumentRequest(BaseModel):
    """Incremental document patch with optimistic-concurrency protection."""

    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(ge=0)
    upserts: list[DocumentBlockInput] = Field(default_factory=list, max_length=300)
    deleted_block_ids: list[UUID] = Field(default_factory=list, max_length=300)


class SyncLearningDocumentResponse(LearningDocumentState):
    changed_block_ids: list[UUID] = Field(default_factory=list)
