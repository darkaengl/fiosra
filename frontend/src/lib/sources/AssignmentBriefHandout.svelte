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

  let parsedCasePrompt = $derived.by(() => {
    const raw = assignment?.task?.prompt || assignment?.published?.task?.prompt || assignment?.prompt || '';
    if (!raw) {
      return { narrative: '', sections: [] };
    }

    // Split by markdown headings starting with '### '
    const parts = raw.split(/\n(?=###\s+)/);
    const narrative = parts[0].replace(/^###\s+.*?\n/, '').trim();
    const sections = [];

    for (let i = 1; i < parts.length; i++) {
      const part = parts[i].trim();
      if (!part) continue;
      const lines = part.split('\n');
      const headingLine = lines[0].replace(/^###\s+/, '').trim();
      const bodyLines = lines.slice(1);

      const items = [];
      let calloutText = '';
      let isTable = false;
      let isMetricGrid = false;

      for (const line of bodyLines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        if (
          trimmed.toLowerCase().startsWith('the catch:') ||
          trimmed.toLowerCase().startsWith('note:') ||
          trimmed.toLowerCase().startsWith('constraint:')
        ) {
          calloutText = trimmed;
          continue;
        }

        // Detect bullet or numbered items: '• ', '- ', '1. '
        const bulletMatch = trimmed.match(/^([•\-\*]|\d+\.)\s*(.*)$/);
        if (bulletMatch) {
          const itemText = bulletMatch[2].trim();

          // Pipe-separated table row: 'col1 | col2 | col3'
          if (itemText.includes('|')) {
            isTable = true;
            const cols = itemText.split('|').map((c) => c.trim());
            items.push({ type: 'row', cols });
          }
          // Metric key-value card: 'Value — Label' or 'Value - Label'
          else if (itemText.includes('—') || itemText.includes(' - ')) {
            isMetricGrid = true;
            const sep = itemText.includes('—') ? '—' : ' - ';
            const [val, ...rest] = itemText.split(sep);
            items.push({ type: 'metric', value: val.trim(), label: rest.join(sep).trim() });
          }
          // Standard bullet item
          else {
            items.push({ type: 'bullet', text: itemText });
          }
        } else {
          items.push({ type: 'text', text: trimmed });
        }
      }

      sections.push({
        title: headingLine,
        isTable,
        isMetricGrid: isMetricGrid && !isTable,
        items,
        calloutText,
      });
    }

    return {
      narrative,
      sections,
    };
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
            <section class="sheet-section">
              <div class="sheet-sec-heading">
                <span class="sec-num">SECTION I</span>
                <h2 class="sheet-sec-title">Case Narrative &amp; Prompt Specification</h2>
              </div>
              {#if parsedCasePrompt.narrative}
                <p class="sheet-narrative-text">{parsedCasePrompt.narrative}</p>
              {/if}

              <!-- Dynamic Exhibits Parsed from Case Prompt -->
              {#each parsedCasePrompt.sections as sec}
                <div class="sub-sec-title">{sec.title}</div>
                {#if sec.isMetricGrid}
                  <div class="economics-grid">
                    {#each sec.items as m}
                      <div class="metric-card">
                        <div class="metric-val">{m.value}</div>
                        <div class="metric-note">{m.label}</div>
                      </div>
                    {/each}
                  </div>
                {:else if sec.isTable}
                  <table class="sheet-table">
                    <tbody>
                      {#each sec.items as row}
                        <tr>
                          {#each row.cols as col, cIdx}
                            <td class:badge-accent={cIdx === 1} class:text-muted-sm={cIdx > 1}>
                              {#if cIdx === 0}<strong>{col}</strong>{:else}{col}{/if}
                            </td>
                          {/each}
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                {:else}
                  <div class="survey-boundary-block">
                    <div class="survey-box" style="grid-column: span {sec.calloutText ? 1 : 2};">
                      <ul class="survey-list">
                        {#each sec.items as it}
                          <li>• {it.text}</li>
                        {/each}
                      </ul>
                    </div>
                    {#if sec.calloutText}
                      <div class="constraint-callout">
                        <span class="callout-badge">CASE NOTE &amp; BOUNDARY</span>
                        <p>{sec.calloutText}</p>
                      </div>
                    {/if}
                  </div>
                {/if}
              {/each}

              <!-- Ground Rules & Strategic Requirements -->
              {#if displayRequirements.length > 0}
                <div class="ground-rules-box">
                  <div class="rules-title">Strategic Mandate &amp; Deliverable Requirements:</div>
                  <div class="rules-grid">
                    {#each displayRequirements as rule, rIdx}
                      <div class="rule-item">
                        <span class="rule-index">{rIdx + 1}</span>
                        <span class="rule-text">{rule}</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </section>
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

            <!-- Section II: Assigned Primary Sources & Frameworks -->
            {#if displaySourcesList.length > 0}
              <section class="sheet-section">
                <div class="sheet-sec-heading">
                  <span class="sec-num">SECTION II</span>
                  <h2 class="sheet-sec-title">Assigned Primary Sources &amp; Theoretical Materials</h2>
                </div>
                <div class="frameworks-grid">
                  {#each displaySourcesList as src, sIdx}
                    <div class="framework-card">
                      <div class="fw-top">
                        <span class="fw-sec">{src.section || `Source ${sIdx + 1}`}</span>
                        {#if src.page}
                          <span class="fw-concept">Page {src.page}</span>
                        {/if}
                      </div>
                      <div class="fw-title">{src.title}</div>
                      {#if src.citation}
                        <div class="crit-sub">{src.citation}</div>
                      {/if}
                      {#if src.relevance_guidance}
                        <div class="fw-app"><strong>Guidance:</strong> {src.relevance_guidance}</div>
                      {/if}
                      <div class="src-action-row no-print">
                        <button
                          type="button"
                          class="btn-open-source-pdf"
                          onclick={() => switchToSource(src.title, src)}
                        >
                          📕 Read in PDF Viewer ↗
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              </section>
            {/if}

            <!-- Section III: Evaluation Rubric Criteria (100% Total) -->
            {#if displayRubricList.length > 0}
              <section class="sheet-section">
                <div class="sheet-sec-heading">
                  <span class="sec-num">SECTION III</span>
                  <h2 class="sheet-sec-title">Evaluation Rubric Criteria (100% Total)</h2>
                </div>
                <table class="sheet-rubric-table">
                  <thead>
                    <tr>
                      <th style="width: 26%;">Criterion &amp; Weight</th>
                      <th style="width: 24%;">Developing</th>
                      <th style="width: 25%;">Secure / Merit</th>
                      <th style="width: 25%;">Strong / Distinction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each displayRubricList as crit}
                      <tr>
                        <td>
                          <strong>{crit.title}</strong>
                          {#if crit.weight}
                            <span class="weight-tag">{crit.weight}%</span>
                          {/if}
                          {#if crit.description}
                            <div class="crit-sub">{crit.description}</div>
                          {/if}
                        </td>
                        {#if crit.levels && crit.levels.length >= 3}
                          {#each crit.levels.slice(0, 3) as lvl}
                            <td>
                              <span class="lvl-title">{lvl.label}</span>
                              <span class="lvl-desc">{lvl.description}</span>
                            </td>
                          {/each}
                        {:else if crit.levels && crit.levels.length > 0}
                          {#each crit.levels as lvl}
                            <td>
                              <span class="lvl-title">{lvl.label}</span>
                              <span class="lvl-desc">{lvl.description}</span>
                            </td>
                          {/each}
                        {:else}
                          <td colspan="3" class="lvl-desc">{crit.description || 'Assessed according to course standards.'}</td>
                        {/if}
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </section>
            {/if}
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

  .sheet-sec-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #111827;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
    margin: 0 0 10px;
  }

  .sheet-task-prompt {
    font-size: 13.5px;
    line-height: 1.6;
    color: #1f2937;
    margin: 0;
  }

  .sheet-requirements, .sheet-goals-list, .sheet-checklist {
    font-size: 12.5px;
    line-height: 1.6;
    color: #374151;
    padding-left: 20px;
    margin: 8px 0 0;
  }

  .sheet-goals-list, .sheet-checklist {
    list-style: none;
    padding-left: 4px;
  }

  .sheet-sources-table {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .sheet-source-row {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-left: 3px solid #374151;
    border-radius: 4px;
    padding: 10px 12px;
  }

  .src-meta strong {
    font-size: 12.5px;
    color: #111827;
    display: block;
  }

  .src-guide {
    font-size: 11.5px;
    color: #6b7280;
    font-style: italic;
    display: block;
    margin-top: 2px;
  }

  .src-excerpt {
    font-size: 12px;
    line-height: 1.5;
    color: #374151;
    margin: 6px 0;
    padding-left: 8px;
    border-left: 2px solid #cbd5e1;
  }

  .src-action-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
  }

  .btn-open-source-pdf {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
    padding: 3px 8px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    background: rgba(2, 132, 199, 0.1);
    color: #0284c7;
    border-color: rgba(2, 132, 199, 0.25);
  }

  .btn-open-source-pdf:hover {
    background: #0284c7;
    color: #ffffff;
  }

  .sheet-rubric-table {
    width: 100%;
    border-collapse: collapse;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11.5px;
    margin-top: 8px;
  }

  .sheet-rubric-table th, .sheet-rubric-table td {
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    padding: 7px 8px;
    vertical-align: top;
    text-align: left;
  }

  .sheet-rubric-table th {
    background: var(--color-bone-muted, #f4f5f0);
    color: var(--color-heading, #111827);
    font-weight: 700;
  }

  .weight-tag {
    display: inline-block;
    background: var(--color-graphite-hover, #e8eae3);
    color: var(--color-heading, #111827);
    font-size: 10px;
    font-weight: bold;
    padding: 1px 4px;
    border-radius: 3px;
    margin-left: 4px;
  }

  .crit-sub {
    font-size: 10.5px;
    color: #6b7280;
    margin-top: 3px;
  }

  .sheet-concept-tag {
    display: inline-block;
    font-size: 9.5px;
    font-weight: 700;
    color: #6d28d9;
    background: #f3e8ff;
    border: 1px solid #e9d5ff;
    padding: 1px 4px;
    border-radius: 3px;
    margin-top: 3px;
  }

  .lvl-title {
    font-weight: 700;
    display: block;
    color: #111827;
    font-size: 10.5px;
    margin-bottom: 2px;
  }

  .lvl-desc {
    font-size: 10.5px;
    color: #4b5563;
    line-height: 1.35;
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

  .sheet-sec-heading {
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1.5px solid #0f172a;
    padding-bottom: 4px;
    margin-bottom: 12px;
  }

  .sec-num {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 10px;
    font-weight: 800;
    background: #0f172a;
    color: #ffffff;
    padding: 2px 6px;
    border-radius: 3px;
    letter-spacing: 0.5px;
  }

  .sheet-narrative-text {
    font-size: 13.5px;
    line-height: 1.65;
    color: #1e293b;
    margin: 0 0 14px;
  }

  .sub-sec-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 12px 0 6px;
  }

  .economics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 14px;
  }

  .metric-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 10px;
  }

  .metric-label {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 9.5px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
  }

  .metric-val {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
    margin: 2px 0;
  }

  .metric-note {
    font-size: 9.5px;
    color: #475569;
    line-height: 1.35;
  }

  .sheet-table {
    width: 100%;
    border-collapse: collapse;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    margin-bottom: 14px;
  }

  .sheet-table th, .sheet-table td {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    vertical-align: middle;
    text-align: left;
  }

  .sheet-table th {
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.3px;
  }

  .badge-accent {
    font-weight: 700;
    color: #0284c7;
  }

  .text-muted-sm {
    color: #64748b;
    font-size: 10.5px;
  }

  .survey-boundary-block {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 14px;
  }

  .survey-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #0284c7;
    border-radius: 6px;
    padding: 8px 12px;
  }

  .survey-hdr {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
  }

  .sample-tag {
    font-size: 9.5px;
    color: #64748b;
  }

  .survey-list {
    list-style: none;
    padding: 0;
    margin: 0;
    font-size: 11px;
    line-height: 1.5;
    color: #334155;
  }

  .constraint-callout {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 3px solid #d97706;
    border-radius: 6px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .callout-badge {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #92400e;
  }

  .constraint-callout p {
    margin: 4px 0 0;
    font-size: 11px;
    font-weight: 600;
    color: #78350f;
    line-height: 1.4;
  }

  .ground-rules-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
  }

  .rules-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    margin-bottom: 8px;
    letter-spacing: 0.4px;
  }

  .rules-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 14px;
  }

  .rule-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 11px;
    line-height: 1.45;
    color: #334155;
  }

  .rule-index {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 9.5px;
    font-weight: 800;
    background: #e2e8f0;
    color: #334155;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 1px;
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

  .frameworks-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 14px;
  }

  .framework-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #475569;
    border-radius: 6px;
    padding: 8px 10px;
  }

  .fw-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  .fw-sec {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 9.5px;
    font-weight: 800;
    color: #0f172a;
    background: #e2e8f0;
    padding: 1px 5px;
    border-radius: 3px;
  }

  .fw-concept {
    font-size: 9px;
    font-weight: 600;
    color: #64748b;
  }

  .fw-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 3px;
  }

  .fw-app {
    font-size: 10px;
    line-height: 1.45;
    color: #475569;
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
