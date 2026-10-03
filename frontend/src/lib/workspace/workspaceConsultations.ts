import type { ChatSession, ConsultationThread } from './workspaceTypes';

export const DEFAULT_CONSULTATIONS: Record<string, ConsultationThread> = {
  julian_hayes: {
    student: "Should Dara locate right outside the library main doors? Footfall is over 1,200 students per hour, so volume will be guaranteed.",
    tutor: "Consider the operational reality of library traffic: students entering are rushing to quiet study spaces or have 5-minute passing periods. What percentage of that footfall actually has the dwell time to purchase handcrafted pour-overs, and what does the case exhibit say about campus administration permits near library steps?",
    concept: "Place & Operational Footfall Quality",
    capsule: "Examine Footfall Dwell Time & Permits"
  },
  elena_rostova: {
    student: "To maximize revenue, Dara should offer 14 flavored syrups, smoothies, matcha lattes, and fresh pastries alongside espresso.",
    tutor: "Examine Dara's operational bottleneck: a single-group espresso cart with one operator. What happens to customer queue wait times when preparing a 5-step blended smoothie versus pulling an espresso? How does inventory spoilage on 14 perishables affect unit net contribution?",
    concept: "Product Depth & Throughput Constraints",
    capsule: "Analyze Prep Bottlenecks & Spoilage"
  },
  marcus_chen: {
    student: "The cart needs to hit 400 cups daily at $2.25 to make the $600 weekly campus licensing fee manageable.",
    tutor: "Let's check the throughput physics: in an 8-hour operating window, 400 cups requires preparing, brewing, and transacting a cup every 72 seconds without pause. Is that sustainable for a solo barista, or should Dara adjust Price to capture higher margin on lower, sustainable volume?",
    concept: "Price Margin vs Unit Volume Physics",
    capsule: "Calculate Realistic Peak Limits"
  },
  priya_patel: {
    student: "I've settled on premium fair-trade beans and a luxury artisan brand identity, priced at $2.00 per 16oz cup with flyers posted around freshman dorms.",
    tutor: "Look closely at the alignment across the 4Ps: if Product is luxury artisan, does a bargain-basement $2.00 Price signal quality or cheapness? And do paper flyers in dorms reach graduate researchers and faculty with higher willingness-to-pay?",
    concept: "4Ps Interlocking Consistency",
    capsule: "Audit Premium Signaling Across All 4Ps"
  },
  david_kim: {
    student: "I calculated $3,000 monthly profit by placing at the library plaza and selling 250 iced drinks daily.",
    tutor: "Have you factored in weather seasonality and the semester break schedule? During winter exams and rain, outdoor library plaza footfall drops 65%. How does your financial model absorb fixed cart amortization during slow months?",
    concept: "Place Weather Vulnerability & Fixed Costs",
    capsule: "Stress-Test Model for Rain Volume"
  },
  maya_lin: {
    student: "Can we sell cold brew kegs and light roast single origins while keeping the menu under 5 core items?",
    tutor: "A focused 5-item menu drastically reduces preparation time and waste! How does offering batch-tapped cold brew solve the morning rush peak bottleneck compared to custom steam-wand drinks?",
    concept: "Product Streamlining & Service Velocity",
    capsule: "Evaluate Tapped Batch vs Manual Steam Yield"
  },
  liam_oconnor: {
    student: "Everyone says the engineering quad has fewer students than the library, but engineering students spend longer hours on campus.",
    tutor: "Excellent observation. Look at the survey data in Exhibit 2: engineering and STEM graduate students have 3.2x higher afternoon repeat purchase rates and prioritize specialty roast caffeine over budget drip coffee. How does this reframe the Place decision?",
    concept: "Place Targeting & Repeat Frequency",
    capsule: "Review Exhibit 2 Afternoon Repeat Purchase Data"
  },
  sofia_rodriguez: {
    student: "If Dara offers pre-ordered digital pickup via a mobile app, can we eliminate queue friction completely?",
    tutor: "Mobile pickup streamlines ordering, but think about cart space: where do finished drinks sit without getting cold while waiting for pickup on a 4-foot outdoor cart? How can Promotion communicate specific pickup windows?",
    concept: "Promotion & Cart Staging Capacity",
    capsule: "Assess Physical Counter Space for Orders"
  },
  aisha_almansoor: {
    student: "I want to align Price and Place by setting up next to the graduate business school at a $4.75 price point.",
    tutor: "Notice how well that aligns: high discretionary budget, appreciation for single-origin sourcing, and willingness to pay premium prices. What promotional strategy best matches this demographic without seeming intrusive?",
    concept: "Target Market Alignment & Margin Capture",
    capsule: "Design Targeted B-School Promotional Channel"
  },
  lucas_bennett: {
    student: "Should Dara negotiate a revenue-share permit with the Student Center instead of paying a fixed $600 weekly fee?",
    tutor: "A revenue-share fee converts fixed overhead into variable costs, protecting Dara against rainy days and exam breaks. How does this lower break-even risk and allow more flexible pricing?",
    concept: "Overhead Structure & Downside Risk Hedging",
    capsule: "Model Fixed vs Variable Permit Sensitivity"
  },
  clara_oswald: {
    student: "I'm starting my initial analysis of Dara's Coffee Cart. What should I prioritize first?",
    tutor: "Start by examining the 4Ps foundation: Product, Price, Place, and Promotion. Review the primary source exhibits on the left, then outline your core thesis on this fresh canvas.",
    concept: "4Ps Foundations & Inquiry Scaffolding",
    capsule: "Examine 4Ps Case Exhibits to Formulate Thesis"
  },
};

export function buildDefaultChatForStudent(sid?: string): ChatSession[] {
  const key = sid || 'julian_hayes';
  const thread = DEFAULT_CONSULTATIONS[key] || {
    student: "Can you help me evaluate the 4Ps trade-offs in my marketing plan?",
    tutor: "Look closely at how each P interacts with the others. If Product is positioned as premium handcrafted coffee, how does that constrain your choices for Price, Place, and Promotion?",
    concept: "4Ps Strategic Synthesis",
    capsule: "Check Coherence of the 4Ps"
  };

  return [
    {
      id: `chat_${sid || 'init'}_1`,
      title: thread.concept.slice(0, 24) + '…',
      startedAt: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
      turns: [
        {
          role: 'student',
          text: thread.student,
        },
        {
          role: 'tutor',
          text: thread.tutor,
          thoughts: {
            pedagogical_goal: `Challenge student assumptions regarding ${thread.concept}`,
            identified_misconception: thread.concept,
          },
          hint_rung: 1,
          is_adversarial: false,
          action_capsules: [],
          prompt_launchers: [
            {
              title: thread.capsule,
              prompt: `Can you help me test my assumptions about ${thread.concept.toLowerCase()}?`,
            }
          ],
        }
      ],
    }
  ];
}

export function getChatStorageKey(aid?: string, sid?: string): string {
  return `fiosra_chat_${aid || 'daras'}_${sid || 'default'}`;
}

export function loadStoredChatSessions(aid?: string, sid?: string): ChatSession[] {
  if (typeof localStorage === 'undefined') return buildDefaultChatForStudent(sid);
  const key = getChatStorageKey(aid, sid);
  const stored = localStorage.getItem(key);
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length > 0) {
        const sanitized = parsed.map((cs: any) => ({
          ...cs,
          turns: (cs.turns || [])
            .filter(
              (t: any) => !(t.role === 'tutor' && typeof t.text === 'string' && t.text.includes('Socratic Tutor is currently unavailable'))
            )
            .map((t: any) => ({
              ...t,
              action_capsules: (t.action_capsules || []).filter(
                (c: any) => Boolean((c.suggested_student_text || c.text_payload)?.trim())
              ),
            })),
        })).filter((cs: any) => cs.turns.length > 0);

        if (sanitized.length > 0) {
          return sanitized;
        }
      }
    } catch (e) {
      console.warn('Failed to parse stored chat sessions:', e);
    }
  }
  return buildDefaultChatForStudent(sid);
}

export function persistChatSessions(sessions: ChatSession[], aid?: string, sid?: string): void {
  if (sid && typeof localStorage !== 'undefined') {
    try {
      localStorage.setItem(getChatStorageKey(aid, sid), JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to save chat sessions to localStorage:', e);
    }
  }
}

export function createNewChatSession(existingCount: number): ChatSession {
  const nextNum = existingCount + 1;
  return {
    id: `chat_${crypto.randomUUID().slice(0, 8)}`,
    title: `Consultation ${nextNum}`,
    startedAt: new Date().toISOString(),
    turns: [
      {
        role: 'tutor',
        text: `Welcome to Consultation ${nextNum}. How can I assist your critical inquiry today?`,
        thoughts: { pedagogical_goal: 'Fresh session initialization' },
        hint_rung: 1,
        is_adversarial: false,
        action_capsules: [],
        radar: null,
        prompt_launchers: [
          { title: "Evaluate evidence", prompt: "Help me evaluate my evidence", text: "Help me evaluate my evidence", category: "evidence" },
          { title: "Check arguments", prompt: "Check my argument structure", text: "Check my argument structure", category: "reasoning" }
        ]
      }
    ]
  };
}

export interface SocraticMessageParams {
  sessionId: string;
  studentId: string;
  assignmentId?: string;
  assignment: any;
  learningDocument: any;
  studentInput: string;
  hintRequested?: boolean;
  sessionHeaders: () => Record<string, string>;
}

export interface SocraticMessageResult {
  tutorTurn: any;
  hintRung?: number;
  success: boolean;
}

export async function sendSocraticMessage({
  sessionId,
  studentId,
  assignmentId,
  assignment,
  learningDocument,
  studentInput,
  hintRequested = false,
  sessionHeaders,
}: SocraticMessageParams): Promise<SocraticMessageResult> {
  const prompt = assignment?.published?.task?.prompt || assignment?.task?.prompt || assignment?.prompt || 'Explore structural historical causation';
  const qId = learningDocument?.question_id || assignment?.question_id || 'q1';
  try {
    const res = await fetch('/dialogue/message', {
      method: 'POST',
      headers: sessionHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        student_id: studentId,
        question_id: qId,
        student_input: studentInput,
        question_prompt: prompt,
        domain: assignment?.domain || 'history',
        hint_requested: hintRequested,
        assignment_id: assignmentId || null,
      }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || 'Dialogue service unavailable');
    }
    const data = await res.json();
    const tutorTurn = {
      role: 'tutor',
      text: data.response_text,
      thoughts: data.thoughts_of_tutorbot,
      hint_rung: data.hint_rung,
      is_adversarial: data.is_adversarial,
      action_capsules: data.action_capsules || [],
      radar: data.learner_radar || null,
      prompt_launchers: data.prompt_launchers || [],
    };
    return {
      tutorTurn,
      hintRung: data.hint_rung,
      success: true,
    };
  } catch (err: any) {
    console.error('Macro dialogue error:', err);
    const errorTurn = {
      role: 'tutor',
      text: `⚠️ Socratic Tutor is currently unavailable: ${err.message || 'LLM service connection required'}. Please ensure your LLM provider is configured and running.`,
      is_adversarial: false,
      hint_rung: 0,
      action_capsules: [],
      radar: null,
    };
    return {
      tutorTurn: errorTurn,
      hintRung: 0,
      success: false,
    };
  }
}

