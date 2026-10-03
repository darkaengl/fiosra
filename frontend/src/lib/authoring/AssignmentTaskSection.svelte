<script lang="ts">
  let {
    contract = $bindable(),
  } = $props<{
    contract: any;
  }>();
</script>

<section class="card-section">
  <div class="card-header">
    <div class="header-tag">01 · TASK &amp; DIRECTIVES</div>
    <h2>Assignment Prompt &amp; Inquiries</h2>
    <p class="section-desc">Specify what historical question, puzzle, or institutional tension students will investigate.</p>
  </div>

  <div class="form-group">
    <label for="task-title">Assignment Title</label>
    <input
      id="task-title"
      class="input-text title-input"
      bind:value={contract.title}
      placeholder="e.g. Imperial Bureaucracy and Temple Economy in Medieval South India"
    />
  </div>

  <div class="form-group">
    <label for="task-prompt">Inquiry Prompt (Student Directions)</label>
    <textarea
      id="task-prompt"
      class="input-textarea prompt-area"
      rows="6"
      bind:value={contract.task.prompt}
      placeholder="Write clear instructions detailing what claims, contradictions, or evidence students must analyze..."
    ></textarea>
  </div>

  <div class="two-col-grid">
    <div class="form-group">
      <label for="task-scope">Historical Scope &amp; Period</label>
      <input
        id="task-scope"
        class="input-text"
        bind:value={contract.task.scope}
        placeholder="e.g. 9th–13th century Chola and Pandyan empires"
      />
    </div>
    <div class="form-group">
      <label for="task-deliverable">Expected Deliverable</label>
      <input
        id="task-deliverable"
        class="input-text"
        bind:value={contract.task.deliverable}
        placeholder="e.g. Source-grounded analytical essay (750–1000 words)"
      />
    </div>
  </div>
</section>

<style>
  .card-section {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 12px;
    padding: 28px 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  :global(.dark-mode) .card-section {
    background: #181b20;
    border-color: #2a2e36;
  }

  .card-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
    border-bottom: 1px solid var(--border, #DDDCD5);
    padding-bottom: 16px;
  }

  :global(.dark-mode) .card-header {
    border-color: #2a2e36;
  }

  .header-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .card-header h2 {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 2px 0 0;
  }

  :global(.dark-mode) .card-header h2 {
    color: #f1f5f9;
  }

  .section-desc {
    font-size: 13px;
    color: var(--color-slate, #6D7378);
    margin: 0;
  }

  :global(.dark-mode) .section-desc {
    color: #94a3b8;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-group label {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-heading, #111315);
  }

  :global(.dark-mode) .form-group label {
    color: #cbd5e1;
  }

  .input-text,
  .input-textarea {
    width: 100%;
    padding: 9px 12px;
    font-size: 13.5px;
    font-family: inherit;
    border-radius: 6px;
    border: 1px solid var(--border, #DDDCD5);
    background: var(--input-bg, #ffffff);
    color: var(--color-heading, #111315);
    box-sizing: border-box;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  :global(.dark-mode) .input-text,
  :global(.dark-mode) .input-textarea {
    background: #111317;
    border-color: #2e3440;
    color: #f1f5f9;
  }

  .input-text:focus,
  .input-textarea:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4F6BFF);
    box-shadow: 0 0 0 3px rgba(79, 107, 255, 0.12);
  }

  .title-input {
    font-size: 16px;
    font-weight: 600;
  }

  .prompt-area {
    line-height: 1.5;
    resize: vertical;
  }

  .two-col-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  @media (max-width: 720px) {
    .two-col-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
