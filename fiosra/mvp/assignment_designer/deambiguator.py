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
    """
    AI Pedagogical Scope De-Ambiguator Co-Pilot.
    Analyzes raw educator assignment prompts for ambiguity across:
    1. Temporal boundary specificity
    2. Causal mechanism inquiry
    3. Curriculum Knowledge Component anchoring
    When ambiguity > 30%, synthesizes a 3-question alignment interview.
    """

    TEMPORAL_ANCHORS: ClassVar[set[str]] = {
        "1787", "1788", "1789", "1790", "1791", "1792", "1793", "1794",
        "pre-revolution", "ancien regime", "estates-general", "tennis court",
        "bastille", "august 4", "declaration of rights", "constitutional monarchy",
    }

    CAUSAL_ANCHORS: ClassVar[set[str]] = {
        "why", "how did", "causes", "caused", "consequences", "trigger",
        "explain how", "evaluate the extent", "mechanism", "fiscal collapse",
        "debt crisis", "voting by head", "tax exemptions",
    }

    def evaluate_prompt_ambiguity(
        self,
        raw_prompt: str,
        domain: str = "history",
        course_id: UUID | None = None,
    ) -> AmbiguityDiagnosis:
        """
        Evaluates prompt ambiguity and generates a 3-question educator interview if needed.
        """
        prompt_lower = raw_prompt.lower()
        words = re.findall(r"\w+", prompt_lower)

        # 1. Temporal Boundary Evaluation
        has_temporal = any(anchor in prompt_lower for anchor in self.TEMPORAL_ANCHORS)
        temporal_score = 0.0 if has_temporal else 0.40

        # 2. Causal Mechanism Evaluation
        has_causal = any(anchor in prompt_lower for anchor in self.CAUSAL_ANCHORS)
        causal_score = 0.0 if has_causal else 0.35

        # 3. Prompt Length / Specificity
        length_score = 0.0 if len(words) >= 15 else 0.25

        total_ambiguity = round(min(temporal_score + causal_score + length_score, 1.0), 2)
        is_ambiguous = total_ambiguity > 0.30

        dimensions = {
            "temporal_boundary": "Specific" if has_temporal else "Ambiguous / Open-ended epoch",
            "causal_inquiry": "Structured" if has_causal else "Descriptive / Lacks causal mechanism",
            "scope_granularity": "Calibrated" if len(words) >= 15 else "Too brief / Under-specified",
        }

        interview_questions: list[ClarificationQuestion] = []
        if is_ambiguous:
            interview_questions = [
                ClarificationQuestion(
                    question_id="Q1_TEMPORAL",
                    dimension="temporal_scope",
                    prompt="What specific temporal window or phase of the French Revolution should students analyze?",
                    options=[
                        "Pre-revolutionary fiscal crisis and structural royal debt (1787–May 1789)",
                        "Estates-General standoff and popular mobilization in Paris (May–July 1789)",
                        "Constitutional monarchy overhaul and August Decrees (August 1789–1791)",
                    ],
                    default_recommendation="Pre-revolutionary fiscal crisis and structural royal debt (1787–May 1789)",
                ),
                ClarificationQuestion(
                    question_id="Q2_MISCONCEPTIONS",
                    dimension="cognitive_traps",
                    prompt="Which common student misconception trap should this assignment specifically diagnose and remediate?",
                    options=[
                        "Attributing the fiscal collapse solely to Marie Antoinette's dresses rather than war debt (MISC_HIST_006)",
                        "Assuming the Third Estate was purely poor peasants, erasing the educated bourgeoisie (MISC_HIST_007)",
                        "Believing doubling the Third Estate gave them power without voting by head (MISC_HIST_009)",
                    ],
                    default_recommendation="Attributing the fiscal collapse solely to Marie Antoinette's dresses rather than war debt (MISC_HIST_006)",
                ),
                ClarificationQuestion(
                    question_id="Q3_EVIDENCE",
                    dimension="evidence_anchor",
                    prompt="What primary evidence or document type should students cite to substantiate their claims?",
                    options=[
                        "Cahiers de Doléances (parish grievance petitions)",
                        "Necker's Compte Rendu au Roi and sovereign debt interest tables",
                        "Decrees of the National Assembly and Tennis Court Oath declaration",
                    ],
                    default_recommendation="Necker's Compte Rendu au Roi and sovereign debt interest tables",
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
