<script>
  import { onMount } from 'svelte';
  import LongFormDocumentEditor from '../lib/LongFormDocumentEditor.svelte';
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
  let studentId = $state('');
  let sessionId = $state('');
  let sessionAccessToken = $state('');
  let sessionStatus = $state('active');
  let learningDocument = $state(null);
  let isLoading = $state(true);
  let isBriefOpen = $state(false);
  let error = $state('');

  function sessionHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Fiosra-Session-Token': sessionAccessToken,
    };
  }

  async function loadDocument() {
    const response = await fetch(`/learning-documents/sessions/${sessionId}`, { headers: sessionHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your long-form document could not be restored.'));
    learningDocument = await response.json();
    sessionStatus = learningDocument.status;
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
    const persistedAccessToken = persistedSessionId
      ? localStorage.getItem(sessionAccessTokenStorageKey(persistedSessionId))
      : '';

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

    await loadDocument();
  }

  async function syncDocument(patch) {
    const response = await fetch(`/learning-documents/sessions/${sessionId}`, {
      method: 'PUT',
      headers: sessionHeaders(),
      body: JSON.stringify(patch),
    });
    if (!response.ok) throw new Error(await responseError(response, 'This document could not be saved.'));
    learningDocument = await response.json();
    return learningDocument;
  }

  onMount(async () => {
    try {
      await loadAssignment();
    } catch (err) {
      error = err.message || 'The long-form learning workspace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

{#if isLoading}
  <main class="loading-view"><div class="spinner"></div><p>Opening your long-form writing workspace…</p></main>
{:else if error && !assignment}
  <main class="empty-view"><h1>Workspace unavailable</h1><p>{error}</p><a class="btn btn-primary" href="#/courses">Return to courses</a></main>
{:else if !assignment}
  <main class="empty-view"><h1>No published assignment selected</h1><p>Open a published assignment from a curriculum module to start a protected reasoning session.</p><a class="btn btn-primary" href="#/courses">Choose a course</a></main>
{:else}
  <main class="document-workspace">
    <header class="assignment-bar">
      <div class="assignment-identity">
        <span class="eyebrow">Active writing</span>
        <h1>{assignment.title || 'Reasoning assignment'}</h1>
        <span class="document-type">Long-form document</span>
      </div>
      <div class="assignment-actions">
        <button class="quiet-control" onclick={() => isBriefOpen = true}>View brief</button>
        <span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span>
      </div>
    </header>

    <section class="workspace-intro">
      <div><span class="eyebrow">Student writing space</span><h2>Build your argument in one document.</h2><p>Use headings to organize your ideas. There is no fixed page or essay limit; your work is saved as individual document blocks.</p></div>
      <a class="trace-link" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`}>View reasoning trace ↗</a>
    </section>

    {#if error}<p class="error-banner" role="alert">{error}</p>{/if}
    {#if learningDocument}
      <LongFormDocumentEditor
        {learningDocument}
        disabled={sessionStatus !== 'active'}
        onSync={syncDocument}
      />
    {/if}
  </main>

  {#if isBriefOpen}
    <div class="brief-overlay" role="presentation" onclick={() => isBriefOpen = false}>
      <dialog class="brief-dialog" open aria-label="Assignment brief" onclick={(event) => event.stopPropagation()} onkeydown={(event) => { if (event.key === 'Escape') isBriefOpen = false; }}>
        <header><div><div class="eyebrow">Assignment brief</div><h2>{assignment.title || 'Reasoning assignment'}</h2></div><button onclick={() => isBriefOpen = false} aria-label="Close assignment brief">×</button></header>
        <p class="brief-prompt">{assignment.prompt}</p>
        <div class="brief-grid"><div><h3>Target knowledge components</h3>{#each assignment.target_kcs || [] as kc}<code>{kc}</code>{/each}</div><div><h3>Approved sources</h3>{#each assignment.grounding_sources || [] as source}<p><strong>{source.title || 'Course material'}</strong><span>{source.excerpt || ''}</span></p>{:else}<p>No source excerpts are available.</p>{/each}</div></div>
        <footer><span>Writing support and evidence probes are introduced only through explicitly reviewed, traceable controls.</span><button class="btn btn-primary" onclick={() => isBriefOpen = false}>Return to writing</button></footer>
      </dialog>
    </div>
  {/if}
{/if}

<style>
  .document-workspace{background:var(--color-obsidian);color:var(--color-slate-bright);min-height:calc(100vh - 56px);padding:0 clamp(18px,5vw,76px) 70px}.assignment-bar{align-items:center;border-bottom:1px solid var(--color-graphite-border);display:flex;gap:18px;justify-content:space-between;min-height:82px}.assignment-identity{align-items:baseline;display:flex;gap:11px;min-width:0}.eyebrow{color:var(--color-slate-muted);font-size:10px;font-weight:700;letter-spacing:.55px;text-transform:uppercase}.assignment-identity h1{color:#fff;font-family:var(--font-brand);font-size:16px;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.document-type{color:var(--color-horizon-bright);font-size:11px;font-weight:700;white-space:nowrap}.assignment-actions{align-items:center;display:flex;gap:8px}.quiet-control{background:transparent;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-light);cursor:pointer;font-size:11px;font-weight:700;padding:8px 10px}.quiet-control:hover{border-color:var(--color-horizon-bright);color:#fff}.session-badge{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.25);border-radius:99px;color:#34d399;font-size:10px;font-weight:700;padding:5px 9px;text-transform:capitalize}.session-badge.submitted{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.25);color:var(--color-amber)}.workspace-intro{align-items:flex-end;display:flex;gap:25px;justify-content:space-between;margin:clamp(28px,6vh,64px) auto 0;max-width:920px}.workspace-intro h2{color:#fff;font-family:var(--font-brand);font-size:clamp(27px,3.6vw,42px);letter-spacing:-.7px;margin:6px 0 8px}.workspace-intro p{color:var(--color-slate-light);font-size:14px;line-height:1.6;margin:0;max-width:655px}.trace-link{border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:#bae6fd;flex:0 0 auto;font-size:11px;font-weight:700;padding:9px 11px;text-decoration:none}.trace-link:hover{border-color:var(--color-horizon-blue);color:#fff}.error-banner{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:var(--radius-sm);color:#fca5a5;font-size:12px;margin:20px auto 0;max-width:920px;padding:10px 12px}.brief-overlay{align-items:center;background:rgba(2,6,23,.75);display:flex;inset:0;justify-content:center;padding:24px;position:fixed;z-index:30}.brief-dialog{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);box-shadow:0 24px 70px rgba(0,0,0,.5);max-width:820px;padding:24px;width:min(100%,820px)}.brief-dialog header{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;padding-bottom:14px}.brief-dialog h2{color:#fff;font-size:20px;margin:4px 0 0}.brief-dialog header button{background:none;border:0;color:#94a3b8;cursor:pointer;font-size:25px;line-height:1}.brief-prompt{color:#e2e8f0;font-size:14px;line-height:1.65;margin:18px 0}.brief-grid{display:grid;gap:15px;grid-template-columns:.8fr 1.2fr}.brief-grid>div{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:flex;flex-direction:column;gap:7px;padding:13px}.brief-grid h3{color:#e2e8f0;font-size:11px;letter-spacing:.35px;margin:0;text-transform:uppercase}.brief-grid code{color:#c4b5fd;font-size:10px;overflow-wrap:anywhere}.brief-grid p{color:#94a3b8;font-size:11px;line-height:1.4;margin:0}.brief-grid p strong{color:#bae6fd;display:block;font-size:11px}.brief-grid p span{display:block;margin-top:3px}.brief-dialog footer{align-items:center;color:#94a3b8;display:flex;font-size:11px;gap:14px;justify-content:space-between;margin-top:17px}.loading-view,.empty-view{align-items:center;background:var(--color-obsidian);color:var(--color-slate-light);display:flex;flex-direction:column;gap:14px;justify-content:center;min-height:calc(100vh - 56px);padding:24px;text-align:center}.empty-view h1{color:#fff;font-family:var(--font-brand);font-size:24px}.empty-view p{max-width:520px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:32px;width:32px}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:780px){.document-workspace{padding:0 16px 56px}.assignment-bar{align-items:flex-start;flex-direction:column;gap:10px;padding:14px 0}.assignment-identity{align-items:flex-start;flex-wrap:wrap}.workspace-intro{align-items:flex-start;flex-direction:column;margin-top:30px}.brief-grid{grid-template-columns:1fr}.brief-dialog footer{align-items:stretch;flex-direction:column}.brief-dialog footer .btn{width:100%}}@media(max-width:480px){.assignment-actions{width:100%}.quiet-control{flex:1}.workspace-intro h2{font-size:29px}}
</style>
