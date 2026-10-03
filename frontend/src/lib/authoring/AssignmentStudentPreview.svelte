<script lang="ts">
  let {
    contract,
    onViewPdf = (pdf: { title: string; url: string }) => {},
  } = $props<{
    contract: any;
    onViewPdf?: (pdf: { title: string; url: string }) => void;
  }>();

  let previewTab = $state<'overview' | 'sources' | 'rubric' | 'checklist'>('overview');
</script>

<div class="student-preview-shell">
  <div class="preview-banner-header">
    <div>
      <span class="preview-eyebrow">Student View Simulation</span>
      <h2>{contract.title || 'Untitled Inquiry'}</h2>
      <p class="preview-sub">{contract.task?.deliverable} · {contract.task?.scope}</p>
    </div>
    <div class="preview-mode-tag">
      <span>●</span> Student Interface
    </div>
  </div>

  <div class="preview-nav-tabs">
    <button class:active={previewTab === 'overview'} onclick={() => previewTab = 'overview'}>Task Inquiries</button>
    <button class:active={previewTab === 'sources'} onclick={() => previewTab = 'sources'}>Assigned Materials ({contract.source_pack?.length || 0})</button>
    <button class:active={previewTab === 'rubric'} onclick={() => previewTab = 'rubric'}>Grading Rubric ({contract.public_rubric?.length || 0})</button>
    <button class:active={previewTab === 'checklist'} onclick={() => previewTab = 'checklist'}>Submission Checklist</button>
  </div>

  <div class="preview-content-box">
    {#if previewTab === 'overview'}
      <div class="preview-overview-pane">
        <div class="task-box">
          <h3>Your Task</h3>
          <p class="prompt-text">{contract.task?.prompt}</p>
        </div>

        <div class="meta-grid">
          <div class="meta-card">
            <span class="meta-label">Scope &amp; Chronology</span>
            <p>{contract.task?.scope}</p>
          </div>
          <div class="meta-card">
            <span class="meta-label">Deliverable</span>
            <p>{contract.task?.deliverable}</p>
          </div>
        </div>

        <div class="goals-box">
          <h3>Core Learning Objectives</h3>
          <ul>
            {#each contract.learning_goals || [] as goal}
              <li>{goal}</li>
            {/each}
          </ul>
        </div>
      </div>

    {:else if previewTab === 'sources'}
      <div class="preview-sources-pane">
        {#each contract.source_pack || [] as src}
          <article class="reading-card">
            <div class="reading-head">
              <h4>{src.title}</h4>
              {#if src.source_url}
                <button
                  type="button"
                  class="btn-read-pdf"
                  onclick={() => onViewPdf({ title: src.title, url: src.source_url })}
                >
                  Read Original PDF ↗
                </button>
              {/if}
            </div>
            <p class="reading-guide">{src.relevance_guidance}</p>
            <blockquote class="reading-quote">{src.excerpt}</blockquote>
          </article>
        {:else}
          <p class="empty-note">No primary sources attached.</p>
        {/each}
      </div>

    {:else if previewTab === 'rubric'}
      <div class="preview-rubric-pane">
        <div class="rubric-table">
          {#each contract.public_rubric || [] as crit}
            <div class="rubric-row">
              <div class="crit-head">
                <h4>{crit.title}</h4>
                <div class="crit-meta-badges">
                  <span class="crit-weight">{crit.weight}%</span>
                  {#if crit.concept_label || crit.concept_id}
                    <span class="crit-concept-pill">⚡ {crit.concept_label || crit.concept_id}</span>
                  {/if}
                </div>
                <p>{crit.description}</p>
              </div>
              <div class="levels-display">
                {#each crit.levels || [] as lvl}
                  <div class="lvl-col">
                    <strong>{lvl.label}</strong>
                    <p>{lvl.description}</p>
                  </div>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </div>

    {:else}
      <div class="preview-checklist-pane">
        <h3>Pre-Submission Checklist</h3>
        <ul class="checklist-items">
          {#each contract.completion_checklist || [] as item}
            <li><input type="checkbox" disabled /> <span>{item}</span></li>
          {/each}
        </ul>
        <div class="integrity-box">
          <strong>Academic Integrity:</strong>
          <p>{contract.integrity_notice}</p>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .student-preview-shell {
    max-width: 900px;
    margin: 0 auto;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  :global(.dark-mode) .student-preview-shell {
    background: #181b20;
    border-color: #2a2e36;
  }

  .preview-banner-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 24px;
    border-bottom: 1px solid var(--border, #DDDCD5);
    background: var(--color-cloud-subtle, #F0EFEA);
  }

  :global(.dark-mode) .preview-banner-header {
    background: #111317;
    border-color: #2a2e36;
  }

  .preview-eyebrow {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .preview-banner-header h2 {
    font-size: 20px;
    font-weight: 700;
    margin: 4px 0 2px;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .preview-banner-header h2 {
    color: #f1f5f9;
  }

  .preview-sub {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
    margin: 0;
  }

  :global(.dark-mode) .preview-sub {
    color: #94a3b8;
  }

  .preview-mode-tag {
    font-size: 11.5px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
    background: #dafbe1;
    border: 1px solid #4ac26b;
    color: #116329;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  :global(.dark-mode) .preview-mode-tag {
    background: rgba(35, 134, 54, 0.2);
    border-color: rgba(46, 160, 67, 0.4);
    color: #3fb950;
  }

  .preview-nav-tabs {
    display: flex;
    padding: 0 16px;
    gap: 4px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border-bottom: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .preview-nav-tabs {
    background: #111317;
    border-color: #2a2e36;
  }

  .preview-nav-tabs button {
    background: transparent;
    border: 0;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    font-size: 12.5px;
    font-weight: 600;
    padding: 12px 14px;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .preview-nav-tabs button {
    color: #94a3b8;
  }

  .preview-nav-tabs button.active {
    color: var(--color-horizon-blue, #4F6BFF);
    border-bottom-color: var(--color-horizon-blue, #4F6BFF);
  }

  .preview-content-box {
    padding: 24px;
  }

  .task-box {
    border-radius: 8px;
    padding: 18px;
    margin-bottom: 18px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .task-box {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .task-box h3 {
    font-size: 14px;
    margin: 0 0 8px;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .prompt-text {
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .prompt-text {
    color: #f1f5f9;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 18px;
  }

  .meta-card {
    border-radius: 8px;
    padding: 12px 14px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .meta-card {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .meta-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .meta-label {
    color: #94a3b8;
  }

  .meta-card p {
    font-size: 13px;
    font-weight: 600;
    margin: 4px 0 0;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .meta-card p {
    color: #f1f5f9;
  }

  .goals-box h3 {
    font-size: 13px;
    margin: 0 0 8px;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .goals-box h3 {
    color: #f1f5f9;
  }

  .goals-box ul {
    margin: 0;
    padding-left: 20px;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .goals-box ul {
    color: #94a3b8;
  }

  .reading-card {
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 14px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .reading-card {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .reading-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .reading-head h4 {
    font-size: 14px;
    margin: 0;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .reading-head h4 {
    color: #f1f5f9;
  }

  .btn-read-pdf {
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    cursor: pointer;
    background: #e7f3ff;
    border: 1px solid #0969da;
    color: #0969da;
  }

  :global(.dark-mode) .btn-read-pdf {
    background: rgba(56, 139, 253, 0.12);
    border-color: #388bfd;
    color: #58a6ff;
  }

  .reading-guide {
    font-size: 12px;
    margin: 0 0 10px;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .reading-guide {
    color: #94a3b8;
  }

  .reading-quote {
    font-size: 12.5px;
    line-height: 1.55;
    margin: 0;
    padding: 10px 14px;
    background: var(--surface, #ffffff);
    border-left: 3px solid var(--color-horizon-blue, #4F6BFF);
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .reading-quote {
    background: #111317;
    border-color: #58a6ff;
    color: #f1f5f9;
  }

  .rubric-row {
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 14px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .rubric-row {
    background: #1e2229;
    border-color: #2a2e36;
  }

  .crit-head h4 {
    font-size: 14px;
    display: inline-block;
    margin: 0 8px 4px 0;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .crit-head h4 {
    color: #f1f5f9;
  }

  .crit-weight {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    background: #eaeef2;
    color: #0969da;
  }

  :global(.dark-mode) .crit-weight {
    background: #21262d;
    color: #58a6ff;
  }

  .crit-meta-badges {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    vertical-align: middle;
  }

  .crit-concept-pill {
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    background: #ede9fe;
    color: #6d28d9;
    border: 1px solid #ddd6fe;
  }

  :global(.dark-mode) .crit-concept-pill {
    background: rgba(124, 58, 237, 0.2);
    color: #c4b5fd;
    border-color: rgba(124, 58, 237, 0.4);
  }

  .crit-head p {
    font-size: 12px;
    margin: 4px 0 0;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .crit-head p {
    color: #94a3b8;
  }

  .levels-display {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
  }

  .lvl-col {
    padding: 8px 10px;
    border-radius: 4px;
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .lvl-col {
    background: #111317;
    border-color: #2a2e36;
  }

  .lvl-col strong {
    font-size: 11px;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .lvl-col strong {
    color: #f1f5f9;
  }

  .lvl-col p {
    font-size: 11.5px;
    margin: 4px 0 0;
    line-height: 1.4;
    color: var(--color-slate, #6D7378);
  }

  :global(.dark-mode) .lvl-col p {
    color: #94a3b8;
  }

  .checklist-items {
    list-style: none;
    padding: 0;
    margin: 0 0 18px;
  }

  .checklist-items li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding: 8px 0;
    color: var(--color-heading, #111315);
    border-bottom: 1px solid var(--border, #DDDCD5);
  }

  :global(.dark-mode) .checklist-items li {
    color: #f1f5f9;
    border-color: #2a2e36;
  }

  .integrity-box {
    border-radius: 6px;
    padding: 12px;
    font-size: 12.5px;
    background: #f0fdf4;
    border: 1px solid #86efac;
    color: #166534;
  }

  :global(.dark-mode) .integrity-box {
    background: rgba(165, 180, 252, 0.08);
    border: 1px solid rgba(165, 180, 252, 0.2);
    color: #c9d1d9;
  }

  .empty-note {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
    font-style: italic;
  }
</style>
