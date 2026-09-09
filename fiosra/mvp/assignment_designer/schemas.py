from typing import Any

from pydantic import BaseModel, Field


class HintRung(BaseModel):
    level: int = Field(ge=0, le=4)
    hint_type: str  # "metacognitive", "conceptual", "procedural", "worked_analogy", "bottom_out"
    content: str
    is_locked: bool = False

class ScaffoldingStep(BaseModel):
    step_id: str
    step_prompt: str
    target_kc: str

class QuestionDraftRequest(BaseModel):
    topic: str
    domain: str = "algebra"
    grade_level: str = "Grade 9"
    blooms_level: str = "Apply"

class QuestionSpec(BaseModel):
    question_id: str
    prompt: str
    domain: str
    target_kcs: list[str]
    subproblems: list[ScaffoldingStep]
    hint_ladder: list[HintRung]
    reference_solution: dict[str, Any]
    rubric_criteria: list[dict[str, Any]]
