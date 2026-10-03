<script>
  let {
    currentDraft = null,
    activeCopilotModuleIndex = -1,
    currentCopilotModule = null,
    latestChangeSummary = '',
    showCritiqueChips = true,
    quickPrompts = [],
    isRevising = false,
    revisionHistory = [],
    reviewComment = $bindable(''),
    copilotCollapsed = $bindable(false),
    onResetContext = () => {},
    onToggleCritiqueChips = () => {},
    onApplyRevision = () => {},
  } = $props();
</script>

<aside class="copilot-sidebar">
  <div class="copilot-header">
    <div class="copilot-title">
      <span class="bot-icon">✦</span>
      <div>
        <h3>Teacher Co-Pilot</h3>
        <span class="bot-sub">Discuss, review, then apply curriculum changes</span>
      </div>
    </div>
    <button
      type="button"
      class="copilot-collapse"
      onclick={() => (copilotCollapsed = !copilotCollapsed)}
      title={copilotCollapsed ? 'Expand co-pilot' : 'Collapse co-pilot'}
    >
      {copilotCollapsed ? '→' : '←'}
    </button>
  </div>

  {#if !copilotCollapsed}
    <div class="copilot-context">
      <div class="context-copy">
        <span class="context-label">Current design context</span>
        <strong>{currentCopilotModule ? `Unit ${currentCopilotModule.position}: ${currentCopilotModule.title}` : 'Whole-course architecture'}</strong>
        <small>{currentCopilotModule ? `${currentCopilotModule.learning_objectives?.length || 0} objectives · ${currentCopilotModule.knowledge_components?.length || 0} concept markers` : `${currentDraft?.modules?.length || 0} modules available for revision`}</small>
      </div>
      {#if currentCopilotModule}
        <button type="button" class="context-reset" onclick={onResetContext}>Use whole course</button>
      {/if}
    </div>

    {#if latestChangeSummary}
      <div class="ai-diff-banner">
        <div class="diff-title">Latest applied change</div>
        <p>{latestChangeSummary}</p>
      </div>
    {/if}

    <div class="critique-section">
      <div class="critique-header">
        <span>Suggested next moves</span>
        <button type="button" class="toggle-btn" onclick={onToggleCritiqueChips}>
          {showCritiqueChips ? 'Hide' : 'Show'}
        </button>
      </div>
      {#if showCritiqueChips}
        <div class="prompt-chips">
          {#each quickPrompts as prompt}
            <button
              type="button"
              class="prompt-chip"
              disabled={isRevising}
              onclick={() => onApplyRevision(prompt)}
            >
              {prompt}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <div class="chat-stream" aria-label="Curriculum co-pilot conversation">
      {#if revisionHistory.length === 0}
        <div class="chat-empty">
          <strong>Start a design conversation.</strong>
          <span>Ask for a revision, select a unit for focused help, or use a suggested next move.</span>
        </div>
      {:else}
        {#each revisionHistory as turn}
          <div class="chat-msg chat-{turn.role}">
            <div class="msg-header">{turn.role === 'user' ? 'Your direction' : 'Co-pilot proposal'}</div>
            <div class="msg-text">{turn.content}</div>
          </div>
        {/each}
      {/if}
    </div>

    <div class="copilot-input-bar">
      <textarea
        class="chat-input"
        rows="3"
        placeholder={currentCopilotModule ? `Ask about Unit ${currentCopilotModule.position}: objectives, concepts, evidence, or sequence…` : 'Ask AI to refine the course sequence, clarify concepts, add evidence, or restructure units…'}
        bind:value={reviewComment}
        disabled={isRevising}
        onkeydown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onApplyRevision();
          }
        }}
      ></textarea>
      <div class="composer-footer">
        <span>Enter to send · Shift+Enter for a new line</span>
        <button
          type="button"
          class="btn-send-revision"
          disabled={isRevising || !reviewComment.trim()}
          onclick={() => onApplyRevision()}
        >
          {isRevising ? 'Refining…' : 'Propose revision'}
        </button>
      </div>
    </div>
  {/if}
</aside>

<style>
  .copilot-sidebar {
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-md, 8px);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    position: sticky;
    top: 16px;
    max-height: calc(100vh - 100px);
    min-height: 560px;
    overflow: hidden;
  }

  .copilot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-graphite-border, #e2e8f0);
    gap: 8px;
    flex-shrink: 0;
  }

  .copilot-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bot-icon {
    align-items: center;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    border-radius: 9px;
    color: white;
    display: inline-flex;
    font-size: 17px;
    height: 30px;
    justify-content: center;
    width: 30px;
  }

  .copilot-title h3 {
    font-size: 13.5px;
    font-weight: 700;
    margin: 0;
    color: var(--color-heading, #0f172a);
  }

  .bot-sub {
    font-size: 10.5px;
    color: var(--color-slate-muted, #64748b);
  }

  .copilot-collapse {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-xs, 4px);
    color: var(--color-slate-light, #475569);
    cursor: pointer;
    font-size: 12px;
    height: 26px;
    width: 26px;
  }
  .copilot-collapse:hover {
    color: var(--color-heading, #0f172a);
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .copilot-context {
    align-items: flex-start;
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.24);
    border-radius: var(--radius-sm, 6px);
    display: flex;
    gap: 10px;
    justify-content: space-between;
    padding: 10px 12px;
    flex-shrink: 0;
  }
  .context-copy { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .context-label { color: var(--color-horizon-bright, #d97706); font-size: 9px; font-weight: 700; letter-spacing: .45px; text-transform: uppercase; }
  .context-copy strong { color: var(--color-heading, #0f172a); font-size: 12px; line-height: 1.35; }
  .context-copy small { color: var(--color-slate-muted, #64748b); font-size: 10px; }
  .context-reset { background: transparent; border: 0; color: var(--color-aurora-bright, #0284c7); cursor: pointer; font-size: 10px; padding: 1px 0; white-space: nowrap; }

  .ai-diff-banner {
    background: rgba(59, 130, 246, 0.07);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: var(--radius-xs, 4px);
    padding: 8px 10px;
    font-size: 11.5px;
    line-height: 1.4;
  }

  .diff-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-aurora-bright, #0284c7);
    margin-bottom: 2px;
  }

  .ai-diff-banner p {
    margin: 0;
    color: var(--color-slate-light, #475569);
  }

  .critique-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
  }

  .critique-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-muted, #64748b);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  .toggle-btn {
    background: transparent;
    border: none;
    color: var(--color-aurora-bright, #0284c7);
    font-size: 10.5px;
    cursor: pointer;
    padding: 0;
  }

  .prompt-chips {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
  }

  .prompt-chip {
    text-align: left;
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: var(--radius-xs, 4px);
    padding: 7px 9px;
    font-size: 10.5px;
    color: var(--color-slate-bright, #0f172a);
    cursor: pointer;
    transition: all 0.12s;
  }
  .prompt-chip:hover {
    background: var(--pill-hover, rgba(0, 0, 0, 0.08));
    border-color: var(--color-graphite-border, #cbd5e1);
  }

  .chat-stream {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    min-height: 170px;
    overflow-y: auto;
    padding: 2px 2px 2px 0;
  }

  .chat-empty {
    align-items: center;
    color: var(--color-slate-muted, #64748b);
    display: flex;
    flex: 1;
    flex-direction: column;
    font-size: 11.5px;
    justify-content: center;
    line-height: 1.5;
    padding: 20px;
    text-align: center;
  }
  .chat-empty strong { color: var(--color-heading, #0f172a); font-size: 12.5px; }

  .chat-msg {
    padding: 7px 10px;
    border-radius: var(--radius-xs, 4px);
    font-size: 11.5px;
    line-height: 1.4;
  }

  .msg-header {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 2px;
  }

  .chat-user {
    background: rgba(59, 130, 246, 0.1);
    color: var(--color-slate-bright, #0f172a);
    border-left: 2px solid var(--color-aurora-bright, #0284c7);
  }
  .chat-user .msg-header {
    color: var(--color-aurora-bright, #0284c7);
  }

  .chat-assistant {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    color: var(--color-slate-bright, #0f172a);
    border-left: 2px solid var(--color-horizon-blue, #4f6bff);
  }
  .chat-assistant .msg-header {
    color: var(--color-horizon-blue, #4f6bff);
  }

  .copilot-input-bar {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: auto;
    border-top: 1px solid var(--color-graphite-border, #e2e8f0);
    padding-top: 12px;
    flex-shrink: 0;
  }

  .chat-input {
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-xs, 4px);
    padding: 10px;
    font-size: 12px;
    color: var(--color-slate-bright, #0f172a);
    outline: none;
    resize: none;
  }
  .chat-input:focus {
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .btn-send-revision {
    background: var(--color-heading, #0f172a);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-xs, 4px);
    padding: 8px 12px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-send-revision:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .composer-footer {
    align-items: center;
    display: flex;
    gap: 10px;
    justify-content: space-between;
  }
  .composer-footer span {
    color: var(--color-slate-muted, #64748b);
    font-size: 9.5px;
  }
</style>
