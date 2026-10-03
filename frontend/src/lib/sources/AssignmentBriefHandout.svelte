<script>
  let {
    assignment = null,
    courseTitle = 'Department of Historical Studies',
    sources = [],
    onSwitchToSource = () => {},
  } = $props();
  let displayDomain = $derived(
    assignment?.domain ||
    assignment?.published?.domain ||
    assignment?.spec?.domain ||
    ''
  );

  let displayDepartment = $derived(
    assignment?.department ||
    assignment?.published?.department ||
    assignment?.spec?.department ||
    (courseTitle && courseTitle.toLowerCase().includes('department') ? courseTitle : '') ||
    (displayDomain ? `Department of ${displayDomain}` : '')
  );

  let displayCourse = $derived(
    assignment?.course_title ||
    assignment?.published?.course_title ||
    assignment?.spec?.course_title ||
    courseTitle ||
    assignment?.title ||
    assignment?.published?.title ||
    'Academic Inquiry'
  );

  import { parseCasePrompt } from './handoutPromptParser';
  import HandoutPromptSection from './HandoutPromptSection.svelte';
  import HandoutSourcesRubric from './HandoutSourcesRubric.svelte';

  let parsedCasePrompt = $derived.by(() => {
    const raw = assignment?.task?.prompt || assignment?.published?.task?.prompt || assignment?.prompt || '';
    return parseCasePrompt(raw);
  });

  let displaySourcesList = $derived(
    assignment?.source_pack ||
    assignment?.published?.source_pack ||
    sources ||
    []
  );

  let displayRubricList = $derived(
    assignment?.public_rubric ||
    assignment?.published?.public_rubric ||
    assignment?.spec?.rubric ||
    []
  );

  let displayGoalsList = $derived(
    assignment?.learning_goals ||
    assignment?.published?.learning_goals ||
    []
  );

  let displayChecklist = $derived(
    assignment?.completion_checklist ||
    assignment?.published?.completion_checklist ||
    []
  );

  let displayRequirements = $derived(
    assignment?.task?.requirements ||
    assignment?.published?.task?.requirements ||
    []
  );

</script>

      <div class="assignment-scroll-container">
        <article class="academic-sheet print-target">
          <!-- PAGE 1 OF 2: CASE BRIEF & OPERATIONAL DATA -->
          <div class="sheet-page sheet-page-1">
            <!-- Sheet Header -->
            <header class="sheet-header">
              <div class="sheet-institution">
                <div class="inst-logo">FIOSRA ACADEMIC LMS</div>
                <div class="inst-course">{displayCourse}</div>
                {#if displayDepartment}
                  <div class="inst-dept">{displayDepartment}</div>
                {/if}
              </div>
              <div class="sheet-meta">
                {#if displayDomain}
                  <div><span>Domain:</span> {displayDomain}</div>
                {/if}
                <div><span>Deliverable:</span> {assignment?.task?.deliverable || assignment?.published?.task?.deliverable || 'Argumentative Work'}</div>
                {#if assignment?.task?.scope || assignment?.published?.task?.scope}
                  <div><span>Scope:</span> {assignment?.task?.scope || assignment?.published?.task?.scope}</div>
                {/if}
                <div><span>Academic Term:</span> Current Active Session</div>
              </div>
            </header>

            <!-- Title Block -->
            <div class="sheet-title-block">
              <h1>{assignment?.published?.title || assignment?.title || 'Assignment Brief'}</h1>
              {#if assignment?.purpose || assignment?.published?.purpose}
                <p class="sheet-purpose">{assignment?.purpose || assignment?.published?.purpose}</p>
              {/if}
            </div>

            <!-- Section I: Case Narrative & Operational Data -->
            <HandoutPromptSection
              {parsedCasePrompt}
              {displayRequirements}
            />
          </div>

          <!-- EXPLICIT PAGE BREAK FOR 2-PAGE PRINT HANDOUT -->
          <div class="sheet-page-break"></div>

          <!-- PAGE 2 OF 2: SOURCES, RUBRIC & INTEGRITY -->
          <div class="sheet-page sheet-page-2">
            <!-- Header for Page 2 -->
            <div class="page-continuation-header">
              <span>{displayCourse}{assignment?.published?.title && displayCourse !== assignment.published.title ? ` — ${assignment.published.title}` : ''}</span>
              <span class="page-num-pill">Page 2 of 3</span>
            </div>

            <!-- Sections II & III: Assigned Primary Sources & Evaluation Rubric Criteria -->
            <HandoutSourcesRubric
              {displaySourcesList}
              {displayRubricList}
              {onSwitchToSource}
            />
          </div>

          <!-- EXPLICIT PAGE BREAK BEFORE SECTION IV -->
          <div class="sheet-page-break"></div>

          <!-- PAGE 3: LEARNING GOALS & INTEGRITY -->
          <div class="sheet-page sheet-page-3">
            <!-- Header for Page 3 -->
            <div class="page-continuation-header">
              <span>{displayCourse}{assignment?.published?.title && displayCourse !== assignment.published.title ? ` — ${assignment.published.title}` : ''}</span>
              <span class="page-num-pill">Page 3 of 3</span>
            </div>

            <!-- Section IV: Learning Goals -->
            {#if displayGoalsList.length > 0}
              <section class="sheet-section">
                <div class="sheet-sec-heading">
                  <span class="sec-num">SECTION IV</span>
                  <h2 class="sheet-sec-title">Milestone Learning Goals</h2>
                </div>
                <div class="goals-grid">
                  {#each displayGoalsList as goal}
                    <div class="goal-item">
                      <span class="goal-check">✓</span>
                      <span class="goal-text">{goal}</span>
                    </div>
                  {/each}
                </div>
              </section>
            {/if}

            <!-- Section V: Academic Integrity Notice & Readiness Checklist -->
            <footer class="sheet-footer">
              {#if displayChecklist.length > 0}
                <div class="ground-rules-box" style="margin-bottom: 8px;">
                  <div class="rules-title">Submission Readiness Checklist:</div>
                  <div class="rules-grid">
                    {#each displayChecklist as item}
                      <div class="rule-item">
                        <span class="rule-index">◻</span>
                        <span class="rule-text">{item}</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
              <div class="integrity-card">
                <div class="integrity-title">
                  <span>🔒 Academic Integrity &amp; Original Authorship Notice</span>
                </div>
                <div class="integrity-text">
                  {assignment?.integrity_notice || assignment?.published?.integrity_notice || 'Your educator evaluates the final submission. All calculations, analysis, and arguments must represent your original reasoning. Cite assigned course frameworks where theoretical support is invoked.'}
                </div>
                <div class="sign-block">
                  <div class="sign-line">Candidate Signature: ____________________________________</div>
                  <div class="sign-line">Submission Date: ____________________</div>
                </div>
              </div>
            </footer>
          </div>
        </article>
      </div>

<style>
  .assignment-scroll-container {
    flex: 1;
    overflow-y: auto;
    background: var(--color-obsidian, #f8f8f5);
    padding: 20px 24px 60px 24px;
  }

  :global([data-theme="dark"]) .assignment-scroll-container {
    background: var(--color-obsidian, #121418);
  }

  .academic-sheet {
    background: #ffffff;
    color: #1f2937;
    border-radius: 6px;
    padding: 36px 40px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    font-family: "Georgia", serif;
    max-width: 800px;
    margin: 0 auto;
    box-sizing: border-box;
  }

  .sheet-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid #111827;
    padding-bottom: 14px;
    margin-bottom: 20px;
  }

  .inst-logo {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #4b5563;
  }

  .inst-course {
    font-size: 15px;
    font-weight: bold;
    color: #111827;
    margin-top: 2px;
  }

  .sheet-meta {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    color: #4b5563;
    line-height: 1.5;
    text-align: right;
  }

  .sheet-meta span {
    font-weight: bold;
    color: #111827;
  }

  .sheet-title-block {
    margin-bottom: 22px;
  }

  .sheet-title-block h1 {
    font-size: 22px;
    font-weight: 800;
    color: #111827;
    margin: 0 0 6px;
    line-height: 1.25;
  }

  .sheet-purpose {
    font-size: 13.5px;
    font-style: italic;
    color: #4b5563;
    margin: 0;
    line-height: 1.5;
  }

  .sheet-section {
    margin-bottom: 22px;
  }

  .sheet-page {
    position: relative;
    box-sizing: border-box;
    background: #ffffff;
  }

  .sheet-page-break {
    border-top: 2px dashed #cbd5e1;
    margin: 32px 0 28px;
    position: relative;
    text-align: center;
  }

  .sheet-page-break::after {
    content: 'PAGE BREAK';
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: #94a3b8;
    background: #ffffff;
    padding: 0 12px;
    position: relative;
    top: -8px;
  }


  .page-continuation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1.5px solid #0f172a;
    padding-bottom: 6px;
    margin-bottom: 14px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #475569;
  }

  .page-num-pill {
    background: #0f172a;
    color: #ffffff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 9.5px;
  }


  .goals-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 14px;
    margin-bottom: 14px;
  }

  .goal-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 10.5px;
    line-height: 1.45;
    color: #334155;
  }

  .goal-check {
    color: #15803d;
    font-weight: bold;
    font-size: 11px;
    flex-shrink: 0;
  }

  .integrity-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #0f172a;
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 10px;
  }

  .integrity-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
  }

  .integrity-text {
    font-size: 10.5px;
    line-height: 1.45;
    color: #475569;
    margin-bottom: 8px;
  }

  .sign-block {
    display: flex;
    justify-content: space-between;
    border-top: 1px dashed #cbd5e1;
    padding-top: 6px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 10px;
    color: #64748b;
  }

  .sheet-footer {
    border-top: 1px solid #e5e7eb;
    margin-top: 16px;
    padding-top: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    color: #6b7280;
  }

  /* -------------------------------------------------------------
     PRINT STYLESHEET (@media print)
     ------------------------------------------------------------- */
  @media print {
    :global(body), :global(html) {
      background: #ffffff !important;
      color: #000000 !important;
      padding: 0 !important;
      margin: 0 !important;
      overflow: visible !important;
      height: auto !important;
    }
    :global(.workspace-header),
    :global(.workspace-topbar),
    :global(.top-nav-bar),
    :global(.workbench-col-canvas),
    :global(.workbench-col-gutter),
    :global(.workbench-resizer-handle),
    :global(.canvas-tab-wrapper),
    :global(.collapsed-sidebar-strip),
    .well-header,
    .no-print,
    .doc-switcher-bar,
    .pdf-reader-frame-container,
    .bottom-ai-search-anchor {
      display: none !important;
    }
    :global(.student-workspace-shell),
    :global(.workspace-viewport),
    :global(.workspace-content-body),
    :global(.in-situ-workbench-grid),
    :global(.workbench-col-sources),
    .evidentiary-well {
      display: block !important;
      position: static !important;
      width: 100% !important;
      height: auto !important;
      overflow: visible !important;
      border: none !important;
      margin: 0 !important;
      padding: 0 !important;
      background: #ffffff !important;
    }
    .assignment-scroll-container {
      overflow: visible !important;
      height: auto !important;
      padding: 0 !important;
      background: #ffffff !important;
    }
    .academic-sheet {
      box-shadow: none !important;
      border: none !important;
      padding: 0 !important;
      max-width: 100% !important;
    }
  }

</style>
