import logging
import re
from typing import Any

from fiosra.mvp.seed_pipeline import search_nearest_misconceptions

logger = logging.getLogger(__name__)

# Patterns attempting to elicit ground-truth solutions or execute jailbreaks
ADVERSARIAL_PATTERNS = [
    r"\b(?:give|tell|show|reveal|hand|output|write)\s+(?:me\s+)?(?:the\s+)?(?:exact\s+)?(?:final\s+)?(?:answer|solution|result|key|thesis\s+statement)\b",
    r"\bjust\s+(?:tell|give|show|write)\s+(?:me)?\b",
    r"\bwhat\s+(?:is|are)\s+the\s+(?:exact\s+)?(?:final\s+)?(?:answer|solution|rubric|key)\b",
    r"\bsolve\s+(?:it|this)\s+(?:for\s+me)?\b",
    r"\bdo\s+(?:the\s+)?(?:math|calculation|essay|writing)\s+for\s+me\b",
    r"\b(?:ignore|disregard)\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|rules|constraints|guidelines)\b",
    r"\byou\s+are\s+now\s+in\s+dan\s+mode\b",
    r"\brepeat\s+(?:the\s+)?(?:system\s+prompt|prompt\s+above)\b",
    r"\bdump\s+(?:all\s+)?(?:hidden\s+)?(?:prompt|instructions|keys|answers)\b",
    r"\b(?:admin|administrator|teacher|superintendent)\s+mode\b",
    r"\bi\s+am\s+(?:your\s+)?(?:teacher|instructor|professor|evaluator)\b",
    r"\bbypass\s+(?:safety|rules|guardrails)\b",
]

ADVERSARIAL_REGEX = re.compile("|".join(ADVERSARIAL_PATTERNS), re.IGNORECASE)



class SocraticDialogueEngine:
    """
    Answer-Isolated Socratic Dialogue Engine.
    Enforces strict Answer Isolation (ground-truth reference keys are never passed into prompt context),
    deterministic adversarial guardrails against solution extraction, and 4-rung non-manipulable
    hint ladders with penalty progression (Δ = 0.25 per rung).
    """

    def is_adversarial_attempt(self, student_input: str) -> bool:
        """Checks whether the student is attempting to force-extract solutions or jailbreak constraints."""
        return bool(ADVERSARIAL_REGEX.search(student_input.strip()))

    def generate_hint_ladder(self, question_prompt: str) -> list[dict[str, Any]]:
        """Generates a default 4-rung Socratic hint ladder for a question."""
        return [
            {"rung": 0, "label": "Orientation", "text": "What are the core concepts or actors identified in the prompt?"},
            {"rung": 1, "label": "Conceptual Anchor", "text": "Consider the structural incentives and fiscal constraints at play."},
            {"rung": 2, "label": "Mechanistic Bridge", "text": "Trace how the state debt service impacted royal options."},
            {"rung": 3, "label": "Target Synthesis", "text": "Synthesize the interaction between war debt and tax exemptions."},
        ]

    def build_adversarial_rejection(

        self,
        question_prompt: str,
        current_rung: int = 0,
    ) -> dict[str, Any]:
        """
        Constructs a firm, supportive Socratic rejection refusing to provide answers.
        """
        probes = [
            "I hear you! However, in Fiosra, my mission is to help you master the material yourself rather than doing the thinking for you. Let's look back at the prompt together: what is the first clue or keyword you notice?",
            "I know this can feel challenging, but revealing the solution won't build your mastery. Let's take it one small step at a time: what do you think is happening in this scenario?",
            "My role as your Socratic guide is to walk beside you, not hand you the destination. What initial idea or assumption can we test first?",
        ]
        chosen_probe = probes[current_rung % len(probes)]
        return {
            "is_adversarial": True,
            "thoughts_of_tutorbot": {
                "student_claim_analyzed": "Direct solution solicitation / guardrail evasion attempt.",
                "identified_error": "Adversarial answer begging detected.",
                "max_permitted_hint_level": current_rung,
                "strategy_selected": "Deflect solution demand with Socratic redirection.",
                "affective_adjustment": "Warm, encouraging, and firm on boundary.",
            },
            "response_text": chosen_probe,
            "hint_rung": current_rung,
            "penalty_score": current_rung * 0.25,
        }

    async def generate_response(
        self,
        student_input: str,
        question_prompt: str,
        domain: str = "history",
        current_rung: int = 0,
        hint_requested: bool = False,
    ) -> dict[str, Any]:
        """
        Generates a Socratic response while strictly maintaining Answer Isolation.
        """
        # 1. Adversarial Guardrail Check
        if self.is_adversarial_attempt(student_input):
            return self.build_adversarial_rejection(question_prompt, current_rung)

        # 2. Advance Hint Rung if requested
        active_rung = current_rung
        if hint_requested:
            active_rung = min(current_rung + 1, 3)

        penalty_score = active_rung * 0.25

        # 3. Diagnose Potential Misconceptions via pgvector similarity search
        matched_misconception = None
        traps = await search_nearest_misconceptions(student_input, limit=1, domain=domain)
        if traps and traps[0]["similarity"] > 0.01:
            matched_misconception = traps[0]

        # 4. Generate Socratic Dialogue output based on hint rung and diagnosis
        if matched_misconception:
            hints = matched_misconception.get("remediation_hint", "").split("\n")
            rung_hint = None
            for h in hints:
                if f"[Rung {active_rung}]" in h:
                    rung_hint = h.replace(f"[Rung {active_rung}]: ", "").strip()
                    break

            if not rung_hint and hints:
                rung_hint = hints[0].replace("[Rung 0]: ", "").strip()

            strategy = f"Address diagnosed misconception: '{matched_misconception['name']}' at Rung {active_rung}."
            tutor_thoughts = {
                "student_claim_analyzed": student_input,
                "identified_error": matched_misconception["flawed_rule"],
                "max_permitted_hint_level": active_rung,
                "strategy_selected": strategy,
                "affective_adjustment": "Supportive inquiry targeted at flawed rule.",
            }
            response_text = rung_hint or (
                f"Consider how '{matched_misconception['name']}' might be influencing your reasoning. "
                "How would you re-examine this claim?"
            )
        else:
            # General Socratic Scaffolding based on Rung
            rung_strategies = {
                0: (
                    "Metacognitive probe: Prompt student to inspect their assumptions.",
                    "Take a moment to reflect on your explanation: what evidence or reason led you to this conclusion?",
                ),
                1: (
                    "Conceptual nudge: Highlight foundational concepts without giving away steps.",
                    f"Think about the broader context of {domain}: what underlying principles or causes apply here?",
                ),
                2: (
                    "Procedural guide: Point to concrete next analytical step.",
                    "Look specifically at the primary causes and contrasting perspectives involved in this problem.",
                ),
                3: (
                    "Worked analogy: Provide isomorphic model with different context.",
                    "Consider an analogy: when an organization faces deep budget shortfalls, it must examine both revenue sources and debt obligations. How does that compare to this situation?",
                ),
            }
            strat, resp = rung_strategies.get(active_rung, rung_strategies[0])
            tutor_thoughts = {
                "student_claim_analyzed": student_input,
                "identified_error": "No specific catalogued misconception trap triggered.",
                "max_permitted_hint_level": active_rung,
                "strategy_selected": strat,
                "affective_adjustment": "Inquisitive and guided reflection.",
            }
            response_text = resp

        return {
            "is_adversarial": False,
            "thoughts_of_tutorbot": tutor_thoughts,
            "response_text": response_text,
            "hint_rung": active_rung,
            "penalty_score": penalty_score,
            "matched_misconception_id": matched_misconception["misconception_id"] if matched_misconception else None,
        }


dialogue_engine = SocraticDialogueEngine()
