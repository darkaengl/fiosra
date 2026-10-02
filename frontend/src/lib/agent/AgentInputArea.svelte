<script lang="ts">
  let {
    inputMessage = $bindable(''),
    isBusy = false,
    currentRung = 0,
    onSendMessage = async () => {},
    onRequestHint = async () => {},
  } = $props<{
    inputMessage?: string;
    isBusy?: boolean;
    currentRung?: number;
    onSendMessage?: (msg: string) => Promise<void> | void;
    onRequestHint?: () => Promise<void> | void;
  }>();

  let textareaEl = $state<HTMLTextAreaElement | null>(null);

  export function focusTextarea() {
    textareaEl?.focus();
  }

  async function handleSend(e?: Event) {
    e?.preventDefault();
    if (!inputMessage.trim() || isBusy) return;
    const msg = inputMessage.trim();
    inputMessage = '';
    await onSendMessage(msg);
  }

  async function handleHint() {
    if (isBusy) return;
    await onRequestHint();
  }
</script>

<div class="agent-footer">
  <div class="hints-row">
    <button
      type="button"
      class="btn-hint"
      onclick={handleHint}
      disabled={isBusy || currentRung >= 3}
      title="Advance the Socratic scaffolding ladder"
    >
      <span class="hint-icon">💡</span>
      <span>Request Socratic Hint</span>
      <span class="hint-pill-sub">{currentRung < 3 ? `(Rung ${currentRung + 1})` : '(Max)'}</span>
    </button>
  </div>

  <form class="agent-input-dock" onsubmit={handleSend}>
    <textarea
      bind:this={textareaEl}
      bind:value={inputMessage}
      placeholder="Discuss your thesis, test a premise, or explore evidence..."
      rows="1"
      disabled={isBusy}
      onkeydown={(e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      }}
    ></textarea>
    <button
      type="submit"
      class="btn-send"
      disabled={isBusy || !inputMessage.trim()}
      aria-label="Send message"
      title="Send message"
    >
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    </button>
  </form>
</div>

<style>
  .agent-footer {
    padding: 10px 14px 14px 14px;
    background: var(--color-obsidian, #f8f8f5);
    border-top: 1px solid var(--color-graphite-border, #e2e4dc);
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .agent-footer {
    background: var(--color-surface-subtle, #181b20);
    border-color: var(--color-graphite-border, #2a2e36);
  }

  .hints-row {
    display: flex;
    justify-content: flex-start;
  }

  .btn-hint {
    background: rgba(217, 119, 6, 0.08);
    border: 1px solid rgba(217, 119, 6, 0.28);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.73rem;
    font-weight: 600;
    color: #b45309;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-hint {
    background: rgba(217, 119, 6, 0.15);
    border-color: rgba(245, 158, 11, 0.3);
    color: #f59e0b;
  }

  .btn-hint:hover:not(:disabled) {
    background: rgba(217, 119, 6, 0.16);
    border-color: #d97706;
  }

  .btn-hint:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .hint-pill-sub {
    font-size: 0.68rem;
    opacity: 0.85;
  }

  .agent-input-dock {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 12px;
    padding: 6px 8px 6px 12px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    transition: all 0.18s ease;
  }

  :global([data-theme="dark"]) .agent-input-dock {
    background: #1e2229;
    border-color: #2a2f38;
  }

  .agent-input-dock:focus-within {
    border-color: var(--color-aurora, #0284c7);
    box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.12);
  }

  .agent-input-dock textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-size: 0.84rem;
    font-family: var(--font-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
    color: var(--color-heading, #111827);
    resize: none;
    min-height: 22px;
    max-height: 120px;
    line-height: 1.45;
    padding: 2px 0;
  }

  :global([data-theme="dark"]) .agent-input-dock textarea {
    color: #f1f5f9;
  }

  .btn-send {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--color-aurora, #0284c7);
    color: #ffffff;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s ease;
  }

  .btn-send:hover:not(:disabled) {
    background: #0369a1;
    transform: scale(1.04);
  }

  .btn-send:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    transform: none;
  }
</style>
