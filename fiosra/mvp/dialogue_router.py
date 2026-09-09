from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from fiosra.mvp.dialogue_engine import dialogue_engine
from fiosra.mvp.event_store import event_store

router = APIRouter(prefix="/dialogue", tags=["Socratic Dialogue"])


class DialogueMessageRequest(BaseModel):
    session_id: UUID = Field(..., description="Active session ID")
    student_id: str = Field(..., description="Student ID")
    question_id: str = Field(default="q1", description="Current question ID")
    student_input: str = Field(..., description="Student message or reasoning attempt")
    question_prompt: str = Field(..., description="The original question prompt")
    domain: str = Field(default="history", description="Curriculum domain")
    current_rung: int = Field(default=0, ge=0, le=3, description="Current hint rung (0-3)")
    hint_requested: bool = Field(default=False, description="Whether the student explicitly asked for a hint")
    assignment_id: UUID | None = Field(default=None, description="Optional assignment ID")


class DialogueMessageResponse(BaseModel):
    response_text: str
    thoughts_of_tutorbot: dict[str, Any]
    hint_rung: int
    penalty_score: float
    is_adversarial: bool
    matched_misconception_id: str | None = None


@router.post("/message", response_model=DialogueMessageResponse)
async def handle_dialogue_turn(request: DialogueMessageRequest) -> dict[str, Any]:
    """
    Processes a student dialogue turn while enforcing Answer Isolation,
    adversarial guardrails, and automated event store flight recording.
    """
    # 1. Log student attempt to event store
    await event_store.log_event(
        session_id=request.session_id,
        student_id=request.student_id,
        question_id=request.question_id,
        event_type="student_prompt_submitted",
        payload={
            "student_input": request.student_input,
            "hint_requested": request.hint_requested,
            "current_rung": request.current_rung,
        },
        assignment_id=request.assignment_id,
    )

    # 2. Run Answer-Isolated Dialogue Engine
    result = await dialogue_engine.generate_response(
        student_input=request.student_input,
        question_prompt=request.question_prompt,
        domain=request.domain,
        current_rung=request.current_rung,
        hint_requested=request.hint_requested,
    )

    # 3. Log tutor response to flight recorder
    if result["is_adversarial"]:
        event_type = "adversarial_probe_defended"
    elif request.hint_requested:
        event_type = "hint_delivered"
    else:
        event_type = "tutor_turn_completed"

    await event_store.log_event(
        session_id=request.session_id,
        student_id=request.student_id,
        question_id=request.question_id,
        event_type=event_type,
        payload={
            "response_text": result["response_text"],
            "thoughts_of_tutorbot": result["thoughts_of_tutorbot"],
            "hint_rung": result["hint_rung"],
            "penalty_score": result["penalty_score"],
            "matched_misconception_id": result.get("matched_misconception_id"),
        },
        assignment_id=request.assignment_id,
    )

    return result
