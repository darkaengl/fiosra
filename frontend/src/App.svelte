<script>
  import Router from 'svelte-spa-router';
  import './css/design-system.css';
  import AppHeader from './lib/AppHeader.svelte';

  import Modules from './routes/Modules.svelte';
  import Courses from './routes/Courses.svelte';
  import AssignmentDesigner from './routes/AssignmentDesigner.svelte';
  import StudioReview from './routes/StudioReview.svelte';
  import CohortDiagnostics from './routes/CohortDiagnostics.svelte';
  import KnowledgeGraph from './routes/KnowledgeGraph.svelte';
  import StudentWorkspace from './routes/StudentWorkspace.svelte';
  import StudentHome from './routes/StudentHome.svelte';
  import StudentPortal from './routes/StudentPortal.svelte';
  import StudentTrace from './routes/StudentTrace.svelte';

  const routes = {
    '/': Modules,
    '/modules': Modules,
    '/courses': Courses,
    '/designer': AssignmentDesigner,
    '/review': StudioReview,
    '/diagnostics': CohortDiagnostics,
    '/graph': KnowledgeGraph,
    '/student': StudentWorkspace,
    '/student/home': StudentHome,
    '/student/portal': StudentPortal,
    '/student/trace': StudentTrace,
    '*': Modules,
  };
</script>

<div class="app-root">
  <AppHeader />
  <div class="route-viewport">
    <Router {routes} />
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: var(--color-obsidian);
    color: var(--color-slate-bright);
    font-family: var(--font-ui);
    -webkit-font-smoothing: antialiased;
  }

  .app-root {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .route-viewport {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
</style>
