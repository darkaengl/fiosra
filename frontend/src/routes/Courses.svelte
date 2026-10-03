<script lang="ts">
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import InstitutionalFooter from '../lib/InstitutionalFooter.svelte';
  import CourseStatsRibbon from '../lib/courses/CourseStatsRibbon.svelte';
  import CourseCardItem from '../lib/courses/CourseCardItem.svelte';
  import CourseCreateModal from '../lib/courses/CourseCreateModal.svelte';
  import CourseIngestModal from '../lib/courses/CourseIngestModal.svelte';

  let courses = $state<any[]>([]);
  let isLoading = $state(true);
  let loadError = $state('');

  // Search & Filter & Pagination
  let searchQuery = $state('');
  let selectedDomain = $state('all');
  let currentPage = $state(1);
  const pageSize = 6;

  // Modals
  let showCreateCourse = $state(false);
  let showIngestModal = $state(false);

  async function loadCourses() {
    isLoading = true;
    loadError = '';
    try {
      const res = await fetch('/courses');
      if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
      courses = await res.json();
    } catch (err) {
      console.error('Failed to load courses:', err);
      loadError = 'The course portfolio could not be loaded. No example data is being shown.';
    } finally {
      isLoading = false;
    }
  }

  // Filtered and Paginated Courses
  let filteredCourses = $derived.by(() => {
    let list = courses;
    if (selectedDomain !== 'all') {
      list = list.filter((c) => {
        const d = (c.domain || '').toLowerCase();
        return d === selectedDomain.toLowerCase();
      });
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((c) => {
        const title = (c.title || c.name || '').toLowerCase();
        const domain = (c.domain || '').toLowerCase();
        const desc = (c.syllabus_context || c.description || '').toLowerCase();
        return title.includes(q) || domain.includes(q) || desc.includes(q);
      });
    }
    return list;
  });

  let totalPages = $derived(Math.max(1, Math.ceil(filteredCourses.length / pageSize)));
  let totalModules = $derived(courses.reduce((total, course) => total + (course.modules?.length || 0), 0));
  let totalAssignments = $derived(courses.reduce((total, course) => total + (course.assignments_count || 0), 0));

  let paginatedCourses = $derived.by(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCourses.slice(start, start + pageSize);
  });

  function setPage(p: number) {
    if (p >= 1 && p <= totalPages) {
      currentPage = p;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function setDomainFilter(dom: string) {
    selectedDomain = dom;
    currentPage = 1;
  }

  function onCourseCreated(newCourse: any) {
    courses = [newCourse, ...courses];
    currentPage = 1;
  }

  onMount(loadCourses);
</script>

<main class="courses-main">
  <!-- Page Header -->
  <div class="page-header">
    <div class="page-title-group">
      <h1 class="page-title">
        Course Portfolio &amp; Academic Grounding
        <span class="term-pill">Fall 2026 Semester</span>
      </h1>
      <p class="page-subtitle">
        See the development behind the final work. Manage sovereign course workspaces, bind foundational syllabi into Neo4j knowledge graphs, and sequence verified reasoning units.
      </p>
    </div>
    <div class="header-actions">
      <button type="button" class="btn btn-primary ai-studio-btn" onclick={() => push('/studio/course')}>
        ✨ Build Course with AI Studio
      </button>
      <button type="button" class="btn btn-secondary" onclick={() => (showIngestModal = true)}>
        📄 Ground course materials
      </button>
      <button type="button" class="btn btn-outline" onclick={() => (showCreateCourse = true)}>
        + Quick Create
      </button>
    </div>
  </div>

  <!-- Stats Ribbon -->
  <CourseStatsRibbon
    coursesCount={courses.length}
    {totalModules}
    {totalAssignments}
  />

  <!-- Search & Filter Controls -->
  <div class="controls-bar">
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input
        type="text"
        class="search-input"
        placeholder="Search courses by code, title, or keywords..."
        bind:value={searchQuery}
        oninput={() => (currentPage = 1)}
      />
      {#if searchQuery}
        <button type="button" class="clear-search" onclick={() => { searchQuery = ''; currentPage = 1; }}>✕</button>
      {/if}
    </div>

    <div class="filter-chips">
      <button
        type="button"
        class="filter-chip {selectedDomain === 'all' ? 'active' : ''}"
        onclick={() => setDomainFilter('all')}
      >
        All Domains ({courses.length})
      </button>
      <button
        type="button"
        class="filter-chip {selectedDomain === 'history' ? 'active' : ''}"
        onclick={() => setDomainFilter('history')}
      >
        History
      </button>
      <button
        type="button"
        class="filter-chip {selectedDomain === 'philosophy' ? 'active' : ''}"
        onclick={() => setDomainFilter('philosophy')}
      >
        Philosophy
      </button>
      <button
        type="button"
        class="filter-chip {selectedDomain === 'literature' ? 'active' : ''}"
        onclick={() => setDomainFilter('literature')}
      >
        Literature
      </button>
      <button
        type="button"
        class="filter-chip {selectedDomain === 'computer science' ? 'active' : ''}"
        onclick={() => setDomainFilter('computer science')}
      >
        Computer Science
      </button>
    </div>
  </div>

  <!-- Courses Grid -->
  <div>
    <div class="section-meta">
      <span>
        Showing {filteredCourses.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}–{Math.min(currentPage * pageSize, filteredCourses.length)} of {filteredCourses.length} courses
      </span>
      {#if searchQuery || selectedDomain !== 'all'}
        <span class="filter-indicator">
          Filtered by: {selectedDomain !== 'all' ? selectedDomain : ''} {searchQuery ? `"${searchQuery}"` : ''}
          <button type="button" class="reset-filter-btn" onclick={() => { searchQuery = ''; selectedDomain = 'all'; currentPage = 1; }}>Reset</button>
        </span>
      {/if}
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <span>Loading course portfolio...</span>
      </div>
    {:else if loadError}
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h3>Course data is unavailable</h3>
        <p>{loadError}</p>
        <button type="button" class="btn btn-secondary" onclick={loadCourses}>Retry loading courses</button>
      </div>
    {:else if paginatedCourses.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>No courses match your filter</h3>
        <p>Try refining your search query or reset the domain filter above.</p>
        <button type="button" class="btn btn-secondary" onclick={() => { searchQuery = ''; selectedDomain = 'all'; currentPage = 1; }}>
          Clear All Filters
        </button>
      </div>
    {:else}
      <div class="courses-grid">
        {#each paginatedCourses as course (course.course_id || course.code || course.name || course.title)}
          <CourseCardItem {course} />
        {/each}
      </div>

      <!-- Pagination Controls -->
      {#if totalPages > 1}
        <div class="pagination-bar">
          <button
            type="button"
            class="page-btn"
            disabled={currentPage === 1}
            onclick={() => setPage(currentPage - 1)}
          >
            ← Previous
          </button>

          <div class="page-numbers">
            {#each Array(totalPages) as _, i}
              {#if i + 1 === 1 || i + 1 === totalPages || (i + 1 >= currentPage - 1 && i + 1 <= currentPage + 1)}
                <button
                  type="button"
                  class="page-num {currentPage === i + 1 ? 'active' : ''}"
                  onclick={() => setPage(i + 1)}
                >
                  {i + 1}
                </button>
              {:else if (i + 1 === currentPage - 2 && currentPage > 3) || (i + 1 === currentPage + 2 && currentPage < totalPages - 2)}
                <span class="page-ellipsis">…</span>
              {/if}
            {/each}
          </div>

          <button
            type="button"
            class="page-btn"
            disabled={currentPage === totalPages}
            onclick={() => setPage(currentPage + 1)}
          >
            Next →
          </button>
        </div>
      {/if}
    {/if}
  </div>
</main>

<InstitutionalFooter variant="application" />

<CourseCreateModal
  isOpen={showCreateCourse}
  onClose={() => (showCreateCourse = false)}
  onCreated={onCourseCreated}
/>

<CourseIngestModal
  isOpen={showIngestModal}
  onClose={() => (showIngestModal = false)}
/>

<style>
  .courses-main {
    padding: 32px 40px 80px;
    max-width: 1440px;
    width: 100%;
    margin: 0 auto;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 24px;
    gap: 24px;
  }

  .page-title-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .page-title {
    font-family: var(--font-brand);
    font-size: 26px;
    font-weight: 700;
    color: var(--color-heading);
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
  }

  .term-pill {
    font-size: 11px;
    font-weight: 600;
    background: var(--pill-active-bg);
    border: 1px solid var(--pill-active-border);
    color: var(--color-horizon-bright);
    padding: 3px 10px;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .page-subtitle {
    font-size: 13.5px;
    color: var(--color-slate-light);
    margin: 0;
    max-width: 800px;
    line-height: 1.5;
  }

  .header-actions {
    display: flex;
    gap: 12px;
    flex-shrink: 0;
  }

  .controls-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 12px 16px;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 6px 12px;
    flex: 1;
    min-width: 260px;
    max-width: 460px;
  }

  .search-icon {
    font-size: 14px;
    color: var(--color-slate-muted);
  }

  .search-input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--color-slate-bright);
    font-size: 13px;
    font-family: var(--font-ui);
    width: 100%;
  }
  .search-input::placeholder {
    color: var(--color-slate-muted);
  }

  .clear-search {
    background: none;
    border: none;
    color: var(--color-slate-muted);
    cursor: pointer;
    font-size: 12px;
    padding: 2px 4px;
  }
  .clear-search:hover { color: var(--color-heading); }

  .filter-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .filter-chip {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-light);
    font-size: 12px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: var(--radius-full);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .filter-chip:hover {
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }
  .filter-chip.active {
    background: var(--pill-active-bg);
    border-color: var(--pill-active-border);
    color: var(--color-horizon-bright);
    font-weight: 600;
  }

  .section-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--color-slate-muted);
    margin-bottom: 16px;
    padding: 0 4px;
  }

  .filter-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .reset-filter-btn {
    background: none;
    border: none;
    color: var(--color-horizon-bright);
    font-size: 12px;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
  }

  .courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
  }

  .pagination-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    margin-top: 36px;
    padding: 16px 0;
  }

  .page-btn {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-light);
    font-size: 12.5px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .page-btn:hover:not(:disabled) {
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
    background: var(--color-graphite-hover);
  }
  .page-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .page-numbers {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .page-num {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-light);
    font-size: 12.5px;
    font-weight: 600;
    width: 34px;
    height: 34px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }
  .page-num:hover {
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }
  .page-num.active {
    background: var(--color-horizon-blue);
    border-color: var(--color-horizon-bright);
    color: #ffffff;
  }

  .page-ellipsis {
    color: var(--color-slate-muted);
    padding: 0 4px;
    font-size: 12px;
  }

  .loading-state, .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-height: 240px;
    color: var(--color-slate-light);
    font-size: 14px;
    background: var(--color-graphite);
    border: 1px dashed var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 40px;
    text-align: center;
  }

  .empty-icon {
    font-size: 32px;
  }
  .empty-state h3 {
    margin: 0;
    color: var(--color-heading);
    font-family: var(--font-brand);
  }
  .empty-state p {
    margin: 0;
    color: var(--color-slate-muted);
    font-size: 13px;
  }

  .loading-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(59, 130, 246, 0.2);
    border-top-color: var(--color-horizon-bright);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
