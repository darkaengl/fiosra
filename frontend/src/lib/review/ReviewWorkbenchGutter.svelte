<script>
  import ReviewRubricTab from "./ReviewRubricTab.svelte";
  import ReviewTrapsTab from "./ReviewTrapsTab.svelte";
  import ReviewTraceTab from "./ReviewTraceTab.svelte";

  let {
    selected,
    dossier,
    workbenchWidth = 380,
    grade = $bindable(""),
    feedback = $bindable(""),
    isFinalizing = false,
    onFinalize,
    activeEvalTab = $bindable("rubric"),
    totalRubricCriteria = 0,
    scan = null,
    isScanning = false,
    scanError = "",
    courseId = "",
    activeInterventions = [],
    interventionNotice = "",
    onRunScan,
    onDismissNotice,
    onAcknowledgeIntervention,
    onDispatchIntervention,
    reasoningNodes = [],
    activityNodes = [],
  } = $props();
</script>

<aside
  class="canvas-workbench-gutter"
  style:width={`${workbenchWidth}px`}
>
  <!-- Pinned Sovereign Grade Finalization Bar -->
  <div class="gutter-finalization-bar">
    {#if selected.status === "submitted"}
      <div class="gutter-grade-form">
        <div class="grade-input-group">
          <label class="field-label-mini">
            <span>Grade</span>
            <input
              type="text"
              class="input-grade-compact"
              bind:value={grade}
              placeholder="A, 92%"
            />
          </label>
          <label class="field-label-mini feedback-flex">
            <span>Formative Feedback</span>
            <input
              type="text"
              class="input-feedback-compact"
              bind:value={feedback}
              placeholder="Feedback for next cycle…"
            />
          </label>
        </div>
        <button
          type="button"
          class="btn-finalize-compact"
          onclick={onFinalize}
          disabled={isFinalizing || !grade.trim()}
        >
          {isFinalizing ? "Finalizing…" : "Finalize Grade & Seal ➔"}
        </button>
      </div>
    {:else if selected.status === "completed"}
      <div class="gutter-sealed-banner">
        <span class="sealed-check">✓</span>
        <div class="sealed-text">
          <strong>Grade Finalized & Sealed</strong>
          <small>Recorded in sovereign ledger.</small>
        </div>
        <a
          class="btn-sealed-pdf"
          href={`/evidence/dossier/${selected.session_id}/pdf`}
          download
        >
          ⬇ PDF
        </a>
      </div>
    {:else}
      <div class="gutter-draft-banner">
        <span class="draft-dot">●</span>
        <div class="draft-text">
          <strong>Live Student Session</strong>
          <small>Student actively reasoning.</small>
        </div>
        <a
          class="btn-recorder-link"
          href={`#/student/trace?session_id=${selected.session_id}`}
        >
          Trace ↗
        </a>
      </div>
    {/if}
  </div>

  <!-- Workbench Tabs Bar -->
  <nav class="gutter-tabs-bar">
    <button
      type="button"
      class="gutter-tab-btn"
      class:active={activeEvalTab === "rubric"}
      onclick={() => (activeEvalTab = "rubric")}
    >
      <span>📊 Rubric</span>
      <span class="gutter-tab-count">{totalRubricCriteria}</span>
    </button>

    <button
      type="button"
      class="gutter-tab-btn"
      class:active={activeEvalTab === "traps"}
      onclick={() => (activeEvalTab = "traps")}
    >
      <span>🪤 Traps</span>
      <span
        class="gutter-tab-count"
        class:alert={scan && (scan.findings || []).length > 0}
      >
        {scan ? (scan.findings || []).length : "Scan"}
      </span>
    </button>

    <button
      type="button"
      class="gutter-tab-btn"
      class:active={activeEvalTab === "reasoning"}
      onclick={() => (activeEvalTab = "reasoning")}
    >
      <span>💡 Trace</span>
      <span class="gutter-tab-count"
        >{reasoningNodes.length + activityNodes.length}</span
      >
    </button>
  </nav>

  <!-- Workbench Tab Body Viewport (Independently Scrolling) -->
  <div class="gutter-tab-viewport">
    <!-- ── TAB 1: Rubric Assessment ── -->
    {#if activeEvalTab === "rubric"}
      <ReviewRubricTab {dossier} />

    <!-- ── TAB 2: Cognitive Traps & Misconceptions ── -->
    {:else if activeEvalTab === "traps"}
      <ReviewTrapsTab
        {scan}
        {isScanning}
        {scanError}
        {courseId}
        {activeInterventions}
        {interventionNotice}
        {onRunScan}
        {onDismissNotice}
        {onAcknowledgeIntervention}
        {onDispatchIntervention}
      />

    <!-- ── TAB 3: Reasoning Trace ── -->
    {:else if activeEvalTab === "reasoning"}
      <ReviewTraceTab
        sessionId={selected.session_id}
        {reasoningNodes}
        {activityNodes}
      />
    {/if}
  </div>
</aside>

<style>
  .canvas-workbench-gutter {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    border-left: 1px solid var(--color-graphite-border);
  }

  /* Pinned Finalization Bar */
  .gutter-finalization-bar {
    padding: 8px 12px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .gutter-grade-form {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .grade-input-group {
    display: flex;
    gap: 8px;
  }

  .field-label-mini {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .field-label-mini.feedback-flex {
    flex: 1;
    min-width: 0;
  }

  .field-label-mini span {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: var(--color-slate-muted);
  }

  .input-grade-compact {
    width: 68px;
    padding: 4px 7px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .input-feedback-compact {
    width: 100%;
    padding: 4px 7px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .input-grade-compact:focus,
  .input-feedback-compact:focus {
    outline: none;
    border-color: #4f6bff;
  }

  .btn-finalize-compact {
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 700;
    background: #059669;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.12s;
    width: 100%;
  }

  .btn-finalize-compact:hover:not(:disabled) {
    background: #047857;
  }

  .btn-finalize-compact:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .gutter-sealed-banner,
  .gutter-draft-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 11px;
  }

  .gutter-sealed-banner {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
  }

  .gutter-draft-banner {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
  }

  .sealed-check {
    color: #059669;
    font-weight: 700;
  }

  .draft-dot {
    color: #0369a1;
  }

  .sealed-text,
  .draft-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .sealed-text strong,
  .draft-text strong {
    font-size: 11px;
    color: var(--color-heading);
  }

  .sealed-text small,
  .draft-text small {
    font-size: 9.5px;
    color: var(--color-slate-muted);
  }

  .btn-sealed-pdf,
  .btn-recorder-link {
    font-size: 10.5px;
    font-weight: 600;
    color: inherit;
    text-decoration: underline;
  }

  /* Gutter Tabs Bar */
  .gutter-tabs-bar {
    display: flex;
    border-bottom: 1px solid var(--color-graphite-border);
    background: #ffffff;
    flex-shrink: 0;
  }

  .gutter-tab-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 6px;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-muted);
    cursor: pointer;
    transition: all 0.12s;
    font-family: inherit;
  }

  .gutter-tab-btn:hover {
    background: var(--color-bone, #f6f5f1);
    color: var(--color-heading);
  }

  .gutter-tab-btn.active {
    color: #0f172a;
    border-bottom-color: #4f6bff;
    font-weight: 700;
    background: #ffffff;
  }

  .gutter-tab-count {
    font-size: 9.5px;
    background: var(--color-bone, #f6f5f1);
    color: var(--color-slate-muted);
    padding: 1px 5px;
    border-radius: 999px;
    border: 1px solid var(--color-graphite-border);
  }

  .gutter-tab-count.alert {
    background: #fef3c7;
    color: #92400e;
    border-color: #fde68a;
  }

  /* Gutter Tab Viewport (Independently Scrolling) */
  .gutter-tab-viewport {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px 40px;
  }
</style>
