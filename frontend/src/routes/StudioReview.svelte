<script>
  import { onMount } from "svelte";
  import PdfViewer from "../lib/PdfViewer.svelte";
  import ReviewRosterSidebar from "../lib/review/ReviewRosterSidebar.svelte";
  import ReviewRubricTab from "../lib/review/ReviewRubricTab.svelte";
  import ReviewTrapsTab from "../lib/review/ReviewTrapsTab.svelte";
  import ReviewTraceTab from "../lib/review/ReviewTraceTab.svelte";
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

  // ---- Misconception review & Interventions ----------------------------
  let scanBySession = $state({});
  let scanningSession = $state("");
  let scanError = $state("");
  let interventionsBySession = $state({});
  let dispatchingFindingId = $state("");
  let interventionNotice = $state("");

  let scan = $derived(
    selected ? scanBySession[selected.session_id] || null : null,
  );
  let isScanning = $derived(
    Boolean(selected) && scanningSession === selected.session_id,
  );
  let activeInterventions = $derived(
    selected ? interventionsBySession[selected.session_id] || [] : [],
  );

  async function loadInterventions(sessionId) {
    if (!sessionId) return;
    try {
      const res = await fetch(`/interventions/session/${sessionId}`);
      if (res.ok) {
        interventionsBySession = {
          ...interventionsBySession,
          [sessionId]: await res.json(),
        };
      }
    } catch (err) {
      console.warn("Failed to load interventions:", err);
    }
  }

  async function dispatchIntervention(finding, customPrompt = "") {
    if (!selected) return;
    const sessionId = selected.session_id;
    dispatchingFindingId = finding.misconception_id;
    interventionNotice = "";
    try {
      const res = await fetch("/interventions/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          student_id: selected.student_id,
          teacher_id: teacherId.trim() || "educator_workspace",
          document_id: finding.document_id || null,
          block_id: finding.block_id || null,
          concept_id: finding.concept_id || null,
          concept_label: finding.concept_label || null,
          misconception_id: finding.misconception_id,
          evidence_quote: finding.evidence_quote || "",
          activity_type: finding.activity_type || "socratic_nudge",
          activity_prompt: (customPrompt || "").trim() || finding.activity_prompt || "",
          activity_guidance: finding.activity_guidance || finding.remediation_hint || "",
        }),
      });
      if (!res.ok) {
        throw new Error(await responseError(res, "Failed to dispatch challenge."));
      }
      const dispatched = await res.json();
      const currentList = interventionsBySession[sessionId] || [];
      interventionsBySession = {
        ...interventionsBySession,
        [sessionId]: [dispatched, ...currentList.filter((i) => i.intervention_id !== dispatched.intervention_id)],
      };
      interventionNotice = `Challenge dispatched to ${selected.student_id}.`;
    } catch (err) {
      interventionNotice = err.message || "Failed to dispatch challenge.";
    } finally {
      dispatchingFindingId = "";
    }
  }

  async function acknowledgeIntervention(interventionId) {
    if (!selected) return;
    const sessionId = selected.session_id;
    try {
      const res = await fetch(`/interventions/${interventionId}/acknowledge`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        const currentList = interventionsBySession[sessionId] || [];
        interventionsBySession = {
          ...interventionsBySession,
          [sessionId]: currentList.map((i) => (i.intervention_id === updated.intervention_id ? updated : i)),
        };
      }
    } catch (err) {
      console.warn("Failed to acknowledge intervention:", err);
    }
  }

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
    loadInterventions(item.session_id);

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
      <ReviewRosterSidebar
        {queue}
        {filteredQueue}
        {selected}
        {rosterWidth}
        {isRosterCollapsed}
        {filterStatus}
        {searchQuery}
        {completedCount}
        {submittedCount}
        {activeCount}
        {assignmentId}
        onSelect={selectItem}
        onCollapse={() => (isRosterCollapsed = true)}
        onExpand={() => (isRosterCollapsed = false)}
        onFilterChange={(status) => (filterStatus = status)}
        onSearchChange={(query) => (searchQuery = query)}
        onRefresh={loadQueue}
      />

      <!-- Left Resize Handle -->
      {#if !isRosterCollapsed}
        <div
          class="resize-handle left-handle"
          onpointerdown={startResizeLeft}
          class:active={isResizingLeft}
          title="Drag to resize student roster"
        >
          <div class="resize-handle-bar"></div>
        </div>
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
              <ReviewRubricTab {dossier} />

            <!-- ── TAB 2: Cognitive Traps & Misconceptions ── -->
            {:else if activeEvalTab === "traps"}
              <ReviewTrapsTab
                {scan}
                {isScanning}
                {scanError}
                {courseId}
                {activeInterventions}
                {interventionNotice}
                onRunScan={runMisconceptionScan}
                onDismissNotice={() => (interventionNotice = "")}
                onAcknowledgeIntervention={acknowledgeIntervention}
                onDispatchIntervention={dispatchIntervention}
              />

            <!-- ── TAB 3: Reasoning Trace ── -->
            {:else if activeEvalTab === "reasoning"}
              <ReviewTraceTab
                sessionId={selected.session_id}
                {reasoningNodes}
                {activityNodes}
              />
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
