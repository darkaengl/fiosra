<script>
  import { onMount } from 'svelte';

  let {
    courseTitle = 'Course Workspace',
  } = $props();

  let currentHash = $state(typeof window !== 'undefined' ? window.location.hash || '#/' : '#/');
  let courses = $state([]);
  let currentTheme = $state('light');

  function handleHashChange() {
    currentHash = window.location.hash || '#/';
  }

  function applyTheme(theme) {
    currentTheme = theme;
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
      document.body.setAttribute('data-theme', theme);
    }
  }

  function toggleTheme() {
    const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('fiosra_theme', nextTheme);
    }
  }

  onMount(async () => {
    window.addEventListener('hashchange', handleHashChange);

    // Initialize theme from storage or system preference
    const saved = localStorage.getItem('fiosra_theme');
    if (saved === 'dark' || saved === 'light') {
      applyTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
    } else {
      applyTheme('light');
    }

    try {
      const res = await fetch('/courses');
      if (res.ok) {
        const data = await res.json();
        courses = Array.isArray(data) ? data : data.courses || [];
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

    const logoHref = isStudentView ? '#/student/portal' : '#/courses';
    const logoTitle = isStudentView ? 'Return to Student Hub' : 'Return to Course Portfolio';
    const isGlobalView = !isStudentView && activeTab === 'courses';

    return { path, courseId, courseQuery, activeTab, isStudentView, isGlobalView, logoHref, logoTitle };
  });

  let activeCourseLabel = $derived.by(() => {
    if (!parsed.courseId) return '';
    const match = courses.find((c) => c.course_id === parsed.courseId || c.id === parsed.courseId);
    if (match) {
      return match.code || match.title || match.name || 'Course';
    }
    return courseTitle && courseTitle !== 'Course Workspace' ? courseTitle : 'Current course';
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

      {#if activeCourseLabel && !parsed.isGlobalView}
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

  {#if !parsed.isGlobalView}
    <nav class="nav-segmented" aria-label="Main Navigation">
      {#if parsed.isStudentView}
        <a
          href="#/student/portal{parsed.courseQuery}"
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
  {:else}
    <div class="header-center-placeholder"></div>
  {/if}

  <div class="header-right">
    <!-- Theme Toggle Button -->
    <button
      type="button"
      class="theme-toggle-btn"
      onclick={toggleTheme}
      title={currentTheme === 'light' ? 'Switch to Dark Mode (🌙)' : 'Switch to Academic Light Mode (☀️)'}
      aria-label="Toggle Light/Dark Theme"
    >
      <span class="theme-icon light-icon" class:active={currentTheme === 'light'}>☀️</span>
      <span class="theme-icon dark-icon" class:active={currentTheme === 'dark'}>🌙</span>
    </button>

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
      <div class="status-chip" title="Live Knowledge Graph Grounding Status">
        <span class="status-dot"></span>
        <span class="status-label">14 KCs Grounded</span>
      </div>

      <a href="#/student/portal" class="role-switch-btn" title="Preview as Student">
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
    background: var(--header-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--header-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: var(--shadow-sm);
    transition: background-color 0.2s ease, border-color 0.2s ease;
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
    color: var(--color-heading);
    text-decoration: none;
    background: linear-gradient(135deg, var(--color-heading) 45%, var(--color-horizon-bright));
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
    color: var(--color-slate-subtle);
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
    background: var(--pill-active-bg);
    color: var(--color-horizon-bright);
    border: 1px solid var(--pill-active-border);
  }

  .context-badge.student {
    background: var(--color-signal-green-bg);
    color: var(--color-signal-green);
    border-color: rgba(78, 170, 122, 0.35);
  }

  .course-context-pill {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-slate-bright);
    text-decoration: none;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    padding: 2px 9px;
    border-radius: var(--radius-full);
    transition: all 0.15s ease;
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .course-context-pill:hover {
    color: var(--color-heading);
    background: var(--pill-hover);
    border-color: var(--color-slate-subtle);
  }

  .header-center-placeholder {
    flex: 1;
  }

  /* Center Segmented Navigation */
  .nav-segmented {
    display: flex;
    align-items: center;
    gap: 2px;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
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
    color: var(--color-heading);
    background: var(--pill-hover);
  }

  .nav-pill.active {
    color: var(--pill-active-color);
    background: var(--pill-active-bg);
    border-color: var(--pill-active-border);
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  }

  /* Right Cluster */
  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  /* Theme Toggle */
  .theme-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 3px 5px;
    border-radius: var(--radius-full);
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    cursor: pointer;
    transition: all 0.18s ease;
    user-select: none;
  }

  .theme-toggle-btn:hover {
    background: var(--pill-hover);
    border-color: var(--color-slate-subtle);
    transform: translateY(-1px);
  }

  .theme-icon {
    font-size: 12px;
    padding: 2px 5px;
    border-radius: var(--radius-full);
    opacity: 0.35;
    transition: all 0.18s ease;
    line-height: 1;
  }

  .theme-icon.active {
    opacity: 1;
    background: var(--pill-active-bg);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .status-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: var(--radius-full);
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(78, 170, 122, 0.3);
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
    background: var(--role-btn-bg);
    border: 1px solid var(--role-btn-border);
    border-radius: var(--radius-sm);
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .role-switch-btn:hover {
    color: var(--color-heading);
    background: var(--role-btn-hover);
    border-color: var(--color-slate-subtle);
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
    background: var(--user-chip-bg);
    border: 1px solid var(--user-chip-border);
    border-radius: var(--radius-full);
    cursor: default;
  }

  .user-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e5a93c, #c68a25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9.5px;
    font-weight: 700;
    color: #121418;
  }

  .user-avatar.student-avatar {
    background: linear-gradient(135deg, #4eaa7a, #38bdf8);
    color: #121418;
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
