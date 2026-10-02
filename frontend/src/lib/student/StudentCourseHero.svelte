<script lang="ts">
  let {
    courseId = '',
    currentCourse = null,
    activeAssignment = null,
    modulesCount = 0,
    totalAssignments = 0,
    getCleanSummary = (prompt?: string) => '',
  } = $props<{
    courseId?: string;
    currentCourse?: any;
    activeAssignment?: any;
    modulesCount?: number;
    totalAssignments?: number;
    getCleanSummary?: (prompt?: string) => string;
  }>();
</script>

<!-- Breadcrumb & Top Bar -->
<div class="top-nav-bar">
  <a href="#/student/portal" class="back-link">
    ← Back to All Enrolled Courses
  </a>
  <div class="term-badge">Fall 2026 Academic Term</div>
</div>

<!-- Course Hero Header -->
<header class="course-hero-header">
  <div class="hero-left">
    <div class="domain-tag-row">
      <span class="domain-pill">{currentCourse?.domain || 'BUSINESS & MANAGEMENT'}</span>
      <span class="status-live-pill">● Active Curriculum</span>
    </div>
    <h1 class="course-main-title">{currentCourse?.title || 'Principles of Marketing'}</h1>
    <p class="course-meta-line">
      Faculty: <strong>{currentCourse?.created_by || 'Prof. Somerville'}</strong>
      <span class="dot-sep">•</span>
      Curriculum: <strong>{modulesCount} Modules</strong>
      <span class="dot-sep">•</span>
      Deliverables: <strong>{totalAssignments} Case Inquiries</strong>
    </p>
  </div>

  <div class="hero-right-card">
    <div class="progress-ring-label">Curriculum Progression</div>
    <div class="progress-number">20% Completed</div>
    <div class="hero-progress-bar">
      <div class="hero-progress-fill" style="width: 20%;"></div>
    </div>
    <span class="progress-subtext">1 of {totalAssignments} assignments submitted</span>
  </div>
</header>

<!-- Active Milestone Highlight -->
{#if activeAssignment}
  <section class="active-focus-card">
    <div class="focus-badge-row">
      <span class="pulse-badge">CURRENT MILESTONE</span>
      <span class="module-loc-badge">Module 1 • Marketing Foundations</span>
    </div>

    <div class="focus-body-grid">
      <div class="focus-main-content">
        <h2 class="active-title">{activeAssignment.title}</h2>
        <p class="active-summary">
          {getCleanSummary(activeAssignment.prompt || activeAssignment.published?.task?.prompt)}
        </p>

        <div class="active-meta-chips">
          <span class="chip">📝 ~400 Words Brief</span>
          <span class="chip">⚖️ {activeAssignment.published?.public_rubric?.length || activeAssignment.rubric_count || 5} Rubric Criteria</span>
          <span class="chip">🛡️ Autonomy Rating: 82%</span>
          <span class="chip status-chip">Active In Progress</span>
        </div>
      </div>

      <div class="focus-action-col">
        <a
          href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(activeAssignment.assignment_id)}`}
          class="btn btn-primary btn-cta-resume"
        >
          ✍️ Resume Reasoning Canvas →
        </a>
        <a
          href={`#/student/sources?course_id=${encodeURIComponent(courseId)}`}
          class="btn btn-secondary btn-cta-sources"
        >
          📖 Assigned Primary Sources
        </a>
      </div>
    </div>
  </section>
{/if}

<style>
  .top-nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border, #DDDCD5);
  }

  .back-link {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-horizon-blue, #4F6BFF);
    text-decoration: none;
    transition: opacity 0.15s ease;
  }

  .back-link:hover {
    opacity: 0.85;
    text-decoration: underline;
  }

  .term-badge {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate, #6D7378);
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    padding: 3px 10px;
    border-radius: 999px;
  }

  .course-hero-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    flex-wrap: wrap;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 10px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  .hero-left {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
    min-width: 300px;
  }

  .domain-tag-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .domain-pill {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .status-live-pill {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--color-signal-green-text, #2D6340);
    background: var(--color-signal-green-bg, #EBF7F0);
    border: 1px solid rgba(95, 175, 122, 0.3);
    padding: 1px 7px;
    border-radius: 999px;
  }

  .course-main-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    font-family: var(--font-brand, inherit);
    margin: 0;
    line-height: 1.25;
    letter-spacing: -0.3px;
  }

  .course-meta-line {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
    margin: 0;
  }

  .dot-sep {
    margin: 0 5px;
    color: var(--color-cloud, #E9E8E3);
  }

  .hero-right-card {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 14px 18px;
    min-width: 200px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .progress-ring-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-subtle, #8A9096);
    letter-spacing: 0.5px;
  }

  .progress-number {
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading, #111315);
  }

  .hero-progress-bar {
    height: 6px;
    background: var(--color-cloud, #E9E8E3);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 2px;
  }

  .hero-progress-fill {
    height: 100%;
    background: var(--color-horizon-blue, #4F6BFF);
    border-radius: 999px;
  }

  .progress-subtext {
    font-size: 11px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .active-focus-card {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-left: 4px solid var(--color-horizon-blue, #4F6BFF);
    border-radius: 10px;
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  .focus-badge-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .pulse-badge {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #ffffff;
    background: var(--color-horizon-blue, #4F6BFF);
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .module-loc-badge {
    font-size: 12px;
    color: var(--color-slate, #6D7378);
    font-weight: 500;
  }

  .focus-body-grid {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
  }

  .focus-main-content {
    flex: 1;
    min-width: 320px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .active-title {
    font-size: 19px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
    line-height: 1.3;
  }

  .active-summary {
    font-size: 13.5px;
    color: var(--color-slate, #6D7378);
    line-height: 1.55;
    margin: 0;
  }

  .active-meta-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 4px;
  }

  .chip {
    font-size: 11.5px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    color: var(--color-slate, #6D7378);
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
  }

  .status-chip {
    background: #EBF0FF;
    border-color: #C9D7FF;
    color: var(--color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .focus-action-col {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 220px;
  }

  .btn {
    font-size: 13px;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: 6px;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-primary {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
    border: none;
  }
  .btn-primary:hover {
    background: #3B57E8;
  }

  .btn-secondary {
    background: #ffffff;
    border: 1px solid var(--border, #DDDCD5);
    color: var(--color-heading, #111315);
  }
  .btn-secondary:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
    border-color: #C5C4BE;
  }

  .btn-cta-resume {
    padding: 11px 20px;
    font-size: 13.5px;
    box-shadow: 0 1px 3px rgba(79, 107, 255, 0.2);
  }

  .btn-cta-sources {
    font-size: 12.5px;
  }
</style>
