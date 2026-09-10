<script>
  import { onMount } from 'svelte';
  import { getStudentId, responseError, routeParams, sessionStorageKey } from '../lib/session.js';

  let courseId = $state('');
  let assignmentId = $state('');
  let assignment = $state(null);
  let sources = $state([]);
  let studentId = $state('');
  let sessionId = $state('');
  let sessionStatus = $state('active');
  let userMessage = $state('');
  let currentRung = $state(0);
  let isLoading = $state(true);
  let isTyping = $state(false);
  let error = $state('');
  let messages = $state([]);

  function appendMessage(role, content, meta = {}) {
    messages = [...messages, { role, content, ...meta }];
  }

  async function loadAssignment() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    assignmentId = params.get('assignment_id') || '';

    if (assignmentId) {
      const response = await fetch(`/assignments/${assignmentId}`);
      if (!response.ok) throw new Error(await responseError(response, 'The requested assignment could not be loaded.'));
      assignment = await response.json();
    } else if (courseId) {
      const response = await fetch(`/assignments?course_id=${encodeURIComponent(courseId)}&status=published`);
      if (!response.ok) throw new Error(await responseError(response, 'Published assignments could not be loaded.'));
      const assignments = await response.json();
      assignment = assignments[0] || null;
      assignmentId = assignment?.assignment_id || '';
    }

    if (!assignment) return;
    studentId = getStudentId();
    const key = sessionStorageKey(assignmentId, studentId);
    const persistedSessionId = localStorage.getItem(key);

    if (persistedSessionId) {
      const existing = await fetch(`/events/session/${persistedSessionId}`);
      if (existing.ok) {
        const session = (await existing.json()).session;
        if (session.status === 'active') {
          sessionId = persistedSessionId;
          sessionStatus = session.status;
        }
      }
    }

    if (!sessionId) {
      const response = await fetch('/events/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          assignment_id: assignmentId,
          current_question_id: assignment.question_id,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'A reasoning session could not be started.'));
      const created = await response.json();
      sessionId = created.session_id;
      sessionStatus = created.status;
      localStorage.setItem(key, sessionId);
    }

    const replay = await fetch(`/events/session/${sessionId}`);
    if (replay.ok) {
      const { events } = await replay.json();
      const restored = [];
      for (const event of events) {
        if (event.event_type === 'student_prompt_submitted') {
          restored.push({ role: 'user', content: event.payload.student_input });
        }
        if (['tutor_turn_completed', 'hint_delivered', 'adversarial_probe_defended'].includes(event.event_type)) {
          restored.push({
            role: 'assistant',
            content: event.payload.response_text,
            hintRung: event.payload.hint_rung,
            isAdversarial: event.event_type === 'adversarial_probe_defended',
          });
          currentRung = Math.max(currentRung, event.payload.hint_rung || 0);
        }
      }
      messages = restored;
    }

    if (courseId) {
      const sourceResponse = await fetch(`/courses/${courseId}/syllabus`);
      if (sourceResponse.ok) sources = (await sourceResponse.json()).slice(0, 5);
    }
  }

  async function sendMessage({ hintRequested = false } = {}) {
    const draft = hintRequested ? 'I need a hint to continue developing my argument.' : userMessage.trim();
    if (!draft || !assignment || !sessionId || sessionStatus !== 'active') return;

    if (!hintRequested) userMessage = '';
    appendMessage('user', draft);
    isTyping = true;
    error = '';

    try {
      const response = await fetch('/dialogue/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          assignment_id: assignmentId,
          question_id: assignment.question_id,
          question_prompt: assignment.prompt,
          domain: assignment.domain,
          student_input: draft,
          current_rung: currentRung,
          hint_requested: hintRequested,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The Socratic guide could not respond.'));
      const result = await response.json();
      currentRung = Math.max(currentRung, result.hint_rung || 0);
      appendMessage('assistant', result.response_text, {
        hintRung: result.hint_rung,
        isAdversarial: result.is_adversarial,
      });
    } catch (err) {
      error = err.message || 'The message could not be sent.';
      messages = messages.slice(0, -1);
      if (!hintRequested) userMessage = draft;
    } finally {
      isTyping = false;
    }
  }

  function citeSource(source) {
    const citation = `\n\n[Source: ${source.title || 'Course material'}] ${source.content?.slice(0, 240) || ''}`;
    userMessage = `${userMessage}${citation}`.trim();
  }

  onMount(async () => {
    try {
      await loadAssignment();
    } catch (err) {
      error = err.message || 'The learning workspace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

{#if isLoading}
  <main class="loading-view"><div class="spinner"></div><p>Opening your reasoning workspace…</p></main>
{:else if error && !assignment}
  <main class="empty-view"><h1>Workspace unavailable</h1><p>{error}</p><a class="btn btn-primary" href="#/courses">Return to courses</a></main>
{:else if !assignment}
  <main class="empty-view">
    <h1>No published assignment selected</h1>
    <p>Open a published assignment from a curriculum module to start a protected reasoning session.</p>
    <a class="btn btn-primary" href="#/courses">Choose a course</a>
  </main>
{:else}
  <div class="workspace-layout">
    <aside class="context-col">
      <div class="eyebrow">Active assignment</div>
      <h1>{assignment.prompt.length > 62 ? `${assignment.prompt.slice(0, 62)}…` : assignment.prompt}</h1>
      <div class="meta-row"><span>{assignment.domain}</span><span>•</span><span>{assignment.target_kcs.length} KCs</span></div>
      <p class="assignment-prompt">{assignment.prompt}</p>

      <section class="progress-section">
        <div class="section-title">Scaffolding availability</div>
        <div class="rung-row"><span>Current support level</span><strong>Rung {currentRung} / 3</strong></div>
        <div class="progress-track"><div class="progress-fill" style={`width: ${(currentRung / 3) * 100}%`}></div></div>
        <p>Hints are advanced by the server only after an explicit request. The bottom-out solution remains locked.</p>
      </section>

      <section class="kc-section">
        <div class="section-title">Target knowledge components</div>
        {#each assignment.target_kcs as kc}
          <code>{kc}</code>
        {/each}
      </section>

      {#if sessionId}
        <a class="btn btn-secondary trace-button" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`}>
          View reasoning trace →
        </a>
      {/if}
    </aside>

    <main class="dialogue-col">
      <header class="dialogue-header">
        <div>
          <div class="dialogue-title">Socratic Reasoning Canvas</div>
          <div class="dialogue-sub">Fiosra strengthens your reasoning without exposing a reference answer.</div>
        </div>
        <span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span>
      </header>

      <div class="messages-container" aria-live="polite">
        {#if messages.length === 0}
          <div class="welcome-card">
            <strong>Start with a provisional claim.</strong>
            <p>State the evidence you would use and why it supports your argument. You can request a bounded Socratic hint whenever you are genuinely stuck.</p>
          </div>
        {/if}
        {#each messages as msg}
          <div class:assistant={msg.role === 'assistant'} class:user={msg.role === 'user'} class="message">
            <div class="msg-avatar">{msg.role === 'assistant' ? 'F' : 'S'}</div>
            <div class="msg-bubble">
              {#if msg.isAdversarial}<span class="guardrail-label">Integrity boundary</span>{/if}
              <p>{msg.content}</p>
              {#if msg.role === 'assistant' && msg.hintRung > 0}<span class="hint-label">Support rung {msg.hintRung}</span>{/if}
            </div>
          </div>
        {/each}
        {#if isTyping}
          <div class="message assistant"><div class="msg-avatar">F</div><div class="msg-bubble typing">Thinking through your reasoning…</div></div>
        {/if}
      </div>

      {#if error}<div class="error-banner">{error}</div>{/if}
      <div class="input-area">
        <textarea
          class="message-input"
          placeholder="Articulate a claim, identify evidence, and explain your reasoning…"
          rows="4"
          bind:value={userMessage}
          disabled={isTyping || sessionStatus !== 'active'}
          onkeydown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); } }}
        ></textarea>
        <div class="input-actions">
          <button class="btn btn-secondary" onclick={() => sendMessage({ hintRequested: true })} disabled={isTyping || sessionStatus !== 'active' || currentRung >= 3}>Request a hint</button>
          <button class="btn btn-primary" onclick={() => sendMessage()} disabled={!userMessage.trim() || isTyping || sessionStatus !== 'active'}>Send reasoning →</button>
        </div>
      </div>
    </main>

    <aside class="evidence-col">
      <div class="section-title">Grounded course material</div>
      <p class="source-subtitle">Use a source as evidence; Fiosra will preserve the trace of your evolving reasoning.</p>
      {#if sources.length === 0}
        <div class="source-empty">No attached material has been indexed for this course yet. You can still develop a claim from the assignment prompt.</div>
      {:else}
        {#each sources as source (source.chunk_id)}
          <article class="source-card">
            <h2>{source.title || 'Course material'}</h2>
            <p>{source.content?.slice(0, 210)}{source.content?.length > 210 ? '…' : ''}</p>
            <button class="btn-cite" onclick={() => citeSource(source)} disabled={sessionStatus !== 'active'}>Add as a citation</button>
          </article>
        {/each}
      {/if}
    </aside>
  </div>
{/if}

<style>
  .workspace-layout { display:grid; grid-template-columns: minmax(240px,300px) minmax(0,1fr) minmax(260px,320px); min-height:calc(100vh - 56px); }
  .context-col,.evidence-col { background:var(--color-graphite); padding:24px 20px; display:flex; flex-direction:column; gap:18px; }
  .context-col { border-right:1px solid var(--color-graphite-border); }
  .evidence-col { border-left:1px solid var(--color-graphite-border); }
  .eyebrow,.section-title { color:var(--color-slate-muted); font-size:11px; font-weight:700; letter-spacing:.5px; text-transform:uppercase; }
  h1 { color:#fff; font-family:var(--font-brand); font-size:18px; line-height:1.3; margin:0; }
  .meta-row { color:var(--color-horizon-bright); font-size:12px; display:flex; gap:6px; text-transform:capitalize; }
  .assignment-prompt,.source-subtitle { color:var(--color-slate-light); font-size:12.5px; line-height:1.65; margin:0; }
  .progress-section,.kc-section { border-top:1px solid var(--color-graphite-border); padding-top:16px; display:flex; flex-direction:column; gap:9px; }
  .rung-row { color:var(--color-slate-light); display:flex; justify-content:space-between; font-size:12px; }
  .rung-row strong { color:var(--color-horizon-bright); }
  .progress-track { height:6px; background:var(--color-graphite-border); border-radius:99px; overflow:hidden; }
  .progress-fill { height:100%; background:linear-gradient(90deg,var(--color-horizon-blue),var(--color-aurora)); transition:width .2s ease; }
  .progress-section p { color:var(--color-slate-muted); font-size:11px; line-height:1.5; margin:0; }
  code { color:var(--color-aurora-bright); font-size:10px; overflow-wrap:anywhere; }
  .trace-button { margin-top:auto; }
  .dialogue-col { min-width:0; display:flex; flex-direction:column; background:var(--color-obsidian); }
  .dialogue-header { border-bottom:1px solid var(--color-graphite-border); padding:20px 28px; display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
  .dialogue-title { color:#fff; font-size:16px; font-weight:700; }.dialogue-sub { color:var(--color-slate-muted); font-size:12px; margin-top:3px; }
  .session-badge { background:rgba(16,185,129,.12); border:1px solid rgba(16,185,129,.25); border-radius:99px; color:#34d399; font-size:11px; font-weight:700; padding:3px 9px; text-transform:capitalize; }.session-badge.submitted { color:var(--color-amber); background:rgba(245,158,11,.12); border-color:rgba(245,158,11,.25); }
  .messages-container { flex:1; padding:28px; overflow-y:auto; display:flex; flex-direction:column; gap:16px; }.welcome-card { max-width:620px; margin:auto; background:var(--color-graphite); border:1px solid var(--color-graphite-border); border-radius:var(--radius-md); padding:24px; color:var(--color-slate-light); line-height:1.6; }.welcome-card strong { color:#fff; }.welcome-card p { margin:8px 0 0; font-size:13px; }
  .message { display:flex; gap:10px; align-items:flex-start; max-width:82%; }.message.user { align-self:flex-end; flex-direction:row-reverse; }.msg-avatar { background:linear-gradient(135deg,var(--color-horizon-blue),var(--color-aurora)); border-radius:50%; color:#fff; display:flex; flex:0 0 30px; height:30px; align-items:center; justify-content:center; font-size:11px; font-weight:700; }.user .msg-avatar { background:linear-gradient(135deg,#059669,#0ea5e9); }.msg-bubble { background:var(--color-graphite); border:1px solid var(--color-graphite-border); border-radius:4px 14px 14px 14px; color:#e2e8f0; padding:12px 15px; font-size:13px; line-height:1.6; }.user .msg-bubble { background:rgba(59,130,246,.13); border-color:rgba(59,130,246,.3); border-radius:14px 4px 14px 14px; }.msg-bubble p { white-space:pre-wrap; margin:0; }.typing { color:var(--color-slate-muted); font-style:italic; }.guardrail-label,.hint-label { display:block; color:var(--color-amber); font-size:10px; font-weight:700; margin-bottom:5px; text-transform:uppercase; }.hint-label { color:var(--color-horizon-bright); margin:7px 0 0; }
  .error-banner { margin:0 28px; background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.3); border-radius:var(--radius-sm); color:#fca5a5; font-size:12px; padding:9px 12px; }.input-area { border-top:1px solid var(--color-graphite-border); padding:18px 28px; }.message-input { background:var(--color-graphite); border:1px solid var(--color-graphite-border); border-radius:var(--radius-md); box-sizing:border-box; color:#fff; font:inherit; font-size:13px; padding:12px 14px; resize:vertical; width:100%; }.message-input:focus { border-color:var(--color-horizon-blue); outline:none; }.input-actions { display:flex; justify-content:space-between; gap:10px; margin-top:10px; }
  .source-card { border-bottom:1px solid var(--color-graphite-border); display:flex; flex-direction:column; gap:8px; padding:0 0 16px; }.source-card h2 { color:#e2e8f0; font-size:13px; margin:0; }.source-card p { color:var(--color-slate-muted); font-size:11.5px; line-height:1.5; margin:0; }.btn-cite { background:none; border:1px solid var(--color-graphite-border); border-radius:var(--radius-xs); color:var(--color-horizon-bright); cursor:pointer; font-size:11px; font-weight:600; padding:6px 8px; text-align:left; }.btn-cite:hover:not(:disabled) { border-color:var(--color-horizon-blue); }.btn-cite:disabled { cursor:not-allowed; opacity:.5; }.source-empty { border:1px dashed var(--color-graphite-border); color:var(--color-slate-muted); font-size:12px; line-height:1.5; padding:14px; }
  .loading-view,.empty-view { align-items:center; background:var(--color-obsidian); color:var(--color-slate-light); display:flex; flex-direction:column; gap:14px; justify-content:center; min-height:calc(100vh - 56px); padding:24px; text-align:center; }.empty-view h1 { font-size:24px; }.empty-view p { max-width:520px; }.spinner { animation:spin .8s linear infinite; border:3px solid rgba(59,130,246,.2); border-radius:50%; border-top-color:var(--color-horizon-bright); height:32px; width:32px; }@keyframes spin{to{transform:rotate(360deg)}}
  @media (max-width:1050px){.workspace-layout{grid-template-columns:240px minmax(0,1fr)}.evidence-col{display:none}}@media (max-width:720px){.workspace-layout{display:flex; flex-direction:column}.context-col{border-bottom:1px solid var(--color-graphite-border);border-right:none}.messages-container{min-height:380px}.message{max-width:94%}.dialogue-header,.messages-container,.input-area{padding-left:16px;padding-right:16px}}
</style>
