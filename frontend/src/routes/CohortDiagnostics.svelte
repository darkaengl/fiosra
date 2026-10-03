<script lang="ts">
  import { onMount } from 'svelte';
  import CohortMasteryGraphCanvas from '../lib/CohortMasteryGraphCanvas.svelte';
  import CohortOverviewContent from '../lib/diagnostics/CohortOverviewContent.svelte';
  import ConceptDiagnosticDetail from '../lib/diagnostics/ConceptDiagnosticDetail.svelte';
  import DiagnosticsFloatingHeader from '../lib/diagnostics/DiagnosticsFloatingHeader.svelte';
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
      if (selectedConceptId) {
        selectedConceptId = '';
      } else if (!cohortOverviewCollapsed) {
        cohortOverviewCollapsed = true;
      }
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
    window.addEventListener('hashchange', handleHashChange);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
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
  <DiagnosticsFloatingHeader
    {courses}
    bind:selectedCourseId
    {course}
    bind:selectedModuleId
    scopedNodesCount={scopedGraph.nodes.length}
    bind:graphPerspective
    bind:selectedStudentId
    {masteryData}
    bind:showBottlenecksOnly
    bind:maxNodesLimit
    bind:theme
    bind:selectedConceptId
    bind:cohortOverviewCollapsed
    hasSelectedConcept={!!selectedConcept}
    onCourseChange={(id) => loadCourseDiagnostics(id)}
  />

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
    <!-- Main Interactive Graph Canvas Container -->
    <div class="full-canvas-container" role="region" aria-label="Cohort Mastery Concept Map">
      {#if scopedGraph.nodes.length > 0}
        <CohortMasteryGraphCanvas
          graph={scopedGraph}
          {selectedConceptId}
          onSelect={(id, node) => {
            selectedConceptId = node ? (node.concept_id || node.id || id) : id;
            if (node || id) cohortOverviewCollapsed = true;
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

  /* Full Screen Loading & Empty */
  .full-screen-loading,
  .full-screen-empty {
    margin: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    z-index: 10;
    color: var(--color-slate-light);
    font-size: 14px;
    padding: 40px;
  }

  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(59, 130, 246, 0.2);
    border-top-color: var(--color-horizon-bright);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .graph-state-pane {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--color-graphite-card);
    border: 1px dashed var(--color-graphite-border);
    padding: 24px 32px;
    border-radius: var(--radius-md);
    color: var(--color-slate-muted);
    font-size: 13.5px;
    z-index: 5;
    pointer-events: none;
  }

  .floating-error-notice {
    position: absolute;
    top: 64px;
    left: 20px;
    z-index: 30;
    background: var(--color-rose-bg);
    color: var(--color-rose-text);
    border: 1px solid var(--color-rose);
    border-radius: var(--radius-sm);
    padding: 8px 16px;
    font-size: 12.5px;
    box-shadow: var(--shadow-sm);
  }

  /* Diagnostic Window Popup Drawer */
  .node-popup-drawer {
    position: absolute;
    top: 14px;
    right: 14px;
    bottom: 14px;
    width: 400px;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 12px;
    z-index: 20;
    display: flex;
    flex-direction: column;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.12);
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }

  :global(.dark-mode) .node-popup-drawer {
    background: rgba(18, 18, 22, 0.94);
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
  }

  /* Canvas Bottom Legend */
  .canvas-bottom-legend {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 20px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    pointer-events: none;
    font-size: 11px;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    color: #475569;
  }

  :global(.dark-mode) .canvas-bottom-legend {
    background: rgba(20, 20, 24, 0.85);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    color: #94a3b8;
  }

  .legend-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
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

  @media (max-width: 900px) {
    .node-popup-drawer {
      width: calc(100% - 28px);
      left: 14px;
      right: 14px;
      bottom: 14px;
      top: auto;
      max-height: 60vh;
    }
  }
</style>
