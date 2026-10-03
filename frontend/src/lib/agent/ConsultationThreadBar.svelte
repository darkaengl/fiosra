<script lang="ts">
  let {
    chatSessions = [],
    activeChatSessionId = '',
    activeSessionTitle = 'Consultation',
    turnsCount = 0,
    onSwitchChatSession = () => {},
    onNewChatSession = () => {},
  } = $props<{
    chatSessions?: any[];
    activeChatSessionId?: string;
    activeSessionTitle?: string;
    turnsCount?: number;
    onSwitchChatSession?: (id: string) => void;
    onNewChatSession?: () => void;
  }>();

  let isThreadMenuOpen = $state(false);
</script>

<div class="consultation-thread-bar">
  <div class="thread-dropdown-wrapper">
    <button
      type="button"
      id="consultation-thread-btn"
      class="btn-thread-select"
      class:is-active={isThreadMenuOpen}
      onclick={() => (isThreadMenuOpen = !isThreadMenuOpen)}
      title="Switch Socratic consultation thread"
      aria-expanded={isThreadMenuOpen}
    >
      <span class="thread-icon" aria-hidden="true">💬</span>
      <span class="thread-title">{activeSessionTitle}</span>
      <span class="thread-turn-count">({Math.floor(turnsCount / 2)} {Math.floor(turnsCount / 2) === 1 ? 'turn' : 'turns'})</span>
      <span class="thread-chevron" aria-hidden="true">{isThreadMenuOpen ? '▴' : '▾'}</span>
    </button>

    {#if isThreadMenuOpen}
      <button
        type="button"
        class="thread-dropdown-backdrop"
        onclick={() => (isThreadMenuOpen = false)}
        aria-label="Close consultation thread menu"
      ></button>
      <div class="thread-dropdown-menu" role="menu">
        <div class="thread-menu-header">Consultation Threads</div>
        <div class="thread-menu-list">
          {#each chatSessions as cs (cs.id)}
            <button
              type="button"
              class="thread-menu-item"
              class:selected={cs.id === activeChatSessionId}
              onclick={() => {
                onSwitchChatSession(cs.id);
                isThreadMenuOpen = false;
              }}
              role="menuitem"
            >
              <div class="thread-item-title">{cs.title}</div>
              <div class="thread-item-meta">
                {Math.floor(cs.turns?.length / 2 || 0)} exchanges · {new Date(cs.startedAt || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </button>
          {/each}
        </div>
        <div class="thread-menu-footer">
          <button
            type="button"
            id="new-consultation-btn"
            class="btn-new-consultation"
            onclick={() => {
              onNewChatSession();
              isThreadMenuOpen = false;
            }}
          >
            <span class="plus-icon">＋</span>
            <span>New Consultation</span>
          </button>
        </div>
      </div>
    {/if}
  </div>

  <button
    type="button"
    id="quick-new-thread-btn"
    class="btn-quick-new-thread"
    onclick={onNewChatSession}
    title="Start a new consultation thread"
  >
    <span>＋ New Chat</span>
  </button>
</div>

<style>
  .consultation-thread-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 12px;
    background: var(--color-obsidian, #f8f8f5);
    border-bottom: 1px solid var(--color-graphite-border, #e2e4dc);
    flex-shrink: 0;
    gap: 8px;
    position: relative;
    z-index: 15;
  }

  :global([data-theme="dark"]) .consultation-thread-bar {
    background: var(--color-surface-subtle, #181b20);
    border-color: var(--color-graphite-border, #2a2e36);
  }

  .thread-dropdown-wrapper {
    position: relative;
    min-width: 0;
  }

  .btn-thread-select {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 6px;
    padding: 4px 9px;
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--color-heading, #121418);
    cursor: pointer;
    transition: all 0.15s ease;
    max-width: 200px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  }

  :global([data-theme="dark"]) .btn-thread-select {
    background: #1e2229;
    color: var(--color-heading, #f0f2f5);
    border-color: #2a2e36;
  }

  .btn-thread-select:hover,
  .btn-thread-select.is-active {
    border-color: var(--color-aurora, #0284c7);
    background: var(--color-graphite-hover, #f1f2ed);
  }

  .thread-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 90px;
  }

  .thread-turn-count {
    font-size: 0.68rem;
    font-weight: 500;
    color: var(--color-slate-muted, #717784);
  }

  .thread-chevron {
    font-size: 0.65rem;
    color: var(--color-slate-muted, #717784);
  }

  .thread-dropdown-backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: transparent;
    border: none;
    cursor: default;
  }

  .thread-dropdown-menu {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    z-index: 50;
    width: 260px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 8px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    overflow: hidden;
    animation: fadeIn 0.12s ease-out;
  }

  :global([data-theme="dark"]) .thread-dropdown-menu {
    background: #1e2229;
    border-color: #2a2e36;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.5);
  }

  .thread-menu-header {
    padding: 8px 12px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-slate-muted, #717784);
    border-bottom: 1px solid var(--color-graphite-border, #e2e4dc);
    background: var(--color-obsidian, #f8f8f5);
  }

  :global([data-theme="dark"]) .thread-menu-header {
    background: #181b20;
    border-color: #2a2e36;
  }

  .thread-menu-list {
    max-height: 220px;
    overflow-y: auto;
  }

  .thread-menu-item {
    width: 100%;
    text-align: left;
    padding: 8px 12px;
    border: none;
    background: transparent;
    cursor: pointer;
    border-bottom: 1px solid var(--color-obsidian-subtle, #f0f0eb);
    transition: background 0.12s ease;
  }

  :global([data-theme="dark"]) .thread-menu-item {
    border-color: #262a33;
  }

  .thread-menu-item:hover {
    background: var(--color-graphite-hover, #f5f6f1);
  }

  :global([data-theme="dark"]) .thread-menu-item:hover {
    background: #252a33;
  }

  .thread-menu-item.selected {
    background: rgba(2, 132, 199, 0.08);
    border-left: 3px solid var(--color-aurora, #0284c7);
  }

  .thread-item-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--color-heading, #121418);
    margin-bottom: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global([data-theme="dark"]) .thread-item-title {
    color: #f0f2f5;
  }

  .thread-item-meta {
    font-size: 0.68rem;
    color: var(--color-slate-muted, #717784);
  }

  .thread-menu-footer {
    padding: 6px 8px;
    background: var(--color-obsidian, #f8f8f5);
    border-top: 1px solid var(--color-graphite-border, #e2e4dc);
  }

  :global([data-theme="dark"]) .thread-menu-footer {
    background: #181b20;
    border-color: #2a2e36;
  }

  .btn-new-consultation {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 6px;
    border: 1px dashed var(--color-graphite-border, #d1d5db);
    border-radius: 6px;
    background: var(--color-graphite, #ffffff);
    color: var(--color-aurora, #0284c7);
    font-size: 0.74rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-new-consultation {
    background: #1e2229;
    border-color: #3b4252;
  }

  .btn-new-consultation:hover {
    background: var(--color-graphite-hover, #f1f2ed);
    border-color: var(--color-aurora, #0284c7);
  }

  .btn-quick-new-thread {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: transparent;
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--color-aurora, #0284c7);
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .btn-quick-new-thread {
    border-color: #2a2e36;
  }

  .btn-quick-new-thread:hover {
    background: rgba(2, 132, 199, 0.08);
    border-color: var(--color-aurora, #0284c7);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
