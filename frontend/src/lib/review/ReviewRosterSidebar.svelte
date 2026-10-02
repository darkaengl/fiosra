<script>
  import { formatDate } from '../session.js';

  let {
    queue = [],
    filteredQueue = [],
    selected = null,
    rosterWidth = 260,
    isRosterCollapsed = false,
    filterStatus = 'all',
    searchQuery = '',
    completedCount = 0,
    submittedCount = 0,
    activeCount = 0,
    assignmentId = '',
    onSelect = () => {},
    onCollapse = () => {},
    onExpand = () => {},
    onFilterChange = () => {},
    onSearchChange = () => {},
    onRefresh = () => {},
  } = $props();
</script>

{#if !isRosterCollapsed}
  <aside class="canvas-roster-sidebar" style:width={`${rosterWidth}px`}>
    <div class="roster-top-bar">
      <span class="roster-top-title">Roster ({filteredQueue.length})</span>
      <button
        type="button"
        class="btn-collapse-sidebar"
        onclick={onCollapse}
        title="Collapse student roster to maximize PDF viewing width"
      >
        ⇤
      </button>
    </div>

    <div class="roster-search-bar">
      <input
        type="text"
        class="roster-search-input"
        placeholder="Filter students…"
        value={searchQuery}
        oninput={(e) => onSearchChange(e.currentTarget.value)}
      />
      <div class="roster-filter-pills">
        <button
          type="button"
          class="filter-pill"
          class:active={filterStatus === 'all'}
          onclick={() => onFilterChange('all')}
        >All ({queue.length})</button>
        <button
          type="button"
          class="filter-pill"
          class:active={filterStatus === 'completed'}
          onclick={() => onFilterChange('completed')}
        >Final ({completedCount})</button>
        {#if submittedCount > 0}
          <button
            type="button"
            class="filter-pill"
            class:active={filterStatus === 'submitted'}
            onclick={() => onFilterChange('submitted')}
          >Ready ({submittedCount})</button>
        {/if}
        {#if activeCount > 0}
          <button
            type="button"
            class="filter-pill"
            class:active={filterStatus === 'active'}
            onclick={() => onFilterChange('active')}
          >Draft ({activeCount})</button>
        {/if}
      </div>
    </div>

    <div class="roster-scroll-list">
      {#if filteredQueue.length === 0}
        <div class="roster-empty">No students found.</div>
      {:else}
        {#each filteredQueue as item (item.session_id)}
          <button
            type="button"
            class="roster-item-btn"
            class:active={selected?.session_id === item.session_id}
            onclick={() => onSelect(item)}
          >
            <span class="roster-avatar-mini"
              >{item.student_id.slice(0, 2).toUpperCase()}</span
            >
            <div class="roster-item-info">
              <span class="roster-item-id">{item.student_id}</span>
              {#if !assignmentId && item.assignment_title}
                <span class="roster-item-assignment"
                  >{item.assignment_title}</span
                >
              {/if}
              <span class="roster-item-date"
                >{formatDate(item.submitted_at)}</span
              >
            </div>
            {#if item.status === 'submitted'}
              <span class="mini-status-badge submitted">Ready</span>
            {:else if item.status === 'completed'}
              <span class="mini-status-badge completed">Final</span>
            {:else}
              <span class="mini-status-badge in-progress">Draft</span>
            {/if}
          </button>
        {/each}
      {/if}
    </div>

    <button
      type="button"
      class="roster-refresh-btn"
      onclick={onRefresh}
      title="Check for new submissions"
    >
      ↻ Refresh Roster
    </button>
  </aside>
{:else}
  <!-- Collapsed Roster Rail (42px) -->
  <aside
    class="canvas-roster-rail"
    onclick={onExpand}
    title="Click to expand student roster"
  >
    <button
      type="button"
      class="btn-expand-rail"
      onclick={onExpand}
      title="Expand student roster"
    >
      ⇥
    </button>
    <div class="rail-vertical-text">
      STUDENTS ({filteredQueue.length})
    </div>
  </aside>
{/if}

<style>
  .canvas-roster-sidebar {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
  }

  .roster-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--color-bone, #f6f5f1);
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
    height: 38px;
    box-sizing: border-box;
  }

  .roster-top-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .btn-collapse-sidebar {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 12px;
    padding: 1px 6px;
    cursor: pointer;
    color: var(--color-slate-muted);
    transition: all 0.12s;
  }

  .btn-collapse-sidebar:hover {
    background: #e2e8f0;
    color: var(--color-heading);
  }

  /* Collapsed Rail */
  .canvas-roster-rail {
    width: 42px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 4px;
    gap: 14px;
    background: #ffffff;
    border-right: 1px solid var(--color-graphite-border);
    cursor: pointer;
    transition: background 0.15s;
  }

  .canvas-roster-rail:hover {
    background: var(--color-bone, #f6f5f1);
  }

  .btn-expand-rail {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: 4px;
    font-size: 12px;
    padding: 3px 5px;
    cursor: pointer;
    color: var(--color-slate-muted);
  }

  .rail-vertical-text {
    writing-mode: vertical-rl;
    text-orientation: mixed;
    transform: rotate(180deg);
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: var(--color-slate-muted);
  }

  .roster-search-bar {
    padding: 8px 10px;
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
  }

  .roster-search-input {
    width: 100%;
    padding: 5px 8px;
    font-size: 11.5px;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm, 6px);
    background: #ffffff;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  .roster-search-input:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .roster-filter-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .filter-pill {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: 999px;
    color: var(--color-slate-muted);
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 7px;
    cursor: pointer;
    transition: all 0.12s;
  }

  .filter-pill:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .filter-pill.active {
    background: rgba(217, 119, 6, 0.12);
    border-color: rgba(217, 119, 6, 0.35);
    color: #92400e;
  }

  .roster-scroll-list {
    flex: 1;
    overflow-y: auto;
    padding: 6px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .roster-empty {
    color: var(--color-slate-muted);
    font-size: 11px;
    text-align: center;
    padding: 20px 8px;
    font-style: italic;
  }

  .roster-item-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 9px;
    background: #ffffff;
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid transparent;
    border-radius: var(--radius-sm, 6px);
    cursor: pointer;
    text-align: left;
    width: 100%;
    transition: all 0.12s ease;
    color: inherit;
    font-family: inherit;
  }

  .roster-item-btn:hover {
    border-left-color: var(--color-horizon-blue, #4f6bff);
    background: #f8fafc;
  }

  .roster-item-btn.active {
    border-left-color: var(--color-horizon-bright, #d97706);
    background: rgba(217, 119, 6, 0.08);
    box-shadow: inset 0 0 0 1px rgba(217, 119, 6, 0.12);
  }

  .roster-avatar-mini {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4f6bff, #0ea5e9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9.5px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
  }

  .roster-item-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .roster-item-id {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-heading);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .roster-item-assignment {
    font-size: 9.5px;
    color: var(--color-slate-light);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .roster-item-date {
    font-size: 9px;
    color: var(--color-slate-muted);
  }

  .mini-status-badge {
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 999px;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .mini-status-badge.submitted {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid rgba(5, 150, 105, 0.2);
  }

  .mini-status-badge.completed {
    background: #ecfdf5;
    color: #047857;
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  .mini-status-badge.in-progress {
    background: rgba(2, 132, 199, 0.1);
    color: #0369a1;
    border: 1px solid rgba(2, 132, 199, 0.2);
  }

  .roster-refresh-btn {
    flex-shrink: 0;
    padding: 7px;
    font-size: 10px;
    font-weight: 600;
    color: var(--color-horizon-bright, #d97706);
    background: none;
    border: none;
    border-top: 1px solid var(--color-graphite-border);
    cursor: pointer;
    transition: background 0.12s;
  }

  .roster-refresh-btn:hover {
    background: var(--color-graphite-hover, #eee);
  }
</style>
