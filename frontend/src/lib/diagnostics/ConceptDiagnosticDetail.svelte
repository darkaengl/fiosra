<script lang="ts">
  import type { GraphNode, MasteryData, Probe, Student } from '../roster/rosterTypes';

  let {
    selectedConcept,
    masteryData = null,
    prerequisites = [],
    downstreamDependents = [],
    strugglingStudentsForConcept = [],
    linkedProbes = [],
    isDispatchingIntervention = false,
    dispatchSuccessNotice = '',
    onClose,
    onInspectStudent,
    onDispatchIntervention,
  } = $props<{
    selectedConcept: GraphNode;
    masteryData?: MasteryData | null;
    prerequisites?: string[];
    downstreamDependents?: string[];
    strugglingStudentsForConcept?: Student[];
    linkedProbes?: Probe[];
    isDispatchingIntervention?: boolean;
    dispatchSuccessNotice?: string;
    onClose?: () => void;
    onInspectStudent?: (studentId: string) => void;
    onDispatchIntervention?: (concept: GraphNode) => void;
  }>();

  let isMisconception = $derived(
    selectedConcept.concept_type === 'misconception' || selectedConcept.level === 'misconception'
  );
</script>

<header class="drawer-header">
  <div class="drawer-header-left">
    {#if isMisconception}
      <span class="drawer-category-tag trap">⚠️ Cognitive Trap</span>
    {:else if selectedConcept.concept_type === 'socratic_probe'}
      <span class="drawer-category-tag probe">✦ Socratic Probe</span>
    {:else if selectedConcept.level === 'strand' || selectedConcept.rank === 0}
      <span class="drawer-category-tag module">📚 Strand</span>
    {:else if selectedConcept.level === 'topic' || selectedConcept.rank === 1}
      <span class="drawer-category-tag topic">📖 Core Topic</span>
    {:else}
      <span class="drawer-category-tag kc">🎯 Knowledge Component</span>
    {/if}
    {#if selectedConcept.bloom_level}
      <span class="bloom-badge">{selectedConcept.bloom_level}</span>
    {/if}
    {#if masteryData?.bottlenecks?.includes((selectedConcept.concept_id || selectedConcept.id) ?? '')}
      <span class="bottleneck-badge">⚠️ Bottleneck</span>
    {/if}
  </div>

  <button
    type="button"
    class="drawer-close-btn"
    onclick={() => onClose?.()}
    aria-label="Close inspector"
    title="Deselect Node (Esc)"
  >
    ✕
  </button>
</header>

<div class="drawer-content">
  <h2 class="drawer-title">{selectedConcept.label}</h2>
  {#if selectedConcept.definition}
    <p class="drawer-definition">{selectedConcept.definition}</p>
  {/if}

  <!-- Diagnostic Metrics -->
  <div class="inspector-section">
    <div class="section-title">Cohort Mastery Status</div>
    <div class="stat-grid">
      <div class="metric-tile">
        <span class="metric-label">Mastery Rate</span>
        <strong
          class="metric-val"
          style="color: {(selectedConcept.cohort_mastery_rate ?? 1) >= 0.8 ? '#059669' : (selectedConcept.cohort_mastery_rate ?? 1) >= 0.6 ? '#d97706' : '#e11d48'};"
        >
          {Math.round((selectedConcept.cohort_mastery_rate ?? 1) * 100)}%
        </strong>
      </div>
      <div class="metric-tile">
        <span class="metric-label">Assessed</span>
        <strong class="metric-val">{selectedConcept.total_assessed || 0}</strong>
      </div>
      <div class="metric-tile">
        <span class="metric-label">Trapped</span>
        <strong
          class="metric-val"
          style="color: {(selectedConcept.struggling_count || 0) > 0 ? '#e11d48' : '#059669'};"
        >
          {selectedConcept.struggling_count || 0}
        </strong>
      </div>
    </div>
  </div>

  <!-- Prerequisite Chain -->
  {#if prerequisites.length > 0 || downstreamDependents.length > 0}
    <div class="inspector-section">
      <div class="section-title">Topological Dependencies</div>
      <div class="topo-connections-box">
        {#if prerequisites.length > 0}
          <div class="topo-row">
            <span class="topo-label">Prerequisites:</span>
            <div class="chips-container">
              {#each prerequisites as req}
                <span class="chip-item">{req}</span>
              {/each}
            </div>
          </div>
        {/if}
        {#if downstreamDependents.length > 0}
          <div class="topo-row">
            <span class="topo-label">Unlocks:</span>
            <div class="chips-container">
              {#each downstreamDependents as dep}
                <span class="chip-item dep">{dep}</span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Active Cognitive Traps -->
  {#if (selectedConcept.active_misconceptions || []).length > 0}
    <div class="inspector-section">
      <div class="section-title text-rose">Active Cognitive Traps ({selectedConcept.active_misconceptions!.length})</div>
      <div class="traps-list">
        {#each selectedConcept.active_misconceptions! as trap}
          <div class="trap-card">
            <span class="trap-name">⚠️ {trap.misconception_id || 'Active Friction'}</span>
            {#if trap.quote}
              <p class="trap-quote">“{trap.quote}”</p>
            {/if}
            {#if trap.prompt}
              <p class="trap-prompt">{trap.prompt}</p>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Trapped Students & Micro-Scaffold Dispatch -->
  {#if strugglingStudentsForConcept.length > 0}
    <div class="inspector-section">
      <div class="section-title text-rose">Trapped Learners ({strugglingStudentsForConcept.length})</div>

      <div class="dispatch-action-box">
        <button
          type="button"
          class="btn-dispatch"
          disabled={isDispatchingIntervention}
          onclick={() => onDispatchIntervention?.(selectedConcept)}
        >
          {#if isDispatchingIntervention}
            <span>⏳ Dispatching...</span>
          {:else}
            <span>🚀 Dispatch Socratic Nudge ({strugglingStudentsForConcept.length})</span>
          {/if}
        </button>
        {#if dispatchSuccessNotice}
          <div class="dispatch-success-pill">{dispatchSuccessNotice}</div>
        {/if}
      </div>

      <div class="students-list">
        {#each strugglingStudentsForConcept as stu}
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

  <!-- Micro Socratic Probes -->
  {#if linkedProbes.length > 0}
    <div class="inspector-section">
      <div class="section-title">Micro Socratic Probes ({linkedProbes.length})</div>
      <div class="probes-list">
        {#each linkedProbes as probe}
          <div class="probe-card">
            <span class="probe-tier">Tier {probe.probe_tier || 1}: {probe.probe_type || 'Clarification'}</span>
            <p class="probe-question">“{probe.prompt || probe.question_text}”</p>
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
    flex-wrap: wrap;
  }

  .drawer-category-tag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    padding: 3px 7px;
    border-radius: 4px;
  }
  .drawer-category-tag.kc { background: rgba(92, 92, 92, 0.14); color: #475569; }
  .drawer-category-tag.topic { background: rgba(37, 99, 235, 0.12); color: #2563eb; }
  .drawer-category-tag.module { background: rgba(13, 148, 136, 0.14); color: #0d9488; }
  .drawer-category-tag.trap { background: rgba(224, 82, 82, 0.14); color: #dc2626; }
  .drawer-category-tag.probe { background: rgba(229, 155, 44, 0.14); color: #d97706; }

  .bloom-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(37, 99, 235, 0.1);
    color: #2563eb;
  }

  .bottleneck-badge {
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(225, 29, 72, 0.12);
    color: #e11d48;
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

  .topo-connections-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: rgba(0, 0, 0, 0.03);
    border-radius: 6px;
    padding: 8px 10px;
  }

  .topo-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .topo-label {
    font-size: 10px;
    font-weight: 600;
    color: #64748b;
  }

  .chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .chip-item {
    font-size: 10.5px;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0, 0, 0, 0.08);
  }

  .chip-item.dep {
    border-color: rgba(5, 150, 105, 0.3);
    color: #059669;
  }

  .traps-list, .probes-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .trap-card {
    background: rgba(225, 29, 72, 0.04);
    border: 1px solid rgba(225, 29, 72, 0.2);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .trap-name {
    font-size: 11px;
    font-weight: 700;
    color: #e11d48;
  }

  .trap-quote {
    font-size: 10.5px;
    font-style: italic;
    margin: 0;
    color: #475569;
  }

  .trap-prompt {
    font-size: 10.5px;
    margin: 0;
    color: #334155;
  }

  .probe-card {
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .probe-tier {
    font-size: 9.5px;
    font-weight: 700;
    color: #d97706;
    text-transform: uppercase;
  }

  .probe-question {
    font-size: 11px;
    font-style: italic;
    margin: 0;
  }

  .dispatch-action-box {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .btn-dispatch {
    background: #0284c7;
    color: #ffffff;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }

  .btn-dispatch:hover:not(:disabled) {
    background: #0369a1;
  }

  .btn-dispatch:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .dispatch-success-pill {
    padding: 4px 8px;
    background: rgba(5, 150, 105, 0.1);
    border: 1px solid rgba(5, 150, 105, 0.25);
    color: #059669;
    border-radius: 4px;
    font-size: 10.5px;
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
