<script>
  import { onMount } from 'svelte';
  import CurriculumGraphCanvas from '../lib/CurriculumGraphCanvas.svelte';
  import { responseError } from '../lib/session.js';

  let courses = $state([]);
  let selectedCourseId = $state('');
  let course = $state(null);
  let masteryData = $state(null);
  let loading = $state(true);
  let error = $state('');

  // Mode and perspective state
  let graphPerspective = $state('cohort'); // 'cohort' | 'student'
  let selectedStudentId = $state('');
  let showBottlenecksOnly = $state(false);
  let selectedConceptId = $state('');
  let cohortOverviewCollapsed = $state(false);
  let theme = $state(typeof localStorage !== 'undefined' ? localStorage.getItem('obsidian_graph_theme') || 'light' : 'light');

  // Filter state
  let selectedModuleId = $state('all');
  let maxNodesLimit = $state(30);
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
    } catch (err) {
      error = err.message || 'Failed to load cohort diagnostics.';
    } finally {
      loading = false;
    }
  }

  async function initialise() {
    loading = true;
    try {
      const response = await fetch('/courses');
      if (!response.ok) throw new Error(await responseError(response, 'Courses could not be loaded.'));
      courses = await response.json();
      selectedCourseId = hashCourseId() || courses[0]?.course_id || '';
      const initialMod = hashModuleId();
      if (initialMod) selectedModuleId = initialMod;
      if (selectedCourseId) await loadCourseDiagnostics(selectedCourseId);
    } catch (err) {
      error = err.message || 'Courses could not be loaded.';
      loading = false;
    }
  }

  function handleKeyDown(e) {
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

  function handleClickOutside(e) {
    if (showSettingsMenu && !e.target.closest('.settings-menu-container')) {
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

    if (showBottlenecksOnly && bottleneckSet.size > 0) {
      const filteredTopics = candidateTopics.filter((t) => {
        const tid = t.concept_id || t.id;
        if (bottleneckSet.has(tid)) return true;
        return activeNodes.some((c) => c.parent_id === tid && bottleneckSet.has(c.concept_id || c.id));
      });
      if (filteredTopics.length > 0) candidateTopics = filteredTopics;
    }

    candidateTopics.sort((a, b) => {
      const aB = bottleneckSet.has(a.concept_id || a.id) ? 1 : 0;
      const bB = bottleneckSet.has(b.concept_id || b.id) ? 1 : 0;
      if (aB !== bB) return bB - aB;
      return (b.struggling_count || 0) - (a.struggling_count || 0);
    });

    for (const t of candidateTopics) {
      selectedIds.add(t.concept_id || t.id);
    }
    const topicIds = new Set(candidateTopics.map((t) => t.concept_id || t.id));

    // 4. Select Knowledge Components / Subconcepts (Rank 2) under chosen topics
    const candidateKCs = activeNodes.filter((n) => {
      const isKC = n.level === 'atomic_concept' || n.rank === 2;
      return isKC && n.parent_id && topicIds.has(n.parent_id);
    });

    candidateKCs.sort((a, b) => {
      const aB = bottleneckSet.has(a.concept_id || a.id) ? 1 : 0;
      const bB = bottleneckSet.has(b.concept_id || b.id) ? 1 : 0;
      if (aB !== bB) return bB - aB;
      return (b.struggling_count || 0) - (a.struggling_count || 0);
    });

    for (const kc of candidateKCs) {
      selectedIds.add(kc.concept_id || kc.id);
    }
    const kcIds = new Set(candidateKCs.map((kc) => kc.concept_id || kc.id));

    // 5. Select active Cognitive Traps / Misconceptions (Rank 3)
    const candidateTraps = activeNodes.filter((n) => {
      const isTrap = n.concept_type === 'misconception' || n.level === 'misconception';
      return isTrap && n.parent_id && kcIds.has(n.parent_id);
    });

    for (const tr of candidateTraps) {
      selectedIds.add(tr.concept_id || tr.id);
    }

    // 6. Apply max node cap if requested
    let finalNodes = activeNodes.filter((n) => selectedIds.has(n.concept_id || n.id));
    if (typeof maxNodesLimit === 'number' && finalNodes.length > maxNodesLimit) {
      const preservedStrands = finalNodes.filter((n) => strandIds.has(n.concept_id || n.id));
      const remainingSlots = Math.max(5, maxNodesLimit - preservedStrands.length);
      const otherNodes = finalNodes.filter((n) => !strandIds.has(n.concept_id || n.id));
      otherNodes.sort((a, b) => {
        const aB = bottleneckSet.has(a.concept_id || a.id) ? 1 : 0;
        const bB = bottleneckSet.has(b.concept_id || b.id) ? 1 : 0;
        if (aB !== bB) return bB - aB;
        return (b.struggling_count || 0) - (a.struggling_count || 0);
      });
      const keptOther = otherNodes.slice(0, remainingSlots);
      const keptSet = new Set([...preservedStrands.map((n) => n.concept_id || n.id), ...keptOther.map((n) => n.concept_id || n.id)]);
      finalNodes = finalNodes.filter((n) => keptSet.has(n.concept_id || n.id));
    }

    const finalNodeIds = new Set(finalNodes.map((n) => n.concept_id || n.id));
    const finalEdges = allEdges.filter((e) => finalNodeIds.has(e.source) && finalNodeIds.has(e.target));

    return {
      nodes: finalNodes,
      edges: finalEdges,
      probes: fullGraph.probes || []
    };
  });

  let activeStudentObj = $derived(
    masteryData?.students?.find((s) => s.student_id === selectedStudentId) || null
  );

  let selectedConcept = $derived(
    masteryData?.graph?.nodes?.find((n) => (n.concept_id || n.id) === selectedConceptId) || null
  );

  let isMisconception = $derived(
    selectedConcept?.concept_type === 'misconception' || selectedConcept?.level === 'misconception'
  );

  let strugglingStudentsForConcept = $derived(
    masteryData?.students?.filter((s) => s.concept_states?.[selectedConceptId] === 'trapped') || []
  );

  let linkedProbes = $derived(
    masteryData?.graph?.probes?.filter((p) => p.kc_id === selectedConceptId || p.concept_id === selectedConceptId || p.misconception_id === selectedConceptId) || []
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
        const stuDetails = (masteryData?.students || []).find((s) => s.student_id === stu.student_id);
        const sessionId = stuDetails?.latest_session_id;
        if (!sessionId) continue;

        const payload = {
          session_id: sessionId,
          student_id: stu.student_id,
          teacher_id: 'educator',
          concept_id: concept.concept_id,
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
          {#each (course.modules || []).slice().sort((a, b) => a.position - b.position) as mod}
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
            if (!selectedStudentId && masteryData?.students?.length > 0) {
              selectedStudentId = masteryData.students[0].student_id;
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
              {s.name} {s.active_struggle ? '⚠️ Trapped' : `(${Math.round(s.average_autonomy_score * 100)}%)`}
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
        class:active={!cohortOverviewCollapsed || selectedConcept}
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
        <CurriculumGraphCanvas
          graph={scopedGraph}
          {selectedConceptId}
          onSelect={(conceptId) => {
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
      <aside class="node-popup-drawer" role="dialog" aria-modal="true" aria-label="Diagnostic Window">
      {#if selectedConcept}
        <!-- Node Detail Diagnostics -->
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
            {#if masteryData?.bottlenecks?.includes(selectedConcept.concept_id || selectedConcept.id)}
              <span class="bottleneck-badge">⚠️ Bottleneck</span>
            {/if}
          </div>

          <button
            type="button"
            class="drawer-close-btn"
            onclick={() => (selectedConceptId = '')}
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
            <div class="section-title">Cohort Diagnostic Stats</div>
            <div class="stat-grid">
              <div class="metric-tile">
                <span class="metric-label">Mastery Rate</span>
                <strong
                  class="metric-val"
                  style="color: {selectedConcept.cohort_mastery_rate >= 0.8 ? '#059669' : selectedConcept.cohort_mastery_rate >= 0.6 ? '#d97706' : '#e11d48'};"
                >
                  {Math.round((selectedConcept.cohort_mastery_rate ?? 1) * 100)}%
                </strong>
              </div>
              <div class="metric-tile">
                <span class="metric-label">Total Assessed</span>
                <strong class="metric-val">{selectedConcept.total_assessed || 0}</strong>
              </div>
              <div class="metric-tile">
                <span class="metric-label">Trapped / Struggling</span>
                <strong
                  class="metric-val"
                  style="color: {selectedConcept.struggling_count > 0 ? '#e11d48' : 'inherit'};"
                >
                  {selectedConcept.struggling_count || 0}
                </strong>
              </div>
            </div>
          </div>

          <!-- Active Misconceptions -->
          {#if (selectedConcept.active_misconceptions || []).length > 0}
            <div class="inspector-section">
              <div class="section-title">Active Cognitive Traps</div>
              <div class="traps-list">
                {#each selectedConcept.active_misconceptions as trap}
                  <div class="trap-card">
                    <span class="trap-name">⚠️ {trap.label}</span>
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
              <div class="section-title">Trapped Learners ({strugglingStudentsForConcept.length})</div>

              <div class="dispatch-action-box">
                <button
                  type="button"
                  class="btn-dispatch"
                  disabled={isDispatchingIntervention}
                  onclick={() => handleBatchDispatchIntervention(selectedConcept)}
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
                      <span class="student-avatar">{stu.name?.slice(0, 2).toUpperCase() || 'ST'}</span>
                      <div>
                        <div class="student-name">{stu.name}</div>
                        <div class="student-sub">Autonomy: {Math.round(stu.average_autonomy_score * 100)}%</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      class="btn-inspect-learner"
                      onclick={() => {
                        selectedStudentId = stu.student_id;
                        graphPerspective = 'student';
                      }}
                    >
                      Inspect ➔
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
      {:else}
        <!-- Cohort Overview & Bottlenecks Diagnostics (when no node is selected) -->
        <header class="drawer-header">
          <div class="drawer-header-left">
            <span class="drawer-category-tag kc">📊 Cohort Overview</span>
          </div>
          <button
            type="button"
            class="drawer-close-btn"
            onclick={() => (cohortOverviewCollapsed = true)}
            aria-label="Collapse Cohort Overview"
            title="Collapse Overview (Esc)"
          >
            ✕
          </button>
        </header>

        <div class="drawer-content">
          <h2 class="drawer-title">Concept Diagnostics</h2>
          <p class="drawer-definition">
            Select any concept or trap node on the canvas to inspect real-time mastery, prerequisite dependencies, and trapped learners.
          </p>

          <!-- Overall Cohort KPIs -->
          <div class="inspector-section">
            <div class="section-title">Cohort Telemetry</div>
            <div class="stat-grid">
              <div class="metric-tile">
                <span class="metric-label">Learners</span>
                <strong class="metric-val">{masteryData?.students?.length || 0}</strong>
              </div>
              <div class="metric-tile">
                <span class="metric-label">Avg Autonomy</span>
                <strong class="metric-val" style="color: #0284c7;">
                  {Math.round(((masteryData?.students || []).reduce((acc, s) => acc + (s.average_autonomy_score || 0), 0) / Math.max(1, masteryData?.students?.length || 1)) * 100)}%
                </strong>
              </div>
              <div class="metric-tile">
                <span class="metric-label">High Bottlenecks</span>
                <strong class="metric-val" style="color: #e11d48;">
                  {masteryData?.bottlenecks?.length || 0}
                </strong>
              </div>
            </div>
          </div>

          <!-- High-Priority Bottlenecks List -->
          {#if (masteryData?.bottlenecks || []).length > 0}
            <div class="inspector-section">
              <div class="section-title text-rose">⚠️ High-Priority Bottlenecks ({masteryData.bottlenecks.length})</div>
              <div class="bottlenecks-list">
                {#each masteryData.bottlenecks as bId}
                  {@const bNode = masteryData.graph?.nodes?.find((n) => (n.concept_id || n.id) === bId)}
                  {#if bNode}
                    <button
                      type="button"
                      class="bottleneck-card-btn"
                      onclick={() => (selectedConceptId = bId)}
                    >
                      <div class="bn-title">{bNode.label}</div>
                      <div class="bn-meta">
                        <span class="bn-trapped">⚠️ {bNode.struggling_count || 0} trapped</span>
                        <span class="bn-arrow">Inspect ➔</span>
                      </div>
                    </button>
                  {/if}
                {/each}
              </div>
            </div>
          {/if}

          <!-- Struggling Learners -->
          {#if (masteryData?.students || []).filter((s) => s.active_struggle).length > 0}
            <div class="inspector-section">
              <div class="section-title text-rose">Learners Needing Scaffolding</div>
              <div class="students-list">
                {#each (masteryData?.students || []).filter((s) => s.active_struggle) as stu}
                  <div class="student-item-row">
                    <div class="student-info-left">
                      <span class="student-avatar">{stu.name?.slice(0, 2).toUpperCase() || 'ST'}</span>
                      <div>
                        <div class="student-name">{stu.name}</div>
                        <div class="student-sub">Autonomy: {Math.round(stu.average_autonomy_score * 100)}%</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      class="btn-inspect-learner"
                      onclick={() => {
                        selectedStudentId = stu.student_id;
                        graphPerspective = 'student';
                      }}
                    >
                      View Frontier ➔
                    </button>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
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
    background: rgba(24, 24, 27, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    color: #f8fafc;
  }

  /* Left Zone: Course & Unit Scope */
  .header-left-zone {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .brand-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .header-badge {
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #64748b;
    padding: 2px 5px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.04);
  }
  .dark-mode .header-badge {
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.06);
  }

  .course-select-pill,
  .unit-select-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: rgba(0, 0, 0, 0.03);
    color: inherit;
    outline: none;
    cursor: pointer;
    max-width: 170px;
    text-overflow: ellipsis;
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
    background: rgba(0, 0, 0, 0.06);
    color: #0f172a;
  }
  .dark-mode .btn-options-toggle:hover,
  .dark-mode .btn-options-toggle.active {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }
  .caret-icon {
    font-size: 9px;
    opacity: 0.7;
  }

  .settings-dropdown-card {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 250px;
    padding: 12px;
    border-radius: 8px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    z-index: 40;
    display: flex;
    flex-direction: column;
    gap: 12px;
    font-size: 11px;
    animation: fadeIn 0.15s ease;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .light-mode .settings-dropdown-card {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
    color: #1e293b;
  }
  .dark-mode .settings-dropdown-card {
    background: rgba(24, 24, 27, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6);
    color: #f1f5f9;
  }

  .menu-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    padding-bottom: 8px;
  }
  .dark-mode .menu-section {
    border-color: rgba(255, 255, 255, 0.08);
  }
  .menu-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .menu-section-title {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
  }
  .dark-mode .menu-section-title {
    color: #94a3b8;
  }

  .menu-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .menu-label {
    font-size: 11px;
    color: inherit;
  }

  .menu-select {
    font-size: 11px;
    padding: 3px 6px;
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.15);
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

  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  }
  .dark-mode .drawer-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
    width: 26px;
    height: 26px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    transition: all 0.15s ease;
  }
  .drawer-close-btn:hover {
    background: rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }
  .dark-mode .drawer-close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }

  .drawer-content {
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .drawer-title {
    font-size: 17px;
    font-weight: 700;
    line-height: 1.3;
    margin: 0;
  }

  .drawer-definition {
    font-size: 12px;
    line-height: 1.45;
    margin: 0;
    color: #475569;
  }
  .dark-mode .drawer-definition { color: #cbd5e1; }

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
  .dark-mode .section-title { color: #94a3b8; }
  .section-title.text-rose { color: #e11d48; }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }
  .metric-tile {
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .dark-mode .metric-tile {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.08);
  }
  .metric-label {
    font-size: 8.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
  }
  .metric-val {
    font-size: 14px;
    font-weight: 700;
  }

  /* Traps List */
  .traps-list {
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
    gap: 4px;
  }
  .trap-name {
    font-size: 11.5px;
    font-weight: 700;
    color: #be123c;
  }
  .trap-quote {
    font-size: 11px;
    font-style: italic;
    color: #334155;
    margin: 0;
  }
  .dark-mode .trap-quote { color: #e2e8f0; }
  .trap-prompt {
    font-size: 11px;
    color: #475569;
    margin: 0;
  }
  .dark-mode .trap-prompt { color: #cbd5e1; }

  /* Dispatch Box */
  .dispatch-action-box {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .btn-dispatch {
    width: 100%;
    padding: 8px 12px;
    background: #e11d48;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-dispatch:hover:not(:disabled) {
    background: #be123c;
  }
  .btn-dispatch:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .dispatch-success-pill {
    font-size: 11px;
    color: #059669;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    padding: 4px 8px;
    border-radius: 4px;
    text-align: center;
  }

  /* Students List */
  .students-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .student-item-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 9px;
    background: rgba(225, 29, 72, 0.04);
    border: 1px solid rgba(225, 29, 72, 0.15);
    border-radius: 5px;
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
    background: rgba(225, 29, 72, 0.15);
    color: #e11d48;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
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
    background: transparent;
    border: 1px solid rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    padding: 3px 7px;
    font-size: 10px;
    font-weight: 600;
    color: inherit;
    cursor: pointer;
  }
  .btn-inspect-learner:hover {
    background: #0284c7;
    color: #ffffff;
    border-color: #0284c7;
  }

  /* Probes List */
  .probes-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .probe-card {
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .dark-mode .probe-card {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.08);
  }
  .probe-tier {
    font-size: 9.5px;
    font-weight: 700;
    color: #0284c7;
    text-transform: uppercase;
  }
  .probe-question {
    font-size: 11.5px;
    font-style: italic;
    margin: 0;
    line-height: 1.35;
  }

  /* Bottlenecks List Panel (overview) */
  .bottlenecks-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .bottleneck-card-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 7px 10px;
    background: rgba(225, 29, 72, 0.05);
    border: 1px solid rgba(225, 29, 72, 0.2);
    border-radius: 5px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
    color: inherit;
  }
  .bottleneck-card-btn:hover {
    background: rgba(225, 29, 72, 0.12);
    border-color: #e11d48;
  }
  .bn-title {
    font-size: 11.5px;
    font-weight: 600;
  }
  .bn-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  .bn-trapped {
    font-size: 10px;
    font-weight: 700;
    color: #e11d48;
  }
  .bn-arrow {
    font-size: 10px;
    color: #64748b;
  }

  /* Empty/Loading states */
  .full-screen-loading,
  .full-screen-empty,
  .graph-state-pane {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #64748b;
    font-size: 13px;
  }
  .spinner {
    width: 28px;
    height: 28px;
    border: 3px solid rgba(59, 130, 246, 0.2);
    border-top-color: #2563eb;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .floating-error-notice {
    position: absolute;
    top: 68px;
    left: 14px;
    z-index: 26;
    background: #fee2e2;
    border: 1px solid #f87171;
    color: #991b1b;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
  }

  /* Subtle Floating Canvas Bottom Legend */
  .canvas-bottom-legend {
    position: absolute;
    bottom: 14px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 12px;
    border-radius: 999px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    font-size: 10.5px;
    font-weight: 500;
    pointer-events: none;
    z-index: 10;
    transition: all 0.2s ease;
  }
  .light-mode .canvas-bottom-legend {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
    color: #475569;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  }
  .dark-mode .canvas-bottom-legend {
    background: rgba(24, 24, 27, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
  }
  .legend-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .legend-dot {
    width: 6.5px;
    height: 6.5px;
    border-radius: 50%;
  }
  .dot-emerald { background: #059669; }
  .dot-amber { background: #d97706; }
  .dot-rose { background: #e11d48; }
  .dot-blue { background: #2563eb; }

</style>
