<script>
  import { onMount } from 'svelte';
  import ThinkingTimeline from '../lib/ThinkingTimeline.svelte';
  import PdfViewer from '../lib/PdfViewer.svelte';
  import { formatDate, responseError, routeParams } from '../lib/session.js';

  let {
    courseId: propCourseId = '',
    assignmentId: propAssignmentId = '',
    targetStudentId = '',
    targetSessionId = '',
    onBack = null,
  } = $props();

  let courseId = $state(propCourseId || '');
  let assignmentId = $state(propAssignmentId || '');
  let filterStatus = $state('all'); // 'all' | 'completed' | 'submitted' | 'active'
  let searchQuery = $state('');

  // UI state for the 3-column canvas workspace
  let isRosterCollapsed = $state(false);
  let activeEvalTab = $state('rubric'); // 'rubric' | 'traps' | 'reasoning'
  let activeWorkTab = $state('sections'); // 'sections' | 'pdf'
  let activeReviewTimelineTab = $state('reasoning'); // 'reasoning' | 'activity'
  let expandedReasoningNode = $state(-1);
  let expandedActivityNode = $state(-1);

  // ---- Misconception review ---------------------------------------------
  let scanBySession = $state({});
  let scanningSession = $state('');
  let scanError = $state('');
  let draftOpenFor = $state('');
  let draftBody = $state('');
  let draftSubject = $state('');

  let scan = $derived(selected ? scanBySession[selected.session_id] || null : null);
  let isScanning = $derived(Boolean(selected) && scanningSession === selected.session_id);

  async function runMisconceptionScan() {
    if (!selected || isScanning) return;
    const sessionId = selected.session_id;
    scanningSession = sessionId;
    scanError = '';
    try {
      const response = await fetch(`/interventions/scan/${sessionId}`);
      if (!response.ok) throw new Error(await responseError(response, 'The submission could not be analysed.'));
      scanBySession = { ...scanBySession, [sessionId]: await response.json() };
    } catch (err) {
      scanError = err.message || 'The submission could not be analysed.';
    } finally {
      scanningSession = '';
    }
  }

  function openDraft(finding) {
    draftOpenFor = finding.misconception_id;
    draftSubject = finding.suggested_message?.subject || '';
    draftBody = finding.suggested_message?.body || '';
  }

  function openInMailClient() {
    const url = `mailto:?subject=${encodeURIComponent(draftSubject)}&body=${encodeURIComponent(draftBody)}`;
    window.open(url, '_blank');
  }

  async function copyDraft() {
    try {
      await navigator.clipboard.writeText(`Subject: ${draftSubject}\n\n${draftBody}`);
    } catch (err) {
      console.warn('Clipboard unavailable', err);
    }
  }

  $effect(() => {
    let changed = false;
    if (propCourseId && propCourseId !== courseId) {
      courseId = propCourseId;
      changed = true;
    }
    if (propAssignmentId !== undefined && propAssignmentId !== assignmentId) {
      assignmentId = propAssignmentId;
      changed = true;
    }
    if (changed) {
      loadQueue();
    }
  });

  $effect(() => {
    if (targetSessionId && selected?.session_id !== targetSessionId && queue.length) {
      const match = queue.find((item) => item.session_id === targetSessionId);
      if (match) selectItem(match);
    } else if (targetStudentId && selected?.student_id !== targetStudentId && queue.length) {
      const match = queue.find((item) => item.student_id === targetStudentId);
      if (match) selectItem(match);
    }
  });

  let queue = $state([]);
  let selected = $state(null);
  let dossier = $state(null);
  let trace = $state([]);
  let reasoningNodes = $state([]);
  let activityNodes = $state([]);
  let canvasData = $state(null);
  let grade = $state('');
  let feedback = $state('');
  let teacherId = $state('educator_workspace');
  let isLoading = $state(true);
  let isFinalizing = $state(false);
  let notice = $state('');
  let error = $state('');

  let filteredQueue = $derived.by(() => {
    let q = queue;
    if (filterStatus === 'completed') q = q.filter((item) => item.status === 'completed');
    else if (filterStatus === 'submitted') q = q.filter((item) => item.status === 'submitted');
    else if (filterStatus === 'active') q = q.filter((item) => item.status !== 'submitted' && item.status !== 'completed');
    if (searchQuery.trim()) {
      const term = searchQuery.trim().toLowerCase();
      q = q.filter((item) => item.student_id.toLowerCase().includes(term) || (item.assignment_title && item.assignment_title.toLowerCase().includes(term)));
    }
    return q;
  });

  let completedCount = $derived(queue.filter((item) => item.status === 'completed').length);
  let submittedCount = $derived(queue.filter((item) => item.status === 'submitted').length);
  let activeCount = $derived(queue.filter((item) => item.status !== 'submitted' && item.status !== 'completed').length);

  // Cohort Quick-Flipper index
  let currentStudentIndex = $derived.by(() => {
    if (!selected || !filteredQueue.length) return -1;
    return filteredQueue.findIndex((item) => item.session_id === selected.session_id);
  });

  function selectPrevStudent() {
    if (currentStudentIndex > 0) {
      selectItem(filteredQueue[currentStudentIndex - 1]);
    }
  }

  function selectNextStudent() {
    if (currentStudentIndex >= 0 && currentStudentIndex < filteredQueue.length - 1) {
      selectItem(filteredQueue[currentStudentIndex + 1]);
    }
  }

  // Student deliverables
  let displaySections = $derived.by(() => {
    if (canvasData?.sections?.length) {
      return canvasData.sections.map((s) => {
        const draft = canvasData.drafts?.find((d) => d.section_id === s.section_id);
        return {
          section_id: s.section_id,
          title: s.title || s.section_id.replaceAll('_', ' '),
          prompt: s.prompt,
          text: draft?.text || '',
          revision: draft?.revision || 1,
          source_references: draft?.source_references || [],
        };
      });
    }
    return dossier?.canvas_sections || [];
  });

  let totalDeliverableWords = $derived.by(() => {
    if (!displaySections.length) return 0;
    return displaySections.reduce((acc, sec) => {
      if (!sec.text) return acc;
      return acc + sec.text.trim().split(/\s+/).filter(Boolean).length;
    }, 0);
  });

  let totalRubricCriteria = $derived.by(() => {
    if (!dossier?.per_question_evidence) return 0;
    return dossier.per_question_evidence.reduce((sum, q) => sum + Object.keys(q.rubric_evidence || {}).length, 0);
  });

  async function loadQueue() {
    error = '';
    const params = new URLSearchParams();
    if (courseId) params.set('course_id', courseId);
    if (assignmentId) params.set('assignment_id', assignmentId);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`/evidence/review-queue${suffix}`);
    if (!response.ok) throw new Error(await responseError(response, 'The evaluation review queue could not be loaded.'));
    queue = await response.json();

    let targetToSelect = null;
    if (targetSessionId) {
      targetToSelect = queue.find((item) => item.session_id === targetSessionId);
    }
    if (!targetToSelect && targetStudentId) {
      targetToSelect = queue.find((item) => item.student_id === targetStudentId);
    }
    if (!targetToSelect && selected) {
      targetToSelect = queue.find((item) => item.session_id === selected.session_id);
    }
    if (!targetToSelect && queue.length) {
      targetToSelect = queue[0];
    }
    if (targetToSelect) {
      await selectItem(targetToSelect);
    } else {
      selected = null;
    }
  }

  async function selectItem(item) {
    selected = item;
    dossier = null;
    trace = [];
    reasoningNodes = [];
    activityNodes = [];
    canvasData = null;
    feedback = '';
    grade = item.suggested_grade && item.suggested_grade !== 'Pending' ? item.suggested_grade : '';
    error = '';
    draftOpenFor = '';

    const [dossierResponse, traceResponse, reasoningRes, activityRes, canvasRes] = await Promise.all([
      fetch(`/evidence/dossier/${item.session_id}`),
      fetch(`/evidence/trace/${item.session_id}`),
      fetch(`/evidence/trace/${item.session_id}/reasoning`),
      fetch(`/evidence/trace/${item.session_id}/activity`),
      fetch(`/canvas/sessions/${item.session_id}`),
    ]);
    if (!dossierResponse.ok) {
      error = await responseError(dossierResponse, 'The evidence dossier could not be loaded.');
      return;
    }
    dossier = await dossierResponse.json();
    if (traceResponse.ok) trace = (await traceResponse.json()).trace_nodes || [];
    if (reasoningRes.ok) reasoningNodes = (await reasoningRes.json()).nodes || [];
    if (activityRes.ok) activityNodes = (await activityRes.json()).nodes || [];
    if (canvasRes.ok) canvasData = await canvasRes.json();
  }

  async function finalise() {
    if (!selected || !grade.trim()) return;
    isFinalizing = true;
    error = '';
    notice = '';
    try {
      const response = await fetch(`/evidence/dossier/${selected.session_id}/finalise-grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved_grade: grade.trim(),
          teacher_id: teacherId.trim() || 'educator_workspace',
          teacher_override: grade.trim() !== selected.suggested_grade,
          feedback_comments: feedback.trim(),
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The final grade could not be recorded.'));
      notice = `Grade ${grade.trim()} finalized for ${selected.student_id}. Session sealed.`;
      selected = null;
      dossier = null;
      await loadQueue();
    } catch (err) {
      error = err.message || 'The final grade could not be recorded.';
    } finally {
      isFinalizing = false;
    }
  }

  onMount(async () => {
    const params = routeParams();
    if (!courseId) courseId = params.get('course_id') || '';
    if (!assignmentId) assignmentId = params.get('assignment_id') || '';
    try {
      await loadQueue();
    } catch (err) {
      error = err.message || 'The evaluation queue could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="canvas-review-root">
  {#if !assignmentId}
    <!-- Compact Standalone Mode Bar -->
    <header class="standalone-top-bar">
      <div class="standalone-title">
        <span class="eyebrow">Educator Workspace</span>
        <h2>Evaluation Window</h2>
      </div>
      <div class="standalone-meta">
        <span>Submissions In Queue:</span>
        <strong>{queue.length}</strong>
      </div>
    </header>
  {/if}

  {#if isLoading}
    <div class="loading"><div class="spinner"></div><span>Loading submitted assignments…</span></div>
  {:else if error && queue.length === 0}
    <section class="load-error" role="alert">
      <strong>The evaluation queue could not be loaded.</strong>
      <p>{error}</p>
      <button class="btn btn-secondary btn-sm" onclick={loadQueue}>Try again</button>
    </section>
  {:else}
    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- 3-COLUMN CANVAS WORKSPACE (Left Roster | Center Hero | Right Gutter) -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div class="canvas-3col-workspace" class:roster-collapsed={isRosterCollapsed}>

      <!-- ── 1. LEFT SIDEBAR: Student Roster ─────────────────────── -->
      {#if !isRosterCollapsed}
        <aside class="canvas-roster-sidebar">
          <div class="roster-top-bar">
            <span class="roster-top-title">Roster ({filteredQueue.length})</span>
            <button
              type="button"
              class="btn-collapse-sidebar"
              onclick={() => (isRosterCollapsed = true)}
              title="Collapse student roster to maximize document reading width"
            >
              ⇤
            </button>
          </div>

          <div class="roster-search-bar">
            <input
              type="text"
              class="roster-search-input"
              placeholder="Filter students…"
              bind:value={searchQuery}
            />
            <div class="roster-filter-pills">
              <button
                type="button"
                class="filter-pill"
                class:active={filterStatus === 'all'}
                onclick={() => (filterStatus = 'all')}
              >All ({queue.length})</button>
              <button
                type="button"
                class="filter-pill"
                class:active={filterStatus === 'completed'}
                onclick={() => (filterStatus = 'completed')}
              >Final ({completedCount})</button>
              {#if submittedCount > 0}
                <button
                  type="button"
                  class="filter-pill"
                  class:active={filterStatus === 'submitted'}
                  onclick={() => (filterStatus = 'submitted')}
                >Ready ({submittedCount})</button>
              {/if}
              {#if activeCount > 0}
                <button
                  type="button"
                  class="filter-pill"
                  class:active={filterStatus === 'active'}
                  onclick={() => (filterStatus = 'active')}
                >Draft ({activeCount})</button>
              {/if}
            </div>
          </div>

          <div class="roster-scroll-list">
            {#if filteredQueue.length === 0}
              <div class="roster-empty">No students found.</div>
            {:else}
              {#each filteredQueue as item (item.session_id)}
                <button
                  type="button"
                  class="roster-item-btn"
                  class:active={selected?.session_id === item.session_id}
                  onclick={() => selectItem(item)}
                >
                  <span class="roster-avatar-mini">{item.student_id.slice(0, 2).toUpperCase()}</span>
                  <div class="roster-item-info">
                    <span class="roster-item-id">{item.student_id}</span>
                    {#if !assignmentId && item.assignment_title}
                      <span class="roster-item-assignment">{item.assignment_title}</span>
                    {/if}
                    <span class="roster-item-date">{formatDate(item.submitted_at)}</span>
                  </div>
                  {#if item.status === 'submitted'}
                    <span class="mini-status-badge submitted">Ready</span>
                  {:else if item.status === 'completed'}
                    <span class="mini-status-badge completed">Final</span>
                  {:else}
                    <span class="mini-status-badge in-progress">Draft</span>
                  {/if}
                </button>
              {/each}
            {/if}
          </div>

          <button type="button" class="roster-refresh-btn" onclick={loadQueue} title="Check for new submissions">
            ↻ Refresh Roster
          </button>
        </aside>
      {:else}
        <!-- Collapsed Roster Rail (42px) -->
        <aside class="canvas-roster-rail" onclick={() => (isRosterCollapsed = false)} title="Click to expand student roster">
          <button type="button" class="btn-expand-rail" onclick={() => (isRosterCollapsed = false)} title="Expand student roster">
            ⇥
          </button>
          <div class="rail-vertical-text">STUDENTS ({filteredQueue.length})</div>
        </aside>
      {/if}

      <!-- ── 2. CENTER STAGE: Student Deliverable Canvas (HERO) ──── -->
      <main class="canvas-document-hero">
        {#if !selected}
          <div class="hero-empty-state">
            <span class="empty-hero-icon">📋</span>
            <h3>No Student Selected</h3>
            <p>Select a student from the roster on the left to review their submission deliverable.</p>
          </div>
        {:else if !dossier}
          <div class="loading small"><div class="spinner"></div><span>Opening evaluation dossier…</span></div>
        {:else}
          <!-- Compact Hero Control Bar -->
          <header class="document-hero-toolbar">
            <div class="hero-student-meta">
              <span class="hero-avatar">{selected.student_id.slice(0, 2).toUpperCase()}</span>
              <div class="hero-student-text">
                <div class="hero-title-row">
                  <h3 class="hero-student-name">{selected.student_id}</h3>
                  <span
                    class="status-chip"
                    class:submitted={selected.status === 'submitted'}
                    class:completed={selected.status === 'completed'}
                    class:in-progress={selected.status !== 'submitted' && selected.status !== 'completed'}
                  >
                    {#if selected.status === 'submitted'}
                      ✓ Ready for Grading
                    {:else if selected.status === 'completed'}
                      ✓ Grade Finalized
                    {:else}
                      ● Live Session (Draft)
                    {/if}
                  </span>
                </div>
                <div class="hero-timestamp-row">
                  {selected.status === 'submitted' ? 'Submitted' : selected.status === 'completed' ? 'Finalized' : 'Active'}: {formatDate(selected.submitted_at)}
                </div>
              </div>
            </div>

            <!-- Cohort Quick-Flipper Navigation -->
            <div class="cohort-quick-flipper">
              <button
                type="button"
                class="btn-flipper"
                onclick={selectPrevStudent}
                disabled={currentStudentIndex <= 0}
                title="Previous Student"
              >
                ‹ Prev
              </button>
              <span class="flipper-index-label">
                {currentStudentIndex >= 0 ? `${currentStudentIndex + 1} of ${filteredQueue.length}` : '—'}
              </span>
              <button
                type="button"
                class="btn-flipper"
                onclick={selectNextStudent}
                disabled={currentStudentIndex < 0 || currentStudentIndex >= filteredQueue.length - 1}
                title="Next Student"
              >
                Next ›
              </button>
            </div>

            <!-- View Switcher & PDF Download -->
            <div class="hero-toolbar-actions">
              <div class="view-toggle-group">
                <button
                  type="button"
                  class="btn-view-toggle"
                  class:active={activeWorkTab === 'sections'}
                  onclick={() => (activeWorkTab = 'sections')}
                  title="View written canvas sections"
                >
                  📝 Canvas
                </button>
                <button
                  type="button"
                  class="btn-view-toggle"
                  class:active={activeWorkTab === 'pdf'}
                  onclick={() => (activeWorkTab = 'pdf')}
                  title="Render student's submitted assignment as a PDF document"
                >
                  📄 PDF
                </button>
              </div>

              <a
                class="btn-download-pdf-compact"
                href={`/evidence/dossier/${selected.session_id}/pdf`}
                download
                title="Download official PDF submission"
              >
                ⬇ PDF
              </a>
            </div>
          </header>

          <!-- Document Center Stage Scroll Viewport -->
          <div class="document-center-viewport">
            {#if activeWorkTab === 'pdf'}
              <!-- Rendered PDF Viewer Mode -->
              <div class="pdf-document-container">
                <div class="pdf-container-toolbar">
                  <span class="pdf-badge">Official PDF Submission Document</span>
                  <a
                    class="btn-open-tab"
                    href={`/evidence/dossier/${selected.session_id}/pdf`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open in Tab ↗
                  </a>
                </div>
                <div class="pdf-embed-box">
                  {#key selected.session_id}
                    <PdfViewer
                      url={`/evidence/dossier/${selected.session_id}/pdf`}
                      title={`${selected.student_id} - ${selected.assignment_title || 'Assignment Submission'}`}
                    />
                  {/key}
                </div>
              </div>
            {:else}
              <!-- Continuous Academic Paper Sheet Mode -->
              <article class="academic-paper-sheet">
                <header class="sheet-title-header">
                  <h1 class="sheet-main-heading">{selected.assignment_title || 'Assignment Submission Deliverables'}</h1>
                  <div class="sheet-meta-line">
                    <span>Author: <strong>{selected.student_id}</strong></span>
                    <span class="sheet-dot">&bull;</span>
                    <span>{displaySections.length} {displaySections.length === 1 ? 'Section' : 'Sections'}</span>
                    {#if totalDeliverableWords > 0}
                      <span class="sheet-dot">&bull;</span>
                      <span>~{totalDeliverableWords} words</span>
                    {/if}
                  </div>
                </header>

                {#if displaySections.length === 0}
                  <div class="paper-empty-notice">
                    No authored text was recorded for this submission.
                  </div>
                {:else}
                  <div class="paper-sections-flow">
                    {#each displaySections as sec, sIdx (sec.section_id)}
                      <section class="paper-section-block">
                        <div class="section-heading-bar">
                          <div class="section-title-wrap">
                            <span class="section-idx-badge">{sIdx + 1}</span>
                            <h2 class="section-title-text">{sec.title || sec.section_id.replaceAll('_', ' ')}</h2>
                          </div>
                          {#if sec.revision}
                            <span class="revision-pill">Rev {sec.revision}</span>
                          {/if}
                        </div>

                        {#if sec.prompt}
                          <blockquote class="paper-prompt-callout">
                            <span class="prompt-eyebrow">Guiding Prompt</span>
                            <p>{sec.prompt}</p>
                          </blockquote>
                        {/if}

                        {#if sec.text}
                          <div class="paper-body-text">{sec.text}</div>
                        {:else}
                          <div class="paper-body-empty">No text provided for this section.</div>
                        {/if}

                        {#if sec.source_references?.length}
                          <div class="paper-sources-footer">
                            <span class="sources-eyebrow">Cited Grounding Sources:</span>
                            <div class="sources-tags-row">
                              {#each sec.source_references as src}
                                <span class="paper-source-chip">
                                  📖 {src.document_title || 'Reference'}{src.page_number ? ` (p. ${src.page_number})` : ''}
                                </span>
                              {/each}
                            </div>
                          </div>
                        {/if}
                      </section>
                    {/each}
                  </div>
                {/if}
              </article>
            {/if}
          </div>
        {/if}
      </main>

      <!-- ── 3. RIGHT SIDEBAR: Evaluator Workbench Gutter ────────── -->
      {#if selected && dossier}
        <aside class="canvas-workbench-gutter">

          <!-- Sticky Pinned Grade Finalization Bar -->
          <div class="gutter-finalization-bar">
            {#if selected.status === 'submitted'}
              <div class="gutter-grade-form">
                <div class="grade-input-group">
                  <label class="field-label-mini">
                    <span>Grade</span>
                    <input
                      type="text"
                      class="input-grade-compact"
                      bind:value={grade}
                      placeholder="A, 92%"
                    />
                  </label>
                  <label class="field-label-mini feedback-flex">
                    <span>Formative Feedback</span>
                    <input
                      type="text"
                      class="input-feedback-compact"
                      bind:value={feedback}
                      placeholder="Feedback for next cycle…"
                    />
                  </label>
                </div>
                <button
                  type="button"
                  class="btn-finalize-compact"
                  onclick={finalise}
                  disabled={isFinalizing || !grade.trim()}
                >
                  {isFinalizing ? 'Finalizing…' : 'Finalize Grade & Seal ➔'}
                </button>
              </div>
            {:else if selected.status === 'completed'}
              <div class="gutter-sealed-banner">
                <span class="sealed-check">✓</span>
                <div class="sealed-text">
                  <strong>Grade Finalized & Sealed</strong>
                  <small>Recorded in sovereign ledger.</small>
                </div>
                <a class="btn-sealed-pdf" href={`/evidence/dossier/${selected.session_id}/pdf`} download>
                  ⬇ PDF
                </a>
              </div>
            {:else}
              <div class="gutter-draft-banner">
                <span class="draft-dot">●</span>
                <div class="draft-text">
                  <strong>Live Student Session</strong>
                  <small>Student actively reasoning.</small>
                </div>
                <a class="btn-recorder-link" href={`#/student/trace?session_id=${selected.session_id}`}>
                  Trace ↗
                </a>
              </div>
            {/if}
          </div>

          <!-- Workbench Tabs Bar -->
          <nav class="gutter-tabs-bar">
            <button
              type="button"
              class="gutter-tab-btn"
              class:active={activeEvalTab === 'rubric'}
              onclick={() => (activeEvalTab = 'rubric')}
            >
              <span>📊 Rubric</span>
              <span class="gutter-tab-count">{totalRubricCriteria}</span>
            </button>

            <button
              type="button"
              class="gutter-tab-btn"
              class:active={activeEvalTab === 'traps'}
              onclick={() => (activeEvalTab = 'traps')}
            >
              <span>🪤 Traps</span>
              <span class="gutter-tab-count" class:alert={scan && (scan.findings || []).length > 0}>
                {scan ? (scan.findings || []).length : 'Scan'}
              </span>
            </button>

            <button
              type="button"
              class="gutter-tab-btn"
              class:active={activeEvalTab === 'reasoning'}
              onclick={() => (activeEvalTab = 'reasoning')}
            >
              <span>💡 Trace</span>
              <span class="gutter-tab-count">{reasoningNodes.length + activityNodes.length}</span>
            </button>
          </nav>

          <!-- Workbench Tab Body Viewport (Independently Scrolling) -->
          <div class="gutter-tab-viewport">

            <!-- ── TAB 1: Rubric Assessment ── -->
            {#if activeEvalTab === 'rubric'}
              <div class="rubric-inspector">
                {#if !dossier.per_question_evidence || dossier.per_question_evidence.length === 0}
                  <div class="tab-empty-msg">No rubric criteria configured for this assignment.</div>
                {:else}
                  <div class="rubric-matrix-list">
                    {#each dossier.per_question_evidence as question}
                      {#each Object.entries(question.rubric_evidence || {}) as [, criterion]}
                        <article class="criterion-chip-card" class:met={criterion.met}>
                          <header class="criterion-chip-header">
                            <span class="criterion-tag" class:met={criterion.met}>
                              {criterion.met ? '✓ Evidence Met' : '● Needs Review'}
                            </span>
                            <span class="criterion-conf-pill">
                              {Math.round((criterion.confidence || 0) * 100)}%
                            </span>
                          </header>

                          <strong class="criterion-label">
                            {criterion.label || (criterion.met ? 'Standard Met' : 'Criterion Pending')}
                          </strong>

                          <p class="criterion-explanation-text">{criterion.description}</p>

                          {#if criterion.evidence}
                            <div class="criterion-quote-block">
                              <span class="quote-header">Submission Quote:</span>
                              <div class="quote-text">{criterion.evidence}</div>
                            </div>
                          {/if}

                          {#if criterion.explanation}
                            <small class="criterion-note">{criterion.explanation}</small>
                          {/if}
                        </article>
                      {/each}
                    {/each}
                  </div>
                {/if}
              </div>

            <!-- ── TAB 2: Cognitive Traps & Misconceptions ── -->
            {:else if activeEvalTab === 'traps'}
              <div class="traps-inspector">
                {#if !scan}
                  <div class="trap-scan-prompt">
                    <span class="trap-scan-icon">🪤</span>
                    <h4>Misconception Trap Scan</h4>
                    <p class="trap-scan-desc">
                      Scans student thesis against cognitive traps authored in the course knowledge graph.
                    </p>
                    <button
                      type="button"
                      class="btn-trigger-scan"
                      onclick={runMisconceptionScan}
                      disabled={isScanning}
                    >
                      {isScanning ? 'Analyzing with LLM…' : '⚡ Run Trap Scan'}
                    </button>
                    {#if isScanning}
                      <p class="scan-running-note">Evidencing mental models (takes ~20s)…</p>
                    {/if}
                  </div>
                {:else if (scan.findings || []).length === 0}
                  <div class="trap-clean-prompt">
                    <span class="clean-check-icon">✓</span>
                    <h4>No Cognitive Traps Found</h4>
                    <p class="clean-desc">The student avoided known mental traps for this inquiry.</p>
                    <button
                      type="button"
                      class="btn-rescan-ghost"
                      onclick={runMisconceptionScan}
                      disabled={isScanning}
                    >
                      ↻ Re-scan Submission
                    </button>
                  </div>
                {:else}
                  <div class="traps-results-bar">
                    <span class="traps-count-label">
                      {(scan.findings || []).length} Cognitive {(scan.findings || []).length === 1 ? 'Trap' : 'Traps'} Evidenced
                    </span>
                    <button
                      type="button"
                      class="btn-rescan-mini"
                      onclick={runMisconceptionScan}
                      disabled={isScanning}
                    >
                      ↻ Re-scan
                    </button>
                  </div>

                  <div class="traps-cards-flow">
                    {#each scan.findings as finding}
                      <article class="trap-item-card">
                        <header class="trap-item-header">
                          <strong class="trap-item-name">{finding.name}</strong>
                          <span class="trap-item-badge" class:weak={finding.detection !== 'llm_verified'}>
                            {finding.detection === 'llm_verified' ? 'Evidenced' : 'Candidate'}
                          </span>
                        </header>

                        <p class="trap-flawed-rule">{finding.flawed_rule}</p>

                        {#if finding.evidence_quote}
                          <div class="trap-quote-box">
                            <span class="quote-eyebrow">Student Quote:</span>
                            <blockquote class="trap-quote-text">"{finding.evidence_quote}"</blockquote>
                          </div>
                          <p class="trap-why-text">{finding.why}</p>
                        {/if}

                        {#if finding.remediation_hint}
                          <div class="trap-remediation-line">
                            <span class="remed-label">Remediate:</span>
                            <span>{finding.remediation_hint}</span>
                          </div>
                        {/if}

                        <div class="trap-card-actions">
                          <button
                            type="button"
                            class="btn-draft-note"
                            onclick={() => openDraft(finding)}
                          >
                            ✉ Socratic Note
                          </button>
                          {#if finding.concept_id}
                            <a
                              class="trap-concept-link"
                              href={`/#/knowledge-graph?course_id=${courseId}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Graph ↗
                            </a>
                          {/if}
                        </div>

                        {#if draftOpenFor === finding.misconception_id}
                          <div class="inline-socratic-draft">
                            <label class="draft-field-label" for="draft-subject">Subject</label>
                            <input
                              id="draft-subject"
                              class="draft-subject-input"
                              bind:value={draftSubject}
                            />
                            <label class="draft-field-label" for="draft-body">Socratic Guidance</label>
                            <textarea
                              id="draft-body"
                              class="draft-body-input"
                              rows="6"
                              bind:value={draftBody}
                            ></textarea>
                            <div class="draft-action-btns">
                              <button type="button" class="btn-mail" onclick={openInMailClient}>Open in Mail</button>
                              <button type="button" class="btn-copy" onclick={copyDraft}>Copy</button>
                              <button type="button" class="btn-close" onclick={() => (draftOpenFor = '')}>Close</button>
                            </div>
                          </div>
                        {/if}
                      </article>
                    {/each}
                  </div>
                {/if}

                {#if scanError}
                  <p class="trap-scan-error">{scanError}</p>
                {/if}
              </div>

            <!-- ── TAB 3: Reasoning Trace ── -->
            {:else if activeEvalTab === 'reasoning'}
              <div class="trace-inspector">
                <div class="trace-sub-toolbar">
                  <div class="trace-toggle-buttons">
                    <button
                      type="button"
                      class="btn-trace-sub"
                      class:active={activeReviewTimelineTab === 'reasoning'}
                      onclick={() => (activeReviewTimelineTab = 'reasoning')}
                    >
                      Milestones ({reasoningNodes.length})
                    </button>
                    <button
                      type="button"
                      class="btn-trace-sub"
                      class:active={activeReviewTimelineTab === 'activity'}
                      onclick={() => (activeReviewTimelineTab = 'activity')}
                    >
                      Log ({activityNodes.length})
                    </button>
                  </div>
                  <a
                    class="btn-flight-recorder"
                    href={`#/student/trace?session_id=${selected.session_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Recorder ↗
                  </a>
                </div>

                <div class="trace-timeline-area">
                  {#if activeReviewTimelineTab === 'reasoning'}
                    {#if reasoningNodes.length === 0}
                      <p class="tab-empty-msg">No reasoning milestones logged yet.</p>
                    {:else}
                      <ThinkingTimeline
                        nodes={reasoningNodes}
                        expandedNodeIndex={expandedReasoningNode}
                        onToggleNode={(idx) => {
                          expandedReasoningNode = expandedReasoningNode === idx ? -1 : idx;
                        }}
                      />
                    {/if}
                  {:else}
                    {#if activityNodes.length === 0}
                      <p class="tab-empty-msg">No activity events logged.</p>
                    {:else}
                      <ThinkingTimeline
                        nodes={activityNodes}
                        expandedNodeIndex={expandedActivityNode}
                        onToggleNode={(idx) => {
                          expandedActivityNode = expandedActivityNode === idx ? -1 : idx;
                        }}
                      />
                    {/if}
                  {/if}
                </div>
              </div>
            {/if}

          </div>
        </aside>
      {/if}

    </div>
  {/if}

  {#if notice}<div class="toast-notice success">{notice}</div>{/if}
  {#if error && queue.length > 0}<div class="toast-notice error">{error}</div>{/if}
</div>

<style>
  /* ================================================================
     CANVAS REVIEW ROOT CONTAINER (FULL HEIGHT 100%)
     ================================================================ */
  .canvas-review-root {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    background: var(--color-bone, #f6f5f1);
    font-family: var(--font-ui, system-ui, sans-serif);
    overflow: hidden;
    position: relative;
    box-sizing: border-box;
  }

  /* Compact Top Bar for Standalone Mode */
  .standalone-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 18px;
    background: #ffffff;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 42px;
    box-sizing: border-box;
  }

  .standalone-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .standalone-title .eyebrow {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .standalone-title h2 {
    font-size: 14px;
    font-family: var(--font-brand, serif);
    color: var(--color-heading);
    margin: 0;
  }

  .standalone-meta {
    font-size: 11.5px;
    color: var(--color-slate-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .standalone-meta strong {
    color: var(--color-horizon-bright, #d97706);
    font-size: 13px;
  }

  /* ================================================================
     3-COLUMN CANVAS WORKSPACE GRID
     [LEFT ROSTER: 260px] [CENTER HERO: 1fr] [RIGHT WORKBENCH: 380px]
     ================================================================ */
  .canvas-3col-workspace {
    display: grid;
    grid-template-columns: 260px minmax(0, 1fr) 380px;
    flex: 1;
    height: calc(100% - 42px);
    min-height: 0;
    overflow: hidden;
    background: var(--color-bone, #f6f5f1);
  }

  .canvas-3col-workspace.roster-collapsed {
    grid-template-columns: 42px minmax(0, 1fr) 380px;
  }

  /* ── 1. LEFT SIDEBAR: Student Roster ─────────────────────────── */
  .canvas-roster-sidebar {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
    height: 100%;
    overflow: hidden;
  }

  .roster-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 38px;
    box-sizing: border-box;
  }

  .roster-top-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .btn-collapse-sidebar {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 12px;
    padding: 1px 6px;
    cursor: pointer;
    color: var(--color-slate-muted);
    transition: all 0.12s;
  }

  .btn-collapse-sidebar:hover {
    background: #e2e8f0;
    color: var(--color-heading);
  }

  /* Collapsed Rail */
  .canvas-roster-rail {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 4px;
    gap: 14px;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
    cursor: pointer;
    transition: background 0.15s;
  }

  .canvas-roster-rail:hover {
    background: var(--color-bone, #f6f5f1);
  }

  .btn-expand-rail {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 12px;
    padding: 3px 5px;
    cursor: pointer;
    color: var(--color-slate-muted);
  }

  .rail-vertical-text {
    writing-mode: vertical-rl;
    text-orientation: mixed;
    transform: rotate(180deg);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: var(--color-slate-muted);
  }

  .roster-search-bar {
    padding: 8px 10px;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
  }

  .roster-search-input {
    width: 100%;
    padding: 5px 8px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .roster-search-input:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .roster-filter-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .filter-pill {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: 999px;
    color: var(--color-slate-muted);
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 7px;
    cursor: pointer;
    transition: all 0.12s;
  }

  .filter-pill:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .filter-pill.active {
    background: rgba(217, 119, 6, 0.12);
    border-color: rgba(217, 119, 6, 0.35);
    color: #92400e;
  }

  .roster-scroll-list {
    flex: 1;
    overflow-y: auto;
    padding: 6px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .roster-empty {
    color: var(--color-slate-muted);
    font-size: 11px;
    text-align: center;
    padding: 20px 8px;
    font-style: italic;
  }

  .roster-item-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 9px;
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid transparent;
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    text-align: left;
    width: 100%;
    transition: all 0.12s ease;
    color: inherit;
    font-family: inherit;
  }

  .roster-item-btn:hover {
    border-left-color: var(--color-horizon-blue, #4f6bff);
    background: #f8fafc;
  }

  .roster-item-btn.active {
    border-left-color: var(--color-horizon-bright, #d97706);
    background: rgba(217, 119, 6, 0.08);
    box-shadow: inset 0 0 0 1px rgba(217, 119, 6, 0.12);
  }

  .roster-avatar-mini {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #0ea5e9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9.5px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }

  .roster-item-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .roster-item-id {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-heading);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .roster-item-assignment {
    font-size: 9.5px;
    color: var(--color-slate-light);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .roster-item-date {
    font-size: 9px;
    color: var(--color-slate-muted);
  }

  .mini-status-badge {
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 999px;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .mini-status-badge.submitted {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid rgba(5, 150, 105, 0.2);
  }

  .mini-status-badge.completed {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  .mini-status-badge.in-progress {
    background: rgba(2, 132, 199, 0.1);
    color: #0369a1;
    border: 1px solid rgba(2, 132, 199, 0.2);
  }

  .roster-refresh-btn {
    flex-shrink: 0;
    padding: 7px;
    font-size: 10px;
    font-weight: 600;
    color: var(--color-horizon-bright, #d97706);
    background: none;
    border: none;
    border-top: 1px solid var(--color-graphite-border);
    cursor: pointer;
    transition: background 0.12s;
  }

  .roster-refresh-btn:hover {
    background: var(--color-graphite-hover, #eee);
  }

  /* ── 2. CENTER STAGE: Student Deliverables Canvas (HERO) ─────── */
  .canvas-document-hero {
    display: flex;
    flex-direction: column;
    background: var(--color-bone, #f6f5f1);
    border-right: 1px solid var(--color-graphite-border);
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  /* Compact Hero Toolbar */
  .document-hero-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 8px 18px;
    background: #ffffff;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 48px;
    box-sizing: border-box;
  }

  .hero-student-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .hero-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #3b82f6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11.5px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }

  .hero-student-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .hero-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .hero-student-name {
    font-size: 14px;
    font-weight: 700;
    font-family: var(--font-brand, serif);
    color: var(--color-heading);
    margin: 0;
    line-height: 1.2;
    white-space: nowrap;
  }

  .hero-timestamp-row {
    font-size: 10px;
    color: var(--color-slate-muted);
  }

  .status-chip {
    padding: 2px 7px;
    border-radius: 999px;
    font-size: 9.5px;
    font-weight: 700;
    white-space: nowrap;
  }

  .status-chip.submitted,
  .status-chip.completed {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid rgba(5, 150, 105, 0.25);
  }

  .status-chip.in-progress {
    background: rgba(2, 132, 199, 0.1);
    color: #0369a1;
    border: 1px solid rgba(2, 132, 199, 0.25);
  }

  /* Cohort Quick-Flipper */
  .cohort-quick-flipper {
    display: flex;
    align-items: center;
    gap: 4px;
    background: var(--color-bone, #f6f5f1);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    padding: 2px 5px;
    flex-shrink: 0;
  }

  .btn-flipper {
    background: transparent;
    border: none;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light);
    cursor: pointer;
    padding: 3px 6px;
    border-radius: 4px;
    transition: all 0.12s;
  }

  .btn-flipper:hover:not(:disabled) {
    background: #ffffff;
    color: var(--color-heading);
  }

  .btn-flipper:disabled {
    opacity: 0.35;
    cursor: default;
  }

  .flipper-index-label {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--color-slate-bright);
    padding: 0 4px;
    white-space: nowrap;
  }

  /* Hero Actions */
  .hero-toolbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .view-toggle-group {
    display: flex;
    background: var(--color-bone, #f6f5f1);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    padding: 2px;
  }

  .btn-view-toggle {
    background: transparent;
    border: none;
    padding: 3px 8px;
    font-size: 10.5px;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-muted);
    transition: all 0.12s;
  }

  .btn-view-toggle:hover {
    color: var(--color-heading);
  }

  .btn-view-toggle.active {
    background: #4f6bff;
    color: #ffffff;
  }

  .btn-download-pdf-compact {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: var(--radius-sm, 6px);
    font-size: 10.5px;
    font-weight: 600;
    color: #1d4ed8;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    text-decoration: none;
    transition: all 0.12s;
  }

  .btn-download-pdf-compact:hover {
    background: #dbeafe;
  }

  /* Document Scroll Viewport */
  .document-center-viewport {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* The Academic Paper Sheet (Center Stage Hero) */
  .academic-paper-sheet {
    background: #ffffff;
    width: 100%;
    max-width: 820px;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02);
    padding: 32px 38px 48px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .sheet-title-header {
    border-bottom: 2px solid var(--color-bone, #f6f5f1);
    padding-bottom: 14px;
  }

  .sheet-main-heading {
    font-family: var(--font-brand, "Newsreader", serif);
    font-size: 21px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0 0 6px;
    line-height: 1.3;
  }

  .sheet-meta-line {
    font-size: 11.5px;
    color: var(--color-slate-muted);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .sheet-dot {
    color: var(--color-graphite-border);
  }

  .paper-sections-flow {
    display: flex;
    flex-direction: column;
    gap: 22px;
  }

  .paper-section-block {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--color-bone, #f6f5f1);
  }

  .paper-section-block:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .section-heading-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .section-title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-idx-badge {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--color-bone, #f6f5f1);
    border: 1px solid var(--color-graphite-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    color: var(--color-slate-light);
  }

  .section-title-text {
    font-family: var(--font-brand, serif);
    font-size: 16px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
    text-transform: capitalize;
  }

  .revision-pill {
    font-size: 9.5px;
    color: var(--color-slate-muted);
    background: rgba(0, 0, 0, 0.04);
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid var(--color-graphite-border);
  }

  .paper-prompt-callout {
    background: #fdfbf7;
    border-left: 3px solid #d97706;
    padding: 8px 12px;
    border-radius: 0 4px 4px 0;
    margin: 0;
  }

  .prompt-eyebrow {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #b45309;
    display: block;
    margin-bottom: 2px;
  }

  .paper-prompt-callout p {
    margin: 0;
    font-size: 12px;
    color: var(--color-slate-light);
    font-style: italic;
    line-height: 1.45;
  }

  .paper-body-text {
    font-size: 13.5px;
    line-height: 1.7;
    color: #1e293b;
    white-space: pre-wrap;
    background: #fafaf8;
    border: 1px solid #eeebe2;
    border-radius: 4px;
    padding: 14px 16px;
  }

  .paper-body-empty {
    font-size: 12px;
    color: var(--color-slate-muted);
    font-style: italic;
    padding: 8px 0;
  }

  .paper-sources-footer {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-top: 4px;
  }

  .sources-eyebrow {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: var(--color-slate-muted);
  }

  .sources-tags-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .paper-source-chip {
    font-size: 10px;
    color: #0369a1;
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    padding: 2px 7px;
    border-radius: 4px;
  }

  .paper-empty-notice {
    text-align: center;
    color: var(--color-slate-muted);
    padding: 48px 16px;
    font-style: italic;
    font-size: 13px;
  }

  /* PDF Reader in Center Stage */
  .pdf-document-container {
    width: 100%;
    max-width: 860px;
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    overflow: hidden;
  }

  .pdf-container-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    background: #f8fafc;
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .pdf-badge {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-heading);
  }

  .btn-open-tab {
    font-size: 11px;
    font-weight: 600;
    color: #2563eb;
    text-decoration: none;
    padding: 2px 6px;
    border-radius: 4px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
  }

  .pdf-embed-box {
    height: 720px;
    min-height: 520px;
    background: #0f172a;
    position: relative;
  }

  /* Empty Hero */
  .hero-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 40px 20px;
    text-align: center;
    color: var(--color-slate-muted);
  }

  .empty-hero-icon { font-size: 40px; margin-bottom: 8px; }
  .hero-empty-state h3 { font-size: 16px; color: var(--color-heading); margin: 0 0 6px; }
  .hero-empty-state p { max-width: 360px; font-size: 12.5px; margin: 0; line-height: 1.5; }

  /* ── 3. RIGHT SIDEBAR: Evaluator Workbench Gutter ────────────── */
  .canvas-workbench-gutter {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }

  /* Pinned Finalization Bar */
  .gutter-finalization-bar {
    padding: 8px 12px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .gutter-grade-form {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .grade-input-group {
    display: flex;
    gap: 8px;
  }

  .field-label-mini {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .field-label-mini.feedback-flex {
    flex: 1;
    min-width: 0;
  }

  .field-label-mini span {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    color: var(--color-slate-muted);
  }

  .input-grade-compact {
    width: 68px;
    padding: 4px 7px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .input-feedback-compact {
    width: 100%;
    padding: 4px 7px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .input-grade-compact:focus,
  .input-feedback-compact:focus {
    outline: none;
    border-color: #4f6bff;
  }

  .btn-finalize-compact {
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 700;
    background: #059669;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.12s;
    width: 100%;
  }

  .btn-finalize-compact:hover:not(:disabled) {
    background: #047857;
  }

  .btn-finalize-compact:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .gutter-sealed-banner,
  .gutter-draft-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 11px;
  }

  .gutter-sealed-banner {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
  }

  .gutter-draft-banner {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
  }

  .sealed-check {
    color: #059669;
    font-weight: 700;
  }

  .draft-dot {
    color: #0369a1;
  }

  .sealed-text,
  .draft-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .sealed-text strong,
  .draft-text strong {
    font-size: 11px;
    color: var(--color-heading);
  }

  .sealed-text small,
  .draft-text small {
    font-size: 9.5px;
    color: var(--color-slate-muted);
  }

  .btn-sealed-pdf,
  .btn-recorder-link {
    font-size: 10.5px;
    font-weight: 600;
    color: inherit;
    text-decoration: underline;
  }

  /* Gutter Tabs Bar */
  .gutter-tabs-bar {
    display: flex;
    border-bottom: 1px solid var(--color-graphite-border);
    background: #ffffff;
    flex-shrink: 0;
  }

  .gutter-tab-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 6px;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-muted);
    cursor: pointer;
    transition: all 0.12s;
    font-family: inherit;
  }

  .gutter-tab-btn:hover {
    background: var(--color-bone, #f6f5f1);
    color: var(--color-heading);
  }

  .gutter-tab-btn.active {
    color: #0f172a;
    border-bottom-color: #4f6bff;
    font-weight: 700;
    background: #ffffff;
  }

  .gutter-tab-count {
    font-size: 9.5px;
    background: var(--color-bone, #f6f5f1);
    color: var(--color-slate-muted);
    padding: 1px 5px;
    border-radius: 999px;
    border: 1px solid var(--color-graphite-border);
  }

  .gutter-tab-count.alert {
    background: #fef3c7;
    color: #92400e;
    border-color: #fde68a;
  }

  /* Gutter Tab Viewport (Independently Scrolling) */
  .gutter-tab-viewport {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px 40px;
  }

  .tab-empty-msg {
    color: var(--color-slate-muted);
    font-size: 11.5px;
    font-style: italic;
    text-align: center;
    padding: 24px 0;
  }

  /* Rubric Matrix */
  .rubric-matrix-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .criterion-chip-card {
    background: #fafaf8;
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid #d97706;
    border-radius: 4px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .criterion-chip-card.met {
    border-left-color: #059669;
    background: #ffffff;
  }

  .criterion-chip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .criterion-tag {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #92400e;
  }

  .criterion-tag.met {
    color: #047857;
  }

  .criterion-conf-pill {
    font-size: 9.5px;
    color: var(--color-slate-muted);
    font-weight: 600;
  }

  .criterion-label {
    font-size: 12px;
    color: var(--color-heading);
  }

  .criterion-explanation-text {
    font-size: 11px;
    color: var(--color-slate-light);
    margin: 0;
    line-height: 1.4;
  }

  .criterion-quote-block {
    background: #f4f5f0;
    padding: 6px 8px;
    border-radius: 4px;
    margin-top: 2px;
  }

  .quote-header {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-muted);
    display: block;
    margin-bottom: 2px;
  }

  .quote-text {
    font-size: 11px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-bright);
    line-height: 1.4;
  }

  .criterion-note {
    font-size: 10px;
    color: var(--color-slate-muted);
    font-style: italic;
    display: block;
  }

  /* Traps Inspector */
  .trap-scan-prompt,
  .trap-clean-prompt {
    text-align: center;
    padding: 24px 14px;
    background: #fafaf8;
    border: 1px dashed var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }

  .trap-scan-icon { font-size: 28px; }
  .clean-check-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #ecfdf5;
    color: #059669;
    font-size: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  .trap-scan-prompt h4,
  .trap-clean-prompt h4 {
    margin: 0;
    font-size: 13.5px;
    color: var(--color-heading);
  }

  .trap-scan-desc,
  .clean-desc {
    font-size: 11.5px;
    color: var(--color-slate-light);
    margin: 0;
    line-height: 1.45;
  }

  .btn-trigger-scan {
    padding: 7px 14px;
    font-size: 11.5px;
    font-weight: 700;
    color: #ffffff;
    background: #0b4a4f;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 4px;
  }

  .btn-trigger-scan:disabled { opacity: 0.55; cursor: default; }

  .scan-running-note {
    font-size: 10.5px;
    color: var(--color-slate-muted);
    margin: 2px 0 0;
  }

  .btn-rescan-ghost {
    padding: 4px 10px;
    font-size: 10.5px;
    font-weight: 600;
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-light);
    margin-top: 4px;
  }

  .traps-results-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 10px;
  }

  .traps-count-label {
    font-size: 11px;
    font-weight: 700;
    color: #b45309;
  }

  .btn-rescan-mini {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 10px;
    padding: 2px 6px;
    cursor: pointer;
    color: var(--color-slate-muted);
  }

  .traps-cards-flow {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .trap-item-card {
    border: 1px solid rgba(216, 154, 58, 0.4);
    border-left: 3px solid #d97706;
    border-radius: 4px;
    padding: 10px 12px;
    background: #fffdfa;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .trap-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
  }

  .trap-item-name {
    font-size: 12.5px;
    color: #92400e;
  }

  .trap-item-badge {
    font-size: 9px;
    text-transform: uppercase;
    padding: 1px 6px;
    border-radius: 999px;
    background: rgba(216, 154, 58, 0.18);
    color: #8c6212;
    font-weight: 700;
  }

  .trap-item-badge.weak {
    background: rgba(148, 163, 184, 0.2);
    color: #64748b;
  }

  .trap-flawed-rule {
    margin: 0;
    font-size: 11.5px;
    line-height: 1.4;
    color: var(--color-heading);
  }

  .trap-quote-box {
    background: rgba(216, 154, 58, 0.08);
    border-left: 2px solid #d97706;
    padding: 5px 8px;
    border-radius: 0 4px 4px 0;
  }

  .quote-eyebrow {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #b45309;
    display: block;
    margin-bottom: 2px;
  }

  .trap-quote-text {
    margin: 0;
    font-size: 11.5px;
    font-style: italic;
    color: #1e293b;
    line-height: 1.4;
  }

  .trap-why-text {
    margin: 0;
    font-size: 11px;
    color: var(--color-slate-light);
    line-height: 1.4;
  }

  .trap-remediation-line {
    font-size: 11px;
    color: var(--color-slate-light);
  }

  .remed-label {
    font-weight: 700;
    color: #0b4a4f;
    font-size: 9px;
    text-transform: uppercase;
  }

  .trap-card-actions {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-top: 4px;
  }

  .btn-draft-note {
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #0b4a4f;
    background: #0b4a4f;
    color: #fff;
    cursor: pointer;
  }

  .trap-concept-link {
    font-size: 10.5px;
    color: #0b4a4f;
    text-decoration: none;
    border-bottom: 1px solid currentColor;
  }

  .inline-socratic-draft {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed rgba(148, 163, 184, 0.45);
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .draft-field-label {
    font-size: 9px;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--color-slate-muted);
  }

  .draft-subject-input,
  .draft-body-input {
    width: 100%;
    font: inherit;
    font-size: 11.5px;
    line-height: 1.4;
    padding: 5px 7px;
    border-radius: 4px;
    border: 1px solid var(--color-graphite-border);
    background: #ffffff;
    box-sizing: border-box;
  }

  .draft-action-btns {
    display: flex;
    gap: 4px;
    margin-top: 4px;
  }

  .btn-mail {
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 8px;
    background: #0b4a4f;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-copy,
  .btn-close {
    font-size: 10.5px;
    padding: 4px 8px;
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-light);
  }

  .trap-scan-error {
    font-size: 11.5px;
    color: #b91c1c;
    margin-top: 8px;
  }

  /* Trace Inspector */
  .trace-sub-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 10px;
    gap: 6px;
  }

  .trace-toggle-buttons {
    display: flex;
    gap: 4px;
  }

  .btn-trace-sub {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    color: var(--color-slate-muted);
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 6px;
    cursor: pointer;
  }

  .btn-trace-sub.active {
    background: rgba(217, 119, 6, 0.12);
    border-color: rgba(217, 119, 6, 0.35);
    color: #92400e;
  }

  .btn-flight-recorder {
    background: #ecfdf5;
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: 4px;
    color: #065f46;
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 6px;
    text-decoration: none;
  }

  /* Shared Load / Error / Notice States */
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: var(--color-slate-light);
    height: 100%;
    min-height: 200px;
  }

  .spinner {
    animation: spin 0.8s linear infinite;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-radius: 50%;
    border-top-color: #d97706;
    height: 22px;
    width: 22px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .load-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: #fef2f2;
    border: 1px solid rgba(220, 38, 38, 0.2);
    border-radius: var(--radius-md, 8px);
    padding: 24px;
    margin: 20px;
    text-align: center;
  }

  .load-error strong { color: #991b1b; }
  .load-error p { color: var(--color-slate-light); font-size: 12px; margin: 0; }

  .toast-notice {
    position: absolute;
    bottom: 16px;
    right: 18px;
    border-radius: 4px;
    font-size: 11.5px;
    padding: 8px 12px;
    z-index: 50;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .toast-notice.success {
    background: #ecfdf5;
    border: 1px solid rgba(5, 150, 105, 0.25);
    color: #065f46;
  }

  .toast-notice.error {
    background: #fef2f2;
    border: 1px solid rgba(220, 38, 38, 0.25);
    color: #991b1b;
  }

  /* ── Responsive adjustments ─────────────────────────────────── */
  @media (max-width: 1200px) {
    .canvas-3col-workspace {
      grid-template-columns: 240px minmax(0, 1fr) 340px;
    }
  }

  @media (max-width: 960px) {
    .canvas-3col-workspace {
      grid-template-columns: 1fr;
      grid-template-rows: auto auto auto;
      overflow-y: auto;
    }

    .canvas-roster-sidebar {
      height: 200px;
      border-right: none;
      border-bottom: 1px solid var(--color-graphite-border);
    }

    .canvas-document-hero {
      border-right: none;
      border-bottom: 1px solid var(--color-graphite-border);
    }
  }
</style>
