<script>
  import { formatDate } from "../../lib/session.js";

  let {
    selected,
    filteredQueue = [],
    currentStudentIndex = -1,
    onPrevStudent,
    onNextStudent,
  } = $props();
</script>

<header class="pdf-hero-toolbar">
  <div class="hero-student-meta">
    <span class="hero-avatar">
      {selected.student_id.slice(0, 2).toUpperCase()}
    </span>
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
        {selected.assignment_title ? `${selected.assignment_title} • ` : ""}
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
      onclick={onPrevStudent}
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
      onclick={onNextStudent}
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

<style>
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
</style>
