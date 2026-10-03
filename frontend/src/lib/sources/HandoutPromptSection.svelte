<script>
  let {
    parsedCasePrompt = { narrative: '', sections: [] },
    displayRequirements = [],
  } = $props();
</script>

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

  .metric-note {
    font-size: 9.5px;
    color: #475569;
    line-height: 1.35;
  }

  .metric-val {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
    margin: 2px 0;
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
</style>
