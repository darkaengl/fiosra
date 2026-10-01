<script lang="ts">
  import CohortMasteryGraphCanvas from './CohortMasteryGraphCanvas.svelte';
  import RosterFilterBar from './roster/RosterFilterBar.svelte';
  import RosterTable from './roster/RosterTable.svelte';
  import RosterGraphToolbar from './roster/RosterGraphToolbar.svelte';
  import ConceptInspectorDrawer from './roster/ConceptInspectorDrawer.svelte';
  import {
    computeScopedGraph,
    getPrerequisites,
    getDownstreamDependents,
    getStrugglingStudentsForConcept,
    getLinkedProbes,
  } from './roster/rosterGraphUtils';
  import type {
    CourseDetails,
    GraphNode,
    GraphPerspective,
    MasteryData,
    RosterFilter,
    Student,
    ViewType,
  } from './roster/rosterTypes';

  let {
    students = [],
    courseId = '',
    onDispatchScaffold,
    onEvaluateStudentAssignment,
  } = $props<{
    students?: Student[];
    courseId?: string;
    onDispatchScaffold?: () => void;
    onEvaluateStudentAssignment?: (assignmentId: string, title?: string, studentId?: string, sessionId?: string) => void;
  }>();

  // Mode and perspective state
  let viewType = $state<ViewType>('table');
  let graphPerspective = $state<GraphPerspective>('cohort');
  let selectedStudentId = $state('');
  let showBottlenecksOnly = $state(false);
  let selectedConceptId = $state('');
  let graphTheme = $state<'light' | 'dark'>('light');

  // Async data state
  let masteryData = $state<MasteryData | null>(null);
  let isLoadingMastery = $state(false);
  let masteryError = $state('');
  let courseDetails = $state<CourseDetails | null>(null);

  // Filters & scoping state
  let filter = $state<RosterFilter>('all');
  let selectedModuleId = $state('all');
  let maxNodesLimit = $state<number | string>('all');

  // Dispatch state for the inspector drawer
  let isDispatchingIntervention = $state(false);
  let dispatchSuccessNotice = $state('');

  let filteredStudents = $derived.by(() => {
    if (filter === 'completed') return students.filter((s) => s.status === 'completed' || (s.completed_assignments ?? 0) > 0);
    if (filter === 'submitted') return students.filter((s) => s.status === 'submitted');
    if (filter === 'struggling') return students.filter((s) => s.active_struggle);
    if (filter === 'in_progress') return students.filter((s) => s.status !== 'submitted' && s.status !== 'completed' && !s.active_struggle);
    return students;
  });

  let completedCount = $derived(students.filter((s) => s.status === 'completed' || (s.completed_assignments ?? 0) > 0).length);
  let submittedCount = $derived(students.filter((s) => s.status === 'submitted').length);
  let strugglingCount = $derived(students.filter((s) => s.active_struggle).length);
  let inProgressCount = $derived(Math.max(0, students.length - completedCount - submittedCount - strugglingCount));

  async function loadMasteryData() {
    if (!courseId) return;
    isLoadingMastery = true;
    masteryError = '';
    try {
      const [masteryRes, courseRes] = await Promise.all([
        fetch(`/courses/${courseId}/concept-mastery`),
        fetch(`/courses/${courseId}`)
      ]);
      if (masteryRes.ok) {
        masteryData = await masteryRes.json();
      } else {
        masteryError = 'Failed to load concept mastery data.';
      }
      if (courseRes.ok) {
        courseDetails = await courseRes.json();
      }
    } catch (err) {
      console.error('Error fetching concept mastery:', err);
      masteryError = 'Network error fetching concept mastery.';
    } finally {
      isLoadingMastery = false;
    }
  }

  $effect(() => {
    if (courseId) {
      loadMasteryData();
    }
  });

  // Tree-preserving hierarchical scoping via extracted utility
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
        const stuDetails = students.find((s) => s.student_id === stu.student_id);
        const sessionId = stuDetails?.latest_session_id;
        if (!sessionId) continue;

        const payload = {
          session_id: sessionId,
          student_id: stu.student_id,
          teacher_id: "educator",
          concept_id: concept.concept_id || concept.id,
          concept_label: concept.label,
          misconception_id: concept.active_misconceptions?.[0]?.misconception_id || null,
          activity_type: "socratic_nudge",
          activity_prompt: concept.active_misconceptions?.[0]?.prompt || `Reflect on the foundational difference between ${concept.label} and related concepts. How does this apply to your reasoning?`,
          activity_guidance: "Review your earlier claims and ground them in specific course principles.",
        };

        const res = await fetch('/interventions/dispatch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) count++;
      }

      dispatchSuccessNotice = `Dispatched Socratic challenge to ${count} student${count === 1 ? '' : 's'}.`;
      await loadMasteryData();
      setTimeout(() => { dispatchSuccessNotice = ''; }, 4500);
    } catch (err) {
      console.error('Error dispatching interventions:', err);
    } finally {
      isDispatchingIntervention = false;
    }
  }

  function handleInspectStudentInGraph(studentId: string) {
    viewType = 'graph';
    graphPerspective = 'student';
    selectedStudentId = studentId;
  }
</script>

<div class="roster-wrapper">
  <!-- Top Segmented View Switcher -->
  <div class="roster-view-bar">
    <div class="view-mode-tabs">
      <button
        type="button"
        class="mode-tab-btn"
        class:active={viewType === 'table'}
        onclick={() => viewType = 'table'}
      >
        <span class="tab-icon">📋</span>
        <span>Learner Table ({students.length})</span>
      </button>
      <button
        type="button"
        class="mode-tab-btn"
        class:active={viewType === 'graph'}
        onclick={() => viewType = 'graph'}
      >
        <span class="tab-icon">🕸️</span>
        <span>Concept Graph Diagnostics</span>
        {#if (masteryData?.bottlenecks || []).length > 0}
          <span class="bottleneck-badge">{masteryData!.bottlenecks!.length} Bottlenecks</span>
        {/if}
      </button>
    </div>
  </div>

  {#if viewType === 'table'}
    <!-- Modular Tabular Roster -->
    <RosterFilterBar
      {filter}
      totalCount={students.length}
      {completedCount}
      {submittedCount}
      {strugglingCount}
      {inProgressCount}
      onFilterChange={(f) => filter = f}
    />

    <RosterTable
      students={filteredStudents}
      totalCount={students.length}
      {onEvaluateStudentAssignment}
      {onDispatchScaffold}
      onInspectStudentInGraph={handleInspectStudentInGraph}
    />
  {:else}
    <!-- Concept Knowledge Graph Diagnostics View -->
    <div class="graph-diagnostics-view">
      <RosterGraphToolbar
        bind:graphPerspective
        bind:selectedStudentId
        bind:selectedModuleId
        bind:maxNodesLimit
        bind:showBottlenecksOnly
        {masteryData}
        {courseDetails}
        nodeCount={scopedGraph.nodes.length}
      />

      <!-- Canvas & Inspector Split Layout -->
      <div class="canvas-inspector-layout">
        <div class="canvas-pane">
          {#if isLoadingMastery}
            <div class="graph-state-pane">
              <div class="loading-spinner"></div>
              <span>Computing Concept Topology &amp; Cohort Mastery...</span>
            </div>
          {:else if scopedGraph.nodes.length > 0}
            <CohortMasteryGraphCanvas
              graph={scopedGraph}
              selectedConceptId={selectedConceptId}
              onSelect={(id: string) => selectedConceptId = id}
              viewMode={graphPerspective}
              activeStudent={activeStudentObj}
              bottlenecksOnly={showBottlenecksOnly}
              bottlenecks={masteryData?.bottlenecks || []}
              theme={graphTheme}
            />
          {:else}
            <div class="graph-state-pane">
              <span>{masteryError || 'No concepts found matching the selected module filter.'}</span>
            </div>
          {/if}
        </div>

        <!-- Concept / Student Inspector Drawer -->
        <ConceptInspectorDrawer
          {selectedConcept}
          {masteryData}
          {prerequisites}
          {downstreamDependents}
          {strugglingStudentsForConcept}
          {linkedProbes}
          {isDispatchingIntervention}
          {dispatchSuccessNotice}
          onSelectConcept={(id) => selectedConceptId = id}
          onInspectStudent={(studentId) => {
            graphPerspective = 'student';
            selectedStudentId = studentId;
          }}
          onDispatchIntervention={handleBatchDispatchIntervention}
        />
      </div>
    </div>
  {/if}
</div>

<style>
  .roster-wrapper {
    background: var(--color-graphite-card, #ffffff);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: var(--radius-md, 8px);
    overflow: hidden;
  }

  .roster-view-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
  }

  .view-mode-tabs {
    display: flex;
    gap: 8px;
  }

  .mode-tab-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 14px;
    border-radius: var(--radius-sm, 6px);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    background: var(--color-graphite-card, #ffffff);
    color: var(--color-slate-light, #6d7378);
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .mode-tab-btn:hover {
    color: var(--color-heading, #111315);
    border-color: #0b4a4f;
  }

  .mode-tab-btn.active {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  .tab-icon {
    font-size: 14px;
  }

  .bottleneck-badge {
    background: #e11d48;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 9999px;
  }

  .graph-diagnostics-view {
    display: flex;
    flex-direction: column;
    min-height: 720px;
  }

  .canvas-inspector-layout {
    display: grid;
    grid-template-columns: 1fr 380px;
    height: 720px;
    overflow: hidden;
  }

  .canvas-pane {
    position: relative;
    border-right: 1px solid var(--color-graphite-border, #dddcd5);
    background: var(--color-obsidian, #111315);
    overflow: hidden;
  }

  .graph-state-pane {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 100%;
    color: var(--color-slate-light, #6d7378);
    font-size: 13px;
  }

  .loading-spinner {
    width: 24px;
    height: 24px;
    border: 3px solid rgba(11, 74, 79, 0.15);
    border-top-color: #0b4a4f;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 1024px) {
    .canvas-inspector-layout {
      grid-template-columns: 1fr;
      grid-template-rows: 500px auto;
      height: auto;
    }
  }
</style>
