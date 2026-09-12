<script>
  import { onMount } from 'svelte';
  import CurriculumGraphCanvas from '../lib/CurriculumGraphCanvas.svelte';
  import { responseError } from '../lib/session.js';

  let courses = $state([]);
  let selectedCourseId = $state('');
  let course = $state(null);
  let graph = $state({ nodes: [], edges: [], module_links: [], source_links: [], stats: {} });
  let selectedConceptId = $state('');
  let loading = $state(true);
  let error = $state('');

  // Student knowledge overlay: same graph, colored by what one student knows
  // instead of by course hierarchy. See docs/knowledge-graph-mastery-plan.md.
  let viewMode = $state('structure'); // 'structure' | 'mastery'
  let students = $state([]);
  let selectedStudentId = $state('');
  let loadingMastery = $state(false);

  let selectedConcept = $derived(graph.nodes.find((node) => node.concept_id === selectedConceptId) || null);
  let parents = $derived(graph.edges.filter((edge) => edge.relation === 'CONTAINS' && edge.target === selectedConceptId).map((edge) => graph.nodes.find((node) => node.concept_id === edge.source)?.label).filter(Boolean));
  let children = $derived(graph.edges.filter((edge) => edge.relation === 'CONTAINS' && edge.source === selectedConceptId).map((edge) => graph.nodes.find((node) => node.concept_id === edge.target)?.label).filter(Boolean));
  let prerequisites = $derived(graph.edges.filter((edge) => edge.relation === 'PREREQUISITE_OF' && edge.target === selectedConceptId).map((edge) => graph.nodes.find((node) => node.concept_id === edge.source)?.label).filter(Boolean));
  let moduleRoles = $derived(graph.module_links.filter((link) => link.concept_id === selectedConceptId).map((link) => ({ ...link, title: course?.modules?.find((module) => module.module_id === link.module_id)?.title || 'Course module' })));

  function hashCourseId() {
    const queryStart = window.location.hash.indexOf('?');
    return queryStart < 0 ? '' : new URLSearchParams(window.location.hash.slice(queryStart + 1)).get('course_id') || '';
  }

  async function loadCourseGraph(courseId = selectedCourseId) {
    if (!courseId) return;
    loading = true;
    error = '';
    viewMode = 'structure';
    selectedStudentId = '';
    try {
      const [courseResponse, graphResponse, rosterResponse] = await Promise.all([
        fetch(`/courses/${courseId}`),
        fetch(`/courses/${courseId}/concept-graph`),
        fetch(`/courses/${courseId}/roster`),
      ]);
      if (!courseResponse.ok) throw new Error(await responseError(courseResponse, 'The selected course could not be loaded.'));
      if (!graphResponse.ok) throw new Error(await responseError(graphResponse, 'The curriculum concept graph could not be loaded.'));
      course = await courseResponse.json();
      graph = await graphResponse.json();
      students = rosterResponse.ok ? (await rosterResponse.json()).students || [] : [];
      selectedCourseId = courseId;
      selectedConceptId = graph.nodes.some((node) => node.concept_id === selectedConceptId)
        ? selectedConceptId
        : graph.nodes[0]?.concept_id || '';
    } catch (err) {
      error = err.message || 'The curriculum concept graph could not be loaded.';
    } finally {
      loading = false;
    }
  }

  async function loadStudentMastery(studentId) {
    if (!selectedCourseId || !studentId) return;
    loadingMastery = true;
    error = '';
    try {
      const response = await fetch(`/courses/${selectedCourseId}/concept-graph/mastery/students/${encodeURIComponent(studentId)}`);
      if (!response.ok) throw new Error(await responseError(response, "That student's knowledge overlay could not be loaded."));
      const overlay = await response.json();
      graph = {
        ...graph,
        nodes: [...overlay.nodes, ...(overlay.emergent_nodes || [])],
        edges: overlay.edges,
        stats: { ...graph.stats, concepts: overlay.nodes.length, edges: overlay.edges.length },
      };
      selectedConceptId = graph.nodes.some((node) => node.concept_id === selectedConceptId)
        ? selectedConceptId
        : graph.nodes[0]?.concept_id || '';
    } catch (err) {
      error = err.message || "That student's knowledge overlay could not be loaded.";
    } finally {
      loadingMastery = false;
    }
  }

  function setViewMode(mode) {
    viewMode = mode;
    if (mode === 'structure') {
      loadCourseGraph(selectedCourseId);
    } else if (selectedStudentId) {
      loadStudentMastery(selectedStudentId);
    }
  }

  function onStudentChange(studentId) {
    selectedStudentId = studentId;
    if (studentId) loadStudentMastery(studentId);
  }

  async function initialise() {
    loading = true;
    try {
      const response = await fetch('/courses');
      if (!response.ok) throw new Error(await responseError(response, 'Courses could not be loaded.'));
      courses = await response.json();
      selectedCourseId = hashCourseId() || courses[0]?.course_id || '';
      if (selectedCourseId) await loadCourseGraph(selectedCourseId);
    } catch (err) {
      error = err.message || 'Courses could not be loaded.';
      loading = false;
    }
  }

  onMount(initialise);
</script>

<main class="live-graph-page">
  <header class="graph-header">
    <div><span class="eyebrow">Live Neo4j-backed curriculum model</span><h1>Curriculum Concept Graph</h1><p>This is the active course concept graph: high-to-low semantic concepts, hierarchy, prerequisites, module roles, and source evidence.</p></div>
    <div class="graph-actions">
      <label>Course<select bind:value={selectedCourseId} onchange={() => loadCourseGraph(selectedCourseId)}>{#each courses as item}<option value={item.course_id}>{item.title}</option>{/each}</select></label>
      <label>View
        <select value={viewMode} onchange={(event) => setViewMode(event.target.value)}>
          <option value="structure">Course structure</option>
          <option value="mastery">Student knowledge</option>
        </select>
      </label>
      {#if viewMode === 'mastery'}
        <label>Student
          <select value={selectedStudentId} onchange={(event) => onStudentChange(event.target.value)}>
            <option value="">Choose a student…</option>
            {#each students as student}<option value={student.student_id}>{student.student_id}</option>{/each}
          </select>
        </label>
      {/if}
      {#if selectedCourseId}<a class="btn btn-primary" href={`/#/modules?course_id=${selectedCourseId}`}>Open graph studio</a>{/if}
    </div>
  </header>

  {#if error}<div class="error-notice">{error}</div>{/if}
  {#if loading}
    <div class="loading"><div class="spinner"></div><span>Loading live course graph…</span></div>
  {:else if !course}
    <div class="empty"><strong>No course is available.</strong><span>Create or publish a course before viewing its concept graph.</span></div>
  {:else}
    <section class="graph-overview"><span>{course.domain}</span><span>{graph.stats.concepts || 0} concepts</span><span>{graph.stats.edges || 0} relationships</span><span>{graph.stats.module_links || 0} module roles</span><span>{graph.stats.source_links || 0} evidence links</span></section>
    {#if viewMode === 'mastery' && !selectedStudentId}
      <div class="empty"><strong>Choose a student.</strong><span>Pick a student above to see the course graph colored by what they've demonstrated.</span></div>
    {:else}
    <div class="graph-layout">
      <section class="live-canvas">
        {#if loadingMastery}<div class="loading canvas-loading"><div class="spinner"></div><span>Loading student overlay…</span></div>{/if}
        <CurriculumGraphCanvas {graph} {selectedConceptId} onSelect={(conceptId) => (selectedConceptId = conceptId)} colorBy={viewMode === 'mastery' ? 'mastery' : 'level'} />
      </section>
      <aside class="inspector">
        {#if selectedConcept}
          <span class="eyebrow">{selectedConcept.concept_type === 'emergent' ? "Student's own concept" : 'Selected live concept'}</span>
          <h2>{selectedConcept.label}</h2>
          <span class="level-pill">{(selectedConcept.state || selectedConcept.level).replaceAll('_', ' ')}</span>
          <p class="definition">{selectedConcept.definition}</p>
          {#if viewMode === 'mastery'}
            <div class="stat-grid">
              <div><span>State</span><strong>{selectedConcept.state}</strong></div>
              <div><span>Evidence</span><strong>{selectedConcept.evidence_count ?? '—'}</strong></div>
            </div>
            {#if selectedConcept.concept_type === 'emergent'}
              <section><p>This concept isn't part of the course graph — the student raised it in their own work. {selectedConcept.related_concept_id ? 'Shown connected to the closest course concept it relates to.' : ''}</p></section>
            {/if}
          {:else}
            <div class="stat-grid"><div><span>Type</span><strong>{selectedConcept.concept_type}</strong></div><div><span>Source evidence</span><strong>{(graph.source_links || []).filter((link) => link.concept_id === selectedConceptId).length} chunks</strong></div></div>
          {/if}
          {#if selectedConcept.concept_type !== 'emergent'}
            <section><h3>Hierarchy</h3><p><strong>Parent</strong>{parents.length ? parents.join(' · ') : 'Top-level concept'}</p><p><strong>Children</strong>{children.length ? children.join(' · ') : 'No lower-level concepts yet'}</p><p><strong>Prerequisites</strong>{prerequisites.length ? prerequisites.join(' · ') : 'No prerequisite relationship set'}</p></section>
          {/if}
          {#if viewMode !== 'mastery'}
            <section><h3>Module roles</h3>{#if moduleRoles.length}{#each moduleRoles as role}<p><span class={`role ${role.role}`}>{role.role}</span>{role.title}</p>{/each}{:else}<p>No explicit course-module role set.</p>{/if}</section>
          {/if}
        {:else}
          <div class="empty-inspector"><strong>Choose a node</strong><span>Select a concept in the live graph to inspect its teaching context and evidence.</span></div>
        {/if}
      </aside>
    </div>
    {/if}
  {/if}
</main>

<style>
  .live-graph-page{box-sizing:border-box;display:flex;flex:1;flex-direction:column;gap:18px;margin:0 auto;max-width:1680px;padding:26px 34px 50px;width:100%}.graph-header{align-items:flex-end;display:flex;gap:24px;justify-content:space-between}.eyebrow{color:var(--color-slate-muted);font-size:10px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}.graph-header h1{color:var(--color-heading);font-family:var(--font-brand);font-size:28px;margin:4px 0 6px}.graph-header p{color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;max-width:780px}.graph-actions{align-items:flex-end;display:flex;gap:10px}.graph-actions label{color:var(--color-slate-muted);display:flex;flex-direction:column;font-size:9px;font-weight:700;gap:5px;letter-spacing:.4px;text-transform:uppercase}.graph-actions select{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-bright);font-size:12px;max-width:260px;padding:8px}.graph-overview{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:flex;gap:0;overflow:auto}.graph-overview span{border-right:1px solid var(--color-graphite-border);color:var(--color-slate-light);font-size:11px;padding:10px 14px;white-space:nowrap}.graph-overview span:first-child{color:var(--color-horizon-bright);font-weight:700}.graph-layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;min-height:650px}.live-canvas{border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg) 0 0 var(--radius-lg);overflow:hidden;position:relative}.canvas-loading{background:rgba(10,14,20,.75);inset:0;min-height:0;position:absolute;z-index:5}.inspector{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-left:0;border-radius:0 var(--radius-lg) var(--radius-lg) 0;overflow:auto;padding:20px}.inspector h2{color:var(--color-heading);font-size:18px;line-height:1.35;margin:6px 0}.level-pill,.role{border-radius:99px;display:inline-block;font-size:9px;font-weight:700;padding:4px 7px;text-transform:uppercase}.level-pill{background:rgba(59,130,246,.13);border:1px solid rgba(59,130,246,.3);color:#93c5fd}.definition{color:var(--color-slate-light);font-size:12px;line-height:1.55}.stat-grid{display:grid;gap:8px;grid-template-columns:1fr 1fr}.stat-grid>div,.inspector section{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);padding:10px}.stat-grid span{color:var(--color-slate-muted);display:block;font-size:9px;font-weight:700;text-transform:uppercase}.stat-grid strong{color:var(--color-heading);font-size:11px}.inspector section{margin-top:12px}.inspector h3{color:var(--color-heading);font-size:10px;letter-spacing:.4px;margin:0 0 8px;text-transform:uppercase}.inspector p{color:var(--color-slate-light);font-size:11px;line-height:1.45;margin:7px 0}.inspector p strong{color:var(--color-slate-muted);display:block;font-size:9px;letter-spacing:.3px;text-transform:uppercase}.role{background:rgba(16,185,129,.12);color:#6ee7b7;margin-right:6px}.role.develops{background:rgba(59,130,246,.14);color:#93c5fd}.role.assesses{background:rgba(168,85,247,.14);color:#d8b4fe}.loading,.empty,.empty-inspector{align-items:center;color:var(--color-slate-light);display:flex;flex:1;flex-direction:column;font-size:13px;gap:10px;justify-content:center;min-height:360px;text-align:center}.empty strong,.empty-inspector strong{color:var(--color-heading);font-size:14px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:27px;width:27px}@keyframes spin{to{transform:rotate(360deg)}}.error-notice{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:var(--radius-sm);color:#fca5a5;font-size:12px;padding:11px 14px}@media(max-width:950px){.graph-header{align-items:flex-start;flex-direction:column}.graph-layout{grid-template-columns:1fr}.live-canvas{border-radius:var(--radius-lg) var(--radius-lg) 0 0}.inspector{border:1px solid var(--color-graphite-border);border-radius:0 0 var(--radius-lg) var(--radius-lg);min-height:260px}.graph-actions{width:100%}.graph-actions select{flex:1;max-width:none}}@media(max-width:600px){.live-graph-page{padding:20px 16px}.graph-actions{align-items:stretch;flex-direction:column}.graph-actions .btn{text-align:center}.graph-overview span{font-size:10px;padding:9px 10px}}
</style>
