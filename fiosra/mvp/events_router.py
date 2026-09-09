from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fiosra.mvp.event_store import event_store

router = APIRouter(prefix="/events", tags=["Event Store"])


class CreateSessionRequest(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    assignment_id: UUID | None = Field(default=None, description="Optional associated assignment ID")
    current_question_id: str = Field(default="q1", description="Initial question identifier")


class CreateSessionResponse(BaseModel):
    session_id: str
    student_id: str
    status: str


class LogEventRequest(BaseModel):
    session_id: UUID = Field(..., description="UUID of active session")
    student_id: str = Field(..., description="Student ID")
    question_id: str = Field(..., description="Current question ID")
    event_type: str = Field(..., description="Type of event (e.g. attempt_submitted, hint_requested)")
    payload: dict[str, Any] = Field(..., description="Arbitrary typed JSON payload")
    assignment_id: UUID | None = Field(default=None, description="Optional assignment ID")


class LogEventResponse(BaseModel):
    event_id: int
    status: str = "logged"


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> dict[str, str]:
    """Initializes a new student session in the database."""
    session_id = await event_store.create_session(
        student_id=request.student_id,
        assignment_id=request.assignment_id,
        current_question_id=request.current_question_id,
    )
    return {
        "session_id": session_id,
        "student_id": request.student_id,
        "status": "active",
    }


@router.post("/log", response_model=LogEventResponse)
async def log_session_event(request: LogEventRequest) -> dict[str, Any]:
    """Appends an immutable event to the student session flight recorder."""
    event_id = await event_store.log_event(
        session_id=request.session_id,
        student_id=request.student_id,
        question_id=request.question_id,
        event_type=request.event_type,
        payload=request.payload,
        assignment_id=request.assignment_id,
    )
    return {"event_id": event_id, "status": "logged"}


@router.get("/session/{session_id}")
async def get_session_replay(session_id: UUID) -> dict[str, Any]:
    """Returns the full chronological flight-recorder trace of all events in the session."""
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    events = await event_store.get_session_events(session_id)
    return {
        "session": session_info,
        "total_events": len(events),
        "events": events,
    }
