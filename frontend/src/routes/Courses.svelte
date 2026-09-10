<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import Modal from '../lib/Modal.svelte';

  let courses = $state([]);
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
  let isCreating = $state(false);
  let createFeedback = $state('');

  // Form fields
  let newCourseCode = $state('');
  let newCourseTitle = $state('');
  let newCourseDomain = $state('History');
  let newCourseInstructor = $state('Dr. Vance');
  let newCourseSyllabus = $state('');

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

  function setPage(p) {
    if (p >= 1 && p <= totalPages) {
      currentPage = p;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function setDomainFilter(dom) {
    selectedDomain = dom;
    currentPage = 1;
  }

  function courseIdentity(course) {
    const title = course.title || course.name || 'Untitled course';
    const match = title.match(/^([A-Za-z]{2,10}-\d{1,4}[A-Za-z]?)\s*:\s*(.+)$/);
    return match ? { code: match[1], title: match[2] } : { code: null, title };
  }

  async function handleCreateCourse(e) {
    e.preventDefault();
    if (!newCourseTitle.trim()) return;
    isCreating = true;
    createFeedback = '';
    try {
      const res = await fetch('/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newCourseCode.trim() ? `${newCourseCode.trim()}: ${newCourseTitle.trim()}` : newCourseTitle.trim(),
          domain: newCourseDomain,
          created_by: newCourseInstructor.trim() || 'Dr. Vance',
          syllabus_context: newCourseSyllabus.trim() || null,
        }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const newCourse = await res.json();
      courses = [newCourse, ...courses];
      showCreateCourse = false;
      newCourseCode = '';
      newCourseTitle = '';
      newCourseSyllabus = '';
      currentPage = 1;
    } catch (err) {
      createFeedback = 'Failed: ' + err.message;
    } finally {
      isCreating = false;
    }
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
        Manage sovereign course workspaces, bind foundational syllabi into Neo4j knowledge graphs, and sequence verified reasoning units.
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
  <div class="stats-ribbon">
    <div class="stat-card">
      <div class="stat-label"><span>Active Workspaces</span><span>📚</span></div>
      <div class="stat-value-row">
        <span class="stat-value">{courses.length}</span>
        <span class="stat-trend neutral">Live Synced</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label"><span>Curriculum Modules</span><span>🗺️</span></div>
      <div class="stat-value-row">
        <span class="stat-value">{totalModules}</span>
        <span class="stat-trend neutral">Live course data</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label"><span>Assignment Drafts</span><span>⚡</span></div>
      <div class="stat-value-row">
        <span class="stat-value">{totalAssignments}</span>
        <span class="stat-trend neutral">Live course data</span>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-label"><span>Student Activity</span><span>🎯</span></div>
      <div class="stat-value-row">
        <span class="stat-value">—</span>
        <span class="stat-trend neutral">Available by course</span>
      </div>
    </div>
  </div>

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
      <div class="empty-state"><div class="empty-icon">⚠️</div><h3>Course data is unavailable</h3><p>{loadError}</p><button type="button" class="btn btn-secondary" onclick={loadCourses}>Retry loading courses</button></div>
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
        {#each paginatedCourses as course (course.course_id || course.code || course.name)}
          {@const identity = courseIdentity(course)}
          <div class="course-card">
            <div class="course-card-top">
              <div>
                <span class="course-code-badge">{identity.code || (course.domain || 'ACADEMIC').toUpperCase()} • WORKSPACE</span>
                <h3 class="course-name">{identity.title}</h3>
              </div>
              <span class="grounding-pill"><span>●</span> Course workspace</span>
            </div>

            <p class="course-desc">
              {course.syllabus_context || course.description || 'Curriculum workspace initialized. Ready for syllabus ingestion and prerequisite module sequencing.'}
            </p>

            <div class="course-metrics">
              <div class="metric-item">
                <span class="metric-val">{course.modules?.length ?? course.modules ?? 0}</span>
                <span class="metric-sub">Modules</span>
              </div>
              <div class="metric-item">
                <span class="metric-val">{course.assignments_count ?? course.assignments ?? 0}</span>
                <span class="metric-sub">Assignments</span>
              </div>
              <div class="metric-item">
                <span class="metric-val" style="color: var(--color-signal-green);">0%</span>
                <span class="metric-sub">Leakage</span>
              </div>
            </div>

            <div class="card-footer">
              <span class="last-active">
                Instructor: <strong>{course.created_by || 'Dr. Vance'}</strong>
              </span>
              <button
                type="button"
                class="course-link"
                onclick={() => push('/modules' + (course.course_id ? '?course_id=' + course.course_id : ''))}
              >
                Enter Curriculum &amp; Modules →
              </button>
            </div>
          </div>
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

<!-- Create Course Modal -->
<Modal isOpen={showCreateCourse} title="🏛️ Create New Course Workspace" onClose={() => (showCreateCourse = false)}>
  <p class="modal-desc">Set a clear course identity and teaching context. You can then create modules, attach source material, and test a student-safe assignment before publication.</p>
  <form onsubmit={handleCreateCourse} class="create-form">
    <div class="form-row">
      <div class="form-field">
        <label for="newCourseCode" class="field-label">Course Code</label>
        <input id="newCourseCode" type="text" class="field-input" placeholder="e.g. HIST-302" bind:value={newCourseCode} />
      </div>
      <div class="form-field">
        <label for="newCourseTitle" class="field-label">Course Title <span class="req">*</span></label>
        <input id="newCourseTitle" type="text" class="field-input" placeholder="e.g. Revolutions in the Atlantic World" bind:value={newCourseTitle} required />
      </div>
    </div>
    <div class="form-row">
      <div class="form-field">
        <label for="newCourseDomain" class="field-label">Academic Domain <span class="req">*</span></label>
        <select id="newCourseDomain" class="field-input" bind:value={newCourseDomain}>
          <option>History</option>
          <option>Philosophy</option>
          <option>Computer Science</option>
          <option>Physics</option>
          <option>Economics</option>
          <option>Literature</option>
        </select>
      </div>
      <div class="form-field">
        <label for="newCourseInstructor" class="field-label">Lead Instructor</label>
        <input id="newCourseInstructor" type="text" class="field-input" bind:value={newCourseInstructor} />
      </div>
    </div>
    <div class="form-field">
      <label for="newCourseSyllabus" class="field-label">Introductory Syllabus Context (Optional)</label>
      <textarea id="newCourseSyllabus" class="field-input" rows="3" bind:value={newCourseSyllabus} placeholder="Key topics, preliminary reading units..."></textarea>
    </div>
    {#if createFeedback}<div class="feedback-error">{createFeedback}</div>{/if}
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" onclick={() => (showCreateCourse = false)}>Cancel</button>
      <button type="submit" class="btn btn-primary" disabled={isCreating}>
        {isCreating ? 'Creating Workspace...' : '+ Create Course Workspace'}
      </button>
    </div>
  </form>
</Modal>

<!-- Ingest Syllabus Modal -->
<Modal isOpen={showIngestModal} title="📄 Ground course materials" onClose={() => (showIngestModal = false)}>
  <p class="modal-desc">Materials must be attached to a curriculum module so their provenance is visible in assignment design. Create or open a course, add a module, and use <strong>Ingest Material</strong> from that module.</p>
  <div class="pipeline-preview">
    <div class="pipeline-title">What grounding records</div>
    <div class="pipeline-step"><span>1. The selected course and module</span><span class="step-ok">Required</span></div>
    <div class="pipeline-step"><span>2. Source title, excerpt, and link when supplied</span><span class="step-ok">Visible to educators</span></div>
    <div class="pipeline-step"><span>3. Knowledge-component mapping when available</span><span class="step-ok">Reviewable</span></div>
  </div>
  <div class="modal-footer">
    <button type="button" class="btn btn-secondary" onclick={() => (showIngestModal = false)}>Cancel</button>
    <a href="#/modules" class="btn btn-primary" onclick={() => (showIngestModal = false)}>Open curriculum</a>
  </div>
</Modal>

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

  .stats-ribbon {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  .stat-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: border-color 0.2s, transform 0.2s;
  }

  .stat-card:hover {
    border-color: var(--color-slate-subtle);
    transform: translateY(-2px);
  }

  .stat-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .stat-value-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  .stat-value {
    font-family: var(--font-brand);
    font-size: 28px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .stat-trend {
    font-size: 11px;
    font-weight: 600;
  }
  .stat-trend.neutral { color: var(--color-slate-light); }

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
    background: var(--color-obsidian);
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
    background: var(--color-obsidian);
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

  .course-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }
  .course-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--color-horizon-blue), var(--color-aurora));
    opacity: 0.8;
  }
  .course-card:hover {
    border-color: var(--color-horizon-blue);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .course-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .course-code-badge {
    font-size: 10.5px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: var(--radius-xs);
    background: var(--pill-bg);
    color: var(--color-slate-bright);
    letter-spacing: 0.5px;
  }

  .course-name {
    font-family: var(--font-brand);
    font-size: 17px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 6px 0 0;
    line-height: 1.35;
  }

  .course-desc {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.55;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 58px;
  }

  .grounding-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: var(--radius-full);
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--color-signal-green);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .course-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    padding: 10px 12px;
    background: var(--color-graphite-card);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    text-align: center;
    gap: 8px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .metric-val {
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .metric-sub {
    font-size: 10px;
    color: var(--color-slate-muted);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 14px;
    margin-top: auto;
  }

  .last-active {
    font-size: 11.5px;
    color: var(--color-slate-muted);
  }
  .last-active strong {
    color: var(--color-slate-bright);
  }

  .course-link {
    background: none;
    border: none;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-horizon-bright);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: gap 0.15s, color 0.15s;
    padding: 0;
  }
  .course-link:hover {
    gap: 9px;
    color: var(--color-heading);
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

  .modal-desc {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.5;
    margin: 0 0 20px;
  }

  .create-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }

  .field-label {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-light);
    letter-spacing: 0.4px;
  }

  .req {
    color: var(--color-rose);
  }

  .field-input {
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    color: var(--color-slate-bright);
    padding: 10px 14px;
    border-radius: var(--radius-sm);
    font-size: 13.5px;
    font-family: var(--font-ui);
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.15s;
  }
  .field-input:focus {
    outline: none;
    border-color: var(--input-focus-border);
  }

  textarea.field-input {
    resize: vertical;
  }

  .feedback-error {
    font-size: 12px;
    padding: 8px 12px;
    border-radius: var(--radius-xs);
    background: var(--color-rose-bg);
    color: var(--color-rose-text);
    border: 1px solid var(--color-rose);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 16px;
  }

  .pipeline-preview {
    background: var(--pill-bg);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 14px;
    font-size: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }
  .pipeline-title {
    font-weight: 600;
    color: var(--color-heading);
  }
  .pipeline-step {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--color-slate-light);
  }
  .step-ok {
    color: var(--color-signal-green);
  }
</style>
