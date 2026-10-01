<script lang="ts">
  let {
    isOutlineOpen = $bindable(false),
    editor = null,
    isLocked = false,
    onToggleCanvasLock = () => {},
    isEpistemicLens = $bindable(true),
    epistemicMetrics = { claim: 0, evidence: 0, reasoning: 0, assumption: 0, premature: 0 },
    canvasWidthMode = $bindable('wide'),
    onSetCanvasWidthMode = () => {},
    isZenFullscreen = false,
    onToggleZen = () => {},
    isSaving = false,
    isDirty = false,
    saveError = '',
    saveErrorDetails = null,
    lastConfirmedSaveAt = '',
    onSyncNow = () => {},
    onSetBlock = () => {},
    onToggleHeading = () => {},
    onToggleMark = () => {},
  } = $props<{
    isOutlineOpen?: boolean;
    editor?: any;
    isLocked?: boolean;
    onToggleCanvasLock?: () => void;
    isEpistemicLens?: boolean;
    epistemicMetrics?: { claim: number; evidence: number; reasoning: number; assumption: number; premature: number };
    canvasWidthMode?: string;
    onSetCanvasWidthMode?: (mode: string) => void;
    isZenFullscreen?: boolean;
    onToggleZen?: () => void;
    isSaving?: boolean;
    isDirty?: boolean;
    saveError?: string;
    saveErrorDetails?: any;
    lastConfirmedSaveAt?: string;
    onSyncNow?: () => void;
    onSetBlock?: (type: string) => void;
    onToggleHeading?: (level: number) => void;
    onToggleMark?: (mark: string) => void;
  }>();
</script>

<header class="minimal-toolbar">
  <div class="toolbar-left">
    <button
      type="button"
      class="tool-btn outline-toggle-btn"
      class:active={isOutlineOpen}
      onclick={() => (isOutlineOpen = !isOutlineOpen)}
      title="Toggle document outline & sections"
    >
      <span class="outline-icon">☰</span>
      <span>Outline</span>
    </button>

    <div class="v-divider"></div>

    <button
      type="button"
      class="tool-btn"
      class:active={editor?.isActive('paragraph')}
      onclick={() => onSetBlock('paragraph')}
      disabled={isLocked}
    >
      Text
    </button>
    <button
      type="button"
      class="tool-btn"
      class:active={editor?.isActive('heading', { level: 1 })}
      onclick={() => onToggleHeading(1)}
      disabled={isLocked}
    >
      H1
    </button>
    <button
      type="button"
      class="tool-btn"
      class:active={editor?.isActive('heading', { level: 2 })}
      onclick={() => onToggleHeading(2)}
      disabled={isLocked}
    >
      H2
    </button>
    <button
      type="button"
      class="tool-btn font-bold"
      class:active={editor?.isActive('bold')}
      onclick={() => onToggleMark('bold')}
      disabled={isLocked}
    >
      B
    </button>
    <button
      type="button"
      class="tool-btn font-italic"
      class:active={editor?.isActive('italic')}
      onclick={() => onToggleMark('italic')}
      disabled={isLocked}
    >
      I
    </button>
    <button
      type="button"
      class="tool-btn lock-toggle-btn"
      class:unlocked={!isLocked}
      class:locked={isLocked}
      onclick={onToggleCanvasLock}
      title={isLocked ? 'Canvas is locked (click to unlock and edit)' : 'Canvas is unlocked (click to lock)'}
      aria-label={isLocked ? 'Unlock canvas for editing' : 'Lock canvas'}
    >
      {#if isLocked}
        <span class="lock-icon">🔒</span>
        <span class="lock-label">Locked</span>
      {:else}
        <span class="lock-icon">🔓</span>
        <span class="lock-label">Editing</span>
      {/if}
    </button>
  </div>

  <div class="toolbar-center">
    <!-- Minimalist High-Visibility Truth Highlights Toggle -->
    <button
      type="button"
      class="truth-highlights-toggle"
      class:active={isEpistemicLens}
      onclick={() => (isEpistemicLens = !isEpistemicLens)}
      title="Toggle sentence-level epistemic highlighting & analysis"
      aria-pressed={isEpistemicLens}
    >
      <span class="truth-toggle-ring">
        <span class="truth-toggle-pip"></span>
      </span>
      <span class="truth-toggle-text">Truth Highlights</span>
      <span class="truth-toggle-pill">{isEpistemicLens ? 'ON' : 'OFF'}</span>
    </button>

    <!-- Epistemic Live Sentence Counters -->
    {#if isEpistemicLens}
      <div class="epistemic-sentence-strip">
        <span class="strip-pill claim" title="🔵 Claims">
          🔵 <strong>{epistemicMetrics.claim}</strong>
        </span>
        <span class="strip-pill evidence" title="🟢 Grounded Evidence">
          🟢 <strong>{epistemicMetrics.evidence}</strong>
        </span>
        <span class="strip-pill reasoning" title="🟣 Causal Reasoning">
          🟣 <strong>{epistemicMetrics.reasoning}</strong>
        </span>
        <span class="strip-pill assumption" title="🟡 Assumptions">
          🟡 <strong>{epistemicMetrics.assumption}</strong>
        </span>
        {#if epistemicMetrics.premature > 0}
          <span class="strip-pill premature" title="🔴 Premature Closures (Unsupported Leaps)">
            🔴 <strong>{epistemicMetrics.premature}</strong> Leaps
          </span>
        {/if}
      </div>
    {/if}
  </div>

  <div class="toolbar-right">
    <!-- Canvas Width Dropdown (Narrow / Wide / Max) -->
    <div class="canvas-width-picker">
      <select
        class="canvas-width-select"
        value={canvasWidthMode}
        onchange={(e) => onSetCanvasWidthMode((e.target as HTMLSelectElement).value)}
        title="Canvas Width Mode"
        aria-label="Canvas Width Mode"
      >
        <option value="narrow">Narrow</option>
        <option value="wide">Wide</option>
        <option value="max">Max</option>
      </select>
    </div>

    <!-- Zen 3-Box Focus Mode Toggle -->
    <button
      type="button"
      class="btn-zen-canvas-toggle"
      class:active={isZenFullscreen}
      onclick={onToggleZen}
      title={isZenFullscreen ? 'Exit Zen Focus Mode (Esc or Fn+F)' : 'Zen 3-Box Focus Mode (Fn+F)'}
      aria-label="Toggle Zen 3-Box Focus Mode"
    >
      {#if isZenFullscreen}
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
        </svg>
      {:else}
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
        </svg>
      {/if}
    </button>

    <div class="v-divider"></div>

    <div class="save-status-text" aria-live="polite">
      {#if saveError}
        <span class="save-status-message">⚠️ {saveError}</span>
        {#if saveErrorDetails?.retryable}
          <button type="button" class="save-status-action" onclick={onSyncNow} disabled={isSaving}>Retry save</button>
        {/if}
        {#if saveErrorDetails?.correlationId}
          <small class="save-status-correlation">Support ID: {saveErrorDetails.correlationId}</small>
        {/if}
      {:else if isSaving}
        <span>Saving…</span>
      {:else if isDirty}
        <span>Autosaving…</span>
      {:else}
        <span>✓ Saved{lastConfirmedSaveAt ? ' just now' : ''}</span>
      {/if}
    </div>
  </div>
</header>

<style>
  .minimal-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 6px 16px;
    background: var(--color-bone-surface, #ffffff);
    border-bottom: 1px solid var(--color-graphite-border, #e2e8f0);
    flex-shrink: 0;
    min-height: 42px;
    z-index: 10;
  }

  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .tool-btn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: var(--color-slate-muted, #64748b);
    font-size: 11px;
    font-weight: 600;
    padding: 3px 7px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .tool-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #f1f5f9);
    color: var(--color-heading, #0f172a);
  }

  .tool-btn.active {
    background: var(--color-graphite-hover, #f1f5f9);
    color: var(--color-heading, #0f172a);
    border-color: var(--color-graphite-border, #cbd5e1);
  }

  .tool-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .font-bold { font-weight: 800; }
  .font-italic { font-style: italic; }

  .outline-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(0, 0, 0, 0.04);
  }

  .v-divider {
    width: 1px;
    height: 18px;
    background: var(--color-graphite-border, #e2e8f0);
    margin: 0 4px;
  }

  .lock-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .truth-highlights-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: 99px;
    font-size: 10.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .truth-highlights-toggle.active {
    background: rgba(59, 130, 246, 0.08);
    border-color: rgba(59, 130, 246, 0.3);
    color: #2563eb;
  }

  .truth-toggle-ring {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    border: 1.5px solid currentColor;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .truth-highlights-toggle.active .truth-toggle-pip {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #2563eb;
  }

  .truth-toggle-pill {
    font-size: 8.5px;
    font-weight: 800;
    padding: 0 4px;
    border-radius: 3px;
    background: rgba(0, 0, 0, 0.06);
  }

  .epistemic-sentence-strip {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: 6px;
  }

  .strip-pill {
    font-size: 9.5px;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.04);
  }

  .canvas-width-select {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: 4px;
    font-size: 10.5px;
    padding: 2px 4px;
    color: var(--color-slate-muted, #64748b);
    cursor: pointer;
  }

  .btn-zen-canvas-toggle {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 3px;
    color: var(--color-slate-muted, #64748b);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-zen-canvas-toggle:hover {
    background: var(--color-graphite-hover, #f1f5f9);
    color: var(--color-heading, #0f172a);
  }

  .save-status-text {
    font-size: 10.5px;
    color: var(--color-slate-muted, #64748b);
  }

  .save-status-message {
    color: #e11d48;
  }

  .save-status-action {
    background: transparent;
    border: underline;
    color: #2563eb;
    cursor: pointer;
    font-size: 10.5px;
    padding: 0;
  }
</style>
