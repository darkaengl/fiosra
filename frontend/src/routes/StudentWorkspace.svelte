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
  let sessionEvents = $state([]);
  let documentHeadings = $state([]);
  let isLoading = $state(true);

  // Sidebar and Panel Controls
  let isSidebarOpen = $state(true);
  let activeSidebarTab = $state('scope'); // 'scope' | 'outline' | 'trace'
  let isTutorPanelOpen = $state(false);
  let activeProbeId = $state('');
  let probeResponse = $state('');
  let probeNotice = $state('');
  let isProbeBusy = $state(false);
  let sourceSearchQuery = $state('');
  let error = $state('');
  let probeTimer;
  let editorRef = $state(null);

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

  async function loadSessionEvents() {
    if (!sessionId) return;
    try {
      const response = await fetch(`/events/session/${sessionId}`, { headers: sessionHeaders() });
      if (response.ok) {
        const data = await response.json();
        sessionEvents = data.events || [];
      }
    } catch (err) {
      console.warn('Loading session events for sidebar trace:', err);
    }
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
    await loadSessionEvents();
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
        probeNotice = 'A Socratic probe is ready. It tests this paragraph’s reasoning.';
        isTutorPanelOpen = true;
      }
      await loadSessionEvents();
    } catch (err) {
      probeNotice = err.message || 'Your writing is saved. A question could not be checked right now.';
    }
  }

  function toggleTutorPanel() {
    isTutorPanelOpen = !isTutorPanelOpen;
    if (isTutorPanelOpen) {
      const current = activeProbe();
      if (current) activeProbeId = current.probe_id;
      probeNotice = '';
    }
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
      await loadSessionEvents();
      activeProbeId = probes[0]?.probe_id || '';
      if (!probes.length) isTutorPanelOpen = false;
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

  function insertSourceFromSidebar(source) {
    if (editorRef?.insertSourceQuote) {
      editorRef.insertSourceQuote(source);
    }
  }

  function addSectionFromSidebar(type) {
    if (editorRef?.insertWritingFrame) {
      editorRef.insertWritingFrame(type);
    }
  }

  function handleHeadingJump(pos) {
    if (editorRef?.scrollToHeading) {
      editorRef.scrollToHeading(pos);
    }
  }

  let filteredSources = $derived(
    (assignment?.grounding_sources || []).filter((s) => {
      if (!sourceSearchQuery) return true;
      const q = sourceSearchQuery.toLowerCase();
      return (s.title || '').toLowerCase().includes(q) || (s.excerpt || '').toLowerCase().includes(q);
    })
  );

  onMount(async () => {
    try {
      await loadAssignment();
    } catch (err) {
      error = err.message || 'The reasoning workspace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });

  onDestroy(() => clearTimeout(probeTimer));
</script>

<svelte:window onkeydown={(e) => {
  if (e.key === 'Escape') {
    if (isTutorPanelOpen) isTutorPanelOpen = false;
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
  <div class="workspace-viewport">
    <!-- Top Control Bar -->
    <header class="workspace-topbar">
      <div class="topbar-left">
        <button 
          class="sidebar-toggle-btn" 
          class:active={isSidebarOpen}
          onclick={() => isSidebarOpen = !isSidebarOpen}
          title="Toggle Navigation & Learning Context Sidebar"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          <span>{isSidebarOpen ? 'Hide Sidebar' : 'Sidebar'}</span>
        </button>

        <div class="assignment-headline">
          <span class="eyebrow">Reasoning Milestone</span>
          <h1>{assignment.title || 'Reasoning Assignment'}</h1>
        </div>
      </div>

      <div class="topbar-right">
        <button 
          class="tutor-toggle-btn" 
          class:active={isTutorPanelOpen}
          onclick={toggleTutorPanel}
          title="Toggle Socratic Inquiry & Bounded Probes"
        >
          <span class="probe-dot" class:has-probes={probes.length > 0}></span>
          <span>Socratic Probes</span>
          {#if probes.length > 0}
            <span class="probe-count-pill">{probes.length}</span>
          {/if}
        </button>

        <span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span>
      </div>
    </header>

    <!-- 3-Zone Workspace Layout Container -->
    <div class="workspace-grid" class:sidebar-closed={!isSidebarOpen} class:tutor-open={isTutorPanelOpen}>
      
      <!-- ZONE 1: LEFT SIDEBAR WITH VERTICAL NAVIGATION -->
      {#if isSidebarOpen}
        <aside class="workspace-sidebar" aria-label="Learning Materials and Navigation Sidebar">
          <!-- Vertically Stacked Navigation Switcher -->
          <div class="sidebar-nav-stack" role="tablist">
            <button 
              class="nav-item-btn" 
              class:active={activeSidebarTab === 'scope'}
              onclick={() => activeSidebarTab = 'scope'}
              role="tab"
              aria-selected={activeSidebarTab === 'scope'}
            >
              <div class="nav-item-left">
                <span class="nav-icon">📋</span>
                <span class="nav-title">Scope & Evidence</span>
              </div>
              <span class="nav-badge">{assignment.grounding_sources?.length || 0} sources</span>
            </button>

            <button 
              class="nav-item-btn" 
              class:active={activeSidebarTab === 'outline'}
              onclick={() => activeSidebarTab = 'outline'}
              role="tab"
              aria-selected={activeSidebarTab === 'outline'}
            >
              <div class="nav-item-left">
                <span class="nav-icon">📑</span>
                <span class="nav-title">Document Outline</span>
              </div>
              <span class="nav-badge">{documentHeadings.length} sec</span>
            </button>

            <button 
              class="nav-item-btn" 
              class:active={activeSidebarTab === 'trace'}
              onclick={() => activeSidebarTab = 'trace'}
              role="tab"
              aria-selected={activeSidebarTab === 'trace'}
            >
              <div class="nav-item-left">
                <span class="nav-icon">⏱️</span>
                <span class="nav-title">Reasoning Trace</span>
              </div>
              <span class="nav-badge">{sessionEvents.length} events</span>
            </button>
          </div>

          <!-- Active Sidebar View Body -->
          <div class="sidebar-tab-body">
            <!-- VIEW 1: CONSOLIDATED SCOPE & ALLOWED SOURCES -->
            {#if activeSidebarTab === 'scope'}
              <div class="tab-panel scope-panel">
                <div class="section-card">
                  <span class="card-eyebrow">Assignment Task</span>
                  <p class="prompt-text">{assignment.prompt}</p>
                </div>

                <div class="section-card">
                  <span class="card-eyebrow">Target Knowledge Components</span>
                  <div class="kc-pills">
                    {#each assignment.target_kcs || [] as kc}
                      <span class="kc-pill">{kc}</span>
                    {:else}
                      <p class="empty-text">No target KCs specified.</p>
                    {/each}
                  </div>
                </div>

                <div class="section-card sources-section">
                  <div class="sources-header-bar">
                    <span class="card-eyebrow">Approved Primary Sources ({assignment.grounding_sources?.length || 0})</span>
                  </div>
                  
                  <div class="source-search-box">
                    <input 
                      type="text" 
                      placeholder="Filter allowed sources..."
                      bind:value={sourceSearchQuery}
                      class="sidebar-search-input"
                    />
                  </div>

                  <div class="sources-stream">
                    {#each filteredSources as source}
                      <div class="source-evidence-card">
                        <div class="source-top">
                          <span class="source-tag">Primary Source</span>
                          <h6>{source.title || 'Course Material'}</h6>
                        </div>
                        <blockquote class="source-body">{source.excerpt || 'No excerpt available.'}</blockquote>
                        <div class="source-bottom">
                          <button class="cite-action-btn" onclick={() => insertSourceFromSidebar(source)}>
                            <span>+ Cite in Document</span>
                          </button>
                        </div>
                      </div>
                    {:else}
                      <div class="empty-state">
                        <p>No primary sources match your search.</p>
                      </div>
                    {/each}
                  </div>
                </div>
              </div>

            <!-- VIEW 2: DOCUMENT OUTLINE & SECTION STEPS (Migrated from toolbar) -->
            {:else if activeSidebarTab === 'outline'}
              <div class="tab-panel outline-panel">
                <div class="section-card">
                  <span class="card-eyebrow">Active Document Outline</span>
                  <p class="outline-hint">Click any heading to jump to that section in your draft.</p>
                  
                  <div class="headings-tree">
                    {#each documentHeadings as heading, i}
                      <button 
                        class="outline-tree-item level-{heading.level}"
                        onclick={() => handleHeadingJump(heading.pos)}
                      >
                        <span class="heading-num">{i + 1}</span>
                        <span class="heading-label">{heading.text}</span>
                      </button>
                    {:else}
                      <div class="empty-outline-box">
                        <p>No headings in document yet.</p>
                      </div>
                    {/each}
                  </div>
                </div>

                <div class="section-card">
                  <span class="card-eyebrow">+ Add Structured CER Section</span>
                  <div class="preset-grid">
                    <button class="preset-btn" onclick={() => addSectionFromSidebar('claim')}>
                      <span>🎯 Working Claim</span>
                    </button>
                    <button class="preset-btn" onclick={() => addSectionFromSidebar('evidence')}>
                      <span>📜 Source Observations</span>
                    </button>
                    <button class="preset-btn" onclick={() => addSectionFromSidebar('reasoning')}>
                      <span>⚡ Causal Mechanism</span>
                    </button>
                    <button class="preset-btn" onclick={() => addSectionFromSidebar('alternative')}>
                      <span>🔄 Alternative Explanation</span>
                    </button>
                    <button class="preset-btn" onclick={() => addSectionFromSidebar('reflection')}>
                      <span>🔍 Revision Reflection</span>
                    </button>
                  </div>
                </div>
              </div>

            <!-- VIEW 3: REASONING TRACE & LIVE PROVENANCE -->
            {:else if activeSidebarTab === 'trace'}
              <div class="tab-panel trace-panel">
                <div class="trace-header">
                  <div>
                    <span class="card-eyebrow">Session Audit Stream</span>
                    <span class="trace-count">{sessionEvents.length} recorded events</span>
                  </div>
                  <a class="deep-trace-link" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`}>
                    Full Trace ↗
                  </a>
                </div>

                <div class="trace-timeline">
                  {#each sessionEvents as ev}
                    <div class="trace-node">
                      <div class="node-dot"></div>
                      <div class="node-content">
                        <span class="node-type">{ev.event_type.replace(/_/g, ' ')}</span>
                        <span class="node-time">{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  {:else}
                    <div class="empty-state">
                      <p>No actions logged yet. Edits and probes will stream live here.</p>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </aside>
      {/if}

      <!-- ZONE 2: CENTER REASONING CANVAS -->
      <main class="canvas-main-area">
        {#if error}<p class="error-banner" role="alert">{error}</p>{/if}
        {#if probeNotice && !isTutorPanelOpen}
          <button class="probe-alert-bar" onclick={toggleTutorPanel}>
            💡 {probeNotice} (Click to open Socratic panel)
          </button>
        {/if}

        {#if learningDocument}
          <LongFormDocumentEditor
            bind:this={editorRef}
            {learningDocument}
            {assignment}
            disabled={sessionStatus !== 'active'}
            onSync={syncDocument}
            onSynced={scheduleProbeEvaluation}
            onOpenQuestions={toggleTutorPanel}
            onHeadingsChange={(h) => documentHeadings = h}
            probeCount={probes.length}
          />
        {/if}
      </main>

      <!-- ZONE 3: RIGHT SOCRATIC PROBE PANEL (Inline push-layout) -->
      {#if isTutorPanelOpen}
        <aside class="socratic-tutor-column" aria-label="Socratic Reasoning and Evidence Panel">
          <header class="tutor-header">
            <div>
              <span class="eyebrow">Socratic Inquiry</span>
              <h3>Evidence & Probes</h3>
            </div>
            <button class="close-panel-btn" onclick={() => isTutorPanelOpen = false} title="Close Panel (Esc)">✕</button>
          </header>

          <div class="tutor-body">
            {#if currentProbe}
              <div class="probe-card">
                <div class="probe-meta">
                  <span class="section-tag">{currentProbe.section_label || 'Active paragraph'}</span>
                  <span class="focus-pill">{currentProbe.focus_type.replace(/_/g, ' ')}</span>
                </div>

                <p class="probe-question">{currentProbe.question}</p>

                <div class="probe-pedagogy-tip">
                  <p>This question tests the causal reasoning in your saved paragraph. Your answer is captured as student evidence for evaluation.</p>
                </div>

                <label for="probe-input" class="probe-input-label">Your Reasoning Explanation</label>
                <textarea 
                  id="probe-input"
                  bind:value={probeResponse}
                  disabled={isProbeBusy}
                  placeholder="Explain your causal reasoning in your own words. This is preserved as distinct student evidence."
                  class="probe-textarea"
                ></textarea>

                {#if probeNotice}<p class="probe-status-msg" role="status">{probeNotice}</p>{/if}

                <div class="probe-actions">
                  <button class="save-evidence-btn" onclick={submitProbeResponse} disabled={isProbeBusy || probeResponse.trim().length < 10}>
                    {isProbeBusy ? 'Saving…' : 'Save Response (Evidence)'}
                  </button>
                  <button class="defer-btn" onclick={() => changeProbe(currentProbe.probe_id, 'defer')} disabled={isProbeBusy}>
                    Later
                  </button>
                  <button class="dismiss-btn" onclick={() => changeProbe(currentProbe.probe_id, 'dismiss')} disabled={isProbeBusy}>
                    Dismiss
                  </button>
                </div>
              </div>
            {:else}
              <div class="empty-probe-state">
                <h4>No Pending Probes</h4>
                <p>Continue writing in your document. When a paragraph contains reasoning worth testing, a targeted Socratic probe will appear here.</p>
                {#if evidenceSummary.evidence_submitted}
                  <span class="evidence-badge">✓ {evidenceSummary.evidence_submitted} evidence response{evidenceSummary.evidence_submitted === 1 ? '' : 's'} recorded</span>
                {/if}
              </div>
            {/if}
          </div>
        </aside>
      {/if}

    </div>
  </div>
{/if}

<style>
  .workspace-viewport {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 56px);
    background: var(--color-obsidian);
    overflow: hidden;
  }

  /* Top Control Bar */
  .workspace-topbar {
    background: var(--color-graphite);
    border-bottom: 1px solid var(--color-graphite-border);
    padding: 8px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 52px;
    flex-shrink: 0;
    z-index: 10;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
  }

  .sidebar-toggle-btn {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    font-size: 11px;
    font-weight: 700;
    padding: 6px 10px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .sidebar-toggle-btn:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }

  .sidebar-toggle-btn.active {
    background: rgba(217, 119, 6, 0.12);
    border-color: var(--color-horizon-blue);
    color: var(--color-horizon-blue);
  }

  .assignment-headline {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .eyebrow {
    font-size: 9px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--color-horizon-blue);
  }

  .assignment-headline h1 {
    margin: 0;
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .tutor-toggle-btn {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: var(--radius-sm);
    color: #8b5cf6;
    font-size: 11px;
    font-weight: 700;
    padding: 6px 11px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .tutor-toggle-btn:hover, .tutor-toggle-btn.active {
    background: rgba(139, 92, 246, 0.2);
    border-color: #8b5cf6;
  }

  .probe-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #8b5cf6;
  }

  .probe-dot.has-probes {
    animation: pulseGlow 2s infinite;
  }

  .probe-count-pill {
    background: #8b5cf6;
    color: #fff;
    border-radius: 99px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: 800;
  }

  .session-badge {
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: 99px;
    color: var(--color-signal-green);
    font-size: 10px;
    font-weight: 700;
    padding: 3px 9px;
    text-transform: capitalize;
  }

  .session-badge.submitted {
    background: var(--color-amber-bg);
    color: var(--color-amber);
    border-color: rgba(217, 119, 6, 0.25);
  }

  /* Main 3-Zone Workspace Grid */
  .workspace-grid {
    display: grid;
    grid-template-columns: 340px 1fr;
    flex: 1;
    min-height: 0;
    overflow: hidden;
    transition: all 0.2s ease;
  }

  .workspace-grid.sidebar-closed {
    grid-template-columns: 0px 1fr;
  }

  .workspace-grid.tutor-open {
    grid-template-columns: 340px 1fr 380px;
  }

  .workspace-grid.sidebar-closed.tutor-open {
    grid-template-columns: 0px 1fr 380px;
  }

  /* ZONE 1: LEFT SIDEBAR */
  .workspace-sidebar {
    background: var(--color-graphite);
    border-right: 1px solid var(--color-graphite-border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 5;
  }

  /* Vertical Navigation Menu */
  .sidebar-nav-stack {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    background: var(--color-bone-muted);
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .nav-item-btn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--radius-xs);
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 600;
    color: var(--color-slate-light);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.12s ease;
  }

  .nav-item-btn:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }

  .nav-item-btn.active {
    background: var(--color-graphite);
    border-color: var(--color-graphite-border);
    color: var(--color-heading);
    font-weight: 700;
    box-shadow: var(--shadow-sm);
  }

  .nav-item-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .nav-icon { font-size: 14px; }
  .nav-title { font-size: 12px; }

  .nav-badge {
    font-size: 10px;
    color: var(--color-slate-subtle);
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    padding: 1px 5px;
    border-radius: 99px;
  }

  .sidebar-tab-body {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .tab-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .section-card {
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .card-eyebrow {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
  }

  .prompt-text {
    margin: 0;
    font-size: 12px;
    line-height: 1.55;
    color: var(--color-slate-bright);
  }

  .kc-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .kc-pill {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    font-size: 10px;
    font-weight: 600;
    color: var(--color-horizon-blue);
    padding: 2px 6px;
  }

  /* Sources section inside scope view */
  .sources-header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .sidebar-search-input {
    width: 100%;
    background: var(--input-bg, var(--color-graphite));
    border: 1px solid var(--input-border, var(--color-graphite-border));
    border-radius: var(--radius-xs);
    padding: 6px 10px;
    font-size: 11px;
    color: var(--color-slate-bright);
    outline: none;
    box-sizing: border-box;
  }
  .sidebar-search-input:focus {
    border-color: var(--color-aurora);
  }

  .sources-stream {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 4px;
  }

  .source-evidence-card {
    background: var(--color-graphite-card, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .source-top {
    display: flex;
    align-items: baseline;
    gap: 6px;
  }

  .source-tag {
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    background: rgba(2, 132, 199, 0.1);
    color: var(--color-aurora);
    padding: 1px 4px;
    border-radius: 99px;
  }

  .source-top h6 {
    margin: 0;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .source-body {
    margin: 0;
    font-size: 11px;
    line-height: 1.45;
    color: var(--color-slate-light);
    background: var(--color-bone-muted);
    border-left: 2px solid var(--color-aurora);
    padding: 6px 8px;
    font-style: italic;
  }

  .cite-action-btn {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    color: var(--color-aurora);
    font-size: 10px;
    font-weight: 700;
    padding: 4px 8px;
    cursor: pointer;
    width: 100%;
  }
  .cite-action-btn:hover {
    background: var(--color-aurora);
    color: #fff;
    border-color: var(--color-aurora);
  }

  /* Outline View */
  .outline-hint {
    margin: 0;
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .headings-tree {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 4px;
  }

  .outline-tree-item {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    padding: 6px 8px;
    display: flex;
    align-items: baseline;
    gap: 8px;
    text-align: left;
    cursor: pointer;
    color: var(--color-slate-bright);
    font-size: 12px;
    transition: all 0.12s ease;
    width: 100%;
  }

  .outline-tree-item:hover {
    background: var(--color-graphite-hover);
    border-color: var(--color-horizon-blue);
    color: var(--color-horizon-blue);
  }

  .outline-tree-item.level-3 {
    margin-left: 14px;
    width: calc(100% - 14px);
    font-size: 11px;
    opacity: 0.85;
  }

  .heading-num {
    font-size: 10px;
    font-weight: 700;
    color: var(--color-horizon-blue);
    min-width: 14px;
  }

  .heading-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .empty-outline-box {
    text-align: center;
    padding: 12px 0;
    color: var(--color-slate-muted);
    font-size: 11px;
  }

  /* Outline Presets */
  .preset-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
  }

  .preset-btn {
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    padding: 8px 10px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-bright);
    cursor: pointer;
    transition: all 0.12s ease;
  }
  .preset-btn:hover {
    background: var(--color-graphite-hover);
    border-color: var(--color-horizon-blue);
    color: var(--color-horizon-blue);
  }

  /* Trace Timeline */
  .trace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .trace-count {
    font-size: 10px;
    color: var(--color-slate-muted);
    display: block;
  }

  .deep-trace-link {
    font-size: 11px;
    color: var(--color-horizon-blue);
    font-weight: 700;
    text-decoration: none;
  }
  .deep-trace-link:hover { text-decoration: underline; }

  .trace-timeline {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 6px;
  }

  .trace-node {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
  }

  .node-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--color-horizon-blue);
  }

  .node-content {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 11px;
  }

  .node-type {
    color: var(--color-heading);
    font-weight: 600;
    text-transform: capitalize;
  }

  .node-time {
    color: var(--color-slate-subtle);
    font-size: 10px;
  }

  /* ZONE 2: CENTER CANVAS MAIN AREA */
  .canvas-main-area {
    overflow-y: auto;
    padding: 20px clamp(16px, 3vw, 40px) 60px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .probe-alert-bar {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: var(--radius-sm);
    color: #8b5cf6;
    font: 600 12px var(--font-ui);
    padding: 10px 14px;
    text-align: left;
    cursor: pointer;
    width: 100%;
    max-width: 960px;
    margin: 0 auto;
  }
  .probe-alert-bar:hover {
    background: rgba(139, 92, 246, 0.18);
  }

  .error-banner {
    background: var(--color-rose-bg);
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: var(--radius-sm);
    color: var(--color-rose);
    font-size: 12px;
    padding: 10px 14px;
    max-width: 960px;
    margin: 0 auto;
    width: 100%;
  }

  /* ZONE 3: RIGHT SOCRATIC TUTOR PANEL */
  .socratic-tutor-column {
    background: var(--color-graphite);
    border-left: 1px solid var(--color-graphite-border);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    z-index: 5;
    animation: slideInRight 0.2s ease-out;
  }

  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(16px); }
    to { opacity: 1; transform: translateX(0); }
  }

  .tutor-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    background: var(--color-bone-muted);
  }

  .tutor-header h3 {
    margin: 2px 0 0;
    font-family: var(--font-brand);
    font-size: 16px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .close-panel-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle);
    font-size: 15px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: var(--radius-xs);
  }
  .close-panel-btn:hover {
    color: var(--color-heading);
    background: var(--color-graphite-hover);
  }

  .tutor-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .probe-card {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .probe-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-tag {
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .focus-pill {
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.28);
    border-radius: 99px;
    color: #8b5cf6;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 7px;
    text-transform: capitalize;
  }

  .probe-question {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 600;
    line-height: 1.5;
    margin: 0;
  }

  .probe-pedagogy-tip {
    background: var(--color-bone-muted);
    border-left: 2px solid var(--color-aurora);
    padding: 8px 10px;
    border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
  }

  .probe-pedagogy-tip p {
    margin: 0;
    font-size: 11px;
    line-height: 1.4;
    color: var(--color-slate-light);
  }

  .probe-input-label {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-heading);
    margin-top: 4px;
  }

  .probe-textarea {
    width: 100%;
    background: var(--input-bg, var(--color-graphite));
    border: 1px solid var(--input-border, var(--color-graphite-border));
    border-radius: var(--radius-sm);
    color: var(--color-slate-bright);
    font: 13px/1.55 var(--font-ui);
    min-height: 120px;
    outline: none;
    padding: 10px;
    resize: vertical;
    box-sizing: border-box;
  }
  .probe-textarea:focus {
    border-color: var(--color-horizon-blue);
    box-shadow: 0 0 0 2px var(--color-horizon-glow);
  }

  .probe-status-msg {
    margin: 0;
    font-size: 11px;
    color: var(--color-horizon-blue);
  }

  .probe-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .save-evidence-btn {
    background: var(--color-horizon-blue);
    border: 1px solid var(--color-horizon-bright);
    border-radius: var(--radius-xs);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 7px 11px;
    cursor: pointer;
    flex: 1;
  }
  .save-evidence-btn:hover:not(:disabled) {
    background: var(--color-horizon-bright);
  }

  .defer-btn {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    color: var(--color-slate-light);
    font-size: 11px;
    font-weight: 600;
    padding: 7px 10px;
    cursor: pointer;
  }

  .dismiss-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle);
    font-size: 10px;
    font-weight: 600;
    padding: 7px 8px;
    cursor: pointer;
  }
  .dismiss-btn:hover { color: var(--color-amber); }

  .empty-probe-state {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 16px;
    text-align: center;
  }

  .empty-probe-state h4 {
    margin: 0 0 6px;
    font-size: 14px;
    color: var(--color-heading);
  }

  .empty-probe-state p {
    margin: 0;
    font-size: 11px;
    line-height: 1.45;
    color: var(--color-slate-muted);
  }

  .evidence-badge {
    display: inline-block;
    color: var(--color-signal-green);
    font-size: 10px;
    font-weight: 700;
    margin-top: 10px;
  }

  .empty-state {
    text-align: center;
    padding: 16px 0;
    color: var(--color-slate-muted);
    font-size: 11px;
  }

  .loading-view, .empty-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 56px);
    background: var(--color-obsidian);
    color: var(--color-slate-light);
    padding: 24px;
    text-align: center;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-top-color: var(--color-horizon-blue);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  @media (max-width: 1024px) {
    .workspace-grid {
      grid-template-columns: 280px 1fr;
    }
    .workspace-grid.tutor-open {
      grid-template-columns: 280px 1fr 320px;
    }
  }

  @media (max-width: 800px) {
    .workspace-grid {
      grid-template-columns: 1fr;
    }
    .workspace-grid.tutor-open {
      grid-template-columns: 1fr;
    }
    .workspace-sidebar {
      display: none;
    }
    .socratic-tutor-column {
      position: fixed;
      inset: 52px 0 0 0;
      z-index: 50;
    }
  }
</style>
