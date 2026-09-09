<script>
  import { onMount } from 'svelte';

  let {
    courseTitle = 'Course Workspace',
  } = $props();

  let currentHash = $state(typeof window !== 'undefined' ? window.location.hash || '#/' : '#/');
  let courses = $state([]);

  function handleHashChange() {
    currentHash = window.location.hash || '#/';
  }

  onMount(async () => {
    window.addEventListener('hashchange', handleHashChange);

    try {
      const res = await fetch('/api/v1/lms/courses');
      if (res.ok) {
        const data = await res.json();
        courses = data.courses || data || [];
      }
    } catch {
      // ignore network errors
    }

    return () => window.removeEventListener('hashchange', handleHashChange);
  });

  let parsed = $derived.by(() => {
    const raw = currentHash.replace(/^#/, '');
    const [pathWithSlash, qs] = raw.split('?');
    const path = pathWithSlash ? (pathWithSlash.startsWith('/') ? pathWithSlash : '/' + pathWithSlash) : '/';
    const searchParams = new URLSearchParams(qs || (typeof window !== 'undefined' ? window.location.search : ''));
    const courseId = searchParams.get('course_id') || '';
    const courseQuery = courseId ? `?course_id=${encodeURIComponent(courseId)}` : '';

    let activeTab = 'modules';
    let isStudentView = false;

    if (path.startsWith('/courses')) {
      activeTab = 'courses';
    } else if (path.startsWith('/designer')) {
      activeTab = 'designer';
    } else if (path.startsWith('/review')) {
      activeTab = 'review';
    } else if (path.startsWith('/diagnostics')) {
      activeTab = 'diagnostics';
    } else if (path.startsWith('/graph')) {
      activeTab = 'graph';
    } else if (path.startsWith('/student')) {
      isStudentView = true;
      if (path.startsWith('/student/portal')) activeTab = 'student-portal';
      else if (path.startsWith('/student/home')) activeTab = 'student-home';
      else if (path.startsWith('/student/trace')) activeTab = 'student-trace';
      else activeTab = 'student-canvas';
    } else {
      activeTab = 'modules';
    }

    const isOnCourses = activeTab === 'courses';
    const logoHref = isOnCourses ? `#/modules${courseQuery}` : '#/courses';
    const logoTitle = isOnCourses ? 'Go to Curriculum Workspace' : 'Go to Course Portfolio';

    return { path, courseId, courseQuery, activeTab, isStudentView, logoHref, logoTitle };
  });

  let activeCourseLabel = $derived.by(() => {
    if (!parsed.courseId) return '';
    const match = courses.find((c) => c.course_id === parsed.courseId || c.id === parsed.courseId);
    if (match) {
      return match.code || match.title || match.name || 'Course';
    }
    return courseTitle && courseTitle !== 'Course Workspace' ? courseTitle : 'HIST-002';
  });
</script>

<header class="app-header">
  <div class="header-left">
    <a href={parsed.logoHref} title={parsed.logoTitle} class="brand-logo">
      FIOSRA
    </a>

    <div class="context-indicator">
      <span class="context-separator">/</span>
      {#if parsed.isStudentView}
        <span class="context-badge student">STUDENT</span>
      {:else}
        <span class="context-badge">LMS</span>
      {/if}

      {#if activeCourseLabel && parsed.activeTab !== 'courses' && parsed.activeTab !== 'student-portal'}
        <span class="context-separator">/</span>
        <a
          href={parsed.isStudentView ? `#/student/home${parsed.courseQuery}` : `#/modules${parsed.courseQuery}`}
          class="course-context-pill"
          title="Active Course: {activeCourseLabel}"
        >
          {activeCourseLabel}
        </a>
      {/if}
    </div>
  </div>

  <nav class="nav-segmented" aria-label="Main Navigation">
    {#if parsed.isStudentView}
      <a
        href="#/student/portal"
        class="nav-pill {parsed.activeTab === 'student-portal' ? 'active' : ''}"
      >
        Timeline
      </a>
      <a
        href="#/student/home{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'student-home' ? 'active' : ''}"
      >
        Home
      </a>
      <a
        href="#/student{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'student-canvas' ? 'active' : ''}"
      >
        Canvas
      </a>
      <a
        href="#/student/trace{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'student-trace' ? 'active' : ''}"
      >
        Trace
      </a>
    {:else}
      <a
        href="#/courses"
        class="nav-pill {parsed.activeTab === 'courses' ? 'active' : ''}"
      >
        Portfolio
      </a>
      <a
        href="#/modules{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'modules' ? 'active' : ''}"
      >
        Curriculum
      </a>
      <a
        href="#/designer{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'designer' ? 'active' : ''}"
      >
        Designer
      </a>
      <a
        href="#/review{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'review' ? 'active' : ''}"
      >
        AutoSCORE
      </a>
      <a
        href="#/diagnostics{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'diagnostics' ? 'active' : ''}"
      >
        Cohort
      </a>
      <a
        href="#/graph{parsed.courseQuery}"
        class="nav-pill {parsed.activeTab === 'graph' ? 'active' : ''}"
      >
        Graph
      </a>
    {/if}
  </nav>

  <div class="header-right">
    {#if parsed.isStudentView}
      <a href="#/modules{parsed.courseQuery}" class="role-switch-btn" title="Switch to Educator LMS">
        <span>Educator LMS</span>
        <span class="switch-icon">↗</span>
      </a>
      <div class="user-chip" title="Active Student Session: Julian Hayes">
        <div class="user-avatar student-avatar">JH</div>
        <span class="user-name">Julian Hayes</span>
      </div>
    {:else}
      <div class="status-chip" title="Live Knowledge Graph Grounded (14 KCs Active)">
        <span class="status-dot"></span>
        <span class="status-label">14 KCs Grounded</span>
      </div>

      <a href="#/student{parsed.courseQuery}" class="role-switch-btn" title="Preview as Student">
        <span>Student View</span>
        <span class="switch-icon">↗</span>
      </a>

      <div class="user-chip" title="Active Educator Session: Dr. Vance">
        <div class="user-avatar">DV</div>
        <span class="user-name">Dr. Vance</span>
      </div>
    {/if}
  </div>
</header>

<style>
  .app-header {
    height: 56px;
    background: rgba(14, 17, 23, 0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }

  /* Left Cluster */
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .brand-logo {
    font-family: var(--font-brand);
    font-weight: 800;
    font-size: 18px;
    letter-spacing: -0.3px;
    color: #ffffff;
    text-decoration: none;
    background: linear-gradient(135deg, #ffffff 45%, var(--color-horizon-bright));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .brand-logo:hover {
    opacity: 0.88;
  }

  .context-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .context-separator {
    color: rgba(255, 255, 255, 0.18);
    font-size: 13px;
    font-weight: 400;
  }

  .context-badge {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 2px 7px;
    border-radius: var(--radius-xs);
    background: rgba(59, 130, 246, 0.12);
    color: var(--color-horizon-bright);
    border: 1px solid rgba(59, 130, 246, 0.28);
  }

  .context-badge.student {
    background: rgba(16, 185, 129, 0.12);
    color: var(--color-signal-green);
    border-color: rgba(16, 185, 129, 0.28);
  }

  .course-context-pill {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-bright);
    text-decoration: none;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 2px 9px;
    border-radius: var(--radius-full);
    transition: all 0.15s ease;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .course-context-pill:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
  }

  /* Center Segmented Navigation */
  .nav-segmented {
    display: flex;
    align-items: center;
    gap: 2px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-full);
    padding: 3px;
    backdrop-filter: blur(8px);
  }

  .nav-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 14px;
    font-size: 12.5px;
    font-weight: 500;
    color: var(--color-slate-light);
    text-decoration: none;
    border-radius: var(--radius-full);
    transition: all 0.15s ease;
    white-space: nowrap;
    line-height: 1;
    border: 1px solid transparent;
  }

  .nav-pill:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.05);
  }

  .nav-pill.active {
    color: #ffffff;
    background: rgba(59, 130, 246, 0.18);
    border-color: rgba(59, 130, 246, 0.4);
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  }

  /* Right Cluster */
  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .status-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: var(--radius-full);
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.22);
    font-size: 11px;
    font-weight: 600;
    color: var(--color-signal-green);
    cursor: default;
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-signal-green);
    box-shadow: 0 0 6px var(--color-signal-green);
  }

  .role-switch-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    font-size: 11.5px;
    font-weight: 500;
    color: var(--color-slate-bright);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .role-switch-btn:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
  }

  .switch-icon {
    font-size: 10px;
    opacity: 0.7;
  }

  .user-chip {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 3px 9px 3px 3px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-full);
    cursor: default;
  }

  .user-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9.5px;
    font-weight: 700;
    color: white;
  }

  .user-avatar.student-avatar {
    background: linear-gradient(135deg, #10b981, #06b6d4);
  }

  .user-name {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-bright);
  }

  /* Responsive Adjustments */
  @media (max-width: 1200px) {
    .user-name {
      display: none;
    }
    .user-chip {
      padding: 2px;
    }
  }

  @media (max-width: 1080px) {
    .status-label {
      display: none;
    }
    .status-chip {
      padding: 5px;
    }
    .nav-pill {
      padding: 5px 10px;
      font-size: 12px;
    }
  }

  @media (max-width: 880px) {
    .context-indicator {
      display: none;
    }
  }
</style>
