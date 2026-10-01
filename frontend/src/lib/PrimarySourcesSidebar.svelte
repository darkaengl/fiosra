<script>
  import PdfViewer from './PdfViewer.svelte';
  import AssignmentBriefHandout from './sources/AssignmentBriefHandout.svelte';
  import { printAssignmentSheet, printSourcePdf } from './sources/sourcePrintUtils';

  let {
    sources = [],
    assignment = null,
    courseTitle = 'Department of Historical Studies',
    courseId = '',
    onQuoteEvidence = () => null,
    isCollapsed = false,
    isExpanded = true,
    onToggleCollapse = () => null,
    onToggleExpand = () => null,
  } = $props();

  // Active tab inside sidebar: 'assignment' | 'sources'
  let activeTab = $state('sources');

  // Parse and group sources into documents
  let displaySources = $derived.by(() => {
    const list = sources || [];
    if (list.length > 0) {
      return list.map((s, idx) => ({
        source_id: s.source_id || s.id || `src_${idx + 1}`,
        author: s.author || s.citation || s.title || 'Primary Source',
        title: s.title || s.source_title || `Document ${idx + 1}`,
        date: s.date || 'Assigned Document',
        provenance: s.provenance || s.citation || '',
        passage: s.passage || s.excerpt || s.text || '',
        hidden_context: s.hidden_context || s.synopsis || s.relevance_guidance || '',
        target_kc: s.target_kc || s.kc || 'KC_EVIDENCE',
        source_url: s.source_url || s.url || s.download_url || null,
        relevance_guidance: s.relevance_guidance || '',
        page: s.page || s.pageNum || null,
        section: s.section || '',
      }));
    }
    return [];
  });

  // Group by document title
  let documents = $derived.by(() => {
    const docMap = new Map();
    for (const src of displaySources) {
      const docKey = src.title || 'Course Reading';
      if (!docMap.has(docKey)) {
        docMap.set(docKey, {
          title: docKey,
          author: src.author,
          source_url: src.source_url,
          sections: [],
        });
      } else if (!docMap.get(docKey).source_url && src.source_url) {
        docMap.get(docKey).source_url = src.source_url;
      }
      docMap.get(docKey).sections.push(src);
    }
    return Array.from(docMap.values());
  });

  let selectedDocIndex = $state(0);
  let activeDoc = $derived(
    (documents[selectedDocIndex]?.source_url ? documents[selectedDocIndex] : null) ||
    documents.find((d) => d.source_url) ||
    documents[selectedDocIndex] ||
    documents[0] ||
    null
  );

  // Search State
  let pdfViewerRef = $state(null);
  let initialViewerPage = $state(1);
  let matchInfo = $state({ current: 0, total: 0 });
  let searchQuery = $state('');
  let activeSearchTerm = $state('');
  let iframeKey = $state(1);

  function handleMatchesChange(info) {
    if (!info) return;
    if (
      matchInfo.current !== info.current ||
      matchInfo.total !== info.total ||
      matchInfo.pageNum !== info.pageNum ||
      matchInfo.sectionTitle !== info.sectionTitle
    ) {
      matchInfo = info;
    }
  }

  function performSearch() {
    const q = searchQuery.trim();
    if (!q) {
      activeSearchTerm = '';
      iframeKey += 1;
      return;
    }
    activeSearchTerm = q;
    iframeKey += 1;
  }

  function clearSearch() {
    searchQuery = '';
    activeSearchTerm = '';
  }

  function handlePrintBrief() {
    printAssignmentSheet(assignment?.published?.title || assignment?.title);
  }

  function handlePrintPdf() {
    printSourcePdf(activeDoc?.source_url);
  }

  function switchToSource(sourceTitle, src = null) {
    if (sourceTitle) {
      const idx = documents.findIndex((d) => d.title === sourceTitle);
      if (idx >= 0) selectedDocIndex = idx;
    }
    activeTab = 'sources';

    const targetPage = src?.page || src?.pageNum || null;
    if (targetPage) {
      initialViewerPage = targetPage;
      setTimeout(() => {
        pdfViewerRef?.scrollToPage(targetPage);
      }, 120);
    } else if (src?.citation) {
      setTimeout(() => {
        pdfViewerRef?.scrollToCitation(src.citation);
      }, 120);
    }
  }
</script>

<aside
  class="evidentiary-well"
  class:collapsed={isCollapsed}
  class:expanded={isExpanded}
  aria-label="Assignment Specification & Primary Sources"
>
  {#if isCollapsed}
    <!-- Collapsed Slim Sidebar Strip with Vertical Tabs -->
    <div class="collapsed-sidebar-strip">
      <button
        type="button"
        class="collapsed-tab-btn"
        class:active={activeTab === 'assignment'}
        onclick={() => { activeTab = 'assignment'; onToggleCollapse(false); }}
        title="Open Assignment Brief"
        aria-label="Open Assignment Brief"
      >
        <span class="collapsed-tab-icon">📋</span>
      </button>

      <button
        type="button"
        class="collapsed-tab-btn"
        class:active={activeTab === 'sources'}
        onclick={() => { activeTab = 'sources'; onToggleCollapse(false); }}
        title="Open Primary Sources"
        aria-label="Open Primary Sources"
      >
        <span class="collapsed-tab-icon">📕</span>
      </button>

      <button
        type="button"
        class="btn-expand-sidebar"
        onclick={() => onToggleCollapse(false)}
        title="Expand Primary Sources"
        aria-label="Expand Primary Sources"
      >
        ▶
      </button>

      <div
        class="vertical-title"
        onclick={() => onToggleCollapse(false)}
        role="button"
        tabindex="0"
        onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggleCollapse(false); }}
      >
        {activeTab === 'assignment' ? 'ASSIGNMENT BRIEF' : 'PRIMARY SOURCES'}
      </div>
    </div>
  {:else}
    <!-- Header Bar with Dual Tabs & Controls -->
    <div class="well-header">
      <div class="sidebar-tabs-nav" role="tablist">
        <button
          type="button"
          class="sidebar-tab-btn"
          class:active={activeTab === 'assignment'}
          onclick={() => activeTab = 'assignment'}
          role="tab"
          aria-selected={activeTab === 'assignment'}
        >
          <span class="tab-icon">📋</span>
          <span class="tab-label">Assignment Brief</span>
        </button>

        <button
          type="button"
          class="sidebar-tab-btn"
          class:active={activeTab === 'sources'}
          onclick={() => activeTab = 'sources'}
          role="tab"
          aria-selected={activeTab === 'sources'}
        >
          <span class="tab-icon">📕</span>
          <span class="tab-label">Primary Sources</span>
          {#if documents.length > 0}
            <span class="tab-pill-badge">{documents.length}</span>
          {/if}
        </button>
      </div>

      <div class="well-header-actions">
        {#if activeTab === 'assignment'}
          <!-- Print / Save as PDF Button -->
          <button
            type="button"
            class="btn-header-action"
            onclick={handlePrintBrief}
            title="Save Handout as PDF / Print Brief"
            aria-label="Save Handout as PDF / Print Brief"
          >
            <span style="font-size: 13px;">🖨️</span>
          </button>
        {:else if activeDoc?.source_url}
          <!-- Print PDF Source Document -->
          <button
            type="button"
            class="btn-header-action"
            onclick={handlePrintPdf}
            title="Print PDF Document"
            aria-label="Print PDF Document"
          >
            <span style="font-size: 13px;">🖨️</span>
          </button>
          <!-- Open PDF External Fullscreen -->
          <a
            href={activeDoc.source_url}
            target="_blank"
            rel="noopener noreferrer"
            class="btn-header-action"
            title="Full screen in new tab"
            aria-label="Full screen in new tab"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 3 21 3 21 9"></polyline>
              <polyline points="9 21 3 21 3 15"></polyline>
              <line x1="21" y1="3" x2="14" y2="10"></line>
              <line x1="3" y1="21" x2="10" y2="14"></line>
            </svg>
          </a>
        {/if}

        <!-- Collapse to Left Toggle -->
        <button
          type="button"
          class="btn-collapse-toggle"
          onclick={() => onToggleCollapse(true)}
          title="Collapse sources to left"
          aria-label="Collapse sources to left"
        >
          ◀
        </button>
      </div>
    </div>

    {#if activeTab === 'assignment'}
      <AssignmentBriefHandout
        {assignment}
        {courseTitle}
        {sources}
        onSwitchToSource={switchToSource}
      />
    {:else}
      <!-- Document Switcher (if more than 1 document) -->
      {#if documents.length > 1}
        <div class="doc-switcher-bar">
          {#each documents as doc, idx}
            <button
              type="button"
              class="btn-doc-tab"
              class:active={selectedDocIndex === idx}
              onclick={() => { selectedDocIndex = idx; clearSearch(); }}
            >
              📕 {doc.title}
            </button>
          {/each}
        </div>
      {/if}

      <!-- Direct PDF Viewer Body with PDF.js and text search highlighting -->
      <div class="pdf-reader-frame-container">
        {#if activeDoc?.source_url}
          <PdfViewer
            bind:this={pdfViewerRef}
            url={activeDoc.source_url}
            title={activeDoc.title}
            searchTerm={activeSearchTerm}
            initialPage={initialViewerPage}
            {onQuoteEvidence}
            onMatchesChange={handleMatchesChange}
          />
        {:else}
          <div class="empty-doc-view">
            <span class="empty-icon">📜</span>
            <p>No PDF attached to this assignment.</p>
          </div>
        {/if}
      </div>

      <!-- Floating Bottom AI Semantic Search Bar -->
      <div class="bottom-ai-search-anchor">
        <form
          class="search-input-form"
          onsubmit={(e) => { e.preventDefault(); performSearch(); }}
        >
          <span class="search-sparkle-icon">✨</span>
          <input
            type="text"
            class="ai-search-input"
            placeholder="Search document... e.g. 'temple endowments' or 'agrarian expansion'"
            bind:value={searchQuery}
          />
          {#if matchInfo.total > 0}
            <div class="search-match-nav">
              <span class="match-count" title={matchInfo.sectionTitle ? `Page ${matchInfo.pageNum} · ${matchInfo.sectionTitle}` : `Page ${matchInfo.pageNum}`}>
                p. {matchInfo.pageNum || 1}{matchInfo.sectionTitle ? ` · ${matchInfo.sectionTitle}` : ''} ({matchInfo.current + 1} of {matchInfo.total})
              </span>
              <button
                type="button"
                class="btn-match-arrow"
                onclick={() => pdfViewerRef?.prevMatch()}
                title="Previous match (↑)"
              >
                ↑
              </button>
              <button
                type="button"
                class="btn-match-arrow"
                onclick={() => pdfViewerRef?.nextMatch()}
                title="Next match (↓)"
              >
                ↓
              </button>
            </div>
          {/if}
          {#if searchQuery}
            <button
              type="button"
              class="btn-input-clear"
              onclick={clearSearch}
              title="Clear search"
            >
              ✕
            </button>
          {/if}
          <button
            type="submit"
            class="btn-submit-search"
            disabled={!searchQuery.trim()}
            title="Search in PDF"
          >
            Search
          </button>
        </form>
      </div>
    {/if}
  {/if}
</aside>

<style>
  .evidentiary-well {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    background: var(--color-obsidian, #f8f8f5);
    border-right: 1px solid var(--color-graphite-border, #e2e4dc);
    position: relative;
    overflow: hidden;
    transition: width 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  :global([data-theme="dark"]) .evidentiary-well {
    background: var(--color-obsidian, #121418);
    border-color: var(--color-graphite-border, #262a33);
  }

  .evidentiary-well.collapsed {
    width: 48px;
    overflow: hidden;
  }

  /* Header */
  .well-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid var(--color-graphite-border, #e2e4dc);
    background: var(--color-graphite, #ffffff);
    backdrop-filter: blur(8px);
    flex-shrink: 0;
    z-index: 10;
  }

  :global([data-theme="dark"]) .well-header {
    background: var(--color-bone-surface, #1e2229);
    border-color: var(--color-graphite-border, #262a33);
  }

  /* Dual Sidebar Tabs */
  .sidebar-tabs-nav {
    display: flex;
    align-items: center;
    gap: 4px;
    background: rgba(0, 0, 0, 0.04);
    padding: 2px;
    border-radius: 8px;
  }

  :global([data-theme="dark"]) .sidebar-tabs-nav {
    background: rgba(255, 255, 255, 0.06);
  }

  .sidebar-tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 6px;
    border: none;
    background: transparent;
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--color-slate-subtle, #64748b);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .sidebar-tab-btn {
    color: #8b949e;
  }

  .sidebar-tab-btn:hover {
    color: var(--color-slate-bright, #0f172a);
  }

  :global([data-theme="dark"]) .sidebar-tab-btn:hover {
    color: #f0f6fc;
  }

  .sidebar-tab-btn.active {
    background: #ffffff;
    color: var(--color-aurora, #0284c7);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  :global([data-theme="dark"]) .sidebar-tab-btn.active {
    background: #21262d;
    color: #38bdf8;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .tab-icon {
    font-size: 0.85rem;
  }

  .tab-pill-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(2, 132, 199, 0.12);
    color: var(--color-aurora, #0284c7);
    font-size: 0.68rem;
    font-weight: 700;
    padding: 0 5px;
    border-radius: 999px;
    min-width: 16px;
    height: 16px;
  }

  :global([data-theme="dark"]) .tab-pill-badge {
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
  }

  .well-header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }

  .btn-header-action {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    color: var(--color-slate-subtle, #475569);
    border-radius: 6px;
    padding: 5px;
    width: 28px;
    height: 28px;
    font-size: 0.72rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .btn-header-action {
    border-color: #30363d;
    color: #8b949e;
  }

  .btn-header-action:hover {
    background: rgba(2, 132, 199, 0.08);
    color: var(--color-aurora, #0284c7);
    border-color: var(--color-aurora, #0284c7);
  }

  /* Collapsed Slim Sidebar Strip */
  .collapsed-sidebar-strip {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 12px 0;
    height: 100%;
    width: 48px;
    cursor: pointer;
    background: rgba(0, 0, 0, 0.02);
    user-select: none;
    box-sizing: border-box;
  }

  :global([data-theme="dark"]) .collapsed-sidebar-strip {
    background: rgba(255, 255, 255, 0.02);
  }

  .collapsed-tab-btn {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .collapsed-tab-btn:hover {
    background: rgba(0, 0, 0, 0.06);
  }

  :global([data-theme="dark"]) .collapsed-tab-btn:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .collapsed-tab-btn.active {
    background: rgba(2, 132, 199, 0.12);
    border-color: rgba(2, 132, 199, 0.3);
  }

  .collapsed-tab-icon {
    font-size: 1rem;
  }

  .btn-expand-sidebar {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    color: var(--color-slate-subtle, #64748b);
    border-radius: 4px;
    width: 26px;
    height: 26px;
    font-size: 0.65rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 4px;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-expand-sidebar {
    border-color: #30363d;
    color: #8b949e;
  }

  .btn-expand-sidebar:hover {
    color: var(--color-aurora, #0284c7);
    border-color: var(--color-aurora, #0284c7);
    background: rgba(2, 132, 199, 0.08);
  }

  .vertical-title {
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--color-slate-subtle, #64748b);
    margin-top: 16px;
    outline: none;
  }

  .btn-collapse-toggle {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    color: var(--color-slate-subtle, #475569);
    border-radius: 6px;
    padding: 5px;
    width: 28px;
    height: 28px;
    font-size: 0.65rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .btn-collapse-toggle {
    border-color: #30363d;
    color: #8b949e;
  }

  .btn-collapse-toggle:hover {
    background: rgba(2, 132, 199, 0.08);
    color: var(--color-aurora, #0284c7);
    border-color: var(--color-aurora, #0284c7);
  }

  /* Document Switcher Tabs (Multiple documents) */
  .doc-switcher-bar {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    background: rgba(0, 0, 0, 0.02);
    border-bottom: 1px solid var(--color-graphite-border, #e2e4dc);
    overflow-x: auto;
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .doc-switcher-bar {
    background: rgba(255, 255, 255, 0.02);
    border-color: #30363d;
  }

  .btn-doc-tab {
    padding: 4px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--color-slate-subtle, #64748b);
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }

  :global([data-theme="dark"]) .btn-doc-tab {
    color: #8b949e;
  }

  .btn-doc-tab:hover {
    color: var(--color-slate-bright, #0f172a);
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .btn-doc-tab:hover {
    color: #f0f6fc;
    background: rgba(255, 255, 255, 0.06);
  }

  .btn-doc-tab.active {
    background: #ffffff;
    color: var(--color-aurora, #0284c7);
    border-color: var(--color-graphite-border, #cbd5e1);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  :global([data-theme="dark"]) .btn-doc-tab.active {
    background: #21262d;
    color: #38bdf8;
    border-color: #30363d;
  }

  /* PDF Reader Frame Container */
  .pdf-reader-frame-container {
    flex: 1;
    overflow: hidden;
    position: relative;
    background: #525659;
  }

  /* Bottom Floating AI Semantic Search Bar */
  .bottom-ai-search-anchor {
    position: absolute;
    bottom: 12px;
    left: 12px;
    right: 12px;
    z-index: 25;
    pointer-events: none;
  }

  .search-input-form {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 999px;
    padding: 4px 6px 4px 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14), 0 1px 3px rgba(0, 0, 0, 0.08);
    transition: all 0.2s ease;
  }

  :global([data-theme="dark"]) .search-input-form {
    background: #1e2229;
    border-color: #30363d;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  }

  .search-input-form:focus-within {
    border-color: var(--color-aurora, #0284c7);
    box-shadow: 0 4px 20px rgba(2, 132, 199, 0.22), 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .search-sparkle-icon {
    font-size: 0.85rem;
    color: var(--color-aurora, #0284c7);
    flex-shrink: 0;
  }

  .ai-search-input {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 0.76rem;
    color: var(--color-slate-bright, #0f172a);
    outline: none;
    min-width: 0;
  }

  :global([data-theme="dark"]) .ai-search-input {
    color: #f0f6fc;
  }

  .ai-search-input::placeholder {
    color: var(--color-slate-subtle, #94a3b8);
  }

  .search-match-nav {
    display: flex;
    align-items: center;
    gap: 2px;
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 999px;
    font-size: 0.68rem;
    color: var(--color-slate-subtle, #475569);
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .search-match-nav {
    background: rgba(255, 255, 255, 0.08);
    color: #8b949e;
  }

  .match-count {
    padding: 0 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .btn-match-arrow {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 0.75rem;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    transition: background 0.12s ease;
  }

  .btn-match-arrow:hover {
    background: rgba(0, 0, 0, 0.08);
    color: var(--color-aurora, #0284c7);
  }

  :global([data-theme="dark"]) .btn-match-arrow:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #38bdf8;
  }

  .btn-input-clear {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle, #94a3b8);
    font-size: 0.8rem;
    cursor: pointer;
    padding: 0 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-input-clear:hover {
    color: var(--color-slate-bright, #0f172a);
  }

  .btn-submit-search {
    background: var(--color-aurora, #0284c7);
    color: #ffffff;
    border: none;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 0.72rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s ease;
    flex-shrink: 0;
  }

  .btn-submit-search:hover:not(:disabled) {
    background: #0369a1;
  }

  .btn-submit-search:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty-doc-view {
    text-align: center;
    padding: 40px 20px;
    color: #cbd5e1;
  }

  .empty-icon {
    font-size: 2rem;
    display: block;
    margin-bottom: 8px;
  }
</style>
