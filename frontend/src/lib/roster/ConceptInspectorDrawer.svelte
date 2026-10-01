<script lang="ts">
  import type { GraphNode, MasteryData, Probe, Student } from './rosterTypes';

  let {
    selectedConcept = null,
    masteryData = null,
    prerequisites = [],
    downstreamDependents = [],
    strugglingStudentsForConcept = [],
    linkedProbes = [],
    isDispatchingIntervention = false,
    dispatchSuccessNotice = '',
    onSelectConcept,
    onInspectStudent,
    onDispatchIntervention,
  } = $props<{
    selectedConcept?: GraphNode | null;
    masteryData?: MasteryData | null;
    prerequisites?: string[];
    downstreamDependents?: string[];
    strugglingStudentsForConcept?: Student[];
    linkedProbes?: Probe[];
    isDispatchingIntervention?: boolean;
    dispatchSuccessNotice?: string;
    onSelectConcept?: (conceptId: string) => void;
    onInspectStudent?: (studentId: string) => void;
    onDispatchIntervention?: (concept: GraphNode) => void;
  }>();
</script>

<aside class="concept-inspector-drawer">
  {#if selectedConcept}
    <div class="inspector-header">
      <div class="inspector-badge-row">
        <span class="type-pill">{selectedConcept.concept_type || selectedConcept.level || 'Concept'}</span>
        {#if selectedConcept.bloom_level}
          <span class="bloom-pill">{selectedConcept.bloom_level}</span>
        {/if}
        {#if masteryData?.bottlenecks?.includes((selectedConcept.concept_id || selectedConcept.id) ?? '')}
          <span class="bottleneck-pill">⚠️ High Bottleneck</span>
        {/if}
      </div>
      <h3 class="concept-title">{selectedConcept.label}</h3>
      {#if selectedConcept.definition}
        <p class="concept-def">{selectedConcept.definition}</p>
      {/if}
    </div>

    <!-- Cohort Diagnostic Stats -->
    <div class="inspector-section">
      <div class="section-title">Cohort Diagnostic Stats</div>
      <div class="stats-metric-grid">
        <div class="metric-card">
          <div
            class="metric-value"
            style="color: {(selectedConcept.cohort_mastery_rate ?? 1) >= 0.8 ? '#059669' : (selectedConcept.cohort_mastery_rate ?? 1) >= 0.6 ? '#d97706' : '#e11d48'};"
          >
            {Math.round((selectedConcept.cohort_mastery_rate ?? 1) * 100)}%
          </div>
          <div class="metric-label">Mastery Rate</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{selectedConcept.total_assessed || 0}</div>
          <div class="metric-label">Assessed</div>
        </div>
        <div class="metric-card">
          <div
            class="metric-value"
            style="color: {(selectedConcept.struggling_count || 0) > 0 ? '#e11d48' : '#059669'};"
          >
            {selectedConcept.struggling_count || 0}
          </div>
          <div class="metric-label">Trapped</div>
        </div>
      </div>
    </div>

    <!-- Topological Connections -->
    {#if prerequisites.length > 0 || downstreamDependents.length > 0}
      <div class="inspector-section">
        <div class="section-title">Prerequisite Chain</div>
        {#if prerequisites.length > 0}
          <div class="connection-group">
            <span class="connection-label">Prerequisites:</span>
            <div class="connection-chips">
              {#each prerequisites as req}
                <span class="chip-item">{req}</span>
              {/each}
            </div>
          </div>
        {/if}
        {#if downstreamDependents.length > 0}
          <div class="connection-group">
            <span class="connection-label">Unlocks Downstream:</span>
            <div class="connection-chips">
              {#each downstreamDependents as dep}
                <span class="chip-item dep">{dep}</span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Trapped Learners & Interventions -->
    <div class="inspector-section">
      <div class="section-header-flex">
        <span class="section-title">Trapped Learners ({strugglingStudentsForConcept.length})</span>
        {#if strugglingStudentsForConcept.length > 0}
          <button
            type="button"
            class="btn-batch-intervention"
            disabled={isDispatchingIntervention}
            onclick={() => onDispatchIntervention?.(selectedConcept!)}
          >
            {isDispatchingIntervention ? 'Dispatching...' : `🪄 Batch Intervene (${strugglingStudentsForConcept.length})`}
          </button>
        {/if}
      </div>

      {#if dispatchSuccessNotice}
        <div class="dispatch-notice-banner">
          {dispatchSuccessNotice}
        </div>
      {/if}

      {#if strugglingStudentsForConcept.length === 0}
        <div class="no-struggle-box">
          <span>✓</span> No learners currently trapped on this concept.
        </div>
      {:else}
        <div class="trapped-students-list">
          {#each strugglingStudentsForConcept as stu}
            <div class="trapped-student-item">
              <div class="student-item-left">
                <div class="mini-avatar">{stu.student_id.slice(0, 2).toUpperCase()}</div>
                <div>
                  <div class="student-item-name">{stu.name || stu.student_id}</div>
                  <div class="student-item-sub">Autonomy: {Math.round((stu.average_autonomy_score ?? 0.85) * 100)}%</div>
                </div>
              </div>
              <button
                type="button"
                class="btn-inspect-student"
                onclick={() => onInspectStudent?.(stu.student_id)}
              >
                Inspect Frontier ↗
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Active Cognitive Traps -->
    {#if (selectedConcept.active_misconceptions || []).length > 0}
      <div class="inspector-section">
        <div class="section-title">Active Cognitive Traps ({selectedConcept.active_misconceptions!.length})</div>
        <div class="traps-list">
          {#each selectedConcept.active_misconceptions! as trap}
            <div class="trap-card">
              <div class="trap-header">
                <span class="trap-label">⚠️ {trap.misconception_id || 'Active Friction Point'}</span>
              </div>
              {#if trap.quote}
                <p class="trap-quote">“{trap.quote}”</p>
              {/if}
              {#if trap.prompt}
                <p class="trap-prompt"><strong>Probe:</strong> {trap.prompt}</p>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Micro Socratic Probes -->
    {#if linkedProbes.length > 0}
      <div class="inspector-section">
        <div class="section-title">Micro Socratic Probes ({linkedProbes.length})</div>
        <p class="section-hint">Targeted questions ready to deploy during learner friction:</p>
        <div class="probes-cards-list">
          {#each linkedProbes as probe}
            <div class="probe-item-card">
              <div class="probe-meta-row">
                <span class="probe-tier-tag tier-{probe.probe_tier || 1}">
                  Tier {probe.probe_tier || 1}: {probe.probe_type || 'Clarification'}
                </span>
              </div>
              <div class="probe-prompt-text">“{probe.prompt || probe.question_text}”</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {:else}
    <!-- Empty Inspector: Cohort Overview & Bottlenecks -->
    <div class="inspector-empty-state">
      <div class="empty-icon">🕸️</div>
      <h4>Curriculum Concept Diagnostics</h4>
      <p>Click any concept node on the canvas to inspect prerequisite topology, cohort mastery rates, and trapped students.</p>

      {#if (masteryData?.bottlenecks || []).length > 0}
        <div class="bottlenecks-list-panel">
          <div class="panel-heading">⚠️ High-Priority Bottlenecks ({masteryData!.bottlenecks!.length})</div>
          <div class="bottleneck-chips-list">
            {#each masteryData!.bottlenecks! as bId}
              {@const bNode = masteryData?.graph?.nodes?.find((n) => (n.concept_id || n.id) === bId)}
              {#if bNode}
                <button
                  type="button"
                  class="bottleneck-chip-btn"
                  onclick={() => onSelectConcept?.(bId)}
                >
                  <span class="chip-name">{bNode.label}</span>
                  <span class="chip-trapped">⚠️ {bNode.struggling_count || 0} trapped</span>
                </button>
              {/if}
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</aside>

<style>
  .concept-inspector-drawer {
    background: var(--color-graphite-card, #ffffff);
    overflow-y: auto;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    height: 100%;
  }

  .inspector-header {
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
    padding-bottom: 12px;
  }

  .inspector-badge-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
    flex-wrap: wrap;
  }

  .type-pill {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(0, 0, 0, 0.06);
    color: var(--color-slate-bright, #111315);
  }

  .bloom-pill {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(37, 99, 235, 0.1);
    color: #2563eb;
  }

  .bottleneck-pill {
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(225, 29, 72, 0.12);
    color: #e11d48;
  }

  .concept-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0 0 6px 0;
    line-height: 1.35;
  }

  .concept-def {
    font-size: 12px;
    line-height: 1.45;
    color: var(--color-slate-light, #6d7378);
    margin: 0;
  }

  .inspector-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted, #6d7378);
  }

  .section-header-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .stats-metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .metric-card {
    background: var(--color-graphite, #23272b);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
  }

  .metric-value {
    font-size: 16px;
    font-weight: 700;
  }

  .metric-label {
    font-size: 9.5px;
    color: var(--color-slate-muted, #6d7378);
    text-transform: uppercase;
    margin-top: 2px;
  }

  .connection-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 11.5px;
  }

  .connection-label {
    font-weight: 600;
    color: var(--color-slate-muted, #6d7378);
  }

  .connection-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .chip-item {
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    color: var(--color-slate-bright, #111315);
  }

  .chip-item.dep {
    border-color: rgba(5, 150, 105, 0.3);
    color: #059669;
  }

  .btn-batch-intervention {
    background: #0b4a4f;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }

  .btn-batch-intervention:hover:not(:disabled) {
    background: #08373b;
  }

  .btn-batch-intervention:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .dispatch-notice-banner {
    padding: 6px 10px;
    background: rgba(5, 150, 105, 0.1);
    border: 1px solid rgba(5, 150, 105, 0.3);
    color: #059669;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }

  .no-struggle-box {
    font-size: 11.5px;
    color: #059669;
    background: rgba(5, 150, 105, 0.05);
    border: 1px solid rgba(5, 150, 105, 0.2);
    border-radius: 5px;
    padding: 8px 10px;
  }

  .trapped-students-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .trapped-student-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 7px 9px;
    background: rgba(225, 29, 72, 0.04);
    border: 1px solid rgba(225, 29, 72, 0.18);
    border-radius: 5px;
  }

  .student-item-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mini-avatar {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    background: rgba(225, 29, 72, 0.15);
    color: #e11d48;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
  }

  .student-item-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-heading, #111315);
  }

  .student-item-sub {
    font-size: 10px;
    color: var(--color-slate-muted, #6d7378);
  }

  .btn-inspect-student {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    color: var(--color-slate-light, #6d7378);
    cursor: pointer;
  }

  .btn-inspect-student:hover {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  .traps-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .trap-card {
    background: rgba(225, 29, 72, 0.04);
    border: 1px solid rgba(225, 29, 72, 0.2);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .trap-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .trap-label {
    font-size: 11.5px;
    font-weight: 700;
    color: #be123c;
  }

  .trap-quote {
    font-size: 11px;
    font-style: italic;
    color: var(--color-slate-dark, #334155);
    margin: 0;
    line-height: 1.35;
  }

  .trap-prompt {
    font-size: 11px;
    color: var(--color-slate-dark, #475569);
    margin: 0;
    line-height: 1.35;
  }

  .section-hint {
    font-size: 11px;
    color: var(--color-slate-light, #6d7378);
    margin: 0 0 6px 0;
    line-height: 1.35;
  }

  .probes-cards-list {
    display: flex;
    flex-direction: column;
    gap: 7px;
  }

  .probe-item-card {
    background: var(--color-bone, #f8fafc);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .probe-meta-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .probe-tier-tag {
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .probe-tier-tag.tier-1 {
    background: rgba(14, 116, 144, 0.1);
    color: #0e7490;
    border: 1px solid rgba(14, 116, 144, 0.25);
  }

  .probe-tier-tag.tier-2 {
    background: rgba(217, 119, 6, 0.1);
    color: #b45309;
    border: 1px solid rgba(217, 119, 6, 0.25);
  }

  .probe-tier-tag.tier-3 {
    background: rgba(109, 40, 217, 0.1);
    color: #6d28d9;
    border: 1px solid rgba(109, 40, 217, 0.25);
  }

  .probe-prompt-text {
    font-size: 11.5px;
    font-style: italic;
    color: var(--color-heading, #111315);
    line-height: 1.4;
  }

  .inspector-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 20px 8px;
    gap: 10px;
  }

  .empty-icon {
    font-size: 32px;
  }

  .inspector-empty-state h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
    color: var(--color-heading, #111315);
  }

  .inspector-empty-state p {
    font-size: 11.5px;
    line-height: 1.45;
    color: var(--color-slate-light, #6d7378);
    margin: 0;
  }

  .bottlenecks-list-panel {
    width: 100%;
    margin-top: 14px;
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .panel-heading {
    font-size: 11px;
    font-weight: 700;
    color: #e11d48;
    text-transform: uppercase;
  }

  .bottleneck-chips-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .bottleneck-chip-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 10px;
    background: rgba(225, 29, 72, 0.05);
    border: 1px solid rgba(225, 29, 72, 0.2);
    border-radius: 5px;
    font-family: var(--font-ui, inherit);
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
  }

  .bottleneck-chip-btn:hover {
    background: rgba(225, 29, 72, 0.12);
    border-color: #e11d48;
  }

  .chip-name {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-heading, #111315);
  }

  .chip-trapped {
    font-size: 10px;
    font-weight: 700;
    color: #e11d48;
  }
</style>
