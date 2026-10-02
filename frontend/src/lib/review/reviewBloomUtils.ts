import type { BloomDefinition, BloomEvaluation, RubricCriterionEvidence } from './reviewTypes.js';

export const BLOOM_LEVELS: Record<string, BloomDefinition> = {
  remember: { level: 1, name: "Remember", color: "#475569", bg: "#f1f5f9", border: "#cbd5e1", badge: "L1 Remember" },
  understand: { level: 2, name: "Understand", color: "#0284c7", bg: "#f0f9ff", border: "#bae6fd", badge: "L2 Understand" },
  apply: { level: 3, name: "Apply", color: "#0d9488", bg: "#f0fdfa", border: "#99f6e4", badge: "L3 Apply" },
  analyze: { level: 4, name: "Analyze", color: "#d97706", bg: "#fffbeb", border: "#fde68a", badge: "L4 Analyze" },
  evaluate: { level: 5, name: "Evaluate", color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", badge: "L5 Evaluate" },
  create: { level: 6, name: "Create", color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", badge: "L6 Create" },
};

export function hasEvidence(criterion?: RubricCriterionEvidence | null): boolean {
  if (!criterion || !criterion.evidence) return false;
  const ev = String(criterion.evidence).trim().toLowerCase();
  return !ev.includes("no student evidence") && !ev.includes("unassessed");
}

export function getCriterionBloom(criterion?: RubricCriterionEvidence | null): BloomEvaluation {
  const id = String(criterion?.criterion_id || "").toLowerCase();
  const label = String(criterion?.label || "").toLowerCase();
  const desc = String(criterion?.description || "").toLowerCase();
  const evText = String(criterion?.evidence || "").toLowerCase();

  let target = BLOOM_LEVELS.analyze;
  let weight = "20%";
  let demandDesc = "Dissect quantitative data and evaluate causal trade-offs";

  if (
    id.includes("advice") ||
    label.includes("advice") ||
    desc.includes("actionable decisions") ||
    desc.includes("elements of the marketing mix")
  ) {
    target = BLOOM_LEVELS.evaluate;
    weight = "25%";
    demandDesc = "Defend strategic decisions & justify choices against rejected alternatives";
  } else if (
    id.includes("reasoning") ||
    label.includes("reasoning") ||
    desc.includes("quantitative") ||
    desc.includes("footfall") ||
    desc.includes("costs")
  ) {
    target = BLOOM_LEVELS.analyze;
    weight = "25%";
    demandDesc = "Analyze quantitative footfall, margin & walk-time trade-offs from case data";
  } else if (
    id.includes("book") ||
    label.includes("book") ||
    desc.includes("marketing concepts") ||
    desc.includes("openstax")
  ) {
    target = BLOOM_LEVELS.apply;
    weight = "20%";
    demandDesc = "Apply theoretical 4Ps marketing frameworks directly to the business scenario";
  } else if (
    id.includes("structure") ||
    label.includes("structure") ||
    desc.includes("synthesizes") ||
    desc.includes("cohesive")
  ) {
    target = BLOOM_LEVELS.create;
    weight = "20%";
    demandDesc = "Synthesize four distinct marketing decisions into a unified strategic plan";
  } else if (
    id.includes("clarity") ||
    label.includes("clarity") ||
    desc.includes("400 words") ||
    desc.includes("length")
  ) {
    target = BLOOM_LEVELS.understand;
    weight = "10%";
    demandDesc = "Communicate clear executive reasoning within concise bounds";
  }

  // Determine demonstrated Bloom tier from student quote text
  let demonstrated: BloomDefinition | null = null;
  if (hasEvidence(criterion)) {
    if (criterion?.met) {
      demonstrated = target;
    } else {
      const hasCausal = /(?:because|therefore|leads? to|results? in|trade-off|versus|rather than|justified|constrained)/i.test(evText);
      const hasNumbers = /\d+/.test(evText);
      if (target.level >= 5 && hasCausal) {
        demonstrated = BLOOM_LEVELS.analyze;
      } else if (hasNumbers || hasCausal) {
        demonstrated = BLOOM_LEVELS.apply;
      } else {
        demonstrated = BLOOM_LEVELS.remember;
      }
    }
  }

  return {
    target,
    weight,
    demandDesc,
    demonstrated,
  };
}
