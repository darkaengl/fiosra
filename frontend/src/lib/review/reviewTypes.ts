export interface BloomDefinition {
  level: number;
  name: string;
  color: string;
  bg: string;
  border: string;
  badge: string;
}

export interface BloomEvaluation {
  target: BloomDefinition;
  weight: string;
  demandDesc: string;
  demonstrated: BloomDefinition | null;
}

export interface QueueItem {
  session_id: string;
  student_id: string;
  status: 'submitted' | 'completed' | 'active' | string;
  assignment_id?: string;
  assignment_title?: string;
  submitted_at?: string;
  suggested_grade?: string;
}

export interface RubricCriterionEvidence {
  criterion_id?: string;
  label?: string;
  description?: string;
  met?: boolean;
  evidence?: string;
  explanation?: string;
}

export interface QuestionEvidence {
  question_id?: string;
  rubric_evidence?: Record<string, RubricCriterionEvidence>;
}

export interface ReviewDossier {
  session_id: string;
  student_id: string;
  per_question_evidence?: QuestionEvidence[];
  [key: string]: any;
}

export interface MisconceptionFinding {
  misconception_id: string;
  name: string;
  flawed_rule?: string;
  evidence_quote?: string;
  why?: string;
  remediation_hint?: string;
  activity_prompt?: string;
  activity_guidance?: string;
  activity_type?: string;
  detection?: 'llm_verified' | string;
  concept_id?: string;
  concept_label?: string;
  document_id?: string;
  block_id?: string;
  suggested_message?: {
    subject?: string;
    body?: string;
  };
}

export interface InterventionRecord {
  intervention_id: string;
  misconception_id: string;
  status: 'dispatched' | 'acknowledged' | 'responded' | string;
  student_response?: string;
  dispatched_at?: string;
}
