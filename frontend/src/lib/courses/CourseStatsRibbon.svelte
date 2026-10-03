<script lang="ts">
  let {
    coursesCount = 0,
    totalModules = 0,
    totalAssignments = 0,
  } = $props<{
    coursesCount?: number;
    totalModules?: number;
    totalAssignments?: number;
  }>();
</script>

<div class="stats-ribbon">
  <div class="stat-card">
    <div class="stat-label"><span>Active Workspaces</span><span>📚</span></div>
    <div class="stat-value-row">
      <span class="stat-value">{coursesCount}</span>
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

<style>
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
  .stat-trend.neutral {
    color: var(--color-slate-light);
  }
</style>
