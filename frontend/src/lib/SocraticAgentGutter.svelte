<script lang="ts">
  import ConsultationThreadBar from './agent/ConsultationThreadBar.svelte';
  import AgentMessageBubble from './agent/AgentMessageBubble.svelte';
  import AgentInputArea from './agent/AgentInputArea.svelte';

  let {
    sessionId = '',
    assignment = null,
    currentRung = 0,
    turns = [],
    chatSessions = [],
    activeChatSessionId = '',
    onNewChatSession = () => null,
    onSwitchChatSession = () => null,
    focusedBlockId = '',
    focusedBlockTitle = '',
    openExhibitTitle = '',
    onSendMessage = async () => null,
    onRequestHint = async () => null,
    onCommitCapsule = async () => null,
    isBusy = false,
  } = $props<{
    sessionId?: string;
    assignment?: any;
    currentRung?: number;
    turns?: any[];
    chatSessions?: any[];
    activeChatSessionId?: string;
    onNewChatSession?: () => void;
    onSwitchChatSession?: (id: string) => void;
    focusedBlockId?: string;
    focusedBlockTitle?: string;
    openExhibitTitle?: string;
    onSendMessage?: (msg: string, isInitial?: boolean) => Promise<any> | any;
    onRequestHint?: () => Promise<any> | any;
    onCommitCapsule?: (capsule: any) => Promise<any> | any;
    isBusy?: boolean;
  }>();

  let inputMessage = $state('');
  let messagesContainer = $state<HTMLDivElement | null>(null);
  let inputAreaRef = $state<any>(null);

  let activeSessionTitle = $derived.by(() => {
    const found = chatSessions.find((cs: any) => cs.id === activeChatSessionId);
    return found ? found.title : 'Consultation';
  });

  async function handleSend(msg: string) {
    if (!msg.trim() || isBusy) return;
    scrollToBottom();
    await onSendMessage(msg, false);
    scrollToBottom();
  }

  async function handleHint() {
    if (isBusy) return;
    await onRequestHint();
    scrollToBottom();
  }

  function handleSelectStarter(prompt: string) {
    if (isBusy) return;
    inputMessage = prompt;
    inputAreaRef?.focusTextarea();
  }

  function scrollToBottom() {
    setTimeout(() => {
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 60);
  }

  $effect(() => {
    if (turns.length > 0 || isBusy) {
      scrollToBottom();
    }
  });
</script>

<div class="socratic-agent-panel" aria-label="Socratic Copilot Agent">
  <!-- Socratic Consultation Thread Bar -->
  <ConsultationThreadBar
    {chatSessions}
    {activeChatSessionId}
    {activeSessionTitle}
    turnsCount={turns.length}
    {onSwitchChatSession}
    {onNewChatSession}
  />

  <!-- Subtle Scholastic Co-Presence Rule -->
  <div class="scholastic-copresence-strip">
    <div class="copresence-node focus-node">
      <span class="copresence-dot">●</span>
      <span class="copresence-label">Focus:</span>
      <span class="copresence-value" title={focusedBlockTitle || ''}>
        {focusedBlockTitle || (focusedBlockId ? `Paragraph (${focusedBlockId.slice(0, 6)})` : 'Canvas Drafting')}
      </span>
    </div>
    {#if openExhibitTitle}
      <span class="copresence-divider">·</span>
      <div class="copresence-node exhibit-node">
        <span class="copresence-icon">📕</span>
        <span class="copresence-value" title={openExhibitTitle}>{openExhibitTitle}</span>
      </div>
    {/if}
  </div>

  <!-- Messages Scroll Area -->
  <div class="agent-messages" bind:this={messagesContainer}>
    {#if turns.length === 0}
      <div class="agent-scholastic-empty">
        <div class="empty-scholastic-header">
          <div class="empty-avatar">
            <img src="./fiosra-symbol.png" alt="Fiosra" class="companion-symbol-img" />
          </div>
          <h4 class="empty-title">Thinking Companion</h4>
          <p class="empty-desc">
            Grounded in your writing. Explore uncertainty, test competing assumptions, and formulate defensible positions with your dialectic tutor.
          </p>
        </div>
      </div>
    {:else}
      {#each turns as turn}
        <AgentMessageBubble
          {turn}
          {isBusy}
          {onCommitCapsule}
          onSelectStarter={handleSelectStarter}
        />
      {/each}
    {/if}

    {#if isBusy}
      <div class="msg-bubble-wrap tutor-wrap">
        <div class="tutor-typing-indicator">
          <span class="tutor-avatar-mini">🏛️</span>
          <span>Thinking with you...</span>
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Action & Input Footer -->
  <AgentInputArea
    bind:this={inputAreaRef}
    bind:inputMessage
    {isBusy}
    {currentRung}
    onSendMessage={handleSend}
    onRequestHint={handleHint}
  />
</div>

<style>
  .socratic-agent-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    width: 100%;
    background: transparent;
    overflow: hidden;
  }

  /* Scholastic Co-Presence Strip */
  .scholastic-copresence-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(0, 0, 0, 0.02);
    border-bottom: 1px solid var(--color-graphite-border, #e2e4dc);
    font-size: 0.7rem;
    color: var(--color-slate-subtle, #64748b);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .scholastic-copresence-strip {
    background: rgba(255, 255, 255, 0.02);
    border-color: var(--color-graphite-border, #2a2e36);
  }

  .copresence-node {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .copresence-dot {
    color: var(--color-aurora, #0284c7);
    font-size: 0.6rem;
  }

  .copresence-label {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    font-size: 0.64rem;
    color: var(--color-slate-muted, #94a3b8);
  }

  .copresence-value {
    color: var(--color-heading, #1e293b);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :global([data-theme="dark"]) .copresence-value {
    color: #e2e8f0;
  }

  .copresence-divider {
    color: var(--color-slate-subtle, #94a3b8);
  }

  .copresence-icon {
    font-size: 0.74rem;
  }

  /* Messages Scroll Area */
  .agent-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px 14px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
  }

  /* Scholastic Empty State */
  .agent-scholastic-empty {
    margin: auto 0;
    padding: 24px 16px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .empty-scholastic-header {
    max-width: 280px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .empty-avatar {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .empty-avatar {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .companion-symbol-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
  }

  .empty-title {
    margin: 0 0 6px 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--color-heading, #1e293b);
  }

  :global([data-theme="dark"]) .empty-title {
    color: #f1f5f9;
  }

  .empty-desc {
    margin: 0;
    font-size: 0.78rem;
    line-height: 1.5;
    color: var(--color-slate-subtle, #64748b);
  }

  :global([data-theme="dark"]) .empty-desc {
    color: #94a3b8;
  }

  .msg-bubble-wrap {
    display: flex;
    width: 100%;
  }

  .tutor-wrap {
    justify-content: flex-start;
  }

  /* Typing Indicator */
  .tutor-typing-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.76rem;
    color: var(--color-slate-subtle, #64748b);
    font-style: italic;
    padding: 6px 12px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .tutor-typing-indicator {
    background: #1a1e26;
    border-color: #2a2f3a;
  }

  .tutor-avatar-mini {
    font-size: 13px;
  }

  .typing-dots span {
    display: inline-block;
    width: 4px;
    height: 4px;
    background: var(--color-aurora, #0284c7);
    border-radius: 50%;
    margin-right: 2px;
    animation: typing 1.4s infinite ease-in-out both;
  }

  .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
  .typing-dots span:nth-child(2) { animation-delay: -0.16s; }

  @keyframes typing {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
</style>
