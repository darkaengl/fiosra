<script>
  import { getCriterionBloom, hasEvidence } from './reviewBloomUtils.js';

  let {
    dossier = null,
  } = $props();
</script>

<div class="rubric-inspector">
  <!-- Bloom's Taxonomy Cognitive Hierarchy Strip -->
  <div class="bloom-framework-strip">
    <span class="bloom-strip-label">Bloom's Taxonomy Framework</span>
    <div class="bloom-strip-pills">
      <span class="bloom-strip-pill l2">L2 Understand</span>
      <span class="bloom-strip-pill l3">L3 Apply</span>
      <span class="bloom-strip-pill l4">L4 Analyze</span>
      <span class="bloom-strip-pill l5">L5 Evaluate</span>
      <span class="bloom-strip-pill l6">L6 Create</span>
    </div>
  </div>

  {#if !dossier?.per_question_evidence || dossier.per_question_evidence.length === 0}
    <div class="tab-empty-msg">
      No rubric criteria configured for this assignment.
    </div>
  {:else}
    <div class="rubric-matrix-list">
      {#each dossier.per_question_evidence as question}
        {#each Object.entries(question.rubric_evidence || {}) as [, criterion]}
          {@const bloom = getCriterionBloom(criterion)}
          {@const isSubmitted = hasEvidence(criterion)}
          <article
            class="criterion-chip-card"
            class:met={criterion.met}
            class:unassessed={!isSubmitted}
          >
            <header class="criterion-chip-header">
              <div class="criterion-header-left">
                <span
                  class="criterion-tag"
                  class:met={criterion.met}
                  class:unassessed={!isSubmitted}
                >
                  {#if !isSubmitted}
                    ○ In Progress
                  {:else if criterion.met}
                    ✓ Evidence Met
                  {:else}
                    ● Partial Evidence
                  {/if}
                </span>
                <span
                  class="bloom-badge target"
                  style={`--b-color: ${bloom.target.color}; --b-bg: ${bloom.target.bg}; --b-border: ${bloom.target.border}`}
                  title={`Target Cognitive Demand: ${bloom.target.name} (Level ${bloom.target.level})`}
                >
                  🎯 {bloom.target.badge}
                </span>
              </div>

              <div class="criterion-header-right">
                <span class="criterion-weight-pill">{bloom.weight} Weight</span>
              </div>
            </header>

            <strong class="criterion-label">
              {criterion.label ||
                (criterion.met
                  ? "Standard Met"
                  : "Criterion Pending")}
            </strong>

            <p class="criterion-explanation-text">
              {criterion.description}
            </p>

            {#if isSubmitted}
              <div class="criterion-quote-block">
                <div class="quote-header-row">
                  <span class="quote-header">Submission Quote</span>
                  {#if bloom.demonstrated}
                    <span
                      class="bloom-demonstrated-pill"
                      class:met={bloom.demonstrated.level >= bloom.target.level}
                      class:below={bloom.demonstrated.level < bloom.target.level}
                    >
                      {#if bloom.demonstrated.level >= bloom.target.level}
                        ✓ Demonstrated: {bloom.demonstrated.badge}
                      {:else}
                        ⚠️ Demonstrated: {bloom.demonstrated.badge} (Target: {bloom.target.name})
                      {/if}
                    </span>
                  {/if}
                </div>
                <div class="quote-text">{criterion.evidence}</div>
              </div>
            {:else}
              <div class="criterion-unassessed-box">
                <div class="unassessed-row">
                  <span class="unassessed-dot">◌</span>
                  <span class="unassessed-text">No student evidence submitted yet</span>
                </div>
                <small class="unassessed-cognitive-demand">
                  Required cognitive depth: <strong>{bloom.target.badge}</strong> — {bloom.demandDesc}
                </small>
              </div>
            {/if}

            {#if criterion.explanation && isSubmitted}
              <small class="criterion-note"
                >{criterion.explanation}</small
              >
            {/if}
          </article>
        {/each}
      {/each}
    </div>
  {/if}
</div>

<style>
  .rubric-inspector {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .bloom-framework-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 10px;
    margin-bottom: 4px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
  }

  .bloom-strip-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #475569;
    white-space: nowrap;
  }

  .bloom-strip-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .bloom-strip-pill {
    font-size: 8.5px;
    font-weight: 700;
    padding: 2px 5px;
    border-radius: 3px;
    letter-spacing: 0.02em;
  }

  .bloom-strip-pill.l2 { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }
  .bloom-strip-pill.l3 { background: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }
  .bloom-strip-pill.l4 { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
  .bloom-strip-pill.l5 { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
  .bloom-strip-pill.l6 { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }

  .tab-empty-msg {
    color: var(--color-slate-muted, #94a3b8);
    font-size: 11.5px;
    font-style: italic;
    text-align: center;
    padding: 24px 8px;
  }

  .rubric-matrix-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .criterion-chip-card {
    background: #ffffff;
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-left: 3.5px solid #d97706;
    border-radius: 6px;
    padding: 11px 13px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: all 0.15s ease;
  }

  .criterion-chip-card.met {
    border-left-color: #059669;
    background: #ffffff;
  }

  .criterion-chip-card.unassessed {
    border-left-color: #cbd5e1;
    background: #fafaf9;
  }

  .criterion-chip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .criterion-header-left {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .criterion-header-right {
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .criterion-tag {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #92400e;
    background: #fef3c7;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .criterion-tag.met {
    color: #047857;
    background: #d1fae5;
  }

  .criterion-tag.unassessed {
    color: #475569;
    background: #f1f5f9;
  }

  .bloom-badge.target {
    font-size: 9.5px;
    font-weight: 700;
    color: var(--b-color, #7c3aed);
    background: var(--b-bg, #f5f3ff);
    border: 1px solid var(--b-border, #ddd6fe);
    padding: 1.5px 6px;
    border-radius: 4px;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  .criterion-weight-pill {
    font-size: 9.5px;
    color: var(--color-slate-muted, #64748b);
    font-weight: 600;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    padding: 2px 6px;
    border-radius: 3px;
    white-space: nowrap;
  }

  .criterion-label {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--color-heading, #0f172a);
    line-height: 1.35;
  }

  .criterion-explanation-text {
    font-size: 11px;
    color: var(--color-slate-light, #475569);
    margin: 0;
    line-height: 1.45;
  }

  .criterion-quote-block {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 8px 10px;
    border-radius: 5px;
    margin-top: 2px;
  }

  .quote-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 5px;
    gap: 6px;
    flex-wrap: wrap;
  }

  .quote-header {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-muted, #64748b);
    letter-spacing: 0.03em;
  }

  .bloom-demonstrated-pill {
    font-size: 9px;
    font-weight: 700;
    padding: 1.5px 6px;
    border-radius: 3px;
    letter-spacing: 0.02em;
  }

  .bloom-demonstrated-pill.met {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }

  .bloom-demonstrated-pill.below {
    background: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
  }

  .quote-text {
    font-size: 11px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-bright, #0f172a);
    line-height: 1.45;
    word-break: break-word;
  }

  .criterion-unassessed-box {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 5px;
    padding: 8px 10px;
    margin-top: 2px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .unassessed-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10.5px;
    color: #64748b;
  }

  .unassessed-dot {
    font-size: 11px;
    color: #94a3b8;
  }

  .unassessed-text {
    font-style: italic;
  }

  .unassessed-cognitive-demand {
    font-size: 10px;
    color: #475569;
    line-height: 1.35;
  }

  .criterion-note {
    font-size: 10px;
    color: var(--color-slate-muted, #64748b);
    font-style: italic;
    display: block;
    margin-top: 2px;
  }
</style>
