<script>
  let {
    module,
    index = 0,
    resources = [],
    courseId = '',
    onAddResource,
    onDeleteResource,
    onDeleteAssignment,
  } = $props();

  let activeTab = $state('materials');
  let unitNum = $derived(String(index + 1).padStart(2, '0'));
  let designerUrl = $derived(
    `#/designer?course_id=${encodeURIComponent(courseId)}&module_id=${encodeURIComponent(module.module_id)}`
  );
  let hasObjectives = $derived(Boolean(module.learning_objectives?.length));
  let hasPublishedAssignment = $derived(
    Boolean(module.assignments?.some((assignment) => assignment.status === 'published'))
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
      <span class="module-badge-status">Unit {module.position}</span>
    </div>
  </div>

  <!-- Learning Objectives -->
  {#if module.learning_objectives && module.learning_objectives.length > 0}
    <div class="learning-objectives-bar">
      <span class="lo-label">Learning Objectives:</span>
      <span class="lo-content">{module.learning_objectives.join(' • ')}</span>
    </div>
  {/if}

  <div class="readiness-bar" aria-label="Module setup readiness">
    <span class:complete={hasObjectives}>Objectives {hasObjectives ? 'mapped' : 'needed'}</span>
    <span class:complete={resources.length > 0}>Sources {resources.length > 0 ? 'grounded' : 'needed'}</span>
    <span class:complete={hasPublishedAssignment}>Student task {hasPublishedAssignment ? 'published' : 'not published'}</span>
  </div>

  <!-- Materials / Assignments tab switch -->
  <div class="unit-tabs" role="tablist">
    <button
      type="button"
      role="tab"
      aria-selected={activeTab === 'materials'}
      class:active={activeTab === 'materials'}
      onclick={() => (activeTab = 'materials')}
    >
      📚 Materials
      <span class="badge badge-info">{resources.length}</span>
    </button>
    <button
      type="button"
      role="tab"
      aria-selected={activeTab === 'assignments'}
      class:active={activeTab === 'assignments'}
      onclick={() => (activeTab = 'assignments')}
    >
      ⚡ Assignments
      <span class="badge badge-info">{module.assignments?.length || 0}</span>
    </button>
  </div>

  {#if activeTab === 'materials'}
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
                  <span class="pgvector-pill">● Grounded source</span>
                  <span class:unmapped={!r.kc_id} class="kc-pill">{r.kc_id ? `KC: ${r.kc_id}` : 'KC mapping pending'}</span>
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
  {:else}
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
              {#if a.status === 'published'}
                <a
                  href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(a.assignment_id)}`}
                  class="btn btn-primary btn-xs"
                >
                  Student canvas →
                </a>
              {/if}
              <button
                type="button"
                class="btn-delete"
                title="Delete this assignment"
                onclick={() => onDeleteAssignment?.(a.assignment_id, a.title)}
              >
                ✕
              </button>
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
  {/if}
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
    color: var(--color-heading);
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
    background: var(--color-signal-green-bg);
    color: var(--color-signal-green);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .learning-objectives-bar {
    padding: 9px 22px;
    font-size: 12px;
    background: var(--pill-bg);
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

  .readiness-bar {
    padding: 9px 22px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--color-graphite-border);
    background: var(--pill-bg);
  }

  .readiness-bar span {
    color: var(--color-slate-muted);
    font-size: 10.5px;
  }

  .readiness-bar span::before {
    content: '○';
    margin-right: 4px;
  }

  .readiness-bar span.complete { color: var(--color-signal-green); }
  .readiness-bar span.complete::before { content: '●'; }

  /* Materials / Assignments tab switch */
  .unit-tabs {
    display: flex;
    gap: 2px;
    padding: 0 22px;
    background: var(--color-graphite-card);
    border-bottom: 1px solid var(--color-graphite-border);
  }

  .unit-tabs button {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--color-slate-muted);
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease;
  }

  .unit-tabs button:hover {
    color: var(--color-slate-bright);
  }

  .unit-tabs button.active {
    color: var(--color-heading);
    border-bottom-color: var(--color-horizon-blue);
  }

  /* Resources Section */
  .resources-section {
    padding: 14px 22px;
    background: var(--color-graphite-card);
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
    border-color: var(--color-horizon-blue);
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
    color: var(--color-heading);
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
    background: var(--color-rose-bg);
    color: var(--color-rose-text);
    border: 1px solid var(--color-rose);
  }

  .resource-type-pill.external_link {
    background: var(--pill-active-bg);
    color: var(--color-horizon-bright);
    border: 1px solid var(--pill-active-border);
  }

  .resource-type-pill.primary_source,
  .resource-type-pill.document {
    background: var(--pill-active-bg);
    color: var(--color-horizon-bright);
    border: 1px solid var(--pill-active-border);
  }

  .pgvector-pill {
    font-size: 10.5px;
    color: var(--color-signal-green);
    font-weight: 600;
  }

  .kc-pill {
    color: var(--color-horizon-bright);
    font-size: 10px;
    font-weight: 600;
  }

  .kc-pill.unmapped { color: var(--color-amber); }

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
    background: var(--color-rose-bg);
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
    color: var(--color-heading);
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
