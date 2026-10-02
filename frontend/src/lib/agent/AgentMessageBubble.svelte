<script lang="ts">
  let {
    turn,
    isBusy = false,
    onCommitCapsule = () => {},
    onSelectStarter = () => {},
  } = $props<{
    turn: any;
    isBusy?: boolean;
    onCommitCapsule?: (capsule: any) => void;
    onSelectStarter?: (prompt: string) => void;
  }>();
</script>

{#if turn.role === 'student'}
  <div class="msg-bubble-wrap student-wrap">
    <div class="msg-bubble student-msg">
      <div class="msg-content">{turn.text}</div>
    </div>
  </div>
{:else}
  <div class="msg-bubble-wrap tutor-wrap">
    <div class="msg-bubble tutor-msg" class:deflected={turn.is_adversarial}>
      <div class="tutor-header-row">
        <div class="tutor-badge">
          <div class="tutor-avatar">
            <img src="./fiosra-symbol.png" alt="" class="companion-badge-img" />
          </div>
          <span class="author-name">Thinking Companion</span>
          <span class="companion-grounded-tag">Grounded</span>
        </div>
        {#if turn.hint_rung > 0}
          <span class="hint-tag">💡 Level {turn.hint_rung} Inquiry</span>
        {/if}
      </div>

      <div class="msg-content">{turn.text}</div>

      <!-- Action Capsules: Quiet, student-owned transfer affordances -->
      {#if turn.action_capsules && turn.action_capsules.length > 0}
        {@const validCapsules = turn.action_capsules.filter((c: any) => Boolean((c.suggested_student_text || c.text_payload)?.trim()))}
        {#if validCapsules.length > 0}
          <div class="action-capsules-wrap">
            {#each validCapsules as capsule}
              <div class="action-capsule-slip">
                <div class="capsule-lead">
                  <span class="capsule-icon">✍️</span>
                  <span class="capsule-quote">“{capsule.suggested_student_text || capsule.text_payload}”</span>
                </div>
                <button
                  type="button"
                  class="btn-capsule-transfer"
                  onclick={() => onCommitCapsule(capsule)}
                  title="Transfer your formulated insight directly into the Canvas draft"
                >
                  {capsule.label || 'Transfer to Paragraph ↗'}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      {/if}

      <!-- Suggested Inquiries: Sleek interactive prompt chips -->
      {#if turn.prompt_launchers && turn.prompt_launchers.length > 0}
        <div class="discussion-starters-block in-thread">
          <div class="starters-eyebrow">
            <span>💡</span> Suggested Inquiries
          </div>
          <div class="starters-list">
            {#each turn.prompt_launchers as launcher}
              <button
                type="button"
                class="btn-scholastic-starter"
                onclick={() => onSelectStarter(launcher.prompt || launcher.title)}
                disabled={isBusy}
                title={launcher.prompt || launcher.title}
              >
                <span class="starter-label">{launcher.title || launcher.prompt}</span>
                <span class="starter-arrow">→</span>
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Learner Metacognitive Radar (rendered ONLY when concept data exists) -->
      {#if (turn.radar?.target_concept) || (turn.thoughts?.diagnosed_kc)}
        {@const concept = turn.radar?.target_concept || turn.thoughts?.diagnosed_kc}
        {@const stance = turn.radar?.epistemic_stance || turn.thoughts?.stance}
        <div class="scholastic-radar-rule">
          <span class="radar-dot"></span>
          <span class="radar-concept">{concept}</span>
          {#if stance}
            <span class="radar-sep">·</span>
            <span class="radar-stance">{stance}</span>
          {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .msg-bubble-wrap {
    display: flex;
    width: 100%;
  }

  .student-wrap {
    justify-content: flex-end;
  }

  .tutor-wrap {
    justify-content: flex-start;
  }

  .student-msg {
    max-width: 84%;
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
    color: #ffffff;
    padding: 9px 13px;
    border-radius: 16px 16px 4px 16px;
    box-shadow: 0 2px 6px rgba(2, 132, 199, 0.2);
  }

  .student-msg .msg-content {
    font-size: 0.85rem;
    line-height: 1.48;
    color: #ffffff;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .tutor-msg {
    max-width: 95%;
    width: 100%;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 14px;
    padding: 13px 15px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .tutor-msg {
    background: #1a1e26;
    border-color: #2a2f3a;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
  }

  .tutor-msg.deflected {
    border-color: rgba(217, 119, 6, 0.35);
    background: rgba(217, 119, 6, 0.04);
  }

  .tutor-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 9px;
  }

  .tutor-badge {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .tutor-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(2, 132, 199, 0.1);
    border: 1px solid rgba(2, 132, 199, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    flex-shrink: 0;
  }

  .companion-badge-img {
    height: 14px;
    width: auto;
    object-fit: contain;
  }

  .companion-grounded-tag {
    font-size: 8.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    background: var(--m-color-horizon-blue-soft, #EBF0FF);
    padding: 1px 5px;
    border-radius: 4px;
    margin-left: 2px;
  }

  :global([data-theme="dark"]) .companion-grounded-tag {
    background: rgba(79, 107, 255, 0.2);
    color: #93c8ff;
  }

  .author-name {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--color-heading, #111827);
  }

  :global([data-theme="dark"]) .author-name {
    color: #f1f5f9;
  }

  .hint-tag {
    font-size: 0.68rem;
    font-weight: 600;
    background: rgba(217, 119, 6, 0.12);
    color: #b45309;
    border: 1px solid rgba(217, 119, 6, 0.25);
    padding: 1px 7px;
    border-radius: 12px;
  }

  :global([data-theme="dark"]) .hint-tag {
    color: #f59e0b;
    border-color: rgba(245, 158, 11, 0.3);
  }

  .tutor-msg .msg-content {
    font-size: 0.86rem;
    line-height: 1.58;
    color: var(--color-heading, #1f2937);
    white-space: pre-wrap;
    word-break: break-word;
  }

  :global([data-theme="dark"]) .tutor-msg .msg-content {
    color: #e2e8f0;
  }

  /* Action Capsules */
  .action-capsules-wrap {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  .action-capsule-slip {
    background: var(--color-graphite-card, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-left: 3px solid var(--color-teal, #0d9488);
    border-radius: 8px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  :global([data-theme="dark"]) .action-capsule-slip {
    background: rgba(30, 41, 59, 0.6);
    border-color: rgba(148, 163, 184, 0.15);
    border-left-color: var(--color-teal, #2dd4bf);
  }

  .capsule-lead {
    display: flex;
    align-items: flex-start;
    gap: 6px;
  }

  .capsule-icon {
    font-size: 0.8rem;
    flex-shrink: 0;
  }

  .capsule-quote {
    font-size: 0.77rem;
    font-style: italic;
    color: var(--color-slate-light, #475569);
    line-height: 1.38;
  }

  :global([data-theme="dark"]) .capsule-quote {
    color: #cbd5e1;
  }

  .btn-capsule-transfer {
    align-self: flex-end;
    background: var(--color-teal, #0d9488);
    border: none;
    border-radius: 5px;
    padding: 3px 9px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #ffffff;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .btn-capsule-transfer:hover {
    background: #0f766e;
  }

  /* Discussion Starters / Suggested Inquiries */
  .discussion-starters-block {
    margin-top: 13px;
    padding-top: 11px;
    border-top: 1px solid var(--color-graphite-border, #f0f0ea);
  }

  :global([data-theme="dark"]) .discussion-starters-block {
    border-top-color: #2a2f3a;
  }

  .starters-eyebrow {
    font-size: 0.71rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-subtle, #64748b);
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 8px;
  }

  .starters-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .btn-scholastic-starter {
    background: rgba(2, 132, 199, 0.04);
    border: 1px solid rgba(2, 132, 199, 0.18);
    border-radius: 8px;
    padding: 8px 12px;
    text-align: left;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    width: 100%;
    box-sizing: border-box;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-scholastic-starter {
    background: rgba(2, 132, 199, 0.08);
    border-color: rgba(56, 189, 248, 0.2);
  }

  .btn-scholastic-starter:hover:not(:disabled) {
    background: rgba(2, 132, 199, 0.1);
    border-color: var(--color-aurora, #0284c7);
    transform: translateY(-1px);
  }

  .starter-label {
    font-size: 0.8rem;
    font-weight: 500;
    line-height: 1.4;
    color: var(--color-heading, #1f2937);
  }

  :global([data-theme="dark"]) .starter-label {
    color: #e2e8f0;
  }

  .starter-arrow {
    color: var(--color-aurora, #0284c7);
    font-weight: 700;
    flex-shrink: 0;
  }

  /* Metacognitive Radar Rule */
  .scholastic-radar-rule {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px dashed var(--color-graphite-border, #e2e8f0);
    font-size: 0.68rem;
    color: var(--color-slate-muted, #64748b);
  }

  :global([data-theme="dark"]) .scholastic-radar-rule {
    border-top-color: #262a33;
  }

  .radar-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #0284c7;
  }

  .radar-concept {
    font-weight: 600;
    color: var(--color-slate-light, #475569);
  }

  :global([data-theme="dark"]) .radar-concept {
    color: #94a3b8;
  }

  .radar-sep {
    color: var(--color-graphite-border, #cbd5e1);
  }

  .radar-stance {
    font-style: italic;
  }
</style>
