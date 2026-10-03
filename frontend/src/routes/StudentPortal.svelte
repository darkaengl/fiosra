<script>
  import { onMount } from 'svelte';
  import { getStudentId } from '../lib/session.js';
  import InstitutionalFooter from '../lib/InstitutionalFooter.svelte';

  let enrolledCourses = $state([]);
  let availableCourses = $state([]);
  let isLoading = $state(true);
  let enrollingId = $state('');
  let droppingId = $state('');
  let studentId = '';
  let searchQuery = $state('');
  let selectedCategory = $state('all');

  onMount(async () => {
    studentId = getStudentId();
    await loadCourses();
  });

  async function loadCourses() {
    isLoading = true;
    try {
      const catalogRes = await fetch(`/courses/student-catalog?student_id=${encodeURIComponent(studentId)}`);
      if (!catalogRes.ok) throw new Error('Course availability could not be restored.');
      const catalog = await catalogRes.json();

      enrolledCourses = catalog.filter((course) => course.is_enrolled);
      availableCourses = catalog.filter((course) => !course.is_enrolled);
    } catch (err) {
      console.error('Failed to fetch courses:', err);
    } finally {
      isLoading = false;
    }
  }

  async function enrollInCourse(courseId) {
    enrollingId = courseId;
    try {
      const res = await fetch(`/courses/${courseId}/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId }),
      });
      if (res.ok) {
        await loadCourses();
      } else {
        const err = await res.json().catch(() => ({}));
        console.error('Enrollment failed:', err.detail || 'Unknown error');
      }
    } catch (err) {
      console.error('Enrollment request failed:', err);
    } finally {
      enrollingId = '';
    }
  }

  async function dropCourse(courseId) {
    droppingId = courseId;
    try {
      const res = await fetch(`/courses/${courseId}/enroll/${encodeURIComponent(studentId)}`, {
        method: 'DELETE',
      });
      if (res.ok || res.status === 204) {
        await loadCourses();
      } else {
        const err = await res.json().catch(() => ({}));
        console.error('Drop failed:', err.detail || 'Unknown error');
      }
    } catch (err) {
      console.error('Drop request failed:', err);
    } finally {
      droppingId = '';
    }
  }

  function getFirstAssignment(course) {
    if (!course) return null;
    if (course.active_assignment) return course.active_assignment;
    if (course.modules) {
      for (const mod of course.modules) {
        if (mod.assignments && mod.assignments.length > 0) {
          const published = mod.assignments.find((a) => a.status === 'published');
          if (published) return published;
        }
      }
    }
    return null;
  }

  // Filtered available courses with search & category support
  let filteredAvailableCourses = $derived(
    availableCourses.filter((course) => {
      const query = searchQuery.trim().toLowerCase();
      const titleMatch = course.title?.toLowerCase().includes(query);
      const domainMatch = course.domain?.toLowerCase().includes(query);
      const instructorMatch = course.created_by?.toLowerCase().includes(query);
      const synopsisMatch = course.syllabus_context?.toLowerCase().includes(query);
      const matchesSearch = !query || titleMatch || domainMatch || instructorMatch || synopsisMatch;

      const domain = (course.domain || '').toLowerCase();
      let matchesCat = true;
      if (selectedCategory === 'business') {
        matchesCat = domain.includes('business') || domain.includes('marketing') || domain.includes('econ');
      } else if (selectedCategory === 'humanities') {
        matchesCat = domain.includes('history') || domain.includes('humanities') || domain.includes('literature') || domain.includes('philosophy');
      } else if (selectedCategory === 'sciences') {
        matchesCat = domain.includes('science') || domain.includes('physics') || domain.includes('biology') || domain.includes('chemistry');
      }

      return matchesSearch && matchesCat;
    })
  );

  let categoryCounts = $derived({
    all: availableCourses.length,
    business: availableCourses.filter((c) => (c.domain || '').toLowerCase().includes('business') || (c.domain || '').toLowerCase().includes('marketing')).length,
    humanities: availableCourses.filter((c) => (c.domain || '').toLowerCase().includes('history') || (c.domain || '').toLowerCase().includes('humanities')).length,
    sciences: availableCourses.filter((c) => (c.domain || '').toLowerCase().includes('physics') || (c.domain || '').toLowerCase().includes('bio') || (c.domain || '').toLowerCase().includes('science')).length,
  });
</script>

<div class="portal-page">
  <main class="portal-main">

    <!-- Clean, Calm Dashboard Header -->
    <header class="portal-header">
      <div class="portal-header-left">
        <h1 class="portal-title">Courses &amp; Milestones</h1>
        <p class="portal-subtitle">Continue your active reasoning investigations or explore available courses.</p>
      </div>
      <div class="term-badge">
        <span class="term-dot"></span>
        Fall 2026 Term
      </div>
    </header>

    <!-- SECTION 1: ENROLLED COURSES (Clean, Full-Width Focus) -->
    <section class="enrolled-section">
      <div class="section-heading-row">
        <div class="section-title-wrap">
          <h2 class="section-title">Active Enrollments</h2>
          <span class="count-pill">{enrolledCourses.length}</span>
        </div>
      </div>

      <div class="enrolled-stack">
        {#if isLoading}
          <div class="student-course-card skeleton-card">
            <div style="height: 16px; width: 100px; background: #e2e8f0; border-radius: 4px;"></div>
            <div style="height: 22px; width: 70%; background: #e2e8f0; border-radius: 4px; margin-top: 8px;"></div>
            <div style="height: 50px; width: 100%; background: #e2e8f0; border-radius: 6px; margin-top: 12px;"></div>
          </div>
        {:else if enrolledCourses.length > 0}
          {#each enrolledCourses as c (c.course_id)}
            {@const firstAssign = getFirstAssignment(c)}
            {@const mods = c.modules || []}
            {@const totalAssigns = mods.reduce((sum, m) => sum + (m.assignments ? m.assignments.length : 0), 0) || c.assignments_count || 1}

            <div class="student-course-card enrolled-card">
              <!-- Course Header -->
              <div class="card-header-row">
                <div class="card-headings">
                  <div class="meta-strip">
                    <span class="domain-tag">{c.domain || 'Business & Management'}</span>
                    <span class="status-tag active">
                      <span class="status-dot"></span>
                      Enrolled
                    </span>
                  </div>
                  <h3 class="course-name">{c.title}</h3>
                  <div class="course-meta">
                    Faculty: <strong>{c.created_by || 'Prof. Somerville'}</strong>
                    <span class="meta-sep">•</span>
                    <span>{mods.length} Modules</span>
                    <span class="meta-sep">•</span>
                    <span>{totalAssigns} Assignments</span>
                  </div>
                </div>
              </div>

              <!-- Sleek Next Milestone Strip -->
              <div class="milestone-strip">
                <div class="milestone-badge-col">
                  <span class="milestone-badge">Next Milestone</span>
                </div>
                <div class="milestone-content">
                  <div class="milestone-title">
                    {firstAssign ? firstAssign.title : 'Primary Source Inquiries & Epistemic Reasoning'}
                  </div>
                  <div class="milestone-sub">
                    Module 1 · 5 Rubric Criteria · ~400 Words Target
                  </div>
                </div>
              </div>

              <!-- Clean Actions Row -->
              <div class="card-footer">
                <div class="card-footer-left">
                  <a
                    href={firstAssign ? `#/student?course_id=${c.course_id}&assignment_id=${firstAssign.assignment_id}` : `#/student/home?course_id=${c.course_id}`}
                    class="btn-primary"
                  >
                    Resume Reasoning Canvas →
                  </a>
                  <a href="#/student/home?course_id={c.course_id}" class="link-outline">
                    Course Outline
                  </a>
                </div>
                <button
                  class="btn-drop"
                  onclick={() => dropCourse(c.course_id)}
                  disabled={droppingId === c.course_id}
                >
                  {droppingId === c.course_id ? 'Dropping...' : 'Drop'}
                </button>
              </div>
            </div>
          {/each}
        {:else}
          <div class="empty-state-card">
            <div class="empty-symbol">📭</div>
            <h3 class="empty-title">No Active Enrollments</h3>
            <p class="empty-desc">You are not currently enrolled in any courses. Browse the catalog below to enroll.</p>
          </div>
        {/if}
      </div>
    </section>

    <!-- SECTION 2: ACADEMIC CATALOG & ENROLLMENT -->
    <section class="catalog-section">
      <div class="catalog-header-bar">
        <div class="section-title-wrap">
          <h2 class="section-title">Course Catalog</h2>
          <span class="count-pill">{filteredAvailableCourses.length} Available</span>
        </div>

        <!-- Sleek Search Input -->
        <div class="search-box">
          <svg class="search-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            placeholder="Search catalog by title, faculty, topic..."
            bind:value={searchQuery}
            class="search-input"
          />
          {#if searchQuery}
            <button class="clear-btn" onclick={() => (searchQuery = '')} aria-label="Clear search">✕</button>
          {/if}
        </div>
      </div>

      <!-- Category Filter Tabs -->
      <div class="category-tabs-bar">
        <button
          type="button"
          class="cat-tab"
          class:active={selectedCategory === 'all'}
          onclick={() => (selectedCategory = 'all')}
        >
          All Subjects <span class="tab-count">{categoryCounts.all}</span>
        </button>
        <button
          type="button"
          class="cat-tab"
          class:active={selectedCategory === 'business'}
          onclick={() => (selectedCategory = 'business')}
        >
          Business &amp; Management <span class="tab-count">{categoryCounts.business}</span>
        </button>
        <button
          type="button"
          class="cat-tab"
          class:active={selectedCategory === 'humanities'}
          onclick={() => (selectedCategory = 'humanities')}
        >
          History &amp; Humanities <span class="tab-count">{categoryCounts.humanities}</span>
        </button>
        <button
          type="button"
          class="cat-tab"
          class:active={selectedCategory === 'sciences'}
          onclick={() => (selectedCategory = 'sciences')}
        >
          Sciences &amp; Physics <span class="tab-count">{categoryCounts.sciences}</span>
        </button>
      </div>

      <!-- Filtered Available Courses Grid -->
      <div class="catalog-grid">
        {#if isLoading}
          <div class="student-course-card skeleton-card">
            <div style="height: 16px; width: 80px; background: #e2e8f0; border-radius: 4px;"></div>
            <div style="height: 22px; width: 60%; background: #e2e8f0; border-radius: 4px; margin-top: 8px;"></div>
          </div>
        {:else if filteredAvailableCourses.length > 0}
          {#each filteredAvailableCourses as c (c.course_id)}
            <div class="student-course-card available-card">
              <div class="card-header-row">
                <div class="card-headings">
                  <div class="meta-strip">
                    <span class="domain-tag">{c.domain || 'Academic'}</span>
                    <span class="status-tag open">Open</span>
                  </div>
                  <h3 class="course-name">{c.title}</h3>
                </div>
              </div>

              <div class="course-meta">
                Faculty: <strong>{c.created_by || 'Faculty'}</strong>
                <span class="meta-sep">•</span>
                <span>{c.modules ? c.modules.length : 0} Modules</span>
                <span class="meta-sep">•</span>
                <span>{c.assignments_count || 0} Tasks</span>
              </div>

              {#if c.syllabus_context}
                <p class="course-synopsis">
                  {c.syllabus_context.slice(0, 130)}{c.syllabus_context.length > 130 ? '...' : ''}
                </p>
              {:else}
                <p class="course-synopsis">
                  Structured curriculum with primary evidence grounding, epistemic inquiry scaffolds, and assessment rubrics.
                </p>
              {/if}

              <div class="catalog-card-footer">
                <span class="term-lbl">Fall 2026</span>
                <button
                  class="btn-enroll"
                  onclick={() => enrollInCourse(c.course_id)}
                  disabled={enrollingId === c.course_id}
                >
                  {enrollingId === c.course_id ? 'Enrolling...' : 'Enroll in Course →'}
                </button>
              </div>
            </div>
          {/each}
        {:else}
          <div class="empty-state-card full-width">
            <div class="empty-symbol">🔍</div>
            <h3 class="empty-title">No Matching Courses Found</h3>
            <p class="empty-desc">
              {searchQuery ? `No courses matching "${searchQuery}".` : 'No courses currently available in this category.'}
            </p>
          </div>
        {/if}
      </div>
    </section>

  </main>
  <InstitutionalFooter variant="application" />
</div>

<style>
  .portal-page {
    background-color: var(--color-bone, #F6F5F1);
    min-height: calc(100vh - 56px);
    color: var(--color-heading, #111315);
    font-family: var(--font-body, system-ui, sans-serif);
  }

  .portal-main {
    max-width: 1040px;
    margin: 0 auto;
    padding: 32px 24px 72px 24px;
    display: flex;
    flex-direction: column;
    gap: 36px;
  }

  /* Clean, Uncluttered Page Header */
  .portal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
    flex-wrap: wrap;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border, #DDDCD5);
  }

  .portal-header-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .portal-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
    letter-spacing: -0.02em;
  }

  .portal-subtitle {
    font-size: 13.5px;
    color: var(--color-slate, #6D7378);
    margin: 0;
  }

  .term-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: var(--color-slate, #6D7378);
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    padding: 5px 12px;
    border-radius: 999px;
  }

  .term-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-signal-green, #5FAF7A);
  }

  /* Enrolled Courses Section */
  .enrolled-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .section-heading-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .section-title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .count-pill {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate, #6D7378);
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    padding: 1px 7px;
    border-radius: 999px;
  }

  .enrolled-stack {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* Clean Enrolled & Available Course Cards */
  .student-course-card {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    padding: 22px 26px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  }

  .student-course-card:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    border-color: #cbc9c2;
  }

  .card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .card-headings {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
  }

  .meta-strip {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .domain-tag {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-horizon-blue, #4F6BFF);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .status-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .status-tag.active {
    background: var(--color-signal-green-bg, #EBF7F0);
    color: var(--color-signal-green-text, #2D6340);
  }

  .status-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--color-signal-green, #5FAF7A);
  }

  .status-tag.open {
    background: var(--color-cloud-subtle, #F0EFEA);
    color: var(--color-slate, #6D7378);
  }

  .course-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
    line-height: 1.35;
  }

  .course-meta {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
  }

  .meta-sep {
    margin: 0 6px;
    color: var(--border, #DDDCD5);
  }

  /* Sleek Next Milestone Strip */
  .milestone-strip {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .milestone-badge-col {
    flex-shrink: 0;
  }

  .milestone-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-horizon-blue, #4F6BFF);
    background: var(--surface, #ffffff);
    border: 1px solid rgba(79, 107, 255, 0.2);
    padding: 3px 9px;
    border-radius: 4px;
  }

  .milestone-content {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .milestone-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-heading, #111315);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .milestone-sub {
    font-size: 12px;
    color: var(--color-slate, #6D7378);
  }

  /* Card Action Footer */
  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    border-top: 1px solid var(--color-cloud-subtle, #F0EFEA);
    gap: 12px;
    flex-wrap: wrap;
  }

  .card-footer-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .btn-primary {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease;
    white-space: nowrap;
    border: 1px solid rgba(61, 90, 254, 0.2);
  }

  .btn-primary:hover {
    background: var(--color-horizon-bright, #3D5AFE);
    box-shadow: 0 2px 8px rgba(79, 107, 255, 0.25);
  }

  .link-outline {
    font-size: 12.5px;
    font-weight: 500;
    color: var(--color-slate, #6D7378);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .link-outline:hover {
    color: var(--color-heading, #111315);
    text-decoration: underline;
  }

  .btn-drop {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-slate-subtle, #8A9096);
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px 6px;
    transition: color 0.15s ease;
  }

  .btn-drop:hover {
    color: var(--color-rose, #B74C4C);
  }

  /* Catalog Section */
  .catalog-section {
    border-top: 1px solid var(--border, #DDDCD5);
    padding-top: 32px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .catalog-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 7px 14px;
    min-width: 300px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    transition: border-color 0.15s ease;
  }

  .search-box:focus-within {
    border-color: var(--color-horizon-blue, #4F6BFF);
    box-shadow: 0 0 0 2px rgba(79, 107, 255, 0.12);
  }

  .search-svg {
    color: var(--color-slate-subtle, #8A9096);
    flex-shrink: 0;
  }

  .search-input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 13px;
    color: var(--color-heading, #111315);
    width: 100%;
  }

  .clear-btn {
    background: none;
    border: none;
    color: var(--color-slate-subtle, #8A9096);
    font-size: 11px;
    cursor: pointer;
    padding: 0;
  }

  .category-tabs-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .cat-tab {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    color: var(--color-slate, #6D7378);
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .cat-tab:hover {
    border-color: var(--color-horizon-blue, #4F6BFF);
    color: var(--color-heading, #111315);
  }

  .cat-tab.active {
    background: var(--color-heading, #111315);
    color: #ffffff;
    border-color: var(--color-heading, #111315);
  }

  .tab-count {
    font-size: 11px;
    opacity: 0.75;
  }

  .catalog-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 18px;
  }

  .available-card {
    border-top: 2px solid transparent;
  }

  .available-card:hover {
    border-top-color: var(--color-horizon-blue, #4F6BFF);
  }

  .course-synopsis {
    font-size: 12.5px;
    color: var(--color-slate, #6D7378);
    line-height: 1.5;
    margin: 0;
  }

  .catalog-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
    padding-top: 14px;
    border-top: 1px solid var(--color-cloud-subtle, #F0EFEA);
  }

  .term-lbl {
    font-size: 12px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .btn-enroll {
    background: var(--surface, #ffffff);
    color: var(--color-horizon-blue, #4F6BFF);
    border: 1px solid rgba(79, 107, 255, 0.3);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-enroll:hover {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
  }

  /* Empty state */
  .empty-state-card {
    background: var(--surface, #ffffff);
    border: 1px dashed var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 32px 20px;
    text-align: center;
    color: var(--color-slate, #6D7378);
  }

  .empty-state-card.full-width {
    grid-column: 1 / -1;
  }

  .empty-symbol {
    font-size: 26px;
    margin-bottom: 6px;
  }

  .empty-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0 0 4px 0;
  }

  .empty-desc {
    font-size: 12.5px;
    margin: 0;
  }
</style>
