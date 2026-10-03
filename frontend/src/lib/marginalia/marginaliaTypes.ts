/**
 * Socratic Marginalia types and focus definitions
 */

export interface FocusTypeInfo {
  label: string;
  icon: string;
  color: string;
}

export const FOCUS_TYPE_LABELS: Record<string, FocusTypeInfo> = {
  direct_observation: { label: 'Direct Observation', icon: '🔍', color: 'var(--color-aurora, #0284c7)' },
  warrant: { label: 'Warrant Required', icon: '⚖️', color: 'var(--color-amber, #d97706)' },
  causal_bridge: { label: 'Causal Bridge', icon: '🌉', color: 'var(--color-signal-green, #10b981)' },
  alternative_explanation: { label: 'Alternative Hypothesis', icon: '🔄', color: 'var(--color-horizon-blue, #3b82f6)' },
  qualification: { label: 'Nuance & Scope', icon: '🎯', color: 'var(--color-slate-light, #64748b)' },
};

export interface SocraticProbe {
  probe_id: string;
  block_id?: string;
  status: 'offered' | 'deferred' | 'responded' | 'dismissed';
  focus_type?: string;
  concept_id?: string;
  concept_label?: string;
  confidence_stance?: string;
  scaffolding_rung?: number;
  claim_text?: string;
  assumption?: string;
  implicit_premise?: string;
  question: string;
  response_text?: string;
}

export interface InstructorIntervention {
  intervention_id: string;
  block_id?: string;
  status: 'dispatched' | 'responded' | 'acknowledged';
  concept_label?: string;
  evidence_quote?: string;
  activity_prompt: string;
  activity_guidance?: string;
  student_reflection?: string;
  instructor_feedback?: string;
}
