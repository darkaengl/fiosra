<script lang="ts">
  import { onMount } from 'svelte';
  import { getStudentId, routeParams } from '../lib/session.js';
  import StudentCourseHero from '../lib/student/StudentCourseHero.svelte';
  import StudentModuleAccordion from '../lib/student/StudentModuleAccordion.svelte';
  import StudentCompetenciesSection from '../lib/student/StudentCompetenciesSection.svelte';

  let courseId = $state('');
  let currentCourse = $state<any>(null);
  let activeAssignment = $state<any>(null);
  let isLoading = $state(true);
  let isEnrolled = $state(true);
  let enrollBusy = $state(false);
  let studentId = '';

  let modules = $derived(currentCourse?.modules || []);
  let totalAssignments = $derived(
    modules.reduce((acc: number, m: any) => acc + (m.assignments ? m.assignments.length : 0), 0)
  );

  async function checkEnrollment() {
    if (!courseId || !studentId) return;
    try {
      const res = await fetch(`/courses/enrolled?student_id=${encodeURIComponent(studentId)}`);
      if (res.ok) {
        const enrolled = await res.json();
        isEnrolled = enrolled.some((c: any) => c.course_id === courseId);
      }
    } catch {
      isEnrolled = true;
    }
  }

  async function enrollAndReload() {
    enrollBusy = true;
    try {
      const res = await fetch(`/courses/${courseId}/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId }),
      });
      if (res.ok) {
        isEnrolled = true;
        await loadCourseData();
      }
    } catch (err) {
      console.error('Enrollment failed:', err);
    } finally {
      enrollBusy = false;
    }
  }

  async function loadCourseData() {
    isLoading = true;
    try {
      const catalogRes = await fetch(`/courses/student-catalog?student_id=${encodeURIComponent(studentId)}`);
      let catalogItem: any = null;
      if (catalogRes.ok) {
        const catalog = await catalogRes.json();
        catalogItem = courseId
          ? catalog.find((c: any) => c.course_id === courseId || c.id === courseId) || null
          : catalog.find((c: any) => c.is_enrolled && c.is_available) || catalog[0] || null;
      }

      if (catalogItem) {
        courseId = catalogItem.course_id || catalogItem.id || '';
        isEnrolled = Boolean(catalogItem.is_enrolled);
        activeAssignment = catalogItem.active_assignment || null;
      }

      if (courseId) {
        const courseRes = await fetch(`/courses/${courseId}`);
        if (courseRes.ok) {
          const fullCourse = await courseRes.json();
          currentCourse = {
            ...fullCourse,
            is_enrolled: isEnrolled,
            active_assignment: activeAssignment,
          };
        } else if (catalogItem) {
          currentCourse = catalogItem;
        }
      }
    } catch (err) {
      console.error('Failed to load course details for student home:', err);
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    studentId = getStudentId();
    await loadCourseData();
  });

  function getCleanSummary(promptText?: string) {
    if (!promptText) return 'Synthesize evidence and evaluate reasoning using assigned primary sources and rubric criteria.';
    const lines = promptText.split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
    return lines[0] || 'Analyze the strategic business scenario and evaluate core marketing frameworks.';
  }
</script>

<div class="home-page">
  <main class="home-container">
    {#if !isLoading && !isEnrolled}
      <!-- Enrollment Guard -->
      <div class="enrollment-guard">
        <div class="guard-icon">🔒</div>
        <h2 class="guard-title">You are not enrolled in this course</h2>
        <p class="guard-desc">
          You need to enroll in <strong>{currentCourse?.title || 'this course'}</strong> before you can access its modules, primary sources, and reasoning assignments.
        </p>
        <div style="display: flex; gap: 12px; align-items: center;">
          <button class="btn btn-primary" onclick={enrollAndReload} disabled={enrollBusy} style="padding: 10px 24px;">
            {enrollBusy ? 'Enrolling...' : 'Enroll Now →'}
          </button>
          <a href="#/student/portal" class="link-subtle" style="font-size: 13px;">← Back to Courses</a>
        </div>
      </div>
    {:else if isLoading}
      <!-- Loading Skeleton -->
      <div class="skeleton-header">
        <div style="height: 18px; width: 140px; background: var(--pill-bg, #f1f5f9); border-radius: 4px;"></div>
        <div style="height: 32px; width: 60%; background: var(--pill-bg, #f1f5f9); border-radius: 6px; margin-top: 10px;"></div>
        <div style="height: 14px; width: 40%; background: var(--pill-bg, #f1f5f9); border-radius: 4px; margin-top: 8px;"></div>
      </div>
    {:else}
      <!-- Course Hero & Active Milestone Focus -->
      <StudentCourseHero
        {courseId}
        {currentCourse}
        {activeAssignment}
        modulesCount={modules.length}
        {totalAssignments}
        {getCleanSummary}
      />

      <!-- Curriculum Roadmap & All Modules Accordion -->
      <StudentModuleAccordion
        {courseId}
        {modules}
        {activeAssignment}
      />

      <!-- Course Core Competencies -->
      <StudentCompetenciesSection {modules} />
    {/if}
  </main>
</div>

<style>
  .home-page {
    background-color: var(--color-bone, #F6F5F1);
    min-height: calc(100vh - 56px);
    color: var(--color-heading, #111315);
    font-family: var(--font-body, system-ui, sans-serif);
  }

  .home-container {
    max-width: 1040px;
    margin: 0 auto;
    padding: 28px 24px 70px 24px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  .enrollment-guard {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    padding: 48px 32px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    max-width: 580px;
    margin: 40px auto;
  }

  .guard-icon {
    font-size: 40px;
  }

  .guard-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
  }

  .guard-desc {
    font-size: 14px;
    color: var(--color-slate, #6D7378);
    line-height: 1.5;
    margin: 0;
  }

  .skeleton-header {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 10px;
    padding: 24px;
  }

  .btn {
    font-size: 13px;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: 6px;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-primary {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
    border: none;
  }
  .btn-primary:hover {
    background: #3B57E8;
  }

  .link-subtle {
    color: var(--color-slate, #6D7378);
    text-decoration: none;
  }
  .link-subtle:hover {
    text-decoration: underline;
  }
</style>
