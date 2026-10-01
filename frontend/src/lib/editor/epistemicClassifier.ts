import type { EpistemicClassification, EpistemicConfigItem, EpistemicType, SentenceItem } from './editorTypes';

export const EPISTEMIC_CONFIG: Record<EpistemicType, EpistemicConfigItem> = {
  claim: { label: 'Claim', icon: '🔵', desc: 'Defensible assertion requiring warrant' },
  evidence: { label: 'Evidence', icon: '🟢', desc: 'Direct primary source observation or empirical citation' },
  reasoning: { label: 'Causal Reasoning', icon: '🟣', desc: 'Causal mechanism or explanatory warrant' },
  assumption: { label: 'Assumption', icon: '🟡', desc: 'Implicit presupposition taken for granted' },
  premature_closure: { label: 'Premature Closure', icon: '🔴', desc: 'Conclusion leap asserted without sufficient backing' },
};

/**
 * Sentence Segmentation & Fast Local Epistemic Classifier
 */
export function localSentenceClassify(text: string, priorEvidenceSeen = false): EpistemicClassification {
  const t = text.trim();
  const tLow = t.toLowerCase();

  const isEvidence = /(?:source|evidence|report|study|data|observed|according to|citation)\b/i.test(tLow) || /[“"”].+?[“"”]/.test(t);
  const isCausal = /(?:because|leads? to|results? in|causes?|mechanism|due to|explains? why|therefore enables)\b/i.test(tLow);
  const isAssumption = /(?:assume|presume|suppose|inherently|naturally|obviously|inevitable|must be)\b/i.test(tLow);
  const isPremature = /(?:therefore|thus|hence|in conclusion|consequently|clearly proves?)\b/i.test(tLow) && !priorEvidenceSeen;

  if (isEvidence) {
    return {
      epistemic_type: 'evidence',
      confidence: 0.95,
      source_grounded: true,
      oracle_probe: 'Which specific details in this source directly verify your inference?',
    };
  }
  if (isPremature) {
    return {
      epistemic_type: 'premature_closure',
      confidence: 0.92,
      oracle_probe: 'You reached a conclusion, but what established evidence in your document has already justified this leap?',
    };
  }
  if (isAssumption) {
    return {
      epistemic_type: 'assumption',
      confidence: 0.88,
      oracle_probe: 'What unstated premise must hold true for this assertion, and what happens if it is invalid?',
    };
  }
  if (isCausal) {
    return {
      epistemic_type: 'reasoning',
      confidence: 0.90,
      oracle_probe: 'What mechanism connects the condition you describe to that outcome?',
    };
  }
  return {
    epistemic_type: 'claim',
    confidence: 0.85,
    oracle_probe: 'What empirical detail in an approved source could you point to before making this claim?',
  };
}

export function splitIntoSentences(
  text: string,
  baseOffset: number,
  sentenceMap: Record<string, EpistemicClassification> = {}
): SentenceItem[] {
  if (!text || text.trim().length < 10) return [];
  if (!/[a-zA-Z]{3,}/.test(text)) return [];
  const results: SentenceItem[] = [];
  const regex = /[^.!?]+(?:[.!?]+["'”’]?|\s*$)/g;
  let match: RegExpExecArray | null;
  let priorEvidence = false;

  while ((match = regex.exec(text)) !== null) {
    const sentenceText = match[0];
    const trimmed = sentenceText.trim();
    if (trimmed.length >= 10 && /[a-zA-Z]{3,}/.test(trimmed)) {
      const leadingWhitespace = sentenceText.indexOf(trimmed);
      const from = baseOffset + match.index + leadingWhitespace;
      const to = from + trimmed.length;

      // Check cache or run fast local classifier
      let classification = sentenceMap[trimmed];
      if (!classification) {
        classification = localSentenceClassify(trimmed, priorEvidence);
        sentenceMap[trimmed] = classification;
      }
      if (classification.epistemic_type === 'evidence') priorEvidence = true;

      results.push({
        from,
        to,
        text: trimmed,
        ...classification,
      });
    }
  }
  return results;
}
