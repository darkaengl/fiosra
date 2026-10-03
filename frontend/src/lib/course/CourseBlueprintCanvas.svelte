<script>
  let {
    currentDraft = $bindable(null),
    expandedModules = $bindable({}),
    activeCopilotModuleIndex = -1,
    onToggleModule = () => {},
    onFocusCopilotModule = () => {},
    onExpandAll = () => {},
    onCollapseAll = () => {},
    onAddEmptyModule = () => {},
    onRemoveModule = () => {},
    onAddObjective = () => {},
    onRemoveObjective = () => {},
  } = $props();
</script>

<main class="canvas-main">
  <!-- Academic Header Block (Spacious Overview & Health Metrics) -->
  {#if currentDraft}
    <div class="course-summary-card">
      <div class="summary-card-left">
        <div class="course-meta-tags">
          <span class="meta-tag tag-domain">{currentDraft.domain}</span>
          <span class="meta-tag tag-audience">{currentDraft.target_audience}</span>
          <span class="meta-tag tag-pedagogy">Bloom's Taxonomy Scaffolding</span>
        </div>
        <input
          type="text"
          class="course-title-clean"
          bind:value={currentDraft.title}
          placeholder="Course Title"
        />
        <textarea
          class="course-overview-clean"
          rows="2"
          bind:value={currentDraft.overview}
          placeholder="Course Overview and pedagogical rationale…"
        ></textarea>
      </div>

      <div class="summary-card-stats">
        <div class="stat-box">
          <span class="stat-num">{currentDraft.modules?.length || 0}</span>
          <span class="stat-lbl">Units</span>
        </div>
        <div class="stat-box">
          <span class="stat-num">
            {(currentDraft.modules || []).reduce((acc, m) => acc + (m.learning_objectives?.length || 0), 0)}
          </span>
          <span class="stat-lbl">Objectives</span>
        </div>
        <div class="stat-box">
          <span class="stat-num">
            {(currentDraft.modules || []).reduce((acc, m) => acc + (m.suggested_assignments?.length || 0), 0)}
          </span>
          <span class="stat-lbl">Inquiries</span>
        </div>
      </div>
    </div>

    <!-- Section Navigation Bar -->
    <div class="units-toolbar">
      <div class="units-count">
        <strong>{currentDraft.modules?.length || 0} Modules</strong> in Sequence
      </div>
      <div class="toolbar-actions">
        <button type="button" class="link-action" onclick={onExpandAll}>Expand All</button>
        <span class="dot-sep">·</span>
        <button type="button" class="link-action" onclick={onCollapseAll}>Collapse All</button>
        <span class="dot-sep">·</span>
        <button type="button" class="btn-add-unit" onclick={onAddEmptyModule}>+ Add Unit</button>
      </div>
    </div>

    <!-- Unit Cards (Accordion / Clean Document Flow) -->
    <div class="unit-card-list">
      {#each currentDraft.modules || [] as mod, modIdx (modIdx)}
        {@const isOpen = expandedModules[modIdx]}
        <div class="unit-card {mod.change_status ? `border-${mod.change_status}` : ''}">
          <!-- Clickable Header Bar -->
          <div
            class="unit-bar"
            role="button"
            tabindex="0"
            onclick={() => onToggleModule(modIdx)}
            onkeydown={(e) => e.key === 'Enter' && onToggleModule(modIdx)}
          >
            <div class="unit-bar-left">
              <span class="unit-pill">Unit {mod.position}</span>
              <input
                type="text"
                class="unit-title-text"
                bind:value={mod.title}
                onclick={(e) => e.stopPropagation()}
              />
              {#if mod.change_status === 'added'}
                <span class="tag-pill tag-green">Added</span>
              {:else if mod.change_status === 'modified'}
                <span class="tag-pill tag-blue">Revised</span>
              {/if}
            </div>

            <div class="unit-bar-right">
              <button
                type="button"
                class:active={activeCopilotModuleIndex === modIdx}
                class="btn-focus-copilot"
                onclick={(e) => { e.stopPropagation(); onFocusCopilotModule(modIdx); }}
              >
                Focus co-pilot
              </button>
              <span class="unit-meta-preview">
                {mod.learning_objectives?.length || 0} Objectives
              </span>
              <button
                type="button"
                class="btn-del-unit"
                title="Delete Unit"
                onclick={(e) => onRemoveModule(e, modIdx)}
              >
                🗑️
              </button>
              <span class="chevron">{isOpen ? '▲' : '▼'}</span>
            </div>
          </div>

          <!-- Collapsible Content Details (2-Column Grid) -->
          {#if isOpen}
            <div class="unit-expanded-content">
              <div class="unit-two-col-grid">
                <!-- Column 1: Scope & Learning Objectives -->
                <div class="unit-col-pedagogy">
                  <!-- Description -->
                  <div class="field-row">
                    <span class="field-title">Scope & Pedagogical Focus</span>
                    <textarea
                      class="clean-textarea-sm"
                      rows="3"
                      bind:value={mod.description}
                      placeholder="Module pedagogical scope…"
                    ></textarea>
                  </div>

                  <!-- Learning Objectives -->
                  <div class="field-row">
                    <div class="field-row-header">
                      <span class="field-title">Target Learning Objectives (Bloom's Taxonomy)</span>
                      <button type="button" class="btn-text-action" onclick={() => onAddObjective(mod)}>
                        + Add Objective
                      </button>
                    </div>
                    <div class="obj-list-clean">
                      {#each mod.learning_objectives as obj, objIdx}
                        <div class="obj-row">
                          <span class="obj-disc">›</span>
                          <input
                            type="text"
                            class="obj-text-input"
                            bind:value={mod.learning_objectives[objIdx]}
                          />
                          <button
                            type="button"
                            class="btn-remove-obj"
                            title="Remove"
                            onclick={() => onRemoveObjective(mod, objIdx)}
                          >
                            ✕
                          </button>
                        </div>
                      {/each}
                    </div>
                  </div>
                </div>

                <!-- Column 2: Socratic Assessment & Grounding -->
                <div class="unit-col-assessment">
                  <!-- Suggested Assessment Milestone -->
                  {#if mod.suggested_assignments && mod.suggested_assignments.length > 0}
                    <div class="assessment-milestone-box">
                      <div class="milestone-badge">🎯 Socratic Inquiry Assessment</div>
                      {#each mod.suggested_assignments as assign}
                        <div class="milestone-content">
                          <div class="milestone-title">{assign.title}</div>
                          <p class="milestone-desc">{assign.description}</p>
                          {#if assign.primary_sources?.length > 0}
                            <div class="source-section-lbl">Anchored Primary Sources</div>
                            <div class="source-pills">
                              {#each assign.primary_sources as src}
                                <span class="source-pill">📜 {src}</span>
                              {/each}
                            </div>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/if}

                  {#if mod.knowledge_components?.length > 0}
                    <div class="kc-box">
                      <span class="kc-title">Adaptive Knowledge Components</span>
                      <div class="kc-pills">
                        {#each mod.knowledge_components as kc}
                          <span class="kc-pill">🧠 {kc}</span>
                        {/each}
                      </div>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</main>

<style>
  .canvas-main {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .course-summary-card {
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-md, 8px);
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
  }

  .summary-card-left {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .course-meta-tags {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 2px;
  }

  .meta-tag {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    color: var(--color-slate-muted, #64748b);
  }

  .tag-domain {
    color: var(--color-aurora-bright, #0284c7);
    background: rgba(59, 130, 246, 0.08);
    border-color: rgba(59, 130, 246, 0.2);
  }

  .tag-pedagogy {
    color: #10b981;
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.2);
  }

  .summary-card-stats {
    display: flex;
    gap: 18px;
    flex-shrink: 0;
    padding-left: 24px;
    border-left: 1px solid var(--color-graphite-border, #e2e8f0);
  }

  .stat-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 60px;
  }

  .stat-num {
    font-size: 22px;
    font-weight: 700;
    color: var(--color-heading, #0f172a);
    line-height: 1.1;
  }

  .stat-lbl {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted, #64748b);
    margin-top: 2px;
  }

  .course-title-clean {
    background: transparent;
    border: none;
    color: var(--color-heading, #0f172a);
    font-size: 20px;
    font-weight: 700;
    outline: none;
    padding: 0;
    width: 100%;
  }
  .course-title-clean:focus {
    border-bottom: 1px solid var(--color-horizon-blue, #4f6bff);
  }

  .course-overview-clean {
    background: transparent;
    border: none;
    color: var(--color-slate-light, #475569);
    font-size: 13px;
    line-height: 1.5;
    outline: none;
    resize: none;
    padding: 0;
    width: 100%;
  }
  .course-overview-clean:focus {
    border-bottom: 1px solid var(--color-horizon-blue, #4f6bff);
  }

  .units-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
  }

  .units-count {
    font-size: 12.5px;
    color: var(--color-slate-muted, #64748b);
  }
  .units-count strong {
    color: var(--color-heading, #0f172a);
  }

  .toolbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
  }

  .link-action {
    background: transparent;
    border: none;
    color: var(--color-slate-muted, #64748b);
    cursor: pointer;
    font-size: 11.5px;
    padding: 0;
  }
  .link-action:hover {
    color: var(--color-heading, #0f172a);
  }

  .dot-sep {
    color: var(--color-slate-subtle, #cbd5e1);
  }

  .btn-add-unit {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    color: var(--color-slate-bright, #0f172a);
    border-radius: var(--radius-xs, 4px);
    padding: 3px 8px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-add-unit:hover {
    background: var(--pill-hover, rgba(0, 0, 0, 0.08));
  }

  .unit-card-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .unit-card {
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-md, 8px);
    overflow: hidden;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
  }
  .unit-card:hover {
    border-color: var(--color-slate-subtle, #94a3b8);
  }

  .border-added {
    border-left: 3px solid #10b981 !important;
  }

  .border-modified {
    border-left: 3px solid #3b82f6 !important;
  }

  .unit-bar {
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    background: var(--color-graphite-card, #f8fafc);
    user-select: none;
  }

  .unit-bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  .unit-pill {
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: var(--radius-xs, 4px);
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 6px;
    color: var(--color-slate-muted, #64748b);
    flex-shrink: 0;
  }

  .unit-title-text {
    background: transparent;
    border: none;
    color: var(--color-heading, #0f172a);
    font-size: 14px;
    font-weight: 600;
    outline: none;
    flex: 1;
    min-width: 0;
    cursor: text;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
  }
  .unit-title-text:focus {
    border-bottom: 1px solid var(--color-horizon-blue, #4f6bff);
    text-overflow: clip;
    overflow: visible;
  }

  .tag-pill {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 1px 6px;
    border-radius: 999px;
    flex-shrink: 0;
  }

  .tag-green {
    background: rgba(16, 185, 129, 0.15);
    color: #059669;
  }

  .tag-blue {
    background: rgba(59, 130, 246, 0.15);
    color: #2563eb;
  }

  .unit-bar-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  .btn-focus-copilot {
    background: transparent;
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: 999px;
    color: var(--color-slate-light, #475569);
    cursor: pointer;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 8px;
  }
  .btn-focus-copilot:hover, .btn-focus-copilot.active {
    background: rgba(59, 130, 246, 0.14);
    border-color: rgba(59, 130, 246, 0.5);
    color: var(--color-horizon-bright, #d97706);
  }

  .unit-meta-preview {
    font-size: 11px;
    color: var(--color-slate-muted, #64748b);
  }

  .btn-del-unit {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 11px;
    opacity: 0.6;
    padding: 2px 4px;
  }
  .btn-del-unit:hover {
    opacity: 1;
  }

  .chevron {
    font-size: 10px;
    color: var(--color-slate-muted, #64748b);
    width: 14px;
    text-align: center;
  }

  .unit-expanded-content {
    padding: 16px 20px 20px;
    border-top: 1px solid var(--color-graphite-border, #e2e8f0);
    background: var(--color-graphite, #ffffff);
  }

  .unit-two-col-grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 24px;
    align-items: start;
  }

  .unit-col-pedagogy {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .unit-col-assessment {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .field-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .field-title {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted, #64748b);
  }

  .btn-text-action {
    background: transparent;
    border: none;
    color: var(--color-aurora-bright, #0284c7);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    padding: 0;
  }
  .btn-text-action:hover {
    text-decoration: underline;
  }

  .clean-textarea-sm {
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-xs, 4px);
    padding: 10px 12px;
    font-size: 12.5px;
    color: var(--color-slate-bright, #0f172a);
    line-height: 1.5;
    outline: none;
    resize: vertical;
  }
  .clean-textarea-sm:focus {
    border-color: var(--color-horizon-blue, #4f6bff);
  }

  .obj-list-clean {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .obj-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 2px 0;
  }

  .obj-disc {
    color: var(--color-horizon-bright, #d97706);
    font-weight: 700;
    font-size: 14px;
  }

  .obj-text-input {
    flex: 1;
    background: transparent;
    border: none;
    border-bottom: 1px dashed transparent;
    color: var(--color-slate-bright, #0f172a);
    font-size: 12.5px;
    padding: 3px 0;
    outline: none;
  }
  .obj-text-input:hover, .obj-text-input:focus {
    border-bottom-color: var(--color-horizon-blue, #4f6bff);
  }

  .btn-remove-obj {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle, #94a3b8);
    cursor: pointer;
    font-size: 10px;
    padding: 2px 4px;
  }
  .btn-remove-obj:hover {
    color: var(--color-rose, #e11d48);
  }

  .assessment-milestone-box {
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-sm, 6px);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .milestone-badge {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-horizon-bright, #d97706);
    letter-spacing: 0.4px;
  }

  .milestone-title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--color-heading, #0f172a);
  }

  .milestone-desc {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-slate-light, #475569);
    margin: 2px 0 6px;
  }

  .source-section-lbl {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted, #64748b);
    margin-top: 4px;
  }

  .source-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .source-pill {
    font-size: 11px;
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: var(--radius-xs, 4px);
    padding: 3px 8px;
    color: var(--color-slate-bright, #0f172a);
  }

  .kc-box {
    background: var(--color-obsidian, #f8fafc);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: var(--radius-sm, 6px);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .kc-title {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted, #64748b);
  }

  .kc-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .kc-pill {
    font-size: 10.5px;
    background: var(--pill-bg, rgba(0, 0, 0, 0.04));
    border: 1px solid var(--pill-border, rgba(0, 0, 0, 0.08));
    border-radius: var(--radius-xs, 4px);
    padding: 3px 8px;
    color: var(--color-aurora-bright, #0284c7);
    font-family: monospace;
  }

  @media (max-width: 1100px) {
    .unit-two-col-grid {
      grid-template-columns: 1fr;
    }
    .course-summary-card {
      flex-direction: column;
      align-items: flex-start;
    }
    .summary-card-stats {
      padding-left: 0;
      border-left: none;
      border-top: 1px solid var(--color-graphite-border, #e2e8f0);
      padding-top: 12px;
      width: 100%;
      justify-content: space-around;
    }
  }
</style>
