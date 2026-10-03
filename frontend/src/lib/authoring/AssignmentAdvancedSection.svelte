<script lang="ts">
  let {
    contract = $bindable(),
  } = $props<{
    contract: any;
  }>();

  let showAdvanced = $state(false);
</script>

<section class="card-section collapsible-section">
  <button
    type="button"
    class="accordion-toggle"
    onclick={() => showAdvanced = !showAdvanced}
  >
    <span>{showAdvanced ? '▾' : '▸'} Advanced Options: Socratic Guidance &amp; AutoSCORE Policies</span>
    <span class="pill-auto">Auto-Managed Defaults</span>
  </button>

  {#if showAdvanced}
    <div class="advanced-body">
      <div class="advanced-group">
        <h4>Socratic Assistance Modes for Students</h4>
        <p class="section-desc">Students can request these scaffolds without receiving direct answers from the AI tutor:</p>
        {#each contract.support_menu as menu}
          <div class="support-menu-row">
            <strong>{menu.title}</strong>
            <input class="input-text" bind:value={menu.description} />
          </div>
        {/each}
      </div>

      <div class="advanced-group">
        <h4>Academic Integrity Statement</h4>
        <textarea class="input-textarea" rows="2" bind:value={contract.integrity_notice}></textarea>
      </div>

      <div class="advanced-group">
        <h4>AutoSCORE Alignment Policy</h4>
        <p class="policy-note">
          AutoSCORE extracts and organizes cited evidence strictly against the <strong>{contract.public_rubric.length} public criteria</strong> above for educator grading. Autonomous final grades are disallowed by system policy.
        </p>
      </div>
    </div>
  {/if}
</section>

<style>
  .card-section {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  :global(.dark-mode) .card-section {
    background: #181b20;
    border-color: #2a2e36;
  }

  .collapsible-section {
    padding: 20px 24px;
    background: var(--surface, #ffffff);
  }

  .accordion-toggle {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    background: none;
    border: none;
    font-size: 14px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    cursor: pointer;
    padding: 0;
  }

  :global(.dark-mode) .accordion-toggle {
    color: #f1f5f9;
  }

  .pill-auto {
    font-size: 11px;
    font-weight: 600;
    background: var(--color-cloud-subtle, #F0EFEA);
    color: var(--color-slate, #6D7378);
    padding: 3px 8px;
    border-radius: 999px;
  }

  :global(.dark-mode) .pill-auto {
    background: #232832;
    color: #94a3b8;
  }

  .advanced-body {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    border-top: 1px solid var(--border, #DDDCD5);
    padding-top: 20px;
  }

  :global(.dark-mode) .advanced-body {
    border-color: #2a2e36;
  }

  .advanced-group h4 {
    font-size: 13px;
    font-weight: 700;
    margin: 0 0 6px;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .advanced-group h4 {
    color: #f1f5f9;
  }

  .section-desc {
    font-size: 12.5px;
    color: var(--color-slate, #6D7378);
    margin: 0 0 10px;
  }

  :global(.dark-mode) .section-desc {
    color: #94a3b8;
  }

  .support-menu-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }

  .support-menu-row strong {
    font-size: 12px;
    min-width: 120px;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .support-menu-row strong {
    color: #cbd5e1;
  }

  .input-text,
  .input-textarea {
    width: 100%;
    padding: 8px 12px;
    font-size: 13px;
    font-family: inherit;
    border-radius: 6px;
    border: 1px solid var(--border, #DDDCD5);
    background: var(--input-bg, #ffffff);
    color: var(--color-heading, #111315);
    box-sizing: border-box;
  }

  :global(.dark-mode) .input-text,
  :global(.dark-mode) .input-textarea {
    background: #111317;
    border-color: #2e3440;
    color: #f1f5f9;
  }

  .policy-note {
    font-size: 12.5px;
    line-height: 1.5;
    color: var(--color-slate, #6D7378);
    margin: 0;
    background: var(--color-cloud-subtle, #F0EFEA);
    padding: 10px 14px;
    border-radius: 6px;
  }

  :global(.dark-mode) .policy-note {
    background: #111317;
    color: #94a3b8;
  }
</style>
