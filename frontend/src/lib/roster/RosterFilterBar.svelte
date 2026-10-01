<script lang="ts">
  import type { RosterFilter } from './rosterTypes';

  let {
    filter = 'all',
    onFilterChange,
    totalCount = 0,
    completedCount = 0,
    submittedCount = 0,
    strugglingCount = 0,
    inProgressCount = 0,
  } = $props<{
    filter?: RosterFilter;
    onFilterChange?: (filter: RosterFilter) => void;
    totalCount?: number;
    completedCount?: number;
    submittedCount?: number;
    strugglingCount?: number;
    inProgressCount?: number;
  }>();
</script>

<div class="roster-filter-bar">
  <div class="filter-group">
    <button
      type="button"
      class="filter-pill"
      class:active={filter === 'all'}
      onclick={() => onFilterChange?.('all')}
    >
      All Learners ({totalCount})
    </button>
    <button
      type="button"
      class="filter-pill"
      class:active={filter === 'completed'}
      onclick={() => onFilterChange?.('completed')}
    >
      Completed ({completedCount})
    </button>
    {#if submittedCount > 0}
      <button
        type="button"
        class="filter-pill"
        class:active={filter === 'submitted'}
        onclick={() => onFilterChange?.('submitted')}
      >
        Submitted ({submittedCount})
      </button>
    {/if}
    <button
      type="button"
      class="filter-pill"
      class:active={filter === 'struggling'}
      onclick={() => onFilterChange?.('struggling')}
    >
      Needs Scaffolding ({strugglingCount})
    </button>
    <button
      type="button"
      class="filter-pill"
      class:active={filter === 'in_progress'}
      onclick={() => onFilterChange?.('in_progress')}
    >
      In Progress ({inProgressCount})
    </button>
  </div>
</div>

<style>
  .roster-filter-bar {
    padding: 12px 18px;
    background: var(--color-graphite-card, #ffffff);
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
    display: flex;
    align-items: center;
  }

  .filter-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .filter-pill {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #dddcd5);
    color: var(--color-slate-light, #6d7378);
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .filter-pill:hover {
    color: var(--color-heading, #111315);
    background: var(--color-graphite-hover, #f0efea);
  }

  .filter-pill.active {
    background: var(--color-heading, #111315);
    color: var(--surface, #ffffff);
    border-color: var(--color-heading, #111315);
  }
</style>
