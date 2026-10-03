<script lang="ts">
  import type { InstructorIntervention } from './marginaliaTypes';

  let {
    intervention,
    isTargeted = false,
    onSelectBlock = () => {},
    onRespondIntervention = async () => null,
  } = $props<{
    intervention: InstructorIntervention;
    isTargeted?: boolean;
    onSelectBlock?: (id: string) => void;
    onRespondIntervention?: (id: string, text: string) => Promise<any>;
  }>();

  let inputText = $state('');
  let isSubmitting = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    const text = inputText.trim();
    if (!intervention.intervention_id || text.length < 5 || isSubmitting) return;
    isSubmitting = true;
    try {
      await onRespondIntervention(intervention.intervention_id, text);
      inputText = '';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div
  class="intervention-card"
  data-intervention-block-id={intervention.block_id}
  class:is-active-target={isTargeted}
  class:status-responded={intervention.status === 'responded' || intervention.status === 'acknowledged'}
>
  <!-- Header -->
  <div class="intervention-card-header">
    <div class="intervention-header-left">
      <span class="instructor-badge">
        <span class="instructor-icon">👨‍🏫</span>
        <span>Instructor Challenge</span>
      </span>
      {#if intervention.concept_label}
        <span class="intervention-concept-badge">{intervention.concept_label}</span>
      {/if}
    </div>
    {#if isTargeted}
      <span class="current-block-tag">
        <span class="dot-pulse"></span>
        <span>Active Paragraph</span>
      </span>
    {/if}
  </div>

  <!-- Quoted Text Anchor -->
  {#if intervention.evidence_quote}
    <button
      type="button"
      class="claim-anchor"
      onclick={() => intervention.block_id && onSelectBlock(intervention.block_id)}
      title="Click to jump to this paragraph in your writing"
    >
      <span class="anchor-label">From your writing:</span>
      <span class="anchor-text">"{intervention.evidence_quote}"</span>
    </button>
  {/if}

  <!-- Challenge Question -->
  <p class="intervention-question-text">{intervention.activity_prompt}</p>

  <!-- Reading Guidance -->
  {#if intervention.activity_guidance}
    <div class="intervention-guidance-box">
      <span class="guidance-icon">💡</span>
      <span class="guidance-text">{intervention.activity_guidance}</span>
    </div>
  {/if}

  <!-- Form Area -->
  {#if intervention.status === 'dispatched'}
    <form class="intervention-reply-form" onsubmit={handleSubmit}>
      <textarea
        id={`intervention-reply-${intervention.intervention_id}`}
        class="intervention-textarea"
        rows="3"
        placeholder="Type your reflection or response here..."
        bind:value={inputText}
        disabled={isSubmitting}
      ></textarea>
      <div class="intervention-form-actions">
        <span class="intervention-discreet-note">Shared with your instructor</span>
        <button
          type="submit"
          class="btn-send-reflection"
          disabled={isSubmitting || !inputText.trim()}
        >
          {isSubmitting ? 'Sending...' : 'Send Reflection'}
        </button>
      </div>
    </form>
  {:else}
    <div class="intervention-echo-box">
      <div class="echo-status-line">
        <span class="check-icon">✓</span>
        <span>{intervention.status === 'acknowledged' ? 'Acknowledged by instructor' : 'Reflection shared with instructor'}</span>
      </div>
      {#if intervention.student_reflection}
        <p class="echo-text">"{intervention.student_reflection}"</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .intervention-card {
    background: #ffffff;
    border: 1px solid rgba(217, 119, 6, 0.28);
    border-left: 3.5px solid #d97706;
    border-radius: 8px;
    padding: 13px 14px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :global([data-theme="dark"]) .intervention-card {
    background: #181d26;
    border-color: rgba(217, 119, 6, 0.3);
    border-left-color: #d97706;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  }

  .intervention-card.is-active-target {
    border-color: #d97706;
    box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.2), 0 4px 12px rgba(217, 119, 6, 0.08);
  }

  .intervention-card.status-responded {
    border-color: rgba(5, 150, 105, 0.3);
    border-left-color: #059669;
    background: #fafcfb;
  }

  :global([data-theme="dark"]) .intervention-card.status-responded {
    background: #141b17;
    border-color: rgba(5, 150, 105, 0.25);
    border-left-color: #059669;
  }

  .intervention-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    flex-wrap: wrap;
  }

  .intervention-header-left {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .instructor-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #92400e;
    background: rgba(245, 158, 11, 0.12);
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: 0.01em;
  }

  :global([data-theme="dark"]) .instructor-badge {
    background: rgba(217, 119, 6, 0.2);
    color: #fbbf24;
  }

  .intervention-concept-badge {
    font-size: 0.68rem;
    font-weight: 500;
    color: var(--color-slate-muted);
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid var(--color-graphite-border);
    padding: 1px 6px;
    border-radius: 3px;
  }

  :global([data-theme="dark"]) .intervention-concept-badge {
    background: rgba(255, 255, 255, 0.04);
  }

  .current-block-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.68rem;
    font-weight: 600;
    color: #2563eb;
    background: rgba(37, 99, 235, 0.08);
    padding: 2px 6px;
    border-radius: 999px;
  }

  .dot-pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #2563eb;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.3); opacity: 0.5; }
  }

  .claim-anchor {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    background: rgba(0, 0, 0, 0.02);
    border: 1px dashed var(--color-graphite-border);
    border-radius: 5px;
    padding: 6px 9px;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s ease;
    width: 100%;
    box-sizing: border-box;
  }

  .claim-anchor:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .claim-anchor {
    background: rgba(255, 255, 255, 0.02);
  }

  .anchor-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-subtle);
  }

  .anchor-text {
    font-size: 0.78rem;
    font-style: italic;
    color: var(--color-slate-bright);
    line-height: 1.35;
  }

  .intervention-question-text {
    font-size: 0.85rem;
    line-height: 1.48;
    font-weight: 600;
    color: var(--color-heading);
    margin: 0;
  }

  .intervention-guidance-box {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.75rem;
    line-height: 1.38;
    color: var(--color-slate-light);
    background: rgba(0, 0, 0, 0.02);
    border: 1px solid var(--color-graphite-border);
    padding: 6px 9px;
    border-radius: 5px;
  }

  :global([data-theme="dark"]) .intervention-guidance-box {
    background: rgba(255, 255, 255, 0.02);
  }

  .intervention-guidance-box .guidance-icon {
    font-size: 0.8rem;
    flex-shrink: 0;
    line-height: 1.2;
  }

  .intervention-reply-form {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 2px;
  }

  .intervention-textarea {
    width: 100%;
    box-sizing: border-box;
    font-family: var(--font-ui, sans-serif);
    font-size: 0.82rem;
    line-height: 1.42;
    padding: 7px 10px;
    border-radius: 6px;
    border: 1px solid var(--color-graphite-border);
    background: var(--color-bone-muted, #f8f8f6);
    color: var(--color-slate-bright);
    resize: vertical;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  :global([data-theme="dark"]) .intervention-textarea {
    background: rgba(18, 22, 29, 0.85);
    border-color: rgba(255, 255, 255, 0.12);
    color: #e2e8f0;
  }

  .intervention-textarea:focus {
    outline: none;
    border-color: #d97706;
    box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.15);
  }

  .intervention-form-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .intervention-discreet-note {
    font-size: 0.7rem;
    color: var(--color-slate-subtle);
    font-style: italic;
  }

  .btn-send-reflection {
    background: #0b4a4f;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: var(--font-ui, sans-serif);
    cursor: pointer;
    transition: background 0.15s ease, transform 0.1s ease;
  }

  .btn-send-reflection:hover:not(:disabled) {
    background: #08373b;
  }

  .btn-send-reflection:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .intervention-echo-box {
    padding-top: 6px;
    border-top: 1px dashed rgba(5, 150, 105, 0.3);
  }

  .echo-status-line {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #059669;
  }

  .echo-text {
    font-size: 0.78rem;
    font-style: italic;
    color: var(--color-slate-light);
    margin: 4px 0 0 0;
    padding: 6px 9px;
    background: rgba(5, 150, 105, 0.05);
    border-left: 2px solid #059669;
    border-radius: 0 4px 4px 0;
  }
</style>
