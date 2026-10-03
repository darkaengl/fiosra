<script lang="ts">
  let {
    contract = $bindable(),
    courseDocuments = [],
    onAddSource = () => {},
    onRemoveSource = (index: number) => {},
    onAttachCourseDoc = (doc: any) => {},
    onViewPdf = (pdf: { title: string; url: string }) => {},
  } = $props<{
    contract: any;
    courseDocuments?: any[];
    onAddSource?: () => void;
    onRemoveSource?: (index: number) => void;
    onAttachCourseDoc?: (doc: any) => void;
    onViewPdf?: (pdf: { title: string; url: string }) => void;
  }>();
</script>

<section class="card-section">
  <div class="card-header space-between">
    <div>
      <div class="header-tag">02 · PRIMARY EVIDENCE</div>
      <h2>Grounded Materials &amp; Assigned Readings</h2>
      <p class="section-desc">Students analyze these specific documents on their canvas to support their arguments.</p>
    </div>
    <button type="button" class="btn-secondary btn-sm" onclick={onAddSource}>
      + Add Custom Source
    </button>
  </div>

  <!-- Uploaded Course Documents Quick Attach Bar -->
  {#if courseDocuments.length > 0}
    <div class="course-docs-bar">
      <span class="bar-title">Course Documents available for this unit:</span>
      <div class="docs-chip-list">
        {#each courseDocuments as doc}
          <div class="doc-chip">
            <span class="doc-icon">📕</span>
            <span class="doc-name">{doc.title || doc.filename}</span>
            <button
              type="button"
              class="chip-attach-btn"
              title="Attach this document to assignment source pack"
              onclick={() => onAttachCourseDoc(doc)}
            >
              + Attach
            </button>
            <button
              type="button"
              class="chip-read-btn"
              title="Open PDF reader"
              onclick={() => onViewPdf({ title: doc.title, url: doc.download_url })}
            >
              Read PDF ↗
            </button>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Source Cards List -->
  <div class="sources-list">
    {#each contract.source_pack as source, index}
      <div class="source-card-item">
        <div class="source-card-header">
          <span class="source-index">#{index + 1}</span>
          <input
            class="source-title-input"
            bind:value={source.title}
            placeholder="Source Title / Inscription / Report"
          />
          <div class="source-actions">
            {#if source.source_url}
              <button
                type="button"
                class="btn-text-action"
                onclick={() => onViewPdf({ title: source.title, url: source.source_url })}
              >
                View Source ↗
              </button>
            {/if}
            <button
              type="button"
              class="btn-delete-item"
              title="Remove source"
              onclick={() => onRemoveSource(index)}
            >
              ✕
            </button>
          </div>
        </div>

        <div class="source-card-body">
          <div class="form-group">
            <label>Relevance &amp; Guidance for Student</label>
            <input
              class="input-text"
              bind:value={source.relevance_guidance}
              placeholder="Why is this assigned? What should students look for in this text?"
            />
          </div>
          <div class="form-group">
            <label>Authentic Excerpt / Passage</label>
            <textarea
              class="input-textarea"
              rows="3"
              bind:value={source.excerpt}
              placeholder="Paste key passages, archival excerpts, or translation text..."
            ></textarea>
          </div>
        </div>
      </div>
    {:else}
      <div class="empty-placeholder">
        <p>No primary sources attached yet. Click <strong>+ Add Custom Source</strong> or attach an uploaded PDF from the bar above.</p>
      </div>
    {/each}
  </div>
</section>

<style>
  .card-section {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  :global(.dark-mode) .card-section {
    background: #181b20;
    border-color: #2a2e36;
  }

  .card-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-bottom: 1px solid var(--border, #DDDCD5);
    padding-bottom: 16px;
  }

  :global(.dark-mode) .card-header {
    border-color: #2a2e36;
  }

  .space-between {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
  }

  .header-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .card-header h2 {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 2px 0 0;
  }

  :global(.dark-mode) .card-header h2 {
    color: #f1f5f9;
  }

  .section-desc {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
    margin: 0;
  }

  :global(.dark-mode) .section-desc {
    color: #94a3b8;
  }

  .btn-secondary {
    display: inline-flex;
    align-items: center;
    background: transparent;
    border: 1px solid var(--border, #DDDCD5);
    color: var(--color-heading, #111315);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  :global(.dark-mode) .btn-secondary {
    border-color: #2e3440;
    color: #f1f5f9;
  }

  .btn-secondary:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
    border-color: #C5C4BE;
  }

  :global(.dark-mode) .btn-secondary:hover {
    background: #232832;
  }

  .btn-sm {
    padding: 6px 12px;
    font-size: 12px;
  }

  .course-docs-bar {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :global(.dark-mode) .course-docs-bar {
    background: #111317;
    border-color: #2a2e36;
  }

  .bar-title {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate, #6D7378);
  }

  .docs-chip-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .doc-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
  }

  :global(.dark-mode) .doc-chip {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .doc-name {
    font-weight: 600;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .doc-name {
    color: #f1f5f9;
  }

  .chip-attach-btn,
  .chip-read-btn {
    background: none;
    border: none;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
    padding: 0;
  }

  .chip-attach-btn {
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .chip-read-btn {
    color: var(--color-slate, #6D7378);
  }

  .sources-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .source-card-item {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  :global(.dark-mode) .source-card-item {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .source-card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid var(--border, #DDDCD5);
    padding-bottom: 10px;
  }

  :global(.dark-mode) .source-card-header {
    border-color: #2a2e36;
  }

  .source-index {
    font-size: 11px;
    font-weight: 800;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .source-title-input {
    flex: 1;
    font-size: 14px;
    font-weight: 700;
    border: none;
    outline: none;
    background: transparent;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .source-title-input {
    color: #f1f5f9;
  }

  .source-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .btn-text-action {
    background: none;
    border: none;
    font-size: 12px;
    font-weight: 600;
    color: var(--color-horizon-blue, #4F6BFF);
    cursor: pointer;
  }

  .btn-delete-item {
    background: none;
    border: none;
    color: var(--color-slate, #6D7378);
    font-size: 14px;
    cursor: pointer;
  }
  .btn-delete-item:hover {
    color: #e11d48;
  }

  .source-card-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-group label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate, #6D7378);
  }

  .input-text,
  .input-textarea {
    width: 100%;
    padding: 8px 12px;
    font-size: 13px;
    font-family: inherit;
    border-radius: 6px;
    border: 1px solid var(--border, #DDDCD5);
    background: var(--input-bg, #ffffff);
    color: var(--color-heading, #111315);
    box-sizing: border-box;
  }

  :global(.dark-mode) .input-text,
  :global(.dark-mode) .input-textarea {
    background: #111317;
    border-color: #2e3440;
    color: #f1f5f9;
  }

  .empty-placeholder {
    padding: 24px;
    text-align: center;
    border: 1px dashed var(--border, #DDDCD5);
    border-radius: 8px;
    color: var(--color-slate, #6D7378);
    font-size: 13px;
  }
</style>
