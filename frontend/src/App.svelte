<script>
  import { onMount } from 'svelte';
  import './css/design-system.css';
  import AppHeader from './lib/AppHeader.svelte';
  import CourseBanner from './lib/CourseBanner.svelte';
  import ModuleCard from './lib/ModuleCard.svelte';
  import AddResourceModal from './lib/AddResourceModal.svelte';
  import AddModuleModal from './lib/AddModuleModal.svelte';
  import CohortRoster from './lib/CohortRoster.svelte';

  let currentCourseId = $state('');
  let currentCourse = $state(null);
  let allResources = $state([]);
  let rosterData = $state({ total_enrolled: 0, students: [] });
  let activeTab = $state('modules'); // 'modules' | 'roster'
  let isLoading = $state(true);

  // Modal States
  let isAddModuleOpen = $state(false);
  let isAddResourceOpen = $state(false);
  let selectedModuleForResource = $state(null);

  async function loadCourseWorkspace() {
    isLoading = true;
    try {
      // 1. Determine Course ID from URL search or hash
      const urlParams = new URLSearchParams(window.location.search);
      let courseId = urlParams.get('course_id');

      if (!courseId) {
        // Fetch first available course as default
        const listRes = await fetch('/courses');
        if (listRes.ok) {
          const courses = await listRes.json();
          if (courses.length > 0) {
            courseId = courses[0].course_id;
          }
        }
      }

      if (!courseId) {
        isLoading = false;
        return;
      }

      currentCourseId = courseId;

      // 2. Fetch Course Data
      const courseRes = await fetch(`/courses/${courseId}`);
      if (courseRes.ok) {
        currentCourse = await courseRes.json();
      }

      // 3. Fetch Syllabus / Material Chunks
      await refreshResources();

      // 4. Fetch Roster Diagnostics
      await refreshRoster();
    } catch (err) {
      console.error('Error loading course workspace:', err);
    } finally {
      isLoading = false;
    }
  }

  async function refreshResources() {
    if (!currentCourseId) return;
    try {
      const res = await fetch(`/courses/${currentCourseId}/syllabus`);
      if (res.ok) {
        allResources = await res.json();
      }
    } catch (err) {
      console.warn('Could not refresh resources:', err);
    }
  }

  async function refreshRoster() {
    if (!currentCourseId) return;
    try {
      const res = await fetch(`/courses/${currentCourseId}/roster`);
      if (res.ok) {
        rosterData = await res.json();
      }
    } catch (err) {
      console.warn('Could not refresh roster:', err);
    }
  }

  async function handleModuleCreated() {
    if (!currentCourseId) return;
    const courseRes = await fetch(`/courses/${currentCourseId}`);
    if (courseRes.ok) {
      currentCourse = await courseRes.json();
    }
  }

  function handleOpenAddResource(mod) {
    selectedModuleForResource = mod;
    isAddResourceOpen = true;
  }

  async function handleDeleteResource(chunkId) {
    if (!confirm('Remove this grounded reading chunk from the curriculum and pgvector?')) return;
    try {
      const res = await fetch(`/courses/${currentCourseId}/resources/${chunkId}`, {
        method: 'DELETE',
      });
      if (res.ok || res.status === 204) {
        allResources = allResources.filter((r) => r.chunk_id !== chunkId);
      }
    } catch (err) {
      alert('Failed to delete resource: ' + err.message);
    }
  }

  onMount(() => {
    loadCourseWorkspace();
  });
</script>

<div class="fiosra-app">
  <AppHeader
    activeTab="modules"
    courseTitle={currentCourse?.title || 'Course Workspace'}
    courseId={currentCourseId}
  />

  <main class="modules-main">
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <div style="color: var(--color-slate-light); font-size: 14px;">
          Initializing Grounded Curriculum Engine...
        </div>
      </div>
    {:else if !currentCourse}
      <div class="empty-workspace">
        <div style="font-size: 42px;">🗺️</div>
        <h2>No Course Selected</h2>
        <p>Please select an active course workspace from the Course Portfolio.</p>
        <a href="educator_lms_courses.html" class="btn btn-primary">Go to Course Portfolio</a>
      </div>
    {:else}
      <!-- Course Banner -->
      <CourseBanner
        course={currentCourse}
        courseId={currentCourseId}
        enrolledCount={rosterData.total_enrolled || rosterData.students?.length || 0}
        onAddModule={() => (isAddModuleOpen = true)}
      />

      <!-- View Switcher Tabs -->
      <div class="view-switcher">
        <button
          type="button"
          class="view-tab-btn {activeTab === 'modules' ? 'active' : ''}"
          onclick={() => (activeTab = 'modules')}
        >
          <span>🗺️</span> Curriculum Architecture &amp; Sequencer ({currentCourse.modules?.length || 0} Units)
        </button>
        <button
          type="button"
          class="view-tab-btn {activeTab === 'roster' ? 'active' : ''}"
          onclick={() => (activeTab = 'roster')}
        >
          <span>👥</span> Cohort Roster &amp; Autonomy Diagnostics ({rosterData.total_enrolled || rosterData.students?.length || 0} Students)
        </button>
      </div>

      <!-- Modules Sequencer View -->
      {#if activeTab === 'modules'}
        <div class="modules-container">
          {#if !currentCourse.modules || currentCourse.modules.length === 0}
            <div class="empty-modules">
              <div style="font-size: 42px;">🗺️</div>
              <h3>No Curriculum Modules Configured Yet</h3>
              <p>
                This workspace is active in PostgreSQL and Neo4j. Add your first curriculum unit module below to start building prerequisite knowledge graphs.
              </p>
              <button
                type="button"
                class="btn btn-primary"
                onclick={() => (isAddModuleOpen = true)}
              >
                + Add First Curriculum Module
              </button>
            </div>
          {:else}
            {#each currentCourse.modules.slice().sort((a, b) => a.position - b.position) as mod, idx (mod.module_id)}
              <ModuleCard
                module={mod}
                index={idx}
                resources={allResources.filter((r) => r.module_id === mod.module_id)}
                courseId={currentCourseId}
                onAddResource={handleOpenAddResource}
                onDeleteResource={handleDeleteResource}
              />
            {/each}
          {/if}
        </div>
      {:else}
        <!-- Cohort Roster View -->
        <CohortRoster
          students={rosterData.students || []}
          courseId={currentCourseId}
          onDispatchScaffold={() => alert('Targeted Socratic micro-scaffold dispatched to flagged students.')}
        />
      {/if}
    {/if}
  </main>

  <!-- Modals -->
  <AddModuleModal
    isOpen={isAddModuleOpen}
    courseId={currentCourseId}
    nextPosition={(currentCourse?.modules?.length || 0) + 1}
    onClose={() => (isAddModuleOpen = false)}
    onSuccess={handleModuleCreated}
  />

  <AddResourceModal
    isOpen={isAddResourceOpen}
    courseId={currentCourseId}
    targetModule={selectedModuleForResource}
    onClose={() => (isAddResourceOpen = false)}
    onSuccess={refreshResources}
  />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: var(--color-obsidian);
    color: var(--color-slate-bright);
    font-family: var(--font-body);
    -webkit-font-smoothing: antialiased;
  }

  .fiosra-app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .modules-main {
    padding: 24px 36px 80px 36px;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    min-height: 360px;
  }

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(59, 130, 246, 0.2);
    border-top-color: var(--color-horizon-bright);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-workspace,
  .empty-modules {
    background: var(--color-graphite);
    border: 2px dashed var(--color-graphite-border);
    border-radius: var(--radius-lg);
    padding: 50px 32px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .empty-workspace h2,
  .empty-modules h3 {
    font-family: var(--font-brand);
    color: #ffffff;
    margin: 0;
  }

  .empty-workspace p,
  .empty-modules p {
    color: var(--color-slate-light);
    max-width: 520px;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
  }

  .view-switcher {
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 12px;
  }

  .view-tab-btn {
    background: none;
    border: none;
    color: var(--color-slate-light);
    font-size: 13.5px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.15s ease;
  }

  .view-tab-btn:hover {
    color: #ffffff;
    background: var(--color-graphite-hover);
  }

  .view-tab-btn.active {
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: var(--color-horizon-bright);
  }

  .modules-container {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
</style>
