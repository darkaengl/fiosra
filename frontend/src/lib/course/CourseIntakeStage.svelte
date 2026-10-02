<script>
  let {
    materialsText = $bindable(''),
    titleHint = $bindable(''),
    selectedDomain = $bindable('History'),
    targetAudience = $bindable('Undergraduate'),
    isGenerating = false,
    onLoadSample = () => {},
    onSynthesize = () => {},
  } = $props();
</script>

<div class="intake-studio-grid">
  <!-- Left Column: Architect Guidance, Standards & Quick Presets -->
  <aside class="intake-sidebar">
    <div class="intake-intro-card">
      <div class="badge-spark">✨ AI Curriculum Architect</div>
      <h2>Socratic Course Studio</h2>
      <p class="intake-desc">
        Transform raw course syllabi, lecture schedules, and reading lists into a scaffolded, inquiry-driven curriculum with Bloom's-aligned learning objectives.
      </p>
    </div>

    <div class="intake-methodology-card">
      <div class="method-header">Pedagogical Standards</div>
      <div class="method-item">
        <span class="method-icon">📐</span>
        <div>
          <strong>Progressive Inquiry Scaffolding</strong>
          <p>Sequences modules from foundational framing to structural debate and evidentiary synthesis.</p>
        </div>
      </div>
      <div class="method-item">
        <span class="method-icon">🎯</span>
        <div>
          <strong>Bloom's Taxonomy Objectives</strong>
          <p>Synthesizes active, measurable cognitive verbs for verifiable student progression.</p>
        </div>
      </div>
      <div class="method-item">
        <span class="method-icon">📜</span>
        <div>
          <strong>Authentic Primary Evidence</strong>
          <p>Anchors Socratic inquiry assignments directly in historical texts and artifact readings.</p>
        </div>
      </div>
    </div>

    <div class="intake-presets-card">
      <span class="presets-header">Quick Starter Presets</span>
      <button type="button" class="preset-pill-btn" onclick={onLoadSample}>
        <div class="preset-info">
          <span class="preset-name">📜 Early Modern Ireland (1536–1750)</span>
          <span class="preset-sub">History & Historiography · Undergraduate</span>
        </div>
        <span class="preset-action">Load Sample →</span>
      </button>
    </div>
  </aside>

  <!-- Right Column: Materials Workbench Form -->
  <div class="intake-workbench-card">
    <div class="workbench-header">
      <div>
        <h3>Course Parameters & Syllabus Source</h3>
        <span class="workbench-sub">Paste syllabus content, lecture schedules, or reading references to synthesize an initial draft</span>
      </div>
      <button type="button" class="btn-sample-link" onclick={onLoadSample}>
        ⚡ Insert Sample Syllabus
      </button>
    </div>

    <div class="intake-body">
      <div class="form-grid-top">
        <div class="input-wrap title-wrap">
          <label for="course-title-hint">Course Title or Identifier</label>
          <input
            id="course-title-hint"
            type="text"
            class="clean-input"
            placeholder="e.g. HI4083: Early Modern Ireland, 1536-1750"
            bind:value={titleHint}
          />
        </div>

        <div class="input-wrap">
          <label for="course-domain">Academic Discipline</label>
          <select id="course-domain" class="clean-select" bind:value={selectedDomain}>
            <option value="History">History</option>
            <option value="Economics">Economics</option>
            <option value="Literature">Literature</option>
            <option value="Philosophy">Philosophy</option>
            <option value="Social Sciences">Social Sciences</option>
          </select>
        </div>

        <div class="input-wrap">
          <label for="target-audience">Academic Level</label>
          <select id="target-audience" class="clean-select" bind:value={targetAudience}>
            <option value="Undergraduate">Undergraduate</option>
            <option value="Advanced Undergraduate">Advanced Seminar</option>
            <option value="Graduate">Graduate</option>
          </select>
        </div>
      </div>

      <div class="textarea-wrap">
        <div class="textarea-label-row">
          <label for="materials-input">Syllabus Text, Weekly Modules & Reading References</label>
        </div>
        <textarea
          id="materials-input"
          class="clean-textarea"
          rows="12"
          placeholder="Paste course syllabus, lecture units, primary source reading links, or learning goals here…"
          bind:value={materialsText}
        ></textarea>
      </div>

      <div class="workbench-footer">
        <div class="workbench-note">
          💡 Fiosra synthesizes an editable curriculum draft that you can iteratively critique and refine with the AI Co-Pilot.
        </div>
        <button
          type="button"
          class="btn-synthesize"
          disabled={isGenerating || !materialsText.trim()}
          onclick={onSynthesize}
        >
          {#if isGenerating}
            <span class="spinner-sm"></span> Synthesizing Course Blueprint…
          {:else}
            ✨ Synthesize Course Draft with AI
          {/if}
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  .intake-studio-grid {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 32px;
    align-items: start;
    margin-top: 8px;
  }

  .intake-sidebar {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .intake-intro-card, .intake-methodology-card, .intake-presets-card {
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-md, 8px);
    padding: 20px 22px;
  }

  .badge-spark {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-horizon-bright, #d97706);
    margin-bottom: 6px;
  }

  .intake-intro-card h2 {
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading, #0f172a);
    margin: 4px 0 8px;
    line-height: 1.3;
  }

  .intake-desc {
    font-size: 13px;
    line-height: 1.55;
    color: var(--color-slate-light, #475569);
    margin: 0;
  }

  .method-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted, #64748b);
    margin-bottom: 14px;
  }

  .method-item {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
  }
  .method-item:last-child {
    margin-bottom: 0;
  }

  .method-icon {
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .method-item strong {
    font-size: 12.5px;
    color: var(--color-heading, #0f172a);
    display: block;
    margin-bottom: 2px;
  }

  .method-item p {
    font-size: 11.5px;
    color: var(--color-slate-light, #475569);
    line-height: 1.45;
    margin: 0;
  }

  .presets-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted, #64748b);
    display: block;
    margin-bottom: 10px;
  }

  .preset-pill-btn {
    width: 100%;
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-sm, 6px);
    padding: 12px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }
  .preset-pill-btn:hover {
    border-color: var(--color-horizon-blue, #4f6bff);
    background: var(--color-graphite-card, #ffffff);
  }

  .preset-info {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .preset-name {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-heading, #0f172a);
  }

  .preset-sub {
    font-size: 11px;
    color: var(--color-slate-muted, #64748b);
  }

  .preset-action {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-aurora-bright, #0284c7);
    white-space: nowrap;
    margin-left: 8px;
  }

  /* Right Workbench Card */
  .intake-workbench-card {
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-md, 8px);
    padding: 24px 28px;
  }

  .workbench-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-graphite-border, #e2e8f0);
    margin-bottom: 20px;
  }

  .workbench-header h3 {
    font-size: 17px;
    font-weight: 700;
    color: var(--color-heading, #0f172a);
    margin: 0 0 4px;
  }

  .workbench-sub {
    font-size: 12.5px;
    color: var(--color-slate-light, #475569);
  }

  .intake-body {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .form-grid-top {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 14px;
  }

  .input-wrap {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .input-wrap label, .textarea-label-row label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted, #64748b);
  }

  .textarea-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
  }

  .btn-sample-link {
    background: transparent;
    border: none;
    color: var(--color-horizon-bright, #d97706);
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-sample-link:hover {
    text-decoration: underline;
  }

  .clean-input, .clean-select {
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-sm, 6px);
    padding: 9px 12px;
    font-size: 13px;
    color: var(--color-slate-bright, #0f172a);
    outline: none;
    transition: border-color 0.15s;
  }

  .clean-textarea {
    width: 100%;
    box-sizing: border-box;
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-sm, 6px);
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.55;
    color: var(--color-slate-bright, #0f172a);
    outline: none;
    resize: vertical;
    transition: border-color 0.15s;
  }

  .clean-input:focus, .clean-select:focus, .clean-textarea:focus {
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .workbench-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding-top: 14px;
    border-top: 1px solid var(--color-graphite-border, #e2e8f0);
  }

  .workbench-note {
    font-size: 12px;
    color: var(--color-slate-muted, #64748b);
    line-height: 1.4;
    flex: 1;
  }

  .btn-synthesize {
    padding: 11px 24px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-md, 8px);
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    white-space: nowrap;
  }
  .btn-synthesize:hover:not(:disabled) {
    opacity: 0.95;
  }
  .btn-synthesize:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .spinner-sm {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 900px) {
    .intake-studio-grid {
      grid-template-columns: 1fr;
    }
    .form-grid-top {
      grid-template-columns: 1fr;
    }
  }
</style>
