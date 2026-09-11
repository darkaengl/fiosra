<script>
  import { onMount } from 'svelte';
  import { responseError, routeParams } from '../lib/session.js';

  const STEPS = [
    { id: 'brief', label: 'Brief', hint: 'Purpose, task and goals' },
    { id: 'materials', label: 'Materials', hint: 'Student source pack' },
    { id: 'rubric', label: 'Public rubric', hint: 'Criteria students see' },
    { id: 'experience', label: 'Student experience', hint: 'Help and submission' },
    { id: 'autoscore', label: 'AutoSCORE plan', hint: 'Teacher-only alignment' },
    { id: 'review', label: 'Publish review', hint: 'Validate and publish' },
  ];

  let courseId = $state('');
  let moduleId = $state('');
  let course = $state(null);
  let topic = $state('');
  let prompt = $state('');
  let domain = $state('history');
  let diagnosis = $state(null);
  let answers = $state({});
  let scaffold = $state(null);
  let draft = $state(null);
  let contract = $state(null);
  let evaluationPlan = $state(null);
  let readiness = $state({ is_publishable: false, items: [] });
  let activeStep = $state('brief');
  let previewTab = $state('overview');
  let isLoading = $state(true);
  let isAnalyzing = $state(false);
  let isGenerating = $state(false);
  let isProposing = $state(false);
  let isSaving = $state(false);
  let assistantInstruction = $state('');
  let notice = $state('');
  let error = $state('');

  const activeModule = $derived(course?.modules?.find((module) => module.module_id === moduleId) || null);
  const currentStep = $derived(STEPS.find((step) => step.id === activeStep));
  const visibleContract = $derived(contract || draft?.published || null);

  function initializeAnswers(questions) {
    const next = {};
    for (const question of questions) next[question.question_id] = question.default_recommendation || question.options?.[0] || '';
    answers = next;
  }

  function sourceCards(sources = []) {
    return sources.map((source, index) => ({
      source_id: `source_${index + 1}`,
      title: source.title || 'Assigned course material',
      excerpt: source.excerpt || '',
      source_url: source.source_url || null,
      citation: source.title || 'Assigned course material',
      relevance_guidance: 'Use this assigned material to develop and support your response to the task.',
    }));
  }

  function publicRubric(rules = []) {
    const rawTotal = rules.reduce((total, rule) => total + Number(rule.weight || 0), 0);
    let allocated = 0;
    return rules.map((rule, index) => {
      let weight = rawTotal ? Math.round((Number(rule.weight || 0) / rawTotal) * 10000) / 100 : 0;
      // The last criterion absorbs the rounding remainder so weights always sum to exactly
      // 100 — matching the backend's _public_rubric normalization (see generator.py).
      if (rawTotal && index === rules.length - 1) {
        weight = Math.round((100 - allocated) * 100) / 100;
      }
      allocated += weight;
      return {
        criterion_id: rule.criterion_id || `criterion_${index + 1}`,
        title: rule.label || `Criterion ${index + 1}`,
        description: rule.description || 'Demonstrates the stated assignment requirement.',
        weight,
        levels: [
          { level_id: 'developing', label: 'Developing', description: 'Begins to address this criterion but needs a clearer, more complete response.' },
          { level_id: 'secure', label: 'Secure', description: 'Addresses this criterion clearly with relevant detail and explanation.' },
          { level_id: 'strong', label: 'Strong', description: 'Addresses this criterion precisely, using well-chosen material and a well-developed explanation.' },
        ],
        self_review_prompt: `Where does your completed work show ${(rule.label || 'this criterion').toLowerCase()}?`,
      };
    });
  }

  function materializeContract(nextScaffold) {
    const goals = (nextScaffold?.rubric_rules || []).map((rule) => rule.description).filter(Boolean).slice(0, 3);
    contract = {
      title: topic.trim() || activeModule?.title || 'Untitled assignment',
      purpose: `This assignment helps you practice the course learning goals for ${topic.trim() || activeModule?.title || 'this module'}.`,
      task: {
        prompt: nextScaffold?.clarified_prompt || prompt,
        scope: answers.Q1_TEMPORAL || 'the scope stated in the task',
        deliverable: 'A source-grounded written response',
        requirements: [
          'Respond directly to the task within the stated scope.',
          'Use the assigned materials to develop your explanation.',
          'Review your work against the published rubric before submitting.',
        ],
      },
      learning_goals: goals.length ? goals : ['Develop a clear, evidence-grounded response to the assignment task.'],
      source_pack: sourceCards(nextScaffold?.grounding_sources || []),
      public_rubric: publicRubric(nextScaffold?.rubric_rules || []),
      start_options: [
        'Read the task and underline the action words and boundaries.',
        'Explore an assigned source and note one detail relevant to the task.',
        'Sketch a short outline before drafting your response.',
      ],
      support_menu: [
        { action_id: 'understand_task', title: 'Understand the task', description: 'Clarify the task, deliverable, or scope without receiving an answer.' },
        { action_id: 'use_materials', title: 'Work with assigned materials', description: 'Find and use relevant details from the approved source pack.' },
        { action_id: 'plan_or_revise', title: 'Plan or revise your response', description: 'Choose a helpful next step for organizing or improving your own work.' },
      ],
      completion_checklist: [
        'I responded directly to the task and stayed within its scope.',
        'I used assigned material in my explanation.',
        'I checked my work against each rubric criterion.',
        'I acknowledged the sources I used.',
      ],
      integrity_notice: 'Your educator evaluates the final submission. Use course materials responsibly and acknowledge sources you use.',
      version_note: null,
    };
    evaluationPlan = {
      public_rubric_map: (nextScaffold?.rubric_rules || []).map((rule, index) => ({
        public_criterion_id: rule.criterion_id || `criterion_${index + 1}`,
        concept_ids: rule.target_kc ? [rule.target_kc] : (nextScaffold?.target_kcs || []).slice(0, 1),
        source_chunk_ids: (nextScaffold?.grounding_sources || []).map((source) => source.chunk_id),
        evidence_expectation: rule.description || 'Collect evidence relevant to this public criterion.',
      })),
      completion_states: ['task understood', 'materials explored', 'response developing', 'ready to review'],
      support_policy: [
        'Offer student-selected task, source, planning, and revision support.',
        'Never generate a final answer, overwrite student writing, or assign a final grade.',
      ],
      evidence_capture_notice: 'The educator may review final work, source use, revisions, and assistance the learner chooses to apply.',
      review_policy: 'Prepare criterion-organized evidence for educator review; never determine the final grade.',
    };
  }

  async function loadContext() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    moduleId = params.get('module_id') || '';
    if (!courseId) return;
    const response = await fetch(`/courses/${courseId}`);
    if (!response.ok) throw new Error(await responseError(response, 'Course context could not be loaded.'));
    course = await response.json();
    if (!moduleId && course.modules?.length) moduleId = course.modules[0].module_id;
    domain = course.domain?.toLowerCase() || 'history';
  }

  async function analyzeScope() {
    if (!prompt.trim()) return;
    isAnalyzing = true; error = ''; notice = '';
    try {
      const response = await fetch('/assignments/analyze-scope', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_prompt: prompt.trim(), domain, course_id: courseId || null, module_id: moduleId || null }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Scope analysis failed.'));
      diagnosis = await response.json();
      initializeAnswers(diagnosis.interview_questions || []);
      if (!diagnosis.is_ambiguous) {
        answers = {
          Q1_TEMPORAL: `The setting and boundaries stated in this task: ${prompt.trim()}`,
          Q2_MISCONCEPTIONS: 'A single-cause explanation that ignores relevant context, mechanisms, or evidence.',
          Q3_EVIDENCE: 'The assigned course materials selected for this module.',
        };
      }
    } catch (err) { error = err.message || 'Scope analysis could not be completed.'; }
    finally { isAnalyzing = false; }
  }

  async function proposeAssignment(direction = assistantInstruction) {
    if (!courseId || !moduleId) { error = 'Select a course and module before asking AI to prepare an assignment proposal.'; return; }
    isProposing = true; error = ''; notice = '';
    try {
      const response = await fetch('/authoring/assignments/propose', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_topic: direction?.trim() || `Source-grounded inquiry for ${activeModule?.title || 'this module'}`,
          course_id: courseId, module_id: moduleId, domain: course?.domain || domain,
          pedagogical_focus: direction?.trim() || 'Create a student-facing task and transparent public rubric grounded in this module.',
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The AI assignment proposal could not be prepared.'));
      const proposal = await response.json();
      topic = proposal.draft.title;
      prompt = proposal.scaffold.clarified_prompt;
      scaffold = proposal.scaffold;
      materializeContract(scaffold);
      diagnosis = null; draft = null; readiness = { is_publishable: false, items: [] };
      activeStep = 'brief';
      notice = 'AI prepared an editable student assignment contract. Review the brief, materials, public rubric, and student preview before saving.';
    } catch (err) { error = err.message || 'The AI assignment proposal could not be prepared.'; }
    finally { isProposing = false; }
  }

  async function generateScaffold() {
    if (!prompt.trim()) return;
    isGenerating = true; error = ''; notice = '';
    try {
      const response = await fetch('/assignments/clarify-and-scaffold', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_prompt: prompt.trim(), domain, answers, course_id: courseId || null, module_id: moduleId || null }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Assignment proposal generation failed.'));
      scaffold = await response.json();
      materializeContract(scaffold);
      draft = null; readiness = { is_publishable: false, items: [] };
      activeStep = 'materials';
      notice = 'The student contract is ready for review. Confirm the source pack and public rubric before saving.';
    } catch (err) { error = err.message || 'Assignment proposal generation could not be completed.'; }
    finally { isGenerating = false; }
  }

  async function refreshAuthoring(assignmentId) {
    const response = await fetch(`/assignments/${assignmentId}/authoring`);
    if (!response.ok) throw new Error(await responseError(response, 'The Assignment Studio could not restore this draft.'));
    const authoring = await response.json();
    contract = authoring.published;
    evaluationPlan = authoring.evaluation_plan;
    readiness = authoring.readiness;
    draft = { ...draft, assignment_id: authoring.assignment_id, question_id: authoring.question_id, status: authoring.status, published: authoring.published };
  }

  async function saveStudio() {
    if (!contract || !evaluationPlan) return;
    isSaving = true; error = ''; notice = '';
    try {
      if (!draft) {
        const response = await fetch('/assignments/draft', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: contract.title, domain, course_id: courseId || null, module_id: moduleId || null,
            created_by: 'educator_workspace', raw_prompt: prompt || contract.task.prompt,
            answers, clarified_prompt: contract.task.prompt,
            target_kcs: scaffold?.target_kcs || [], hint_ladder: scaffold?.hint_ladder || [],
            rubric_rules: scaffold?.rubric_rules || [], grounding_mode: scaffold?.grounding_mode || 'generic',
            grounding_sources: scaffold?.grounding_sources || [], generation_metadata: scaffold?.generation_metadata || null,
            canvas_sections: scaffold?.canvas_sections || [], published: contract, evaluation_plan: evaluationPlan,
          }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The assignment draft could not be saved.'));
        draft = await response.json();
      } else {
        const response = await fetch(`/assignments/${draft.assignment_id}/authoring`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ published: contract, evaluation_plan: evaluationPlan, canvas_sections: scaffold?.canvas_sections || [] }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The Assignment Studio changes could not be saved.'));
      }
      await refreshAuthoring(draft.assignment_id);
      notice = 'Draft saved. The student contract and private AutoSCORE plan are now versioned together.';
    } catch (err) { error = err.message || 'The assignment could not be saved.'; }
    finally { isSaving = false; }
  }

  async function publish() {
    await saveStudio();
    if (!draft?.assignment_id) return;
    if (!readiness.is_publishable) { activeStep = 'review'; error = 'Resolve the publication checks before publishing.'; return; }
    isSaving = true; error = ''; notice = '';
    try {
      const response = await fetch(`/assignments/${draft.assignment_id}/publish`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ module_id: moduleId || null }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The assignment could not be published.'));
      draft = { ...draft, status: 'published' };
      notice = 'Assignment published. Students now receive the approved public task, materials, rubric, and support menu.';
    } catch (err) { error = err.message || 'The assignment could not be published.'; }
    finally { isSaving = false; }
  }

  function addCriterion() {
    if (!contract) return;
    contract.public_rubric.push({
      criterion_id: `criterion_${contract.public_rubric.length + 1}`,
      title: 'New criterion', description: 'Describe what this criterion evaluates.', weight: 0,
      levels: [
        { level_id: 'developing', label: 'Developing', description: 'Beginning to demonstrate this criterion.' },
        { level_id: 'secure', label: 'Secure', description: 'Demonstrates this criterion clearly.' },
        { level_id: 'strong', label: 'Strong', description: 'Demonstrates this criterion precisely and persuasively.' },
      ], self_review_prompt: 'Where does your completed work demonstrate this criterion?',
    });
  }

  onMount(async () => {
    try {
      await loadContext();
      const params = routeParams();
      if (params.get('assistant') === 'draft') { assistantInstruction = params.get('assistant_instruction') || ''; await proposeAssignment(assistantInstruction); }
    } catch (err) { error = err.message || 'Course context could not be initialized.'; }
    finally { isLoading = false; }
  });
</script>

<main class="studio-main">
  <header class="studio-header">
    <div>
      <span class="eyebrow">Educator studio</span>
      <h1>Assignment Studio</h1>
      <p>Design the student contract first. AutoSCORE supports the approved rubric; it does not introduce hidden grading standards.</p>
    </div>
    <div class="header-actions">
      {#if course}<span class="course-chip">{course.title}{activeModule ? ` · ${activeModule.title}` : ''}</span>{/if}
      {#if contract}<button class="btn btn-secondary" onclick={() => previewTab = 'overview'}>Preview as student</button>{/if}
      <button class="btn btn-secondary" disabled={!contract || isSaving} onclick={saveStudio}>{isSaving ? 'Saving…' : draft ? 'Save changes' : 'Save draft'}</button>
    </div>
  </header>

  {#if isLoading}
    <div class="loading-card"><span class="spinner"></span> Loading curriculum context…</div>
  {:else}
    <div class="studio-layout">
      <nav class="workflow-rail" aria-label="Assignment Studio steps">
        <div class="rail-context">
          <label for="module">Curriculum module</label>
          <select id="module" bind:value={moduleId}>
            <option value="">Unbound draft</option>
            {#each course?.modules || [] as module}<option value={module.module_id}>{module.position}. {module.title}</option>{/each}
          </select>
        </div>
        {#each STEPS as step, index}
          <button class:active={activeStep === step.id} class="step-button" onclick={() => activeStep = step.id}>
            <span>{index + 1}</span><div><strong>{step.label}</strong><small>{step.hint}</small></div>
            {#if step.id === 'review' && readiness.items?.length}<i>{readiness.items.length}</i>{/if}
          </button>
        {/each}
        <div class="rail-footnote"><strong>Boundary</strong><p>Students see the public assignment contract. Concept mappings, evidence policy, and answer material remain teacher-only.</p></div>
      </nav>

      <section class="editor-canvas">
        <div class="canvas-heading"><div><span class="eyebrow">Step {STEPS.findIndex((step) => step.id === activeStep) + 1}</span><h2>{currentStep?.label}</h2></div>{#if contract}<span class="save-state">{draft ? 'Draft saved' : 'Unsaved proposal'}</span>{/if}</div>

        {#if activeStep === 'brief'}
          <section class="editor-section intro-card">
            <div><span class="eyebrow">AI starting point</span><h3>Start from this module</h3><p>Ask AI for an editable proposal, or write your teaching intention and refine it below.</p></div>
            <button class="btn btn-primary" disabled={!moduleId || isProposing} onclick={() => proposeAssignment()}>{isProposing ? 'Drafting with AI…' : '✦ Draft with AI'}</button>
          </section>
          <section class="editor-section">
            <label for="title">Assignment title</label><input id="title" bind:value={topic} placeholder="e.g. Tudor conquest and Stuart consolidation" />
            <label for="prompt">Teaching intention or task draft</label><textarea id="prompt" rows="8" bind:value={prompt} placeholder="State what students should investigate, make, or explain."></textarea>
            <div class="inline-actions"><button class="btn btn-secondary" disabled={!prompt.trim() || isAnalyzing} onclick={analyzeScope}>{isAnalyzing ? 'Analyzing…' : 'Analyze scope'}</button>{#if diagnosis}<span class:clear={!diagnosis.is_ambiguous} class="scope-status">{diagnosis.is_ambiguous ? 'Clarification needed' : 'Scope is ready to draft'}</span>{/if}</div>
          </section>
          {#if diagnosis?.is_ambiguous}<section class="editor-section"><h3>Clarify the task</h3>{#each diagnosis.interview_questions as question}<label for={question.question_id}>{question.dimension.replaceAll('_', ' ')}</label><textarea id={question.question_id} rows="3" bind:value={answers[question.question_id]}></textarea>{/each}<button class="btn btn-primary" disabled={isGenerating} onclick={generateScaffold}>{isGenerating ? 'Preparing contract…' : 'Create assignment contract'}</button></section>{:else if diagnosis}<section class="editor-section ready-card"><p>The scope has enough boundaries to build an assignment contract.</p><button class="btn btn-primary" disabled={isGenerating} onclick={generateScaffold}>{isGenerating ? 'Preparing contract…' : 'Create assignment contract'}</button></section>{/if}
          {#if contract}<section class="editor-section"><h3>Student-facing brief</h3><label for="contract-title">Title</label><input id="contract-title" bind:value={contract.title} /><label for="purpose">Why this matters</label><textarea id="purpose" rows="3" bind:value={contract.purpose}></textarea><label for="task">Your task</label><textarea id="task" rows="5" bind:value={contract.task.prompt}></textarea><div class="two-col"><div><label for="scope">Scope</label><textarea id="scope" rows="3" bind:value={contract.task.scope}></textarea></div><div><label for="deliverable">Deliverable</label><input id="deliverable" bind:value={contract.task.deliverable} /></div></div><label>Student learning goals</label><div class="string-list">{#each contract.learning_goals as goal, index}<input aria-label={`Learning goal ${index + 1}`} bind:value={contract.learning_goals[index]} />{/each}</div></section>{/if}

        {:else if activeStep === 'materials'}
          {#if contract}<section class="editor-section"><div class="section-title"><div><h3>Student source pack</h3><p>Students receive readable excerpts, relevance guidance, and source access—not chunk IDs or graph diagnostics.</p></div><span class="success-pill">{contract.source_pack.length} ready</span></div>{#each contract.source_pack as source, index}<article class="source-editor"><div class="source-number">{index + 1}</div><div><label>Display title</label><input bind:value={source.title} /><label>Why this is assigned</label><textarea rows="2" bind:value={source.relevance_guidance}></textarea><label>Student excerpt</label><textarea rows="5" bind:value={source.excerpt}></textarea><label>Original link (optional)</label><input bind:value={source.source_url} placeholder="https://…" /></div></article>{:else}<div class="empty-state"><strong>No substantive source is available yet.</strong><p>Attach or import a readable module resource before publishing.</p></div>{/each}</section>{:else}<div class="empty-state"><strong>Create a brief first.</strong><p>Source-pack editing becomes available after an assignment contract is generated.</p></div>{/if}

        {:else if activeStep === 'rubric'}
          {#if contract}<section class="editor-section"><div class="section-title"><div><h3>Public rubric</h3><p>These criteria are published to students and are the standards AutoSCORE must follow.</p></div><button class="btn btn-secondary" onclick={addCriterion}>+ Add criterion</button></div>{#each contract.public_rubric as criterion, index}<article class="criterion-editor"><div class="criterion-index">{index + 1}</div><div class="criterion-main"><div class="two-col"><div><label>Criterion name</label><input bind:value={criterion.title} /></div><div><label>Weight (%)</label><input type="number" min="0" max="100" bind:value={criterion.weight} /></div></div><label>What it evaluates</label><textarea rows="2" bind:value={criterion.description}></textarea><div class="level-grid">{#each criterion.levels as level}<div><label>{level.label}</label><textarea rows="3" bind:value={level.description}></textarea></div>{/each}</div><label>Student self-review prompt</label><input bind:value={criterion.self_review_prompt} /></div></article>{/each}</section>{:else}<div class="empty-state"><strong>Create a brief first.</strong></div>{/if}

        {:else if activeStep === 'experience'}
          {#if contract}<section class="editor-section"><h3>Student experience</h3><p class="section-copy">Support should help students complete the assignment. It should not require a separate claim-validation ritual.</p><label>Suggested ways to begin</label><div class="string-list">{#each contract.start_options as option, index}<input bind:value={contract.start_options[index]} />{/each}</div><label>Available help</label>{#each contract.support_menu as item}<article class="support-editor"><strong>{item.title}</strong><textarea rows="2" bind:value={item.description}></textarea></article>{/each}<label>Submission checklist</label><div class="string-list">{#each contract.completion_checklist as item, index}<input bind:value={contract.completion_checklist[index]} />{/each}</div><label>Integrity and evaluation statement</label><textarea rows="3" bind:value={contract.integrity_notice}></textarea></section>{:else}<div class="empty-state"><strong>Create a brief first.</strong></div>{/if}

        {:else if activeStep === 'autoscore'}
          {#if contract && evaluationPlan}<section class="editor-section private-plan"><div class="section-title"><div><span class="private-label">Teacher and agent only</span><h3>AutoSCORE evaluation plan</h3><p>Each internal mapping must serve a public rubric criterion. This plan produces educator-review evidence, never an autonomous grade.</p></div></div>{#each evaluationPlan.public_rubric_map as mapping, index}<article class="mapping-row"><strong>{contract.public_rubric.find((criterion) => criterion.criterion_id === mapping.public_criterion_id)?.title || mapping.public_criterion_id}</strong><span>Public criterion</span><p>{mapping.evidence_expectation}</p><small>{mapping.concept_ids.length} concept target(s) · {mapping.source_chunk_ids.length} source evidence item(s)</small></article>{/each}<div class="policy-list"><h4>Support boundary</h4>{#each evaluationPlan.support_policy as policy}<p>{policy}</p>{/each}<h4>Teacher review boundary</h4><p>{evaluationPlan.review_policy}</p></div></section>{:else}<div class="empty-state"><strong>Create a brief first.</strong></div>{/if}

        {:else if activeStep === 'review'}
          {#if contract}<section class="editor-section"><div class="section-title"><div><h3>Publication review</h3><p>Publication freezes the student contract and keeps the private evaluation plan teacher-only.</p></div><button class="btn btn-secondary" disabled={!draft || isSaving} onclick={saveStudio}>Refresh checks</button></div><div class:ready={draft && readiness.is_publishable} class="readiness-banner"><strong>{!draft ? 'Not yet checked' : readiness.is_publishable ? 'Ready to publish' : 'Action needed before publishing'}</strong><p>{!draft ? 'Checks run automatically when you publish.' : readiness.is_publishable ? 'The public contract and private plan are aligned.' : `${readiness.items.length} required check${readiness.items.length === 1 ? '' : 's'} remain.`}</p></div>{#each readiness.items || [] as item}<div class="readiness-item"><span>!</span><p>{item.message}</p></div>{/each}<div class="review-actions"><button class="btn btn-secondary" onclick={() => previewTab = 'rubric'}>Review public rubric</button><button class="btn btn-primary" disabled={!contract || isSaving || draft?.status === 'published'} onclick={publish}>{draft?.status === 'published' ? 'Published' : 'Publish'}</button></div></section>{:else}<div class="empty-state"><strong>Save a draft to validate it.</strong></div>{/if}
        {/if}
      </section>

      <aside class="student-preview" aria-label="Live student preview">
        <div class="preview-heading"><div><span class="eyebrow">Live student preview</span><h2>{visibleContract?.title || 'Assignment preview'}</h2></div><span class="student-pill">Student-facing</span></div>
        <div class="preview-tabs"><button class:active={previewTab === 'overview'} onclick={() => previewTab = 'overview'}>Overview</button><button class:active={previewTab === 'sources'} onclick={() => previewTab = 'sources'}>Sources</button><button class:active={previewTab === 'rubric'} onclick={() => previewTab = 'rubric'}>Rubric</button><button class:active={previewTab === 'submit'} onclick={() => previewTab = 'submit'}>Submit</button></div>
        {#if visibleContract}
          <div class="preview-body">
            {#if previewTab === 'overview'}<span class="preview-label">Why this matters</span><p>{visibleContract.purpose}</p><span class="preview-label">Your task</span><p class="preview-task">{visibleContract.task.prompt}</p><dl><div><dt>Scope</dt><dd>{visibleContract.task.scope}</dd></div><div><dt>Deliverable</dt><dd>{visibleContract.task.deliverable}</dd></div></dl><span class="preview-label">What you will practice</span><ul>{#each visibleContract.learning_goals as goal}<li>{goal}</li>{/each}</ul><span class="preview-label">A useful way to begin</span><ol>{#each visibleContract.start_options as option}<li>{option}</li>{/each}</ol>
            {:else if previewTab === 'sources'}{#each visibleContract.source_pack as source}<article class="preview-source"><strong>{source.title}</strong><p>{source.relevance_guidance}</p><blockquote>{source.excerpt}</blockquote></article>{:else}<p>No assigned materials are ready yet.</p>{/each}
            {:else if previewTab === 'rubric'}{#each visibleContract.public_rubric as criterion}<article class="preview-rubric"><div><strong>{criterion.title}</strong>{#if criterion.weight}<span>{criterion.weight}%</span>{/if}</div><p>{criterion.description}</p>{#each criterion.levels as level}<small><b>{level.label}:</b> {level.description}</small>{/each}</article>{/each}
            {:else}<span class="preview-label">Before you submit</span><ul>{#each visibleContract.completion_checklist as item}<li>{item}</li>{/each}</ul><div class="integrity-note">{visibleContract.integrity_notice}</div>{/if}
          </div>
        {:else}<div class="preview-empty"><strong>Your student preview will appear here.</strong><p>Generate an assignment contract to review the task, materials, rubric, and submission information as students will see them.</p></div>{/if}
      </aside>
    </div>
  {/if}
  {#if notice}<div class="notice success">{notice}</div>{/if}
  {#if error}<div class="notice error">{error}</div>{/if}
</main>

<style>
  .studio-main{max-width:1540px;margin:0 auto;padding:30px 28px 70px}.studio-header{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;gap:24px;justify-content:space-between;padding-bottom:20px}.eyebrow{color:var(--color-slate-muted);font-size:10px;font-weight:800;letter-spacing:.6px;text-transform:uppercase}.studio-header h1{color:var(--color-heading);font-family:var(--font-brand);font-size:30px;margin:5px 0 7px}.studio-header p{color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;max-width:760px}.header-actions{align-items:center;display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end}.course-chip,.student-pill,.success-pill,.save-state{border-radius:999px;font-size:10px;font-weight:700;padding:5px 9px}.course-chip{background:rgba(59,130,246,.12);border:1px solid rgba(96,165,250,.3);color:#93c5fd}.student-pill{background:rgba(16,185,129,.12);color:#6ee7b7}.success-pill,.save-state{background:rgba(148,163,184,.12);color:var(--color-slate-light)}.studio-layout{display:grid;gap:18px;grid-template-columns:235px minmax(460px,1fr) minmax(310px,.65fr);margin-top:24px}.workflow-rail,.editor-canvas,.student-preview{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg)}.workflow-rail{align-self:start;display:flex;flex-direction:column;overflow:hidden;position:sticky;top:74px}.rail-context{background:rgba(15,23,42,.48);border-bottom:1px solid var(--color-graphite-border);display:flex;flex-direction:column;gap:6px;padding:14px}.rail-context label,.editor-section label{color:var(--color-slate-muted);font-size:10px;font-weight:800;letter-spacing:.4px;text-transform:uppercase}.rail-context select,.editor-section input,.editor-section textarea{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);box-sizing:border-box;color:var(--color-slate-bright);font:inherit;font-size:12px;padding:9px 10px;width:100%}.rail-context select:focus,.editor-section input:focus,.editor-section textarea:focus{border-color:var(--color-horizon-blue);outline:none}.step-button{align-items:center;background:transparent;border:0;border-bottom:1px solid rgba(148,163,184,.09);color:var(--color-slate-light);cursor:pointer;display:flex;gap:10px;padding:12px;text-align:left}.step-button:hover,.step-button.active{background:rgba(59,130,246,.11);color:var(--color-heading)}.step-button>span,.criterion-index,.source-number{align-items:center;background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:50%;color:var(--color-horizon-bright);display:flex;font-size:10px;font-weight:800;height:22px;justify-content:center;width:22px}.step-button.active>span{background:var(--color-horizon-blue);color:white}.step-button div{display:flex;flex:1;flex-direction:column;gap:2px}.step-button strong{font-size:12px}.step-button small{color:var(--color-slate-muted);font-size:10px}.step-button i{align-items:center;background:#f59e0b;border-radius:50%;color:#111827;display:flex;font-size:9px;font-style:normal;font-weight:800;height:17px;justify-content:center;width:17px}.rail-footnote{background:rgba(139,92,246,.08);margin-top:12px;padding:13px}.rail-footnote strong{color:#c4b5fd;font-size:10px;text-transform:uppercase}.rail-footnote p{color:var(--color-slate-light);font-size:10.5px;line-height:1.5;margin:5px 0 0}.editor-canvas{min-height:720px;padding:24px}.canvas-heading{align-items:center;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;margin-bottom:20px;padding-bottom:15px}.canvas-heading h2{color:var(--color-heading);font-size:21px;margin:4px 0 0}.editor-section{display:flex;flex-direction:column;gap:9px;margin-bottom:18px}.editor-section h3{color:var(--color-heading);font-size:15px;margin:0}.editor-section p,.section-copy{color:var(--color-slate-light);font-size:12px;line-height:1.55;margin:0}.intro-card{align-items:center;background:linear-gradient(135deg,rgba(59,130,246,.12),rgba(124,58,237,.09));border:1px solid rgba(96,165,250,.28);border-radius:var(--radius-md);display:flex;flex-direction:row;justify-content:space-between;padding:16px}.intro-card p{max-width:520px}.inline-actions{align-items:center;display:flex;gap:10px}.scope-status{border-radius:999px;font-size:11px;font-weight:700;padding:5px 9px;background:rgba(245,158,11,.13);color:#fde68a}.scope-status.clear{background:rgba(16,185,129,.13);color:#6ee7b7}.ready-card{background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.25);border-radius:var(--radius-md);padding:15px}.two-col{display:grid;gap:12px;grid-template-columns:1fr 1fr}.two-col>div{display:flex;flex-direction:column;gap:6px}.string-list{display:flex;flex-direction:column;gap:7px}.section-title{align-items:flex-start;display:flex;gap:12px;justify-content:space-between}.section-title p{margin-top:4px}.source-editor,.criterion-editor,.support-editor,.mapping-row{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-md);display:grid;gap:12px;grid-template-columns:26px 1fr;padding:14px}.source-editor>div:nth-child(2),.criterion-main{display:flex;flex-direction:column;gap:7px}.criterion-editor{margin-top:10px}.level-grid{display:grid;gap:8px;grid-template-columns:repeat(3,1fr)}.level-grid>div{display:flex;flex-direction:column;gap:5px}.support-editor{display:flex;flex-direction:column;gap:6px;margin-bottom:8px}.support-editor strong{color:var(--color-heading);font-size:12px}.private-plan{background:rgba(139,92,246,.05);border:1px solid rgba(139,92,246,.24);border-radius:var(--radius-md);padding:17px}.private-label{color:#c4b5fd;font-size:10px;font-weight:800;letter-spacing:.5px;text-transform:uppercase}.mapping-row{display:flex;flex-direction:column;gap:4px;margin-top:10px}.mapping-row strong{color:var(--color-heading);font-size:12px}.mapping-row span,.mapping-row small{color:#c4b5fd;font-size:10px}.mapping-row p{font-size:11px}.policy-list{border-top:1px solid rgba(139,92,246,.25);margin-top:12px;padding-top:10px}.policy-list h4{color:var(--color-heading);font-size:11px;margin:10px 0 5px}.policy-list p{color:var(--color-slate-light);font-size:11px;line-height:1.5;margin:5px 0}.readiness-banner{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.28);border-radius:var(--radius-md);padding:13px}.readiness-banner.ready{background:rgba(16,185,129,.1);border-color:rgba(16,185,129,.28)}.readiness-banner strong{color:#fde68a;font-size:13px}.readiness-banner.ready strong{color:#6ee7b7}.readiness-banner p{font-size:11px;margin-top:4px}.readiness-item{align-items:center;background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.22);border-radius:var(--radius-sm);display:flex;gap:9px;padding:9px}.readiness-item span{align-items:center;background:#ef4444;border-radius:50%;color:white;display:flex;font-size:10px;font-weight:800;height:17px;justify-content:center;width:17px}.readiness-item p{font-size:11px}.review-actions{display:flex;gap:8px;justify-content:flex-end}.student-preview{align-self:start;overflow:hidden;position:sticky;top:74px}.preview-heading{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;padding:17px}.preview-heading h2{color:var(--color-heading);font-size:15px;line-height:1.35;margin:4px 0 0;max-width:240px}.preview-tabs{background:rgba(15,23,42,.42);display:flex;overflow:auto;padding:7px}.preview-tabs button{background:transparent;border:0;border-radius:var(--radius-xs);color:var(--color-slate-muted);cursor:pointer;font-size:10px;font-weight:700;padding:7px}.preview-tabs button.active{background:var(--color-graphite);color:var(--color-heading)}.preview-body{display:flex;flex-direction:column;gap:11px;max-height:650px;overflow-y:auto;padding:17px}.preview-body p,.preview-body li,.preview-body dd{color:var(--color-slate-light);font-size:11.5px;line-height:1.55}.preview-label{color:var(--color-slate-muted);font-size:9px;font-weight:800;letter-spacing:.4px;text-transform:uppercase}.preview-task{color:var(--color-heading)!important;font-size:12px!important}.preview-body dl{display:grid;gap:7px;margin:0}.preview-body dl div{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-xs);padding:8px}.preview-body dt{color:var(--color-slate-muted);font-size:9px;font-weight:800;text-transform:uppercase}.preview-body dd{margin:3px 0 0}.preview-body ul,.preview-body ol{margin:0;padding-left:18px}.preview-source,.preview-rubric{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);padding:10px}.preview-source strong,.preview-rubric strong{color:var(--color-heading);font-size:11.5px}.preview-source p,.preview-rubric p{margin:5px 0}.preview-source blockquote{border-left:2px solid var(--color-horizon-blue);color:var(--color-slate-light);font-size:11px;line-height:1.5;margin:8px 0 0;padding-left:8px}.preview-rubric>div{display:flex;justify-content:space-between}.preview-rubric span{color:var(--color-horizon-bright);font-size:10px;font-weight:700}.preview-rubric small{color:var(--color-slate-light);display:block;font-size:10px;line-height:1.45;margin-top:5px}.integrity-note{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);border-radius:var(--radius-sm);color:var(--color-slate-light);font-size:11px;line-height:1.5;padding:10px}.preview-empty,.empty-state{border:1px dashed var(--color-graphite-border);border-radius:var(--radius-md);color:var(--color-slate-muted);padding:26px 16px;text-align:center}.preview-empty strong,.empty-state strong{color:var(--color-heading);font-size:12px}.preview-empty p,.empty-state p{font-size:11px;line-height:1.5;margin:7px 0 0}.notice{border-radius:var(--radius-sm);font-size:12px;margin-top:16px;padding:11px 14px}.notice.success{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);color:#86efac}.notice.error{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#fca5a5}.loading-card{align-items:center;color:var(--color-slate-light);display:flex;gap:10px;justify-content:center;min-height:340px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:24px;width:24px}@keyframes spin{to{transform:rotate(360deg)}}
  @media(max-width:1180px){.studio-layout{grid-template-columns:210px minmax(0,1fr)}.student-preview{grid-column:2;position:static}.workflow-rail{grid-row:span 2}.preview-body{max-height:none}}@media(max-width:780px){.studio-main{padding:22px 15px}.studio-header{flex-direction:column}.header-actions{justify-content:flex-start}.studio-layout{grid-template-columns:1fr}.workflow-rail{position:static}.step-button{display:none}.workflow-rail{display:flex;flex-direction:row;overflow:auto}.rail-context,.rail-footnote{display:none}.editor-canvas{min-height:0;padding:17px}.student-preview{grid-column:auto}.intro-card{align-items:flex-start;flex-direction:column}.two-col,.level-grid{grid-template-columns:1fr}}
</style>
