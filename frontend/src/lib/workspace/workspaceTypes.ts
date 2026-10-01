export interface ChatTurn {
  role: 'student' | 'tutor';
  text: string;
  thoughts?: {
    pedagogical_goal?: string;
    identified_misconception?: string;
  };
  hint_rung?: number;
  is_adversarial?: boolean;
  action_capsules?: Array<{
    title?: string;
    suggested_student_text?: string;
    text_payload?: string;
    [key: string]: any;
  }>;
  prompt_launchers?: Array<{
    title: string;
    prompt: string;
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
