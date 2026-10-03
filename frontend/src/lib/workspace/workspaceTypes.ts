export interface ChatTurn {
  role: 'student' | 'tutor';
  text: string;
  thoughts?: string | {
    pedagogical_goal?: string;
    identified_misconception?: string;
    [key: string]: any;
  };
  hint_rung?: number;
  is_adversarial?: boolean;
  radar?: any;
  action_capsules?: Array<{
    title?: string;
    suggested_student_text?: string;
    text_payload?: string;
    [key: string]: any;
  }>;
  prompt_launchers?: Array<{
    title?: string;
    prompt?: string;
    text?: string;
    category?: string;
    [key: string]: any;
  }>;
}

export interface ChatSession {
  id: string;
  title: string;
  startedAt: string;
  turns: ChatTurn[];
}

export interface ConsultationThread {
  student: string;
  tutor: string;
  concept: string;
  capsule: string;
}

export interface SupportItem {
  action_id: string;
  title: string;
  description: string;
}

export interface SupportResult {
  title: string;
  guidance: string;
  next_steps: string[];
}

export interface Probe {
  probe_id: string;
  question: string;
  focus_type: string;
  section_label?: string;
  [key: string]: any;
}
