<script>
  import { onMount } from 'svelte';
  import ScoreMeter from './ScoreMeter.svelte';
  import CurriculumGraphCanvas from './CurriculumGraphCanvas.svelte';

  let {
    students = [],
    courseId = '',
    onDispatchScaffold,
    onEvaluateStudentAssignment,
  } = $props();

  // Mode and perspective state
  let viewType = $state('table'); // 'table' | 'graph'
  let graphPerspective = $state('cohort'); // 'cohort' | 'student'
  let selectedStudentId = $state('');
  let showBottlenecksOnly = $state(false);
  let selectedConceptId = $state('');
  let graphTheme = $state('light');

  // Async data state
  let masteryData = $state(null);
  let isLoadingMastery = $state(false);
  let masteryError = $state('');

  // Dispatch state for the inspector drawer
  let isDispatchingIntervention = $state(false);
  let dispatchSuccessNotice = $state('');

  // Table filter state
  let filter = $state('all'); // 'all' | 'completed' | 'submitted' | 'struggling' | 'in_progress'

  let filteredStudents = $derived.by(() => {
    if (filter === 'completed') return students.filter((s) => s.status === 'completed' || s.completed_assignments > 0);
    if (filter === 'submitted') return students.filter((s) => s.status === 'submitted');
    if (filter === 'struggling') return students.filter((s) => s.active_struggle);
    if (filter === 'in_progress') return students.filter((s) => s.status !== 'submitted' && s.status !== 'completed' && !s.active_struggle);
    return students;
  });

  let completedCount = $derived(students.filter((s) => s.status === 'completed' || s.completed_assignments > 0).length);
  let submittedCount = $derived(students.filter((s) => s.status === 'submitted').length);
  let strugglingCount = $derived(students.filter((s) => s.active_struggle).length);

  let courseDetails = $state(null);
  let selectedModuleId = $state('all');
  let maxNodesLimit = $state(30);

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

  // Tree-preserving hierarchical scoping: ensures parents and children remain connected
  let scopedGraph = $derived.by(() => {
    if (!masteryData?.graph) return { nodes: [], edges: [], probes: [] };
    const fullGraph = masteryData.graph;
    const allNodes = fullGraph.nodes || [];
    const allEdges = fullGraph.edges || [];

    // 1. Filter out probes and dormant misconceptions (0 student triggers)
    const activeNodes = allNodes.filter((n) => {
      const type = n.concept_type || n.level;
      if (type === 'socratic_probe') return false;
      if (type === 'misconception') {
        const triggers = n.active_trigger_count || n.struggling_count || 0;
        if (triggers === 0) return false;
      }
      return true;
    });

    const activeNodeMap = new Map(activeNodes.map((n) => [n.concept_id || n.id, n]));
    const bottleneckSet = new Set(masteryData?.bottlenecks || []);

    // 2. Select root / strand nodes
    let rootStrands = [];
    const strandNodes = activeNodes.filter((n) => n.level === 'strand');
    if (selectedModuleId !== 'all') {
      rootStrands = strandNodes.filter((n) => n.module_id === selectedModuleId);
      if (rootStrands.length === 0) {
        rootStrands = activeNodes.filter((n) => n.module_id === selectedModuleId && n.rank === 0);
      }
      if (rootStrands.length === 0) {
        rootStrands = strandNodes.slice(0, 1);
      }
    } else {
      rootStrands = strandNodes.length > 0 ? strandNodes : activeNodes.filter((n) => n.rank === 0);
    }

    const selectedIds = new Set(rootStrands.map((r) => r.concept_id || r.id));
    const strandIds = new Set(selectedIds);

    // 3. Select Topics (Rank 1) under chosen strands
    let candidateTopics = activeNodes.filter((n) => {
      const isTopic = n.level === 'topic' || n.rank === 1;
      if (!isTopic) return false;
      if (selectedModuleId !== 'all') {
        return (n.module_id === selectedModuleId) || (n.parent_id && strandIds.has(n.parent_id));
      }
      return true;
    });

    // If Bottlenecks Only filter is checked, prioritize topics that are bottlenecks or have bottleneck children
    if (showBottlenecksOnly && bottleneckSet.size > 0) {
      const filteredTopics = candidateTopics.filter((t) => {
        const tid = t.concept_id || t.id;
        if (bottleneckSet.has(tid)) return true;
        return activeNodes.some((c) => c.parent_id === tid && bottleneckSet.has(c.concept_id || c.id));
      });
      if (filteredTopics.length > 0) candidateTopics = filteredTopics;
    }

    // Sort topics by bottleneck status & struggle count
    candidateTopics.sort((a, b) => {
      const aB = bottleneckSet.has(a.concept_id || a.id) ? 1 : 0;
      const bB = bottleneckSet.has(b.concept_id || b.id) ? 1 : 0;
      if (aB !== bB) return bB - aB;
      return (b.struggling_count || 0) - (a.struggling_count || 0);
    });

    // Add topics to selection
    for (const t of candidateTopics) {
      selectedIds.add(t.concept_id || t.id);
    }
    const topicIds = new Set(candidateTopics.map((t) => t.concept_id || t.id));

    // 4. Select Knowledge Components / Subconcepts (Rank 2) under chosen topics
    const candidateKCs = activeNodes.filter((n) => {
      const isKC = n.level === 'atomic_concept' || n.rank === 2;
      return isKC && n.parent_id && topicIds.has(n.parent_id);
    });

    // Sort KCs by struggle count (prioritize concepts where students are trapped)
    candidateKCs.sort((a, b) => {
      const aStruggle = (a.struggling_count || 0) > 0 ? 1 : 0;
      const bStruggle = (b.struggling_count || 0) > 0 ? 1 : 0;
      if (aStruggle !== bStruggle) return bStruggle - aStruggle;
      return (b.struggling_count || 0) - (a.struggling_count || 0);
    });

    // Determine max node quota for KCs
    const limit = maxNodesLimit === 'all' ? 250 : Number(maxNodesLimit);
    const availableKCSlots = Math.max(4, limit - selectedIds.size);
    const chosenKCs = candidateKCs.slice(0, availableKCSlots);

    for (const kc of chosenKCs) {
      selectedIds.add(kc.concept_id || kc.id);
    }
    const kcIds = new Set(chosenKCs.map((k) => k.concept_id || k.id));

    // 5. Select Active Misconceptions (Rank 3) attached to the chosen KCs or Topics
    const activeMisconceptions = activeNodes.filter((n) => {
      const isMisc = n.level === 'misconception' || n.concept_type === 'misconception';
      if (!isMisc) return false;
      const pid = n.parent_id;
      return pid && (kcIds.has(pid) || topicIds.has(pid));
    });

    for (const m of activeMisconceptions) {
      selectedIds.add(m.concept_id || m.id);
    }

    // Filter final nodes & edges preserving connections
    const scopedNodes = activeNodes.filter((n) => selectedIds.has(n.concept_id || n.id));
    const scopedEdges = allEdges.filter(
      (e) => selectedIds.has(e.source) && selectedIds.has(e.target)
    );

    return {
      ...fullGraph,
      nodes: scopedNodes,
      edges: scopedEdges,
      probes: fullGraph.probes || [],
    };
  });

  let activeStudentObj = $derived(
    masteryData?.students?.find((s) => s.student_id === selectedStudentId) || null
  );

  let selectedConcept = $derived(
    masteryData?.graph?.nodes?.find((n) => (n.concept_id || n.id) === selectedConceptId) || null
  );

  let prerequisites = $derived(
    masteryData?.graph?.edges
      ?.filter((e) => (e.relation === 'REQUIRES' || e.relation === 'PREREQUISITE_OF') && e.target === selectedConceptId)
      ?.map((e) => masteryData.graph.nodes.find((n) => (n.concept_id || n.id) === e.source)?.label || e.source)
      ?.filter(Boolean) || []
  );

  let downstreamDependents = $derived(
    masteryData?.graph?.edges
      ?.filter((e) => (e.relation === 'REQUIRES' || e.relation === 'PREREQUISITE_OF') && e.source === selectedConceptId)
      ?.map((e) => masteryData.graph.nodes.find((n) => (n.concept_id || n.id) === e.target)?.label || e.target)
      ?.filter(Boolean) || []
  );

  let strugglingStudentsForConcept = $derived(
    masteryData?.students?.filter((s) => s.concept_states?.[selectedConceptId] === 'trapped') || []
  );

  let linkedProbes = $derived(
    masteryData?.graph?.probes?.filter((p) => p.kc_id === selectedConceptId || p.concept_id === selectedConceptId) || []
  );

  async function handleBatchDispatchIntervention(concept) {
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
          concept_id: concept.concept_id,
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
          <span class="bottleneck-badge">{masteryData.bottlenecks.length} Bottlenecks</span>
        {/if}
      </button>
    </div>
  </div>

  {#if viewType === 'table'}
    <!-- Tabular Roster View -->
    <div class="roster-filter-bar">
      <div class="filter-group">
        <button
          type="button"
          class="filter-pill"
          class:active={filter === 'all'}
          onclick={() => filter = 'all'}
        >
          All Learners ({students.length})
        </button>
        <button
          type="button"
          class="filter-pill"
          class:active={filter === 'completed'}
          onclick={() => filter = 'completed'}
        >
          Completed ({completedCount})
        </button>
        {#if submittedCount > 0}
          <button
            type="button"
            class="filter-pill"
            class:active={filter === 'submitted'}
            onclick={() => filter = 'submitted'}
          >
            Submitted ({submittedCount})
          </button>
        {/if}
        <button
          type="button"
          class="filter-pill"
          class:active={filter === 'struggling'}
          onclick={() => filter = 'struggling'}
        >
          Needs Scaffolding ({strugglingCount})
        </button>
        <button
          type="button"
          class="filter-pill"
          class:active={filter === 'in_progress'}
          onclick={() => filter = 'in_progress'}
        >
          In Progress ({Math.max(0, students.length - completedCount - submittedCount - strugglingCount)})
        </button>
      </div>
    </div>

    <div class="roster-table-scroll">
      <table class="roster-table">
        <thead>
          <tr>
            <th style="min-width: 200px;">Student Learner</th>
            <th style="min-width: 220px;">Current Assignment</th>
            <th style="min-width: 140px;">Diagnostic Status</th>
            <th style="min-width: 130px;">Autonomy Score</th>
            <th style="min-width: 110px;">Hint Rate</th>
            <th style="min-width: 220px;">Identified Flags &amp; Frontier</th>
          </tr>
        </thead>
        <tbody>
          {#if filteredStudents.length === 0}
            <tr>
              <td colspan="6" class="roster-empty">
                No students found matching the selected filter.
              </td>
            </tr>
          {:else}
            {#each filteredStudents as stu (stu.student_id)}
              <tr>
                <td>
                  <div class="student-cell">
                    <div class="student-avatar">
                      {stu.student_id.substring(0, 2).toUpperCase()}
                    </div>
                    <div class="student-info">
                      <div class="student-id">{stu.student_id}</div>
                      <div class="student-sub">{stu.session_count || 0} Sessions Logged</div>
                    </div>
                  </div>
                </td>
                <td>
                  {#if stu.assignment_id}
                    <button
                      type="button"
                      class="assignment-link-btn"
                      title="Inspect {stu.student_id}'s work on this assignment"
                      onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                    >
                      {stu.assignment_title || 'Course Module Task'} ↗
                    </button>
                  {:else}
                    <span class="assignment-text">
                      {stu.assignment_title || 'Course Module Task'}
                    </span>
                  {/if}
                </td>
                <td>
                  {#if stu.status === 'completed' || (stu.completed_assignments > 0 && stu.status !== 'submitted')}
                    {#if stu.assignment_id}
                      <button
                        type="button"
                        class="status-badge badge-completed clickable"
                        title="Inspect {stu.student_id}'s completed reasoning trace"
                        onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                      >
                        ✓ Completed ↗
                      </button>
                    {:else}
                      <span class="status-badge badge-completed">
                        ✓ Completed
                      </span>
                    {/if}
                  {:else if stu.status === 'submitted'}
                    {#if stu.assignment_id}
                      <button
                        type="button"
                        class="status-badge badge-submitted clickable"
                        title="Evaluate {stu.student_id}'s submission"
                        onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                      >
                        ✓ Submitted ↗
                      </button>
                    {:else}
                      <span class="status-badge badge-submitted">
                        ✓ Submitted
                      </span>
                    {/if}
                  {:else if stu.active_struggle}
                    {#if stu.assignment_id}
                      <button
                        type="button"
                        class="status-badge badge-scaffold clickable"
                        title="Inspect {stu.student_id}'s struggle trace"
                        onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                      >
                        ⚠️ Needs Scaffolding ↗
                      </button>
                    {:else}
                      <span class="status-badge badge-scaffold">
                        ⚠️ Needs Scaffolding
                      </span>
                    {/if}
                  {:else}
                    {#if stu.assignment_id}
                      <button
                        type="button"
                        class="status-badge badge-progressing clickable"
                        title="Inspect {stu.student_id}'s live progress & draft"
                        onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                      >
                        ● In Progress ↗
                      </button>
                    {:else}
                      <span class="status-badge badge-progressing">
                        ● In Progress
                      </span>
                    {/if}
                  {/if}
                </td>
                <td>
                  <ScoreMeter score={stu.average_autonomy_score || 0} />
                </td>
                <td>
                  <span class="hint-rate-chip">
                    {Math.round((stu.hint_consumption_rate || 0) * 100)}%
                  </span>
                </td>
                <td>
                  <div class="flags-cell">
                    {#if stu.active_struggle && stu.struggling_kcs?.length > 0}
                      <span class="struggle-warning">
                        ⚠️ {stu.struggling_kcs.join(', ')}
                      </span>
                    {:else}
                      <span class="no-struggle">None Detected</span>
                    {/if}
                    <button
                      type="button"
                      class="btn-inspect-graph-icon"
                      title="Inspect {stu.student_id}'s Concept Knowledge Graph"
                      onclick={() => {
                        viewType = 'graph';
                        graphPerspective = 'student';
                        selectedStudentId = stu.student_id;
                      }}
                    >
                      🕸️ Graph ↗
                    </button>
                  </div>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>

    <div class="roster-footer">
      <span class="footer-meta">
        Showing {filteredStudents.length} of {students.length} enrolled students.
      </span>
      <button
        type="button"
        class="btn btn-secondary btn-sm"
        onclick={() => onDispatchScaffold?.()}
      >
        🚀 Dispatch Targeted Socratic Micro-Scaffold
      </button>
    </div>
  {:else}
    <!-- Concept Knowledge Graph Diagnostics View -->
    <div class="graph-diagnostics-view">
      <!-- Toolbar -->
      <div class="graph-toolbar">
        <div class="toolbar-left">
          <div class="perspective-toggle-group">
            <button
              type="button"
              class="perspective-btn"
              class:active={graphPerspective === 'cohort'}
              onclick={() => { graphPerspective = 'cohort'; selectedStudentId = ''; }}
            >
              👥 Whole Cohort Heatmap
            </button>
            <div class="student-select-box">
              <span class="select-prefix">👤</span>
              <select
                class="student-dropdown"
                bind:value={selectedStudentId}
                onchange={(e) => {
                  if (e.target.value) {
                    graphPerspective = 'student';
                  } else {
                    graphPerspective = 'cohort';
                  }
                }}
              >
                <option value="">Select Individual Learner...</option>
                {#each (masteryData?.students || []) as s}
                  <option value={s.student_id}>
                    {s.name} {s.active_struggle ? '⚠️ (Trapped)' : `(${Math.round(s.average_autonomy_score * 100)}% Autonomy)`}
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
                <option value="all">All Units ({scopedGraph.nodes.length} nodes)</option>
                {#each courseDetails.modules as mod}
                  <option value={mod.module_id}>
                    Unit {mod.position}: {mod.title}
                  </option>
                {/each}
              </select>
            </div>
          {/if}

          <!-- Max Nodes Cap Selector (as in reference screenshot) -->
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

      <!-- Canvas & Inspector Split Layout -->
      <div class="canvas-inspector-layout">
        <div class="canvas-pane">
          {#if isLoadingMastery}
            <div class="graph-state-pane">
              <div class="loading-spinner"></div>
              <span>Computing Concept Topology &amp; Cohort Mastery...</span>
            </div>
          {:else if scopedGraph.nodes.length > 0}
            <CurriculumGraphCanvas
              graph={scopedGraph}
              selectedConceptId={selectedConceptId}
              onSelect={(id) => selectedConceptId = id}
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
        <aside class="concept-inspector-drawer">
          {#if selectedConcept}
            <div class="inspector-header">
              <div class="inspector-badge-row">
                <span class="type-pill">{selectedConcept.concept_type || selectedConcept.level || 'Concept'}</span>
                {#if selectedConcept.bloom_level}
                  <span class="bloom-pill">{selectedConcept.bloom_level}</span>
                {/if}
                {#if masteryData?.bottlenecks?.includes(selectedConcept.concept_id)}
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
                    style="color: {selectedConcept.cohort_mastery_rate >= 0.8 ? '#059669' : selectedConcept.cohort_mastery_rate >= 0.6 ? '#d97706' : '#e11d48'};"
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
                    onclick={() => handleBatchDispatchIntervention(selectedConcept)}
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
                          <div class="student-item-name">{stu.name}</div>
                          <div class="student-item-sub">Autonomy: {Math.round(stu.average_autonomy_score * 100)}%</div>
                        </div>
                      </div>
                      <button
                        type="button"
                        class="btn-inspect-student"
                        onclick={() => {
                          graphPerspective = 'student';
                          selectedStudentId = stu.student_id;
                        }}
                      >
                        Inspect Frontier ↗
                      </button>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>

            <!-- Active Cognitive Traps (Triggered by real students) -->
            {#if (selectedConcept.active_misconceptions || []).length > 0}
              <div class="inspector-section">
                <div class="section-title">Active Cognitive Traps ({selectedConcept.active_misconceptions.length})</div>
                <div class="traps-list">
                  {#each selectedConcept.active_misconceptions as trap}
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

            <!-- Micro Socratic Probes (Kept in drawer, off canvas to reduce noise) -->
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
                  <div class="panel-heading">⚠️ High-Priority Bottlenecks ({masteryData.bottlenecks.length})</div>
                  <div class="bottleneck-chips-list">
                    {#each masteryData.bottlenecks as bId}
                      {@const bNode = masteryData.graph?.nodes?.find((n) => (n.concept_id || n.id) === bId)}
                      {#if bNode}
                        <button
                          type="button"
                          class="bottleneck-chip-btn"
                          onclick={() => selectedConceptId = bId}
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
      </div>
    </div>
  {/if}
</div>

<style>
  .roster-wrapper {
    background: var(--color-graphite-card);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .roster-view-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--color-graphite-card);
    border-bottom: 1px solid var(--color-graphite-border);
    padding: 8px 16px;
  }

  .view-mode-tabs {
    display: flex;
    gap: 8px;
  }

  .mode-tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    font-size: 12.5px;
    font-weight: 600;
    font-family: var(--font-ui);
    color: var(--color-slate-light);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .mode-tab-btn:hover {
    background: rgba(0, 0, 0, 0.04);
    color: var(--color-heading);
  }

  .mode-tab-btn.active {
    background: var(--color-bone, #ffffff);
    color: var(--color-heading);
    border-color: var(--color-graphite-border);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .bottleneck-badge {
    font-size: 10px;
    font-weight: 700;
    color: #e11d48;
    background: rgba(225, 29, 72, 0.1);
    border: 1px solid rgba(225, 29, 72, 0.25);
    padding: 1px 6px;
    border-radius: 999px;
  }

  .roster-filter-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    border-bottom: 1px solid var(--color-graphite-border);
    background: var(--color-graphite);
  }

  .filter-group {
    display: flex;
    gap: 8px;
  }

  .filter-pill {
    padding: 5px 12px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-graphite-border);
    background: transparent;
    color: var(--color-slate-muted);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .filter-pill:hover {
    color: var(--color-heading);
    background: rgba(255, 255, 255, 0.04);
  }

  .filter-pill.active {
    background: var(--color-horizon-bright);
    color: #ffffff;
    border-color: var(--color-horizon-bright);
  }

  .roster-table-scroll {
    overflow-x: auto;
  }

  .roster-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 13px;
  }

  .roster-table th {
    background: var(--color-graphite);
    color: var(--color-slate-muted);
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 10px 18px;
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .roster-table td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--color-graphite-border);
    vertical-align: middle;
  }

  .roster-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }

  .roster-empty {
    text-align: center;
    padding: 40px;
    color: var(--color-slate-muted);
    font-style: italic;
  }

  .student-cell {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .student-avatar {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-sm);
    background: var(--color-horizon-muted, #1e293b);
    color: var(--color-horizon-bright, #38bdf8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 11px;
    flex-shrink: 0;
  }

  .student-id {
    font-weight: 600;
    color: var(--color-heading);
    font-size: 13px;
  }

  .student-sub {
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .assignment-link-btn {
    background: none;
    border: none;
    padding: 0;
    color: var(--color-horizon-bright);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: color 0.15s;
  }

  .assignment-link-btn:hover {
    color: #60a5fa;
    text-decoration: underline;
  }

  .assignment-text {
    color: var(--color-slate-bright);
    font-size: 12.5px;
  }

  .status-badge {
    display: inline-flex;
    padding: 3px 8px;
    border-radius: var(--radius-xs);
    font-size: 11px;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }

  .badge-completed {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #059669;
    font-weight: 700;
  }

  .badge-submitted {
    background: rgba(59, 130, 246, 0.12);
    border: 1px solid rgba(59, 130, 246, 0.28);
    color: #2563eb;
  }

  .status-badge.clickable {
    cursor: pointer;
    border: 1px solid rgba(16, 185, 129, 0.4);
    transition: all 0.15s;
  }

  .status-badge.clickable:hover {
    background: rgba(16, 185, 129, 0.25);
    transform: translateY(-1px);
  }

  .badge-scaffold {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.28);
    color: #f59e0b;
  }

  .badge-progressing {
    background: rgba(59, 130, 246, 0.12);
    border: 1px solid rgba(59, 130, 246, 0.28);
    color: #3b82f6;
  }

  .hint-rate-chip {
    font-size: 11.5px;
    font-family: var(--font-mono);
    color: var(--color-slate-bright);
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 7px;
    border-radius: var(--radius-xs);
  }

  .flags-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .struggle-warning {
    color: var(--color-rose);
    font-weight: 600;
    font-size: 12px;
  }

  .no-struggle {
    color: var(--color-slate-muted);
    font-size: 12px;
  }

  .btn-inspect-graph-icon {
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light);
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .btn-inspect-graph-icon:hover {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  .roster-footer {
    padding: 12px 20px;
    background: var(--color-graphite-card);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .footer-meta {
    font-size: 12px;
    color: var(--color-slate-light);
  }

  .btn-sm {
    padding: 5px 12px;
    font-size: 11.5px;
  }

  /* Graph Diagnostics View Styling */
  .graph-diagnostics-view {
    display: flex;
    flex-direction: column;
    min-height: 720px;
  }

  .graph-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 18px;
    background: var(--color-graphite);
    border-bottom: 1px solid var(--color-graphite-border);
    gap: 12px;
    flex-wrap: wrap;
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .perspective-toggle-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .perspective-btn {
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 5px;
    border: 1px solid var(--color-graphite-border);
    background: transparent;
    color: var(--color-slate-light);
    cursor: pointer;
    transition: all 0.15s;
  }

  .perspective-btn.active {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  .student-select-box {
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--color-bone, #ffffff);
    border: 1px solid var(--color-graphite-border);
    border-radius: 5px;
    padding: 2px 8px;
  }

  .select-prefix {
    font-size: 12px;
  }

  .student-dropdown {
    border: none;
    background: transparent;
    font-size: 12px;
    font-family: var(--font-ui);
    color: var(--color-heading);
    outline: none;
    cursor: pointer;
  }

  .bottleneck-toggle-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: #e11d48;
    cursor: pointer;
  }

  .graph-legend {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 11px;
    color: var(--color-slate-light);
  }

  .legend-item {
    display: inline-flex;
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
  .dot-blue { background: #2563eb; }
  .dot-muted { background: #94a3b8; }

  /* Canvas and Inspector Split */
  .canvas-inspector-layout {
    display: grid;
    grid-template-columns: 1fr 340px;
    height: 700px;
    overflow: hidden;
  }

  .canvas-pane {
    position: relative;
    width: 100%;
    height: 100%;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
  }

  .graph-state-pane {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 100%;
    color: var(--color-slate-light);
    font-size: 13px;
  }

  /* Concept Inspector Drawer */
  .concept-inspector-drawer {
    background: var(--color-graphite-card);
    overflow-y: auto;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .inspector-header {
    border-bottom: 1px solid var(--color-graphite-border);
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
    color: var(--color-slate-bright);
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
    color: var(--color-heading);
    margin: 0 0 6px 0;
    line-height: 1.35;
  }

  .concept-def {
    font-size: 12px;
    line-height: 1.45;
    color: var(--color-slate-light);
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
    color: var(--color-slate-muted);
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
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
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
    color: var(--color-slate-muted);
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
    color: var(--color-slate-muted);
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
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-bright);
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
    color: var(--color-heading);
  }

  .student-item-sub {
    font-size: 10px;
    color: var(--color-slate-muted);
  }

  .btn-inspect-student {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    color: var(--color-slate-light);
    cursor: pointer;
  }

  .btn-inspect-student:hover {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  /* Empty Inspector State */
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
    color: var(--color-heading);
  }

  .inspector-empty-state p {
    font-size: 11.5px;
    line-height: 1.45;
    color: var(--color-slate-light);
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
    font-family: var(--font-ui);
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
    color: var(--color-heading);
  }

  .chip-trapped {
    font-size: 10px;
    font-weight: 700;
    color: #e11d48;
  }

  .unit-select-box {
    display: flex;
    align-items: center;
    gap: 5px;
    background: var(--color-bone, #ffffff);
    border: 1px solid var(--color-graphite-border);
    border-radius: 5px;
    padding: 2px 8px;
  }

  .max-nodes-box {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--color-bone, #ffffff);
    border: 1px solid var(--color-graphite-border);
    border-radius: 5px;
    padding: 2px 8px;
  }

  .max-nodes-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light);
    white-space: nowrap;
  }

  .max-nodes-select {
    border: none;
    background: transparent;
    font-size: 11.5px;
    font-family: var(--font-ui);
    color: var(--color-heading);
    outline: none;
    cursor: pointer;
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
    color: var(--color-slate-light);
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
    border: 1px solid var(--color-graphite-border);
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
    color: var(--color-heading);
    line-height: 1.4;
  }
</style>
