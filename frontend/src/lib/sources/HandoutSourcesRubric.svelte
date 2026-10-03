<script>
  let {
    displaySourcesList = [],
    displayRubricList = [],
    onSwitchToSource = () => {},
  } = $props();
</script>

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
              onclick={() => onSwitchToSource(src.title, src)}
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

<style>
  .sheet-section {
    margin-bottom: 22px;
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

  .sheet-sec-title {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #111827;
    margin: 0;
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

  .crit-sub {
    font-size: 10.5px;
    color: #6b7280;
    margin-top: 3px;
  }

  .fw-app {
    font-size: 10px;
    line-height: 1.45;
    color: #475569;
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

  .no-print {
    /* hides during print if necessary */
  }
</style>
