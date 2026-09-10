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
    event_type: str = Field(..., description="Type of event")
    payload: dict[str, Any] = Field(..., description="Arbitrary typed JSON payload")
    assignment_id: UUID | None = Field(default=None, description="Optional assignment ID")


class LogEventResponse(BaseModel):
    event_id: int
    status: str = "logged"


class SubmitSessionResponse(BaseModel):
    session_id: str
    status: str
    message: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest) -> dict[str, str]:
    """Initialize an active student reasoning session."""
    session_id = await event_store.create_session(
        student_id=request.student_id,
        assignment_id=request.assignment_id,
        current_question_id=request.current_question_id,
    )
    return {"session_id": session_id, "student_id": request.student_id, "status": "active"}


@router.post("/log", response_model=LogEventResponse)
async def log_session_event(request: LogEventRequest) -> dict[str, Any]:
    """Append an immutable event to the student session flight recorder."""
    event_id = await event_store.log_event(
        session_id=request.session_id,
        student_id=request.student_id,
        question_id=request.question_id,
        event_type=request.event_type,
        payload=request.payload,
        assignment_id=request.assignment_id,
    )
    return {"event_id": event_id, "status": "logged"}


@router.post("/session/{session_id}/submit", response_model=SubmitSessionResponse)
async def submit_session_for_review(session_id: UUID) -> dict[str, str]:
    """Send a student reasoning trace to the educator review queue without granting grade authority."""
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    if session_info["status"] == "completed":
        raise HTTPException(status_code=409, detail="This session has already been finalized by an educator.")
    if session_info["status"] != "submitted":
        submitted = await event_store.submit_session(session_id)
        if not submitted:
            raise HTTPException(status_code=409, detail="The session could not be submitted.")
        await event_store.log_event(
            session_id=session_id,
            student_id=session_info["student_id"],
            question_id=session_info.get("current_question_id", "q1"),
            event_type="student_submitted_for_review",
            payload={"submission_status": "submitted"},
            assignment_id=session_info.get("assignment_id"),
        )
    return {
        "session_id": str(session_id),
        "status": "submitted",
        "message": "Reasoning trace submitted for educator review.",
    }


@router.get("/session/{session_id}")
async def get_session_replay(session_id: UUID) -> dict[str, Any]:
    """Return the full chronological flight-recorder trace for a session."""
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    events = await event_store.get_session_events(session_id)
    return {"session": session_info, "total_events": len(events), "events": events}
