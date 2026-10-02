<script lang="ts">
  let {
    item,
    index = 0,
    totalCount = 0,
  } = $props<{
    item: any;
    index?: number;
    totalCount?: number;
  }>();
</script>

<div class="milestone-entry">
  <!-- Left Rail: Marker & Line -->
  <div class="rail-column">
    <div class="rail-node {item.type === 'baseline' ? 'baseline-node' : 'active-node'}">
      {totalCount - index}
    </div>
    {#if index < totalCount - 1}
      <div class="rail-line"></div>
    {/if}
  </div>

  <!-- Right Content Card -->
  <div class="milestone-card">
    <div class="card-top">
      <div class="card-title-col">
        <div class="meta-row">
          <span class="course-chip">{item.courseId}</span>
          <span class="date-chip">{item.date}</span>
          <span class="badge {item.badgeClass}">{item.status}</span>
        </div>
        <h3 class="milestone-title">{item.title}</h3>
      </div>

      <div class="score-pill">
        <span class="score-label">Evaluation</span>
        <span class="score-val">{item.score}</span>
      </div>
    </div>

    <!-- Growth Insight Box -->
    <div class="growth-insight-box">
      <div class="insight-header">
        <span class="insight-tag">🌱 KEY EPISTEMIC GROWTH</span>
        <span class="autonomy-tag">{item.autonomyLevel} • {item.autonomyScore}% Autonomy</span>
      </div>
      <p class="growth-text">{item.growthNote}</p>
      {#if item.evidenceQuote}
        <blockquote class="milestone-quote">
          "{item.evidenceQuote}"
        </blockquote>
      {/if}
    </div>

    <!-- Metrics & Verification Footer -->
    <div class="milestone-footer">
      <div class="footer-metrics">
        <span class="footer-stat">
          <strong>{item.hintsUsed}</strong> {item.hintsUsed === 1 ? 'hint' : 'hints'} used
        </span>
        <span class="stat-bullet">•</span>
        <span class="footer-stat">
          <strong>{item.selfCorrections}</strong> {item.selfCorrections === 1 ? 'self-correction' : 'self-corrections'}
        </span>
        <span class="stat-bullet">•</span>
        <span class="footer-stat verification-stat">
          🛡️ {item.verifiedProtocol}
        </span>
      </div>

      <div class="footer-actions">
        <a href="#/student/portal" class="btn btn-secondary" style="font-size: 11.5px; padding: 6px 12px;">
          View Course →
        </a>
        <a href="#/student" class="btn btn-primary" style="font-size: 11.5px; padding: 6px 14px;">
          Resume Canvas →
        </a>
      </div>
    </div>
  </div>
</div>

<style>
  .milestone-entry {
    display: flex;
    gap: 24px;
    position: relative;
  }

  .rail-column {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 36px;
    flex-shrink: 0;
  }

  .rail-node {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    z-index: 2;
  }

  .active-node {
    background: var(--color-horizon-blue);
    color: #ffffff;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
  }

  .baseline-node {
    background: var(--color-graphite-card);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-muted);
  }

  .rail-line {
    width: 2px;
    flex: 1;
    background: var(--color-graphite-border);
    margin: 8px 0;
  }

  .milestone-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 22px 24px;
    flex: 1;
    margin-bottom: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    transition: all 0.2s ease;
  }

  .milestone-card:hover {
    border-color: var(--color-slate-subtle);
    box-shadow: var(--shadow-md);
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }

  .card-title-col {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .course-chip {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: var(--radius-xs);
    background: var(--pill-bg);
    color: var(--color-horizon-bright);
    letter-spacing: 0.5px;
  }

  .date-chip {
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .badge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: var(--radius-xs);
    text-transform: uppercase;
  }

  .badge-success {
    background: var(--color-signal-green-bg);
    color: var(--color-signal-green);
  }

  .badge-info {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
  }

  .badge-neutral {
    background: var(--pill-bg);
    color: var(--color-slate-muted);
  }

  .milestone-title {
    font-family: var(--font-brand);
    font-size: 17px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
    line-height: 1.35;
  }

  .score-pill {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 6px 12px;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 1px;
    flex-shrink: 0;
  }

  .score-label {
    font-size: 9.5px;
    font-weight: 600;
    color: var(--color-slate-muted);
    text-transform: uppercase;
  }

  .score-val {
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-signal-green);
  }

  .growth-insight-box {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-left: 3px solid var(--color-signal-green);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }

  .insight-tag {
    color: var(--color-signal-green);
  }

  .autonomy-tag {
    color: var(--color-horizon-bright);
  }

  .growth-text {
    font-size: 13px;
    color: var(--color-slate-bright);
    line-height: 1.5;
    margin: 0;
  }

  .milestone-quote {
    font-size: 12px;
    font-style: italic;
    color: var(--color-slate-light);
    margin: 4px 0 0;
    padding-left: 10px;
    border-left: 2px solid var(--color-slate-subtle);
  }

  .milestone-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--color-graphite-border);
    flex-wrap: wrap;
  }

  .footer-metrics {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
    color: var(--color-slate-light);
    flex-wrap: wrap;
  }

  .footer-stat strong {
    color: var(--color-slate-bright);
  }

  .stat-bullet {
    color: var(--color-slate-subtle);
  }

  .verification-stat {
    color: var(--color-horizon-bright);
  }

  .footer-actions {
    display: flex;
    gap: 8px;
  }

  .btn {
    border-radius: var(--radius-sm);
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    transition: all 0.15s ease;
    border: 1px solid transparent;
  }

  .btn-primary {
    background: var(--color-horizon-blue);
    color: #ffffff;
  }
  .btn-primary:hover {
    background: var(--color-horizon-bright);
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
</style>
