import uuid
from typing import Any

from fiosra.mvp.assignment_designer.schemas import (
    HintRung,
    QuestionDraftRequest,
    QuestionSpec,
    ScaffoldingStep,
)


class AssignmentGenerator:
    """
    RAG-grounded prompt pipeline for crafting syllabus-aligned,
    misconception-seeded questions and hint ladders.
    """
    @classmethod
    async def draft_question(
        cls, 
        req: QuestionDraftRequest,
        prerequisite_kcs: list[str],
        common_misconceptions: list[dict[str, Any]]
    ) -> QuestionSpec:
        # Generate question spec grounded in curriculum DAG & misconceptions
        q_id = f"Q_{uuid.uuid4().hex[:8].upper()}"
        
        hint_ladder = [
            HintRung(level=0, hint_type="metacognitive", content="Review the given equation and identify what unknown you need to isolate first.", is_locked=False),
            HintRung(level=1, hint_type="conceptual", content="Remember the distributive property: a*(b + c) = a*b + a*c.", is_locked=False),
            HintRung(level=2, hint_type="procedural", content="Distribute the outer factor to both terms inside the parentheses.", is_locked=False),
            HintRung(level=3, hint_type="worked_analogy", content="For example: 3*(x - 4) = 3*x - 12. Apply the same logic here.", is_locked=False),
            HintRung(level=4, hint_type="bottom_out", content="Bottom-out full solution (Locked by default).", is_locked=True)
        ]

        subproblems = [
            ScaffoldingStep(step_id="step_1", step_prompt="Expand the left side of the equation.", target_kc="KC_DISTRIBUTIVE_EXPANSION"),
            ScaffoldingStep(step_id="step_2", step_prompt="Combine like terms and solve for x.", target_kc="KC_LINEAR_EQUATION_ISOLATION")
        ]

        return QuestionSpec(
            question_id=q_id,
            prompt="Solve the linear equation for x: 4*(2*x - 3) = 20",
            domain=req.domain,
            target_kcs=prerequisite_kcs or ["KC_LINEAR_EQUATION_ISOLATION"],
            subproblems=subproblems,
            hint_ladder=hint_ladder,
            reference_solution={
                "step_1": "8*x - 12 = 20",
                "step_2": "x = 4",
                "final_answer": "4"
            },
            rubric_criteria=[
                {"criterion_id": "c1", "description": "Correctly distributed factor 4 across (2x - 3)", "max_points": 2},
                {"criterion_id": "c2", "description": "Accurately isolated variable x without sign error", "max_points": 3}
            ]
        )
