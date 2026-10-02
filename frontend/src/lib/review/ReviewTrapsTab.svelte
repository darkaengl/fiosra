<script>
  let {
    scan = null,
    isScanning = false,
    scanError = '',
    courseId = '',
    activeInterventions = [],
    interventionNotice = '',
    onRunScan = () => {},
    onDismissNotice = () => {},
    onAcknowledgeIntervention = () => {},
    onDispatchIntervention = async () => {},
  } = $props();

  let draftOpenFor = $state('');
  let draftBody = $state('');
  let draftSubject = $state('');
  let challengeDraftOpenFor = $state('');
  let challengeDraftPrompt = $state('');
  let isDispatching = $state(false);

  function openChallengeDraft(finding) {
    if (challengeDraftOpenFor === finding.misconception_id) {
      challengeDraftOpenFor = '';
      return;
    }
    challengeDraftOpenFor = finding.misconception_id;
    challengeDraftPrompt = finding.activity_prompt || finding.suggested_message?.body || '';
  }

  async function handleDispatch(finding) {
    isDispatching = true;
    try {
      await onDispatchIntervention(finding, challengeDraftPrompt);
      challengeDraftOpenFor = '';
    } finally {
      isDispatching = false;
    }
  }

  function openDraft(finding) {
    draftOpenFor = finding.misconception_id;
    draftSubject = finding.suggested_message?.subject || '';
    draftBody = finding.suggested_message?.body || '';
  }

  function openInMailClient() {
    const url = `mailto:?subject=${encodeURIComponent(draftSubject)}&body=${encodeURIComponent(draftBody)}`;
    window.open(url, '_blank');
  }

  async function copyDraft() {
    try {
      await navigator.clipboard.writeText(
        `Subject: ${draftSubject}\n\n${draftBody}`
      );
    } catch (err) {
      console.warn('Clipboard unavailable', err);
    }
  }
</script>

<div class="traps-inspector">
  {#if !scan}
    <div class="trap-scan-prompt">
      <span class="trap-scan-icon">🪤</span>
      <h4>Misconception Trap Scan</h4>
      <p class="trap-scan-desc">
        Scans student thesis against cognitive traps authored in
        the course knowledge graph.
      </p>
      <button
        type="button"
        class="btn-trigger-scan"
        onclick={onRunScan}
        disabled={isScanning}
      >
        {isScanning ? 'Analyzing with LLM…' : '⚡ Run Trap Scan'}
      </button>
      {#if isScanning}
        <p class="scan-running-note">
          Evidencing mental models (takes ~20s)…
        </p>
      {/if}
    </div>
  {:else if (scan.findings || []).length === 0}
    <div class="trap-clean-prompt">
      <span class="clean-check-icon">✓</span>
      <h4>No Cognitive Traps Found</h4>
      <p class="clean-desc">
        The student avoided known mental traps for this inquiry.
      </p>
      <button
        type="button"
        class="btn-rescan-ghost"
        onclick={onRunScan}
        disabled={isScanning}
      >
        ↻ Re-scan Submission
      </button>
    </div>
  {:else}
    {#if interventionNotice}
      <div class="intervention-toast-bar">
        <span>💡</span>
        <span>{interventionNotice}</span>
        <button type="button" class="btn-toast-dismiss" onclick={onDismissNotice}>✕</button>
      </div>
    {/if}

    <div class="traps-results-bar">
      <span class="traps-count-label">
        {(scan.findings || []).length} Cognitive {(scan.findings || []).length === 1 ? 'Trap' : 'Traps'} Evidenced
      </span>
      <button
        type="button"
        class="btn-rescan-mini"
        onclick={onRunScan}
        disabled={isScanning}
      >
        ↻ Re-scan
      </button>
    </div>

    <div class="traps-cards-flow">
      {#each scan.findings as finding}
        {@const matchedIntervention = activeInterventions.find((i) => i.misconception_id === finding.misconception_id)}
        <article class="trap-item-card">
          <header class="trap-item-header">
            <strong class="trap-item-name">{finding.name}</strong>
            <span
              class="trap-item-badge"
              class:weak={finding.detection !== 'llm_verified'}
            >
              {finding.detection === 'llm_verified' ? 'Evidenced' : 'Candidate'}
            </span>
          </header>

          <p class="trap-flawed-rule">{finding.flawed_rule}</p>

          {#if finding.evidence_quote}
            <div class="trap-quote-box">
              <span class="quote-eyebrow">Student Quote:</span>
              <blockquote class="trap-quote-text">
                "{finding.evidence_quote}"
              </blockquote>
            </div>
            <p class="trap-why-text">{finding.why}</p>
          {/if}

          {#if finding.remediation_hint}
            <div class="trap-remediation-line">
              <span class="remed-label">Remediate:</span>
              <span>{finding.remediation_hint}</span>
            </div>
          {/if}

          {#if matchedIntervention}
            <div class="intervention-status-box" class:is-responded={matchedIntervention.status === 'responded'} class:is-ack={matchedIntervention.status === 'acknowledged'}>
              <div class="intervention-status-header">
                <span class="status-indicator">
                  {#if matchedIntervention.status === 'acknowledged'}
                    ✓ Intervention Acknowledged
                  {:else if matchedIntervention.status === 'responded'}
                    🟢 Student Reflection Received
                  {:else}
                    🟡 Challenge Dispatched to Student
                  {/if}
                </span>
                {#if matchedIntervention.status === 'responded'}
                  <button
                    type="button"
                    class="btn-ack-intervention"
                    onclick={() => onAcknowledgeIntervention(matchedIntervention.intervention_id)}
                  >
                    Mark Acknowledged ✓
                  </button>
                {/if}
              </div>
              {#if matchedIntervention.student_response}
                <blockquote class="student-reflection-echo">
                  "{matchedIntervention.student_response}"
                </blockquote>
              {:else}
                <p class="status-sub">Awaiting student reflection in their marginalia gutter.</p>
              {/if}
            </div>
          {/if}

          <div class="trap-card-actions">
            <button
              type="button"
              class="btn-dispatch-challenge"
              class:active={challengeDraftOpenFor === finding.misconception_id}
              onclick={() => openChallengeDraft(finding)}
            >
              ⚡ {matchedIntervention ? 'Edit / Re-dispatch' : 'Dispatch Activity'}
            </button>
            <button
              type="button"
              class="btn-draft-note"
              onclick={() => openDraft(finding)}
            >
              ✉ Mail
            </button>
            {#if finding.concept_id}
              <a
                class="trap-concept-link"
                href={`/#/knowledge-graph?course_id=${courseId}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Graph ↗
              </a>
            {/if}
          </div>

          {#if challengeDraftOpenFor === finding.misconception_id}
            <div class="inline-challenge-dispatch">
              <label class="draft-field-label" for={`challenge-${finding.misconception_id}`}>
                AI-Crafted Socratic Activity / Challenge (Editable)
              </label>
              <textarea
                id={`challenge-${finding.misconception_id}`}
                class="draft-body-input"
                rows="3"
                bind:value={challengeDraftPrompt}
              ></textarea>
              {#if finding.activity_guidance || finding.remediation_hint}
                <div class="challenge-guidance-preview">
                  <span class="guidance-label">Reading / Remediation Hint:</span>
                  <span>{finding.activity_guidance || finding.remediation_hint}</span>
                </div>
              {/if}
              <div class="draft-action-btns">
                <button
                  type="button"
                  class="btn-send-challenge"
                  disabled={isDispatching}
                  onclick={() => handleDispatch(finding)}
                >
                  {isDispatching ? 'Dispatching...' : 'Send Activity to Student'}
                </button>
                <button
                  type="button"
                  class="btn-close"
                  onclick={() => (challengeDraftOpenFor = '')}
                >
                  Cancel
                </button>
              </div>
            </div>
          {/if}

          {#if draftOpenFor === finding.misconception_id}
            <div class="inline-socratic-draft">
              <label class="draft-field-label" for="draft-subject">Subject</label>
              <input
                id="draft-subject"
                class="draft-subject-input"
                bind:value={draftSubject}
              />
              <label class="draft-field-label" for="draft-body">Socratic Guidance</label>
              <textarea
                id="draft-body"
                class="draft-body-input"
                rows="6"
                bind:value={draftBody}
              ></textarea>
              <div class="draft-action-btns">
                <button
                  type="button"
                  class="btn-mail"
                  onclick={openInMailClient}
                >Open in Mail</button>
                <button
                  type="button"
                  class="btn-copy"
                  onclick={copyDraft}
                >Copy</button>
                <button
                  type="button"
                  class="btn-close"
                  onclick={() => (draftOpenFor = '')}
                >Close</button>
              </div>
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}

  {#if scanError}
    <p class="trap-scan-error">{scanError}</p>
  {/if}
</div>

<style>
  .traps-inspector {
    display: flex;
    flex-direction: column;
  }

  .trap-scan-prompt,
  .trap-clean-prompt {
    text-align: center;
    padding: 24px 14px;
    background: #fafaf8;
    border: 1px dashed var(--color-graphite-border, #cbd5e1);
    border-radius: var(--radius-md, 8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }

  .trap-scan-icon {
    font-size: 28px;
  }
  .clean-check-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #ecfdf5;
    color: #059669;
    font-size: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  .trap-scan-prompt h4,
  .trap-clean-prompt h4 {
    margin: 0;
    font-size: 13.5px;
    color: var(--color-heading, #0f172a);
  }

  .trap-scan-desc,
  .clean-desc {
    font-size: 11.5px;
    color: var(--color-slate-light, #475569);
    margin: 0;
    line-height: 1.45;
  }

  .btn-trigger-scan {
    padding: 7px 14px;
    font-size: 11.5px;
    font-weight: 700;
    color: #ffffff;
    background: #0b4a4f;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 4px;
  }

  .btn-trigger-scan:disabled {
    opacity: 0.55;
    cursor: default;
  }

  .scan-running-note {
    font-size: 10.5px;
    color: var(--color-slate-muted, #64748b);
    margin: 2px 0 0;
  }

  .btn-rescan-ghost {
    padding: 4px 10px;
    font-size: 10.5px;
    font-weight: 600;
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-light, #475569);
    margin-top: 4px;
  }

  .traps-results-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--color-graphite-border, #cbd5e1);
    margin-bottom: 10px;
  }

  .traps-count-label {
    font-size: 11px;
    font-weight: 700;
    color: #b45309;
  }

  .btn-rescan-mini {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 4px;
    font-size: 10px;
    padding: 2px 6px;
    cursor: pointer;
    color: var(--color-slate-muted, #64748b);
  }

  .traps-cards-flow {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .trap-item-card {
    border: 1px solid rgba(216, 154, 58, 0.4);
    border-left: 3px solid #d97706;
    border-radius: 4px;
    padding: 10px 12px;
    background: #fffdfa;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .trap-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
  }

  .trap-item-name {
    font-size: 12.5px;
    color: #92400e;
  }

  .trap-item-badge {
    font-size: 9px;
    text-transform: uppercase;
    padding: 1px 6px;
    border-radius: 999px;
    background: rgba(216, 154, 58, 0.18);
    color: #8c6212;
    font-weight: 700;
  }

  .trap-item-badge.weak {
    background: rgba(148, 163, 184, 0.2);
    color: #64748b;
  }

  .trap-flawed-rule {
    margin: 0;
    font-size: 11.5px;
    line-height: 1.4;
    color: var(--color-heading, #0f172a);
  }

  .trap-quote-box {
    background: rgba(216, 154, 58, 0.08);
    border-left: 2px solid #d97706;
    padding: 5px 8px;
    border-radius: 0 4px 4px 0;
  }

  .quote-eyebrow {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #b45309;
    display: block;
    margin-bottom: 2px;
  }

  .trap-quote-text {
    margin: 0;
    font-size: 11.5px;
    font-style: italic;
    color: #1e293b;
    line-height: 1.4;
  }

  .trap-why-text {
    margin: 0;
    font-size: 11px;
    color: var(--color-slate-light, #475569);
    line-height: 1.4;
  }

  .trap-remediation-line {
    font-size: 11px;
    color: var(--color-slate-light, #475569);
  }

  .remed-label {
    font-weight: 700;
    color: #0b4a4f;
    font-size: 9px;
    text-transform: uppercase;
  }

  .trap-card-actions {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-top: 4px;
  }

  .btn-draft-note {
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #0b4a4f;
    background: #0b4a4f;
    color: #fff;
    cursor: pointer;
  }

  .trap-concept-link {
    font-size: 10.5px;
    color: #0b4a4f;
    text-decoration: none;
    border-bottom: 1px solid currentColor;
  }

  .inline-socratic-draft {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed rgba(148, 163, 184, 0.45);
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .draft-field-label {
    font-size: 9px;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--color-slate-muted, #64748b);
  }

  .draft-subject-input,
  .draft-body-input {
    width: 100%;
    font: inherit;
    font-size: 11.5px;
    line-height: 1.4;
    padding: 5px 7px;
    border-radius: 4px;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    background: #ffffff;
    box-sizing: border-box;
  }

  .draft-action-btns {
    display: flex;
    gap: 4px;
    margin-top: 4px;
  }

  .btn-mail {
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 8px;
    background: #0b4a4f;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-copy,
  .btn-close {
    font-size: 10.5px;
    padding: 4px 8px;
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-light, #475569);
  }

  .btn-dispatch-challenge {
    font-size: 10.5px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #b45309;
    background: #fef3c7;
    color: #92400e;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-dispatch-challenge {
    background: rgba(217, 119, 6, 0.2);
    color: #fbbf24;
    border-color: #d97706;
  }

  .btn-dispatch-challenge:hover,
  .btn-dispatch-challenge.active {
    background: #b45309;
    color: #ffffff;
  }

  .btn-send-challenge {
    font-size: 10.5px;
    font-weight: 700;
    padding: 4px 10px;
    background: #b45309;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-send-challenge:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .inline-challenge-dispatch {
    margin-top: 8px;
    padding: 8px;
    background: rgba(245, 158, 11, 0.05);
    border: 1px solid #fde68a;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  :global([data-theme="dark"]) .inline-challenge-dispatch {
    background: rgba(245, 158, 11, 0.08);
    border-color: rgba(245, 158, 11, 0.25);
  }

  .challenge-guidance-preview {
    font-size: 10.5px;
    color: var(--color-slate-light, #475569);
    line-height: 1.35;
    padding: 4px 6px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 4px;
  }

  :global([data-theme="dark"]) .challenge-guidance-preview {
    background: rgba(0, 0, 0, 0.2);
  }

  .guidance-label {
    font-weight: 700;
    color: #b45309;
    margin-right: 4px;
  }

  .intervention-status-box {
    margin: 8px 0;
    padding: 8px 10px;
    border-radius: 6px;
    background: #fefce8;
    border: 1px solid #fef08a;
    font-size: 11px;
  }

  :global([data-theme="dark"]) .intervention-status-box {
    background: rgba(234, 179, 8, 0.08);
    border-color: rgba(234, 179, 8, 0.25);
  }

  .intervention-status-box.is-responded {
    background: #f0fdf4;
    border-color: #bbf7d0;
  }

  :global([data-theme="dark"]) .intervention-status-box.is-responded {
    background: rgba(34, 197, 94, 0.08);
    border-color: rgba(34, 197, 94, 0.25);
  }

  .intervention-status-box.is-ack {
    background: #f8fafc;
    border-color: var(--color-graphite-border, #cbd5e1);
  }

  :global([data-theme="dark"]) .intervention-status-box.is-ack {
    background: rgba(255, 255, 255, 0.03);
  }

  .intervention-status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
  }

  .status-indicator {
    font-weight: 700;
    font-size: 11px;
  }

  .status-sub {
    margin: 4px 0 0 0;
    font-size: 10.5px;
    color: var(--color-slate-light, #475569);
    font-style: italic;
  }

  .student-reflection-echo {
    margin: 6px 0 0 0;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.03);
    border-left: 2.5px solid #10b981;
    font-size: 11px;
    font-style: italic;
    color: var(--color-heading, #0f172a);
    border-radius: 0 4px 4px 0;
  }

  :global([data-theme="dark"]) .student-reflection-echo {
    background: rgba(255, 255, 255, 0.03);
  }

  .btn-ack-intervention {
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 7px;
    background: #059669;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    cursor: pointer;
  }

  .btn-ack-intervention:hover {
    background: #047857;
  }

  .intervention-toast-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 10px;
    background: #fef3c7;
    border: 1px solid #fde68a;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: #92400e;
    margin-bottom: 8px;
  }

  :global([data-theme="dark"]) .intervention-toast-bar {
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.3);
    color: #fbbf24;
  }

  .btn-toast-dismiss {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 11px;
    color: inherit;
    padding: 0 4px;
  }

  .trap-scan-error {
    font-size: 11.5px;
    color: #b91c1c;
    margin-top: 8px;
  }
</style>
