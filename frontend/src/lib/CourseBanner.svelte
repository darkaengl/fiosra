<script>
  let {
    course = null,
    enrolledCount = 0,
    courseId = '',
    onAddModule,
  } = $props();

  let designerHref = $derived(
    courseId ? `#/designer?course_id=${encodeURIComponent(courseId)}` : '#/designer'
  );
</script>

<div class="course-banner">
  <div class="banner-left">
    <div class="banner-meta">
      <span class="meta-tag">{(course?.domain || 'ACADEMIC').toUpperCase()} CURRICULUM</span>
      <span class="meta-sep">•</span>
      <span style="color: var(--color-horizon-bright);">FALL 2026</span>
      <span class="meta-sep">•</span>
      <span>{enrolledCount} ENROLLED STUDENTS</span>
    </div>

    <h1 class="course-h1">{course?.title || 'Course Workspace'}</h1>

    <div class="banner-indicators">
      <div class="indicator-chip">
        <span class="chip-icon">📖</span>
        <span class="chip-label">Syllabus Grounding:</span>
        <span class="chip-val">{course?.syllabus_context || 'Curriculum initialized in PostgreSQL & Neo4j'}</span>
      </div>
      <div class="indicator-chip">
        <span class="chip-icon">🧬</span>
        <span class="chip-label">Prerequisite DAG:</span>
        <span class="chip-val">{course?.modules?.length || 0} Modules Configured</span>
      </div>
    </div>
  </div>

  <div class="banner-right">
    <button type="button" class="btn btn-secondary" onclick={onAddModule}>
      + Add Module
    </button>
    <a href={designerHref} class="btn btn-primary">
      + Co-Pilot New Assignment
    </a>
  </div>
</div>

<style>
  .course-banner {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    padding: 22px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    position: relative;
    overflow: hidden;
  }

  .course-banner::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--color-horizon-blue), var(--color-aurora));
  }

  .banner-left {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .banner-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-light);
  }

  .meta-tag {
    letter-spacing: 0.4px;
  }

  .meta-sep {
    color: var(--color-slate-muted);
  }

  .course-h1 {
    font-family: var(--font-brand);
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    line-height: 1.25;
  }

  .banner-indicators {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 2px;
  }

  .indicator-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--color-slate-light);
    background: rgba(0, 0, 0, 0.25);
    padding: 4px 10px;
    border-radius: var(--radius-xs);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .chip-icon {
    font-size: 13px;
  }

  .chip-label {
    font-weight: 500;
    color: var(--color-slate-muted);
  }

  .chip-val {
    color: var(--color-slate-bright);
    font-weight: 500;
  }

  .banner-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }
</style>
