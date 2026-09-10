from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status

from fiosra.mvp.learning_canvas_schemas import (
    AcceptSuggestionRequest,
    CanvasActionResponse,
    CanvasStateResponse,
    CanvasSuggestion,
    CreateSuggestionRequest,
    DismissSuggestionRequest,
    SaveCanvasSectionRequest,
    SaveCanvasSectionResponse,
)
from fiosra.mvp.learning_canvas_service import (
    CanvasAccessError,
    CanvasConflictError,
    CanvasValidationError,
    learning_canvas_service,
)

router = APIRouter(prefix="/learning-canvas", tags=["Student Learning Canvas"])
SessionToken = Annotated[str | None, Header(alias="X-Fiosra-Session-Token")]


def _raise_canvas_error(error: Exception) -> None:
    if isinstance(error, CanvasAccessError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, CanvasConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, CanvasValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    raise error


@router.get("/sessions/{session_id}", response_model=CanvasStateResponse)
async def get_canvas_state(session_id: UUID, session_token: SessionToken = None) -> CanvasStateResponse:
    """Return the public section contract and the authorized learner's saved draft state."""
    try:
        return await learning_canvas_service.get_state(session_id, session_token)
    except (CanvasAccessError, CanvasConflictError, CanvasValidationError) as error:
        _raise_canvas_error(error)


@router.put(
    "/sessions/{session_id}/sections/{section_id}",
    response_model=SaveCanvasSectionResponse,
)
async def save_canvas_section(
    session_id: UUID,
    section_id: str,
    request: SaveCanvasSectionRequest,
    session_token: SessionToken = None,
) -> SaveCanvasSectionResponse:
    """Save a learner-authored section revision with source-reference validation."""
    try:
        return await learning_canvas_service.save_section(session_id, section_id, session_token, request)
    except (CanvasAccessError, CanvasConflictError, CanvasValidationError) as error:
        _raise_canvas_error(error)


@router.post("/sessions/{session_id}/suggestions", response_model=CanvasSuggestion)
async def offer_canvas_suggestion(
    session_id: UUID,
    request: CreateSuggestionRequest,
    session_token: SessionToken = None,
) -> CanvasSuggestion:
    """Offer a deterministic, section-scoped writing support card without mutating learner text."""
    try:
        return await learning_canvas_service.create_suggestion(session_id, session_token, request)
    except (CanvasAccessError, CanvasConflictError, CanvasValidationError) as error:
        _raise_canvas_error(error)


@router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/accept",
    response_model=CanvasActionResponse,
)
async def accept_canvas_suggestion(
    session_id: UUID,
    suggestion_id: UUID,
    request: AcceptSuggestionRequest,
    session_token: SessionToken = None,
) -> CanvasActionResponse:
    """Apply learner-confirmed text while preserving assistance attribution and revision safety."""
    try:
        return await learning_canvas_service.accept_suggestion(
            session_id, suggestion_id, session_token, request
        )
    except (CanvasAccessError, CanvasConflictError, CanvasValidationError) as error:
        _raise_canvas_error(error)


@router.post(
    "/sessions/{session_id}/suggestions/{suggestion_id}/dismiss",
    response_model=CanvasActionResponse,
)
async def dismiss_canvas_suggestion(
    session_id: UUID,
    suggestion_id: UUID,
    request: DismissSuggestionRequest,
    session_token: SessionToken = None,
) -> CanvasActionResponse:
    """Record an explicit learner decision not to use an offered support card."""
    try:
        return await learning_canvas_service.dismiss_suggestion(
            session_id, suggestion_id, session_token, request
        )
    except (CanvasAccessError, CanvasConflictError, CanvasValidationError) as error:
        _raise_canvas_error(error)
