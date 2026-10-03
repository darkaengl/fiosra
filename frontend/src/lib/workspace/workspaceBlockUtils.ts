export interface CanonicalBlock {
  block_id: string;
  block_type?: string;
  plaintext?: string;
  semantic_type?: string;
  position?: number;
  section_id?: string;
  text: string;
  canonical_type: string;
  has_premature: boolean;
  content?: any;
}

export function canonicalBlockAnalysis(block: any): CanonicalBlock {
  const text = (block.plaintext || '').trim();
  if (block.block_type === 'heading') {
    return { ...block, text, canonical_type: 'heading', has_premature: false };
  }
  const suppliedType = block.semantic_type || block.content?.attrs?.semanticType;
  const validTypes = new Set(['claim', 'evidence', 'reasoning', 'assumption', 'counter', 'conclusion']);
  let canonicalType = validTypes.has(suppliedType) ? suppliedType : '';
  if (!canonicalType) {
    const likelyEvidence = /\b(?:the|this) (?:source|report|text|record|excavation|material)\s+(?:describes|states|shows|records|notes|documents)\b/i.test(text);
    const likelyReasoning = /\b(?:because|therefore|thus|consequently|which means|this suggests|as a result|leads? to)\b/i.test(text);
    const likelyAssumption = /\b(?:assumes?|taken for granted|must have|obviously)\b/i.test(text);
    canonicalType = likelyAssumption ? 'assumption'
      : likelyReasoning ? 'reasoning'
        : likelyEvidence ? 'evidence'
          : 'claim';
  }
  const hasPremature = /(?:therefore|thus|hence|in conclusion|consequently)\b/i.test(text)
    && !/\b(?:source|evidence|data|table|figure|report)\b/i.test(text);
  return { ...block, text, canonical_type: canonicalType, has_premature: hasPremature };
}

export function computeGraphMetrics(canonicalBlocks: CanonicalBlock[], probes: any[] = []) {
  let c = 0, e = 0, w = 0, a = 0, p = 0;
  for (const b of canonicalBlocks) {
    const sem = b.canonical_type;
    if (sem === 'claim') c++;
    else if (sem === 'evidence') e++;
    else if (sem === 'reasoning') w++;
    else if (sem === 'assumption') a++;
    if (probes.some((pr) => pr.block_id === b.block_id && pr.status !== 'superseded')) p++;
  }
  return { claims: c, evidence: e, warrants: w, assumptions: a, probes: p };
}

export function normalizeAssignmentSources(publishedOrAssignment: any): any[] {
  const published = publishedOrAssignment?.published || publishedOrAssignment;
  const list = published?.source_pack
    || publishedOrAssignment?.grounding_sources
    || published?.sources
    || publishedOrAssignment?.sources
    || [];
  return list.map((s: any, idx: number) => ({
    source_id: s.source_id || s.id || `src_${idx + 1}`,
    author: s.author || s.citation || s.title || 'Primary Source',
    title: s.title || s.source_title || `Primary Source ${idx + 1}`,
    date: s.date || 'Assigned Document',
    provenance: s.provenance || s.citation || '',
    passage: s.passage || s.excerpt || s.text || '',
    hidden_context: s.hidden_context || s.synopsis || s.relevance_guidance || '',
    target_kc: s.target_kc || s.kc || 'KC_EVIDENCE',
    source_url: s.source_url || s.url || s.download_url || null,
    relevance_guidance: s.relevance_guidance || '',
    resource_type: s.resource_type || 'Primary Source',
    excerpt: s.passage || s.excerpt || s.text || '',
    citation: s.provenance || s.citation || '',
  }));
}
