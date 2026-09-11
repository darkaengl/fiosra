<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { responseError, routeParams } from '../lib/session.js';

  // Intake State
  let materialsText = $state('');
  let titleHint = $state('');
  let selectedDomain = $state('History');
  let targetAudience = $state('Undergraduate');
  let authorId = $state('prof_educator');

  // Draft State
  let currentDraft = $state(null);
  let revisionHistory = $state([]);
  let latestChangeSummary = $state('');
  let revisionCount = $state(0);
  let expandedModules = $state({ 0: true }); // By default expand unit 1

  // UI / Async State
  let isGenerating = $state(false);
  let isRevising = $state(false);
  let isPublishing = $state(false);
  let reviewComment = $state('');
  let notice = $state('');
  let error = $state('');
  let showCritiqueChips = $state(true);
  let activeCopilotModuleIndex = $state(-1);
  let copilotCollapsed = $state(false);
  let currentCopilotModule = $derived(
    activeCopilotModuleIndex >= 0 ? currentDraft?.modules?.[activeCopilotModuleIndex] : null,
  );

  const quickPrompts = [
    "Align learning objectives with Bloom's Taxonomy verbs",
    "Add more primary source inquiry tasks across units",
    "Insert an introductory module on historical methodology",
    "Split complex multi-theme modules into focused units",
    "Emphasize institutional constraints & debate interpretations",
  ];

  const SAMPLE_SYLLABUS = `Course: HI4083: Early Modern Ireland, 1536-1750
Instructor: Dr. Vance · Department of History

Course Overview:
This course examines the political, religious, and economic transformation of Ireland from the Tudor conquests through the Williamite settlement. Students will analyze primary sources including state papers, plantation surveys, and Gaelic poetry to interrogate how institutional policies shaped early modern society.

Unit 1: The Tudor Reconquest & Surrender and Regrant (1536-1603)
- Analyze the constitutional shift from lordship to sovereign kingdom.
- Evaluate Gaelic resistance and the culmination of the Nine Years' War.
- Primary Source: The Nine Years' War State Papers & Hugh O'Neill's Articles.

Unit 2: The Plantation Schemes & Confessional Division (1603-1641)
- Examine demographic restructuring during the Ulster Plantation.
- Investigate legal land confiscation and rising tensions.
- Primary Source: 1641 Depositions (Trinity College Dublin archives).

Unit 3: Cromwellian Conquest & Restoration Settlement (1649-1685)
- Assess the impact of the Act for the Settlement of Ireland (1652).
- Critique cartographic survey methods as instruments of state power.
- Primary Source: Sir William Petty's Down Survey maps and diaries.

Unit 4: The Williamite Settlement & The Penal Era (1689-1750)
- Interrogate the Treaty of Limerick and structural economic statutes.
- Socratic Task: Did early modern legislation primarily target religious conformity or economic hegemony?
- Primary Source: The Penal Code Statutes (1695-1704).`;

  function loadSample() {
    titleHint = 'HI4083: Early Modern Ireland, 1536-1750';
    selectedDomain = 'History';
    targetAudience = 'Undergraduate';
    materialsText = SAMPLE_SYLLABUS;
  }

  async function handleSynthesizeDraft() {
    if (!materialsText.trim()) return;
    isGenerating = true;
    error = '';
    notice = '';
    try {
      const res = await fetch('/authoring/courses/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          materials_text: materialsText.trim(),
          title_hint: titleHint.trim() || null,
          domain: selectedDomain,
          author_id: authorId.trim() || 'prof_educator',
        }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Course draft synthesis failed.'));
      currentDraft = await res.json();
      revisionCount = 1;
      expandedModules = { 0: true };
      activeCopilotModuleIndex = 0;
      revisionHistory = [
        {
          role: 'assistant',
          content: `Synthesized course blueprint "${currentDraft.title}" with ${currentDraft.modules.length} scaffolded units.`,
        },
      ];
      notice = 'Course blueprint synthesized! Click any unit to inspect or refine with the Co-Pilot.';
    } catch (err) {
      error = err.message || 'Failed to synthesize course draft.';
    } finally {
      isGenerating = false;
    }
  }

  async function handleApplyRevision(promptText) {
    const commentToSend = promptText || reviewComment.trim();
    if (!commentToSend || !currentDraft) return;
    isRevising = true;
    error = '';
    notice = '';
    try {
      revisionHistory.push({ role: 'user', content: commentToSend });
      const res = await fetch('/authoring/courses/revise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_draft: currentDraft,
          review_comments: commentToSend,
          target_module_index: activeCopilotModuleIndex >= 0 ? activeCopilotModuleIndex : null,
          conversation_history: revisionHistory,
        }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Failed to revise course draft.'));
      const data = await res.json();
      currentDraft = data.revised_draft;
      latestChangeSummary = data.changes_summary;
      revisionCount = data.revision_count || revisionCount + 1;
      revisionHistory.push({
        role: 'assistant',
        content: data.changes_summary,
      });
      reviewComment = '';
      notice = 'Draft updated based on feedback. Revised sections are highlighted.';
    } catch (err) {
      error = err.message || 'Failed to apply revisions.';
    } finally {
      isRevising = false;
    }
  }

  async function handlePublishCourse() {
    if (!currentDraft) return;
    isPublishing = true;
    error = '';
    notice = '';
    try {
      const res = await fetch('/authoring/courses/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          draft: currentDraft,
          author_id: authorId.trim() || 'prof_educator',
        }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Failed to publish course.'));
      const published = await res.json();
      notice = `Course published! Opening curriculum view…`;
      setTimeout(() => {
        push(`/modules?course_id=${encodeURIComponent(published.course_id)}`);
      }, 750);
    } catch (err) {
      error = err.message || 'Course publication failed.';
    } finally {
      isPublishing = false;
    }
  }

  function toggleModule(idx) {
    expandedModules[idx] = !expandedModules[idx];
  }

  function focusCopilotModule(idx) {
    activeCopilotModuleIndex = idx;
    expandedModules[idx] = true;
    copilotCollapsed = false;
  }

  function expandAll() {
    const all = {};
    currentDraft?.modules?.forEach((_, i) => (all[i] = true));
    expandedModules = all;
  }

  function collapseAll() {
    expandedModules = {};
  }

  function addEmptyModule() {
    if (!currentDraft) return;
    const pos = currentDraft.modules.length + 1;
    const newIdx = currentDraft.modules.length;
    currentDraft.modules = [
      ...currentDraft.modules,
      {
        title: `Unit ${pos}: New Curriculum Topic`,
        description: 'Describe the pedagogical scope and inquiries for this module.',
        learning_objectives: ['Formulate clear analytical claims', 'Evaluate primary evidence'],
        position: pos,
        knowledge_components: [`KC_${currentDraft.domain.toUpperCase()}_UNIT_${pos}`],
        suggested_assignments: [
          {
            title: `Unit ${pos} Analytical Task`,
            description: 'Inquiry assignment exploring core unit themes.',
            primary_sources: ['Selected Primary Source Document'],
          },
        ],
        change_status: 'added',
      },
    ];
    expandedModules[newIdx] = true;
  }

  function removeModule(e, index) {
    e.stopPropagation();
    if (!currentDraft) return;
    currentDraft.modules = currentDraft.modules.filter((_, i) => i !== index);
    currentDraft.modules.forEach((mod, i) => {
      mod.position = i + 1;
    });
  }

  function addObjective(mod) {
    mod.learning_objectives = [...(mod.learning_objectives || []), 'Demonstrate critical analysis of core primary sources'];
  }

  function removeObjective(mod, idx) {
    mod.learning_objectives = mod.learning_objectives.filter((_, i) => i !== idx);
  }

  onMount(() => {
    const queryIndex = window.location.hash.indexOf('?');
    if (queryIndex < 0) return;
    const params = new URLSearchParams(window.location.hash.slice(queryIndex + 1));
    if (params.get('assistant') !== 'course') return;
    const direction = params.get('assistant_instruction') || '';
    if (direction) {
      titleHint = 'AI-assisted course design';
      materialsText = `Educator design direction:\n${direction}`;
      notice = 'The AI Design Assistant added your direction to the course studio. Review or expand it, then synthesize the editable curriculum draft.';
    }
  });
</script>

<div class="studio-shell">
  <!-- Minimalist Clean Top Header -->
  <header class="studio-topbar">
    <div class="topbar-breadcrumb">
      <button type="button" class="nav-back-link" onclick={() => push('/courses')}>
        ← Courses
      </button>
      <span class="sep">/</span>
      <span class="current-crumb">
        {currentDraft ? currentDraft.title : 'Curriculum Architect'}
      </span>
      {#if currentDraft}
        <span class="badge-revision">v{revisionCount}</span>
      {/if}
    </div>

    {#if currentDraft}
      <div class="topbar-actions">
        <button
          type="button"
          class="btn-ghost"
          onclick={() => { currentDraft = null; revisionHistory = []; }}
        >
          Reset
        </button>
        <button
          type="button"
          class="btn-publish"
          disabled={isPublishing}
          onclick={handlePublishCourse}
        >
          {#if isPublishing}
            Publishing…
          {:else}
            🚀 Approve & Publish
          {/if}
        </button>
      </div>
    {/if}
  </header>

  <!-- Quiet Toast Feedback -->
  {#if notice}
    <div class="toast toast-info">
      <span>💡 {notice}</span>
      <button type="button" class="toast-close" onclick={() => (notice = '')}>✕</button>
    </div>
  {/if}
  {#if error}
    <div class="toast toast-error">
      <span>⚠️ {error}</span>
      <button type="button" class="toast-close" onclick={() => (error = '')}>✕</button>
    </div>
  {/if}

  <!-- STAGE 1: Full-Width 2-Column Studio Intake View -->
  {#if !currentDraft}
    <div class="intake-studio-grid">
      <!-- Left Column: Architect Guidance, Standards & Quick Presets -->
      <aside class="intake-sidebar">
        <div class="intake-intro-card">
          <div class="badge-spark">✨ AI Curriculum Architect</div>
          <h2>Socratic Course Studio</h2>
          <p class="intake-desc">
            Transform raw course syllabi, lecture schedules, and reading lists into a scaffolded, inquiry-driven curriculum with Bloom's-aligned learning objectives.
          </p>
        </div>

        <div class="intake-methodology-card">
          <div class="method-header">Pedagogical Standards</div>
          <div class="method-item">
            <span class="method-icon">📐</span>
            <div>
              <strong>Progressive Inquiry Scaffolding</strong>
              <p>Sequences modules from foundational framing to structural debate and evidentiary synthesis.</p>
            </div>
          </div>
          <div class="method-item">
            <span class="method-icon">🎯</span>
            <div>
              <strong>Bloom's Taxonomy Objectives</strong>
              <p>Synthesizes active, measurable cognitive verbs for verifiable student progression.</p>
            </div>
          </div>
          <div class="method-item">
            <span class="method-icon">📜</span>
            <div>
              <strong>Authentic Primary Evidence</strong>
              <p>Anchors Socratic inquiry assignments directly in historical texts and artifact readings.</p>
            </div>
          </div>
        </div>

        <div class="intake-presets-card">
          <span class="presets-header">Quick Starter Presets</span>
          <button type="button" class="preset-pill-btn" onclick={loadSample}>
            <div class="preset-info">
              <span class="preset-name">📜 Early Modern Ireland (1536–1750)</span>
              <span class="preset-sub">History & Historiography · Undergraduate</span>
            </div>
            <span class="preset-action">Load Sample →</span>
          </button>
        </div>
      </aside>

      <!-- Right Column: Materials Workbench Form -->
      <div class="intake-workbench-card">
        <div class="workbench-header">
          <div>
            <h3>Course Parameters & Syllabus Source</h3>
            <span class="workbench-sub">Paste syllabus content, lecture schedules, or reading references to synthesize an initial draft</span>
          </div>
          <button type="button" class="btn-sample-link" onclick={loadSample}>
            ⚡ Insert Sample Syllabus
          </button>
        </div>

        <div class="intake-body">
          <div class="form-grid-top">
            <div class="input-wrap title-wrap">
              <label for="course-title-hint">Course Title or Identifier</label>
              <input
                id="course-title-hint"
                type="text"
                class="clean-input"
                placeholder="e.g. HI4083: Early Modern Ireland, 1536-1750"
                bind:value={titleHint}
              />
            </div>

            <div class="input-wrap">
              <label for="course-domain">Academic Discipline</label>
              <select id="course-domain" class="clean-select" bind:value={selectedDomain}>
                <option value="History">History</option>
                <option value="Economics">Economics</option>
                <option value="Literature">Literature</option>
                <option value="Philosophy">Philosophy</option>
                <option value="Social Sciences">Social Sciences</option>
              </select>
            </div>

            <div class="input-wrap">
              <label for="target-audience">Academic Level</label>
              <select id="target-audience" class="clean-select" bind:value={targetAudience}>
                <option value="Undergraduate">Undergraduate</option>
                <option value="Advanced Undergraduate">Advanced Seminar</option>
                <option value="Graduate">Graduate</option>
              </select>
            </div>
          </div>

          <div class="textarea-wrap">
            <div class="textarea-label-row">
              <label for="materials-input">Syllabus Text, Weekly Modules & Reading References</label>
            </div>
            <textarea
              id="materials-input"
              class="clean-textarea"
              rows="12"
              placeholder="Paste course syllabus, lecture units, primary source reading links, or learning goals here…"
              bind:value={materialsText}
            ></textarea>
          </div>

          <div class="workbench-footer">
            <div class="workbench-note">
              💡 Fiosra synthesizes an editable curriculum draft that you can iteratively critique and refine with the AI Co-Pilot.
            </div>
            <button
              type="button"
              class="btn-synthesize"
              disabled={isGenerating || !materialsText.trim()}
              onclick={handleSynthesizeDraft}
            >
              {#if isGenerating}
                <span class="spinner-sm"></span> Synthesizing Course Blueprint…
              {:else}
                ✨ Synthesize Course Draft with AI
              {/if}
            </button>
          </div>
        </div>
      </div>
    </div>

  <!-- STAGE 2: Clutter-Free Interactive Studio Workspace -->
  {:else}
    <div class:copilot-collapsed={copilotCollapsed} class="workspace-layout">
      <!-- Left: Resizable teacher co-pilot workbench -->
      <aside class="copilot-sidebar">
        <div class="copilot-header">
          <div class="copilot-title">
            <span class="bot-icon">✦</span>
            <div>
              <h3>Teacher Co-Pilot</h3>
              <span class="bot-sub">Discuss, review, then apply curriculum changes</span>
            </div>
          </div>
          <button type="button" class="copilot-collapse" onclick={() => (copilotCollapsed = !copilotCollapsed)} title={copilotCollapsed ? 'Expand co-pilot' : 'Collapse co-pilot'}>
            {copilotCollapsed ? '→' : '←'}
          </button>
        </div>

        {#if !copilotCollapsed}
          <div class="copilot-context">
            <div class="context-copy">
              <span class="context-label">Current design context</span>
              <strong>{currentCopilotModule ? `Unit ${currentCopilotModule.position}: ${currentCopilotModule.title}` : 'Whole-course architecture'}</strong>
              <small>{currentCopilotModule ? `${currentCopilotModule.learning_objectives?.length || 0} objectives · ${currentCopilotModule.knowledge_components?.length || 0} concept markers` : `${currentDraft.modules.length} modules available for revision`}</small>
            </div>
            {#if currentCopilotModule}
              <button type="button" class="context-reset" onclick={() => (activeCopilotModuleIndex = -1)}>Use whole course</button>
            {/if}
          </div>

          {#if latestChangeSummary}
            <div class="ai-diff-banner">
              <div class="diff-title">Latest applied change</div>
              <p>{latestChangeSummary}</p>
            </div>
          {/if}

          <div class="critique-section">
            <div class="critique-header">
              <span>Suggested next moves</span>
              <button type="button" class="toggle-btn" onclick={() => (showCritiqueChips = !showCritiqueChips)}>
                {showCritiqueChips ? 'Hide' : 'Show'}
              </button>
            </div>
            {#if showCritiqueChips}
              <div class="prompt-chips">
                {#each quickPrompts as prompt}
                  <button type="button" class="prompt-chip" disabled={isRevising} onclick={() => handleApplyRevision(prompt)}>{prompt}</button>
                {/each}
              </div>
            {/if}
          </div>

          <div class="chat-stream" aria-label="Curriculum co-pilot conversation">
            {#if revisionHistory.length === 0}
              <div class="chat-empty"><strong>Start a design conversation.</strong><span>Ask for a revision, select a unit for focused help, or use a suggested next move.</span></div>
            {:else}
              {#each revisionHistory as turn}
                <div class="chat-msg chat-{turn.role}">
                  <div class="msg-header">{turn.role === 'user' ? 'Your direction' : 'Co-pilot proposal'}</div>
                  <div class="msg-text">{turn.content}</div>
                </div>
              {/each}
            {/if}
          </div>

          <div class="copilot-input-bar">
            <textarea
              class="chat-input"
              rows="3"
              placeholder={currentCopilotModule ? `Ask about Unit ${currentCopilotModule.position}: objectives, concepts, evidence, or sequence…` : 'Ask AI to refine the course sequence, clarify concepts, add evidence, or restructure units…'}
              bind:value={reviewComment}
              disabled={isRevising}
              onkeydown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleApplyRevision();
                }
              }}
            ></textarea>
            <div class="composer-footer"><span>Enter to send · Shift+Enter for a new line</span><button type="button" class="btn-send-revision" disabled={isRevising || !reviewComment.trim()} onclick={() => handleApplyRevision()}>{isRevising ? 'Refining…' : 'Propose revision'}</button></div>
          </div>
        {/if}
      </aside>

      <!-- Right: Clean Blueprint Canvas -->
      <main class="canvas-main">
        <!-- Academic Header Block (Spacious Overview & Health Metrics) -->
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
              <span class="stat-num">{currentDraft.modules.length}</span>
              <span class="stat-lbl">Units</span>
            </div>
            <div class="stat-box">
              <span class="stat-num">
                {currentDraft.modules.reduce((acc, m) => acc + (m.learning_objectives?.length || 0), 0)}
              </span>
              <span class="stat-lbl">Objectives</span>
            </div>
            <div class="stat-box">
              <span class="stat-num">
                {currentDraft.modules.reduce((acc, m) => acc + (m.suggested_assignments?.length || 0), 0)}
              </span>
              <span class="stat-lbl">Inquiries</span>
            </div>
          </div>
        </div>

        <!-- Section Navigation Bar -->
        <div class="units-toolbar">
          <div class="units-count">
            <strong>{currentDraft.modules.length} Modules</strong> in Sequence
          </div>
          <div class="toolbar-actions">
            <button type="button" class="link-action" onclick={expandAll}>Expand All</button>
            <span class="dot-sep">·</span>
            <button type="button" class="link-action" onclick={collapseAll}>Collapse All</button>
            <span class="dot-sep">·</span>
            <button type="button" class="btn-add-unit" onclick={addEmptyModule}>+ Add Unit</button>
          </div>
        </div>

        <!-- Unit Cards (Accordion / Clean Document Flow) -->
        <div class="unit-card-list">
          {#each currentDraft.modules as mod, modIdx (modIdx)}
            {@const isOpen = expandedModules[modIdx]}
            <div class="unit-card {mod.change_status ? `border-${mod.change_status}` : ''}">
              <!-- Clickable Header Bar -->
              <div class="unit-bar" role="button" tabindex="0" onclick={() => toggleModule(modIdx)} onkeydown={(e) => e.key === 'Enter' && toggleModule(modIdx)}>
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
                    onclick={(e) => { e.stopPropagation(); focusCopilotModule(modIdx); }}
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
                    onclick={(e) => removeModule(e, modIdx)}
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
                          <button type="button" class="btn-text-action" onclick={() => addObjective(mod)}>
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
                                onclick={() => removeObjective(mod, objIdx)}
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
      </main>
    </div>
  {/if}
</div>

<style>
  /* Base Shell - Full-Width Expansive Studio */
  .studio-shell {
    max-width: 1680px;
    width: 100%;
    margin: 0 auto;
    padding: 24px 40px 60px;
    color: var(--color-slate-bright);
    box-sizing: border-box;
  }

  /* Minimalist Topbar */
  .studio-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 24px;
  }

  .topbar-breadcrumb {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13.5px;
  }

  .nav-back-link {
    background: transparent;
    border: none;
    color: var(--color-slate-muted);
    cursor: pointer;
    font-size: 13px;
    padding: 0;
    transition: color 0.15s;
  }
  .nav-back-link:hover {
    color: var(--color-heading);
  }

  .sep {
    color: var(--color-slate-subtle);
  }

  .current-crumb {
    font-weight: 600;
    color: var(--color-heading);
    max-width: 600px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .badge-revision {
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    color: var(--color-horizon-bright);
  }

  .topbar-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .btn-ghost {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    padding: 6px 14px;
    font-size: 12.5px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-ghost:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }

  .btn-publish {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-sm);
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
  }
  .btn-publish:hover:not(:disabled) {
    opacity: 0.92;
  }
  .btn-publish:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Quiet Notifications */
  .toast {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 14px;
    border-radius: var(--radius-sm);
    font-size: 12.5px;
    margin-bottom: 20px;
  }

  .toast-info {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.25);
    color: var(--color-aurora-bright);
  }

  .toast-error {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.25);
    color: var(--color-rose);
  }

  .toast-close {
    background: transparent;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 12px;
    padding: 2px 6px;
    opacity: 0.7;
  }
  .toast-close:hover {
    opacity: 1;
  }

  /* Full-Width 2-Column Studio Intake Grid */
  .intake-studio-grid {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 32px;
    align-items: start;
    margin-top: 8px;
  }

  .intake-sidebar {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .intake-intro-card, .intake-methodology-card, .intake-presets-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 20px 22px;
  }

  .badge-spark {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-horizon-bright);
    margin-bottom: 6px;
  }

  .intake-intro-card h2 {
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 4px 0 8px;
    line-height: 1.3;
  }

  .intake-desc {
    font-size: 13px;
    line-height: 1.55;
    color: var(--color-slate-light);
    margin: 0;
  }

  .method-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
    margin-bottom: 14px;
  }

  .method-item {
    display: flex;
    gap: 12px;
    margin-bottom: 14px;
  }
  .method-item:last-child {
    margin-bottom: 0;
  }

  .method-icon {
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .method-item strong {
    font-size: 12.5px;
    color: var(--color-heading);
    display: block;
    margin-bottom: 2px;
  }

  .method-item p {
    font-size: 11.5px;
    color: var(--color-slate-light);
    line-height: 1.45;
    margin: 0;
  }

  .presets-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
    display: block;
    margin-bottom: 10px;
  }

  .preset-pill-btn {
    width: 100%;
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 12px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }
  .preset-pill-btn:hover {
    border-color: var(--color-horizon-blue);
    background: var(--color-graphite-card);
  }

  .preset-info {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .preset-name {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-heading);
  }

  .preset-sub {
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .preset-action {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--color-aurora-bright);
    white-space: nowrap;
    margin-left: 8px;
  }

  /* Right Workbench Card */
  .intake-workbench-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 24px 28px;
  }

  .workbench-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--color-graphite-border);
    margin-bottom: 20px;
  }

  .workbench-header h3 {
    font-size: 17px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0 0 4px;
  }

  .workbench-sub {
    font-size: 12.5px;
    color: var(--color-slate-light);
  }

  .intake-body {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .form-grid-top {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 14px;
  }

  .input-wrap {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .input-wrap label, .textarea-label-row label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
  }

  .textarea-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
  }

  .btn-sample-link {
    background: transparent;
    border: none;
    color: var(--color-horizon-bright);
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-sample-link:hover {
    text-decoration: underline;
  }

  .clean-input, .clean-select {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 9px 12px;
    font-size: 13px;
    color: var(--color-slate-bright);
    outline: none;
    transition: border-color 0.15s;
  }

  .clean-textarea {
    width: 100%;
    box-sizing: border-box;
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.55;
    color: var(--color-slate-bright);
    outline: none;
    resize: vertical;
    transition: border-color 0.15s;
  }

  .clean-input:focus, .clean-select:focus, .clean-textarea:focus {
    border-color: var(--color-horizon-blue);
  }

  .workbench-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding-top: 14px;
    border-top: 1px solid var(--color-graphite-border);
  }

  .workbench-note {
    font-size: 12px;
    color: var(--color-slate-muted);
    line-height: 1.4;
    flex: 1;
  }

  .btn-synthesize {
    padding: 11px 24px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-md);
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    white-space: nowrap;
  }
  .btn-synthesize:hover:not(:disabled) {
    opacity: 0.95;
  }
  .btn-synthesize:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Workspace 2-Column Expansive Layout */
  .workspace-layout {
    display: grid;
    grid-template-columns: minmax(430px, 0.82fr) minmax(0, 1.18fr);
    gap: 24px;
    align-items: start;
    transition: grid-template-columns 0.2s ease;
  }

  .workspace-layout.copilot-collapsed {
    grid-template-columns: 58px minmax(0, 1fr);
  }

  /* Left: Teacher co-pilot workbench */
  .copilot-sidebar {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    position: sticky;
    top: 16px;
    max-height: calc(100vh - 100px);
    min-height: 560px;
    overflow: hidden;
  }

  .copilot-collapsed .copilot-sidebar {
    align-items: center;
    min-height: 0;
    padding: 10px 8px;
  }

  .copilot-collapsed .copilot-title > div {
    display: none;
  }

  .copilot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--color-graphite-border);
    gap: 8px;
    flex-shrink: 0;
  }

  .copilot-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bot-icon {
    align-items: center;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    border-radius: 9px;
    color: white;
    display: inline-flex;
    font-size: 17px;
    height: 30px;
    justify-content: center;
    width: 30px;
  }

  .copilot-title h3 {
    font-size: 13.5px;
    font-weight: 700;
    margin: 0;
    color: var(--color-heading);
  }

  .bot-sub {
    font-size: 10.5px;
    color: var(--color-slate-muted);
  }

  .copilot-collapse {
    background: transparent;
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    color: var(--color-slate-light);
    cursor: pointer;
    font-size: 12px;
    height: 26px;
    width: 26px;
  }
  .copilot-collapse:hover { color: var(--color-heading); border-color: var(--color-horizon-blue); }

  .copilot-context {
    align-items: flex-start;
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.24);
    border-radius: var(--radius-sm);
    display: flex;
    gap: 10px;
    justify-content: space-between;
    padding: 10px 12px;
    flex-shrink: 0;
  }
  .context-copy { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .context-label { color: var(--color-horizon-bright); font-size: 9px; font-weight: 700; letter-spacing: .45px; text-transform: uppercase; }
  .context-copy strong { color: var(--color-heading); font-size: 12px; line-height: 1.35; }
  .context-copy small { color: var(--color-slate-muted); font-size: 10px; }
  .context-reset { background: transparent; border: 0; color: var(--color-aurora-bright); cursor: pointer; font-size: 10px; padding: 1px 0; white-space: nowrap; }

  .ai-diff-banner {
    background: rgba(59, 130, 246, 0.07);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: var(--radius-xs);
    padding: 8px 10px;
    font-size: 11.5px;
    line-height: 1.4;
  }

  .diff-title {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-aurora-bright);
    margin-bottom: 2px;
  }

  .ai-diff-banner p {
    margin: 0;
    color: var(--color-slate-light);
  }

  .critique-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
  }

  .critique-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-muted);
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }

  .toggle-btn {
    background: transparent;
    border: none;
    color: var(--color-aurora-bright);
    font-size: 10.5px;
    cursor: pointer;
    padding: 0;
  }

  .prompt-chips {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
  }

  .prompt-chip {
    text-align: left;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    border-radius: var(--radius-xs);
    padding: 7px 9px;
    font-size: 10.5px;
    color: var(--color-slate-bright);
    cursor: pointer;
    transition: all 0.12s;
  }
  .prompt-chip:hover {
    background: var(--pill-hover);
    border-color: var(--color-graphite-border);
  }

  .chat-stream {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
    min-height: 170px;
    overflow-y: auto;
    padding: 2px 2px 2px 0;
  }

  .chat-empty {
    align-items: center;
    color: var(--color-slate-muted);
    display: flex;
    flex: 1;
    flex-direction: column;
    font-size: 11.5px;
    justify-content: center;
    line-height: 1.5;
    padding: 20px;
    text-align: center;
  }
  .chat-empty strong { color: var(--color-heading); font-size: 12.5px; }

  .chat-msg {
    padding: 7px 10px;
    border-radius: var(--radius-xs);
    font-size: 11.5px;
    line-height: 1.4;
  }

  .msg-header {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 2px;
  }

  .chat-user {
    background: rgba(59, 130, 246, 0.1);
    color: var(--color-slate-bright);
    border-left: 2px solid var(--color-aurora-bright);
  }
  .chat-user .msg-header {
    color: var(--color-aurora-bright);
  }

  .chat-assistant {
    background: var(--pill-bg);
    color: var(--color-slate-bright);
    border-left: 2px solid var(--color-horizon-blue);
  }
  .chat-assistant .msg-header {
    color: var(--color-horizon-blue);
  }

  .copilot-input-bar {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: auto;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 12px;
    flex-shrink: 0;
  }

  .chat-input {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    padding: 10px;
    font-size: 12px;
    color: var(--color-slate-bright);
    outline: none;
    resize: none;
  }
  .chat-input:focus {
    border-color: var(--color-horizon-blue);
  }

  .btn-send-revision {
    background: var(--color-heading);
    color: var(--color-obsidian);
    border: none;
    border-radius: var(--radius-xs);
    padding: 8px 12px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-send-revision:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .composer-footer { align-items: center; display: flex; gap: 10px; justify-content: space-between; }
  .composer-footer span { color: var(--color-slate-muted); font-size: 9.5px; }

  /* Right Canvas */
  .canvas-main {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .course-summary-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
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
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    color: var(--color-slate-muted);
  }

  .tag-domain {
    color: var(--color-aurora-bright);
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
    border-left: 1px solid var(--color-graphite-border);
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
    color: var(--color-heading);
    line-height: 1.1;
  }

  .stat-lbl {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
    margin-top: 2px;
  }

  .course-title-clean {
    background: transparent;
    border: none;
    color: var(--color-heading);
    font-size: 20px;
    font-weight: 700;
    outline: none;
    padding: 0;
    width: 100%;
  }
  .course-title-clean:focus {
    border-bottom: 1px solid var(--color-horizon-blue);
  }

  .course-overview-clean {
    background: transparent;
    border: none;
    color: var(--color-slate-light);
    font-size: 13px;
    line-height: 1.5;
    outline: none;
    resize: none;
    padding: 0;
    width: 100%;
  }
  .course-overview-clean:focus {
    border-bottom: 1px solid var(--color-horizon-blue);
  }

  .units-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
  }

  .units-count {
    font-size: 12.5px;
    color: var(--color-slate-muted);
  }
  .units-count strong {
    color: var(--color-heading);
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
    color: var(--color-slate-muted);
    cursor: pointer;
    font-size: 11.5px;
    padding: 0;
  }
  .link-action:hover {
    color: var(--color-heading);
  }

  .dot-sep {
    color: var(--color-slate-subtle);
  }

  .btn-add-unit {
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    color: var(--color-slate-bright);
    border-radius: var(--radius-xs);
    padding: 3px 8px;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
  }
  .btn-add-unit:hover {
    background: var(--pill-hover);
  }

  /* Unit Card Accordion Styles */
  .unit-card-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .unit-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
  }
  .unit-card:hover {
    border-color: var(--color-slate-subtle);
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
    background: var(--color-graphite-card);
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
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    border-radius: var(--radius-xs);
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 6px;
    color: var(--color-slate-muted);
    flex-shrink: 0;
  }

  .unit-title-text {
    background: transparent;
    border: none;
    color: var(--color-heading);
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
    border-bottom: 1px solid var(--color-horizon-blue);
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
    border: 1px solid var(--pill-border);
    border-radius: 999px;
    color: var(--color-slate-light);
    cursor: pointer;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 8px;
  }
  .btn-focus-copilot:hover, .btn-focus-copilot.active {
    background: rgba(59, 130, 246, 0.14);
    border-color: rgba(59, 130, 246, 0.5);
    color: var(--color-horizon-bright);
  }

  .unit-meta-preview {
    font-size: 11px;
    color: var(--color-slate-muted);
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
    color: var(--color-slate-muted);
    width: 14px;
    text-align: center;
  }

  .unit-expanded-content {
    padding: 16px 20px 20px;
    border-top: 1px solid var(--color-graphite-border);
    background: var(--color-graphite);
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
    color: var(--color-slate-muted);
  }

  .btn-text-action {
    background: transparent;
    border: none;
    color: var(--color-aurora-bright);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    padding: 0;
  }
  .btn-text-action:hover {
    text-decoration: underline;
  }

  .clean-textarea-sm {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-xs);
    padding: 10px 12px;
    font-size: 12.5px;
    color: var(--color-slate-bright);
    line-height: 1.5;
    outline: none;
    resize: vertical;
  }
  .clean-textarea-sm:focus {
    border-color: var(--color-horizon-blue);
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
    color: var(--color-horizon-bright);
    font-weight: 700;
    font-size: 14px;
  }

  .obj-text-input {
    flex: 1;
    background: transparent;
    border: none;
    border-bottom: 1px dashed transparent;
    color: var(--color-slate-bright);
    font-size: 12.5px;
    padding: 3px 0;
    outline: none;
  }
  .obj-text-input:hover, .obj-text-input:focus {
    border-bottom-color: var(--color-horizon-blue);
  }

  .btn-remove-obj {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle);
    cursor: pointer;
    font-size: 10px;
    padding: 2px 4px;
  }
  .btn-remove-obj:hover {
    color: var(--color-rose);
  }

  .assessment-milestone-box {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .milestone-badge {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-horizon-bright);
    letter-spacing: 0.4px;
  }

  .milestone-title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--color-heading);
  }

  .milestone-desc {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-slate-light);
    margin: 2px 0 6px;
  }

  .source-section-lbl {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: var(--color-slate-muted);
    margin-top: 4px;
  }

  .source-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .source-pill {
    font-size: 11px;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    border-radius: var(--radius-xs);
    padding: 3px 8px;
    color: var(--color-slate-bright);
  }

  .kc-box {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
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
    color: var(--color-slate-muted);
  }

  .kc-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .kc-pill {
    font-size: 10.5px;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    border-radius: var(--radius-xs);
    padding: 3px 8px;
    color: var(--color-aurora-bright);
    font-family: monospace;
  }

  .spinner-sm {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 1100px) {
    .intake-studio-grid {
      grid-template-columns: 1fr;
    }
    .workspace-layout {
      grid-template-columns: 1fr;
    }
    .workspace-layout.copilot-collapsed {
      grid-template-columns: 1fr;
    }
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
      border-top: 1px solid var(--color-graphite-border);
      padding-top: 12px;
      width: 100%;
      justify-content: space-around;
    }
    .copilot-sidebar {
      position: static;
      max-height: none;
      min-height: 460px;
    }
    .copilot-collapsed .copilot-sidebar { min-height: 0; }
    .prompt-chips { grid-template-columns: 1fr; }
    .form-grid-top {
      grid-template-columns: 1fr;
    }
  }
</style>
