"""HTTP boundary for protected long-form learner documents."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from fiosra.mvp.learning_document_schemas import (
    LearningDocumentState,
    SyncLearningDocumentRequest,
    SyncLearningDocumentResponse,
)
from fiosra.mvp.learning_document_service import (
    LearningDocumentAccessError,
    LearningDocumentConflictError,
    LearningDocumentValidationError,
    learning_document_service,
)

router = APIRouter(prefix="/learning-documents", tags=["Long-form Student Documents"])
SessionToken = Annotated[str | None, Header(alias="X-Fiosra-Session-Token")]


def _raise_document_error(error: Exception) -> None:
    if isinstance(error, LearningDocumentAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, LearningDocumentConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, LearningDocumentValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    raise error


@router.get("/sessions/{session_id}", response_model=LearningDocumentState)
async def get_learning_document(
    session_id: UUID,
    session_token: SessionToken = None,
) -> LearningDocumentState:
    """Load or import the current learner-owned document for an authorized active session."""
    try:
        return await learning_document_service.get_state(session_id, session_token)
    except (LearningDocumentAccessError, LearningDocumentConflictError, LearningDocumentValidationError) as error:
        _raise_document_error(error)


@router.put("/sessions/{session_id}", response_model=SyncLearningDocumentResponse)
async def sync_learning_document(
    session_id: UUID,
    request: SyncLearningDocumentRequest,
    session_token: SessionToken = None,
) -> SyncLearningDocumentResponse:
    """Persist a revision-checked batch of learner document block changes."""
    try:
        return await learning_document_service.sync_document(session_id, session_token, request)
    except (LearningDocumentAccessError, LearningDocumentConflictError, LearningDocumentValidationError) as error:
        _raise_document_error(error)
