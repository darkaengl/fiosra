<script>
  import { onDestroy, onMount } from 'svelte';
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
  let probes = $state([]);
  let evidenceSummary = $state({ pending_questions: 0, evidence_submitted: 0 });
  let isLoading = $state(true);
  let isBriefOpen = $state(false);
  let isQuickPromptOpen = $state(false);
  let isQuestionDrawerOpen = $state(false);
  let activeProbeId = $state('');
  let probeResponse = $state('');
  let probeNotice = $state('');
  let isProbeBusy = $state(false);
  let error = $state('');
  let probeTimer;
  let currentProbe = $derived(activeProbe());

  const QUIET_PERIOD_MS = 5000;

  function sessionHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Fiosra-Session-Token': sessionAccessToken,
    };
  }

  function activeProbe() {
    return probes.find((probe) => probe.probe_id === activeProbeId) || probes[0] || null;
  }

  async function loadDocument() {
    const response = await fetch(`/learning-documents/sessions/${sessionId}`, { headers: sessionHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your long-form document could not be restored.'));
    learningDocument = await response.json();
    sessionStatus = learningDocument.status;
  }

  async function loadProbes() {
    if (!sessionId || sessionStatus !== 'active') return;
    const response = await fetch(`/learning-documents/sessions/${sessionId}/probes`, { headers: sessionHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your evidence questions could not be restored.'));
    const result = await response.json();
    probes = result.probes || [];
    evidenceSummary = result.evidence_summary || evidenceSummary;
    if (!activeProbeId && probes[0]) activeProbeId = probes[0].probe_id;
  }

  async function loadAssignment() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    assignmentId = params.get('assignment_id') || '';

    if (assignmentId) {
      const response = await fetch(`/assignments/${assignmentId}`);
      if (!response.ok) throw new Error(await responseError(response, 'The requested assignment could not be loaded.'));
      const found = await response.json();
      if (found.status === 'published') {
        assignment = found;
      } else {
        assignment = null;
      }
    } else if (courseId) {
      const response = await fetch(`/assignments?course_id=${encodeURIComponent(courseId)}&status=published`);
      if (response.ok) {
        const assignments = await response.json();
        const pub = assignments.filter((a) => a.status === 'published');
        assignment = pub[0] || null;
        assignmentId = assignment?.assignment_id || '';
      }
    }

    // Auto-discover active assignment across courses if neither assignment_id nor course_id was passed
    if (!assignment && !courseId) {
      try {
        const coursesRes = await fetch('/courses');
        if (coursesRes.ok) {
          const coursesList = await coursesRes.json();
          const courses = Array.isArray(coursesList) ? coursesList : coursesList.courses || [];
          for (const c of courses) {
            const cid = c.course_id || c.id;
            if (!cid) continue;
            const res = await fetch(`/assignments?course_id=${encodeURIComponent(cid)}&status=published`);
            if (res.ok) {
              const list = await res.json();
              const pubList = list.filter((a) => a.status === 'published');
              if (pubList.length > 0) {
                assignment = pubList[0];
                assignmentId = assignment.assignment_id;
                courseId = cid;
                break;
              }
            }
          }
        }
      } catch (err) {
        console.warn('Auto-discovering published assignment:', err);
      }
    }

    if (!assignment && !courseId) {
      try {
        const directRes = await fetch('/assignments');
        if (directRes.ok) {
          const allList = await directRes.json();
          const pubList = allList.filter((a) => a.status === 'published');
          if (pubList.length > 0) {
            assignment = pubList[0];
            assignmentId = assignment.assignment_id;
          }
        }
      } catch (err) {
        console.warn('Direct assignment fallback fetch:', err);
      }
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
    await loadProbes();
  }

  async function syncDocument(patch) {
    clearTimeout(probeTimer);
    const response = await fetch(`/learning-documents/sessions/${sessionId}`, {
      method: 'PUT',
      headers: sessionHeaders(),
      body: JSON.stringify(patch),
    });
    if (!response.ok) throw new Error(await responseError(response, 'This document could not be saved.'));
    learningDocument = await response.json();
    return learningDocument;
  }

  function scheduleProbeEvaluation(syncedDocument) {
    clearTimeout(probeTimer);
    if (sessionStatus !== 'active' || !syncedDocument?.changed_block_ids?.length) return;
    probeTimer = setTimeout(() => evaluateProbes(syncedDocument), QUIET_PERIOD_MS);
  }

  async function evaluateProbes(syncedDocument) {
    try {
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/evaluate`, {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify({
          document_revision: syncedDocument.document_revision,
          changed_block_ids: syncedDocument.changed_block_ids,
        }),
      });
      if (response.status === 409) return;
      if (!response.ok) throw new Error(await responseError(response, 'Your writing was saved, but its evidence question could not be checked.'));
      const result = await response.json();
      probes = result.pending || [];
      evidenceSummary = result.evidence_summary || evidenceSummary;
      if (result.created?.length) {
        activeProbeId = result.created[0].probe_id;
        probeNotice = 'A focused Socratic question is ready. It tests this paragraph’s reasoning, not your grade.';
      }
    } catch (err) {
      probeNotice = err.message || 'Your writing is saved. A question could not be checked right now.';
    }
  }

  function toggleQuestions() {
    if (isQuestionDrawerOpen) {
      isQuestionDrawerOpen = false;
    } else {
      const current = activeProbe();
      if (current) activeProbeId = current.probe_id;
      isQuestionDrawerOpen = true;
      probeNotice = '';
    }
  }

  function closeQuestions() {
    isQuestionDrawerOpen = false;
  }

  function openQuestions() {
    const current = activeProbe();
    if (current) activeProbeId = current.probe_id;
    isQuestionDrawerOpen = true;
    probeNotice = '';
  }

  async function changeProbe(probeId, action, body = null) {
    isProbeBusy = true;
    probeNotice = '';
    try {
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/${probeId}/${action}`, {
        method: 'POST',
        headers: sessionHeaders(),
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
      if (!response.ok) throw new Error(await responseError(response, 'This question could not be updated.'));
      const result = await response.json();
      probeNotice = result.message;
      probeResponse = '';
      await loadProbes();
      activeProbeId = probes[0]?.probe_id || '';
      if (!probes.length) isQuestionDrawerOpen = false;
    } catch (err) {
      probeNotice = err.message || 'This question could not be updated.';
    } finally {
      isProbeBusy = false;
    }
  }

  async function submitProbeResponse() {
    const probe = activeProbe();
    if (!probe || probeResponse.trim().length < 10) {
      probeNotice = 'Write at least a short explanation before saving your response.';
      return;
    }
    await changeProbe(probe.probe_id, 'responses', { response_text: probeResponse.trim() });
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

  onDestroy(() => clearTimeout(probeTimer));
</script>

<svelte:window onkeydown={(e) => {
  if (e.key === 'Escape') {
    if (isQuestionDrawerOpen) isQuestionDrawerOpen = false;
    if (isBriefOpen) isBriefOpen = false;
    if (isQuickPromptOpen) isQuickPromptOpen = false;
  }
}} />

{#if isLoading}
  <main class="loading-view">
    <div class="spinner"></div>
    <p>Opening your reasoning canvas…</p>
  </main>
{:else if error && !assignment}
  <main class="empty-view">
    <h1>Workspace unavailable</h1>
    <p>{error}</p>
    <div style="display: flex; gap: 12px; margin-top: 14px;">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Return to Timeline</a>
    </div>
  </main>
{:else if !assignment}
  <main class="empty-view">
    <h1>{courseId ? 'No published assignment in this course yet' : 'No active assignment selected'}</h1>
    <p>
      {courseId 
        ? 'Your instructor has not published an active reasoning assignment for this course yet.' 
        : 'Open an active milestone from your enrolled courses to start a protected reasoning session.'}
    </p>
    <div style="display: flex; gap: 12px; margin-top: 14px;">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Browse Student Timeline</a>
    </div>
  </main>
{:else}
  <main class="document-workspace">
    <!-- Top Assignment Bar -->
    <header class="assignment-bar">
      <div class="assignment-identity">
        <span class="eyebrow">Reasoning Canvas</span>
        <h1>{assignment.title || 'Reasoning Assignment'}</h1>
        <span class="document-type">Claim–Evidence–Reasoning</span>
      </div>

      <div class="assignment-actions">
        <button class="quiet-control" onclick={() => isQuickPromptOpen = !isQuickPromptOpen}>
          {isQuickPromptOpen ? 'Hide Prompt ▲' : 'Prompt & Sources ▼'}
        </button>
        <button class="quiet-control" onclick={() => isBriefOpen = true}>
          Full Brief
        </button>

        {#if probes.length}
          <button class="question-control" onclick={toggleQuestions} aria-label={`Toggle ${probes.length} evidence question${probes.length === 1 ? '' : 's'}`}>
            Socratic Probes <span>{probes.length}</span>
          </button>
        {/if}

        <a class="trace-control" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`}>
          Trace ↗
        </a>

        <span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span>
      </div>
    </header>

    <!-- Collapsible Quick Prompt & Sources Accordion -->
    {#if isQuickPromptOpen}
      <section class="quick-prompt-banner">
        <div class="prompt-col">
          <span class="banner-tag">Assignment Prompt</span>
          <p class="prompt-text">{assignment.prompt}</p>
        </div>
        {#if assignment.grounding_sources?.length}
          <div class="sources-col">
            <span class="banner-tag">Approved Evidence Sources</span>
            <div class="source-chips">
              {#each assignment.grounding_sources as source}
                <div class="source-chip" title={source.excerpt || ''}>
                  📜 {source.title || 'Course Material'}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </section>
    {/if}

    {#if error}<p class="error-banner" role="alert">{error}</p>{/if}
    {#if probeNotice && !isQuestionDrawerOpen}
      <button class="probe-notice" onclick={openQuestions}>
        💡 {probeNotice}
      </button>
    {/if}

    <!-- Long-Form Document Editor -->
    {#if learningDocument}
      <LongFormDocumentEditor
        {learningDocument}
        {assignment}
        disabled={sessionStatus !== 'active'}
        onSync={syncDocument}
        onSynced={scheduleProbeEvaluation}
        onOpenQuestions={toggleQuestions}
        probeCount={probes.length}
      />
    {/if}

    <!-- Backdrop for Question Drawer -->
    {#if isQuestionDrawerOpen}
      <div class="drawer-backdrop" onclick={closeQuestions} aria-hidden="true"></div>
    {/if}

    <!-- Socratic Questions Side Drawer -->
    <aside class:open={isQuestionDrawerOpen} class="question-drawer" aria-label="Evidence and questions" aria-hidden={!isQuestionDrawerOpen}>
      <header>
        <div>
          <span class="eyebrow">Socratic Inquiry</span>
          <h2>Evidence & Probes</h2>
        </div>
        <button class="close-btn" onclick={closeQuestions} aria-label="Close evidence questions" title="Close Panel (Esc)">✕</button>
      </header>

      {#if currentProbe}
        <div class="question-context">
          <span>{currentProbe.section_label || 'Active paragraph'}</span>
          <strong>{currentProbe.focus_type.replace(/_/g, ' ')}</strong>
        </div>
        <p class="question-copy">{currentProbe.question}</p>
        <div class="evidence-explainer">
          <p>This question tests the causal reasoning in your saved paragraph. Your response is captured as student-authored evidence for your instructor to review.</p>
        </div>

        <label for="probe-response">Your Reasoning Explanation</label>
        <textarea 
          id="probe-response" 
          bind:value={probeResponse} 
          disabled={isProbeBusy} 
          placeholder="Explain your causal reasoning in your own words. This is preserved as distinct student evidence."
        ></textarea>

        {#if probeNotice}<p class="probe-message" role="status">{probeNotice}</p>{/if}

        <div class="question-actions">
          <button class="primary-question-action" onclick={submitProbeResponse} disabled={isProbeBusy || probeResponse.trim().length < 10}>
            {isProbeBusy ? 'Saving…' : 'Save Response (Evidence)'}
          </button>
          <button class="secondary-btn" onclick={() => changeProbe(currentProbe.probe_id, 'defer')} disabled={isProbeBusy}>
            Later
          </button>
          <button class="dismiss-btn" onclick={() => changeProbe(currentProbe.probe_id, 'dismiss')} disabled={isProbeBusy}>
            Dismiss
          </button>
        </div>
      {:else}
        <div class="empty-questions">
          <h3>No Open Questions</h3>
          <p>Continue writing. When a saved paragraph contains reasoning worth testing, a targeted Socratic probe will appear here without interrupting your work.</p>
          {#if evidenceSummary.evidence_submitted}
            <span class="evidence-submitted-badge">✓ {evidenceSummary.evidence_submitted} evidence response{evidenceSummary.evidence_submitted === 1 ? '' : 's'} recorded</span>
          {/if}
        </div>
      {/if}

      <div class="drawer-footer">
        <button class="return-canvas-btn" onclick={closeQuestions}>✕ Close Panel (Esc)</button>
      </div>
    </aside>
  </main>

  <!-- Full Assignment Brief Modal -->
  {#if isBriefOpen}
    <div class="brief-overlay" role="presentation" onclick={() => isBriefOpen = false}>
      <dialog class="brief-dialog" open aria-label="Assignment brief" onclick={(event) => event.stopPropagation()} onkeydown={(event) => { if (event.key === 'Escape') isBriefOpen = false; }}>
        <header>
          <div>
            <div class="eyebrow">Assignment Specification</div>
            <h2>{assignment.title || 'Reasoning Assignment'}</h2>
          </div>
          <button class="close-btn" onclick={() => isBriefOpen = false} aria-label="Close assignment brief">✕</button>
        </header>

        <div class="brief-content">
          <div class="brief-section">
            <h3>Prompt & Task</h3>
            <p class="brief-prompt">{assignment.prompt}</p>
          </div>

          <div class="brief-grid">
            <div class="brief-card">
              <h3>Target Knowledge Components</h3>
              <div class="kc-list">
                {#each assignment.target_kcs || [] as kc}
                  <code class="kc-tag">{kc}</code>
                {:else}
                  <p class="empty-text">No target KCs specified.</p>
                {/each}
              </div>
            </div>

            <div class="brief-card">
              <h3>Approved Course Sources ({assignment.grounding_sources?.length || 0})</h3>
              <div class="sources-list-mini">
                {#each assignment.grounding_sources || [] as source}
                  <div class="source-item-mini">
                    <strong>📜 {source.title || 'Course Evidence'}</strong>
                    <span>{source.excerpt || ''}</span>
                  </div>
                {:else}
                  <p class="empty-text">No primary source excerpts attached.</p>
                {/each}
              </div>
            </div>
          </div>
        </div>

        <footer>
          <span>Socratic questions test understanding and capture reviewable evidence; AI never writes answers or grades.</span>
          <button class="btn btn-primary" onclick={() => isBriefOpen = false}>Return to Canvas</button>
        </footer>
      </dialog>
    </div>
  {/if}
{/if}

<style>
  .document-workspace {
    background: var(--color-obsidian);
    color: var(--color-slate-bright);
    min-height: calc(100vh - 56px);
    padding: 0 clamp(16px, 4vw, 48px) 60px;
    transition: background 0.2s ease;
  }

  .assignment-bar {
    align-items: center;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    gap: 16px;
    justify-content: space-between;
    min-height: 72px;
    padding: 12px 0;
  }

  .assignment-identity {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .eyebrow {
    color: var(--color-horizon-blue);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    text-transform: uppercase;
  }

  .assignment-identity h1 {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .document-type {
    color: var(--color-slate-muted);
    font-size: 11px;
    font-weight: 600;
  }

  .assignment-actions {
    align-items: center;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .quiet-control, .trace-control {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 11px;
    font-weight: 600;
    padding: 6px 11px;
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .quiet-control:hover, .trace-control:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }

  .question-control {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.35);
    border-radius: var(--radius-sm);
    color: #8b5cf6;
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 11px;
    font-weight: 700;
    padding: 6px 11px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .question-control span {
    background: #8b5cf6;
    color: #fff;
    border-radius: 99px;
    padding: 1px 6px;
    font-size: 10px;
  }

  .session-badge {
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: 99px;
    color: var(--color-signal-green);
    font-size: 10px;
    font-weight: 700;
    padding: 4px 10px;
    text-transform: capitalize;
  }

  .session-badge.submitted {
    background: var(--color-amber-bg);
    border-color: rgba(217, 119, 6, 0.25);
    color: var(--color-amber);
  }

  /* Quick Prompt Banner */
  .quick-prompt-banner {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 16px;
    margin-top: 14px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    box-shadow: var(--shadow-sm);
    animation: slideDown 0.15s ease-out;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .banner-tag {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-horizon-blue);
    display: block;
    margin-bottom: 6px;
  }

  .prompt-text {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-slate-bright);
  }

  .source-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .source-chip {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    font-size: 11px;
    color: var(--color-slate-bright);
    padding: 4px 8px;
    font-weight: 600;
  }

  .error-banner {
    background: var(--color-rose-bg);
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: var(--radius-sm);
    color: var(--color-rose);
    font-size: 12px;
    margin: 16px 0;
    padding: 10px 14px;
  }

  .probe-notice {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: var(--radius-sm);
    color: #8b5cf6;
    cursor: pointer;
    display: block;
    font: 600 13px var(--font-ui);
    margin: 14px 0 -4px;
    padding: 10px 14px;
    text-align: left;
    width: 100%;
    transition: all 0.15s ease;
  }

  .probe-notice:hover {
    background: rgba(139, 92, 246, 0.16);
  }

  /* Socratic Question Drawer */
  .question-drawer {
    background: var(--color-graphite-card, var(--color-graphite));
    border-left: 1px solid var(--color-graphite-border);
    box-shadow: -12px 0 40px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    gap: 16px;
    height: 100%;
    padding: 24px;
    position: fixed;
    right: 0;
    top: 0;
    transform: translateX(105%);
    transition: transform 0.24s ease;
    visibility: hidden;
    width: min(440px, 100vw);
    z-index: 70;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .question-drawer.open {
    transform: translateX(0);
    visibility: visible;
  }

  .question-drawer header {
    align-items: flex-start;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    justify-content: space-between;
    padding-bottom: 14px;
  }

  .question-drawer h2 {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    margin: 4px 0 0;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle);
    font-size: 16px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: var(--radius-xs);
  }
  .close-btn:hover {
    color: var(--color-heading);
    background: var(--color-graphite-hover);
  }

  .question-context {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .question-context span {
    color: var(--color-slate-muted);
    font-size: 12px;
  }

  .question-context strong {
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.28);
    border-radius: 99px;
    color: #8b5cf6;
    font-size: 10px;
    padding: 2px 8px;
    text-transform: capitalize;
  }

  .question-copy {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 17px;
    line-height: 1.5;
    margin: 0;
    font-weight: 600;
  }

  .evidence-explainer {
    background: var(--color-bone-muted);
    border-left: 3px solid var(--color-aurora);
    padding: 10px 12px;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  }

  .evidence-explainer p {
    margin: 0;
    font-size: 11px;
    color: var(--color-slate-light);
    line-height: 1.45;
  }

  .question-drawer label {
    color: var(--color-heading);
    font-size: 12px;
    font-weight: 700;
    margin-top: 4px;
  }

  .question-drawer textarea {
    background: var(--input-bg, var(--color-graphite));
    border: 1px solid var(--input-border, var(--color-graphite-border));
    border-radius: var(--radius-sm);
    color: var(--color-slate-bright);
    font: 14px/1.55 var(--font-ui);
    min-height: 140px;
    outline: none;
    padding: 12px;
    resize: vertical;
    box-sizing: border-box;
    width: 100%;
  }

  .question-drawer textarea:focus {
    border-color: var(--color-horizon-blue);
    box-shadow: 0 0 0 2px var(--color-horizon-glow);
  }

  .probe-message {
    color: var(--color-horizon-blue);
    font-size: 12px;
    line-height: 1.4;
    margin: 0;
  }

  .question-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .primary-question-action {
    background: var(--color-horizon-blue);
    border: 1px solid var(--color-horizon-bright);
    border-radius: var(--radius-sm);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    padding: 8px 12px;
    cursor: pointer;
    flex: 1;
  }
  .primary-question-action:hover:not(:disabled) {
    background: var(--color-horizon-bright);
  }

  .secondary-btn {
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    font-size: 12px;
    font-weight: 600;
    padding: 8px 12px;
    cursor: pointer;
  }
  .secondary-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }

  .dismiss-btn {
    background: transparent;
    border: 1px solid transparent;
    color: var(--color-slate-subtle);
    font-size: 11px;
    font-weight: 600;
    padding: 8px 10px;
    cursor: pointer;
  }
  .dismiss-btn:hover:not(:disabled) {
    color: var(--color-amber);
  }

  .empty-questions {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 18px;
    text-align: center;
  }

  .empty-questions h3 {
    color: var(--color-heading);
    font-size: 15px;
    margin: 0 0 6px;
  }

  .empty-questions p {
    color: var(--color-slate-muted);
    font-size: 12px;
    line-height: 1.5;
    margin: 0;
  }

  .evidence-submitted-badge {
    color: var(--color-signal-green);
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    margin-top: 12px;
  }

  .drawer-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(2px);
    z-index: 69;
    animation: fadeIn 0.15s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .drawer-footer {
    margin-top: auto;
    padding-top: 16px;
    border-top: 1px solid var(--color-graphite-border);
    display: flex;
    justify-content: flex-end;
  }

  .return-canvas-btn {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    font-size: 12px;
    font-weight: 600;
    padding: 7px 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .return-canvas-btn:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }

  /* Brief Modal */
  .brief-overlay {
    align-items: center;
    background: var(--modal-overlay-bg, rgba(25, 28, 33, 0.6));
    backdrop-filter: blur(4px);
    display: flex;
    inset: 0;
    justify-content: center;
    padding: 24px;
    position: fixed;
    z-index: 80;
  }

  .brief-dialog {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    max-width: 800px;
    padding: 24px;
    width: min(100%, 800px);
    color: var(--color-slate-bright);
  }

  .brief-dialog header {
    align-items: flex-start;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    justify-content: space-between;
    padding-bottom: 14px;
  }

  .brief-dialog h2 {
    color: var(--color-heading);
    font-size: 20px;
    margin: 4px 0 0;
  }

  .brief-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin: 18px 0;
    max-height: 60vh;
    overflow-y: auto;
  }

  .brief-prompt {
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
  }

  .brief-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: 1fr 1.2fr;
  }

  .brief-card {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .brief-card h3 {
    margin: 0;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
  }

  .kc-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .kc-tag {
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    padding: 2px 6px;
    border-radius: var(--radius-xs);
    font-size: 11px;
    color: var(--color-horizon-blue);
  }

  .sources-list-mini {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .source-item-mini strong {
    display: block;
    font-size: 12px;
    color: var(--color-heading);
  }

  .source-item-mini span {
    font-size: 11px;
    color: var(--color-slate-muted);
    line-height: 1.4;
    display: block;
  }

  .brief-dialog footer {
    align-items: center;
    border-top: 1px solid var(--color-graphite-border);
    color: var(--color-slate-muted);
    display: flex;
    font-size: 11px;
    gap: 14px;
    justify-content: space-between;
    padding-top: 16px;
  }

  /* Empty / Loading Views */
  .loading-view, .empty-view {
    align-items: center;
    background: var(--color-obsidian);
    color: var(--color-slate-light);
    display: flex;
    flex-direction: column;
    gap: 14px;
    justify-content: center;
    min-height: calc(100vh - 56px);
    padding: 24px;
    text-align: center;
  }

  .empty-view h1 {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 24px;
    margin: 0;
  }

  .empty-view p {
    color: var(--color-slate-light);
    max-width: 520px;
    line-height: 1.5;
    margin: 0;
  }

  .spinner {
    animation: spin 0.8s linear infinite;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-radius: 50%;
    border-top-color: var(--color-horizon-blue);
    height: 32px;
    width: 32px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 780px) {
    .document-workspace { padding: 0 14px 40px; }
    .assignment-bar { align-items: flex-start; flex-direction: column; gap: 10px; }
    .quick-prompt-banner { grid-template-columns: 1fr; }
    .brief-grid { grid-template-columns: 1fr; }
    .question-drawer { width: 100%; }
  }
</style>
