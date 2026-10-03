<script lang="ts">
  import { push } from 'svelte-spa-router';

  let { course } = $props<{ course: any }>();

  let identity = $derived.by(() => {
    const title = course.title || course.name || 'Untitled course';
    const match = title.match(/^([A-Za-z]{2,10}-\d{1,4}[A-Za-z]?)\s*:\s*(.+)$/);
    return match ? { code: match[1], title: match[2] } : { code: null, title };
  });
</script>

<div class="course-card">
  <div class="course-card-top">
    <div>
      <span class="course-code-badge">{identity.code || (course.domain || 'ACADEMIC').toUpperCase()} • WORKSPACE</span>
      <h3 class="course-name">{identity.title}</h3>
    </div>
    <span class="grounding-pill"><span>●</span> Course workspace</span>
  </div>

  <p class="course-desc">
    {course.syllabus_context || course.description || 'Curriculum workspace initialized. Ready for syllabus ingestion and prerequisite module sequencing.'}
  </p>

  <div class="course-metrics">
    <div class="metric-item">
      <span class="metric-val">{course.modules?.length ?? course.modules ?? 0}</span>
      <span class="metric-sub">Modules</span>
    </div>
    <div class="metric-item">
      <span class="metric-val">{course.assignments_count ?? course.assignments ?? 0}</span>
      <span class="metric-sub">Assignments</span>
    </div>
    <div class="metric-item">
      <span class="metric-val" style="color: var(--color-signal-green);">0%</span>
      <span class="metric-sub">Leakage</span>
    </div>
  </div>

  <div class="card-footer">
    <span class="last-active">
      Instructor: <strong>{course.created_by || 'Dr. Vance'}</strong>
    </span>
    <button
      type="button"
      class="course-link"
      onclick={() => push('/modules' + (course.course_id ? '?course_id=' + course.course_id : ''))}
    >
      Enter Curriculum &amp; Modules →
    </button>
  </div>
</div>

<style>
  .course-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }
  .course-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--color-horizon-blue), var(--color-aurora));
    opacity: 0.8;
  }
  .course-card:hover {
    border-color: var(--color-horizon-blue);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .course-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .course-code-badge {
    font-size: 10.5px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: var(--radius-xs);
    background: var(--pill-bg);
    color: var(--color-slate-bright);
    letter-spacing: 0.5px;
  }

  .course-name {
    font-family: var(--font-brand);
    font-size: 17px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 6px 0 0;
    line-height: 1.35;
  }

  .course-desc {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.55;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 58px;
  }

  .grounding-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: var(--radius-full);
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--color-signal-green);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .course-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    padding: 10px 12px;
    background: var(--color-graphite-card);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    text-align: center;
    gap: 8px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .metric-val {
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .metric-sub {
    font-size: 10px;
    color: var(--color-slate-muted);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 14px;
    margin-top: auto;
  }

  .last-active {
    font-size: 11.5px;
    color: var(--color-slate-muted);
  }
  .last-active strong {
    color: var(--color-slate-bright);
  }

  .course-link {
    background: none;
    border: none;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-horizon-bright);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: gap 0.15s, color 0.15s;
    padding: 0;
  }
  .course-link:hover {
    gap: 9px;
    color: var(--color-heading);
  }
</style>
