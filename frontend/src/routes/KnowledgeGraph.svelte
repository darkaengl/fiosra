<script>
  import { onMount } from 'svelte';
  import CurriculumGraphCanvas from '../lib/CurriculumGraphCanvas.svelte';
  import KnowledgeGraphHeader from '../lib/graph/KnowledgeGraphHeader.svelte';
  import KnowledgeGraphInspector from '../lib/graph/KnowledgeGraphInspector.svelte';
  import HydrationModal from '../lib/graph/HydrationModal.svelte';
  import EmptyGraphHero from '../lib/graph/EmptyGraphHero.svelte';
  import { subgraphForUnit } from '../lib/graph/subgraphUtils';
  import { responseError } from '../lib/session.js';

  let courses = $state([]);
  let selectedCourseId = $state('');
  let course = $state(null);
  let graph = $state({ nodes: [], edges: [], module_links: [], source_links: [], probes: [], stats: {} });
  let selectedConceptId = $state('');
  let loading = $state(true);
  let error = $state('');

  // Synchronized Obsidian theme ('light' by default, matching reference)
  let theme = $state(typeof localStorage !== 'undefined' ? localStorage.getItem('obsidian_graph_theme') || 'light' : 'light');

  let selectedConcept = $derived(graph.nodes.find((node) => node.concept_id === selectedConceptId) || null);
  let selectedModuleId = $state('');

  let visibleGraph = $derived(subgraphForUnit(graph, selectedModuleId));
  let unitFilterActive = $derived(Boolean(selectedModuleId) && visibleGraph !== graph);
  let selectedUnitTitle = $derived(
    course?.modules?.find((m) => m.module_id === selectedModuleId)?.title || ''
  );

  let isHydrating = $state(false);
  let hydrationProgress = $state(0);
  let hydrationStage = $state('');
  let hydrationTimer = null;

  function hashCourseId() {
    const queryStart = window.location.hash.indexOf('?');
    return queryStart < 0 ? '' : new URLSearchParams(window.location.hash.slice(queryStart + 1)).get('course_id') || '';
  }

  function hashModuleId() {
    const queryStart = window.location.hash.indexOf('?');
    return queryStart < 0 ? '' : new URLSearchParams(window.location.hash.slice(queryStart + 1)).get('module_id') || '';
  }

  async function loadCourseGraph(courseId = selectedCourseId) {
    if (!courseId) return;
    loading = true;
    error = '';
    try {
      const [courseResponse, graphResponse] = await Promise.all([
        fetch(`/courses/${courseId}`),
        fetch(`/courses/${courseId}/concept-graph`),
      ]);
      if (!courseResponse.ok) throw new Error(await responseError(courseResponse, 'The selected course could not be loaded.'));
      if (!graphResponse.ok) throw new Error(await responseError(graphResponse, 'The curriculum concept graph could not be loaded.'));
      course = await courseResponse.json();
      graph = await graphResponse.json();
      selectedCourseId = courseId;
      selectedConceptId = graph.nodes.some((node) => node.concept_id === selectedConceptId)
        ? selectedConceptId
        : '';
    } catch (err) {
      error = err.message || 'The curriculum concept graph could not be loaded.';
    } finally {
      loading = false;
    }
  }

  async function startHydration() {
    if (!selectedCourseId || isHydrating) return;
    isHydrating = true;
    hydrationProgress = 12;
    hydrationStage = 'Extracting module syllabus and primary source excerpts...';
    error = '';

    clearInterval(hydrationTimer);
    let step = 0;
    const stages = [
      { pct: 32, msg: 'Analyzing primary source evidence and vocabulary...' },
      { pct: 58, msg: 'Synthesizing pedagogical concept hierarchy & DAG...' },
      { pct: 78, msg: 'Validating prerequisite relationships & cycle checks...' },
      { pct: 92, msg: 'Committing to Neo4j and binding source evidence links...' },
    ];
    hydrationTimer = setInterval(() => {
      if (step < stages.length) {
        hydrationProgress = stages[step].pct;
        hydrationStage = stages[step].msg;
        step++;
      }
    }, 2000);

    try {
      const res = await fetch(`/courses/${selectedCourseId}/concept-graph/hydrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_id: selectedModuleId || null }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Failed to hydrate concept graph.'));

      clearInterval(hydrationTimer);
      hydrationProgress = 100;
      hydrationStage = 'Graph hydrated! Rendering interactive canvas...';

      const newGraph = await res.json();
      setTimeout(() => {
        graph = newGraph;
        if (!selectedConceptId && newGraph.nodes.length) {
          selectedConceptId = '';
        }
        isHydrating = false;
      }, 500);
    } catch (err) {
      clearInterval(hydrationTimer);
      error = err.message || 'Failed to hydrate concept graph.';
      isHydrating = false;
    }
  }

  async function initialise() {
    loading = true;
    try {
      const response = await fetch('/courses');
      if (!response.ok) throw new Error(await responseError(response, 'Courses could not be loaded.'));
      courses = await response.json();
      selectedCourseId = hashCourseId() || courses[0]?.course_id || '';
      selectedModuleId = hashModuleId() || '';
      if (selectedCourseId) await loadCourseGraph(selectedCourseId);
    } catch (err) {
      error = err.message || 'Courses could not be loaded.';
      loading = false;
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape' && selectedConceptId) {
      selectedConceptId = '';
    }
  }

  function handleHashChange() {
    const newCourseId = hashCourseId();
    const newModuleId = hashModuleId();
    if (newModuleId && newModuleId !== selectedModuleId) {
      selectedModuleId = newModuleId;
    }
    if (newCourseId && newCourseId !== selectedCourseId) {
      selectedCourseId = newCourseId;
      loadCourseGraph(selectedCourseId);
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
</script>

<main class="full-screen-graph-page" class:light-mode={theme === 'light'} class:dark-mode={theme === 'dark'}>
  <KnowledgeGraphHeader
    {course}
    {courses}
    bind:selectedCourseId
    bind:selectedModuleId
    {isHydrating}
    {selectedUnitTitle}
    {visibleGraph}
    fullGraph={graph}
    {unitFilterActive}
    onCourseChange={(id) => loadCourseGraph(id)}
    onStartHydration={startHydration}
  />

  {#if error}
    <div class="floating-error-notice">{error}</div>
  {/if}

  <HydrationModal
    {isHydrating}
    {hydrationStage}
    {hydrationProgress}
  />

  {#if loading}
    <div class="full-screen-loading">
      <div class="spinner"></div>
      <span>Loading curriculum graph…</span>
    </div>
  {:else if !course}
    <div class="full-screen-empty">
      <strong>No course is available.</strong>
      <span>Create or publish a course before viewing its concept graph.</span>
    </div>
  {:else}
    <!-- 100% Full-Page Graph Canvas -->
    <div class="full-canvas-container">
      <CurriculumGraphCanvas
        graph={visibleGraph}
        {selectedConceptId}
        onSelect={(conceptId) => (selectedConceptId = conceptId)}
        bind:theme
      />

      {#if graph.nodes.length === 0 && !loading && !isHydrating}
        <EmptyGraphHero
          {course}
          bind:selectedModuleId
          {isHydrating}
          onStartHydration={startHydration}
        />
      {/if}
    </div>

    {#if selectedConcept}
      <KnowledgeGraphInspector
        {selectedConcept}
        {selectedConceptId}
        graph={visibleGraph}
        {course}
        onSelectNode={(id) => (selectedConceptId = id)}
        onClose={() => (selectedConceptId = '')}
      />
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

  /* Full Screen Loading & Empty states */
  .full-screen-loading,
  .full-screen-empty {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    z-index: 10;
  }
  .light-mode .full-screen-loading,
  .light-mode .full-screen-empty {
    background: #ffffff;
    color: #475569;
  }
  .dark-mode .full-screen-loading,
  .dark-mode .full-screen-empty {
    background: #161616;
    color: #94a3b8;
  }

  .spinner {
    animation: spin 0.8s linear infinite;
    border: 3px solid rgba(59, 130, 246, 0.2);
    border-radius: 50%;
    border-top-color: #2563eb;
    height: 32px;
    width: 32px;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .floating-error-notice {
    position: absolute;
    top: 70px;
    left: 14px;
    z-index: 30;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    color: #dc2626;
    font-size: 11.5px;
    padding: 8px 12px;
  }
  .dark-mode .floating-error-notice {
    color: #fca5a5;
  }
</style>
