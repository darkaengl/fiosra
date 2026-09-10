<script>
  import { onMount } from 'svelte';
  import {
    getStudentId,
    responseError,
    routeParams,
    sessionAccessTokenStorageKey,
    sessionStorageKey,
  } from '../lib/session.js';

  let courseId = $state('');
  let assignmentId = $state('');
  let assignment = $state(null);
  let sources = $state([]);
  let studentId = $state('');
  let sessionId = $state('');
  let sessionAccessToken = $state('');
  let sessionStatus = $state('active');
  let userMessage = $state('');
  let currentRung = $state(0);
  let isLoading = $state(true);
  let isTyping = $state(false);
  let isSavingCanvas = $state(false);
  let isRequestingSupport = $state(false);
  let error = $state('');
  let messages = $state([]);
  let canvasSections = $state([]);
  let canvasDrafts = $state({});
  let canvasSuggestions = $state({});
  let activeSectionId = $state('working_claim');
  let activeSuggestion = $state(null);
  let activeSectionText = $state('');
  let activeSourceReferences = $state([]);

  let activeSection = $derived(canvasSections.find((section) => section.section_id === activeSectionId) || canvasSections[0] || null);
  let activeDraft = $derived(canvasDrafts[activeSectionId] || { section_id: activeSectionId, text: '', revision: 0, source_references: [] });
  let sourceById = $derived(Object.fromEntries(sources.map((source) => [source.chunk_id, source])));

  function appendMessage(role, content, meta = {}) {
    messages = [...messages, { role, content, ...meta }];
  }

  function canvasHeaders() {
    return { 'X-Fiosra-Session-Token': sessionAccessToken, 'Content-Type': 'application/json' };
  }

  function resetActiveEditor(sectionId) {
    activeSectionId = sectionId;
    const draft = canvasDrafts[sectionId] || { text: '', source_references: [] };
    activeSectionText = draft.text || '';
    activeSourceReferences = draft.source_references || [];
    activeSuggestion = canvasSuggestions[sectionId] || null;
  }

  async function loadCanvas() {
    if (!sessionId || !sessionAccessToken) return;
    const response = await fetch(`/learning-canvas/sessions/${sessionId}`, { headers: canvasHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your evidence canvas could not be restored.'));
    const canvas = await response.json();
    sessionStatus = canvas.status;
    canvasSections = canvas.sections || [];
    canvasDrafts = Object.fromEntries((canvas.drafts || []).map((draft) => [draft.section_id, draft]));
    canvasSuggestions = Object.fromEntries((canvas.suggestions || []).map((suggestion) => [suggestion.section_id, suggestion]));
    const visibleSection = canvasSections.some((section) => section.section_id === activeSectionId)
      ? activeSectionId
      : canvasSections[0]?.section_id;
    if (visibleSection) resetActiveEditor(visibleSection);
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
    sources = assignment.grounding_sources || [];
    const key = sessionStorageKey(assignmentId, studentId);
    const persistedSessionId = localStorage.getItem(key);
    const persistedAccessToken = persistedSessionId ? localStorage.getItem(sessionAccessTokenStorageKey(persistedSessionId)) : '';

    if (persistedSessionId && persistedAccessToken) {
      const existing = await fetch(`/events/session/${persistedSessionId}`, {
        headers: { 'X-Fiosra-Session-Token': persistedAccessToken },
      });
      if (existing.ok) {
        const session = (await existing.json()).session;
        if (session.status === 'active') {
          sessionId = persistedSessionId;
          sessionAccessToken = persistedAccessToken;
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
      sessionAccessToken = created.access_token;
      sessionStatus = created.status;
      localStorage.setItem(key, sessionId);
      localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
    }

    const replay = await fetch(`/events/session/${sessionId}`, {
      headers: { 'X-Fiosra-Session-Token': sessionAccessToken },
    });
    if (replay.ok) {
      const { events } = await replay.json();
      const restored = [];
      for (const event of events) {
        if (event.event_type === 'student_prompt_submitted') restored.push({ role: 'user', content: event.payload.student_input });
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
    await loadCanvas();
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
        headers: canvasHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          assignment_id: assignmentId,
          question_id: assignment.question_id,
          active_section_id: activeSectionId,
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
      appendMessage('assistant', result.response_text, { hintRung: result.hint_rung, isAdversarial: result.is_adversarial });
    } catch (err) {
      error = err.message || 'The message could not be sent.';
      messages = messages.slice(0, -1);
      if (!hintRequested) userMessage = draft;
    } finally {
      isTyping = false;
    }
  }

  function selectSection(sectionId) {
    if (isSavingCanvas || isRequestingSupport) return;
    resetActiveEditor(sectionId);
  }

  function citeSource(source) {
    if (!activeSection) return;
    if (activeSourceReferences.some((reference) => reference.chunk_id === source.chunk_id)) return;
    activeSourceReferences = [
      ...activeSourceReferences,
      {
        chunk_id: source.chunk_id,
        quote: source.excerpt || '',
        rationale: `Selected for ${activeSection.label.toLowerCase()}.`,
      },
    ];
  }

  function removeSourceReference(chunkId) {
    activeSourceReferences = activeSourceReferences.filter((reference) => reference.chunk_id !== chunkId);
  }

  async function saveActiveSection({ fromSuggestion = false } = {}) {
    if (!activeSection || !sessionId || sessionStatus !== 'active') return;
    isSavingCanvas = true;
    error = '';
    try {
      let response;
      if (fromSuggestion && activeSuggestion) {
        response = await fetch(
          `/learning-canvas/sessions/${sessionId}/suggestions/${activeSuggestion.suggestion_id}/accept`,
          {
            method: 'POST',
            headers: canvasHeaders(),
            body: JSON.stringify({ text: activeSectionText, source_references: activeSourceReferences }),
          },
        );
      } else {
        response = await fetch(`/learning-canvas/sessions/${sessionId}/sections/${activeSection.section_id}`, {
          method: 'PUT',
          headers: canvasHeaders(),
          body: JSON.stringify({
            text: activeSectionText,
            base_revision: activeDraft.revision || 0,
            source_references: activeSourceReferences,
            author_type: 'student',
          }),
        });
      }
      if (!response.ok) throw new Error(await responseError(response, 'This section could not be saved.'));
      const result = await response.json();
      const updatedDraft = fromSuggestion ? result.draft : result;
      canvasDrafts = { ...canvasDrafts, [activeSection.section_id]: updatedDraft };
      if (fromSuggestion) canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: null };
      activeSuggestion = null;
      activeSectionText = updatedDraft.text;
      activeSourceReferences = updatedDraft.source_references || [];
    } catch (err) {
      error = err.message || 'This section could not be saved.';
    } finally {
      isSavingCanvas = false;
    }
  }

  async function requestSectionSupport(kind) {
    if (!activeSection || !sessionId || sessionStatus !== 'active') return;
    isRequestingSupport = true;
    error = '';
    try {
      const response = await fetch(`/learning-canvas/sessions/${sessionId}/suggestions`, {
        method: 'POST',
        headers: canvasHeaders(),
        body: JSON.stringify({ section_id: activeSection.section_id, kind, base_revision: activeDraft.revision || 0 }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Section support could not be prepared.'));
      activeSuggestion = await response.json();
      canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: activeSuggestion };
    } catch (err) {
      error = err.message || 'Section support could not be prepared.';
    } finally {
      isRequestingSupport = false;
    }
  }

  function editSuggestion() {
    if (!activeSuggestion) return;
    activeSectionText = activeSuggestion.content;
  }

  async function dismissSuggestion() {
    if (!activeSuggestion || !sessionId) return;
    isRequestingSupport = true;
    try {
      const response = await fetch(
        `/learning-canvas/sessions/${sessionId}/suggestions/${activeSuggestion.suggestion_id}/dismiss`,
        { method: 'POST', headers: canvasHeaders(), body: JSON.stringify({ reason: 'Student chose to continue independently.' }) },
      );
      if (!response.ok) throw new Error(await responseError(response, 'The support card could not be dismissed.'));
      canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: null };
      activeSuggestion = null;
    } catch (err) {
      error = err.message || 'The support card could not be dismissed.';
    } finally {
      isRequestingSupport = false;
    }
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
  <main class="empty-view"><h1>No published assignment selected</h1><p>Open a published assignment from a curriculum module to start a protected reasoning session.</p><a class="btn btn-primary" href="#/courses">Choose a course</a></main>
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
      <section class="kc-section"><div class="section-title">Target knowledge components</div>{#each assignment.target_kcs as kc}<code>{kc}</code>{/each}</section>
      {#if sessionId}<a class="btn btn-secondary trace-button" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`}>View reasoning trace →</a>{/if}
    </aside>

    <main class="workspace-col">
      <header class="workspace-header">
        <div><div class="workspace-title">Reasoning canvas</div><div class="workspace-sub">Build your own argument in visible steps. Support cards are optional and never write to your work automatically.</div></div>
        <span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span>
      </header>

      <section class="canvas-panel" aria-label="Student reasoning canvas">
        <div class="canvas-steps" role="tablist" aria-label="Reasoning sections">
          {#each canvasSections as section}
            {@const draft = canvasDrafts[section.section_id] || { text: '' }}
            <button class:active={section.section_id === activeSectionId} class:complete={draft.text?.trim()} onclick={() => selectSection(section.section_id)} role="tab" aria-selected={section.section_id === activeSectionId}>
              <span>{section.position}</span><div><strong>{section.label}</strong><small>{draft.text?.trim() ? 'Saved draft' : section.required ? 'Required' : 'Optional'}</small></div>
            </button>
          {/each}
        </div>
        {#if activeSection}
          <div class="section-editor">
            <div class="section-editor-heading"><div><div class="eyebrow">Student-authored section</div><h2>{activeSection.label}</h2><p>{activeSection.purpose}</p></div><span>Revision {activeDraft.revision || 0}</span></div>
            <p class="section-guidance">{activeSection.completion_guidance}</p>
            <textarea class="canvas-input" rows="6" maxlength={activeSection.max_characters} bind:value={activeSectionText} disabled={isSavingCanvas || sessionStatus !== 'active'} placeholder={`Write your ${activeSection.label.toLowerCase()} in your own words…`}></textarea>
            <div class="canvas-status"><span>{activeSectionText.length} / {activeSection.max_characters} characters</span>{#if activeDraft.author_type === 'student_edited_assistance'}<span class="assistance-label">You edited an optional support frame</span>{:else if activeDraft.author_type === 'student'}<span>Student-authored</span>{/if}</div>
            {#if activeSourceReferences.length}
              <div class="selected-sources"><strong>Selected source references</strong>{#each activeSourceReferences as reference}<span><button aria-label="Remove source reference" onclick={() => removeSourceReference(reference.chunk_id)}>×</button>{sourceById[reference.chunk_id]?.title || 'Approved course source'}</span>{/each}</div>
            {/if}
            {#if activeSuggestion}
              <aside class="support-card"><div class="support-card-heading"><span>Optional support card</span><small>Nothing has been saved automatically.</small></div><p>{activeSuggestion.content}</p><div><button class="btn btn-secondary" onclick={editSuggestion}>Use as an editable frame</button><button class="btn btn-primary" onclick={() => saveActiveSection({ fromSuggestion: true })} disabled={!activeSectionText.trim() || isSavingCanvas}>Apply & save my edit</button><button class="btn-link" onclick={dismissSuggestion} disabled={isRequestingSupport}>Dismiss</button></div></aside>
            {:else}
              <div class="canvas-actions"><div><button class="btn btn-secondary" onclick={() => requestSectionSupport('section_question')} disabled={isRequestingSupport || sessionStatus !== 'active'}>Ask a section question</button><button class="btn btn-secondary" onclick={() => requestSectionSupport('writing_frame')} disabled={isRequestingSupport || sessionStatus !== 'active'}>Request a writing frame</button></div><button class="btn btn-primary" onclick={() => saveActiveSection()} disabled={isSavingCanvas || sessionStatus !== 'active'}>{isSavingCanvas ? 'Saving…' : 'Save my section'}</button></div>
            {/if}
          </div>
        {/if}
      </section>

      <section class="dialogue-panel">
        <header class="dialogue-heading"><div><div class="dialogue-title">Socratic dialogue</div><div class="dialogue-sub">Use this space to think aloud; the guide asks questions but does not provide a reference answer.</div></div></header>
        <div class="messages-container" aria-live="polite">
          {#if messages.length === 0}<div class="welcome-card"><strong>Start with a provisional claim.</strong><p>Use the canvas to capture your reasoning, then ask the Socratic guide to test an assumption or request bounded support.</p></div>{/if}
          {#each messages as msg}
            <div class:assistant={msg.role === 'assistant'} class:user={msg.role === 'user'} class="message"><div class="msg-avatar">{msg.role === 'assistant' ? 'F' : 'S'}</div><div class="msg-bubble">{#if msg.isAdversarial}<span class="guardrail-label">Integrity boundary</span>{/if}<p>{msg.content}</p>{#if msg.role === 'assistant' && msg.hintRung > 0}<span class="hint-label">Support rung {msg.hintRung}</span>{/if}</div></div>
          {/each}
          {#if isTyping}<div class="message assistant"><div class="msg-avatar">F</div><div class="msg-bubble typing">Thinking through your reasoning…</div></div>{/if}
        </div>
        {#if error}<div class="error-banner">{error}</div>{/if}
        <div class="input-area"><textarea class="message-input" placeholder="Ask about an assumption, a source observation, or your reasoning…" rows="3" bind:value={userMessage} disabled={isTyping || sessionStatus !== 'active'} onkeydown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); } }}></textarea><div class="input-actions"><button class="btn btn-secondary" onclick={() => sendMessage({ hintRequested: true })} disabled={isTyping || sessionStatus !== 'active' || currentRung >= 3}>Request a hint</button><button class="btn btn-primary" onclick={() => sendMessage()} disabled={!userMessage.trim() || isTyping || sessionStatus !== 'active'}>Send reasoning →</button></div></div>
      </section>
    </main>

    <aside class="evidence-col"><div class="section-title">Approved assignment sources</div><p class="source-subtitle">Select a source for the canvas section you are writing. Its reference is saved with your revision.</p>{#if sources.length === 0}<div class="source-empty">No approved source excerpts are available for this assignment yet.</div>{:else}{#each sources as source (source.chunk_id)}<article class="source-card"><h2>{source.title || 'Course material'}</h2><p>{source.excerpt || ''}</p><button class="btn-cite" onclick={() => citeSource(source)} disabled={sessionStatus !== 'active' || activeSourceReferences.some((reference) => reference.chunk_id === source.chunk_id)}>{activeSourceReferences.some((reference) => reference.chunk_id === source.chunk_id) ? 'Selected for this section' : 'Select for this section'}</button></article>{/each}{/if}</aside>
  </div>
{/if}

<style>
  .workspace-layout{display:grid;grid-template-columns:minmax(235px,290px) minmax(0,1fr) minmax(255px,315px);min-height:calc(100vh - 56px)}.context-col,.evidence-col{background:var(--color-graphite);padding:24px 20px;display:flex;flex-direction:column;gap:18px}.context-col{border-right:1px solid var(--color-graphite-border)}.evidence-col{border-left:1px solid var(--color-graphite-border)}.eyebrow,.section-title{color:var(--color-slate-muted);font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}h1{color:#fff;font-family:var(--font-brand);font-size:18px;line-height:1.3;margin:0}.meta-row{color:var(--color-horizon-bright);font-size:12px;display:flex;gap:6px;text-transform:capitalize}.assignment-prompt,.source-subtitle{color:var(--color-slate-light);font-size:12.5px;line-height:1.65;margin:0}.progress-section,.kc-section{border-top:1px solid var(--color-graphite-border);padding-top:16px;display:flex;flex-direction:column;gap:9px}.rung-row{color:var(--color-slate-light);display:flex;justify-content:space-between;font-size:12px}.rung-row strong{color:var(--color-horizon-bright)}.progress-track{height:6px;background:var(--color-graphite-border);border-radius:99px;overflow:hidden}.progress-fill{height:100%;background:linear-gradient(90deg,var(--color-horizon-blue),var(--color-aurora));transition:width .2s ease}.progress-section p{color:var(--color-slate-muted);font-size:11px;line-height:1.5;margin:0}code{color:var(--color-aurora-bright);font-size:10px;overflow-wrap:anywhere}.trace-button{margin-top:auto}.workspace-col{background:var(--color-obsidian);min-width:0}.workspace-header{border-bottom:1px solid var(--color-graphite-border);padding:20px 28px;display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.workspace-title{color:#fff;font-size:17px;font-weight:700}.workspace-sub,.dialogue-sub{color:var(--color-slate-muted);font-size:12px;line-height:1.45;margin-top:3px}.session-badge{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.25);border-radius:99px;color:#34d399;font-size:11px;font-weight:700;padding:3px 9px;text-transform:capitalize;white-space:nowrap}.session-badge.submitted{color:var(--color-amber);background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.25)}.canvas-panel,.dialogue-panel{margin:20px 28px;background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);overflow:hidden}.canvas-steps{background:rgba(15,23,42,.55);border-bottom:1px solid var(--color-graphite-border);display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));overflow-x:auto}.canvas-steps button{background:transparent;border:0;border-right:1px solid var(--color-graphite-border);color:var(--color-slate-muted);cursor:pointer;display:flex;gap:8px;min-width:130px;padding:13px;text-align:left}.canvas-steps button:last-child{border-right:0}.canvas-steps button:hover,.canvas-steps button.active{background:rgba(59,130,246,.11);color:#fff}.canvas-steps button.active{box-shadow:inset 0 -2px 0 var(--color-horizon-bright)}.canvas-steps button.complete span{border-color:#34d399;color:#6ee7b7}.canvas-steps span{align-items:center;border:1px solid var(--color-graphite-border);border-radius:50%;display:flex;flex:0 0 22px;font-size:10px;font-weight:700;height:22px;justify-content:center}.canvas-steps div{display:flex;flex-direction:column;gap:2px;min-width:0}.canvas-steps strong{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.canvas-steps small{font-size:9px;text-transform:uppercase}.section-editor{display:flex;flex-direction:column;gap:12px;padding:21px}.section-editor-heading{align-items:flex-start;display:flex;gap:16px;justify-content:space-between}.section-editor-heading h2{color:#fff;font-size:17px;margin:4px 0}.section-editor-heading p,.section-guidance{color:var(--color-slate-light);font-size:12px;line-height:1.5;margin:0}.section-editor-heading>span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;white-space:nowrap}.section-guidance{background:rgba(59,130,246,.08);border-left:2px solid var(--color-horizon-blue);padding:8px 10px}.canvas-input,.message-input{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-md);box-sizing:border-box;color:#fff;font:inherit;font-size:13px;line-height:1.6;padding:12px 14px;resize:vertical;width:100%}.canvas-input:focus,.message-input:focus{border-color:var(--color-horizon-blue);outline:none}.canvas-status{color:var(--color-slate-muted);display:flex;font-size:10px;justify-content:space-between}.assistance-label{color:#c4b5fd}.selected-sources{display:flex;flex-wrap:wrap;gap:6px;align-items:center;color:var(--color-slate-light);font-size:11px}.selected-sources strong{font-size:10px;text-transform:uppercase;color:var(--color-slate-muted)}.selected-sources span{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);border-radius:99px;color:#bae6fd;padding:4px 7px}.selected-sources button{background:none;border:0;color:#7dd3fc;cursor:pointer;font-size:14px;padding:0 3px}.support-card{background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.35);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:10px;padding:14px}.support-card-heading{align-items:center;color:#ddd6fe;display:flex;font-size:11px;font-weight:700;justify-content:space-between;text-transform:uppercase}.support-card-heading small{color:#c4b5fd;font-size:9px;font-weight:500;text-transform:none}.support-card p{color:#ede9fe;font-size:12.5px;line-height:1.55;margin:0;white-space:pre-wrap}.support-card>div:last-child,.canvas-actions,.canvas-actions>div{align-items:center;display:flex;gap:8px}.canvas-actions{justify-content:space-between}.btn-link{background:none;border:0;color:#c4b5fd;cursor:pointer;font-size:11px;text-decoration:underline}.dialogue-heading{border-bottom:1px solid var(--color-graphite-border);padding:15px 20px}.dialogue-title{color:#fff;font-size:14px;font-weight:700}.messages-container{display:flex;flex-direction:column;gap:14px;max-height:300px;min-height:190px;overflow-y:auto;padding:20px}.welcome-card{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-md);color:var(--color-slate-light);line-height:1.6;margin:auto;max-width:600px;padding:18px}.welcome-card strong{color:#fff}.welcome-card p{font-size:12px;margin:7px 0 0}.message{align-items:flex-start;display:flex;gap:10px;max-width:86%}.message.user{align-self:flex-end;flex-direction:row-reverse}.msg-avatar{align-items:center;background:linear-gradient(135deg,var(--color-horizon-blue),var(--color-aurora));border-radius:50%;color:#fff;display:flex;flex:0 0 28px;font-size:10px;font-weight:700;height:28px;justify-content:center}.user .msg-avatar{background:linear-gradient(135deg,#059669,#0ea5e9)}.msg-bubble{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:4px 14px 14px 14px;color:#e2e8f0;font-size:12px;line-height:1.55;padding:10px 13px}.user .msg-bubble{background:rgba(59,130,246,.13);border-color:rgba(59,130,246,.3);border-radius:14px 4px 14px 14px}.msg-bubble p{margin:0;white-space:pre-wrap}.typing{color:var(--color-slate-muted);font-style:italic}.guardrail-label,.hint-label{color:var(--color-amber);display:block;font-size:10px;font-weight:700;margin-bottom:5px;text-transform:uppercase}.hint-label{color:var(--color-horizon-bright);margin:7px 0 0}.error-banner{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:var(--radius-sm);color:#fca5a5;font-size:12px;margin:0 20px;padding:9px 12px}.input-area{border-top:1px solid var(--color-graphite-border);padding:15px 20px}.input-actions{display:flex;justify-content:space-between;gap:10px;margin-top:9px}.source-card{border-bottom:1px solid var(--color-graphite-border);display:flex;flex-direction:column;gap:8px;padding:0 0 16px}.source-card h2{color:#e2e8f0;font-size:13px;margin:0}.source-card p{color:var(--color-slate-muted);font-size:11.5px;line-height:1.5;margin:0}.btn-cite{background:none;border:1px solid var(--color-graphite-border);border-radius:var(--radius-xs);color:var(--color-horizon-bright);cursor:pointer;font-size:11px;font-weight:600;padding:6px 8px;text-align:left}.btn-cite:hover:not(:disabled){border-color:var(--color-horizon-blue)}.btn-cite:disabled{cursor:not-allowed;opacity:.5}.source-empty{border:1px dashed var(--color-graphite-border);color:var(--color-slate-muted);font-size:12px;line-height:1.5;padding:14px}.loading-view,.empty-view{align-items:center;background:var(--color-obsidian);color:var(--color-slate-light);display:flex;flex-direction:column;gap:14px;justify-content:center;min-height:calc(100vh - 56px);padding:24px;text-align:center}.empty-view h1{font-size:24px}.empty-view p{max-width:520px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:32px;width:32px}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:1160px){.workspace-layout{grid-template-columns:240px minmax(0,1fr)}.evidence-col{display:none}}@media(max-width:800px){.workspace-layout{display:flex;flex-direction:column}.context-col{border-bottom:1px solid var(--color-graphite-border);border-right:none}.canvas-panel,.dialogue-panel{margin:15px}.canvas-steps{grid-template-columns:repeat(5,130px)}.workspace-header{padding:18px 16px}.support-card>div:last-child,.canvas-actions,.canvas-actions>div{align-items:stretch;flex-direction:column}.canvas-actions .btn{width:100%}}@media(max-width:520px){.section-editor-heading{flex-direction:column;gap:4px}.messages-container,.input-area,.dialogue-heading{padding-left:14px;padding-right:14px}.message{max-width:94%}.input-actions{flex-direction:column}.input-actions .btn{width:100%}}
</style>
