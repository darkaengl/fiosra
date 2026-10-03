<script lang="ts">
  let { onExport = () => {} } = $props<{ onExport?: () => void }>();
</script>

<section class="pathway-card">
  <div class="pathway-header">
    <div>
      <h2 class="pathway-title">Longitudinal Autonomy Stages</h2>
      <p class="pathway-desc">Progressive shift from guided scaffolding to authentic autonomous scholarship</p>
    </div>
    <button type="button" class="btn btn-secondary" onclick={onExport} style="font-size: 12px; padding: 7px 14px;">
      📄 Export Verifiable Proof (.json-ld)
    </button>
  </div>

  <div class="stage-track">
    <div class="stage-step completed">
      <div class="stage-indicator">✓</div>
      <div class="stage-info">
        <span class="stage-name">Stage 1: Guided Inquiries</span>
        <span class="stage-detail">Initial baseline • High hint dependency</span>
      </div>
    </div>

    <div class="stage-connector active"></div>

    <div class="stage-step completed">
      <div class="stage-indicator">✓</div>
      <div class="stage-info">
        <span class="stage-name">Stage 2: Socratic Probing</span>
        <span class="stage-detail">Defending claims against counter-evidence</span>
      </div>
    </div>

    <div class="stage-connector active"></div>

    <div class="stage-step completed">
      <div class="stage-indicator">✓</div>
      <div class="stage-info">
        <span class="stage-name">Stage 3: Evidence Synthesis</span>
        <span class="stage-detail">Primary text citation & self-correction</span>
      </div>
    </div>

    <div class="stage-connector active"></div>

    <div class="stage-step active">
      <div class="stage-indicator">★</div>
      <div class="stage-info">
        <span class="stage-name">Stage 4: Autonomous Reasoner</span>
        <span class="stage-detail">Active level • Top decile independence</span>
      </div>
    </div>
  </div>
</section>

<style>
  .pathway-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    box-shadow: var(--shadow-sm);
  }

  .pathway-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .pathway-title {
    font-family: var(--font-brand);
    font-size: 18px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
  }

  .pathway-desc {
    font-size: 12.5px;
    color: var(--color-slate-light);
    margin: 4px 0 0;
  }

  .stage-track {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 0 4px;
    overflow-x: auto;
  }

  .stage-step {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 170px;
  }

  .stage-indicator {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
    background: var(--pill-bg);
    color: var(--color-slate-muted);
    border: 1px solid var(--color-graphite-border);
  }

  .stage-step.completed .stage-indicator {
    background: var(--color-signal-green);
    color: #ffffff;
    border-color: var(--color-signal-green);
  }

  .stage-step.active .stage-indicator {
    background: var(--color-horizon-blue);
    color: #ffffff;
    border-color: var(--color-horizon-bright);
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
  }

  .stage-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stage-name {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .stage-detail {
    font-size: 10.5px;
    color: var(--color-slate-subtle);
  }

  .stage-connector {
    height: 2px;
    flex: 0.5;
    background: var(--color-graphite-border);
    min-width: 20px;
  }

  .stage-connector.active {
    background: var(--color-signal-green);
  }

  .btn {
    border-radius: var(--radius-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid transparent;
  }

  .btn-secondary {
    background: var(--color-graphite);
    border-color: var(--color-graphite-border);
    color: var(--color-slate-bright);
  }

  .btn-secondary:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }

  @media (max-width: 860px) {
    .stage-track {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }
    .stage-connector {
      display: none;
    }
  }
</style>
