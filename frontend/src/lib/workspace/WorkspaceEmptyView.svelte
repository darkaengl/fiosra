<script lang="ts">
  let {
    isLoading = false,
    error = '',
    assignment = null,
    courseId = '',
  } = $props<{
    isLoading?: boolean;
    error?: string;
    assignment?: any;
    courseId?: string;
  }>();
</script>

{#if isLoading}
  <main class="loading-view">
    <div class="spinner"></div>
    <p>Opening your reasoning canvas…</p>
  </main>
{:else if error && !assignment}
  <main class="empty-view">
    <h1>Workspace unavailable</h1>
    <p>{error}</p>
    <div class="empty-actions">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Return to Courses</a>
    </div>
  </main>
{:else if !assignment}
  <main class="empty-view">
    <h1>{courseId ? 'No published assignment in this course yet' : 'No active assignment selected'}</h1>
    <p>
      {courseId 
        ? 'Your instructor has not published an active reasoning assignment for this course yet.' 
        : 'Open an active milestone from your enrolled courses to start a protected reasoning session.'}
    </p>
    <div class="empty-actions">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Browse Available Courses</a>
    </div>
  </main>
{/if}

<style>
  .loading-view, .empty-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 56px);
    background: var(--color-obsidian);
    color: var(--color-slate-light);
    padding: 24px;
    text-align: center;
  }

  .empty-view h1 {
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0 0 8px;
  }

  .empty-view p {
    font-size: 13px;
    color: var(--color-slate-muted);
    max-width: 480px;
    margin: 0 0 16px;
    line-height: 1.5;
  }

  .empty-actions {
    display: flex;
    gap: 12px;
    margin-top: 14px;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-top-color: var(--color-horizon-blue);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: pointer;
  }

  .btn-primary {
    background: var(--color-horizon-blue);
    color: #fff;
    border: 1px solid var(--color-horizon-blue);
  }

  .btn-primary:hover {
    filter: brightness(1.1);
  }

  .btn-secondary {
    background: var(--color-graphite);
    color: var(--color-slate-light);
    border: 1px solid var(--color-graphite-border);
  }

  .btn-secondary:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }
</style>
