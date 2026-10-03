<script lang="ts">
  let {
    wordCount = 0,
    readingTimeMin = 1,
    totalPages = 1,
    currentPageIndex = 1,
    documentHeadingsCount = 0,
    isLocked = false,
    pagesMap = {},
    onAddNewPage = () => {},
    onPrevPage = () => {},
    onNextPage = () => {},
    onGoToPage = (page: number) => {},
    onDeletePage = (page: number) => {},
  } = $props<{
    wordCount?: number;
    readingTimeMin?: number;
    totalPages?: number;
    currentPageIndex?: number;
    documentHeadingsCount?: number;
    isLocked?: boolean;
    pagesMap?: Record<number, any>;
    onAddNewPage?: () => void;
    onPrevPage?: () => void;
    onNextPage?: () => void;
    onGoToPage?: (page: number) => void;
    onDeletePage?: (page: number) => void;
  }>();
</script>

<footer class="document-page-footer">
  <div class="page-footer-stats">
    <span>{wordCount.toLocaleString()} words</span>
    <span>•</span>
    <span>{readingTimeMin} min read</span>
    {#if totalPages > 1}
      <span>•</span>
      <span>Page {currentPageIndex} of {totalPages}</span>
    {/if}
    {#if documentHeadingsCount > 0}
      <span>•</span>
      <span>{documentHeadingsCount} {documentHeadingsCount === 1 ? 'section' : 'sections'}</span>
    {/if}
    {#if !isLocked}
      <span>•</span>
      <button type="button" class="page-footer-add-btn" onclick={onAddNewPage} title="Add a new page">＋ Add page</button>
    {/if}
  </div>

  {#if totalPages > 1}
    <div class="page-footer-pagination">
      <button 
        type="button" 
        class="page-nav-mini-btn" 
        onclick={onPrevPage}
        disabled={currentPageIndex <= 1}
        title="Previous page"
      >
        ‹
      </button>
      {#each Object.keys(pagesMap).map(Number).sort((a, b) => a - b) as p}
        <button 
          type="button" 
          class="page-mini-pill" 
          class:active={p === currentPageIndex}
          onclick={() => onGoToPage(p)}
          title="Go to Page {p}"
        >
          {p}
        </button>
      {/each}
      <button 
        type="button" 
        class="page-nav-mini-btn" 
        onclick={onNextPage}
        disabled={currentPageIndex >= totalPages}
        title="Next page"
      >
        ›
      </button>
      {#if totalPages > 1 && !isLocked}
        <button 
          type="button" 
          class="page-delete-mini-btn" 
          onclick={() => onDeletePage(currentPageIndex)}
          title="Delete current page ({currentPageIndex})"
        >
          ✕
        </button>
      {/if}
    </div>
  {/if}
</footer>

<style>
  .document-page-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 20px;
    border-top: 1px solid var(--color-graphite-border, #e2e4dc);
    font-size: 11px;
    color: var(--color-slate-muted, #94a3b8);
    user-select: none;
    flex-shrink: 0;
  }

  .page-footer-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .page-footer-add-btn {
    background: transparent;
    border: none;
    font-size: inherit;
    font-weight: 600;
    color: var(--color-slate-light, #64748b);
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
    padding: 0;
    transition: color 0.15s ease;
  }

  .page-footer-add-btn:hover {
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .page-footer-pagination {
    display: inline-flex;
    align-items: center;
    gap: 3px;
  }

  .page-nav-mini-btn {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 4px;
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-heading, #121418);
    cursor: pointer;
  }

  .page-nav-mini-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #e8eae3);
  }

  .page-nav-mini-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .page-mini-pill {
    min-width: 22px;
    height: 22px;
    padding: 0 4px;
    border-radius: 4px;
    border: 1px solid transparent;
    background: transparent;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light, #474d5a);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .page-mini-pill:hover:not(.active) {
    background: var(--color-graphite-hover, #e8eae3);
  }

  .page-mini-pill.active {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
  }

  .page-delete-mini-btn {
    background: transparent;
    border: none;
    font-size: 11px;
    color: #dc2626;
    cursor: pointer;
    margin-left: 2px;
    padding: 2px 4px;
  }
</style>
