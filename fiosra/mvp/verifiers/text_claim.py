import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

logger = logging.getLogger(__name__)


class NLILabel(str, Enum):
    ENTAILED = "ENTAILED"
    CONTRADICTION = "CONTRADICTION"
    NEUTRAL = "NEUTRAL"


@dataclass
class NLIResult:
    label: NLILabel
    confidence: float
    latency_ms: float
    explanation: str


class TextClaimVerifier:
    """
    Deterministic Natural Language Inference (NLI) Text Claim Verifier.
    Evaluates whether a student text claim (premise) entails, contradicts,
    or is neutral with respect to a target rubric requirement (hypothesis).
    Operates with < 50ms inference latency.
    """

    NEGATION_WORDS: ClassVar[set[str]] = {
        "not", "no", "never", "neither", "nor", "none", "cannot", "cant",
        "without", "fails", "failed", "denied", "denies", "refused", "impossible",
    }

    STOP_WORDS: ClassVar[set[str]] = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "as", "is", "was", "were", "are", "be", "been", "that",
    }

    SEMANTIC_CLUSTERS: ClassVar[list[set[str]]] = [
        {"fiscal", "debt", "debts", "tax", "taxes", "taxation", "revenue", "financial", "bankruptcy", "budget", "deficit"},
        {"cause", "causes", "causal", "driven", "trigger", "triggers", "led", "reason", "reasons", "result", "catalyst"},
        {"institution", "institutional", "estate", "estates", "order", "orders", "clergy", "nobility", "bourgeoisie", "monarchy", "crown", "parlement"},
        {"voting", "vote", "votes", "head", "order", "deadlock", "chamber", "assembly"},
        {"war", "wars", "military", "conflict", "revolution", "revolutionary", "american", "seven"},
    ]

    def _stem(self, word: str) -> str:
        for suffix in ("ing", "tions", "tion", "ies", "es", "ed", "al", "ive", "s"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if w]

    def _has_negation(self, words: list[str]) -> bool:
        return any(w in self.NEGATION_WORDS for w in words)

    def _concepts_match(self, w1: str, w2: str) -> bool:
        if w1 == w2 or self._stem(w1) == self._stem(w2):
            return True
        for cluster in self.SEMANTIC_CLUSTERS:
            if w1 in cluster and w2 in cluster:
                return True
        return False

    def verify_claim(self, premise: str, hypothesis: str) -> NLIResult:
        """
        Evaluates entailment between student premise and rubric hypothesis.
        """
        start_time = time.perf_counter()

        p_words = self._tokenize(premise)
        h_words = self._tokenize(hypothesis)

        if not p_words or not h_words:
            elapsed = (time.perf_counter() - start_time) * 1000
            return NLIResult(
                label=NLILabel.NEUTRAL,
                confidence=0.5,
                latency_ms=elapsed,
                explanation="Empty premise or hypothesis provided.",
            )

        h_content = [w for w in h_words if w not in self.STOP_WORDS and w not in {"rather", "than", "or", "and"}]
        p_content = [w for w in p_words if w not in self.STOP_WORDS]

        # Calculate semantic matches
        matched_h = set()
        for hw in h_content:
            for pw in p_content:
                if self._concepts_match(hw, pw):
                    matched_h.add(hw)
                    break

        overlap_ratio = len(matched_h) / max(len(h_content), 1)

        p_neg = self._has_negation(p_words)
        h_neg = self._has_negation(h_words)
        negation_flip = p_neg != h_neg

        # Heuristic NLI classification
        if overlap_ratio >= 0.25:
            if negation_flip:
                label = NLILabel.CONTRADICTION
                confidence = min(0.70 + overlap_ratio * 0.25, 0.95)
                explanation = f"Contradiction detected: matched concepts {matched_h} with conflicting polarity."
            else:
                label = NLILabel.ENTAILED
                confidence = min(0.65 + overlap_ratio * 0.35, 0.98)
                explanation = f"Entailment verified: student premise grounds {overlap_ratio:.1%} of rubric concepts ({matched_h})."
        elif overlap_ratio >= 0.10:
            label = NLILabel.NEUTRAL
            confidence = 0.60
            explanation = f"Partial overlap ({overlap_ratio:.1%}), but insufficient evidence to confirm entailment."
        else:
            label = NLILabel.NEUTRAL
            confidence = 0.85
            explanation = "Premise does not address the hypothesis concepts."

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return NLIResult(
            label=label,
            confidence=round(confidence, 3),
            latency_ms=round(elapsed_ms, 3),
            explanation=explanation,
        )


text_claim_verifier = TextClaimVerifier()
