<script lang="ts">
  import type { DocumentHeading } from './editorTypes';

  let {
    isOpen = false,
    totalPages = 1,
    documentHeadings = [],
    pagesMap = {},
    currentPageIndex = 1,
    onGoToPage = () => {},
    onJumpToHeading = () => {},
    onClose = () => {},
  } = $props<{
    isOpen?: boolean;
    totalPages?: number;
    documentHeadings?: DocumentHeading[];
    pagesMap?: Record<number, any[]>;
    currentPageIndex?: number;
    onGoToPage?: (page: number) => void;
    onJumpToHeading?: (heading: DocumentHeading) => void;
    onClose?: () => void;
  }>();
</script>

{#if isOpen}
  <aside class="document-outline-sidebar" aria-label="Document Outline">
    <div class="outline-header">
      <div class="outline-title-row">
        <span class="outline-heading-label">Document Outline</span>
        <button
          type="button"
          class="outline-collapse-btn"
          onclick={onClose}
          title="Collapse outline"
        >
          ✕
        </button>
      </div>
      <div class="outline-meta-sub">
        <span>{totalPages} {totalPages === 1 ? 'Page' : 'Pages'}</span>
        <span>•</span>
        <span>{documentHeadings.length} {documentHeadings.length === 1 ? 'Heading' : 'Headings'}</span>
      </div>
    </div>

    <div class="outline-tree-container">
      {#each Object.keys(pagesMap).map(Number).sort((a, b) => a - b) as p}
        {@const pHeadings = documentHeadings.filter((h) => h.page === p)}
        <div class="outline-page-group" class:is-current-page={p === currentPageIndex}>
          <button
            type="button"
            class="outline-page-item"
            class:active={p === currentPageIndex}
            onclick={() => onGoToPage(p)}
            title="Go to Page {p}"
          >
            <div class="outline-page-item-left">
              <span class="page-sheet-icon">📄</span>
              <span class="page-name">Page {p}</span>
            </div>
            <span class="page-item-badge">{pHeadings.length} sec</span>
          </button>

          {#if pHeadings.length > 0}
            <div class="outline-headings-list">
              {#each pHeadings as h}
                <button
                  type="button"
                  class="outline-heading-item level-{h.level}"
                  onclick={() => onJumpToHeading(h)}
                  title="Jump to {h.text}"
                >
                  <span class="heading-tag">H{h.level}</span>
                  <span class="heading-text">{h.text}</span>
                </button>
              {/each}
            </div>
          {:else}
            <div class="outline-empty-page-hint">
              <span>(No headings)</span>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </aside>
{/if}

<style>
  .document-outline-sidebar {
    width: 240px;
    height: 100%;
    background: var(--color-bone-muted, #f8fafc);
    border-right: 1px solid var(--color-graphite-border, #e2e8f0);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    overflow: hidden;
    z-index: 15;
  }

  .outline-header {
    padding: 12px 14px 8px;
    border-bottom: 1px solid var(--color-graphite-border, #e2e8f0);
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .outline-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .outline-heading-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-slate-muted, #64748b);
  }

  .outline-collapse-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-muted, #64748b);
    font-size: 13px;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 3px;
  }

  .outline-collapse-btn:hover {
    color: var(--color-heading, #0f172a);
    background: rgba(0, 0, 0, 0.05);
  }

  .outline-meta-sub {
    font-size: 10px;
    color: var(--color-slate-muted, #64748b);
    display: flex;
    gap: 5px;
  }

  .outline-tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .outline-page-group {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .outline-page-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 5px 8px;
    background: transparent;
    border: none;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-heading, #0f172a);
    cursor: pointer;
    text-align: left;
    transition: background 0.12s ease;
  }

  .outline-page-item:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  .outline-page-item.active {
    background: rgba(37, 99, 235, 0.08);
    color: #2563eb;
  }

  .outline-page-item-left {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .page-item-badge {
    font-size: 9px;
    padding: 1px 4px;
    border-radius: 3px;
    background: rgba(0, 0, 0, 0.05);
    color: var(--color-slate-muted, #64748b);
  }

  .outline-headings-list {
    display: flex;
    flex-direction: column;
    gap: 1px;
    padding-left: 12px;
  }

  .outline-heading-item {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 3px 6px;
    background: transparent;
    border: none;
    border-radius: 3px;
    font-size: 11px;
    color: var(--color-slate-muted, #64748b);
    cursor: pointer;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .outline-heading-item:hover {
    background: rgba(0, 0, 0, 0.04);
    color: var(--color-heading, #0f172a);
  }

  .outline-heading-item.level-1 {
    font-weight: 700;
    color: var(--color-heading, #0f172a);
  }

  .outline-heading-item.level-2 {
    padding-left: 8px;
  }

  .outline-heading-item.level-3 {
    padding-left: 14px;
    font-size: 10px;
  }

  .heading-tag {
    font-size: 8.5px;
    font-weight: 800;
    padding: 1px 3px;
    border-radius: 2px;
    background: rgba(0, 0, 0, 0.05);
  }

  .outline-empty-page-hint {
    font-size: 9.5px;
    font-style: italic;
    color: var(--color-slate-muted, #94a3b8);
    padding-left: 20px;
  }
</style>
