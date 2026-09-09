<script>
  let {
    module,
    index = 0,
    resources = [],
    courseId = '',
    onAddResource,
    onDeleteResource,
  } = $props();

  let unitNum = $derived(String(index + 1).padStart(2, '0'));
  let designerUrl = $derived(
    `#/designer?course_id=${encodeURIComponent(courseId)}&module_id=${encodeURIComponent(module.module_id)}`
  );
</script>

<div class="module-card">
  <!-- Unit Header -->
  <div class="module-header">
    <div class="module-title-group">
      <span class="module-index-badge">UNIT {unitNum}</span>
      <div>
        <div class="module-title">{module.title}</div>
        {#if module.description}
          <div class="module-desc">{module.description}</div>
        {/if}
      </div>
    </div>
    <div class="module-header-meta">
      <span class="module-badge-status">Active • Position {module.position}</span>
    </div>
  </div>

  <!-- Learning Objectives -->
  {#if module.learning_objectives && module.learning_objectives.length > 0}
    <div class="learning-objectives-bar">
      <span class="lo-label">Learning Objectives:</span>
      <span class="lo-content">{module.learning_objectives.join(' • ')}</span>
    </div>
  {/if}

  <!-- Grounded Readings & Primary Sources Section -->
  <div class="resources-section">
    <div class="resources-header">
      <div class="resources-header-left">
        <span style="font-size: 14px;">📚</span>
        <span class="resources-heading">GROUNDED READINGS &amp; PRIMARY SOURCES</span>
        <span class="badge badge-info">{resources.length}</span>
      </div>
      <button type="button" class="btn btn-secondary btn-xs" onclick={() => onAddResource?.(module)}>
        + Ingest Material
      </button>
    </div>

    {#if resources.length > 0}
      <div class="resources-list">
        {#each resources as r (r.chunk_id)}
          <div class="resource-item">
            <div class="resource-left">
              <span class="resource-icon">
                {r.resource_type === 'pdf' ? '📕' : r.resource_type === 'external_link' ? '🔗' : '📄'}
              </span>
              <div class="resource-details">
                <div class="resource-title-row">
                  <span class="resource-name">{r.title || 'Curriculum Material'}</span>
                  <span class="resource-type-pill {r.resource_type}">
                    {r.resource_type === 'pdf' ? 'PDF' : r.resource_type === 'external_link' ? 'Link' : 'Primary Source'}
                  </span>
                  <span class="pgvector-pill">
                    ● Grounded
                  </span>
                  {#if r.source_url}
                    <a href={r.source_url} target="_blank" rel="noopener" class="resource-link">
                      Open Link ↗
                    </a>
                  {/if}
                </div>
                <div class="resource-excerpt">
                  {r.content?.substring(0, 160)}{r.content?.length > 160 ? '...' : ''}
                </div>
              </div>
            </div>
            <div class="resource-actions">
              <button
                type="button"
                class="btn-delete"
                title="Remove this grounded resource"
                onclick={() => onDeleteResource?.(r.chunk_id)}
              >
                ✕
              </button>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="resources-empty">
        <span>No primary sources, PDFs, or external links attached to this module yet.</span>
        <button type="button" class="btn btn-secondary btn-xs" onclick={() => onAddResource?.(module)}>
          + Ingest First Material
        </button>
      </div>
    {/if}
  </div>

  <!-- Assignments List -->
  <div class="assignments-section">
    {#if module.assignments && module.assignments.length > 0}
      <div class="assignments-list">
        {#each module.assignments as a (a.assignment_id)}
          <div class="assignment-row">
            <div class="assignment-left">
              <span class="assignment-icon">⚡</span>
              <div class="assignment-info">
                <div class="assignment-name">
                  <span>{a.title || 'Assignment'}</span>
                  <span class="badge badge-success">{a.status || 'Active'}</span>
                </div>
              </div>
            </div>
            <div class="assignment-actions">
              <a href={designerUrl} class="btn btn-secondary btn-xs">
                Designer ➔
              </a>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="assignments-empty">
        <span>No assignments attached to this module yet.</span>
        <a href={designerUrl} class="btn btn-secondary btn-xs">
          + Design Assignment
        </a>
      </div>
    {/if}
  </div>
</div>

<style>
  .module-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .module-card:hover {
    border-color: rgba(59, 130, 246, 0.3);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .module-header {
    padding: 16px 22px;
    background: var(--color-graphite-card);
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .module-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .module-index-badge {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    padding: 4px 8px;
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    color: var(--color-horizon-bright);
    flex-shrink: 0;
  }

  .module-title {
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
  }

  .module-desc {
    font-size: 12px;
    color: var(--color-slate-light);
    margin-top: 2px;
  }

  .module-header-meta {
    display: flex;
    align-items: center;
  }

  .module-badge-status {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 9999px;
    background: rgba(16, 185, 129, 0.1);
    color: var(--color-signal-green);
    border: 1px solid rgba(16, 185, 129, 0.25);
  }

  .learning-objectives-bar {
    padding: 9px 22px;
    font-size: 12px;
    background: rgba(0, 0, 0, 0.2);
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .lo-label {
    color: var(--color-slate-muted);
    font-weight: 600;
  }

  .lo-content {
    color: var(--color-slate-bright);
  }

  /* Resources Section */
  .resources-section {
    padding: 14px 22px;
    background: rgba(15, 18, 25, 0.45);
    border-bottom: 1px solid var(--color-graphite-border);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .resources-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .resources-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .resources-heading {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--color-slate-bright);
    letter-spacing: 0.4px;
  }

  .resources-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .resource-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    gap: 12px;
    transition: border-color 0.15s ease;
  }

  .resource-item:hover {
    border-color: rgba(59, 130, 246, 0.35);
  }

  .resource-left {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }

  .resource-icon {
    font-size: 15px;
    margin-top: 2px;
    flex-shrink: 0;
  }

  .resource-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 0;
  }

  .resource-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .resource-name {
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
  }

  .resource-type-pill {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    padding: 2px 7px;
    border-radius: var(--radius-xs);
  }

  .resource-type-pill.pdf {
    background: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.25);
  }

  .resource-type-pill.external_link {
    background: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.25);
  }

  .resource-type-pill.primary_source,
  .resource-type-pill.document {
    background: rgba(168, 85, 247, 0.12);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.25);
  }

  .pgvector-pill {
    font-size: 10.5px;
    color: var(--color-signal-green);
    font-weight: 600;
  }

  .resource-link {
    font-size: 11px;
    color: var(--color-horizon-bright);
    text-decoration: none;
    transition: underline 0.15s ease;
  }

  .resource-link:hover {
    text-decoration: underline;
  }

  .resource-excerpt {
    font-size: 11.5px;
    color: var(--color-slate-light);
    line-height: 1.4;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .btn-delete {
    background: none;
    border: none;
    color: var(--color-slate-muted);
    font-size: 12px;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: var(--radius-xs);
    transition: all 0.15s ease;
  }

  .btn-delete:hover {
    color: var(--color-rose);
    background: rgba(239, 68, 68, 0.12);
  }

  .resources-empty {
    padding: 8px 12px;
    font-size: 12px;
    color: var(--color-slate-muted);
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* Assignments Section */
  .assignments-section {
    padding: 12px 22px;
  }

  .assignments-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .assignment-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
  }

  .assignment-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .assignment-icon {
    font-size: 15px;
    color: var(--color-horizon-bright);
  }

  .assignment-name {
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .assignments-empty {
    padding: 8px 4px;
    font-size: 12px;
    color: var(--color-slate-muted);
    font-style: italic;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .btn-xs {
    padding: 3px 9px;
    font-size: 11px;
  }
</style>
