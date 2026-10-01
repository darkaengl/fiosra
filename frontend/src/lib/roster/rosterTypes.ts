export interface Student {
  student_id: string;
  name?: string;
  status?: string;
  completed_assignments?: number;
  active_struggle?: boolean;
  assignment_id?: string;
  assignment_title?: string;
  latest_session_id?: string;
  session_count?: number;
  average_autonomy_score?: number;
  hint_frequency?: number;
  critical_thinking_flags?: string[];
  frontier_concept?: string;
  concept_states?: Record<string, 'mastered' | 'partial' | 'trapped' | 'locked'>;
}

export interface GraphNode {
  id?: string;
  concept_id?: string;
  label?: string;
  level?: string;
  rank?: number;
  concept_type?: string;
  module_id?: string;
  parent_id?: string;
  struggling_count?: number;
  active_trigger_count?: number;
  bloom_level?: string;
  definition?: string;
  cohort_mastery_rate?: number;
  total_assessed?: number;
  active_misconceptions?: Array<{
    misconception_id?: string;
    quote?: string;
    prompt?: string;
  }>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation?: string;
}

export interface Probe {
  probe_id?: string;
  kc_id?: string;
  concept_id?: string;
  probe_tier?: number;
  probe_type?: string;
  prompt?: string;
  question_text?: string;
}

export interface MasteryData {
  bottlenecks?: string[];
  students?: Student[];
  graph?: {
    nodes?: GraphNode[];
    edges?: GraphEdge[];
    probes?: Probe[];
  };
}

export interface CourseModule {
  module_id: string;
  title: string;
  position: number;
}

export interface CourseDetails {
  course_id?: string;
  title?: string;
  modules?: CourseModule[];
}

export type RosterFilter = 'all' | 'completed' | 'submitted' | 'struggling' | 'in_progress';
export type ViewType = 'table' | 'graph';
export type GraphPerspective = 'cohort' | 'student';
