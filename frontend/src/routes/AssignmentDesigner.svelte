<script>
  import { onMount } from 'svelte';
  import { responseError, routeParams } from '../lib/session.js';

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
  let isLoading = $state(true);
  let isAnalyzing = $state(false);
  let isGenerating = $state(false);
  let isProposing = $state(false);
  let isSaving = $state(false);
  let agentProposal = $state(null);
  let assistantInstruction = $state('');
  let notice = $state('');
  let error = $state('');

  let publishBlocked = $derived(
    Boolean(moduleId) && scaffold?.grounding_mode !== 'course_grounded'
  );

  function initializeAnswers(questions) {
    const next = {};
    for (const question of questions) next[question.question_id] = question.default_recommendation || question.options?.[0] || '';
    answers = next;
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
    isAnalyzing = true;
    error = '';
    notice = '';
    scaffold = null;
    draft = null;
    try {
      const response = await fetch('/assignments/analyze-scope', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_prompt: prompt.trim(),
          domain,
          course_id: courseId || null,
          module_id: moduleId || null,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Scope analysis failed.'));
      diagnosis = await response.json();
      initializeAnswers(diagnosis.interview_questions || []);
      if (!diagnosis.is_ambiguous) {
        answers = {
          Q1_TEMPORAL: `The historical setting and chronology stated in this task: ${prompt.trim()}`,
          Q2_MISCONCEPTIONS: 'A single-cause explanation that ignores structural fiscal pressures, institutional constraints, or evidence.',
          Q3_EVIDENCE: 'The course sources named in the task and relevant assigned primary-source evidence.',
        };
      }
    } catch (err) {
      error = err.message || 'Scope analysis could not be completed.';
    } finally {
      isAnalyzing = false;
    }
  }

  async function proposeAssignment(direction = assistantInstruction) {
    if (!courseId || !moduleId) {
      error = 'Select a course and module before asking the AI to prepare an assignment proposal.';
      return;
    }
    isProposing = true;
    error = '';
    notice = '';
    try {
      const module = course?.modules?.find((item) => item.module_id === moduleId);
      const response = await fetch('/authoring/assignments/propose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_topic: direction?.trim() || `Source-grounded inquiry for ${module?.title || 'this module'}`,
          course_id: courseId,
          module_id: moduleId,
          domain: course?.domain || domain,
          pedagogical_focus: direction?.trim() || 'Develop a contestable, evidence-grounded claim and probe likely misconceptions.',
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The AI assignment proposal could not be prepared.'));
      agentProposal = await response.json();
      topic = agentProposal.draft.title;
      prompt = agentProposal.scaffold.clarified_prompt;
      scaffold = agentProposal.scaffold;
      diagnosis = null;
      draft = null;
      notice = 'The AI prepared a complete assignment package with an editable student task, course-grounded sources, support ladder, and review criteria. Review it, then save or publish through this same designer.';
    } catch (err) {
      error = err.message || 'The AI assignment proposal could not be prepared.';
    } finally {
      isProposing = false;
    }
  }

  async function generateScaffold() {
    if (!prompt.trim()) return;
    isGenerating = true;
    error = '';
    notice = '';
    try {
      const response = await fetch('/assignments/clarify-and-scaffold', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_prompt: prompt.trim(),
          domain,
          answers,
          course_id: courseId || null,
          module_id: moduleId || null,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Scaffold generation failed.'));
      scaffold = await response.json();
      draft = null;
      notice = 'Scaffold prepared. Review the bounded hint ladder and rubric, then save a draft or publish it.';
    } catch (err) {
      error = err.message || 'Scaffold generation could not be completed.';
    } finally {
      isGenerating = false;
    }
  }

  async function saveDraft(publish = false) {
    if (!scaffold) return;
    isSaving = true;
    error = '';
    notice = '';
    try {
      let activeDraft = draft;
      if (!activeDraft) {
        const response = await fetch('/assignments/draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: topic.trim() || 'Untitled reasoning assignment',
            domain,
            course_id: courseId || null,
            module_id: moduleId || null,
            created_by: 'educator_workspace',
            clarified_prompt: scaffold.clarified_prompt,
            target_kcs: scaffold.target_kcs,
            hint_ladder: scaffold.hint_ladder,
            rubric_rules: scaffold.rubric_rules,
            grounding_mode: scaffold.grounding_mode,
            grounding_sources: scaffold.grounding_sources,
            generation_metadata: scaffold.generation_metadata,
            canvas_sections: scaffold.canvas_sections,
          }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The draft could not be saved.'));
        activeDraft = await response.json();
        draft = activeDraft;
      }
      if (publish) {
        const response = await fetch(`/assignments/${activeDraft.assignment_id}/publish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ module_id: moduleId || null }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The assignment could not be published.'));
        draft = { ...activeDraft, status: 'published' };
        notice = 'Assignment published. Students can now start answer-isolated reasoning sessions.';
      } else {
        notice = 'Draft saved. Its reference solution is locked in the educator-only Answer Vault.';
      }
    } catch (err) {
      error = err.message || 'The assignment could not be saved.';
    } finally {
      isSaving = false;
    }
  }

  onMount(async () => {
    try {
      await loadContext();
      const params = routeParams();
      if (params.get('assistant') === 'draft') {
        assistantInstruction = params.get('assistant_instruction') || '';
        await proposeAssignment(assistantInstruction);
      }
    } catch (err) {
      error = err.message || 'Course context could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

<main class="designer-main">
  <header class="page-header">
    <div>
      <div class="eyebrow">Educator studio</div>
      <h1>Assignment Scaffold Designer</h1>
      <p>Translate a teaching intention into a bounded Socratic learning task. Reference solutions are never exposed to the student workflow.</p>
    </div>
    {#if course}<div class="course-chip">{course.title}</div>{/if}
  </header>

  {#if isLoading}
    <div class="loading-card"><div class="spinner"></div><span>Loading curriculum context…</span></div>
  {:else}
    <div class="designer-grid">
      <section class="form-card">
        <div class="card-title">1. Define the learning task</div>
        <label for="topic">Assignment title</label>
        <input id="topic" bind:value={topic} placeholder="e.g. Structural causes of the French fiscal crisis" />
        <label for="module">Curriculum module</label>
        <select id="module" bind:value={moduleId}>
          <option value="">Unbound draft</option>
          {#each course?.modules || [] as module}
            <option value={module.module_id}>{module.position}. {module.title}</option>
          {/each}
        </select>
        <section class="agent-draft-card">
          <div><span>Proactive AI draft</span><strong>Turn this module into an evidence-grounded Socratic assignment</strong><p>The assistant uses the selected course and module scope to propose a task, source boundaries, hint ladder, cognitive traps, and rubric criteria. You remain in control of scope analysis, saving, and publication.</p></div>
          <button type="button" class="btn btn-primary" disabled={!moduleId || isProposing} onclick={() => proposeAssignment()}>{isProposing ? 'Drafting with AI…' : '✦ Draft assignment for this module'}</button>
          {#if agentProposal}<div class="agent-proposal-summary"><strong>{agentProposal.draft.title}</strong><span>{agentProposal.draft.learning_objectives?.length || 0} objectives · {agentProposal.scaffold.grounding_sources?.length || 0} grounded sources · {agentProposal.draft.cognitive_traps?.length || 0} misconception checks</span></div>{/if}
        </section>
        <label for="prompt">Prompt</label>
        <textarea id="prompt" rows="9" bind:value={prompt} placeholder="Write the inquiry students should investigate. Include a context, a claim or question, and the evidence expectations."></textarea>
        <button class="btn btn-secondary" onclick={analyzeScope} disabled={!prompt.trim() || isAnalyzing}>
          {isAnalyzing ? 'Analyzing scope…' : 'Analyze scope'}
        </button>

        {#if diagnosis}
          <section class="diagnosis" class:clear={!diagnosis.is_ambiguous}>
            <div class="diagnosis-header">
              <strong>{diagnosis.is_ambiguous ? 'Clarification needed' : 'Scope is sufficiently specific'}</strong>
              <span>{Math.round(diagnosis.ambiguity_index * 100)}% ambiguity</span>
            </div>
            {#if diagnosis.is_ambiguous}
              <p>Answer the alignment prompts below before generating the scaffold.</p>
              {#each diagnosis.interview_questions as question}
                <label for={question.question_id}>{question.dimension.replaceAll('_', ' ')}</label>
                <textarea id={question.question_id} rows="3" bind:value={answers[question.question_id]}></textarea>
              {/each}
            {:else}
              <p>The supplied prompt has enough temporal, causal, and evidence boundaries to generate a scaffold.</p>
            {/if}
            <button class="btn btn-primary" onclick={generateScaffold} disabled={isGenerating}>
              {isGenerating ? 'Generating scaffold…' : 'Generate AutoSCORE scaffold'}
            </button>
          </section>
        {:else}
          <p class="helper-text">Analyze the prompt first. Fiosra will flag missing temporal boundaries, misconception targets, and evidence anchors.</p>
        {/if}
      </section>

      <aside class="preview-card">
        <div class="card-title">2. Review the protected learning design</div>
        {#if scaffold}
          <div class="status-line"><span class="status-dot"></span> Scaffold ready</div>
          {#if scaffold.generation_metadata}
            <p class="generation-line" class:live={scaffold.generation_metadata.used_live_provider}>
              {#if scaffold.generation_metadata.used_live_provider}
                Model-assisted wording · {scaffold.generation_metadata.provider} / {scaffold.generation_metadata.model}
              {:else}
                Deterministic wording {scaffold.generation_metadata.fallback_reason ? `· provider fallback: ${scaffold.generation_metadata.fallback_reason}` : ''}
              {/if}
            </p>
          {/if}
          <section>
            <h2>Clarified task</h2>
            <p>{scaffold.clarified_prompt}</p>
          </section>
          <section>
            <h2>Target knowledge components</h2>
            <div class="tag-list">{#each scaffold.target_kcs as kc}<code>{kc}</code>{/each}</div>
          </section>
          <section class:generic-grounding={scaffold.grounding_mode !== 'course_grounded'} class="grounding-section">
            <h2>Grounding check</h2>
            {#if scaffold.grounding_mode === 'course_grounded'}
              <p>This scaffold is constrained to the selected module’s course materials.</p>
              <div class="grounding-list">
                {#each scaffold.grounding_sources as source}
                  <article><strong>{source.title}</strong><span>{source.kc_id || 'KC mapping pending'}</span><p>{source.excerpt}</p></article>
                {/each}
              </div>
            {:else}
              <p>This is a generic scaffold. Attach and ground a module source before publishing a module-bound assignment.</p>
            {/if}
          </section>
          <section>
            <h2>Hint ladder</h2>
            <div class="ladder-list">
              {#each scaffold.hint_ladder as rung}
                <div class:locked={rung.is_locked} class="ladder-item"><span>Rung {rung.level}</span><div><strong>{rung.hint_type.replace('_', ' ')}</strong><p>{rung.content}</p></div></div>
              {/each}
            </div>
          </section>
          <section>
            <h2>Rubric criteria</h2>
            {#each scaffold.rubric_rules as rule}
              <div class="rule-item"><strong>{rule.label}</strong><p>{rule.description}</p><span>{Math.round(rule.nli_threshold * 100)}% threshold</span></div>
            {/each}
          </section>
          <section>
            <h2>Student reasoning canvas</h2>
            <p>The published task will open a student-owned, five-step evidence canvas. Support cards are optional and must be accepted or edited by the learner.</p>
            <div class="canvas-preview-list">
              {#each scaffold.canvas_sections || [] as section}
                <div><span>{section.position}</span><strong>{section.label}</strong><small>{section.completion_guidance}</small></div>
              {/each}
            </div>
          </section>
          <div class="actions">
            <button class="btn btn-secondary" onclick={() => saveDraft(false)} disabled={isSaving}>{draft ? 'Draft saved' : 'Save draft'}</button>
            <button class="btn btn-primary" onclick={() => saveDraft(true)} disabled={isSaving || draft?.status === 'published' || publishBlocked}>{draft?.status === 'published' ? 'Published' : 'Publish to students'}</button>
          </div>
          {#if publishBlocked}<p class="publish-warning">Publishing is blocked until this module has a grounded course source.</p>{/if}
          {#if draft?.status === 'published'}
            <a class="btn btn-success launch" href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(draft.assignment_id)}`}>Open student canvas →</a>
          {/if}
        {:else}
          <div class="empty-preview"><strong>Awaiting a scaffold</strong><p>Once the scope has been analyzed and clarified, this panel will show the student-safe prompt, bounded hints, and verifiable criteria.</p></div>
        {/if}
      </aside>
    </div>
  {/if}

  {#if notice}<div class="notice success">{notice}</div>{/if}
  {#if error}<div class="notice error">{error}</div>{/if}
</main>

<style>
  .designer-main{max-width:1280px;margin:0 auto;padding:36px 28px 80px;display:flex;flex-direction:column;gap:24px}
  .page-header{border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;gap:20px;padding-bottom:22px}
  .eyebrow,.card-title{color:var(--color-slate-muted);font-size:11px;font-weight:700;letter-spacing:.55px;text-transform:uppercase}
  .page-header h1{color:var(--color-heading);font-family:var(--font-brand);font-size:27px;margin:4px 0 7px}
  .page-header p{color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;max-width:700px}
  .course-chip{align-self:flex-end;background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.3);border-radius:99px;color:var(--color-horizon-bright);font-size:12px;font-weight:600;padding:6px 11px}
  .designer-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(350px,.9fr);gap:22px;align-items:start}
  .form-card,.preview-card{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);padding:24px;display:flex;flex-direction:column;gap:12px}
  .preview-card{position:sticky;top:76px}
  .form-card label,.diagnosis label{color:var(--color-slate-light);font-size:11px;font-weight:700;letter-spacing:.35px;text-transform:uppercase;margin-top:4px}
  .form-card input,.form-card select,.form-card textarea,.diagnosis textarea{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);box-sizing:border-box;color:var(--color-slate-bright);font:inherit;font-size:13px;padding:10px 12px;width:100%}
  .form-card input:focus,.form-card select:focus,.form-card textarea:focus,.diagnosis textarea:focus{border-color:var(--color-horizon-blue);outline:none}
  .helper-text{color:var(--color-slate-muted);font-size:12px;line-height:1.6;margin:0}
  .agent-draft-card{background:linear-gradient(135deg,rgba(59,130,246,.12),rgba(124,58,237,.08));border:1px solid rgba(96,165,250,.3);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:10px;padding:14px}.agent-draft-card>div:first-child>span{color:var(--color-horizon-bright);display:block;font-size:10px;font-weight:700;letter-spacing:.4px;text-transform:uppercase}.agent-draft-card>div:first-child>strong{color:var(--color-heading);display:block;font-size:13px;margin-top:4px}.agent-draft-card>div:first-child>p{color:var(--color-slate-light);font-size:11px;line-height:1.5;margin:5px 0 0}.agent-draft-card .btn{align-self:flex-start}.agent-proposal-summary{background:rgba(15,23,42,.6);border:1px solid rgba(148,163,184,.16);border-radius:var(--radius-sm);padding:9px}.agent-proposal-summary strong{color:var(--color-heading);display:block;font-size:11px}.agent-proposal-summary span{color:var(--color-slate-muted);font-size:10px}
  .diagnosis{background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:10px;padding:16px}
  .diagnosis.clear{background:rgba(16,185,129,.07);border-color:rgba(16,185,129,.25)}
  .diagnosis-header{display:flex;justify-content:space-between;gap:12px;color:#fde68a;font-size:13px}
  .clear .diagnosis-header{color:#6ee7b7}
  .diagnosis p{color:var(--color-slate-light);font-size:12px;line-height:1.5;margin:0}
  .status-line{color:#6ee7b7;font-size:12px;font-weight:600}
  .status-dot{background:var(--color-signal-green);border-radius:50%;box-shadow:0 0 7px var(--color-signal-green);display:inline-block;height:7px;margin-right:6px;width:7px}
  .generation-line{color:var(--color-slate-muted)!important;font-size:10.5px!important}
  .generation-line.live{color:#93c5fd!important}
  .preview-card section{border-top:1px solid var(--color-graphite-border);padding-top:14px}
  .preview-card h2{color:var(--color-heading);font-size:13px;margin:0 0 7px}
  .preview-card p{color:var(--color-slate-light);font-size:12px;line-height:1.55;margin:0}
  .tag-list{display:flex;flex-wrap:wrap;gap:6px}
  .tag-list code{background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.25);border-radius:4px;color:var(--color-aurora-bright);font-size:10px;padding:4px 6px}
  .grounding-section{background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.2);border-radius:var(--radius-sm);padding:12px}
  .grounding-section.generic-grounding{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.3)}
  .grounding-list{display:flex;flex-direction:column;gap:7px;margin-top:10px}
  .grounding-list article{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-xs);padding:8px}
  .grounding-list strong{color:var(--color-heading);display:block;font-size:11px}
  .grounding-list span{color:var(--color-horizon-bright);font-size:10px}
  .grounding-list p{font-size:10px;margin-top:4px}
  .ladder-list{display:flex;flex-direction:column;gap:8px}
  .ladder-item{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:grid;gap:10px;grid-template-columns:58px 1fr;padding:9px}
  .ladder-item>span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;text-transform:uppercase}
  .ladder-item strong{color:var(--color-heading);font-size:11px;text-transform:capitalize}
  .ladder-item p{font-size:11px;margin-top:3px}
  .ladder-item.locked{opacity:.6}
  .rule-item{border-top:1px solid rgba(255,255,255,.06);padding:9px 0}
  .rule-item:first-of-type{border-top:none;padding-top:0}
  .rule-item strong{color:var(--color-heading);font-size:12px}
  .rule-item span{color:var(--color-horizon-bright);font-size:10px;font-weight:700}
  .canvas-preview-list{display:flex;flex-direction:column;gap:6px;margin-top:10px}
  .canvas-preview-list div{align-items:flex-start;background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-xs);display:grid;gap:7px;grid-template-columns:20px 1fr;padding:8px}
  .canvas-preview-list span{align-items:center;background:rgba(139,92,246,.15);border-radius:50%;color:#c4b5fd;display:flex;font-size:9px;font-weight:700;height:18px;justify-content:center}
  .canvas-preview-list strong{color:var(--color-heading);font-size:11px}
  .canvas-preview-list small{color:var(--color-slate-muted);font-size:10px;grid-column:2;line-height:1.4}
  .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:4px}
  .publish-warning{color:#fde68a!important;font-size:11px!important}
  .launch{align-self:stretch}
  .empty-preview{border:1px dashed var(--color-graphite-border);border-radius:var(--radius-md);color:var(--color-slate-muted);padding:28px 20px;text-align:center}
  .empty-preview strong{color:var(--color-heading);font-size:13px}
  .empty-preview p{margin-top:7px}
  .notice{border-radius:var(--radius-sm);font-size:12px;padding:11px 14px}
  .notice.success{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);color:#86efac}
  .notice.error{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#fca5a5}
  .loading-card{align-items:center;background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);color:var(--color-slate-light);display:flex;gap:12px;justify-content:center;min-height:240px}
  .spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:25px;width:25px}
  @keyframes spin{to{transform:rotate(360deg)}}
  @media(max-width:900px){.designer-grid{grid-template-columns:1fr}.preview-card{position:static}.course-chip{align-self:flex-start}}
  @media(max-width:620px){.designer-main{padding:26px 16px}.page-header{flex-direction:column}.actions{flex-direction:column}.actions .btn{width:100%}}
</style>
