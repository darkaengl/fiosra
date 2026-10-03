<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { responseError, routeParams } from '../lib/session.js';
  import CourseIntakeStage from '../lib/course/CourseIntakeStage.svelte';
  import CourseCopilotSidebar from '../lib/course/CourseCopilotSidebar.svelte';
  import CourseBlueprintCanvas from '../lib/course/CourseBlueprintCanvas.svelte';

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
    <CourseIntakeStage
      bind:materialsText
      bind:titleHint
      bind:selectedDomain
      bind:targetAudience
      {isGenerating}
      onLoadSample={loadSample}
      onSynthesize={handleSynthesizeDraft}
    />

  <!-- STAGE 2: Clutter-Free Interactive Studio Workspace -->
  {:else}
    <div class:copilot-collapsed={copilotCollapsed} class="workspace-layout">
      <!-- Left: Resizable teacher co-pilot workbench -->
      <CourseCopilotSidebar
        {currentDraft}
        {activeCopilotModuleIndex}
        {currentCopilotModule}
        {latestChangeSummary}
        {showCritiqueChips}
        {quickPrompts}
        {isRevising}
        {revisionHistory}
        bind:reviewComment
        bind:copilotCollapsed
        onResetContext={() => (activeCopilotModuleIndex = -1)}
        onToggleCritiqueChips={() => (showCritiqueChips = !showCritiqueChips)}
        onApplyRevision={handleApplyRevision}
      />

      <!-- Right: Clean Blueprint Canvas -->
      <CourseBlueprintCanvas
        bind:currentDraft
        bind:expandedModules
        {activeCopilotModuleIndex}
        onToggleModule={toggleModule}
        onFocusCopilotModule={focusCopilotModule}
        onExpandAll={expandAll}
        onCollapseAll={collapseAll}
        onAddEmptyModule={addEmptyModule}
        onRemoveModule={removeModule}
        onAddObjective={addObjective}
        onRemoveObjective={removeObjective}
      />
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
    font-size: 1.1rem;
    line-height: 1;
    padding: 0 4px;
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

  @media (max-width: 1100px) {
    .workspace-layout {
      grid-template-columns: 1fr;
    }
    .workspace-layout.copilot-collapsed {
      grid-template-columns: 1fr;
    }
  }
</style>
