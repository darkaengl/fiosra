export interface SourceCard {
  source_id: string;
  title: string;
  excerpt: string;
  source_url: string;
  citation: string;
  relevance_guidance: string;
}

export interface RubricLevel {
  level_id: string;
  label: string;
  description: string;
}

export interface RubricCriterion {
  criterion_id: string;
  title: string;
  description: string;
  weight: number;
  levels: RubricLevel[];
  self_review_prompt?: string;
  concept_id?: string;
  concept_label?: string;
  target_kc?: string;
}

export interface AssignmentContract {
  title: string;
  purpose: string;
  task: {
    prompt: string;
    scope: string;
    deliverable: string;
    requirements: string[];
  };
  learning_goals: string[];
  source_pack: SourceCard[];
  public_rubric: RubricCriterion[];
  start_options: string[];
  support_menu: Array<{ action_id: string; title: string; description: string }>;
  completion_checklist: string[];
  integrity_notice: string;
  version_note?: string | null;
}

export interface EvaluationPlan {
  public_rubric_map: Array<{
    public_criterion_id: string;
    concept_ids: string[];
    source_chunk_ids: string[];
    evidence_expectation: string;
  }>;
  completion_states: string[];
  support_policy: string[];
  evidence_capture_notice: string;
  review_policy: string;
}
