import type { SourceCard, RubricCriterion, AssignmentContract, EvaluationPlan } from './authoringTypes';

export function sourceCards(sources: any[] = []): SourceCard[] {
  return sources.map((source, index) => ({
    source_id: `source_${index + 1}`,
    title: source.title || `Primary Source Document ${index + 1}`,
    excerpt: source.excerpt || 'Historical text excerpt for student inquiry...',
    source_url: source.source_url || '',
    citation: source.citation || source.title || 'Course Material',
    relevance_guidance: source.relevance_guidance || 'Use this source to ground and support your argument.',
  }));
}

export function publicRubric(rules: any[] = []): RubricCriterion[] {
  const rawTotal = rules.reduce((total, rule) => total + Number(rule.weight || 0), 0);
  let allocated = 0;
  return rules.map((rule, index) => {
    let weight = rawTotal ? Math.round((Number(rule.weight || 0) / rawTotal) * 10000) / 100 : 0;
    if (rawTotal && index === rules.length - 1) {
      weight = Math.round((100 - allocated) * 100) / 100;
    }
    allocated += weight;
    const criterionTitle = rule.title || rule.label || `Criterion ${index + 1}`;
    const criterionLevels = (rule.levels && rule.levels.length >= 3)
      ? rule.levels
      : [
          { level_id: 'developing', label: 'Developing', description: 'Partial synthesis; relies on unsubstantiated assumptions or summary.' },
          { level_id: 'secure', label: 'Secure', description: 'Clear, grounded analysis supported by citations from the assigned materials.' },
          { level_id: 'strong', label: 'Strong', description: 'Sophisticated historical reasoning, nuanced causal analysis, and precise source integration.' },
        ];
    return {
      criterion_id: rule.criterion_id || `criterion_${index + 1}`,
      title: criterionTitle,
      description: rule.description || 'Demonstrates analytical depth and evidence usage.',
      weight,
      levels: criterionLevels,
      self_review_prompt: rule.self_review_prompt || `How effectively does your draft address ${criterionTitle.toLowerCase()}?`,
      concept_id: rule.concept_id,
      concept_label: rule.concept_label,
      target_kc: rule.target_kc,
    };
  });
}

export function createContract(
  topic: string,
  prompt: string,
  activeModule: any,
  nextScaffold?: any
): { contract: AssignmentContract; evaluationPlan: EvaluationPlan } {
  const goals = (nextScaffold?.rubric_rules || []).map((r: any) => r.description).filter(Boolean).slice(0, 3);
  const contract: AssignmentContract = {
    title: topic.trim() || (activeModule ? `${activeModule.title}: Inquiry` : 'Historical Inquiry Task'),
    purpose: `Investigate the key tensions and institutional transformations of ${activeModule?.title || 'this module'} using grounded primary evidence.`,
    task: {
      prompt: nextScaffold?.clarified_prompt || prompt || 'Analyze the primary sources assigned in this unit to construct an evidence-grounded argument.',
      scope: activeModule ? `Chronological and institutional boundaries of Unit ${activeModule.position}: ${activeModule.title}` : 'The chronological scope defined in the prompt',
      deliverable: 'Source-grounded analytical essay (750–1000 words)',
      requirements: [
        'Directly address the inquiry question using explicit textual evidence.',
        'Interrogate assumptions and single-cause explanations using the primary sources.',
        'Review your completed draft against the published 3-level rubric before submitting.',
      ],
    },
    learning_goals: goals.length ? goals : [
      'Formulate a defensible thesis supported by authentic primary source citations.',
      'Distinguish between stated institutional claims and underlying material realities.',
    ],
    source_pack: sourceCards(nextScaffold?.grounding_sources || []),
    public_rubric: publicRubric(nextScaffold?.rubric_rules || [
      { label: 'Primary Source Evidence', description: 'Integrates authentic excerpts and avoids claims without source backing.', weight: 40 },
      { label: 'Causal Reasoning & Complexity', description: 'Explains multiple interacting causes rather than simplistic narratives.', weight: 35 },
      { label: 'Argumentative Clarity', description: 'Presents a coherent, structured, and logically sequenced thesis.', weight: 25 },
    ]),
    start_options: [
      'Read the inquiry prompt and identify the key historical entities and mechanisms in question.',
      'Explore the assigned primary sources and highlight two contrasting perspectives.',
      'Draft an initial thesis outline before writing full analytical paragraphs.',
    ],
    support_menu: [
      { action_id: 'understand_task', title: 'Task Clarification', description: 'Clarify deliverables, scope boundaries, or vocabulary without receiving answers.' },
      { action_id: 'use_materials', title: 'Source Exploration', description: 'Locate relevant passages in the assigned documents for your working claims.' },
      { action_id: 'plan_or_revise', title: 'Socratic Review', description: 'Test argument counter-claims and logic gaps before final submission.' },
    ],
    completion_checklist: [
      'I cited at least two assigned primary documents directly.',
      'I explained the historical mechanisms connecting cause to consequence.',
      'I conducted a self-review against the three rubric criteria.',
    ],
    integrity_notice: 'Your educator evaluates the final submission. AI assistance acts solely as a Socratic interlocutor to test reasoning.',
    version_note: null,
  };

  const evaluationPlan: EvaluationPlan = {
    public_rubric_map: (contract.public_rubric || []).map((rule, index) => ({
      public_criterion_id: rule.criterion_id || `criterion_${index + 1}`,
      concept_ids: rule.concept_id ? [rule.concept_id] : (rule.target_kc ? [rule.target_kc] : (nextScaffold?.target_kcs || []).slice(0, 1)),
      source_chunk_ids: (nextScaffold?.grounding_sources || []).map((s: any) => s.chunk_id),
      evidence_expectation: rule.description || 'Collect citations relevant to this public standard.',
    })),
    completion_states: ['task understood', 'sources explored', 'response drafted', 'ready for educator review'],
    support_policy: [
      'Provide Socratic questioning, reading guidance, and structural critique on demand.',
      'Never write text for the student or assign automated grades.',
    ],
    evidence_capture_notice: 'Educator reviews student writing, cited evidence, and interactive reasoning steps.',
    review_policy: 'Prepare criterion-organized evidence for educator evaluation; never compute autonomous grades.',
  };

  return { contract, evaluationPlan };
}
