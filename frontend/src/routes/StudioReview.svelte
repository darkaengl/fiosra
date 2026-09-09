<script>
  const submissions = [
    { student: 'Alex Chen', initials: 'AC', score: 87, rubric: [25, 30, 18, 14], status: 'auto-scored', flags: 1, assignment: 'Essay: Fiscal Crisis & Sovereignty' },
    { student: 'Maria Santos', initials: 'MS', score: 72, rubric: [20, 22, 16, 14], status: 'needs-review', flags: 2, assignment: 'Essay: Fiscal Crisis & Sovereignty' },
    { student: 'James Park', initials: 'JP', score: 94, rubric: [25, 35, 20, 14], status: 'approved', flags: 0, assignment: 'Essay: Fiscal Crisis & Sovereignty' },
    { student: 'Sarah Mitchell', initials: 'SM', score: 61, rubric: [18, 20, 12, 11], status: 'needs-review', flags: 3, assignment: 'Essay: Fiscal Crisis & Sovereignty' },
    { student: 'Tom Rodriguez', initials: 'TR', score: 79, rubric: [22, 28, 16, 13], status: 'auto-scored', flags: 1, assignment: 'Essay: Fiscal Crisis & Sovereignty' },
  ];

  const kpis = [
    { label: 'Submissions Scored', value: '24', sub: 'Pending: 4', color: 'var(--color-horizon-bright)' },
    { label: 'Avg AutoSCORE', value: '78%', sub: 'vs 71% prev cohort', color: '#34d399' },
    { label: 'Misconception Flags', value: '31', sub: 'Across 28 students', color: 'var(--color-amber)' },
    { label: 'Needs Review', value: '4', sub: 'Instructor approval', color: 'var(--color-rose)' },
  ];

  function statusBadge(status) {
    if (status === 'approved') return { label: '✓ Approved', class: 'badge-green' };
    if (status === 'auto-scored') return { label: '⚡ Auto-Scored', class: 'badge-blue' };
    return { label: '⚠ Needs Review', class: 'badge-amber' };
  }
</script>

<main class="review-main">
  <div class="review-header">
    <div>
      <h1 class="review-title">AutoSCORE Review Dashboard</h1>
      <p class="review-subtitle">DeBERTa NLI grounded rubric scoring • pgvector claim verification</p>
    </div>
    <div class="header-actions">
      <button class="btn btn-secondary">Export Results</button>
      <button class="btn btn-primary">Approve All Auto-Scored</button>
    </div>
  </div>

  <div class="kpi-grid">
    {#each kpis as kpi}
      <div class="kpi-card">
        <div class="kpi-label">{kpi.label}</div>
        <div class="kpi-value" style="color: {kpi.color}">{kpi.value}</div>
        <div class="kpi-sub">{kpi.sub}</div>
      </div>
    {/each}
  </div>

  <div class="submissions-panel">
    <div class="panel-header">
      <div class="panel-title">📋 Submission Review Queue</div>
      <div style="font-size: 12px; color: var(--color-slate-muted);">Assignment: Essay — Fiscal Crisis & Sovereignty</div>
    </div>
    <table class="review-table">
      <thead>
        <tr>
          <th>Student</th>
          <th>AutoSCORE</th>
          <th>Rubric Breakdown</th>
          <th>Misconception Flags</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each submissions as s}
          {@const badge = statusBadge(s.status)}
          <tr>
            <td>
              <div class="student-cell">
                <div class="student-avatar">{s.initials}</div>
                <span>{s.student}</span>
              </div>
            </td>
            <td>
              <div class="score-cell">
                <span class="score-number">{s.score}</span>
                <span class="score-denom">/100</span>
              </div>
            </td>
            <td>
              <div class="rubric-bars">
                {#each s.rubric as pts, i}
                  <div class="rubric-bar-item">
                    <div class="rubric-bar-fill" style="width: {(pts / [25,35,20,20][i]) * 100}%; background: var(--color-horizon-blue);"></div>
                  </div>
                {/each}
              </div>
            </td>
            <td><span class="flag-count {s.flags > 1 ? 'flag-high' : ''}">{s.flags} flag{s.flags !== 1 ? 's' : ''}</span></td>
            <td><span class="status-badge {badge.class}">{badge.label}</span></td>
            <td>
              <div class="action-btns">
                <button class="btn-xs btn-ghost">Review</button>
                <button class="btn-xs btn-approve">Approve</button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</main>

<style>
  .review-main { padding: 32px 40px 80px; max-width: 1440px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
  .review-header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid var(--color-graphite-border); padding-bottom: 24px; }
  .review-title { font-family: var(--font-brand); font-size: 24px; font-weight: 700; color: #fff; margin: 0 0 4px; }
  .review-subtitle { font-size: 13px; color: var(--color-slate-muted); margin: 0; }
  .header-actions { display: flex; gap: 12px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
  .kpi-card { background: var(--color-graphite); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-md); padding: 20px 22px; }
  .kpi-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: var(--color-slate-muted); margin-bottom: 6px; }
  .kpi-value { font-family: var(--font-brand); font-size: 28px; font-weight: 700; line-height: 1; }
  .kpi-sub { font-size: 11px; color: var(--color-slate-muted); margin-top: 4px; }
  .submissions-panel { background: var(--color-graphite); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-lg); overflow: hidden; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--color-graphite-border); }
  .panel-title { font-size: 14px; font-weight: 700; color: #fff; }
  .review-table { width: 100%; border-collapse: collapse; }
  .review-table th { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: var(--color-slate-muted); padding: 12px 24px; text-align: left; background: var(--color-graphite-card); }
  .review-table td { padding: 16px 24px; border-top: 1px solid var(--color-graphite-border); }
  .review-table tbody tr:hover { background: rgba(255,255,255,.02); }
  .student-cell { display: flex; align-items: center; gap: 10px; }
  .student-avatar { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #8b5cf6); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #fff; flex-shrink: 0; }
  .score-cell { display: flex; align-items: baseline; gap: 2px; }
  .score-number { font-family: var(--font-brand); font-size: 20px; font-weight: 700; color: #fff; }
  .score-denom { font-size: 12px; color: var(--color-slate-muted); }
  .rubric-bars { display: flex; flex-direction: column; gap: 3px; width: 120px; }
  .rubric-bar-item { height: 4px; background: var(--color-graphite-border); border-radius: 2px; overflow: hidden; }
  .rubric-bar-fill { height: 100%; border-radius: 2px; }
  .flag-count { font-size: 12px; font-weight: 600; color: var(--color-slate-light); }
  .flag-count.flag-high { color: var(--color-amber); }
  .status-badge { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: var(--radius-xs); }
  .badge-green { background: rgba(16,185,129,.15); color: #34d399; border: 1px solid rgba(16,185,129,.3); }
  .badge-blue { background: rgba(59,130,246,.15); color: var(--color-horizon-bright); border: 1px solid rgba(59,130,246,.3); }
  .badge-amber { background: rgba(245,158,11,.15); color: var(--color-amber); border: 1px solid rgba(245,158,11,.3); }
  .action-btns { display: flex; gap: 6px; }
  .btn-xs { font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: var(--radius-xs); cursor: pointer; border: 1px solid var(--color-graphite-border); }
  .btn-ghost { background: none; color: var(--color-slate-light); }
  .btn-approve { background: rgba(16,185,129,.15); color: #34d399; border-color: rgba(16,185,129,.3); }
</style>
