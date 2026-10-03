<script lang="ts">
  let {
    hoveredNode,
    mousePos = { x: 0, y: 0 },
    viewMode = 'standard',
    activeStudent = null,
  } = $props<{
    hoveredNode: any;
    mousePos?: { x: number; y: number };
    viewMode?: string;
    activeStudent?: any;
  }>();
</script>

{#if hoveredNode}
  <div
    class="node-tooltip"
    style="left: {mousePos.x + 14}px; top: {mousePos.y - 12}px;"
  >
    <div class="tooltip-header">
      <span
        class="tooltip-tag"
        style="background: {hoveredNode.color}22; color: {hoveredNode.color}; border: 1px solid {hoveredNode.color}44;"
      >
        {hoveredNode.raw?.concept_type || hoveredNode.raw?.level || 'Concept'}
      </span>
      <span class="tooltip-degree">
        {hoveredNode.degree} {hoveredNode.degree === 1 ? 'connection' : 'connections'}
      </span>
    </div>
    <strong class="tooltip-title">{hoveredNode.raw?.label}</strong>

    {#if viewMode === 'cohort' && hoveredNode.raw?.cohort_mastery_rate !== undefined}
      <div class="tooltip-metric-pill" style="border-left: 3px solid {hoveredNode.color};">
        <span class="metric-rate">{Math.round((hoveredNode.raw.cohort_mastery_rate ?? 1) * 100)}% Cohort Mastery</span>
        {#if (hoveredNode.raw.struggling_count || 0) > 0}
          <span class="struggle-tag">⚠️ {hoveredNode.raw.struggling_count} trapped</span>
        {/if}
      </div>
    {/if}

    {#if viewMode === 'student' && activeStudent}
      {@const cState = activeStudent.concept_states?.[hoveredNode.id] || 'locked'}
      <div class="tooltip-metric-pill" style="border-left: 3px solid {hoveredNode.color};">
        <span class="metric-rate">{activeStudent.name || activeStudent.student_id}:</span>
        <strong style="text-transform: capitalize; color: {hoveredNode.color}; font-size: 10px;">{cState}</strong>
      </div>
    {/if}

    {#if hoveredNode.raw?.definition}
      <p class="tooltip-def">{hoveredNode.raw.definition}</p>
    {/if}
    <span class="tooltip-hint">Click node to inspect details</span>
  </div>
{/if}

<style>
  .node-tooltip {
    position: fixed;
    pointer-events: none;
    border-radius: 6px;
    font-family: inherit;
    max-width: 270px;
    padding: 9px 12px;
    z-index: 50;
    transition: opacity 0.1s ease;
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.14);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
    color: #1e293b;
  }

  :global(.dark-mode) .node-tooltip {
    background: rgba(24, 24, 27, 0.94);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.65);
    color: #f8fafc;
  }

  .tooltip-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 5px;
  }

  .tooltip-tag {
    border-radius: 3px;
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.3px;
    padding: 2px 5px;
    text-transform: uppercase;
  }

  .tooltip-degree {
    font-size: 9px;
    color: #64748b;
  }

  :global(.dark-mode) .tooltip-degree {
    color: #94a3b8;
  }

  .tooltip-title {
    display: block;
    font-size: 12px;
    line-height: 1.35;
    margin-bottom: 4px;
    color: #0f172a;
  }

  :global(.dark-mode) .tooltip-title {
    color: #ffffff;
  }

  .tooltip-def {
    font-size: 10.5px;
    line-height: 1.4;
    color: #475569;
    margin: 0 0 5px 0;
  }

  :global(.dark-mode) .tooltip-def {
    color: #cbd5e1;
  }

  .tooltip-hint {
    color: #2563eb;
    font-size: 9px;
    font-style: italic;
  }

  :global(.dark-mode) .tooltip-hint {
    color: #60a5fa;
  }

  .tooltip-metric-pill {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 3px 6px;
    margin: 4px 0 6px 0;
    border-radius: 4px;
    font-size: 10px;
    background: rgba(0, 0, 0, 0.04);
  }

  :global(.dark-mode) .tooltip-metric-pill {
    background: rgba(255, 255, 255, 0.06);
  }

  .metric-rate {
    font-size: 9.5px;
    font-weight: 600;
  }

  .struggle-tag {
    font-size: 9.5px;
    color: #e11d48;
    font-weight: 700;
  }
</style>
