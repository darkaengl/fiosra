<script lang="ts">
  const loop = [
    { number: "01", title: "Context", text: "Course, assignment, materials, rubric and policy create a credible place to begin." },
    { number: "02", title: "Learning", text: "Students write, inspect and explore within the work rather than leaving it for a generic chat." },
    { number: "03", title: "Development", text: "Fiosra recognises meaningful changes in reasoning without claiming to observe everything." },
    { number: "04", title: "Evidence", text: "Qualifying work is captured with provenance so it can be interpreted in academic context." },
    { number: "05", title: "Understanding", text: "Students review their Development Trace. Educators see evidence with context, not an activity dashboard." },
  ];
</script>

<section id="how-it-works" class="loop-section">
  <div class="loop-container">
    <div class="loop-header-row">
      <div>
        <p class="section-kicker">The Fiosra loop</p>
        <h2 class="loop-title">A continuous route from context to understanding.</h2>
      </div>
      <p class="loop-subtitle">
        The loop is designed to be lived within assignment work, not administered around it.
      </p>
    </div>

    <div class="loop-steps-grid">
      {#each loop as item, index}
        <article class="loop-step-card">
          <span class="step-num">{item.number}</span>
          <h3 class="step-title">{item.title}</h3>
          <p class="step-desc">{item.text}</p>
          {#if index < loop.length - 1}
            <span aria-hidden="true" class="step-connector">→</span>
          {/if}
        </article>
      {/each}
    </div>
  </div>
</section>

<style>
  .loop-section {
    border-top: 1px solid var(--border, #DDDCD5);
    border-bottom: 1px solid var(--border, #DDDCD5);
    background: #FFFEFA;
    padding: 80px 0;
  }

  .loop-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .loop-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 32px;
  }

  .section-kicker {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    margin: 0;
  }

  .loop-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 38px;
    line-height: 1.05;
    letter-spacing: -0.035em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 12px 0 0;
    max-width: 580px;
  }

  .loop-subtitle {
    font-size: 13px;
    line-height: 1.5;
    color: var(--m-color-slate, #6D7378);
    max-width: 340px;
    margin: 0;
  }

  .loop-steps-grid {
    margin-top: 48px;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    border-top: 1px solid #D5D4CD;
    border-bottom: 1px solid #D5D4CD;
  }

  .loop-step-card {
    position: relative;
    padding: 24px 20px 24px 0;
    min-height: 170px;
    border-right: 1px solid #D5D4CD;
  }

  .loop-step-card:last-child {
    border-right: none;
    padding-right: 0;
  }

  .loop-step-card:not(:first-child) {
    padding-left: 20px;
  }

  .step-num {
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .step-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
    margin: 20px 0 8px;
  }

  .step-desc {
    font-size: 12px;
    line-height: 1.5;
    color: var(--m-color-slate, #6D7378);
    margin: 0;
  }

  .step-connector {
    position: absolute;
    right: -8px;
    top: 56px;
    z-index: 10;
    background: #FFFEFA;
    padding: 0 4px;
    font-family: var(--font-serif, serif);
    font-size: 16px;
    color: var(--m-color-horizon-blue, #4F6BFF);
  }

  @media (max-width: 960px) {
    .loop-header-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }

    .loop-steps-grid {
      grid-template-columns: 1fr;
      border-top: none;
    }

    .loop-step-card {
      border-right: none;
      border-bottom: 1px solid #D5D4CD;
      padding: 16px 0;
      min-height: auto;
    }

    .loop-step-card:not(:first-child) {
      padding-left: 0;
    }

    .step-connector {
      display: none;
    }
  }
</style>
