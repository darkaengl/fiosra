<script>
  import { onMount } from 'svelte';

  let courseId = $state('');
  let userMessage = $state('');
  let messages = $state([
    { role: 'assistant', content: 'Welcome to your Fiosra reasoning workspace. I am your Socratic scaffold for this module. What aspect of the French Revolution\'s fiscal origins would you like to explore first?' },
  ]);
  let isTyping = $state(false);

  async function sendMessage() {
    if (!userMessage.trim()) return;
    const msg = userMessage.trim();
    userMessage = '';
    messages = [...messages, { role: 'user', content: msg }];
    isTyping = true;

    try {
      // In a real implementation: POST /dialogue with the message
      await new Promise(r => setTimeout(r, 1200));
      messages = [...messages, {
        role: 'assistant',
        content: 'That\'s an excellent line of inquiry. Before I provide my perspective, I want to challenge your reasoning: can you identify which specific fiscal mechanism in the Ancien Régime was structurally incapable of reform, and why? Ground your response in the primary readings from Module 1.'
      }];
    } finally {
      isTyping = false;
    }
  }

  onMount(() => {
    const hash = window.location.hash;
    const q = hash.indexOf('?');
    if (q >= 0) {
      const params = new URLSearchParams(hash.slice(q + 1));
      courseId = params.get('course_id') || '';
    }
  });
</script>

<div class="workspace-layout">
  <!-- Left: Assignment Context -->
  <aside class="context-col">
    <div class="context-header">
      <div class="context-title">Active Assignment</div>
      <span class="assignment-badge">Due: 72h</span>
    </div>

    <div class="assignment-card">
      <div class="assignment-title">Essay: Fiscal Crisis & Sovereignty</div>
      <div class="assignment-meta">HIST-201 • Module 2 • 1200 words</div>
      <p class="assignment-prompt">
        Analyze the relationship between the Ancien Régime fiscal crisis and the conceptual emergence of popular sovereignty. Drawing on primary readings, construct a causal argument grounded in at least three Knowledge Components.
      </p>
    </div>

    <div class="progress-section">
      <div class="progress-label">
        <span>Autonomy Index</span>
        <span class="progress-pct">62%</span>
      </div>
      <div class="progress-track"><div class="progress-fill" style="width: 62%;"></div></div>
      <div class="progress-note">Target: 80% mastery before submission</div>
    </div>

    <div class="kc-section">
      <div class="section-label">Grounded KCs</div>
      <div class="kc-stack">
        {#each [
          { code: 'KC_HIST_FISCAL_CRISIS_1786', mastery: 78, status: 'grounded' },
          { code: 'KC_HIST_ESTATE_SYSTEM', mastery: 65, status: 'partial' },
          { code: 'KC_HIST_POPULAR_SOV', mastery: 41, status: 'flagged' },
        ] as kc}
          <div class="kc-item">
            <div class="kc-item-header">
              <code class="kc-code-sm">{kc.code}</code>
              <span class="kc-mastery {kc.status}">{kc.mastery}%</span>
            </div>
            <div class="kc-bar-track"><div class="kc-bar-fill {kc.status}" style="width: {kc.mastery}%"></div></div>
          </div>
        {/each}
      </div>
    </div>
  </aside>

  <!-- Center: Dialogue Canvas -->
  <main class="dialogue-col">
    <div class="dialogue-header">
      <div class="dialogue-title">Socratic Reasoning Canvas</div>
      <div class="dialogue-sub">Fiosra scaffolds your epistemic reasoning — not your answers</div>
    </div>

    <div class="messages-container">
      {#each messages as msg}
        <div class="message {msg.role}">
          {#if msg.role === 'assistant'}
            <div class="msg-avatar">F</div>
          {/if}
          <div class="msg-bubble">
            <p class="msg-text">{msg.content}</p>
          </div>
          {#if msg.role === 'user'}
            <div class="msg-avatar user-avatar">S</div>
          {/if}
        </div>
      {/each}
      {#if isTyping}
        <div class="message assistant">
          <div class="msg-avatar">F</div>
          <div class="msg-bubble typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      {/if}
    </div>

    <div class="input-area">
      <textarea
        class="message-input"
        placeholder="Articulate your reasoning grounded in the syllabus readings..."
        rows="3"
        bind:value={userMessage}
        onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
      ></textarea>
      <button class="btn btn-primary send-btn" onclick={sendMessage} disabled={!userMessage.trim() || isTyping}>
        Send →
      </button>
    </div>
  </main>

  <!-- Right: Evidence & Sources -->
  <aside class="evidence-col">
    <div class="evidence-header">
      <div class="evidence-title">Source Evidence</div>
      <div class="evidence-sub">pgvector grounded readings</div>
    </div>

    <div class="evidence-list">
      {#each [
        { title: 'Necker\'s Account of Royal Finances, 1781', similarity: 0.94, module: 'Module 1' },
        { title: 'Sieyès: What is the Third Estate? (1789)', similarity: 0.88, module: 'Module 2' },
        { title: 'Rousseau: Social Contract, Book II', similarity: 0.82, module: 'Module 2' },
      ] as src}
        <div class="evidence-card">
          <div class="evidence-title-sm">{src.title}</div>
          <div class="evidence-meta">
            <span class="evidence-badge">{src.module}</span>
            <span class="similarity-score">sim: {src.similarity}</span>
          </div>
          <button class="btn-cite">Cite this source</button>
        </div>
      {/each}
    </div>
  </aside>
</div>

<style>
  .workspace-layout { display: grid; grid-template-columns: 300px 1fr 320px; height: calc(100vh - 56px); }
  .context-col { background: var(--color-graphite); border-right: 1px solid var(--color-graphite-border); padding: 24px 20px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
  .context-header { display: flex; justify-content: space-between; align-items: center; }
  .context-title { font-size: 13px; font-weight: 700; color: #fff; text-transform: uppercase; letter-spacing: .5px; }
  .assignment-badge { font-size: 10.5px; font-weight: 600; color: var(--color-amber); background: rgba(245,158,11,.12); border: 1px solid rgba(245,158,11,.3); padding: 2px 8px; border-radius: var(--radius-xs); }
  .assignment-card { background: var(--color-graphite-card); border: 1px solid var(--color-horizon-blue); border-radius: var(--radius-sm); padding: 16px; }
  .assignment-title { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; }
  .assignment-meta { font-size: 10.5px; color: var(--color-slate-muted); margin-bottom: 10px; }
  .assignment-prompt { font-size: 12px; color: var(--color-slate-light); line-height: 1.6; margin: 0; }
  .progress-section { display: flex; flex-direction: column; gap: 6px; }
  .progress-label { display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: var(--color-slate-light); }
  .progress-pct { color: var(--color-horizon-bright); }
  .progress-track { height: 6px; background: var(--color-graphite-border); border-radius: var(--radius-full); overflow: hidden; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, var(--color-horizon-blue), #8b5cf6); border-radius: var(--radius-full); }
  .progress-note { font-size: 10.5px; color: var(--color-slate-muted); }
  .section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--color-slate-muted); letter-spacing: .5px; }
  .kc-section { display: flex; flex-direction: column; gap: 10px; }
  .kc-stack { display: flex; flex-direction: column; gap: 10px; }
  .kc-item { display: flex; flex-direction: column; gap: 5px; }
  .kc-item-header { display: flex; justify-content: space-between; align-items: center; }
  .kc-code-sm { font-family: var(--font-mono); font-size: 9.5px; color: var(--color-aurora-bright); }
  .kc-mastery { font-size: 11px; font-weight: 700; }
  .kc-mastery.grounded { color: #34d399; }
  .kc-mastery.partial { color: var(--color-horizon-bright); }
  .kc-mastery.flagged { color: var(--color-rose); }
  .kc-bar-track { height: 4px; background: var(--color-graphite-border); border-radius: var(--radius-full); overflow: hidden; }
  .kc-bar-fill { height: 100%; border-radius: var(--radius-full); }
  .kc-bar-fill.grounded { background: #34d399; }
  .kc-bar-fill.partial { background: var(--color-horizon-blue); }
  .kc-bar-fill.flagged { background: var(--color-rose); }
  .dialogue-col { display: flex; flex-direction: column; background: var(--color-obsidian); }
  .dialogue-header { padding: 20px 28px; border-bottom: 1px solid var(--color-graphite-border); }
  .dialogue-title { font-size: 15px; font-weight: 700; color: #fff; }
  .dialogue-sub { font-size: 12px; color: var(--color-slate-muted); margin-top: 2px; }
  .messages-container { flex: 1; overflow-y: auto; padding: 24px 28px; display: flex; flex-direction: column; gap: 20px; }
  .message { display: flex; align-items: flex-start; gap: 12px; }
  .message.user { flex-direction: row-reverse; }
  .msg-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #8b5cf6); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #fff; flex-shrink: 0; }
  .user-avatar { background: linear-gradient(135deg, #10b981, #3b82f6); }
  .msg-bubble { max-width: 70%; background: var(--color-graphite); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-lg); padding: 14px 18px; }
  .message.user .msg-bubble { background: rgba(59,130,246,.12); border-color: rgba(59,130,246,.3); }
  .msg-text { margin: 0; font-size: 13.5px; color: #e2e8f0; line-height: 1.6; }
  .typing-indicator { display: flex; gap: 4px; align-items: center; padding: 12px 16px; }
  .typing-indicator span { width: 6px; height: 6px; background: var(--color-slate-muted); border-radius: 50%; animation: bounce .8s infinite; }
  .typing-indicator span:nth-child(2) { animation-delay: .15s; }
  .typing-indicator span:nth-child(3) { animation-delay: .3s; }
  @keyframes bounce { 0%,80%,100% { transform: translateY(0); } 40% { transform: translateY(-6px); } }
  .input-area { display: flex; gap: 12px; padding: 20px 28px; border-top: 1px solid var(--color-graphite-border); }
  .message-input { flex: 1; background: var(--color-graphite); border: 1px solid var(--color-graphite-border); color: #fff; padding: 12px 16px; border-radius: var(--radius-md); font-family: var(--font-body); font-size: 13.5px; resize: none; transition: border-color .15s; }
  .message-input:focus { outline: none; border-color: var(--color-horizon-blue); }
  .send-btn { align-self: flex-end; }
  .evidence-col { background: var(--color-graphite); border-left: 1px solid var(--color-graphite-border); display: flex; flex-direction: column; overflow-y: auto; }
  .evidence-header { padding: 24px 20px; border-bottom: 1px solid var(--color-graphite-border); }
  .evidence-title { font-size: 13px; font-weight: 700; color: #fff; }
  .evidence-sub { font-size: 11px; color: var(--color-slate-muted); margin-top: 2px; }
  .evidence-list { display: flex; flex-direction: column; gap: 0; }
  .evidence-card { padding: 16px 20px; border-bottom: 1px solid var(--color-graphite-border); display: flex; flex-direction: column; gap: 8px; }
  .evidence-title-sm { font-size: 12.5px; font-weight: 600; color: #e2e8f0; line-height: 1.4; }
  .evidence-meta { display: flex; justify-content: space-between; align-items: center; }
  .evidence-badge { font-size: 10px; font-weight: 600; background: rgba(59,130,246,.12); color: var(--color-horizon-bright); border: 1px solid rgba(59,130,246,.3); padding: 2px 7px; border-radius: var(--radius-xs); }
  .similarity-score { font-family: var(--font-mono); font-size: 10.5px; color: #34d399; }
  .btn-cite { background: none; border: 1px solid var(--color-graphite-border); color: var(--color-slate-light); font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: var(--radius-xs); cursor: pointer; transition: all .15s; }
  .btn-cite:hover { border-color: var(--color-horizon-blue); color: var(--color-horizon-bright); }
</style>
