<script lang="ts">
  let {
    courseId = '',
    modules = [],
    activeAssignment = null,
  } = $props<{
    courseId?: string;
    modules?: any[];
    activeAssignment?: any;
  }>();

  let expandedModules = $state<Set<string>>(new Set());

  // Expand first module by default when modules are loaded
  $effect(() => {
    if (modules && modules.length > 0 && expandedModules.size === 0) {
      expandedModules = new Set([modules[0].module_id]);
    }
  });

  function toggleModule(modId: string) {
    const next = new Set(expandedModules);
    if (next.has(modId)) {
      next.delete(modId);
    } else {
      next.add(modId);
    }
    expandedModules = next;
  }

  function expandAllModules() {
    expandedModules = new Set(modules.map((m: any) => m.module_id));
  }

  function collapseAllModules() {
    expandedModules = new Set();
  }
</script>

<section class="curriculum-section">
  <div class="section-title-row">
    <div>
      <span class="eyebrow-text">COURSE STRUCTURE</span>
      <h2 class="section-headline">Sequential Curriculum &amp; Inquiries</h2>
    </div>
    <div class="accordion-controls">
      <button class="btn-text-action" onclick={expandAllModules}>Expand All</button>
      <span class="dot-sep">•</span>
      <button class="btn-text-action" onclick={collapseAllModules}>Collapse All</button>
    </div>
  </div>

  {#if modules.length === 0}
    <div class="empty-modules-notice">
      <p>No modules have been published for this course yet.</p>
    </div>
  {:else}
    <div class="modules-accordion-stack">
      {#each modules as mod, mIdx (mod.module_id || mIdx)}
        {@const isExpanded = expandedModules.has(mod.module_id)}
        {@const isFirst = mIdx === 0}
        {@const assignCount = mod.assignments ? mod.assignments.length : 0}

        <div class="module-panel" class:expanded={isExpanded} class:is-active-module={isFirst}>
          <!-- Module Header Accordion Trigger -->
          <button
            type="button"
            class="module-panel-header"
            onclick={() => toggleModule(mod.module_id)}
            aria-expanded={isExpanded}
          >
            <div class="panel-header-left">
              <span class="mod-step-pill" class:step-active={isFirst}>
                MODULE {mod.position || (mIdx + 1)}
              </span>
              <div class="mod-header-text">
                <h3 class="mod-title">{mod.title}</h3>
                {#if mod.description}
                  <p class="mod-desc-preview">{mod.description}</p>
                {/if}
              </div>
            </div>

            <div class="panel-header-right">
              <span class="assign-count-badge">
                {assignCount} {assignCount === 1 ? 'Assignment' : 'Assignments'}
              </span>
              <span class="module-status-pill {isFirst ? 'status-active' : 'status-upcoming'}">
                {isFirst ? 'Active Unit' : (mod.is_locked ? 'Locked' : 'Open')}
              </span>
              <span class="chevron-icon">{isExpanded ? '▾' : '▸'}</span>
            </div>
          </button>

          <!-- Collapsible Module Body -->
          {#if isExpanded}
            <div class="module-panel-body">
              <!-- Learning Objectives -->
              {#if mod.learning_objectives && mod.learning_objectives.length > 0}
                <div class="objectives-strip">
                  <span class="obj-label">Pedagogical Objectives:</span>
                  <div class="obj-tags-list">
                    {#each mod.learning_objectives as obj}
                      <span class="obj-tag">🎯 {obj}</span>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Assignments in this Module -->
              <div class="assignments-list-container">
                <div class="assign-list-header">
                  <span>Assigned Deliverables &amp; Reasoning Tasks</span>
                  <span>Status &amp; Action</span>
                </div>

                {#if !mod.assignments || mod.assignments.length === 0}
                  <div class="no-assignments-hint">
                    No assignments published in this module yet.
                  </div>
                {:else}
                  <div class="assignments-cards-grid">
                    {#each mod.assignments as assign, aIdx (assign.assignment_id || aIdx)}
                      {@const isActiveThis = activeAssignment && activeAssignment.assignment_id === assign.assignment_id}
                      <div class="assignment-row-card" class:is-active-task={isActiveThis}>
                        <div class="assign-card-main">
                          <div class="assign-meta-top">
                            <span class="assign-num-badge">Task {mIdx + 1}.{aIdx + 1}</span>
                            {#if isActiveThis}
                              <span class="badge badge-success">Active Now</span>
                            {:else if assign.status === 'published'}
                              <span class="badge badge-info">Available</span>
                            {:else}
                              <span class="badge badge-neutral">Draft</span>
                            {/if}
                          </div>

                          <h4 class="assign-card-title">{assign.title}</h4>
                          {#if assign.summary}
                            <p class="assign-card-summary">{assign.summary}</p>
                          {/if}

                          <div class="assign-card-tags">
                            {#if assign.rubric_count}
                              <span class="card-mini-tag">⚖️ {assign.rubric_count} Rubric Criteria</span>
                            {/if}
                            <span class="card-mini-tag">📝 Socratic Evidence Workspace</span>
                          </div>
                        </div>

                        <div class="assign-card-action">
                          {#if isActiveThis}
                            <a
                              href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assign.assignment_id)}`}
                              class="btn btn-primary btn-open-canvas"
                            >
                              Resume Canvas →
                            </a>
                          {:else}
                            <a
                              href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assign.assignment_id)}`}
                              class="btn btn-secondary btn-open-canvas"
                            >
                              Open Assignment →
                            </a>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</section>

<style>
  .curriculum-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .section-title-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .eyebrow-text {
    font-size: 10.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .section-headline {
    font-size: 19px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 4px 0 0;
  }

  .accordion-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-text-action {
    background: none;
    border: none;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-horizon-blue, #4F6BFF);
    cursor: pointer;
    padding: 0;
  }
  .btn-text-action:hover {
    text-decoration: underline;
  }

  .dot-sep {
    color: var(--color-cloud, #E9E8E3);
  }

  .empty-modules-notice {
    padding: 32px;
    text-align: center;
    background: var(--surface, #ffffff);
    border: 1px dashed var(--border, #DDDCD5);
    border-radius: 8px;
    color: var(--color-slate, #6D7378);
    font-size: 13.5px;
  }

  .modules-accordion-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .module-panel {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    overflow: hidden;
    transition: border-color 0.15s ease;
  }

  .module-panel.is-active-module {
    border-color: #C9D7FF;
  }

  .module-panel-header {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: transparent;
    border: none;
    cursor: pointer;
    text-align: left;
    gap: 16px;
    transition: background 0.1s ease;
  }

  .module-panel-header:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
  }

  .panel-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
    min-width: 0;
  }

  .mod-step-pill {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: var(--color-slate, #6D7378);
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    padding: 3px 8px;
    border-radius: 4px;
    white-space: nowrap;
  }

  .mod-step-pill.step-active {
    color: #ffffff;
    background: var(--color-horizon-blue, #4F6BFF);
    border-color: var(--color-horizon-blue, #4F6BFF);
  }

  .mod-header-text {
    flex: 1;
    min-width: 0;
  }

  .mod-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 0;
    line-height: 1.3;
  }

  .mod-desc-preview {
    font-size: 12px;
    color: var(--color-slate, #6D7378);
    margin: 3px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 520px;
  }

  .panel-header-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }

  .assign-count-badge {
    font-size: 11.5px;
    color: var(--color-slate, #6D7378);
    font-weight: 500;
  }

  .module-status-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
  }

  .status-active {
    background: #EBF7F0;
    border: 1px solid rgba(95, 175, 122, 0.3);
    color: #2D6340;
  }

  .status-upcoming {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    color: var(--color-slate, #6D7378);
  }

  .chevron-icon {
    font-size: 13px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .module-panel-body {
    border-top: 1px solid var(--border, #DDDCD5);
    padding: 16px 20px 20px;
    background: #fafaf8;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .objectives-strip {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 10px 14px;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 6px;
  }

  .obj-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .obj-tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .obj-tag {
    font-size: 11.5px;
    color: var(--color-heading, #111315);
    background: var(--color-cloud-subtle, #F0EFEA);
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid var(--border, #DDDCD5);
  }

  .assignments-list-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .assign-list-header {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-subtle, #8A9096);
    padding: 0 4px;
  }

  .no-assignments-hint {
    padding: 16px;
    font-size: 12.5px;
    color: var(--color-slate, #6D7378);
    font-style: italic;
  }

  .assignments-cards-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .assignment-row-card {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 6px;
    padding: 14px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    transition: all 0.15s ease;
  }

  .assignment-row-card.is-active-task {
    border-left: 3px solid var(--color-horizon-blue, #4F6BFF);
    background: #FCFDFF;
  }

  .assignment-row-card:hover {
    border-color: #C5C4BE;
  }

  .assign-card-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .assign-meta-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .assign-num-badge {
    font-size: 10px;
    font-weight: 700;
    color: var(--color-slate, #6D7378);
    text-transform: uppercase;
  }

  .badge {
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .badge-success {
    background: #EBF7F0;
    color: #2D6340;
    border: 1px solid rgba(95, 175, 122, 0.4);
  }

  .badge-info {
    background: #EBF0FF;
    color: var(--color-horizon-blue, #4F6BFF);
    border: 1px solid #C9D7FF;
  }

  .badge-neutral {
    background: var(--color-cloud-subtle, #F0EFEA);
    color: var(--color-slate, #6D7378);
    border: 1px solid var(--border, #DDDCD5);
  }

  .assign-card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-heading, #111315);
    margin: 0;
  }

  .assign-card-summary {
    font-size: 12px;
    color: var(--color-slate, #6D7378);
    margin: 0;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 600px;
  }

  .assign-card-tags {
    display: flex;
    gap: 8px;
    margin-top: 4px;
  }

  .card-mini-tag {
    font-size: 10.5px;
    color: var(--color-slate, #6D7378);
    background: var(--color-cloud-subtle, #F0EFEA);
    padding: 1px 6px;
    border-radius: 3px;
  }

  .assign-card-action {
    flex-shrink: 0;
  }

  .btn {
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
  }

  .btn-primary {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
    border: none;
  }
  .btn-primary:hover {
    background: #3B57E8;
  }

  .btn-secondary {
    background: #ffffff;
    border: 1px solid var(--border, #DDDCD5);
    color: var(--color-heading, #111315);
  }
  .btn-secondary:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
  }
</style>
