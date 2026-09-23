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
  } = $props();

  let courseId = $state(propCourseId || '');
  let assignmentId = $state(propAssignmentId || '');
  let filterStatus = $state('all'); // 'all' | 'completed' | 'submitted' | 'active'
  let searchQuery = $state('');

  // UI state for the educator workspace
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

  // Quick-Flipper index navigation
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

  // Derived student work deliverables
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
      notice = `Grade ${grade.trim()} finalized for ${selected.student_id}. Session is sealed in event log.`;
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

<main class="review-main" class:embedded-container={!!assignmentId}>
  {#if !assignmentId}
    <!-- Standalone Mode Header -->
    <header class="review-header">
      <div>
        <div class="eyebrow">Educator Workspace</div>
        <h1>Evaluation Window</h1>
        <p>Review submitted assignments, examine student intellectual progression, and exercise sovereign grade authority.</p>
      </div>
      <div class="queue-count">
        <span>Submissions In Queue</span>
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
      <button class="btn btn-secondary" onclick={loadQueue}>Try again</button>
    </section>
  {:else}
    <div class="review-layout" class:roster-hidden={isRosterCollapsed}>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- COLLAPSIBLE ROSTER SIDEBAR                                 -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      {#if !isRosterCollapsed}
        <aside class="roster-sidebar">
          <div class="roster-top-bar">
            <span class="roster-top-title">Student Roster ({filteredQueue.length})</span>
            <button
              type="button"
              class="btn-collapse-sidebar"
              onclick={() => (isRosterCollapsed = true)}
              title="Collapse student roster to maximize evaluation width"
            >
              ⇤
            </button>
          </div>

          <div class="roster-header">
            <input
              type="text"
              class="roster-search"
              placeholder="Search student or task…"
              bind:value={searchQuery}
            />
            <div class="roster-filters">
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
              >Finalized ({completedCount})</button>
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

          <div class="roster-list">
            {#if filteredQueue.length === 0}
              <div class="roster-empty">No students match this filter.</div>
            {:else}
              {#each filteredQueue as item (item.session_id)}
                <button
                  type="button"
                  class="roster-card"
                  class:active={selected?.session_id === item.session_id}
                  onclick={() => selectItem(item)}
                >
                  <span class="roster-avatar">{item.student_id.slice(0, 2).toUpperCase()}</span>
                  <div class="roster-card-info">
                    <span class="roster-name">{item.student_id}</span>
                    {#if !assignmentId && item.assignment_title}
                      <span class="roster-assignment-tag" title={item.assignment_title}>{item.assignment_title}</span>
                    {/if}
                    <span class="roster-time">{formatDate(item.submitted_at)}</span>
                  </div>
                  {#if item.status === 'submitted'}
                    <span class="roster-badge submitted">Ready</span>
                  {:else if item.status === 'completed'}
                    <span class="roster-badge completed">Finalized</span>
                  {:else}
                    <span class="roster-badge in-progress">Draft</span>
                  {/if}
                </button>
              {/each}
            {/if}
          </div>

          <button type="button" class="roster-refresh" onclick={loadQueue} title="Check for new submissions">
            ↻ Refresh Roster
          </button>
        </aside>
      {:else}
        <!-- Collapsed Roster Rail -->
        <aside class="roster-rail" onclick={() => (isRosterCollapsed = false)} title="Click to expand student roster">
          <button type="button" class="btn-expand-rail" onclick={() => (isRosterCollapsed = false)} title="Expand student roster">
            ⇥
          </button>
          <div class="rail-label">ROSTER ({filteredQueue.length})</div>
        </aside>
      {/if}

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- EVALUATION WORKSPACE: Side-by-Side Dual-Pane Layout        -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section class="dossier-pane">
        {#if !selected}
          <div class="empty-dossier">
            <div class="empty-icon">📋</div>
            <strong>No student selected for evaluation</strong>
            <p>Select a learner from the student roster on the left to inspect their submitted deliverables and reasoning trace.</p>
          </div>
        {:else if !dossier}
          <div class="loading small"><div class="spinner"></div><span>Opening evaluation dossier…</span></div>
        {:else}
          <!-- Unified Dossier Header with Quick-Flipper & Document Controls -->
          <header class="dossier-header-bar">
            <div class="dossier-student-info">
              <span class="dossier-avatar">{selected.student_id.slice(0, 2).toUpperCase()}</span>
              <div>
                <div class="dossier-title-line">
                  <h2>{selected.student_id}</h2>
                  <div
                    class="status-badge"
                    class:submitted={selected.status === 'submitted'}
                    class:completed={selected.status === 'completed'}
                    class:in-progress={selected.status !== 'submitted' && selected.status !== 'completed'}
                  >
                    {#if selected.status === 'submitted'}
                      <span>✓ Ready for Grading</span>
                    {:else if selected.status === 'completed'}
                      <span>✓ Grade Finalized</span>
                    {:else}
                      <span>● In Progress (Live Draft)</span>
                    {/if}
                  </div>
                </div>
                <p class="dossier-sub">
                  {#if selected.assignment_title}
                    <span class="dossier-assignment-name">{selected.assignment_title}</span> &bull;
                  {/if}
                  {selected.status === 'submitted' ? 'Submitted' : selected.status === 'completed' ? 'Finalized' : 'Last Active'}: {formatDate(selected.submitted_at)}
                </p>
              </div>
            </div>

            <!-- Cohort Quick-Flipper -->
            <div class="quick-flipper">
              <button
                type="button"
                class="flipper-btn"
                onclick={selectPrevStudent}
                disabled={currentStudentIndex <= 0}
                title="Go to previous student in queue"
              >
                ‹ Prev
              </button>
              <span class="flipper-counter">
                {currentStudentIndex >= 0 ? `${currentStudentIndex + 1} of ${filteredQueue.length}` : '—'}
              </span>
              <button
                type="button"
                class="flipper-btn"
                onclick={selectNextStudent}
                disabled={currentStudentIndex < 0 || currentStudentIndex >= filteredQueue.length - 1}
                title="Go to next student in queue"
              >
                Next ›
              </button>
            </div>

            <!-- Deliverables View Toggles & Actions -->
            <div class="dossier-header-actions">
              <div class="work-view-selector">
                <button
                  type="button"
                  class="work-view-btn"
                  class:active={activeWorkTab === 'sections'}
                  onclick={() => (activeWorkTab = 'sections')}
                  title="View written canvas sections"
                >
                  📝 Sections
                </button>
                <button
                  type="button"
                  class="work-view-btn"
                  class:active={activeWorkTab === 'pdf'}
                  onclick={() => (activeWorkTab = 'pdf')}
                  title="Render student's submitted assignment as a PDF document"
                >
                  📄 PDF
                </button>
              </div>

              <a
                class="btn-download-pdf"
                href={`/evidence/dossier/${selected.session_id}/pdf`}
                download
                title="Download assignment submission as a PDF"
              >
                <span class="btn-icon">⬇</span> PDF
              </a>
            </div>
          </header>

          <!-- ── Side-by-Side Dual-Pane Grid ──────────────────────────── -->
          <div class="eval-dual-workspace">

            <!-- ── LEFT PANE: Student Deliverables Academic Reader ────── -->
            <div class="eval-document-pane">
              <div class="pane-header-bar">
                <div class="pane-title-group">
                  <span class="pane-icon">📝</span>
                  <span class="pane-title">Student Deliverables</span>
                </div>
                <div class="pane-meta-badge">
                  {displaySections.length} {displaySections.length === 1 ? 'Section' : 'Sections'}
                  {#if totalDeliverableWords > 0}
                    &bull; ~{totalDeliverableWords} words
                  {/if}
                </div>
              </div>

              <div class="document-scroll-viewport">
                {#if activeWorkTab === 'pdf'}
                  <!-- Rendered PDF View -->
                  <div class="pdf-reader-card">
                    <div class="pdf-reader-toolbar">
                      <div class="pdf-reader-title">
                        <span>📄</span>
                        <strong>Official Submission Document</strong>
                      </div>
                      <div class="pdf-reader-actions">
                        <a
                          class="btn-action-ghost"
                          href={`/evidence/dossier/${selected.session_id}/pdf`}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Open PDF in a new browser tab"
                        >
                          Open in Tab ↗
                        </a>
                        <a
                          class="btn-action-ghost"
                          href={`/evidence/dossier/${selected.session_id}/pdf`}
                          download
                          title="Download PDF to device"
                        >
                          Download ⬇
                        </a>
                      </div>
                    </div>
                    <div class="pdf-render-viewport">
                      {#key selected.session_id}
                        <PdfViewer
                          url={`/evidence/dossier/${selected.session_id}/pdf`}
                          title={`${selected.student_id} - ${selected.assignment_title || 'Assignment Submission'}`}
                        />
                      {/key}
                    </div>
                  </div>
                {:else}
                  <!-- Canvas Sections Continuous Academic Reader -->
                  {#if displaySections.length === 0}
                    <div class="academic-empty-state">
                      <p>No authored work sections recorded for this session.</p>
                    </div>
                  {:else}
                    <div class="academic-document-body">
                      {#each displaySections as sec, sIdx (sec.section_id)}
                        <article class="academic-section-card">
                          <header class="academic-section-header">
                            <div class="academic-section-title-wrap">
                              <span class="section-number-pill">{sIdx + 1}</span>
                              <h3 class="academic-section-title">{sec.title || sec.section_id.replaceAll('_', ' ')}</h3>
                            </div>
                            {#if sec.revision}
                              <span class="revision-tag">Rev {sec.revision}</span>
                            {/if}
                          </header>

                          {#if sec.prompt}
                            <div class="academic-prompt-box">
                              <span class="prompt-label">Prompt:</span>
                              <p class="prompt-text">{sec.prompt}</p>
                            </div>
                          {/if}

                          {#if sec.text}
                            <div class="academic-text-content">{sec.text}</div>
                          {:else}
                            <div class="work-empty-text">No text submitted for this section.</div>
                          {/if}

                          {#if sec.source_references?.length}
                            <div class="academic-sources-box">
                              <span class="sources-label">Cited References:</span>
                              <div class="sources-pills-list">
                                {#each sec.source_references as src}
                                  <span class="source-tag">
                                    📖 {src.document_title || 'Reference'}{src.page_number ? ` (p. ${src.page_number})` : ''}
                                  </span>
                                {/each}
                              </div>
                            </div>
                          {/if}
                        </article>
                      {/each}
                    </div>
                  {/if}
                {/if}
              </div>
            </div>

            <!-- ── RIGHT PANE: Evaluator Workbench ───────────────────── -->
            <div class="eval-workbench-pane">

              <!-- Sticky Sovereign Finalization Bar / Status -->
              <div class="workbench-action-header">
                {#if selected.status === 'submitted'}
                  <div class="grade-action-form">
                    <div class="grade-inputs-row">
                      <label class="grade-input-label">
                        <span>Grade</span>
                        <input
                          type="text"
                          class="grade-input"
                          bind:value={grade}
                          placeholder="A, B+, 92%"
                        />
                      </label>
                      <label class="feedback-input-label">
                        <span>Formative Evaluation Feedback</span>
                        <input
                          type="text"
                          class="feedback-input"
                          bind:value={feedback}
                          placeholder="Actionable feedback for next reasoning cycle…"
                        />
                      </label>
                    </div>
                    <button
                      type="button"
                      class="btn btn-success grade-finalize-btn"
                      onclick={finalise}
                      disabled={isFinalizing || !grade.trim()}
                    >
                      {isFinalizing ? 'Finalizing…' : 'Finalize Grade & Seal ➔'}
                    </button>
                  </div>
                {:else if selected.status === 'completed'}
                  <div class="status-banner completed-banner">
                    <span class="banner-badge">✓ Grade Finalized</span>
                    <span class="banner-text">Submission officially graded and sealed in ledger.</span>
                    <a class="btn-banner-link" href={`/evidence/dossier/${selected.session_id}/pdf`} download>
                      ⬇ Sealed PDF
                    </a>
                  </div>
                {:else}
                  <div class="status-banner inprogress-banner">
                    <span class="banner-badge">● Live Draft</span>
                    <span class="banner-text">Student is currently in an active reasoning session.</span>
                    <a class="btn-banner-link" href={`#/student/trace?session_id=${selected.session_id}`}>
                      Flight Recorder ↗
                    </a>
                  </div>
                {/if}
              </div>

              <!-- Workbench Tabs Navigation -->
              <nav class="eval-tabs-bar">
                <button
                  type="button"
                  class="eval-tab-btn"
                  class:active={activeEvalTab === 'rubric'}
                  onclick={() => (activeEvalTab = 'rubric')}
                >
                  <span class="tab-icon">📊</span>
                  <span>Rubric Assessment</span>
                  <span class="tab-count-pill">{totalRubricCriteria}</span>
                </button>

                <button
                  type="button"
                  class="eval-tab-btn"
                  class:active={activeEvalTab === 'traps'}
                  onclick={() => (activeEvalTab = 'traps')}
                >
                  <span class="tab-icon">🪤</span>
                  <span>Misconceptions & Traps</span>
                  <span class="tab-count-pill" class:highlight={scan && (scan.findings || []).length > 0}>
                    {scan ? (scan.findings || []).length : 'Scan'}
                  </span>
                </button>

                <button
                  type="button"
                  class="eval-tab-btn"
                  class:active={activeEvalTab === 'reasoning'}
                  onclick={() => (activeEvalTab = 'reasoning')}
                >
                  <span class="tab-icon">💡</span>
                  <span>Reasoning Trace</span>
                  <span class="tab-count-pill">{reasoningNodes.length + activityNodes.length}</span>
                </button>
              </nav>

              <!-- Workbench Tab Body Container -->
              <div class="eval-tab-viewport">

                <!-- ════ TAB 1: Rubric Assessment ════ -->
                {#if activeEvalTab === 'rubric'}
                  <div class="rubric-tab-content">
                    {#if !dossier.per_question_evidence || dossier.per_question_evidence.length === 0}
                      <p class="tab-empty">No rubric evaluation criteria published for this assignment.</p>
                    {:else}
                      <div class="rubric-summary-bar">
                        <span class="rubric-summary-title">Evidence Entailment Matrix</span>
                        <span class="rubric-summary-note">Scored against authored curriculum rubrics</span>
                      </div>

                      <div class="criteria-list">
                        {#each dossier.per_question_evidence as question}
                          {#each Object.entries(question.rubric_evidence || {}) as [, criterion]}
                            <article class="criterion-card" class:met={criterion.met}>
                              <header class="criterion-header">
                                <div class="criterion-badge-row">
                                  <span class="criterion-status-tag" class:met={criterion.met}>
                                    {criterion.met ? '✓ Evidence Met' : '● Needs Review'}
                                  </span>
                                  <span class="criterion-confidence">
                                    Confidence: {Math.round((criterion.confidence || 0) * 100)}%
                                  </span>
                                </div>
                                <strong class="criterion-title">
                                  {criterion.label || (criterion.met ? 'Standard Met' : 'Criterion Pending')}
                                </strong>
                              </header>

                              <p class="criterion-desc">{criterion.description}</p>

                              {#if criterion.evidence}
                                <div class="criterion-quote-box">
                                  <span class="quote-label">Direct Submission Quote:</span>
                                  <div class="criterion-quote">{criterion.evidence}</div>
                                </div>
                              {/if}

                              {#if criterion.explanation}
                                <small class="criterion-explanation">{criterion.explanation}</small>
                              {/if}
                            </article>
                          {/each}
                        {/each}
                      </div>
                    {/if}
                  </div>

                <!-- ════ TAB 2: Misconceptions & Cognitive Traps ════ -->
                {:else if activeEvalTab === 'traps'}
                  <div class="traps-tab-content">
                    {#if !scan}
                      <div class="traps-unscanned-box">
                        <div class="traps-unscanned-icon">🪤</div>
                        <h4>Misconception & Cognitive Trap Scan</h4>
                        <p class="trap-intro">
                          Reads the student's submitted text against cognitive traps and flawed mental models
                          authored in the course knowledge graph, surfacing verified textual evidence.
                        </p>
                        <button
                          type="button"
                          class="trap-scan-btn"
                          onclick={runMisconceptionScan}
                          disabled={isScanning}
                        >
                          {isScanning ? 'Analyzing submission with LLM…' : '⚡ Analyze This Submission'}
                        </button>
                        {#if isScanning}
                          <p class="trap-note">Examining student thesis against cognitive traps (takes ~20-30s)…</p>
                        {/if}
                      </div>
                    {:else if (scan.findings || []).length === 0}
                      <div class="traps-clear-box">
                        <span class="clear-check">✓</span>
                        <h4>No Cognitive Traps Evidenced</h4>
                        <p class="trap-clear-note">The student avoided known mental traps for this inquiry.</p>
                        {#if scan.note}<p class="trap-note">{scan.note}</p>{/if}
                        <button
                          type="button"
                          class="trap-rescan-btn"
                          onclick={runMisconceptionScan}
                          disabled={isScanning}
                        >
                          Re-Analyze Submission
                        </button>
                      </div>
                    {:else}
                      <div class="traps-findings-header">
                        <span class="traps-found-count">
                          {(scan.findings || []).length} Cognitive {(scan.findings || []).length === 1 ? 'Trap' : 'Traps'} Identified
                        </span>
                        <button
                          type="button"
                          class="trap-rescan-btn-inline"
                          onclick={runMisconceptionScan}
                          disabled={isScanning}
                        >
                          ↻ Re-scan
                        </button>
                      </div>

                      <div class="traps-list">
                        {#each scan.findings as finding}
                          <article class="trap-card">
                            <header class="trap-head">
                              <strong class="trap-title">{finding.name}</strong>
                              <span class="trap-method" class:weak={finding.detection !== 'llm_verified'}>
                                {finding.detection === 'llm_verified' ? 'Evidenced' : 'Candidate'}
                              </span>
                            </header>

                            <p class="trap-rule">{finding.flawed_rule}</p>

                            {#if finding.evidence_quote}
                              <div class="trap-quote-wrap">
                                <span class="trap-quote-label">Student excerpt:</span>
                                <blockquote class="trap-quote">"{finding.evidence_quote}"</blockquote>
                              </div>
                              <p class="trap-why">{finding.why}</p>
                            {/if}

                            {#if finding.remediation_hint}
                              <p class="trap-refer">
                                <span class="trap-refer-label">Remediation focus:</span> {finding.remediation_hint}
                              </p>
                            {/if}

                            <div class="trap-actions">
                              <button
                                type="button"
                                class="trap-draft-btn"
                                onclick={() => openDraft(finding)}
                              >
                                ✉ Draft Socratic Intervention
                              </button>
                              {#if finding.concept_id}
                                <a
                                  class="trap-graph-link"
                                  href={`/#/knowledge-graph?course_id=${courseId}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  Explore in graph ↗
                                </a>
                              {/if}
                            </div>

                            {#if draftOpenFor === finding.misconception_id}
                              <div class="trap-draft">
                                <label class="trap-draft-label" for="draft-subject">Intervention Subject</label>
                                <input
                                  id="draft-subject"
                                  class="trap-draft-subject"
                                  bind:value={draftSubject}
                                />
                                <label class="trap-draft-label" for="draft-body">Formative Guidance Message</label>
                                <textarea
                                  id="draft-body"
                                  class="trap-draft-body"
                                  rows="8"
                                  bind:value={draftBody}
                                ></textarea>
                                <p class="trap-note">
                                  Points the learner toward source material through Socratic questioning rather than giving answers.
                                </p>
                                <div class="trap-draft-actions">
                                  <button type="button" class="trap-send" onclick={openInMailClient}>Open in Mail</button>
                                  <button type="button" class="trap-copy" onclick={copyDraft}>Copy to Clipboard</button>
                                  <button type="button" class="trap-cancel" onclick={() => (draftOpenFor = '')}>Close</button>
                                </div>
                              </div>
                            {/if}
                          </article>
                        {/each}
                      </div>
                      {#if scan.note}<p class="trap-note">{scan.note}</p>{/if}
                    {/if}

                    {#if scanError}
                      <p class="trap-error">{scanError}</p>
                    {/if}
                  </div>

                <!-- ════ TAB 3: Reasoning & Engagement Trace ════ -->
                {:else if activeEvalTab === 'reasoning'}
                  <div class="reasoning-tab-content">
                    <div class="reasoning-subnav">
                      <div class="reasoning-pills">
                        <button
                          type="button"
                          class="acc-tab-btn"
                          class:active={activeReviewTimelineTab === 'reasoning'}
                          onclick={() => (activeReviewTimelineTab = 'reasoning')}
                        >
                          💡 Intellectual Milestones ({reasoningNodes.length})
                        </button>
                        <button
                          type="button"
                          class="acc-tab-btn"
                          class:active={activeReviewTimelineTab === 'activity'}
                          onclick={() => (activeReviewTimelineTab = 'activity')}
                        >
                          ⏱️ Activity Log ({activityNodes.length})
                        </button>
                      </div>
                      <a
                        class="acc-flight-link"
                        href={`#/student/trace?session_id=${selected.session_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Flight Recorder ↗
                      </a>
                    </div>

                    <div class="timeline-container">
                      {#if activeReviewTimelineTab === 'reasoning'}
                        {#if reasoningNodes.length === 0}
                          <p class="tab-empty">No reasoning trace events logged yet for this session.</p>
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
                          <p class="tab-empty">No activity events logged for this session.</p>
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
            </div>

          </div>
        {/if}
      </section>

    </div>
  {/if}

  {#if notice}<div class="notice success">{notice}</div>{/if}
  {#if error && queue.length > 0}<div class="notice error">{error}</div>{/if}
</main>

<style>
  /* ================================================================
     BASE LAYOUT & CONTAINER
     ================================================================ */
  .review-main {
    max-width: 1600px;
    margin: 0 auto;
    padding: 24px 28px 80px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    font-family: var(--font-ui, system-ui, sans-serif);
  }

  .review-main.embedded-container {
    padding: 0;
    max-width: 100%;
    margin: 0;
  }

  /* ── Standalone Mode Header ──────────────────────────────────── */
  .review-header {
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 20px;
    padding-bottom: 16px;
  }

  .eyebrow {
    color: var(--color-slate-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.55px;
    text-transform: uppercase;
  }

  .review-header h1 {
    color: var(--color-heading);
    font-family: var(--font-brand, "Newsreader", serif);
    font-size: 26px;
    margin: 4px 0 6px;
  }

  .review-header p {
    color: var(--color-slate-light);
    font-size: 13px;
    line-height: 1.5;
    margin: 0;
    max-width: 740px;
  }

  .queue-count {
    background: var(--color-aurora-glow, rgba(2, 132, 199, 0.12));
    border: 1px solid rgba(2, 132, 199, 0.28);
    border-radius: var(--radius-md, 8px);
    display: flex;
    flex-direction: column;
    padding: 8px 14px;
    text-align: right;
  }

  .queue-count span {
    color: var(--color-slate-muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  .queue-count strong {
    color: var(--color-aurora-bright, #0369a1);
    font-family: var(--font-brand, serif);
    font-size: 22px;
  }

  /* ================================================================
     REVIEW LAYOUT: ROSTER SIDEBAR + WORKSPACE
     ================================================================ */
  .review-layout {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    gap: 0;
    align-items: stretch;
    min-height: calc(100vh - 220px);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    background: var(--color-bone-surface, #fff);
    overflow: hidden;
  }

  .review-layout.roster-hidden {
    grid-template-columns: 44px minmax(0, 1fr);
  }

  /* ── Left Sidebar: Student Roster ────────────────────────────── */
  .roster-sidebar {
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--color-graphite-border);
    background: var(--color-graphite, #f8f9f5);
    height: calc(100vh - 220px);
    overflow: hidden;
  }

  .roster-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border-bottom: 1px solid var(--color-graphite-border);
    background: var(--color-bone, #f6f5f1);
  }

  .roster-top-title {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .btn-collapse-sidebar {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    font-size: 13px;
    padding: 2px 7px;
    color: var(--color-slate-muted);
    transition: all 0.15s ease;
  }

  .btn-collapse-sidebar:hover {
    background: var(--color-graphite-hover, #eee);
    color: var(--color-heading);
  }

  /* Collapsed Roster Rail */
  .roster-rail {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 14px 4px;
    gap: 16px;
    background: var(--color-graphite, #f8f9f5);
    border-right: 1px solid var(--color-graphite-border);
    cursor: pointer;
    transition: background 0.15s;
  }

  .roster-rail:hover {
    background: var(--color-bone-muted, #f4f5f0);
  }

  .btn-expand-rail {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    font-size: 13px;
    padding: 4px 6px;
    color: var(--color-slate-muted);
  }

  .rail-label {
    writing-mode: vertical-rl;
    text-orientation: mixed;
    transform: rotate(180deg);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--color-slate-muted);
  }

  .roster-header {
    padding: 12px 14px 10px;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .roster-search {
    width: 100%;
    padding: 7px 10px;
    font-size: 12px;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    background: var(--color-bone-surface, #fff);
    color: var(--color-slate-bright);
    font-family: var(--font-ui);
    box-sizing: border-box;
  }

  .roster-search:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .roster-filters {
    display: flex;
    gap: 4px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  .filter-pill {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: 999px;
    color: var(--color-slate-muted);
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    cursor: pointer;
    transition: all 0.15s ease;
    font-family: var(--font-ui);
  }

  .filter-pill:hover {
    background: var(--pill-hover, rgba(0, 0, 0, 0.07));
    color: var(--color-slate-bright);
  }

  .filter-pill.active {
    background: var(--pill-active-bg, rgba(217, 119, 6, 0.14));
    border-color: var(--pill-active-border, rgba(217, 119, 6, 0.35));
    color: var(--pill-active-color, #92400e);
  }

  .roster-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .roster-empty {
    color: var(--color-slate-muted);
    font-size: 11.5px;
    text-align: center;
    padding: 24px 10px;
    font-style: italic;
  }

  .roster-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 11px;
    background: var(--color-bone-surface, #fff);
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid transparent;
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    text-align: left;
    width: 100%;
    transition: all 0.15s ease;
    font-family: var(--font-ui);
    color: inherit;
  }

  .roster-card:hover {
    border-left-color: var(--color-horizon-blue, #4f6bff);
    background: var(--color-graphite-hover, #f1f2ed);
  }

  .roster-card.active {
    border-left-color: var(--color-horizon-bright, #d97706);
    background: var(--color-horizon-glow, rgba(217, 119, 6, 0.08));
    box-shadow: inset 0 0 0 1px rgba(217, 119, 6, 0.15);
  }

  .roster-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #0ea5e9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }

  .roster-card-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .roster-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-heading);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .roster-assignment-tag {
    font-size: 10px;
    color: var(--color-slate-light);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .roster-time {
    font-size: 9.5px;
    color: var(--color-slate-muted);
  }

  .roster-badge {
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 999px;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .roster-badge.submitted {
    background: var(--color-signal-green-bg, #ecfdf5);
    color: var(--color-signal-green-text, #065f46);
    border: 1px solid rgba(5, 150, 105, 0.2);
  }

  .roster-badge.completed {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  .roster-badge.in-progress {
    background: var(--color-aurora-glow, rgba(2, 132, 199, 0.12));
    color: var(--color-aurora-bright, #0369a1);
    border: 1px solid rgba(2, 132, 199, 0.2);
  }

  .roster-refresh {
    flex-shrink: 0;
    padding: 8px;
    font-size: 10.5px;
    font-weight: 600;
    color: var(--color-horizon-bright, #d97706);
    background: none;
    border: none;
    border-top: 1px solid var(--color-graphite-border);
    cursor: pointer;
    font-family: var(--font-ui);
    transition: background 0.15s;
  }

  .roster-refresh:hover {
    background: var(--color-graphite-hover, #f1f2ed);
  }

  /* ================================================================
     DOSSIER PANE: MAIN WORKSPACE CONTAINER
     ================================================================ */
  .dossier-pane {
    display: flex;
    flex-direction: column;
    background: var(--color-bone-surface, #fff);
    height: calc(100vh - 220px);
    overflow: hidden;
    position: relative;
    min-width: 0;
  }

  /* ── Dossier Header Bar ──────────────────────────────────────── */
  .dossier-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
    padding: 12px 18px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .dossier-student-info {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }

  .dossier-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #3b82f6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }

  .dossier-title-line {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .dossier-title-line h2 {
    color: var(--color-heading);
    font-size: 17px;
    font-family: var(--font-brand, serif);
    margin: 0;
    line-height: 1.2;
  }

  .dossier-sub {
    color: var(--color-slate-muted);
    font-size: 11px;
    margin: 2px 0 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dossier-assignment-name {
    color: var(--color-slate-light);
    font-weight: 600;
  }

  /* Quick Flipper */
  .quick-flipper {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--color-bone-surface, #fff);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    padding: 3px 6px;
    flex-shrink: 0;
  }

  .flipper-btn {
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

  .flipper-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #eee);
    color: var(--color-heading);
  }

  .flipper-btn:disabled {
    opacity: 0.35;
    cursor: default;
  }

  .flipper-counter {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-slate-bright);
    padding: 0 4px;
    white-space: nowrap;
  }

  /* Dossier Header Actions */
  .dossier-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .work-view-selector {
    display: flex;
    background: var(--color-bone-surface, #fff);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    padding: 2px;
  }

  .work-view-btn {
    background: transparent;
    border: none;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-muted);
    transition: all 0.15s;
    font-family: var(--font-ui);
  }

  .work-view-btn:hover {
    color: var(--color-heading);
  }

  .work-view-btn.active {
    background: var(--color-horizon-blue, #4f6bff);
    color: #fff;
  }

  .btn-download-pdf {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 5px 10px;
    border-radius: var(--radius-sm, 6px);
    font-size: 11px;
    font-weight: 600;
    color: #1d4ed8;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-download-pdf:hover {
    background: #dbeafe;
    color: #1e40af;
  }

  .status-badge {
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 700;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .status-badge.submitted,
  .status-badge.completed {
    background: var(--color-signal-green-bg, #ecfdf5);
    color: var(--color-signal-green-text, #065f46);
    border: 1px solid rgba(5, 150, 105, 0.25);
  }

  .status-badge.in-progress {
    background: var(--color-aurora-glow, rgba(2, 132, 199, 0.12));
    color: var(--color-aurora-bright, #0369a1);
    border: 1px solid rgba(2, 132, 199, 0.25);
  }

  /* ================================================================
     EVALUATION SPLIT WORKSPACE: LEFT (DOC) + RIGHT (WORKBENCH)
     ================================================================ */
  .eval-dual-workspace {
    display: grid;
    grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.95fr);
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  /* ── LEFT PANE: Academic Deliverables Reader ─────────────────── */
  .eval-document-pane {
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--color-graphite-border);
    background: var(--color-bone, #f6f5f1);
    min-height: 0;
    overflow: hidden;
  }

  .pane-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 18px;
    background: #ffffff;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .pane-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .pane-icon {
    font-size: 14px;
  }

  .pane-title {
    font-size: 12.5px;
    font-weight: 700;
    color: var(--color-heading);
    letter-spacing: 0.2px;
  }

  .pane-meta-badge {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--color-slate-muted);
    background: var(--color-bone, #f6f5f1);
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid var(--color-graphite-border);
  }

  .document-scroll-viewport {
    flex: 1;
    overflow-y: auto;
    padding: 20px 24px 60px;
  }

  /* Academic Document Cards */
  .academic-document-body {
    display: flex;
    flex-direction: column;
    gap: 20px;
    max-width: 820px;
    margin: 0 auto;
  }

  .academic-section-card {
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .academic-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 10px;
  }

  .academic-section-title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-number-pill {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--color-bone, #f6f5f1);
    border: 1px solid var(--color-graphite-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-slate-light);
  }

  .academic-section-title {
    font-size: 15px;
    font-family: var(--font-brand, serif);
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
    text-transform: capitalize;
  }

  .revision-tag {
    font-size: 10px;
    color: var(--color-slate-muted);
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid var(--color-graphite-border);
  }

  .academic-prompt-box {
    background: #fdfbf7;
    border-left: 3px solid #d97706;
    padding: 8px 12px;
    border-radius: 0 var(--radius-xs, 4px) var(--radius-xs, 4px) 0;
    font-size: 12px;
  }

  .prompt-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #b45309;
    display: block;
    margin-bottom: 2px;
  }

  .prompt-text {
    margin: 0;
    color: var(--color-slate-light);
    font-style: italic;
    line-height: 1.45;
  }

  .academic-text-content {
    font-size: 13.5px;
    line-height: 1.68;
    color: #1e293b;
    white-space: pre-wrap;
    background: #fafaf8;
    border: 1px solid #eceae2;
    border-radius: var(--radius-xs, 4px);
    padding: 14px 16px;
  }

  .work-empty-text {
    font-size: 12px;
    color: var(--color-slate-muted);
    font-style: italic;
    padding: 10px 0;
  }

  .academic-sources-box {
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-top: 1px dashed var(--color-graphite-border);
    padding-top: 8px;
  }

  .sources-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .sources-pills-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .source-tag {
    font-size: 10.5px;
    color: #0369a1;
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    padding: 3px 8px;
    border-radius: 4px;
  }

  .academic-empty-state {
    text-align: center;
    color: var(--color-slate-muted);
    padding: 60px 20px;
    font-style: italic;
    font-size: 13px;
  }

  /* PDF Reader in Left Pane */
  .pdf-reader-card {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    overflow: hidden;
  }

  .pdf-reader-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: #f8fafc;
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .pdf-reader-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--color-heading);
  }

  .pdf-reader-actions {
    display: flex;
    gap: 8px;
  }

  .btn-action-ghost {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-horizon-blue, #2563eb);
    text-decoration: none;
    padding: 3px 7px;
    border-radius: 4px;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
  }

  .btn-action-ghost:hover {
    background: #dbeafe;
  }

  .pdf-render-viewport {
    height: 700px;
    min-height: 520px;
    background: #0f172a;
    position: relative;
  }

  /* ── RIGHT PANE: Evaluator Workbench ──────────────────────────── */
  .eval-workbench-pane {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    min-height: 0;
    overflow: hidden;
  }

  /* Sticky Workbench Header: Sovereign Finalization / Status */
  .workbench-action-header {
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    padding: 12px 16px;
    flex-shrink: 0;
  }

  .grade-action-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .grade-inputs-row {
    display: flex;
    gap: 10px;
  }

  .grade-input-label {
    flex: 0 0 85px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .feedback-input-label {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .grade-input-label span,
  .feedback-input-label span {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .grade-input,
  .feedback-input {
    padding: 6px 9px;
    font-size: 12px;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    background: #ffffff;
    color: var(--color-slate-bright);
    font-family: var(--font-ui);
  }

  .grade-input:focus,
  .feedback-input:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .grade-finalize-btn {
    padding: 7px 12px;
    font-size: 11.5px;
    font-weight: 700;
    cursor: pointer;
    background: #059669;
    color: #fff;
    border: none;
    border-radius: var(--radius-sm, 6px);
    transition: background 0.15s;
    width: 100%;
  }

  .grade-finalize-btn:hover:not(:disabled) {
    background: #047857;
  }

  .grade-finalize-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .status-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: var(--radius-sm, 6px);
    font-size: 11px;
  }

  .status-banner.completed-banner {
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
  }

  .status-banner.inprogress-banner {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
  }

  .banner-badge {
    font-weight: 700;
    color: #065f46;
    white-space: nowrap;
  }

  .inprogress-banner .banner-badge {
    color: #0369a1;
  }

  .banner-text {
    flex: 1;
    color: var(--color-slate-light);
  }

  .btn-banner-link {
    font-size: 11px;
    font-weight: 600;
    color: inherit;
    text-decoration: underline;
    white-space: nowrap;
  }

  /* Workbench Tabs Bar */
  .eval-tabs-bar {
    display: flex;
    border-bottom: 1px solid var(--color-graphite-border);
    background: #ffffff;
    flex-shrink: 0;
    overflow-x: auto;
  }

  .eval-tab-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-muted);
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
    font-family: var(--font-ui);
  }

  .eval-tab-btn:hover {
    color: var(--color-heading);
    background: var(--color-bone-muted, #f4f5f0);
  }

  .eval-tab-btn.active {
    color: #0f172a;
    border-bottom-color: var(--color-horizon-blue, #4f6bff);
    background: #ffffff;
    font-weight: 700;
  }

  .tab-icon {
    font-size: 13px;
  }

  .tab-count-pill {
    font-size: 10px;
    font-weight: 700;
    background: var(--color-bone, #f6f5f1);
    color: var(--color-slate-muted);
    padding: 1px 6px;
    border-radius: 999px;
    border: 1px solid var(--color-graphite-border);
  }

  .tab-count-pill.highlight {
    background: #fef3c7;
    color: #92400e;
    border-color: #fde68a;
  }

  /* Tab Viewport */
  .eval-tab-viewport {
    flex: 1;
    overflow-y: auto;
    padding: 16px 18px 40px;
  }

  .tab-empty {
    color: var(--color-slate-muted);
    font-size: 12px;
    font-style: italic;
    padding: 24px 0;
    text-align: center;
  }

  /* ── Tab 1: Rubric Assessment Styles ─────────────────────────── */
  .rubric-summary-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 12px;
  }

  .rubric-summary-title {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-heading);
  }

  .rubric-summary-note {
    font-size: 10.5px;
    color: var(--color-slate-muted);
  }

  .criteria-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .criterion-card {
    background: #fafaf8;
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid #d97706;
    border-radius: var(--radius-sm, 6px);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .criterion-card.met {
    border-left-color: #059669;
    background: #ffffff;
  }

  .criterion-header {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .criterion-badge-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .criterion-status-tag {
    font-size: 10px;
    font-weight: 700;
    color: #92400e;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .criterion-status-tag.met {
    color: #047857;
  }

  .criterion-confidence {
    font-size: 10px;
    font-weight: 600;
    color: var(--color-slate-muted);
  }

  .criterion-title {
    font-size: 13px;
    color: var(--color-heading);
  }

  .criterion-desc {
    color: var(--color-slate-light);
    font-size: 12px;
    margin: 0;
    line-height: 1.45;
  }

  .criterion-quote-box {
    margin-top: 4px;
    background: #f4f5f0;
    border-radius: var(--radius-xs, 4px);
    padding: 8px 10px;
  }

  .quote-label {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
    display: block;
    margin-bottom: 3px;
  }

  .criterion-quote {
    color: var(--color-slate-bright);
    font-size: 11.5px;
    font-family: var(--font-mono, monospace);
    line-height: 1.45;
  }

  .criterion-explanation {
    color: var(--color-slate-muted);
    font-size: 10.5px;
    display: block;
    margin-top: 2px;
    font-style: italic;
  }

  /* ── Tab 2: Misconceptions & Cognitive Traps ─────────────────── */
  .traps-unscanned-box,
  .traps-clear-box {
    text-align: center;
    padding: 32px 18px;
    background: #fafaf8;
    border: 1px dashed var(--color-graphite-border);
    border-radius: var(--radius-md, 8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .traps-unscanned-icon {
    font-size: 32px;
  }

  .clear-check {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #ecfdf5;
    color: #059669;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
  }

  .traps-unscanned-box h4,
  .traps-clear-box h4 {
    margin: 0;
    font-size: 15px;
    color: var(--color-heading);
  }

  .trap-intro {
    font-size: 12px;
    color: var(--color-slate-light);
    line-height: 1.5;
    max-width: 400px;
    margin: 0;
  }

  .trap-clear-note {
    font-size: 12px;
    color: var(--color-slate-light);
    margin: 0;
  }

  .trap-note {
    font-size: 11px;
    color: var(--color-slate-muted);
    margin: 4px 0 0;
  }

  .trap-error {
    font-size: 12px;
    color: #b91c1c;
    margin-top: 10px;
  }

  .trap-scan-btn {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 700;
    color: #ffffff;
    background: #0b4a4f;
    border: none;
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    margin-top: 6px;
    transition: background 0.15s;
  }

  .trap-scan-btn:hover:not(:disabled) {
    background: #083337;
  }

  .trap-scan-btn:disabled,
  .trap-rescan-btn:disabled {
    opacity: 0.55;
    cursor: default;
  }

  .trap-rescan-btn {
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    margin-top: 8px;
    color: var(--color-slate-light);
  }

  .traps-findings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 12px;
  }

  .traps-found-count {
    font-size: 12px;
    font-weight: 700;
    color: #b45309;
  }

  .trap-rescan-btn-inline {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 10.5px;
    padding: 2px 7px;
    cursor: pointer;
    color: var(--color-slate-muted);
  }

  .traps-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .trap-card {
    border: 1px solid rgba(216, 154, 58, 0.4);
    border-left: 3px solid #d97706;
    border-radius: var(--radius-sm, 6px);
    padding: 12px 14px;
    background: #fffdfa;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .trap-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .trap-title {
    font-size: 13.5px;
    color: #92400e;
  }

  .trap-method {
    font-size: 9.5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 999px;
    background: rgba(216, 154, 58, 0.18);
    color: #8c6212;
    font-weight: 700;
  }

  .trap-method.weak {
    background: rgba(148, 163, 184, 0.2);
    color: #64748b;
  }

  .trap-rule {
    margin: 0;
    font-size: 12px;
    line-height: 1.45;
    color: var(--color-heading);
  }

  .trap-quote-wrap {
    background: rgba(216, 154, 58, 0.08);
    border-left: 2px solid #d97706;
    padding: 6px 10px;
    border-radius: 0 4px 4px 0;
    margin: 2px 0;
  }

  .trap-quote-label {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #b45309;
    display: block;
    margin-bottom: 2px;
  }

  .trap-quote {
    margin: 0;
    font-size: 12px;
    font-style: italic;
    color: #1e293b;
    line-height: 1.45;
  }

  .trap-why {
    margin: 0;
    font-size: 11.5px;
    color: var(--color-slate-light);
    line-height: 1.45;
  }

  .trap-refer {
    margin: 0;
    font-size: 11.5px;
    color: var(--color-slate-light);
  }

  .trap-refer-label {
    font-weight: 700;
    color: #0b4a4f;
    text-transform: uppercase;
    font-size: 9.5px;
  }

  .trap-actions {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-top: 4px;
    flex-wrap: wrap;
  }

  .trap-draft-btn {
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 4px;
    border: 1px solid #0b4a4f;
    background: #0b4a4f;
    color: #fff;
    cursor: pointer;
  }

  .trap-graph-link {
    font-size: 11px;
    color: #0b4a4f;
    text-decoration: none;
    border-bottom: 1px solid currentColor;
  }

  .trap-draft {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed rgba(148, 163, 184, 0.45);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .trap-draft-label {
    font-size: 9.5px;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--color-slate-muted);
  }

  .trap-draft-subject,
  .trap-draft-body {
    width: 100%;
    font: inherit;
    font-size: 12px;
    line-height: 1.45;
    padding: 7px 9px;
    border-radius: 4px;
    border: 1px solid var(--color-graphite-border);
    background: #fff;
    box-sizing: border-box;
  }

  .trap-draft-actions {
    display: flex;
    gap: 6px;
    margin-top: 6px;
  }

  .trap-send {
    font-size: 11px;
    font-weight: 600;
    padding: 5px 10px;
    background: #0b4a4f;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .trap-copy,
  .trap-cancel {
    font-size: 11px;
    padding: 5px 10px;
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    cursor: pointer;
    color: var(--color-slate-light);
  }

  /* ── Tab 3: Reasoning & Engagement Trace ─────────────────────── */
  .reasoning-subnav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .reasoning-pills {
    display: flex;
    gap: 4px;
  }

  .acc-tab-btn {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    color: var(--color-slate-muted);
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 8px;
    transition: all 0.15s ease;
    font-family: var(--font-ui);
  }

  .acc-tab-btn:hover {
    color: var(--color-heading);
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .acc-tab-btn.active {
    background: var(--pill-active-bg, rgba(217, 119, 6, 0.14));
    border-color: var(--pill-active-border, rgba(217, 119, 6, 0.35));
    color: var(--pill-active-color, #92400e);
  }

  .acc-flight-link {
    background: var(--color-signal-green-bg, #ecfdf5);
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: var(--radius-sm, 6px);
    color: var(--color-signal-green-text, #065f46);
    font-size: 11px;
    font-weight: 600;
    padding: 4px 8px;
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .acc-flight-link:hover {
    background: rgba(5, 150, 105, 0.12);
  }

  .timeline-container {
    padding-top: 4px;
  }

  /* ── Shared Utilities & Empty States ─────────────────────────── */
  .empty-dossier {
    color: var(--color-slate-muted);
    font-size: 12.5px;
    line-height: 1.6;
    padding: 60px 24px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin: auto;
  }

  .empty-icon {
    font-size: 40px;
  }

  .empty-dossier strong {
    color: var(--color-heading);
    font-size: 15px;
  }

  .empty-dossier p {
    max-width: 380px;
    margin: 0;
  }

  .load-error {
    align-items: center;
    background: #fef2f2;
    border: 1px solid rgba(220, 38, 38, 0.2);
    border-radius: var(--radius-lg, 12px);
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 250px;
    justify-content: center;
    text-align: center;
  }

  .load-error strong { color: #991b1b; }
  .load-error p { color: var(--color-slate-light); font-size: 12px; margin: 0; max-width: 540px; }

  .notice {
    border-radius: var(--radius-sm, 6px);
    font-size: 12px;
    padding: 10px 14px;
  }

  .notice.success {
    background: var(--color-signal-green-bg, #ecfdf5);
    border: 1px solid rgba(5, 150, 105, 0.2);
    color: var(--color-signal-green-text, #065f46);
  }

  .notice.error {
    background: #fef2f2;
    border: 1px solid rgba(220, 38, 38, 0.2);
    color: #991b1b;
  }

  .loading {
    align-items: center;
    color: var(--color-slate-light);
    display: flex;
    gap: 12px;
    justify-content: center;
    min-height: 280px;
  }

  .loading.small { min-height: 380px; }

  .spinner {
    animation: spin 0.8s linear infinite;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-radius: 50%;
    border-top-color: var(--color-horizon-bright, #d97706);
    height: 24px;
    width: 24px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Responsive Behavior ─────────────────────────────────────── */
  @media (max-width: 1100px) {
    .eval-dual-workspace {
      grid-template-columns: 1fr;
      grid-template-rows: auto auto;
      overflow-y: auto;
    }

    .eval-document-pane {
      border-right: none;
      border-bottom: 1px solid var(--color-graphite-border);
      height: 480px;
    }

    .eval-workbench-pane {
      height: 520px;
    }
  }

  @media (max-width: 820px) {
    .review-layout {
      grid-template-columns: 1fr;
    }

    .review-layout.roster-hidden {
      grid-template-columns: 1fr;
    }

    .roster-sidebar {
      height: auto;
      max-height: 220px;
      border-right: none;
      border-bottom: 1px solid var(--color-graphite-border);
    }

    .dossier-header-bar {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }

    .quick-flipper {
      align-self: flex-start;
    }
  }
</style>
