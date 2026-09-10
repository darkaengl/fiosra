import logging
import re
from typing import ClassVar
from uuid import UUID

from fiosra.mvp.assignment_designer.schemas import (
    AmbiguityDiagnosis,
    ClarificationQuestion,
)

logger = logging.getLogger(__name__)


class ScopeDeAmbiguator:
    """Identify missing instructional boundaries without assuming a subject-specific template."""

    CAUSAL_ANCHORS: ClassVar[set[str]] = {
        "why",
        "how did",
        "causes",
        "caused",
        "consequences",
        "trigger",
        "explain how",
        "evaluate the extent",
        "mechanism",
        "compare",
        "analyze",
        "argue",
        "infer",
        "evaluate",
    }
    CONTEXTUAL_ANCHORS: ClassVar[set[str]] = {
        "century",
        "era",
        "period",
        "during",
        "between",
        "from",
        "module",
        "excerpt",
        "source",
        "case study",
        "chapter",
    }

    @classmethod
    def _has_scope_anchor(cls, prompt: str) -> bool:
        return bool(re.search(r"\b\d{3,4}\b", prompt)) or any(
            anchor in prompt for anchor in cls.CONTEXTUAL_ANCHORS
        )

    def evaluate_prompt_ambiguity(
        self,
        raw_prompt: str,
        domain: str = "history",
        course_id: UUID | None = None,
        module_id: UUID | None = None,
    ) -> AmbiguityDiagnosis:
        """Evaluate scope in terms a teacher can correct for any supported domain."""
        prompt_lower = raw_prompt.lower()
        words = re.findall(r"\w+", prompt_lower)
        has_scope = self._has_scope_anchor(prompt_lower)
        has_causal = any(anchor in prompt_lower for anchor in self.CAUSAL_ANCHORS)

        scope_score = 0.0 if has_scope else 0.40
        causal_score = 0.0 if has_causal else 0.35
        length_score = 0.0 if len(words) >= 15 else 0.25
        total_ambiguity = round(min(scope_score + causal_score + length_score, 1.0), 2)
        is_ambiguous = total_ambiguity > 0.30

        dimensions = {
            "contextual_boundary": "Specific" if has_scope else "Needs a setting, period, or conceptual boundary",
            "reasoning_demand": "Structured" if has_causal else "Needs a claim, comparison, or causal question",
            "scope_granularity": "Calibrated" if len(words) >= 15 else "Too brief / under-specified",
        }

        interview_questions: list[ClarificationQuestion] = []
        if is_ambiguous:
            interview_questions = [
                ClarificationQuestion(
                    question_id="Q1_TEMPORAL",
                    dimension="scope and boundary",
                    prompt="What setting, period, case, or conceptual boundary should students hold fixed?",
                    options=[
                        "Use the specific setting or time period named in the task.",
                        "Focus on the selected curriculum module and its assigned sources.",
                        "Define a narrower comparison or case before students begin.",
                    ],
                    default_recommendation="Focus on the selected curriculum module and its assigned sources.",
                ),
                ClarificationQuestion(
                    question_id="Q2_MISCONCEPTIONS",
                    dimension="cognitive trap",
                    prompt="What incomplete inference should the reasoning scaffold help students test?",
                    options=[
                        "Treating a single observation as proof of a broad conclusion.",
                        "Offering a single-cause explanation without weighing alternatives.",
                        "Restating a source without explaining how it supports a claim.",
                    ],
                    default_recommendation="Treating a single observation as proof of a broad conclusion.",
                ),
                ClarificationQuestion(
                    question_id="Q3_EVIDENCE",
                    dimension="evidence anchor",
                    prompt="Which assigned source or evidence type must students use in their response?",
                    options=[
                        "The primary source or reading attached to this module.",
                        "A course source plus one corroborating assigned text.",
                        "Evidence identified explicitly by the educator before publication.",
                    ],
                    default_recommendation="The primary source or reading attached to this module.",
                ),
            ]

        return AmbiguityDiagnosis(
            raw_prompt=raw_prompt,
            ambiguity_index=total_ambiguity,
            is_ambiguous=is_ambiguous,
            diagnosed_dimensions=dimensions,
            interview_questions=interview_questions,
        )


scope_deambiguator = ScopeDeAmbiguator()
