<script lang="ts">
  import type { CourseDetails, GraphPerspective, MasteryData } from '../roster/rosterTypes';

  let {
    courses = [],
    selectedCourseId = $bindable(''),
    course = null,
    selectedModuleId = $bindable('all'),
    scopedNodesCount = 0,
    graphPerspective = $bindable<'cohort' | 'student'>('cohort'),
    selectedStudentId = $bindable(''),
    masteryData = null,
    showBottlenecksOnly = $bindable(false),
    maxNodesLimit = $bindable<number | string>('all'),
    theme = $bindable<'light' | 'dark'>('light'),
    selectedConceptId = $bindable(''),
    cohortOverviewCollapsed = $bindable(false),
    hasSelectedConcept = false,
    onCourseChange = () => {},
  } = $props<{
    courses?: Array<{ course_id: string; title: string }>;
    selectedCourseId?: string;
    course?: CourseDetails | null;
    selectedModuleId?: string;
    scopedNodesCount?: number;
    graphPerspective?: 'cohort' | 'student';
    selectedStudentId?: string;
    masteryData?: MasteryData | null;
    showBottlenecksOnly?: boolean;
    maxNodesLimit?: number | string;
    theme?: 'light' | 'dark';
    selectedConceptId?: string;
    cohortOverviewCollapsed?: boolean;
    hasSelectedConcept?: boolean;
    onCourseChange?: (id: string) => void;
  }>();

  let showSettingsMenu = $state(false);

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && showSettingsMenu) {
      showSettingsMenu = false;
    }
  }

  function handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (showSettingsMenu && !target.closest('.settings-menu-container')) {
      showSettingsMenu = false;
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} onclick={handleClickOutside} />

<header class="floating-header">
  <!-- Left Zone: Course & Scope -->
  <div class="header-left-zone">
    <div class="brand-group">
      <span class="header-badge">Diagnostics</span>
      <select
        class="course-select-pill"
        bind:value={selectedCourseId}
        onchange={() => onCourseChange(selectedCourseId)}
        title="Switch Course"
      >
        {#each courses as item}
          <option value={item.course_id}>{item.title}</option>
        {/each}
      </select>
    </div>

    {#if (course?.modules || []).length > 0}
      <select class="unit-select-pill" bind:value={selectedModuleId} title="Filter by Unit / Module">
        <option value="all">All Units ({scopedNodesCount} nodes)</option>
        {#each (course!.modules || []).slice().sort((a: any, b: any) => a.position - b.position) as mod}
          <option value={mod.module_id}>Unit {mod.position}: {mod.title}</option>
        {/each}
      </select>
    {/if}
  </div>

  <!-- Center Zone: Mode & Bottlenecks Filter -->
  <div class="header-center-zone">
    <div class="segmented-mode-bar">
      <button
        type="button"
        class="mode-segment-btn"
        class:active={graphPerspective === 'cohort'}
        onclick={() => { graphPerspective = 'cohort'; selectedStudentId = ''; }}
      >
        👥 Cohort
      </button>
      <button
        type="button"
        class="mode-segment-btn"
        class:active={graphPerspective === 'student'}
        onclick={() => {
          graphPerspective = 'student';
          if (!selectedStudentId && (masteryData?.students || []).length > 0) {
            selectedStudentId = masteryData!.students![0].student_id;
          }
        }}
      >
        👤 Learner
      </button>
    </div>

    {#if graphPerspective === 'student'}
      <select
        class="student-picker-inline"
        bind:value={selectedStudentId}
        title="Select learner to inspect"
      >
        {#each (masteryData?.students || []) as s}
          <option value={s.student_id}>
            {s.name || s.student_id} {s.active_struggle ? '⚠️ Trapped' : `(${Math.round((s.average_autonomy_score ?? 0.85) * 100)}%)`}
          </option>
        {/each}
      </select>
    {/if}

    <!-- Bottlenecks Filter Chip -->
    <button
      type="button"
      class="bottleneck-chip"
      class:active={showBottlenecksOnly}
      onclick={() => (showBottlenecksOnly = !showBottlenecksOnly)}
      title="Toggle Bottlenecks focus"
    >
      <span class="chip-dot"></span>
      <span>Bottlenecks</span>
      <span class="chip-count">{masteryData?.bottlenecks?.length || 0}</span>
    </button>
  </div>

  <!-- Right Zone: Options -->
  <div class="header-right-zone">
    <!-- Options Popover Menu -->
    <div class="settings-menu-container">
      <button
        type="button"
        class="btn-options-toggle"
        class:active={showSettingsMenu}
        onclick={() => (showSettingsMenu = !showSettingsMenu)}
        title="Display options & filters"
      >
        <span>⚙️ Options</span>
        <span class="caret-icon">{showSettingsMenu ? '▴' : '▾'}</span>
      </button>

      {#if showSettingsMenu}
        <div class="settings-dropdown-card" role="menu">
          <div class="menu-section">
            <span class="menu-section-title">Display & Limits</span>
            <div class="menu-row">
              <span class="menu-label">Node Cap:</span>
              <select class="menu-select" bind:value={maxNodesLimit}>
                <option value={20}>20 nodes</option>
                <option value={30}>30 nodes</option>
                <option value={50}>50 nodes</option>
                <option value="all">All ({masteryData?.graph?.nodes?.length || 0})</option>
              </select>
            </div>
            <div class="menu-row">
              <span class="menu-label">Theme:</span>
              <div class="theme-pill-group">
                <button
                  type="button"
                  class="theme-sub-btn"
                  class:active={theme === 'light'}
                  onclick={() => { theme = 'light'; localStorage?.setItem('obsidian_graph_theme', 'light'); }}
                >☀ Light</button>
                <button
                  type="button"
                  class="theme-sub-btn"
                  class:active={theme === 'dark'}
                  onclick={() => { theme = 'dark'; localStorage?.setItem('obsidian_graph_theme', 'dark'); }}
                >☾ Dark</button>
              </div>
            </div>
          </div>

          <div class="menu-section">
            <span class="menu-section-title">Mastery Legend</span>
            {#if graphPerspective === 'cohort'}
              <div class="legend-rows">
                <div class="legend-row-item"><span class="legend-dot dot-emerald"></span> ≥80% High Cohort Mastery</div>
                <div class="legend-row-item"><span class="legend-dot dot-amber"></span> 60–79% Developing / Partial</div>
                <div class="legend-row-item"><span class="legend-dot dot-rose"></span> &lt;60% Critical Friction / Trap</div>
              </div>
            {:else}
              <div class="legend-rows">
                <div class="legend-row-item"><span class="legend-dot dot-emerald"></span> Mastered Component</div>
                <div class="legend-row-item"><span class="legend-dot dot-blue"></span> Active Learning Frontier</div>
                <div class="legend-row-item"><span class="legend-dot dot-rose"></span> Trapped in Cognitive Trap</div>
              </div>
            {/if}
          </div>

          <div class="menu-section menu-links-section">
            <span class="menu-section-title">Quick Links</span>
            <div class="menu-links-row">
              <a class="menu-link-btn" href={`/#/modules?course_id=${selectedCourseId}`}>Studio ↗</a>
              <a class="menu-link-btn" href={`/#/knowledge-graph?course_id=${selectedCourseId}`}>Curriculum Graph ↗</a>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Overview Drawer Toggle Button -->
    <button
      type="button"
      class="btn-drawer-pill"
      class:active={!cohortOverviewCollapsed || hasSelectedConcept}
      onclick={() => {
        if (hasSelectedConcept) {
          selectedConceptId = '';
        } else {
          cohortOverviewCollapsed = !cohortOverviewCollapsed;
        }
      }}
      title="Toggle Diagnostic Drawer"
    >
      <span class="pill-icon">📊</span>
      <span>{hasSelectedConcept ? 'Return to Overview' : cohortOverviewCollapsed ? 'Show Overview' : 'Hide Overview'}</span>
    </button>
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
    gap: 12px;
    padding: 6px 10px;
    border-radius: 10px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    pointer-events: auto;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    max-width: calc(100vw - 440px);
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }

  :global(.dark-mode) .floating-header {
    background: rgba(20, 20, 24, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    color: #f1f5f9;
  }

  .header-left-zone {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .brand-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .header-badge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 2px 6px;
    border-radius: 4px;
    background: #0284c7;
    color: #ffffff;
  }

  .course-select-pill,
  .unit-select-pill {
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: rgba(0, 0, 0, 0.03);
    color: inherit;
    outline: none;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }
  .unit-select-pill {
    max-width: 160px;
  }
  :global(.dark-mode) .course-select-pill,
  :global(.dark-mode) .unit-select-pill {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.12);
  }
  .course-select-pill:hover,
  .unit-select-pill:hover {
    border-color: #0284c7;
  }

  .header-center-zone {
    display: flex;
    align-items: center;
    gap: 6px;
    border-left: 1px solid rgba(0, 0, 0, 0.08);
    border-right: 1px solid rgba(0, 0, 0, 0.08);
    padding: 0 10px;
  }
  :global(.dark-mode) .header-center-zone {
    border-color: rgba(255, 255, 255, 0.08);
  }

  .segmented-mode-bar {
    display: flex;
    align-items: center;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 6px;
    padding: 2px;
    gap: 2px;
  }
  :global(.dark-mode) .segmented-mode-bar {
    background: rgba(255, 255, 255, 0.08);
  }

  .mode-segment-btn {
    border: none;
    background: transparent;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
    cursor: pointer;
    color: #64748b;
    transition: all 0.15s ease;
    white-space: nowrap;
  }
  :global(.dark-mode) .mode-segment-btn {
    color: #94a3b8;
  }
  .mode-segment-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  :global(.dark-mode) .mode-segment-btn.active {
    background: #27272a;
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }

  .student-picker-inline {
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 5px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: rgba(0, 0, 0, 0.03);
    color: inherit;
    max-width: 140px;
    outline: none;
    cursor: pointer;
  }
  :global(.dark-mode) .student-picker-inline {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.12);
  }

  .bottleneck-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(225, 29, 72, 0.25);
    background: rgba(225, 29, 72, 0.06);
    color: #e11d48;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
  }
  .bottleneck-chip:hover {
    background: rgba(225, 29, 72, 0.12);
  }
  .bottleneck-chip.active {
    background: #e11d48;
    color: #ffffff;
    border-color: #e11d48;
    box-shadow: 0 1px 6px rgba(225, 29, 72, 0.35);
  }
  .chip-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #e11d48;
  }
  .bottleneck-chip.active .chip-dot {
    background: #ffffff;
  }
  .chip-count {
    font-size: 10px;
    font-weight: 700;
    padding: 0 4px;
    border-radius: 4px;
    background: rgba(225, 29, 72, 0.14);
  }
  .bottleneck-chip.active .chip-count {
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
  }

  .header-right-zone {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .settings-menu-container {
    position: relative;
  }

  .btn-options-toggle {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    background: transparent;
    color: #475569;
    border: 1px solid rgba(0, 0, 0, 0.12);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  :global(.dark-mode) .btn-options-toggle {
    color: #cbd5e1;
    border-color: rgba(255, 255, 255, 0.14);
  }
  .btn-options-toggle:hover,
  .btn-options-toggle.active {
    background: rgba(0, 0, 0, 0.05);
    color: #0f172a;
  }
  :global(.dark-mode) .btn-options-toggle:hover,
  :global(.dark-mode) .btn-options-toggle.active {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
  }

  .caret-icon {
    font-size: 8px;
  }

  .settings-dropdown-card {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 240px;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    z-index: 50;
  }
  :global(.dark-mode) .settings-dropdown-card {
    background: #18181b;
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
  }

  .menu-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    padding-bottom: 8px;
  }
  :global(.dark-mode) .menu-section {
    border-color: rgba(255, 255, 255, 0.06);
  }
  .menu-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .menu-section-title {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #94a3b8;
    letter-spacing: 0.4px;
  }

  .menu-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
  }

  .menu-label {
    color: #475569;
  }
  :global(.dark-mode) .menu-label {
    color: #cbd5e1;
  }

  .menu-select {
    font-size: 10.5px;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: transparent;
    color: inherit;
  }
  :global(.dark-mode) .menu-select {
    border-color: rgba(255, 255, 255, 0.15);
  }

  .theme-pill-group {
    display: flex;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 4px;
    padding: 2px;
    gap: 2px;
  }
  :global(.dark-mode) .theme-pill-group {
    background: rgba(255, 255, 255, 0.08);
  }

  .theme-sub-btn {
    border: none;
    background: transparent;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 3px;
    cursor: pointer;
    color: #64748b;
    transition: all 0.15s ease;
  }
  :global(.dark-mode) .theme-sub-btn {
    color: #94a3b8;
  }
  .theme-sub-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }
  :global(.dark-mode) .theme-sub-btn.active {
    background: #27272a;
    color: #ffffff;
  }

  .legend-rows {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 10px;
    color: #64748b;
  }
  :global(.dark-mode) .legend-rows {
    color: #94a3b8;
  }

  .legend-row-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .legend-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }
  .dot-emerald { background: #10b981; }
  .dot-amber { background: #f59e0b; }
  .dot-rose { background: #e11d48; }
  .dot-blue { background: #0284c7; }

  .menu-links-row {
    display: flex;
    gap: 8px;
  }

  .menu-link-btn {
    font-size: 10.5px;
    font-weight: 600;
    color: #0284c7;
    text-decoration: none;
    padding: 3px 6px;
    border-radius: 4px;
    background: rgba(2, 132, 199, 0.08);
    transition: background 0.15s ease;
  }
  .menu-link-btn:hover {
    background: rgba(2, 132, 199, 0.16);
  }

  .btn-drawer-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: rgba(0, 0, 0, 0.03);
    color: inherit;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
  }
  :global(.dark-mode) .btn-drawer-pill {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.12);
  }
  .btn-drawer-pill:hover,
  .btn-drawer-pill.active {
    border-color: #0284c7;
    color: #0284c7;
    background: rgba(2, 132, 199, 0.08);
  }
</style>
