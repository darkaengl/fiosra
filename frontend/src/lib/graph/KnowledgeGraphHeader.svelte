<script lang="ts">
  let {
    course = null,
    courses = [],
    selectedCourseId = $bindable(''),
    selectedModuleId = $bindable(''),
    isHydrating = false,
    selectedUnitTitle = '',
    visibleGraph = { nodes: [], edges: [], module_links: [], source_links: [], probes: [], stats: {} },
    fullGraph = { nodes: [] },
    unitFilterActive = false,
    onCourseChange = () => {},
    onStartHydration = () => {}
  } = $props<{
    course?: any;
    courses?: any[];
    selectedCourseId?: string;
    selectedModuleId?: string;
    isHydrating?: boolean;
    selectedUnitTitle?: string;
    visibleGraph?: any;
    fullGraph?: any;
    unitFilterActive?: boolean;
    onCourseChange?: (id: string) => void;
    onStartHydration?: () => void;
  }>();

  let conceptCount = $derived(
    visibleGraph.stats?.concepts ??
    visibleGraph.nodes?.filter((n: any) => n.concept_type !== 'misconception' && n.concept_type !== 'socratic_probe' && n.concept_type !== 'module').length
  );
  let trapCount = $derived(
    visibleGraph.stats?.misconceptions ??
    visibleGraph.nodes?.filter((n: any) => n.concept_type === 'misconception').length
  );
  let probeCount = $derived(
    visibleGraph.stats?.socratic_probes ??
    (visibleGraph.probes?.length || 0)
  );
</script>

<header class="floating-header">
  <div class="header-brand">
    <span class="header-badge">Pedagogical Graph</span>
    <h1 class="header-title">{course?.title || 'Curriculum Concept Graph'}</h1>
  </div>

  <div class="header-controls">
    <label class="course-picker">
      <span class="picker-label">Course:</span>
      <select bind:value={selectedCourseId} onchange={() => onCourseChange(selectedCourseId)}>
        {#each courses as item}
          <option value={item.course_id}>{item.title}</option>
        {/each}
      </select>
    </label>

    {#if course?.modules?.length}
      <label class="module-picker" title="Filters the graph to one unit, and targets Hydrate Graph at it">
        <span class="picker-label">Unit:</span>
        <select bind:value={selectedModuleId} disabled={isHydrating}>
          <option value="">All Units (Course)</option>
          {#each (course.modules || []).slice().sort((a: any, b: any) => a.position - b.position) as mod}
            <option value={mod.module_id}>Unit {mod.position}: {mod.title}</option>
          {/each}
        </select>
      </label>
    {/if}

    <button
      type="button"
      class="btn-hydrate"
      onclick={onStartHydration}
      disabled={isHydrating || !selectedCourseId}
      title={selectedModuleId
        ? `Regenerate concepts for ${selectedUnitTitle || 'the selected unit'} only`
        : 'Regenerate concepts across every unit in this course'}
    >
      <span class="bolt-icon {isHydrating ? 'spinning' : ''}">⚡</span>
      {isHydrating ? 'Hydrating…' : selectedModuleId ? 'Hydrate Unit' : 'Hydrate Graph'}
    </button>

    {#if course}
      <div class="header-stats">
        <span class="stat-tag">{conceptCount} concepts</span>
        <span class="stat-tag trap">{trapCount} traps</span>
        <span class="stat-tag probe">{probeCount} probes</span>
        {#if visibleGraph.stats?.source_links}
          <span class="stat-tag evidence">{visibleGraph.stats.source_links} sources</span>
        {/if}
        {#if unitFilterActive}
          <span class="stat-tag filtered">of {fullGraph.nodes?.length || 0} in course</span>
        {/if}
      </div>
    {/if}

    {#if selectedCourseId}
      <a class="btn-studio-link" href={`/#/modules?course_id=${selectedCourseId}`} title="Open Course Studio">
        Studio ↗
      </a>
      <a class="btn-studio-link" href={`/#/cohort-diagnostics?course_id=${selectedCourseId}`} title="Open Students & Cohort Diagnostics">
        Cohort Diagnostics 👥 ↗
      </a>
    {/if}
  </div>
</header>

<style>
  .floating-header {
    position: absolute;
    top: 14px;
    left: 14px;
    z-index: 25;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 7px 14px;
    border-radius: 8px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    pointer-events: auto;
    transition: all 0.2s ease;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }

  :global(.dark-mode) .floating-header {
    background: rgba(24, 24, 27, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    color: #f8fafc;
  }

  .header-brand {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .header-badge {
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #64748b;
  }
  :global(.dark-mode) .header-badge {
    color: #94a3b8;
  }

  .header-title {
    font-size: 14px;
    font-weight: 600;
    margin: 0;
    line-height: 1.2;
    white-space: nowrap;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .course-picker {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
  }

  .picker-label {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
  }

  .course-picker select {
    border-radius: 4px;
    font-size: 11.5px;
    padding: 4px 8px;
    outline: none;
    max-width: 220px;
    cursor: pointer;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0f172a;
  }
  :global(.dark-mode) .course-picker select {
    background: #27272a;
    border: 1px solid #3f3f46;
    color: #f1f5f9;
  }

  .module-picker {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--color-graphite-card, #ffffff);
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 6px;
    padding: 3px 8px;
  }
  .module-picker .picker-label {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
  }
  .module-picker select {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 12px;
    font-weight: 500;
    outline: none;
    cursor: pointer;
    max-width: 170px;
  }

  .btn-hydrate {
    display: flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 13px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    transition: all 0.2s ease;
  }
  .btn-hydrate:hover:not(:disabled) {
    background: linear-gradient(135deg, #1d4ed8, #6d28d9);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
  }
  .btn-hydrate:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .bolt-icon.spinning {
    display: inline-block;
    animation: spin 1s infinite linear;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .header-stats {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .stat-tag {
    font-size: 9.5px;
    font-weight: 600;
    padding: 3px 7px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.05);
    color: #475569;
    white-space: nowrap;
  }
  :global(.dark-mode) .stat-tag {
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
  }
  .stat-tag.trap {
    background: rgba(224, 82, 82, 0.12);
    color: #dc2626;
  }
  :global(.dark-mode) .stat-tag.trap {
    background: rgba(239, 83, 80, 0.18);
    color: #fca5a5;
  }
  .stat-tag.probe {
    background: rgba(229, 155, 44, 0.12);
    color: #d97706;
  }
  :global(.dark-mode) .stat-tag.probe {
    background: rgba(245, 158, 11, 0.18);
    color: #fde047;
  }
  .stat-tag.evidence {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border-color: rgba(16, 185, 129, 0.3);
  }
  .stat-tag.filtered {
    background: rgba(36, 36, 36, 0.10);
    color: #475569;
    font-style: italic;
  }
  :global(.dark-mode) .stat-tag.filtered {
    background: rgba(244, 244, 245, 0.14);
    color: #cbd5e1;
  }

  .btn-studio-link {
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 4px;
    text-decoration: none;
    transition: all 0.15s ease;
    white-space: nowrap;
    background: #0f172a;
    color: #ffffff;
  }
  .btn-studio-link:hover {
    background: #1e293b;
  }
  :global(.dark-mode) .btn-studio-link {
    background: #2563eb;
    color: #ffffff;
  }
  :global(.dark-mode) .btn-studio-link:hover {
    background: #1d4ed8;
  }

  @media (max-width: 768px) {
    .floating-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
      max-width: calc(100vw - 28px);
    }
    .header-controls {
      flex-wrap: wrap;
    }
  }
</style>
