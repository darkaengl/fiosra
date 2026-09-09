from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal
from fiosra.mvp.event_store import event_store
from fiosra.mvp.evidence_dossier.synthesizer import evidence_dossier_synthesizer

router = APIRouter(prefix="/evidence", tags=["Evidence & AutoSCORE Dossier"])


class FinaliseGradeRequest(BaseModel):
    approved_grade: str = Field(..., description="Final grade approved or overridden by educator (e.g. 'A', '88%')")
    teacher_id: str = Field(default="teacher_sovereign_01", description="Educator ID finalizing the grade")
    teacher_override: bool = Field(default=False, description="Whether the teacher overrode the agent-suggested score")
    feedback_comments: str = Field(default="", description="Formative feedback notes to the student")


class FinaliseGradeResponse(BaseModel):
    session_id: str
    status: str
    final_grade: str
    teacher_id: str
    teacher_override: bool
    message: str


@router.get("/dossier/{session_id}")
async def get_executive_evidence_dossier(session_id: UUID) -> dict[str, Any]:
    """
    Synthesizes the 1-page executive educator review dossier (AutoSCORE Evidence Packet Z).
    Includes rubric criteria assessments with direct verbatim student quote citations.
    """
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    events = await event_store.get_session_events(session_id)
    dossier = evidence_dossier_synthesizer.synthesize_dossier(
        session_info=session_info,
        events=events,
    )
    return dossier


@router.post("/dossier/{session_id}/finalise-grade", response_model=FinaliseGradeResponse)
async def finalise_student_grade(
    session_id: UUID,
    request: FinaliseGradeRequest,
) -> dict[str, Any]:
    """
    1-Click Educator Sovereign Grade Finalization.
    Updates the session status to 'completed' and records the sovereign grade decision
    in the immutable event store flight recorder.
    """
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    # 1. Log sovereign grade decision to flight recorder
    await event_store.log_event(
        session_id=session_id,
        student_id=session_info["student_id"],
        question_id=session_info.get("current_question_id", "q1"),
        event_type="grade_finalised_by_educator",
        payload={
            "approved_grade": request.approved_grade,
            "teacher_id": request.teacher_id,
            "teacher_override": request.teacher_override,
            "feedback_comments": request.feedback_comments,
        },
        assignment_id=session_info.get("assignment_id"),
    )

    # 2. Update session status to completed in student_sessions table
    update_sql = text("""
        UPDATE student_sessions
        SET status = 'completed',
            completed_at = NOW(),
            last_activity_at = NOW()
        WHERE session_id = :session_id;
    """)
    async with AsyncSessionLocal() as session:
        await session.execute(update_sql, {"session_id": str(session_id)})
        await session.commit()

    return {
        "session_id": str(session_id),
        "status": "completed",
        "final_grade": request.approved_grade,
        "teacher_id": request.teacher_id,
        "teacher_override": request.teacher_override,
        "message": "Grade successfully recorded and session finalized.",
    }


@router.get("/trace/{session_id}")
async def get_student_reasoning_trace(session_id: UUID) -> dict[str, Any]:
    """
    Retrieves the chronological reasoning trace nodes for visualization on the student canvas.
    """
    session_info = await event_store.get_session_details(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    events = await event_store.get_session_events(session_id)
    trace_nodes = []
    for ev in events:
        ev_type = ev.get("event_type")
        payload = ev.get("payload", {})
        trace_nodes.append({
            "event_id": ev.get("event_id"),
            "timestamp": ev.get("created_at"),
            "event_type": ev_type,
            "question_id": ev.get("question_id"),
            "summary": (
                payload.get("student_input")
                or payload.get("response_text")
                or payload.get("approved_grade")
                or ev_type
            ),
            "payload": payload,
        })

    return {
        "session_id": str(session_id),
        "total_nodes": len(trace_nodes),
        "trace_nodes": trace_nodes,
    }
