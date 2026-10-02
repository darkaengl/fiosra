<script>
  let {
    rubric = $bindable([]),
    activeModule = null,
    isSynthesizing = false,
    onSynthesize = () => {},
    onAutoBalance = () => {},
    onAddCriterion = () => {},
    onRemoveCriterion = () => {},
  } = $props();

  const totalRubricWeight = $derived(
    rubric.reduce((acc, curr) => acc + Number(curr.weight || 0), 0)
  );
</script>

<section class="card-section">
  <div class="card-header space-between">
    <div>
      <div class="header-tag">03 · TRANSPARENT RUBRIC</div>
      <h2>Evaluation Standards &amp; Weights</h2>
      <p class="section-desc">Students consult these exact criteria as they draft. AutoSCORE follows these standards strictly.</p>
    </div>
    <div class="rubric-header-actions">
      <div class="weight-badge {totalRubricWeight === 100 ? 'balanced' : 'unbalanced'}">
        Total Weight: {totalRubricWeight}% {totalRubricWeight === 100 ? '✓' : '(Needs 100%)'}
      </div>
      {#if totalRubricWeight !== 100}
        <button type="button" class="btn-text-action" onclick={onAutoBalance}>
          Auto-Balance
        </button>
      {/if}
      <button
        type="button"
        class="btn-ai-rubric btn-sm"
        onclick={onSynthesize}
        disabled={isSynthesizing}
        title="Synthesize authentic, topic-grounded criteria with 3-level descriptors using AI"
      >
        <span class="sparkle {isSynthesizing ? 'pulsing' : ''}">✦</span>
        {isSynthesizing ? 'Synthesizing…' : 'AI Generate Rubric'}
      </button>
      <button type="button" class="btn-secondary btn-sm" onclick={onAddCriterion}>
        + Add Criterion
      </button>
    </div>
  </div>

  {#if (activeModule?.learning_objectives?.length || activeModule?.knowledge_components?.length)}
    <div class="module-concepts-preview">
      <div class="concepts-preview-header">
        <span class="concepts-icon">🎯</span>
        <span class="concepts-label">Module Target Concepts &amp; Learning Objectives:</span>
      </div>
      <div class="concepts-chips">
        {#each (activeModule.learning_objectives || []) as obj}
          <span class="concept-chip" title="Module Learning Objective">{obj}</span>
        {/each}
        {#each (activeModule.knowledge_components || []) as kc}
          <span class="concept-chip kc" title="Knowledge Component">
            ⚡ {typeof kc === 'string' ? kc.replace(/^KC_[A-Z]+_/, '').replace(/_/g, ' ') : (kc.label || kc.kc_id || kc)}
          </span>
        {/each}
      </div>
    </div>
  {/if}

  <div class="rubric-list">
    {#each rubric as criterion, index}
      <div class="rubric-card-item">
        <div class="rubric-card-top">
          <div class="criterion-name-row">
            <span class="criterion-num">{index + 1}</span>
            <input
              class="criterion-title-input"
              bind:value={criterion.title}
              placeholder="Criterion Name (e.g. Primary Source Synthesis)"
            />
          </div>
          <div class="weight-control">
            <label for={`weight-crit-${index}`}>Weight:</label>
            <input
              id={`weight-crit-${index}`}
              type="number"
              min="0"
              max="100"
              class="weight-input"
              bind:value={criterion.weight}
            />
            <span>%</span>
            <button
              type="button"
              class="btn-delete-item"
              title="Delete criterion"
              onclick={() => onRemoveCriterion(index)}
            >
              ✕
            </button>
          </div>
        </div>

        {#if criterion.concept_label || criterion.concept_id}
          <div class="criterion-concept-tag">
            <span class="concept-tag-icon">⚡ Tied Concept:</span>
            <span class="concept-tag-name">{criterion.concept_label || criterion.concept_id}</span>
          </div>
        {/if}

        <div class="form-group">
          <label for={`desc-crit-${index}`}>Description of Standard</label>
          <textarea
            id={`desc-crit-${index}`}
            class="input-textarea"
            rows="2"
            bind:value={criterion.description}
            placeholder="Explain what constitutes mastery of this skill..."
          ></textarea>
        </div>

        <!-- 3-Tier Achievement Levels Grid -->
        <div class="levels-grid">
          {#each criterion.levels as level}
            <div class="level-box">
              <span class="level-name {level.level_id}">{level.label}</span>
              <textarea
                class="level-desc-input"
                rows="2"
                bind:value={level.description}
                placeholder={`Expectations for ${level.label}...`}
              ></textarea>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>
</section>

<style>
  .card-section {
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    background: var(--color-surface, #ffffff);
    border: 1px solid var(--color-graphite-border, #d0d7de);
  }

  :global([data-theme="dark"]) .card-section {
    background: #161b22;
    border-color: #30363d;
  }

  .card-header {
    margin-bottom: 20px;
  }
  .card-header.space-between {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }

  .header-tag {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: var(--color-aurora, #0969da);
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .card-header h2 {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 6px;
  }

  .section-desc {
    font-size: 13px;
    color: var(--color-slate-subtle, #57606a);
    margin: 0;
    line-height: 1.45;
  }

  :global([data-theme="dark"]) .section-desc {
    color: #8b949e;
  }

  .rubric-header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .weight-badge {
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
  }
  .weight-badge.balanced {
    background: rgba(26, 127, 55, 0.12);
    color: #1a7f37;
    border: 1px solid rgba(26, 127, 55, 0.25);
  }
  .weight-badge.unbalanced {
    background: rgba(187, 85, 0, 0.12);
    color: #bc4c00;
    border: 1px solid rgba(187, 85, 0, 0.25);
  }

  :global([data-theme="dark"]) .weight-badge.balanced {
    background: rgba(46, 160, 67, 0.15);
    color: #3fb950;
    border-color: rgba(46, 160, 67, 0.3);
  }
  :global([data-theme="dark"]) .weight-badge.unbalanced {
    background: rgba(210, 153, 34, 0.15);
    color: #d29922;
    border-color: rgba(210, 153, 34, 0.3);
  }

  .btn-text-action {
    background: transparent;
    border: none;
    color: var(--color-aurora, #0969da);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
  }

  .btn-ai-rubric {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-ai-rubric:hover:not(:disabled) {
    opacity: 0.92;
    transform: translateY(-1px);
  }
  .btn-ai-rubric:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: 1px solid var(--color-graphite-border, #d0d7de);
    color: var(--color-heading, #1f2328);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-secondary {
    border-color: #30363d;
    color: #f0f6fc;
  }

  .btn-secondary:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.06);
  }

  .btn-sm {
    padding: 5px 10px;
    font-size: 11.5px;
  }

  .sparkle {
    font-size: 13px;
  }
  .sparkle.pulsing {
    display: inline-block;
    animation: pulse 1s infinite alternate;
  }
  @keyframes pulse {
    0% { transform: scale(1); opacity: 0.7; }
    100% { transform: scale(1.3); opacity: 1; }
  }

  .module-concepts-preview {
    background: rgba(9, 105, 218, 0.04);
    border: 1px solid rgba(9, 105, 218, 0.15);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
  }

  :global([data-theme="dark"]) .module-concepts-preview {
    background: rgba(56, 139, 253, 0.06);
    border-color: rgba(56, 139, 253, 0.2);
  }

  .concepts-preview-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    font-weight: 700;
    color: var(--color-aurora, #0969da);
    margin-bottom: 6px;
  }

  .concepts-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .concept-chip {
    display: inline-flex;
    align-items: center;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 11px;
    background: rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.08);
  }

  :global([data-theme="dark"]) .concept-chip {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.1);
    color: #e6edf3;
  }

  .concept-chip.kc {
    background: #ede9fe;
    border-color: #ddd6fe;
    color: #5b21b6;
    font-weight: 600;
  }

  :global([data-theme="dark"]) .concept-chip.kc {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.4);
    color: #d8b4fe;
  }

  .criterion-concept-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 10px;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    background: #ede9fe;
    border: 1px solid #ddd6fe;
    color: #6d28d9;
  }

  :global([data-theme="dark"]) .criterion-concept-tag {
    background: rgba(124, 58, 237, 0.15);
    border-color: rgba(124, 58, 237, 0.35);
    color: #c4b5fd;
  }

  .concept-tag-icon { font-weight: 800; }
  .concept-tag-name { font-weight: 700; }

  .rubric-list { display: flex; flex-direction: column; gap: 16px; }

  .rubric-card-item {
    border-radius: 8px;
    padding: 16px;
    background: #f6f8fa;
    border: 1px solid #d0d7de;
  }

  :global([data-theme="dark"]) .rubric-card-item {
    background: #0d1117;
    border-color: #30363d;
  }

  .rubric-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .criterion-name-row { display: flex; align-items: center; gap: 10px; flex: 1; }

  .criterion-num {
    font-size: 11px;
    font-weight: 800;
    border-radius: 4px;
    padding: 3px 7px;
    background: #eaeef2;
    color: #57606a;
  }

  :global([data-theme="dark"]) .criterion-num {
    background: #21262d;
    color: #8b949e;
  }

  .criterion-title-input {
    flex: 0.8;
    background: transparent;
    border: 1px solid transparent;
    font-size: 14px;
    font-weight: 700;
    padding: 4px 6px;
    outline: none;
    border-bottom: 1px solid #d0d7de;
    color: #1f2328;
  }

  .criterion-title-input:focus {
    border-color: #0969da;
    background: #ffffff;
    border-radius: 4px;
  }

  :global([data-theme="dark"]) .criterion-title-input {
    border-bottom-color: #30363d;
    color: #f0f6fc;
  }

  :global([data-theme="dark"]) .criterion-title-input:focus {
    border-color: #58a6ff;
    background: #161b22;
  }

  .weight-control {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #57606a;
  }

  :global([data-theme="dark"]) .weight-control {
    color: #8b949e;
  }

  .weight-input {
    width: 48px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
    padding: 3px 6px;
    text-align: center;
    outline: none;
    background: #ffffff;
    border: 1px solid #d0d7de;
    color: #1f2328;
  }

  :global([data-theme="dark"]) .weight-input {
    background: #161b22;
    border-color: #30363d;
    color: #f0f6fc;
  }

  .btn-delete-item {
    background: transparent;
    border: none;
    color: #cf222e;
    font-size: 13px;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 4px;
  }
  .btn-delete-item:hover {
    background: rgba(207, 34, 46, 0.1);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 14px;
  }

  .form-group label {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--color-slate-subtle, #57606a);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  :global([data-theme="dark"]) .form-group label {
    color: #8b949e;
  }

  .input-textarea {
    width: 100%;
    border-radius: 6px;
    border: 1px solid #d0d7de;
    background: #ffffff;
    color: #1f2328;
    padding: 8px 12px;
    font-family: inherit;
    font-size: 13px;
    line-height: 1.5;
    outline: none;
    box-sizing: border-box;
    resize: vertical;
  }

  .input-textarea:focus {
    border-color: #0969da;
    box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.15);
  }

  :global([data-theme="dark"]) .input-textarea {
    background: #161b22;
    border-color: #30363d;
    color: #f0f6fc;
  }

  :global([data-theme="dark"]) .input-textarea:focus {
    border-color: #58a6ff;
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
  }

  .levels-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-top: 10px;
  }

  .level-box {
    border-radius: 6px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: #ffffff;
    border: 1px solid #d0d7de;
  }

  :global([data-theme="dark"]) .level-box {
    background: #161b22;
    border-color: #21262d;
  }

  .level-name {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .level-name.developing { color: #9a6700; }
  .level-name.secure { color: #0969da; }
  .level-name.strong { color: #1a7f37; }

  :global([data-theme="dark"]) .level-name.developing { color: #d29922; }
  :global([data-theme="dark"]) .level-name.secure { color: #58a6ff; }
  :global([data-theme="dark"]) .level-name.strong { color: #3fb950; }

  .level-desc-input {
    background: transparent;
    border: 0;
    font-family: inherit;
    font-size: 11.5px;
    line-height: 1.45;
    padding: 0;
    outline: none;
    resize: vertical;
    color: #57606a;
  }

  :global([data-theme="dark"]) .level-desc-input {
    color: #c9d1d9;
  }
</style>
