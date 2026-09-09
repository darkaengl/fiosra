<script>
  import { onMount } from 'svelte';

  let courseId = $state('');
  let selectedKC = $state('KC_HIST_POPULAR_SOV');
  let prompt = $state('');
  let isGenerating = $state(false);
  let generatedScaffold = $state(null);

  const prereqs = [
    { code: 'KC_HIST_FISCAL_CRISIS_1786', title: 'Royal Fiscal Crisis of 1786 — Necker Reforms', coverage: 72 },
    { code: 'KC_HIST_ESTATE_SYSTEM', title: 'Three Estates Social Structure & Representation Gap', coverage: 68 },
    { code: 'KC_HIST_SOCIAL_CONTRACT', title: 'Enlightenment Social Contract Theory (Rousseau/Locke)', coverage: 81 },
  ];

  const traps = [
    { code: 'MISC_HIST_REV_CAUSE', desc: 'Confusing the fiscal crisis with the sole cause of the Revolution, ignoring social and political factors.', trigger: 'Detected in 42% of submissions' },
    { code: 'MISC_HIST_POPULAR_SOV', desc: 'Conflating popular sovereignty with democracy; Rousseau\'s General Will differs from majority rule.', trigger: 'Detected in 38% of submissions' },
    { code: 'MISC_HIST_DEBT_CAUSE', desc: 'Misattributing American war debt as primary driver vs. structural Ancien Régime fiscal architecture.', trigger: 'Detected in 29% of submissions' },
  ];

  async function generateScaffold() {
    if (!prompt.trim()) return;
    isGenerating = true;
    generatedScaffold = null;
    try {
      // Simulate AI generation
      await new Promise(r => setTimeout(r, 1500));
      generatedScaffold = {
        stem: prompt,
        scaffoldTier: 'Tier 2 — Structural Scaffolding',
        verbalAnchors: ['fiscal bankruptcy', 'Estates General', 'popular sovereignty'],
        misconceptionTrap: 'MISC_HIST_REV_CAUSE',
        rubricCriteria: [
          { label: 'Causal Chain Identification', points: 25, desc: 'Identifies at least 3 causal factors linking fiscal crisis to constitutional crisis.' },
          { label: 'KC Citation Precision', points: 35, desc: 'Grounds argument in verified syllabus readings (pgvector similarity ≥ 0.82).' },
          { label: 'Misconception Avoidance', points: 20, desc: 'Avoids conflating single-cause explanations for complex revolutionary dynamics.' },
          { label: 'Epistemic Clarity', points: 20, desc: 'Distinguishes between primary source evidence and interpretive claims.' },
        ]
      };
    } finally {
      isGenerating = false;
    }
  }

  onMount(() => {
    const hash = window.location.hash;
    const q = hash.indexOf('?');
    if (q >= 0) {
      const params = new URLSearchParams(hash.slice(q + 1));
      courseId = params.get('course_id') || '';
    }
  });
</script>

<div class="designer-layout">
  <!-- Left: Knowledge Graph Panel -->
  <aside class="knowledge-col">
    <div class="col-header">
      <div class="col-title">Curriculum Knowledge Graph</div>
      <div class="col-sub">KC: The French Revolution & Modern Statehood</div>
    </div>

    <div>
      <div class="panel-label">Target Knowledge Component</div>
      <div class="target-node-card">
        <span class="kc-code">{selectedKC}</span>
        <span class="kc-name">Transition to Popular Sovereignty (1789–1791)</span>
        <span class="kc-status">14 Misconception Traps Registered • pgvector Grounded</span>
      </div>
    </div>

    <div>
      <div class="panel-label">Prerequisite DAG</div>
      <div class="prereq-stack">
        {#each prereqs as p}
          <div class="prereq-card">
            <span class="prereq-code">{p.code}</span>
            <span class="prereq-title">{p.title}</span>
            <div class="progress-track"><div class="progress-fill" style="width: {p.coverage}%"></div></div>
            <span class="prereq-meta">Cohort Coverage: {p.coverage}%</span>
          </div>
        {/each}
      </div>
    </div>

    <div>
      <div class="panel-label">Autonomy Score — Cohort Average</div>
      <div class="autonomy-card">
        <div style="display: flex; justify-content: space-between;">
          <span style="font-size: 13px; color: #e2e8f0; font-weight: 600;">Epistemic Autonomy Index</span>
          <span style="font-size: 22px; font-weight: 700; color: var(--color-horizon-bright);">62%</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width: 62%; background: var(--color-horizon-blue);"></div></div>
        <span style="font-size: 11px; color: var(--color-slate-muted);">Target: 80% by Week 6</span>
      </div>
    </div>

    <div>
      <div class="panel-label">Misconception Trap Library</div>
      <div class="traps-stack">
        {#each traps as t}
          <div class="trap-card">
            <span class="trap-code">{t.code}</span>
            <span class="trap-desc">{t.desc}</span>
            <span class="trap-trigger">⚠ {t.trigger}</span>
          </div>
        {/each}
      </div>
    </div>
  </aside>

  <!-- Center: Assignment Editor -->
  <main class="editor-col">
    <div class="editor-header">
      <div class="editor-title">Assignment Scaffold Designer</div>
      <div class="editor-subtitle">Grounded in pgvector syllabus • DeBERTa NLI verified rubric criteria</div>
    </div>

    <div class="form-group">
      <label class="field-label">Assignment Stem / Prompt</label>
      <textarea
        class="field-textarea"
        rows="6"
        placeholder="Analyze the relationship between the Ancien Régime fiscal crisis and the conceptual emergence of popular sovereignty. Drawing on the primary readings indexed in your course syllabus, construct a causal argument..."
        bind:value={prompt}
      ></textarea>
    </div>

    <div class="form-row-3">
      <div class="form-group">
        <label class="field-label">Assignment Type</label>
        <select class="field-select"><option>Long-Form Essay</option><option>Short Response</option><option>Socratic Dialogue</option></select>
      </div>
      <div class="form-group">
        <label class="field-label">Scaffold Tier</label>
        <select class="field-select"><option>Tier 1 — Minimal</option><option selected>Tier 2 — Structural</option><option>Tier 3 — Full Guided</option></select>
      </div>
      <div class="form-group">
        <label class="field-label">Word Limit</label>
        <input type="number" class="field-input" value="1200" />
      </div>
    </div>

    <button class="btn btn-primary generate-btn" onclick={generateScaffold} disabled={isGenerating || !prompt.trim()}>
      {#if isGenerating}⏳ Generating Grounded Scaffold...{:else}⚡ Generate AutoSCORE Scaffold{/if}
    </button>

    {#if generatedScaffold}
      <div class="scaffold-output">
        <div class="output-title">Generated Rubric Scaffold</div>
        <div class="output-tier-badge">{generatedScaffold.scaffoldTier}</div>
        <div class="verbal-anchors">
          {#each generatedScaffold.verbalAnchors as anchor}
            <span class="anchor-tag">{anchor}</span>
          {/each}
        </div>
        <div class="rubric-criteria">
          {#each generatedScaffold.rubricCriteria as c}
            <div class="criterion-card">
              <div class="criterion-header">
                <span class="criterion-label">{c.label}</span>
                <span class="criterion-points">{c.points} pts</span>
              </div>
              <p class="criterion-desc">{c.desc}</p>
            </div>
          {/each}
        </div>
        <div class="output-actions">
          <button class="btn btn-secondary">Save as Draft</button>
          <button class="btn btn-primary">Publish to Students →</button>
        </div>
      </div>
    {/if}
  </main>

  <!-- Right: Rubric & Review Panel -->
  <aside class="review-col">
    <div class="col-header">
      <div class="col-title">AutoSCORE Preview</div>
      <div class="col-sub">Live rubric criteria scoring simulation</div>
    </div>

    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-label">Rubric Criteria</div><div class="kpi-val" style="color: var(--color-horizon-bright);">4</div></div>
      <div class="kpi-card"><div class="kpi-label">Total Points</div><div class="kpi-val">100</div></div>
    </div>

    <div class="review-placeholder">
      <div style="font-size: 32px;">🎯</div>
      <div style="font-size: 13px; color: var(--color-slate-light); text-align: center;">Generate a scaffold to preview the AutoSCORE rubric and NLI evidence chains here.</div>
    </div>
  </aside>
</div>

<style>
  .designer-layout { display: grid; grid-template-columns: 320px 1fr 380px; min-height: calc(100vh - 56px); }
  .knowledge-col { background: var(--color-graphite); border-right: 1px solid var(--color-graphite-border); padding: 24px 20px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
  .editor-col { padding: 32px 36px; display: flex; flex-direction: column; gap: 24px; overflow-y: auto; background: var(--color-obsidian); }
  .review-col { background: var(--color-graphite); border-left: 1px solid var(--color-graphite-border); padding: 24px 20px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
  .col-header { display: flex; flex-direction: column; gap: 4px; }
  .col-title { font-size: 14px; font-weight: 700; color: #fff; }
  .col-sub { font-size: 11px; color: var(--color-slate-muted); }
  .panel-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--color-slate-muted); margin-bottom: 8px; }
  .target-node-card { background: #0f172a; border: 1px solid var(--color-horizon-blue); border-radius: var(--radius-sm); padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 0 12px rgba(59,130,246,.2); }
  .kc-code { font-family: var(--font-mono); font-size: 11px; color: var(--color-horizon-bright); font-weight: 600; }
  .kc-name { font-size: 13px; font-weight: 600; color: #fff; }
  .kc-status { font-size: 10.5px; color: var(--color-slate-muted); }
  .prereq-stack { display: flex; flex-direction: column; gap: 10px; }
  .prereq-card { background: var(--color-graphite-card); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 10px 14px; display: flex; flex-direction: column; gap: 4px; }
  .prereq-code { font-family: var(--font-mono); font-size: 10px; color: var(--color-aurora-bright); }
  .prereq-title { font-size: 12px; color: #e2e8f0; font-weight: 500; }
  .prereq-meta { font-size: 10.5px; color: var(--color-slate-muted); }
  .progress-track { height: 4px; background: var(--color-graphite-border); border-radius: var(--radius-full); overflow: hidden; }
  .progress-fill { height: 100%; background: var(--color-horizon-blue); border-radius: var(--radius-full); }
  .autonomy-card { background: #0f172a; border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }
  .traps-stack { display: flex; flex-direction: column; gap: 10px; }
  .trap-card { background: #0f172a; border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
  .trap-code { font-family: var(--font-mono); font-size: 10.5px; color: var(--color-amber); font-weight: 600; }
  .trap-desc { font-size: 11.5px; color: #cbd5e1; line-height: 1.4; }
  .trap-trigger { font-size: 10.5px; color: var(--color-slate-muted); }
  .editor-header { display: flex; flex-direction: column; gap: 4px; }
  .editor-title { font-size: 20px; font-weight: 700; color: #fff; }
  .editor-subtitle { font-size: 12.5px; color: var(--color-slate-muted); }
  .form-group { display: flex; flex-direction: column; gap: 8px; }
  .field-label { font-size: 11.5px; font-weight: 700; text-transform: uppercase; color: var(--color-slate-light); letter-spacing: .4px; }
  .field-textarea, .field-select, .field-input { background: var(--color-graphite); border: 1px solid var(--color-graphite-border); color: #fff; padding: 10px 14px; border-radius: var(--radius-sm); font-family: var(--font-body); font-size: 13.5px; width: 100%; box-sizing: border-box; }
  .field-textarea:focus, .field-select:focus, .field-input:focus { outline: none; border-color: var(--color-horizon-blue); }
  .field-textarea { resize: vertical; }
  .form-row-3 { display: grid; grid-template-columns: 1fr 1fr 120px; gap: 14px; }
  .generate-btn { align-self: flex-start; }
  .scaffold-output { background: var(--color-graphite); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-lg); padding: 24px; display: flex; flex-direction: column; gap: 16px; }
  .output-title { font-size: 15px; font-weight: 700; color: #fff; }
  .output-tier-badge { display: inline-block; font-size: 11px; font-weight: 600; background: rgba(59,130,246,.15); border: 1px solid rgba(59,130,246,.3); color: var(--color-horizon-bright); padding: 3px 10px; border-radius: var(--radius-full); }
  .verbal-anchors { display: flex; flex-wrap: wrap; gap: 6px; }
  .anchor-tag { font-size: 11px; font-family: var(--font-mono); background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.3); color: #34d399; padding: 2px 8px; border-radius: var(--radius-xs); }
  .rubric-criteria { display: flex; flex-direction: column; gap: 10px; }
  .criterion-card { background: var(--color-graphite-card); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 14px 16px; }
  .criterion-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .criterion-label { font-size: 13px; font-weight: 600; color: #fff; }
  .criterion-points { font-size: 14px; font-weight: 700; color: var(--color-horizon-bright); }
  .criterion-desc { font-size: 12.5px; color: var(--color-slate-light); margin: 0; line-height: 1.5; }
  .output-actions { display: flex; justify-content: flex-end; gap: 10px; }
  .kpi-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .kpi-card { background: var(--color-graphite-card); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 14px 16px; }
  .kpi-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--color-slate-muted); margin-bottom: 4px; }
  .kpi-val { font-family: var(--font-brand); font-size: 24px; font-weight: 700; color: #fff; }
  .review-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; padding: 40px 20px; border: 2px dashed var(--color-graphite-border); border-radius: var(--radius-md); }
</style>
