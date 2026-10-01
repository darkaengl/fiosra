<script lang="ts">
  import type { SupportResult, Probe } from './workspaceTypes';

  let {
    isOpen = false,
    published = null,
    isSupportBusy = false,
    supportResult = null,
    currentProbe = null,
    probeResponse = $bindable(''),
    isProbeBusy = false,
    probeNotice = '',
    evidenceSummary = { evidence_submitted: 0, pending_questions: 0 },
    onRequestSupport = () => {},
    onClearSupportResult = () => {},
    onSubmitProbeResponse = () => {},
    onChangeProbe = () => {},
    onClose = () => {},
  } = $props<{
    isOpen?: boolean;
    published?: any;
    isSupportBusy?: boolean;
    supportResult?: SupportResult | null;
    currentProbe?: Probe | null;
    probeResponse?: string;
    isProbeBusy?: boolean;
    probeNotice?: string;
    evidenceSummary?: { evidence_submitted: number; pending_questions?: number };
    onRequestSupport?: (actionId: string) => void;
    onClearSupportResult?: () => void;
    onSubmitProbeResponse?: () => void;
    onChangeProbe?: (probeId: string, action: string) => void;
    onClose?: () => void;
  }>();
</script>

{#if isOpen}
  <aside class="socratic-tutor-column flyout-mode" aria-label="Optional writing support">
    <header class="tutor-header">
      <div>
        <span class="eyebrow">Optional support</span>
        <h3>Writing support</h3>
      </div>
      <button class="close-panel-btn" onclick={onClose} title="Close Panel (Esc)">✕</button>
    </header>

    <div class="tutor-body">
      {#if published?.support_menu?.length}
        <div class="completion-support-menu">
          <span class="card-eyebrow">Choose what would help now</span>
          {#each published.support_menu as item}
            <button
              class="completion-support-action"
              disabled={isSupportBusy}
              onclick={() => onRequestSupport(item.action_id)}
            >
              <strong>{item.title}</strong>
              <small>{item.description}</small>
            </button>
          {/each}
        </div>
      {/if}

      {#if supportResult}
        <div class="support-result-card">
          <div class="probe-meta"><span class="section-tag">Next useful step</span></div>
          <h4>{supportResult.title}</h4>
          <p>{supportResult.guidance}</p>
          <ol>
            {#each supportResult.next_steps as step}
              <li>{step}</li>
            {/each}
          </ol>
          <button class="defer-btn" onclick={onClearSupportResult}>Choose another support option</button>
        </div>
      {:else if currentProbe}
        <div class="probe-card">
          <div class="probe-meta">
            <span class="section-tag">{currentProbe.section_label || 'Active paragraph'}</span>
            <span class="focus-pill">{currentProbe.focus_type?.replace(/_/g, ' ') || 'Focus'}</span>
          </div>

          <p class="probe-question">{currentProbe.question}</p>

          <div class="probe-pedagogy-tip">
            <p>Use this optional question only if it helps you develop or revise your response. Your educator evaluates the final work.</p>
          </div>

          <label for="probe-input" class="probe-input-label">Your working note</label>
          <textarea
            id="probe-input"
            bind:value={probeResponse}
            disabled={isProbeBusy}
            placeholder="Write a note that helps you continue your own draft."
            class="probe-textarea"
          ></textarea>

          {#if probeNotice}<p class="probe-status-msg" role="status">{probeNotice}</p>{/if}

          <div class="probe-actions">
            <button
              class="save-evidence-btn"
              onclick={onSubmitProbeResponse}
              disabled={isProbeBusy || probeResponse.trim().length < 10}
            >
              {isProbeBusy ? 'Saving…' : 'Save note'}
            </button>
            <button
              class="defer-btn"
              onclick={() => onChangeProbe(currentProbe?.probe_id || '', 'defer')}
              disabled={isProbeBusy}
            >
              Later
            </button>
            <button
              class="dismiss-btn"
              onclick={() => onChangeProbe(currentProbe?.probe_id || '', 'dismiss')}
              disabled={isProbeBusy}
            >
              Dismiss
            </button>
          </div>
        </div>
      {:else}
        <div class="empty-probe-state">
          <h4>No Pending Probes</h4>
          <p>Use the assignment, materials, and rubric to continue your draft. Optional support will be available when it can help you take a next step.</p>
          {#if evidenceSummary?.evidence_submitted}
            <span class="evidence-badge">
              ✓ {evidenceSummary.evidence_submitted} evidence response{evidenceSummary.evidence_submitted === 1 ? '' : 's'} recorded
            </span>
          {/if}
        </div>
      {/if}
    </div>
  </aside>
{/if}

<style>
  .socratic-tutor-column.flyout-mode {
    position: fixed;
    top: 52px;
    right: 0;
    bottom: 0;
    width: 380px;
    background: var(--color-graphite, #1c1d21);
    border-left: 1px solid var(--color-graphite-border, #2d3039);
    box-shadow: -6px 0 28px rgba(0, 0, 0, 0.5);
    z-index: 100;
    display: flex;
    flex-direction: column;
    animation: slideInRight 0.2s ease-out;
  }

  @keyframes slideInRight {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
  }

  .tutor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 18px;
    border-bottom: 1px solid var(--color-graphite-border, #2d3039);
  }

  .eyebrow {
    display: block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-muted, #94a3b8);
  }

  .tutor-header h3 {
    margin: 0;
    font-size: 15px;
    color: var(--color-heading, #f1f5f9);
  }

  .close-panel-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-muted, #94a3b8);
    font-size: 16px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
  }

  .close-panel-btn:hover {
    color: var(--color-heading, #f1f5f9);
    background: var(--color-graphite-hover, #282a32);
  }

  .tutor-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .completion-support-menu {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-graphite-border, #2d3039);
  }

  .card-eyebrow {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-muted, #94a3b8);
  }

  .completion-support-action {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--color-graphite-border, #2d3039);
    border-radius: 6px;
    padding: 10px;
    text-align: left;
    cursor: pointer;
    transition: background 0.15s ease;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .completion-support-action:hover:not(:disabled) {
    background: var(--color-graphite-hover, #282a32);
    border-color: #8b5cf6;
  }

  .completion-support-action strong {
    font-size: 12px;
    color: var(--color-heading, #f1f5f9);
  }

  .completion-support-action small {
    font-size: 10.5px;
    color: var(--color-slate-muted, #94a3b8);
  }

  .support-result-card {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .support-result-card h4 {
    margin: 0;
    font-size: 14px;
    color: var(--color-heading, #f1f5f9);
  }

  .support-result-card p {
    margin: 0;
    font-size: 12px;
    line-height: 1.45;
    color: var(--color-slate-light, #cbd5e1);
  }

  .support-result-card ol {
    margin: 0;
    padding-left: 18px;
    font-size: 11.5px;
    color: var(--color-slate-light, #cbd5e1);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .probe-card {
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid var(--color-graphite-border, #2d3039);
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .probe-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .section-tag {
    font-size: 10px;
    font-weight: 700;
    color: var(--color-horizon-blue, #38bdf8);
  }

  .focus-pill {
    font-size: 9.5px;
    font-weight: 800;
    text-transform: uppercase;
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
    padding: 1px 6px;
    border-radius: 99px;
  }

  .probe-question {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.45;
    color: var(--color-heading, #f1f5f9);
  }

  .probe-pedagogy-tip {
    font-size: 10.5px;
    line-height: 1.4;
    color: var(--color-slate-muted, #94a3b8);
  }

  .probe-pedagogy-tip p {
    margin: 0;
  }

  .probe-input-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-slate-light, #cbd5e1);
  }

  .probe-textarea {
    width: 100%;
    min-height: 80px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--color-graphite-border, #2d3039);
    border-radius: 6px;
    padding: 10px;
    color: var(--color-heading, #f1f5f9);
    font-size: 12px;
    resize: vertical;
    outline: none;
    font-family: inherit;
    box-sizing: border-box;
  }

  .probe-textarea:focus {
    border-color: #8b5cf6;
  }

  .probe-status-msg {
    margin: 0;
    font-size: 11px;
    color: #38bdf8;
  }

  .probe-actions {
    display: flex;
    gap: 8px;
  }

  .save-evidence-btn {
    flex: 1;
    background: #8b5cf6;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 11.5px;
    font-weight: 700;
    cursor: pointer;
  }

  .save-evidence-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .defer-btn, .dismiss-btn {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #2d3039);
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 11.5px;
    color: var(--color-slate-muted, #94a3b8);
    cursor: pointer;
  }

  .defer-btn:hover, .dismiss-btn:hover {
    color: var(--color-heading, #f1f5f9);
    background: var(--color-graphite-hover, #282a32);
  }

  .empty-probe-state {
    text-align: center;
    padding: 24px 12px;
    color: var(--color-slate-muted, #94a3b8);
    font-size: 12px;
  }

  .empty-probe-state h4 {
    margin: 0 0 6px;
    font-size: 14px;
    color: var(--color-heading, #f1f5f9);
  }

  .evidence-badge {
    display: inline-block;
    margin-top: 10px;
    padding: 4px 10px;
    border-radius: 99px;
    background: rgba(16, 185, 129, 0.15);
    color: #6ee7b7;
    font-size: 11px;
    font-weight: 700;
  }
</style>
