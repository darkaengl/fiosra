<script lang="ts">
  import { FOCUS_TYPE_LABELS, type SocraticProbe } from './marginaliaTypes';

  let {
    probe,
    isTargeted = false,
    isBusy = false,
    onSelectBlock = () => {},
    onRespond = async () => null,
    onDefer = async () => null,
    onDismiss = async () => null,
    onEscalateToAgent = () => {},
    onAssumptionAction = async () => null,
  } = $props<{
    probe: SocraticProbe;
    isTargeted?: boolean;
    isBusy?: boolean;
    onSelectBlock?: (id?: string) => void;
    onRespond?: (probeId: string, text: string) => Promise<any>;
    onDefer?: (probeId: string) => Promise<any>;
    onDismiss?: (probeId: string) => Promise<any>;
    onEscalateToAgent?: (probe: SocraticProbe) => void;
    onAssumptionAction?: (probe: SocraticProbe, action: string) => Promise<any>;
  }>();

  let replyText = $state('');
  let isAssumptionExpanded = $state(false);

  let focusInfo = $derived(
    FOCUS_TYPE_LABELS[probe.focus_type || ''] || {
      label: probe.focus_type || 'Inquiry',
      icon: '❓',
      color: 'var(--color-aurora, #0284c7)'
    }
  );

  async function handleFormSubmit(e: SubmitEvent) {
    e.preventDefault();
    const text = replyText.trim();
    if (!probe.probe_id || text.length < 5 || isBusy) return;
    replyText = '';
    await onRespond(probe.probe_id, text);
  }

  async function handleAssumptionClick(action: string) {
    isAssumptionExpanded = false;
    await onAssumptionAction(probe, action);
  }
</script>

<div
  class="probe-card"
  data-probe-block-id={probe.block_id}
  class:is-active-target={isTargeted}
  class:status-responded={probe.status === 'responded'}
  class:status-deferred={probe.status === 'deferred'}
>
  <!-- Card Header: Focus badge, concept badge, and active status -->
  <div class="probe-card-header">
    <span class="focus-badge" style:--focus-color={focusInfo.color}>
      <span class="focus-icon">{focusInfo.icon}</span>
      <span>{focusInfo.label}</span>
    </span>

    {#if probe.concept_label || probe.concept_id}
      <span class="kc-badge" title={probe.concept_id}>
        {probe.concept_label || probe.concept_id}
      </span>
    {/if}

    {#if probe.confidence_stance}
      <span class="scholastic-stance-tag">{probe.confidence_stance}</span>
    {/if}

    {#if probe.scaffolding_rung !== undefined && probe.scaffolding_rung > 0}
      <span class="scholastic-rung-tag">Level {probe.scaffolding_rung} Inquiry</span>
    {/if}

    {#if isTargeted}
      <span class="current-block-tag">
        <span class="dot-pulse"></span>
        <span>Active Block</span>
      </span>
    {/if}
  </div>

  <!-- Claim Anchor Excerpt (clickable jump to canvas block) -->
  {#if probe.claim_text}
    <button
      type="button"
      class="claim-anchor"
      onclick={() => probe.block_id && onSelectBlock(probe.block_id)}
      title="Click to jump to this paragraph in the canvas"
    >
      <span class="anchor-pin">📌</span>
      <span class="anchor-quote">
        "{probe.claim_text.length > 95 ? probe.claim_text.slice(0, 95) + '…' : probe.claim_text}"
      </span>
      <span class="anchor-jump">Jump ↗</span>
    </button>
  {/if}

  <!-- Subtle Scholarly Assumption Note -->
  {#if probe.assumption || probe.implicit_premise}
    {@const assumptionText = probe.assumption || probe.implicit_premise}
    <div class="scholarly-assumption-note">
      <span class="assumption-lead">Assumes:</span>
      <button
        type="button"
        class="assumption-toggle"
        onclick={() => (isAssumptionExpanded = !isAssumptionExpanded)}
        title="Click to examine assumption"
      >
        “{assumptionText}”
        <span class="assumption-affordance">· examine ▾</span>
      </button>

      {#if isAssumptionExpanded}
        <div class="assumption-options-row">
          <button type="button" class="btn-assumption-opt" onclick={() => handleAssumptionClick('defend')}>
            Defend premise
          </button>
          <button type="button" class="btn-assumption-opt" onclick={() => handleAssumptionClick('test_sources')}>
            Test in sources
          </button>
          <button type="button" class="btn-assumption-opt" onclick={() => handleAssumptionClick('concede')}>
            Concede &amp; revise
          </button>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Inquiry Question -->
  <div class="probe-question">
    <p>{probe.question}</p>
  </div>

  <!-- Inquiry Response State -->
  {#if probe.status === 'responded'}
    <div class="probe-resolved-box">
      <div class="resolved-badge">
        <span>✅</span>
        <strong>Epistemic Pivot Captured</strong>
      </div>
      {#if probe.response_text}
        <p class="resolved-text">"{probe.response_text}"</p>
      {/if}
    </div>
  {:else if probe.status === 'deferred'}
    <div class="probe-deferred-box">
      <div class="deferred-badge">
        <span>⏳</span>
        <span>Postponed for later revision</span>
      </div>
      <button
        type="button"
        class="btn-resume"
        onclick={() => onDefer(probe.probe_id)}
        disabled={isBusy}
      >
        Reopen Inquiry
      </button>
    </div>
  {:else}
    <div class="probe-canvas-hint">
      <span>💡</span>
      <small>Rewrite in the Canvas to resolve, or explain your reasoning:</small>
    </div>

    <form class="probe-reply-form" onsubmit={handleFormSubmit}>
      <textarea
        bind:value={replyText}
        placeholder="Clarify evidence, scope, or causal link..."
        rows="3"
        disabled={isBusy}
        aria-label="Socratic explanation response"
      ></textarea>

      <div class="probe-form-actions">
        <button
          type="submit"
          class="btn-respond"
          disabled={isBusy || !(replyText && replyText.trim().length >= 5)}
        >
          {isBusy ? 'Submitting...' : 'Submit Explanation'}
        </button>

        <div class="secondary-actions">
          <button
            type="button"
            class="btn-text"
            onclick={() => onDefer(probe.probe_id)}
            disabled={isBusy}
            title="Defer inquiry for later"
          >
            Later
          </button>
          <button
            type="button"
            class="btn-text"
            onclick={() => onDismiss(probe.probe_id)}
            disabled={isBusy}
            title="Dismiss inquiry"
          >
            Dismiss
          </button>
        </div>
      </div>
    </form>
  {/if}

  <!-- Scholarly Card Footer: Subtle Footnote Escalation -->
  <div class="card-scholastic-footer">
    <button
      type="button"
      class="escalation-footnote-btn"
      onclick={() => onEscalateToAgent(probe)}
      title="Discuss this paragraph in depth with the Socratic Tutor"
    >
      Discuss in depth with tutor ↗
    </button>
  </div>
</div>

<style>
  .probe-card {
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-radius: 8px;
    padding: 14px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
  }

  :global([data-theme="dark"]) .probe-card {
    background: #181d26;
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  }

  .probe-card.is-active-target {
    border-color: var(--color-aurora, #0284c7);
    box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2), 0 4px 12px rgba(2, 132, 199, 0.08);
  }

  .probe-card.status-responded {
    opacity: 0.85;
    background: #fafcfb;
    border-color: rgba(5, 150, 105, 0.25);
  }

  :global([data-theme="dark"]) .probe-card.status-responded {
    background: #141b17;
  }

  .probe-card.status-deferred {
    opacity: 0.75;
    border-style: dashed;
    border-color: rgba(245, 158, 11, 0.35);
  }

  .probe-card-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 7px;
    margin-bottom: 10px;
  }

  .focus-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--focus-color, var(--color-aurora));
    background: rgba(2, 132, 199, 0.08);
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid rgba(2, 132, 199, 0.18);
  }

  .kc-badge {
    font-size: 0.7rem;
    padding: 2px 6px;
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    color: var(--color-slate-light);
    font-family: var(--font-mono, monospace);
  }

  :global([data-theme="dark"]) .kc-badge {
    background: rgba(255, 255, 255, 0.05);
  }

  .current-block-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--color-aurora, #0284c7);
    margin-left: auto;
    background: rgba(2, 132, 199, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .dot-pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-aurora, #0284c7);
    animation: pulseGlow 1.8s infinite;
  }

  @keyframes pulseGlow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.3); }
  }

  .claim-anchor {
    display: flex;
    align-items: baseline;
    gap: 6px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px dashed var(--color-graphite-border);
    border-radius: 6px;
    padding: 5px 8px;
    margin-bottom: 10px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
    width: 100%;
    box-sizing: border-box;
  }

  :global([data-theme="dark"]) .claim-anchor {
    background: rgba(255, 255, 255, 0.04);
  }

  .claim-anchor:hover {
    background: rgba(2, 132, 199, 0.08);
    border-color: rgba(2, 132, 199, 0.35);
  }

  .anchor-pin {
    font-size: 0.78rem;
    flex-shrink: 0;
  }

  .anchor-quote {
    font-size: 0.76rem;
    font-style: italic;
    color: var(--color-slate-light);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }

  .anchor-jump {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--color-aurora, #0284c7);
    flex-shrink: 0;
    letter-spacing: 0.02em;
  }

  .probe-question {
    font-size: 0.9rem;
    line-height: 1.45;
    color: var(--color-heading, var(--color-slate-bright));
    margin-bottom: 12px;
    font-weight: 500;
  }

  .probe-question p { margin: 0; }

  .probe-canvas-hint {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.76rem;
    color: var(--color-slate-subtle);
    margin-bottom: 8px;
    line-height: 1.35;
  }

  .probe-reply-form textarea {
    width: 100%;
    box-sizing: border-box;
    font-family: var(--font-ui, sans-serif);
    font-size: 0.84rem;
    line-height: 1.4;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid var(--color-graphite-border);
    background: var(--color-bone-muted, #f8f8f5);
    color: var(--color-slate-bright);
    resize: vertical;
    transition: border-color 0.15s ease;
  }

  :global([data-theme="dark"]) .probe-reply-form textarea {
    background: rgba(18, 22, 29, 0.8);
    border-color: rgba(255, 255, 255, 0.12);
  }

  .probe-reply-form textarea:focus {
    outline: none;
    border-color: var(--color-aurora);
    box-shadow: 0 0 0 2px var(--color-aurora-glow);
  }

  .probe-form-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
  }

  .btn-respond {
    background: var(--color-aurora, #0284c7);
    color: #ffffff;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .btn-respond:hover:not(:disabled) {
    background: var(--color-aurora-bright, #0369a1);
  }

  .btn-respond:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .secondary-actions {
    display: flex;
    gap: 6px;
  }

  .btn-text {
    background: none;
    border: none;
    font-size: 0.76rem;
    color: var(--color-slate-subtle);
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 4px;
  }

  .btn-text:hover:not(:disabled) {
    color: var(--color-slate-bright);
    background: rgba(0, 0, 0, 0.05);
  }

  :global([data-theme="dark"]) .btn-text:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.08);
  }

  .probe-resolved-box {
    background: rgba(5, 150, 105, 0.08);
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: 6px;
    padding: 9px 11px;
  }

  .resolved-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    color: var(--color-signal-green-text, #065f46);
    margin-bottom: 4px;
  }

  :global([data-theme="dark"]) .resolved-badge {
    color: #34d399;
  }

  .resolved-text {
    font-size: 0.8rem;
    font-style: italic;
    color: var(--color-slate-light);
    margin: 0;
  }

  .probe-deferred-box {
    background: rgba(245, 158, 11, 0.08);
    border: 1px dashed rgba(245, 158, 11, 0.3);
    border-radius: 6px;
    padding: 9px 11px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .deferred-badge {
    font-size: 0.76rem;
    color: var(--color-amber, #d97706);
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .btn-resume {
    background: none;
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: var(--color-amber, #d97706);
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    cursor: pointer;
  }

  .btn-resume:hover {
    background: rgba(245, 158, 11, 0.15);
  }

  .scholastic-stance-tag {
    font-size: 10px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-muted);
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--color-graphite-border);
    padding: 1px 6px;
    border-radius: 4px;
    letter-spacing: 0.02em;
  }

  :global([data-theme="dark"]) .scholastic-stance-tag {
    background: rgba(255, 255, 255, 0.04);
  }

  .scholastic-rung-tag {
    font-size: 10px;
    font-family: var(--font-mono, monospace);
    color: var(--color-horizon-blue, #d97706);
    background: rgba(217, 119, 6, 0.08);
    border: 1px solid rgba(217, 119, 6, 0.2);
    padding: 1px 6px;
    border-radius: 4px;
  }

  .scholarly-assumption-note {
    margin: 8px 0;
    padding: 6px 10px;
    background: rgba(217, 119, 6, 0.04);
    border-left: 2px solid var(--color-horizon-blue, #d97706);
    border-radius: 0 4px 4px 0;
    font-size: 0.78rem;
    line-height: 1.4;
  }

  .assumption-lead {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
    color: var(--color-slate-muted);
    margin-right: 4px;
  }

  .assumption-toggle {
    background: none;
    border: none;
    padding: 0;
    font-family: inherit;
    font-size: inherit;
    font-style: italic;
    color: var(--color-slate-light);
    cursor: pointer;
    text-align: left;
    display: inline;
  }

  .assumption-toggle:hover {
    color: var(--color-heading);
    text-decoration: underline;
  }

  .assumption-affordance {
    font-style: normal;
    font-size: 0.7rem;
    color: var(--color-horizon-blue, #d97706);
    margin-left: 4px;
  }

  .assumption-options-row {
    display: flex;
    gap: 6px;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed var(--color-graphite-border);
  }

  .btn-assumption-opt {
    background: none;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 0.7rem;
    font-family: var(--font-ui);
    color: var(--color-slate-light);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-assumption-opt:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
    border-color: var(--color-horizon-blue, #d97706);
  }

  .card-scholastic-footer {
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid rgba(0, 0, 0, 0.04);
    display: flex;
    justify-content: flex-end;
  }

  :global([data-theme="dark"]) .card-scholastic-footer {
    border-top-color: rgba(255, 255, 255, 0.04);
  }

  .escalation-footnote-btn {
    background: none;
    border: none;
    padding: 0;
    font-family: var(--font-ui);
    font-size: 0.72rem;
    color: var(--color-slate-muted);
    cursor: pointer;
    transition: color 0.15s ease;
  }

  .escalation-footnote-btn:hover {
    color: var(--color-horizon-blue, #d97706);
    text-decoration: underline;
  }
</style>
