<script lang="ts">
  let {
    autonomyScore = 88.4,
    autonomyLevel = 'Level 4 Independent',
    growthDelta = '+26.4%',
  } = $props<{
    autonomyScore?: number;
    autonomyLevel?: string;
    growthDelta?: string;
  }>();
</script>

<!-- Progression Summary KPIs -->
<section class="kpi-grid">
  <div class="kpi-card">
    <span class="kpi-icon">📈</span>
    <div class="kpi-meta">
      <span class="kpi-label">Autonomy Index</span>
      <div class="kpi-value-row">
        <span class="kpi-value highlight-accent">{autonomyScore}%</span>
        <span class="kpi-badge badge-green">Top Decile</span>
      </div>
      <span class="kpi-sub">Grew from 62.0% at baseline</span>
    </div>
  </div>

  <div class="kpi-card">
    <span class="kpi-icon">💡</span>
    <div class="kpi-meta">
      <span class="kpi-label">Socratic Hint Dependency</span>
      <div class="kpi-value-row">
        <span class="kpi-value highlight-green">0.18</span>
        <span class="kpi-badge badge-green">Decreased 78%</span>
      </div>
      <span class="kpi-sub">Minimal tutor scaffolding required</span>
    </div>
  </div>

  <div class="kpi-card">
    <span class="kpi-icon">🛡️</span>
    <div class="kpi-meta">
      <span class="kpi-label">Verifiable Claims Entailment</span>
      <div class="kpi-value-row">
        <span class="kpi-value">18 / 20</span>
        <span class="kpi-badge badge-blue">90% Entailed</span>
      </div>
      <span class="kpi-sub">Verified via DeBERTa-v3 model</span>
    </div>
  </div>

  <div class="kpi-card">
    <span class="kpi-icon">🔄</span>
    <div class="kpi-meta">
      <span class="kpi-label">Autonomous Self-Corrections</span>
      <div class="kpi-value-row">
        <span class="kpi-value highlight-purple">4 Major</span>
        <span class="kpi-badge badge-purple">Zero Penalty</span>
      </div>
      <span class="kpi-sub">Pivots made upon examining primary data</span>
    </div>
  </div>
</section>

<style>
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }

  .kpi-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
    transition: transform 0.2s, border-color 0.2s;
  }

  .kpi-card:hover {
    border-color: var(--color-slate-subtle);
    transform: translateY(-2px);
  }

  .kpi-icon {
    font-size: 24px;
  }

  .kpi-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
  }

  .kpi-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-muted);
  }

  .kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .kpi-value {
    font-family: var(--font-brand);
    font-size: 22px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .kpi-value.highlight-accent {
    color: var(--color-horizon-bright);
  }

  .kpi-value.highlight-green {
    color: var(--color-signal-green);
  }

  .kpi-value.highlight-purple {
    color: #a855f7;
  }

  .kpi-badge {
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: var(--radius-xs);
    text-transform: uppercase;
  }

  .badge-green {
    background: var(--color-signal-green-bg);
    color: var(--color-signal-green);
  }

  .badge-blue {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
  }

  .badge-purple {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
  }

  .kpi-sub {
    font-size: 11px;
    color: var(--color-slate-subtle);
  }

  @media (max-width: 900px) {
    .kpi-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 540px) {
    .kpi-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
