<script lang="ts">
  import { onMount } from 'svelte';
  import CohortMasteryGraphCanvas from '../lib/CohortMasteryGraphCanvas.svelte';
  import CohortOverviewContent from '../lib/diagnostics/CohortOverviewContent.svelte';
  import ConceptDiagnosticDetail from '../lib/diagnostics/ConceptDiagnosticDetail.svelte';
  import {
    computeScopedGraph,
    getPrerequisites,
    getDownstreamDependents,
    getStrugglingStudentsForConcept,
    getLinkedProbes,
  } from '../lib/roster/rosterGraphUtils';
  import type { CourseDetails, GraphNode, GraphPerspective, MasteryData } from '../lib/roster/rosterTypes';
  import { responseError } from '../lib/session.js';

  let courses = $state<Array<{ course_id: string; title: string }>>([]);
  let selectedCourseId = $state('');
  let course = $state<CourseDetails | null>(null);
  let masteryData = $state<MasteryData | null>(null);
  let loading = $state(true);
  let error = $state('');

  // Mode and perspective state
  let graphPerspective = $state<GraphPerspective>('cohort');
  let selectedStudentId = $state('');
  let showBottlenecksOnly = $state(false);
  let selectedConceptId = $state('');
  let cohortOverviewCollapsed = $state(false);
  let theme = $state<'light' | 'dark'>(typeof localStorage !== 'undefined' && localStorage.getItem('obsidian_graph_theme') === 'dark' ? 'dark' : 'light');

  // Filter state
  let selectedModuleId = $state('all');
  let maxNodesLimit = $state<number | string>('all');
  let showSettingsMenu = $state(false);

  // Intervention state
  let isDispatchingIntervention = $state(false);
  let dispatchSuccessNotice = $state('');

  function hashCourseId() {
    const queryStart = window.location.hash.indexOf('?');
    return queryStart < 0 ? '' : new URLSearchParams(window.location.hash.slice(queryStart + 1)).get('course_id') || '';
  }

  function hashModuleId() {
    const queryStart = window.location.hash.indexOf('?');
    return queryStart < 0 ? '' : new URLSearchParams(window.location.hash.slice(queryStart + 1)).get('module_id') || '';
  }

  async function loadCourseDiagnostics(courseId = selectedCourseId) {
    if (!courseId) return;
    loading = true;
    error = '';
    try {
      const [courseRes, masteryRes] = await Promise.all([
        fetch(`/courses/${courseId}`),
        fetch(`/courses/${courseId}/concept-mastery`)
      ]);
      if (!courseRes.ok) throw new Error(await responseError(courseRes, 'Course could not be loaded.'));
      course = await courseRes.json();

      if (masteryRes.ok) {
        masteryData = await masteryRes.json();
      } else {
        throw new Error(await responseError(masteryRes, 'Cohort mastery data could not be loaded.'));
      }
      selectedCourseId = courseId;
    } catch (err: any) {
      error = err.message || 'Failed to load cohort diagnostics.';
    } finally {
      loading = false;
    }
  }

  async function initialise() {
    loading = true;
    error = '';
    try {
      const response = await fetch('/courses');
      if (!response.ok) throw new Error(await responseError(response, 'Course list could not be loaded.'));
      courses = await response.json();
      selectedCourseId = hashCourseId() || courses[0]?.course_id || '';
      const initialMod = hashModuleId();
      if (initialMod) selectedModuleId = initialMod;
      if (selectedCourseId) await loadCourseDiagnostics(selectedCourseId);
    } catch (err: any) {
      error = err.message || 'Courses could not be loaded.';
      loading = false;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      if (showSettingsMenu) {
        showSettingsMenu = false;
      } else if (selectedConceptId) {
        selectedConceptId = '';
      } else if (!cohortOverviewCollapsed) {
        cohortOverviewCollapsed = true;
      }
    }
  }

  function handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (showSettingsMenu && !target.closest('.settings-menu-container')) {
      showSettingsMenu = false;
    }
  }

  function handleHashChange() {
    const newCourseId = hashCourseId();
    if (newCourseId && newCourseId !== selectedCourseId) {
      selectedCourseId = newCourseId;
      loadCourseDiagnostics(selectedCourseId);
    }
    const newModuleId = hashModuleId();
    if (newModuleId && newModuleId !== selectedModuleId) {
      selectedModuleId = newModuleId;
    }
  }

  onMount(() => {
    initialise();
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('click', handleClickOutside);
    window.addEventListener('hashchange', handleHashChange);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('click', handleClickOutside);
      window.removeEventListener('hashchange', handleHashChange);
    };
  });

  // Tree-preserving hierarchical scoping via shared utility
  let scopedGraph = $derived(
    computeScopedGraph(masteryData, selectedModuleId, showBottlenecksOnly, maxNodesLimit)
  );

  let activeStudentObj = $derived(
    masteryData?.students?.find((s) => s.student_id === selectedStudentId) || null
  );

  let selectedConcept = $derived(
    masteryData?.graph?.nodes?.find((n) => (n.concept_id || n.id) === selectedConceptId) || null
  );

  let prerequisites = $derived(getPrerequisites(masteryData, selectedConceptId));
  let downstreamDependents = $derived(getDownstreamDependents(masteryData, selectedConceptId));
  let strugglingStudentsForConcept = $derived(getStrugglingStudentsForConcept(masteryData, selectedConceptId));
  let linkedProbes = $derived(getLinkedProbes(masteryData, selectedConceptId));

  async function handleBatchDispatchIntervention(concept: GraphNode) {
    if (!concept) return;
    isDispatchingIntervention = true;
    dispatchSuccessNotice = '';
    try {
      const targetStudents = strugglingStudentsForConcept;
      if (targetStudents.length === 0) return;

      let count = 0;
      for (const stu of targetStudents) {
        const stuDetails = (masteryData?.students || []).find((s) => s.student_id === stu.student_id);
        const sessionId = stuDetails?.latest_session_id;
        if (!sessionId) continue;

        const payload = {
          session_id: sessionId,
          student_id: stu.student_id,
          teacher_id: 'educator',
          concept_id: concept.concept_id || concept.id,
          concept_label: concept.label,
          misconception_id: concept.active_misconceptions?.[0]?.misconception_id || null,
          activity_type: 'socratic_nudge',
          activity_prompt: concept.active_misconceptions?.[0]?.prompt || `Reflect on the foundational difference between ${concept.label} and related concepts. How does this apply to your reasoning?`,
          activity_guidance: 'Review your earlier claims and ground them in specific course principles.',
        };

        const res = await fetch('/interventions/dispatch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) count++;
      }

      dispatchSuccessNotice = `Dispatched Socratic challenge to ${count} student${count === 1 ? '' : 's'}.`;
      await loadCourseDiagnostics(selectedCourseId);
      setTimeout(() => { dispatchSuccessNotice = ''; }, 4500);
    } catch (err) {
      console.error('Error dispatching interventions:', err);
    } finally {
      isDispatchingIntervention = false;
    }
  }
</script>

<main class="full-screen-graph-page" class:light-mode={theme === 'light'} class:dark-mode={theme === 'dark'}>
  <!-- Streamlined Floating Command Toolbar -->
  <header class="floating-header">
    <!-- Left Zone: Course & Scope -->
    <div class="header-left-zone">
      <div class="brand-group">
        <span class="header-badge">Diagnostics</span>
        <select
          class="course-select-pill"
          bind:value={selectedCourseId}
          onchange={() => loadCourseDiagnostics(selectedCourseId)}
          title="Switch Course"
        >
          {#each courses as item}
            <option value={item.course_id}>{item.title}</option>
          {/each}
        </select>
      </div>

      {#if (course?.modules || []).length > 0}
        <select class="unit-select-pill" bind:value={selectedModuleId} title="Filter by Unit / Module">
          <option value="all">All Units ({scopedGraph.nodes.length} nodes)</option>
          {#each (course!.modules || []).slice().sort((a, b) => a.position - b.position) as mod}
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
        class:active={!cohortOverviewCollapsed || !!selectedConcept}
        onclick={() => {
          if (selectedConcept) {
            selectedConceptId = '';
          } else {
            cohortOverviewCollapsed = !cohortOverviewCollapsed;
          }
        }}
        title="Toggle Diagnostic Drawer"
      >
        <span class="pill-icon">📊</span>
        <span>{selectedConcept ? 'Return to Overview' : cohortOverviewCollapsed ? 'Show Overview' : 'Hide Overview'}</span>
      </button>
    </div>
  </header>

  {#if error}
    <div class="floating-error-notice">{error}</div>
  {/if}

  {#if loading}
    <div class="full-screen-loading">
      <div class="spinner"></div>
      <span>Computing Concept Topology &amp; Cohort Mastery...</span>
    </div>
  {:else if !course}
    <div class="full-screen-empty">
      <strong>No course is available.</strong>
      <span>Please select or configure a course in the Course Portfolio.</span>
    </div>
  {:else}
    <!-- 100% Full-Screen Canvas -->
    <div class="full-canvas-container">
      {#if scopedGraph.nodes.length > 0}
        <CohortMasteryGraphCanvas
          graph={scopedGraph}
          {selectedConceptId}
          onSelect={(conceptId: string) => {
            selectedConceptId = conceptId;
            if (conceptId) cohortOverviewCollapsed = false;
          }}
          bind:theme
          viewMode={graphPerspective}
          activeStudent={activeStudentObj}
          bottlenecksOnly={showBottlenecksOnly}
          bottlenecks={masteryData?.bottlenecks || []}
          showHud={false}
        />
      {:else}
        <div class="graph-state-pane">
          <span>No concepts found matching the selected scope filter.</span>
        </div>
      {/if}

      <!-- Subtle Floating Legend at Bottom-Center of Canvas -->
      <div class="canvas-bottom-legend">
        {#if graphPerspective === 'cohort'}
          <span class="legend-chip"><span class="legend-dot dot-emerald"></span> ≥80% Mastered</span>
          <span class="legend-chip"><span class="legend-dot dot-amber"></span> 60–79% Developing</span>
          <span class="legend-chip"><span class="legend-dot dot-rose"></span> &lt;60% Trapped</span>
        {:else}
          <span class="legend-chip"><span class="legend-dot dot-emerald"></span> Mastered</span>
          <span class="legend-chip"><span class="legend-dot dot-blue"></span> Active Frontier</span>
          <span class="legend-chip"><span class="legend-dot dot-rose"></span> Trapped</span>
        {/if}
      </div>
    </div>

    <!-- Diagnostic Window on the Right -->
    {#if selectedConcept || !cohortOverviewCollapsed}
      <aside class="node-popup-drawer" aria-label="Diagnostic Window">
        {#if selectedConcept}
          <ConceptDiagnosticDetail
            {selectedConcept}
            {masteryData}
            {prerequisites}
            {downstreamDependents}
            {strugglingStudentsForConcept}
            {linkedProbes}
            {isDispatchingIntervention}
            {dispatchSuccessNotice}
            onClose={() => (selectedConceptId = '')}
            onInspectStudent={(studentId) => {
              selectedStudentId = studentId;
              graphPerspective = 'student';
            }}
            onDispatchIntervention={handleBatchDispatchIntervention}
          />
        {:else}
          <CohortOverviewContent
            {masteryData}
            onClose={() => (cohortOverviewCollapsed = true)}
            onSelectConcept={(conceptId) => (selectedConceptId = conceptId)}
            onInspectStudent={(studentId) => {
              selectedStudentId = studentId;
              graphPerspective = 'student';
            }}
          />
        {/if}
      </aside>
    {/if}
  {/if}
</main>

<style>
  .full-screen-graph-page {
    position: relative;
    width: 100%;
    height: calc(100vh - 64px);
    overflow: hidden;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }

  .full-canvas-container {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
  }

  /* Streamlined Floating Command Toolbar */
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
  }

  .light-mode .floating-header {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }

  .dark-mode .floating-header {
    background: rgba(20, 20, 24, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    color: #f1f5f9;
  }

  /* Left Zone: Course & Scope */
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
  .dark-mode .course-select-pill,
  .dark-mode .unit-select-pill {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.12);
  }
  .course-select-pill:hover,
  .unit-select-pill:hover {
    border-color: #0284c7;
  }

  /* Center Zone: Perspective & Bottlenecks */
  .header-center-zone {
    display: flex;
    align-items: center;
    gap: 6px;
    border-left: 1px solid rgba(0, 0, 0, 0.08);
    border-right: 1px solid rgba(0, 0, 0, 0.08);
    padding: 0 10px;
  }
  .dark-mode .header-center-zone {
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
  .dark-mode .segmented-mode-bar {
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
  .dark-mode .mode-segment-btn {
    color: #94a3b8;
  }
  .mode-segment-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  .dark-mode .mode-segment-btn.active {
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
  .dark-mode .student-picker-inline {
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

  /* Right Zone: Options & Drawer Toggle */
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
  .dark-mode .btn-options-toggle {
    color: #cbd5e1;
    border-color: rgba(255, 255, 255, 0.14);
  }
  .btn-options-toggle:hover,
  .btn-options-toggle.active {
    background: rgba(0, 0, 0, 0.05);
    color: #0f172a;
  }
  .dark-mode .btn-options-toggle:hover,
  .dark-mode .btn-options-toggle.active {
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
  .dark-mode .settings-dropdown-card {
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
  .dark-mode .menu-section {
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
  .dark-mode .menu-label {
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
  .dark-mode .menu-select {
    border-color: rgba(255, 255, 255, 0.15);
  }

  .theme-pill-group {
    display: flex;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 4px;
    padding: 2px;
    gap: 2px;
  }
  .dark-mode .theme-pill-group {
    background: rgba(255, 255, 255, 0.08);
  }
  .theme-sub-btn {
    border: none;
    background: transparent;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    cursor: pointer;
    color: #64748b;
  }
  .dark-mode .theme-sub-btn { color: #94a3b8; }
  .theme-sub-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  .dark-mode .theme-sub-btn.active {
    background: #27272a;
    color: #ffffff;
  }

  .legend-rows {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .legend-row-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10.5px;
    color: #475569;
  }
  .dark-mode .legend-row-item {
    color: #cbd5e1;
  }

  .menu-links-row {
    display: flex;
    gap: 6px;
  }
  .menu-link-btn {
    flex: 1;
    text-align: center;
    padding: 4px 6px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 600;
    text-decoration: none;
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.1);
    color: inherit;
    transition: all 0.15s;
  }
  .dark-mode .menu-link-btn {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.12);
  }
  .menu-link-btn:hover {
    background: #0284c7;
    color: #ffffff;
    border-color: #0284c7;
  }

  .btn-drawer-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(2, 132, 199, 0.08);
    color: #0284c7;
    border: 1px solid rgba(2, 132, 199, 0.25);
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
  }
  .btn-drawer-pill:hover,
  .btn-drawer-pill.active {
    background: #0284c7;
    color: #ffffff;
    border-color: #0284c7;
    box-shadow: 0 1px 6px rgba(2, 132, 199, 0.3);
  }
  .pill-icon {
    font-size: 11px;
  }

  /* Diagnostic Window on the Right */
  .node-popup-drawer {
    position: absolute;
    top: 14px;
    right: 14px;
    bottom: 14px;
    width: 410px;
    max-width: calc(100vw - 28px);
    z-index: 35;
    border-radius: 10px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: slideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(18px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .light-mode .node-popup-drawer {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(0, 0, 0, 0.14);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.14);
    color: #0f172a;
  }

  .dark-mode .node-popup-drawer {
    background: rgba(20, 20, 24, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.65);
    color: #f1f5f9;
  }

  .canvas-bottom-legend {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 14px;
    border-radius: 9999px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    pointer-events: none;
  }
  .light-mode .canvas-bottom-legend {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
    color: #475569;
  }
  .dark-mode .canvas-bottom-legend {
    background: rgba(24, 24, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    color: #cbd5e1;
  }

  .legend-chip {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 500;
  }

  .legend-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }
  .dot-emerald { background: #059669; }
  .dot-amber { background: #d97706; }
  .dot-rose { background: #e11d48; }
  .dot-blue { background: #0284c7; }

  .graph-state-pane,
  .full-screen-loading,
  .full-screen-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 100%;
    font-size: 13px;
    color: #64748b;
  }

  .spinner {
    width: 28px;
    height: 28px;
    border: 3px solid rgba(2, 132, 199, 0.15);
    border-top-color: #0284c7;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .floating-error-notice {
    position: absolute;
    top: 60px;
    left: 14px;
    z-index: 30;
    padding: 8px 14px;
    border-radius: 8px;
    background: rgba(225, 29, 72, 0.1);
    border: 1px solid rgba(225, 29, 72, 0.3);
    color: #e11d48;
    font-size: 12px;
    font-weight: 600;
  }
</style>
