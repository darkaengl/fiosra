<script lang="ts">
  import type { MasteryData } from '../roster/rosterTypes';

  let {
    masteryData = null,
    onClose,
    onSelectConcept,
    onInspectStudent,
  } = $props<{
    masteryData?: MasteryData | null;
    onClose?: () => void;
    onSelectConcept?: (conceptId: string) => void;
    onInspectStudent?: (studentId: string) => void;
  }>();

  let avgAutonomy = $derived.by(() => {
    const students = masteryData?.students || [];
    if (students.length === 0) return 0;
    const sum = students.reduce((acc, s) => acc + (s.average_autonomy_score || 0), 0);
    return Math.round((sum / students.length) * 100);
  });

  let strugglingStudents = $derived(
    (masteryData?.students || []).filter((s) => s.active_struggle)
  );
</script>

<header class="drawer-header">
  <div class="drawer-header-left">
    <span class="drawer-category-tag kc">📊 Cohort Overview</span>
  </div>
  <button
    type="button"
    class="drawer-close-btn"
    onclick={() => onClose?.()}
    aria-label="Collapse Cohort Overview"
    title="Collapse Overview (Esc)"
  >
    ✕
  </button>
</header>

<div class="drawer-content">
  <h2 class="drawer-title">Concept Diagnostics</h2>
  <p class="drawer-definition">
    Select any concept or trap node on the canvas to inspect real-time mastery, prerequisite dependencies, and trapped learners.
  </p>

  <!-- Overall Cohort KPIs -->
  <div class="inspector-section">
    <div class="section-title">Cohort Telemetry</div>
    <div class="stat-grid">
      <div class="metric-tile">
        <span class="metric-label">Learners</span>
        <strong class="metric-val">{masteryData?.students?.length || 0}</strong>
      </div>
      <div class="metric-tile">
        <span class="metric-label">Avg Autonomy</span>
        <strong class="metric-val" style="color: #0284c7;">{avgAutonomy}%</strong>
      </div>
      <div class="metric-tile">
        <span class="metric-label">High Bottlenecks</span>
        <strong class="metric-val" style="color: #e11d48;">
          {masteryData?.bottlenecks?.length || 0}
        </strong>
      </div>
    </div>
  </div>

  <!-- High-Priority Bottlenecks List -->
  {#if (masteryData?.bottlenecks || []).length > 0}
    <div class="inspector-section">
      <div class="section-title text-rose">⚠️ High-Priority Bottlenecks ({masteryData!.bottlenecks!.length})</div>
      <div class="bottlenecks-list">
        {#each masteryData!.bottlenecks! as bId}
          {@const bNode = masteryData?.graph?.nodes?.find((n) => (n.concept_id || n.id) === bId)}
          {#if bNode}
            <button
              type="button"
              class="bottleneck-card-btn"
              onclick={() => onSelectConcept?.(bId)}
            >
              <div class="bn-title">{bNode.label}</div>
              <div class="bn-meta">
                <span class="bn-trapped">⚠️ {bNode.struggling_count || 0} trapped</span>
                <span class="bn-arrow">Inspect ➔</span>
              </div>
            </button>
          {/if}
        {/each}
      </div>
    </div>
  {/if}

  <!-- Struggling Learners -->
  {#if strugglingStudents.length > 0}
    <div class="inspector-section">
      <div class="section-title text-rose">Learners Needing Scaffolding ({strugglingStudents.length})</div>
      <div class="students-list">
        {#each strugglingStudents as stu}
          <div class="student-item-row">
            <div class="student-info-left">
              <span class="student-avatar">{stu.name?.slice(0, 2).toUpperCase() || stu.student_id.slice(0, 2).toUpperCase()}</span>
              <div>
                <div class="student-name">{stu.name || stu.student_id}</div>
                <div class="student-sub">Autonomy: {Math.round((stu.average_autonomy_score ?? 0.85) * 100)}%</div>
              </div>
            </div>
            <button
              type="button"
              class="btn-inspect-learner"
              onclick={() => onInspectStudent?.(stu.student_id)}
            >
              View Frontier ➔
            </button>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  }

  .drawer-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .drawer-category-tag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    padding: 3px 7px;
    border-radius: 4px;
  }

  .drawer-category-tag.kc {
    background: rgba(92, 92, 92, 0.14);
    color: #475569;
  }

  .drawer-close-btn {
    background: transparent;
    border: none;
    font-size: 14px;
    cursor: pointer;
    color: #64748b;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.15s;
  }

  .drawer-close-btn:hover {
    background: rgba(0, 0, 0, 0.06);
    color: #0f172a;
  }

  .drawer-content {
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    flex: 1;
  }

  .drawer-title {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    line-height: 1.3;
  }

  .drawer-definition {
    margin: 0;
    font-size: 11.5px;
    line-height: 1.45;
    color: #64748b;
  }

  .inspector-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
  }

  .section-title.text-rose {
    color: #e11d48;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .metric-tile {
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 8px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .metric-label {
    font-size: 9.5px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
  }

  .metric-val {
    font-size: 16px;
    font-weight: 700;
  }

  .bottlenecks-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .bottleneck-card-btn {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(225, 29, 72, 0.05);
    border: 1px solid rgba(225, 29, 72, 0.2);
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
    font-family: inherit;
  }

  .bottleneck-card-btn:hover {
    background: rgba(225, 29, 72, 0.1);
    border-color: #e11d48;
  }

  .bn-title {
    font-size: 11.5px;
    font-weight: 600;
    color: inherit;
  }

  .bn-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 10px;
  }

  .bn-trapped {
    color: #e11d48;
    font-weight: 600;
  }

  .bn-arrow {
    color: #64748b;
    font-weight: 600;
  }

  .students-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .student-item-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.06);
    gap: 8px;
  }

  .student-info-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .student-avatar {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    background: rgba(225, 29, 72, 0.12);
    color: #e11d48;
    font-size: 9.5px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .student-name {
    font-size: 11.5px;
    font-weight: 600;
  }

  .student-sub {
    font-size: 10px;
    color: #64748b;
  }

  .btn-inspect-learner {
    font-size: 10px;
    font-weight: 600;
    background: transparent;
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 4px;
    padding: 3px 6px;
    cursor: pointer;
    color: #0284c7;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .btn-inspect-learner:hover {
    background: #0284c7;
    color: #ffffff;
    border-color: #0284c7;
  }
</style>
