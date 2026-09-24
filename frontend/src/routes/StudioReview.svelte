<script>
  import { onMount } from "svelte";
  import ThinkingTimeline from "../lib/ThinkingTimeline.svelte";
  import PdfViewer from "../lib/PdfViewer.svelte";
  import { formatDate, responseError, routeParams } from "../lib/session.js";

  let {
    courseId: propCourseId = "",
    assignmentId: propAssignmentId = "",
    targetStudentId = "",
    targetSessionId = "",
    onBack = null,
  } = $props();

  let courseId = $state(propCourseId || "");
  let assignmentId = $state(propAssignmentId || "");
  let filterStatus = $state("all"); // 'all' | 'completed' | 'submitted' | 'active'
  let searchQuery = $state("");

  // UI state for the 3-panel workspace
  let isRosterCollapsed = $state(false);
  let activeEvalTab = $state("rubric"); // 'rubric' | 'traps' | 'reasoning'
  let activeReviewTimelineTab = $state("reasoning"); // 'reasoning' | 'activity'
  let expandedReasoningNode = $state(-1);
  let expandedActivityNode = $state(-1);

  // Draggable sidebar widths (matching StudentWorkspace margin sliders)
  let rosterWidth = $state(
    (typeof localStorage !== "undefined" &&
      Number(localStorage.getItem("fiosra_eval_roster_width"))) ||
      260,
  );
  let workbenchWidth = $state(
    (typeof localStorage !== "undefined" &&
      Number(localStorage.getItem("fiosra_eval_workbench_width"))) ||
      380,
  );
  let isResizingLeft = $state(false);
  let isResizingRight = $state(false);

  function startResizeLeft(e) {
    e.preventDefault();
    isResizingLeft = true;
    const startX = e.clientX;
    const startWidth = rosterWidth;

    function onPointerMove(moveEvent) {
      const deltaX = moveEvent.clientX - startX;
      const maxAllowed = Math.max(
        200,
        Math.min(460, window.innerWidth - workbenchWidth - 360),
      );
      rosterWidth = Math.round(
        Math.max(180, Math.min(maxAllowed, startWidth + deltaX)),
      );
    }

    function onPointerUp() {
      isResizingLeft = false;
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      try {
        localStorage.setItem("fiosra_eval_roster_width", String(rosterWidth));
      } catch {}
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  }

  function startResizeRight(e) {
    e.preventDefault();
    isResizingRight = true;
    const startX = e.clientX;
    const startWidth = workbenchWidth;

    function onPointerMove(moveEvent) {
      const deltaX = startX - moveEvent.clientX;
      const leftColWidth = isRosterCollapsed ? 42 : rosterWidth;
      const maxAllowed = Math.max(
        300,
        Math.min(560, window.innerWidth - leftColWidth - 360),
      );
      workbenchWidth = Math.round(
        Math.max(280, Math.min(maxAllowed, startWidth + deltaX)),
      );
    }

    function onPointerUp() {
      isResizingRight = false;
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      try {
        localStorage.setItem(
          "fiosra_eval_workbench_width",
          String(workbenchWidth),
        );
      } catch {}
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  }

  // ---- Misconception review ---------------------------------------------
  let scanBySession = $state({});
  let scanningSession = $state("");
  let scanError = $state("");
  let draftOpenFor = $state("");
  let draftBody = $state("");
  let draftSubject = $state("");

  let scan = $derived(
    selected ? scanBySession[selected.session_id] || null : null,
  );
  let isScanning = $derived(
    Boolean(selected) && scanningSession === selected.session_id,
  );

  async function runMisconceptionScan() {
    if (!selected || isScanning) return;
    const sessionId = selected.session_id;
    scanningSession = sessionId;
    scanError = "";
    try {
      const response = await fetch(`/interventions/scan/${sessionId}`);
      if (!response.ok)
        throw new Error(
          await responseError(
            response,
            "The submission could not be analysed.",
          ),
        );
      scanBySession = { ...scanBySession, [sessionId]: await response.json() };
    } catch (err) {
      scanError = err.message || "The submission could not be analysed.";
    } finally {
      scanningSession = "";
    }
  }

  function openDraft(finding) {
    draftOpenFor = finding.misconception_id;
    draftSubject = finding.suggested_message?.subject || "";
    draftBody = finding.suggested_message?.body || "";
  }

  function openInMailClient() {
    const url = `mailto:?subject=${encodeURIComponent(draftSubject)}&body=${encodeURIComponent(draftBody)}`;
    window.open(url, "_blank");
  }

  async function copyDraft() {
    try {
      await navigator.clipboard.writeText(
        `Subject: ${draftSubject}\n\n${draftBody}`,
      );
    } catch (err) {
      console.warn("Clipboard unavailable", err);
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
    if (
      targetSessionId &&
      selected?.session_id !== targetSessionId &&
      queue.length
    ) {
      const match = queue.find((item) => item.session_id === targetSessionId);
      if (match) selectItem(match);
    } else if (
      targetStudentId &&
      selected?.student_id !== targetStudentId &&
      queue.length
    ) {
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
  let grade = $state("");
  let feedback = $state("");
  let teacherId = $state("educator_workspace");
  let isLoading = $state(true);
  let isFinalizing = $state(false);
  let notice = $state("");
  let error = $state("");

  let filteredQueue = $derived.by(() => {
    let q = queue;
    if (filterStatus === "completed")
      q = q.filter((item) => item.status === "completed");
    else if (filterStatus === "submitted")
      q = q.filter((item) => item.status === "submitted");
    else if (filterStatus === "active")
      q = q.filter(
        (item) => item.status !== "submitted" && item.status !== "completed",
      );
    if (searchQuery.trim()) {
      const term = searchQuery.trim().toLowerCase();
      q = q.filter(
        (item) =>
          item.student_id.toLowerCase().includes(term) ||
          (item.assignment_title &&
            item.assignment_title.toLowerCase().includes(term)),
      );
    }
    return q;
  });

  let completedCount = $derived(
    queue.filter((item) => item.status === "completed").length,
  );
  let submittedCount = $derived(
    queue.filter((item) => item.status === "submitted").length,
  );
  let activeCount = $derived(
    queue.filter(
      (item) => item.status !== "submitted" && item.status !== "completed",
    ).length,
  );

  // Cohort Quick-Flipper index
  let currentStudentIndex = $derived.by(() => {
    if (!selected || !filteredQueue.length) return -1;
    return filteredQueue.findIndex(
      (item) => item.session_id === selected.session_id,
    );
  });

  function selectPrevStudent() {
    if (currentStudentIndex > 0) {
      selectItem(filteredQueue[currentStudentIndex - 1]);
    }
  }

  function selectNextStudent() {
    if (
      currentStudentIndex >= 0 &&
      currentStudentIndex < filteredQueue.length - 1
    ) {
      selectItem(filteredQueue[currentStudentIndex + 1]);
    }
  }

  let totalRubricCriteria = $derived.by(() => {
    if (!dossier?.per_question_evidence) return 0;
    return dossier.per_question_evidence.reduce(
      (sum, q) => sum + Object.keys(q.rubric_evidence || {}).length,
      0,
    );
  });

  async function loadQueue() {
    error = "";
    const params = new URLSearchParams();
    if (courseId) params.set("course_id", courseId);
    if (assignmentId) params.set("assignment_id", assignmentId);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    const response = await fetch(`/evidence/review-queue${suffix}`);
    if (!response.ok)
      throw new Error(
        await responseError(
          response,
          "The evaluation review queue could not be loaded.",
        ),
      );
    queue = await response.json();

    let targetToSelect = null;
    if (targetSessionId) {
      targetToSelect = queue.find(
        (item) => item.session_id === targetSessionId,
      );
    }
    if (!targetToSelect && targetStudentId) {
      targetToSelect = queue.find(
        (item) => item.student_id === targetStudentId,
      );
    }
    if (!targetToSelect && selected) {
      targetToSelect = queue.find(
        (item) => item.session_id === selected.session_id,
      );
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
    feedback = "";
    grade =
      item.suggested_grade && item.suggested_grade !== "Pending"
        ? item.suggested_grade
        : "";
    error = "";
    draftOpenFor = "";

    const [dossierResponse, traceResponse, reasoningRes, activityRes] =
      await Promise.all([
        fetch(`/evidence/dossier/${item.session_id}`),
        fetch(`/evidence/trace/${item.session_id}`),
        fetch(`/evidence/trace/${item.session_id}/reasoning`),
        fetch(`/evidence/trace/${item.session_id}/activity`),
      ]);
    if (!dossierResponse.ok) {
      error = await responseError(
        dossierResponse,
        "The evidence dossier could not be loaded.",
      );
      return;
    }
    dossier = await dossierResponse.json();
    if (traceResponse.ok)
      trace = (await traceResponse.json()).trace_nodes || [];
    if (reasoningRes.ok)
      reasoningNodes = (await reasoningRes.json()).nodes || [];
    if (activityRes.ok) activityNodes = (await activityRes.json()).nodes || [];
  }

  async function finalise() {
    if (!selected || !grade.trim()) return;
    isFinalizing = true;
    error = "";
    notice = "";
    try {
      const response = await fetch(
        `/evidence/dossier/${selected.session_id}/finalise-grade`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            approved_grade: grade.trim(),
            teacher_id: teacherId.trim() || "educator_workspace",
            teacher_override: grade.trim() !== selected.suggested_grade,
            feedback_comments: feedback.trim(),
          }),
        },
      );
      if (!response.ok)
        throw new Error(
          await responseError(
            response,
            "The final grade could not be recorded.",
          ),
        );
      notice = `Grade ${grade.trim()} finalized for ${selected.student_id}. Session sealed.`;
      selected = null;
      dossier = null;
      await loadQueue();
    } catch (err) {
      error = err.message || "The final grade could not be recorded.";
    } finally {
      isFinalizing = false;
    }
  }

  onMount(async () => {
    const params = routeParams();
    if (!courseId) courseId = params.get("course_id") || "";
    if (!assignmentId) assignmentId = params.get("assignment_id") || "";
    try {
      await loadQueue();
    } catch (err) {
      error = err.message || "The evaluation queue could not be initialized.";
    } finally {
      isLoading = false;
    }
  });
</script>

<div
  class="canvas-review-root"
  class:is-resizing={isResizingLeft || isResizingRight}
>
  {#if !assignmentId}
    <!-- Compact Standalone Mode Top Bar -->
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
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading submitted assignments…</span>
    </div>
  {:else if error && queue.length === 0}
    <section class="load-error" role="alert">
      <strong>The evaluation queue could not be loaded.</strong>
      <p>{error}</p>
      <button class="btn btn-secondary btn-sm" onclick={loadQueue}
        >Try again</button
      >
    </section>
  {:else}
    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- 3-PANEL CANVAS WORKSPACE (Draggable Left | Center PDF | Draggable Right) -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div class="canvas-eval-body">
      <!-- ── 1. LEFT SIDEBAR: Student Roster ─────────────────────── -->
      {#if !isRosterCollapsed}
        <aside class="canvas-roster-sidebar" style:width={`${rosterWidth}px`}>
          <div class="roster-top-bar">
            <span class="roster-top-title">Roster ({filteredQueue.length})</span
            >
            <button
              type="button"
              class="btn-collapse-sidebar"
              onclick={() => (isRosterCollapsed = true)}
              title="Collapse student roster to maximize PDF viewing width"
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
                class:active={filterStatus === "all"}
                onclick={() => (filterStatus = "all")}
                >All ({queue.length})</button
              >
              <button
                type="button"
                class="filter-pill"
                class:active={filterStatus === "completed"}
                onclick={() => (filterStatus = "completed")}
                >Final ({completedCount})</button
              >
              {#if submittedCount > 0}
                <button
                  type="button"
                  class="filter-pill"
                  class:active={filterStatus === "submitted"}
                  onclick={() => (filterStatus = "submitted")}
                  >Ready ({submittedCount})</button
                >
              {/if}
              {#if activeCount > 0}
                <button
                  type="button"
                  class="filter-pill"
                  class:active={filterStatus === "active"}
                  onclick={() => (filterStatus = "active")}
                  >Draft ({activeCount})</button
                >
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
                  <span class="roster-avatar-mini"
                    >{item.student_id.slice(0, 2).toUpperCase()}</span
                  >
                  <div class="roster-item-info">
                    <span class="roster-item-id">{item.student_id}</span>
                    {#if !assignmentId && item.assignment_title}
                      <span class="roster-item-assignment"
                        >{item.assignment_title}</span
                      >
                    {/if}
                    <span class="roster-item-date"
                      >{formatDate(item.submitted_at)}</span
                    >
                  </div>
                  {#if item.status === "submitted"}
                    <span class="mini-status-badge submitted">Ready</span>
                  {:else if item.status === "completed"}
                    <span class="mini-status-badge completed">Final</span>
                  {:else}
                    <span class="mini-status-badge in-progress">Draft</span>
                  {/if}
                </button>
              {/each}
            {/if}
          </div>

          <button
            type="button"
            class="roster-refresh-btn"
            onclick={loadQueue}
            title="Check for new submissions"
          >
            ↻ Refresh Roster
          </button>
        </aside>

        <!-- Left Resize Handle -->
        <div
          class="resize-handle left-handle"
          onpointerdown={startResizeLeft}
          class:active={isResizingLeft}
          title="Drag to resize student roster"
        >
          <div class="resize-handle-bar"></div>
        </div>
      {:else}
        <!-- Collapsed Roster Rail (42px) -->
        <aside
          class="canvas-roster-rail"
          onclick={() => (isRosterCollapsed = false)}
          title="Click to expand student roster"
        >
          <button
            type="button"
            class="btn-expand-rail"
            onclick={() => (isRosterCollapsed = false)}
            title="Expand student roster"
          >
            ⇥
          </button>
          <div class="rail-vertical-text">
            STUDENTS ({filteredQueue.length})
          </div>
        </aside>
      {/if}

      <!-- ── 2. CENTER STAGE: Dedicated PDF Viewer (HERO) ────────── -->
      <main class="canvas-pdf-hero">
        {#if !selected}
          <div class="hero-empty-state">
            <span class="empty-hero-icon">📋</span>
            <h3>No Student Selected</h3>
            <p>
              Select a student from the roster on the left to review their
              official submission PDF.
            </p>
          </div>
        {:else if !dossier}
          <div class="loading small">
            <div class="spinner"></div>
            <span>Opening evaluation dossier…</span>
          </div>
        {:else}
          <!-- Slim Control Toolbar -->
          <header class="pdf-hero-toolbar">
            <div class="hero-student-meta">
              <span class="hero-avatar"
                >{selected.student_id.slice(0, 2).toUpperCase()}</span
              >
              <div class="hero-student-text">
                <div class="hero-title-row">
                  <h3 class="hero-student-name">{selected.student_id}</h3>
                  <span
                    class="status-chip"
                    class:submitted={selected.status === "submitted"}
                    class:completed={selected.status === "completed"}
                    class:in-progress={selected.status !== "submitted" &&
                      selected.status !== "completed"}
                  >
                    {#if selected.status === "submitted"}
                      ✓ Ready for Grading
                    {:else if selected.status === "completed"}
                      ✓ Grade Finalized
                    {:else}
                      ● Live Session (Draft)
                    {/if}
                  </span>
                </div>
                <div class="hero-timestamp-row">
                  {selected.assignment_title
                    ? `${selected.assignment_title} • `
                    : ""}
                  {selected.status === "submitted"
                    ? "Submitted"
                    : selected.status === "completed"
                      ? "Finalized"
                      : "Active"}: {formatDate(selected.submitted_at)}
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
                {currentStudentIndex >= 0
                  ? `${currentStudentIndex + 1} of ${filteredQueue.length}`
                  : "—"}
              </span>
              <button
                type="button"
                class="btn-flipper"
                onclick={selectNextStudent}
                disabled={currentStudentIndex < 0 ||
                  currentStudentIndex >= filteredQueue.length - 1}
                title="Next Student"
              >
                Next ›
              </button>
            </div>

            <!-- PDF Utilities -->
            <div class="pdf-toolbar-actions">
              <a
                class="btn-pdf-ghost"
                href={`/evidence/dossier/${selected.session_id}/pdf`}
                target="_blank"
                rel="noopener noreferrer"
                title="Open PDF in new browser tab"
              >
                Open in Tab ↗
              </a>
              <a
                class="btn-pdf-download"
                href={`/evidence/dossier/${selected.session_id}/pdf`}
                download
                title="Download official PDF submission"
              >
                ⬇ Download PDF
              </a>
            </div>
          </header>

          <!-- Full-Height Continuous PDF Document Container -->
          <div class="pdf-fullheight-viewport">
            {#key selected.session_id}
              <PdfViewer
                url={`/evidence/dossier/${selected.session_id}/pdf`}
                title={`${selected.student_id} - ${selected.assignment_title || "Assignment Submission"}`}
              />
            {/key}
          </div>
        {/if}
      </main>

      <!-- Right Resize Handle -->
      {#if selected && dossier}
        <div
          class="resize-handle right-handle"
          onpointerdown={startResizeRight}
          class:active={isResizingRight}
          title="Drag to resize evaluator workbench"
        >
          <div class="resize-handle-bar"></div>
        </div>

        <!-- ── 3. RIGHT SIDEBAR: Evaluator Workbench Gutter ──────── -->
        <aside
          class="canvas-workbench-gutter"
          style:width={`${workbenchWidth}px`}
        >
          <!-- Pinned Sovereign Grade Finalization Bar -->
          <div class="gutter-finalization-bar">
            {#if selected.status === "submitted"}
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
                  {isFinalizing ? "Finalizing…" : "Finalize Grade & Seal ➔"}
                </button>
              </div>
            {:else if selected.status === "completed"}
              <div class="gutter-sealed-banner">
                <span class="sealed-check">✓</span>
                <div class="sealed-text">
                  <strong>Grade Finalized & Sealed</strong>
                  <small>Recorded in sovereign ledger.</small>
                </div>
                <a
                  class="btn-sealed-pdf"
                  href={`/evidence/dossier/${selected.session_id}/pdf`}
                  download
                >
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
                <a
                  class="btn-recorder-link"
                  href={`#/student/trace?session_id=${selected.session_id}`}
                >
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
              class:active={activeEvalTab === "rubric"}
              onclick={() => (activeEvalTab = "rubric")}
            >
              <span>📊 Rubric</span>
              <span class="gutter-tab-count">{totalRubricCriteria}</span>
            </button>

            <button
              type="button"
              class="gutter-tab-btn"
              class:active={activeEvalTab === "traps"}
              onclick={() => (activeEvalTab = "traps")}
            >
              <span>🪤 Traps</span>
              <span
                class="gutter-tab-count"
                class:alert={scan && (scan.findings || []).length > 0}
              >
                {scan ? (scan.findings || []).length : "Scan"}
              </span>
            </button>

            <button
              type="button"
              class="gutter-tab-btn"
              class:active={activeEvalTab === "reasoning"}
              onclick={() => (activeEvalTab = "reasoning")}
            >
              <span>💡 Trace</span>
              <span class="gutter-tab-count"
                >{reasoningNodes.length + activityNodes.length}</span
              >
            </button>
          </nav>

          <!-- Workbench Tab Body Viewport (Independently Scrolling) -->
          <div class="gutter-tab-viewport">
            <!-- ── TAB 1: Rubric Assessment ── -->
            {#if activeEvalTab === "rubric"}
              <div class="rubric-inspector">
                <!-- Bloom's Taxonomy Cognitive Hierarchy Strip -->
                <div class="bloom-framework-strip">
                  <span class="bloom-strip-label">Bloom's Taxonomy Framework</span>
                  <div class="bloom-strip-pills">
                    <span class="bloom-strip-pill l2">L2 Understand</span>
                    <span class="bloom-strip-pill l3">L3 Apply</span>
                    <span class="bloom-strip-pill l4">L4 Analyze</span>
                    <span class="bloom-strip-pill l5">L5 Evaluate</span>
                    <span class="bloom-strip-pill l6">L6 Create</span>
                  </div>
                </div>

                {#if !dossier.per_question_evidence || dossier.per_question_evidence.length === 0}
                  <div class="tab-empty-msg">
                    No rubric criteria configured for this assignment.
                  </div>
                {:else}
                  <div class="rubric-matrix-list">
                    {#each dossier.per_question_evidence as question}
                      {#each Object.entries(question.rubric_evidence || {}) as [, criterion]}
                        {@const bloom = getCriterionBloom(criterion)}
                        {@const isSubmitted = hasEvidence(criterion)}
                        <article
                          class="criterion-chip-card"
                          class:met={criterion.met}
                          class:unassessed={!isSubmitted}
                        >
                          <header class="criterion-chip-header">
                            <div class="criterion-header-left">
                              <span
                                class="criterion-tag"
                                class:met={criterion.met}
                                class:unassessed={!isSubmitted}
                              >
                                {#if !isSubmitted}
                                  ○ In Progress
                                {:else if criterion.met}
                                  ✓ Evidence Met
                                {:else}
                                  ● Partial Evidence
                                {/if}
                              </span>
                              <span
                                class="bloom-badge target"
                                style={`--b-color: ${bloom.target.color}; --b-bg: ${bloom.target.bg}; --b-border: ${bloom.target.border}`}
                                title={`Target Cognitive Demand: ${bloom.target.name} (Level ${bloom.target.level})`}
                              >
                                🎯 {bloom.target.badge}
                              </span>
                            </div>

                            <div class="criterion-header-right">
                              <span class="criterion-weight-pill">{bloom.weight} Weight</span>
                            </div>
                          </header>

                          <strong class="criterion-label">
                            {criterion.label ||
                              (criterion.met
                                ? "Standard Met"
                                : "Criterion Pending")}
                          </strong>

                          <p class="criterion-explanation-text">
                            {criterion.description}
                          </p>

                          {#if isSubmitted}
                            <div class="criterion-quote-block">
                              <div class="quote-header-row">
                                <span class="quote-header">Submission Quote</span>
                                {#if bloom.demonstrated}
                                  <span
                                    class="bloom-demonstrated-pill"
                                    class:met={bloom.demonstrated.level >= bloom.target.level}
                                    class:below={bloom.demonstrated.level < bloom.target.level}
                                  >
                                    {#if bloom.demonstrated.level >= bloom.target.level}
                                      ✓ Demonstrated: {bloom.demonstrated.badge}
                                    {:else}
                                      ⚠️ Demonstrated: {bloom.demonstrated.badge} (Target: {bloom.target.name})
                                    {/if}
                                  </span>
                                {/if}
                              </div>
                              <div class="quote-text">{criterion.evidence}</div>
                            </div>
                          {:else}
                            <div class="criterion-unassessed-box">
                              <div class="unassessed-row">
                                <span class="unassessed-dot">◌</span>
                                <span class="unassessed-text">No student evidence submitted yet</span>
                              </div>
                              <small class="unassessed-cognitive-demand">
                                Required cognitive depth: <strong>{bloom.target.badge}</strong> — {bloom.demandDesc}
                              </small>
                            </div>
                          {/if}

                          {#if criterion.explanation && isSubmitted}
                            <small class="criterion-note"
                              >{criterion.explanation}</small
                            >
                          {/if}
                        </article>
                      {/each}
                    {/each}
                  </div>
                {/if}
              </div>

              <!-- ── TAB 2: Cognitive Traps & Misconceptions ── -->
            {:else if activeEvalTab === "traps"}
              <div class="traps-inspector">
                {#if !scan}
                  <div class="trap-scan-prompt">
                    <span class="trap-scan-icon">🪤</span>
                    <h4>Misconception Trap Scan</h4>
                    <p class="trap-scan-desc">
                      Scans student thesis against cognitive traps authored in
                      the course knowledge graph.
                    </p>
                    <button
                      type="button"
                      class="btn-trigger-scan"
                      onclick={runMisconceptionScan}
                      disabled={isScanning}
                    >
                      {isScanning ? "Analyzing with LLM…" : "⚡ Run Trap Scan"}
                    </button>
                    {#if isScanning}
                      <p class="scan-running-note">
                        Evidencing mental models (takes ~20s)…
                      </p>
                    {/if}
                  </div>
                {:else if (scan.findings || []).length === 0}
                  <div class="trap-clean-prompt">
                    <span class="clean-check-icon">✓</span>
                    <h4>No Cognitive Traps Found</h4>
                    <p class="clean-desc">
                      The student avoided known mental traps for this inquiry.
                    </p>
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
                      {(scan.findings || []).length} Cognitive {(
                        scan.findings || []
                      ).length === 1
                        ? "Trap"
                        : "Traps"} Evidenced
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
                          <span
                            class="trap-item-badge"
                            class:weak={finding.detection !== "llm_verified"}
                          >
                            {finding.detection === "llm_verified"
                              ? "Evidenced"
                              : "Candidate"}
                          </span>
                        </header>

                        <p class="trap-flawed-rule">{finding.flawed_rule}</p>

                        {#if finding.evidence_quote}
                          <div class="trap-quote-box">
                            <span class="quote-eyebrow">Student Quote:</span>
                            <blockquote class="trap-quote-text">
                              "{finding.evidence_quote}"
                            </blockquote>
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
                            <label class="draft-field-label" for="draft-subject"
                              >Subject</label
                            >
                            <input
                              id="draft-subject"
                              class="draft-subject-input"
                              bind:value={draftSubject}
                            />
                            <label class="draft-field-label" for="draft-body"
                              >Socratic Guidance</label
                            >
                            <textarea
                              id="draft-body"
                              class="draft-body-input"
                              rows="6"
                              bind:value={draftBody}
                            ></textarea>
                            <div class="draft-action-btns">
                              <button
                                type="button"
                                class="btn-mail"
                                onclick={openInMailClient}>Open in Mail</button
                              >
                              <button
                                type="button"
                                class="btn-copy"
                                onclick={copyDraft}>Copy</button
                              >
                              <button
                                type="button"
                                class="btn-close"
                                onclick={() => (draftOpenFor = "")}
                                >Close</button
                              >
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
            {:else if activeEvalTab === "reasoning"}
              <div class="trace-inspector">
                <div class="trace-sub-toolbar">
                  <div class="trace-toggle-buttons">
                    <button
                      type="button"
                      class="btn-trace-sub"
                      class:active={activeReviewTimelineTab === "reasoning"}
                      onclick={() => (activeReviewTimelineTab = "reasoning")}
                    >
                      Milestones ({reasoningNodes.length})
                    </button>
                    <button
                      type="button"
                      class="btn-trace-sub"
                      class:active={activeReviewTimelineTab === "activity"}
                      onclick={() => (activeReviewTimelineTab = "activity")}
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
                  {#if activeReviewTimelineTab === "reasoning"}
                    {#if reasoningNodes.length === 0}
                      <p class="tab-empty-msg">
                        No reasoning milestones logged yet.
                      </p>
                    {:else}
                      <ThinkingTimeline
                        nodes={reasoningNodes}
                        expandedNodeIndex={expandedReasoningNode}
                        onToggleNode={(idx) => {
                          expandedReasoningNode =
                            expandedReasoningNode === idx ? -1 : idx;
                        }}
                      />
                    {/if}
                  {:else if activityNodes.length === 0}
                    <p class="tab-empty-msg">No activity events logged.</p>
                  {:else}
                    <ThinkingTimeline
                      nodes={activityNodes}
                      expandedNodeIndex={expandedActivityNode}
                      onToggleNode={(idx) => {
                        expandedActivityNode =
                          expandedActivityNode === idx ? -1 : idx;
                      }}
                    />
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
  {#if error && queue.length > 0}<div class="toast-notice error">
      {error}
    </div>{/if}
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

  .canvas-review-root.is-resizing {
    user-select: none;
    cursor: col-resize;
  }

  /* Compact Top Bar for Standalone Mode */
  .standalone-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 18px;
    background: #ffffff;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 40px;
    box-sizing: border-box;
  }

  .standalone-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .standalone-title .eyebrow {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .standalone-title h2 {
    font-size: 13.5px;
    font-family: var(--font-brand, serif);
    color: var(--color-heading);
    margin: 0;
  }

  .standalone-meta {
    font-size: 11px;
    color: var(--color-slate-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .standalone-meta strong {
    color: var(--color-horizon-bright, #d97706);
    font-size: 12.5px;
  }

  /* ================================================================
     3-PANEL FLEX LAYOUT (Left Roster | Center PDF | Right Workbench)
     ================================================================ */
  .canvas-eval-body {
    display: flex;
    flex: 1;
    min-height: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: var(--color-bone, #f6f5f1);
  }

  /* ── Resize Handles (Matching StudentWorkspace) ──────────────── */
  .resize-handle {
    width: 6px;
    cursor: col-resize;
    position: relative;
    background: transparent;
    transition: background 0.15s ease;
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .resize-handle:hover,
  .resize-handle.active {
    background: rgba(79, 107, 255, 0.25);
  }

  .resize-handle-bar {
    width: 2px;
    height: 32px;
    background: var(--color-graphite-border);
    border-radius: 999px;
    transition: all 0.15s ease;
  }

  .resize-handle:hover .resize-handle-bar,
  .resize-handle.active .resize-handle-bar {
    background: var(--color-horizon-blue, #4f6bff);
    height: 48px;
  }

  /* ── 1. LEFT SIDEBAR: Student Roster ─────────────────────────── */
  .canvas-roster-sidebar {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
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
    width: 42px;
    flex-shrink: 0;
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

  /* ── 2. CENTER STAGE: Dedicated PDF Viewer (HERO) ────────────── */
  .canvas-pdf-hero {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
    height: 100%;
    min-height: 0;
    background: var(--color-bone, #f6f5f1);
    overflow: hidden;
  }

  /* Compact Hero Toolbar */
  .pdf-hero-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 6px 18px;
    background: #ffffff;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 44px;
    box-sizing: border-box;
  }

  .hero-student-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .hero-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #3b82f6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
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
    font-size: 13.5px;
    font-weight: 700;
    font-family: var(--font-brand, serif);
    color: var(--color-heading);
    margin: 0;
    line-height: 1.2;
    white-space: nowrap;
  }

  .hero-timestamp-row {
    font-size: 9.5px;
    color: var(--color-slate-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
    padding: 2px 6px;
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

  /* PDF Actions */
  .pdf-toolbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .btn-pdf-ghost {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    font-size: 10.5px;
    font-weight: 600;
    color: #2563eb;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    text-decoration: none;
    transition: all 0.12s;
  }

  .btn-pdf-ghost:hover {
    background: #dbeafe;
  }

  .btn-pdf-download {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 9px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 600;
    color: #1d4ed8;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    text-decoration: none;
    transition: all 0.12s;
  }

  .btn-pdf-download:hover {
    background: #dbeafe;
  }

  /* Full-Height Continuous PDF Document Viewport (Matches Student Workspace) */
  .pdf-fullheight-viewport {
    flex: 1;
    min-height: 0;
    width: 100%;
    height: 100%;
    position: relative;
    background: var(--color-obsidian, #f8f8f5);
    overflow: hidden;
    display: flex;
    flex-direction: column;
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

  .empty-hero-icon {
    font-size: 40px;
    margin-bottom: 8px;
  }
  .hero-empty-state h3 {
    font-size: 15px;
    color: var(--color-heading);
    margin: 0 0 6px;
  }
  .hero-empty-state p {
    max-width: 360px;
    font-size: 12px;
    margin: 0;
    line-height: 1.5;
  }

  /* ── 3. RIGHT SIDEBAR: Evaluator Workbench Gutter ────────────── */
  .canvas-workbench-gutter {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    border-left: 1px solid var(--color-graphite-border);
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

  /* Rubric Matrix with Bloom's Taxonomy Cognitive Hierarchy */
  .rubric-matrix-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .bloom-framework-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 10px;
    margin-bottom: 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
  }

  .bloom-strip-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #475569;
    white-space: nowrap;
  }

  .bloom-strip-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .bloom-strip-pill {
    font-size: 8.5px;
    font-weight: 700;
    padding: 2px 5px;
    border-radius: 3px;
    letter-spacing: 0.02em;
  }

  .bloom-strip-pill.l2 { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }
  .bloom-strip-pill.l3 { background: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }
  .bloom-strip-pill.l4 { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
  .bloom-strip-pill.l5 { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
  .bloom-strip-pill.l6 { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }

  .criterion-chip-card {
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-left: 3.5px solid #d97706;
    border-radius: 6px;
    padding: 11px 13px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: all 0.15s ease;
  }

  .criterion-chip-card.met {
    border-left-color: #059669;
    background: #ffffff;
  }

  .criterion-chip-card.unassessed {
    border-left-color: #cbd5e1;
    background: #fafaf9;
  }

  .criterion-chip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .criterion-header-left {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .criterion-header-right {
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .criterion-tag {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #92400e;
    background: #fef3c7;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .criterion-tag.met {
    color: #047857;
    background: #d1fae5;
  }

  .criterion-tag.unassessed {
    color: #475569;
    background: #f1f5f9;
  }

  .bloom-badge.target {
    font-size: 9.5px;
    font-weight: 700;
    color: var(--b-color, #7c3aed);
    background: var(--b-bg, #f5f3ff);
    border: 1px solid var(--b-border, #ddd6fe);
    padding: 1.5px 6px;
    border-radius: 4px;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  .criterion-weight-pill {
    font-size: 9.5px;
    color: var(--color-slate-muted);
    font-weight: 600;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    padding: 2px 6px;
    border-radius: 3px;
    white-space: nowrap;
  }

  .criterion-label {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-heading);
    line-height: 1.35;
  }

  .criterion-explanation-text {
    font-size: 11px;
    color: var(--color-slate-light);
    margin: 0;
    line-height: 1.45;
  }

  .criterion-quote-block {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 8px 10px;
    border-radius: 5px;
    margin-top: 2px;
  }

  .quote-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 5px;
    gap: 6px;
    flex-wrap: wrap;
  }

  .quote-header {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-muted);
    letter-spacing: 0.03em;
  }

  .bloom-demonstrated-pill {
    font-size: 9px;
    font-weight: 700;
    padding: 1.5px 6px;
    border-radius: 3px;
    letter-spacing: 0.02em;
  }

  .bloom-demonstrated-pill.met {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }

  .bloom-demonstrated-pill.below {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
  }

  .quote-text {
    font-size: 11px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-bright);
    line-height: 1.45;
    word-break: break-word;
  }

  .criterion-unassessed-box {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 5px;
    padding: 8px 10px;
    margin-top: 2px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .unassessed-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10.5px;
    color: #64748b;
  }

  .unassessed-dot {
    font-size: 11px;
    color: #94a3b8;
  }

  .unassessed-text {
    font-style: italic;
  }

  .unassessed-cognitive-demand {
    font-size: 10px;
    color: #475569;
    line-height: 1.35;
  }

  .criterion-note {
    font-size: 10px;
    color: var(--color-slate-muted);
    font-style: italic;
    display: block;
    margin-top: 2px;
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

  .trap-scan-icon {
    font-size: 28px;
  }
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

  .btn-trigger-scan:disabled {
    opacity: 0.55;
    cursor: default;
  }

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

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

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

  .load-error strong {
    color: #991b1b;
  }
  .load-error p {
    color: var(--color-slate-light);
    font-size: 12px;
    margin: 0;
  }

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
</style>
