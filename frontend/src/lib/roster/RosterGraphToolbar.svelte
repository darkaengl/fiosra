<script lang="ts">
  import type { CourseDetails, GraphPerspective, MasteryData } from './rosterTypes';

  let {
    graphPerspective = $bindable('cohort'),
    selectedStudentId = $bindable(''),
    selectedModuleId = $bindable('all'),
    maxNodesLimit = $bindable('all'),
    showBottlenecksOnly = $bindable(false),
    masteryData = null,
    courseDetails = null,
    nodeCount = 0,
  } = $props<{
    graphPerspective?: GraphPerspective;
    selectedStudentId?: string;
    selectedModuleId?: string;
    maxNodesLimit?: number | string;
    showBottlenecksOnly?: boolean;
    masteryData?: MasteryData | null;
    courseDetails?: CourseDetails | null;
    nodeCount?: number;
  }>();
</script>

<div class="graph-toolbar">
  <div class="toolbar-left">
    <div class="perspective-toggle-group">
      <button
        type="button"
        class="perspective-btn"
        class:active={graphPerspective === 'cohort'}
        onclick={() => {
          graphPerspective = 'cohort';
          selectedStudentId = '';
        }}
      >
        👥 Whole Cohort Heatmap
      </button>
      <div class="student-select-box">
        <span class="select-prefix">👤</span>
        <select
          class="student-dropdown"
          bind:value={selectedStudentId}
          onchange={(e) => {
            const target = e.target as HTMLSelectElement;
            if (target.value) {
              graphPerspective = 'student';
            } else {
              graphPerspective = 'cohort';
            }
          }}
        >
          <option value="">Select Individual Learner...</option>
          {#each (masteryData?.students || []) as s}
            <option value={s.student_id}>
              {s.name || s.student_id} {s.active_struggle ? '⚠️ (Trapped)' : `(${Math.round((s.average_autonomy_score ?? 0.85) * 100)}% Autonomy)`}
            </option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Unit / Module Scope Filter -->
    {#if (courseDetails?.modules || []).length > 0}
      <div class="unit-select-box">
        <span class="select-prefix">📚</span>
        <select class="student-dropdown" bind:value={selectedModuleId}>
          <option value="all">All Units ({nodeCount} nodes)</option>
          {#each courseDetails!.modules! as mod}
            <option value={mod.module_id}>
              Unit {mod.position}: {mod.title}
            </option>
          {/each}
        </select>
      </div>
    {/if}

    <!-- Max Nodes Cap Selector -->
    <div class="max-nodes-box">
      <span class="max-nodes-label">Max nodes:</span>
      <select class="max-nodes-select" bind:value={maxNodesLimit}>
        <option value={20}>20 nodes</option>
        <option value={30}>30 nodes</option>
        <option value={50}>50 nodes</option>
        <option value="all">All nodes</option>
      </select>
    </div>

    <label class="bottleneck-toggle-label">
      <input type="checkbox" bind:checked={showBottlenecksOnly} />
      <span>⚠️ Bottlenecks Only ({masteryData?.bottlenecks?.length || 0})</span>
    </label>
  </div>

  <div class="graph-legend">
    {#if graphPerspective === 'cohort'}
      <span class="legend-item"><span class="legend-dot dot-emerald"></span> ≥80% Mastered</span>
      <span class="legend-item"><span class="legend-dot dot-amber"></span> 60–79% Partial</span>
      <span class="legend-item"><span class="legend-dot dot-rose"></span> &lt;60% Trapped</span>
    {:else}
      <span class="legend-item"><span class="legend-dot dot-emerald"></span> Mastered</span>
      <span class="legend-item"><span class="legend-dot dot-blue"></span> Learning Frontier</span>
      <span class="legend-item"><span class="legend-dot dot-rose"></span> Trapped</span>
      <span class="legend-item"><span class="legend-dot dot-muted"></span> Locked</span>
    {/if}
  </div>
</div>

<style>
  .graph-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    background: var(--color-graphite, #23272b);
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
    gap: 12px;
    flex-wrap: wrap;
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .perspective-toggle-group {
    display: flex;
    align-items: center;
    background: var(--color-bone, #f6f5f1);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 6px;
    padding: 2px;
  }

  .perspective-btn {
    background: transparent;
    border: none;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-light, #6d7378);
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .perspective-btn.active {
    background: #0b4a4f;
    color: #ffffff;
  }

  .student-select-box,
  .unit-select-box,
  .max-nodes-box {
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--color-bone, #ffffff);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 5px;
    padding: 2px 8px;
  }

  .select-prefix {
    font-size: 12px;
  }

  .student-dropdown {
    border: none;
    background: transparent;
    font-size: 11.5px;
    color: var(--color-heading, #111315);
    outline: none;
    cursor: pointer;
    font-family: inherit;
  }

  .max-nodes-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light, #6d7378);
    white-space: nowrap;
  }

  .max-nodes-select {
    border: none;
    background: transparent;
    font-size: 11.5px;
    color: var(--color-heading, #111315);
    outline: none;
    cursor: pointer;
    font-family: inherit;
  }

  .bottleneck-toggle-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    font-weight: 600;
    color: #e11d48;
    cursor: pointer;
  }

  .graph-legend {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 11px;
    color: var(--color-slate-light, #6d7378);
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .dot-emerald { background: #059669; }
  .dot-amber { background: #d97706; }
  .dot-rose { background: #e11d48; }
  .dot-blue { background: #3b82f6; }
  .dot-muted { background: #94a3b8; }
</style>
