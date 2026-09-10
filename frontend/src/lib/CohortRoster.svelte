<script>
  import ScoreMeter from './ScoreMeter.svelte';

  let {
    students = [],
    courseId = '',
    onDispatchScaffold,
  } = $props();
</script>

<div class="roster-wrapper">
  <div class="roster-table-scroll">
    <table class="roster-table">
      <thead>
        <tr>
          <th style="min-width: 220px;">Student Learner</th>
          <th style="min-width: 180px;">Current Milestone</th>
          <th style="min-width: 140px;">Autonomy Score (A&#772;<sub>s</sub>)</th>
          <th style="min-width: 130px;">Hint Rate</th>
          <th style="min-width: 190px;">Active Cognitive Traps</th>
          <th style="min-width: 130px;">Diagnostic Status</th>
          <th style="min-width: 90px; text-align: right;">Action</th>
        </tr>
      </thead>
      <tbody>
        {#if students.length === 0}
          <tr>
            <td colspan="7" class="roster-empty">
              No students enrolled in this cohort yet. Student profiles will populate automatically as learners log Socratic sessions.
            </td>
          </tr>
        {:else}
          {#each students as stu (stu.student_id)}
            <tr>
              <td>
                <div class="student-cell">
                  <div class="student-avatar">
                    {stu.student_id.substring(0, 2).toUpperCase()}
                  </div>
                  <div class="student-info">
                    <div class="student-id">{stu.student_id}</div>
                    <div class="student-sub">{stu.session_count || 0} Sessions Logged</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="milestone-text">
                  {stu.completed_assignments > 0
                    ? `${stu.completed_assignments} Assignments Completed`
                    : 'Canvas Active'}
                </span>
              </td>
              <td>
                <ScoreMeter score={stu.average_autonomy_score || 0} />
              </td>
              <td>
                <span class="hint-rate-chip">
                  {Math.round((stu.hint_consumption_rate || 0) * 100)}%
                </span>
              </td>
              <td>
                {#if stu.active_struggle && stu.struggling_kcs?.length > 0}
                  <span class="struggle-warning">
                    ⚠️ {stu.struggling_kcs.join(', ')}
                  </span>
                {:else}
                  <span class="no-struggle">None Detected</span>
                {/if}
              </td>
              <td>
                <span class="badge {stu.active_struggle ? 'badge-warning' : 'badge-success'}">
                  {stu.active_struggle ? 'Needs Scaffolding' : 'Progressing'}
                </span>
              </td>
              <td style="text-align: right;">
                <a
                  href="#/student/trace?student_id={encodeURIComponent(stu.student_id)}&course_id={encodeURIComponent(courseId)}"
                  class="btn btn-secondary btn-xs"
                >
                  Trace ↗
                </a>
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <div class="roster-footer">
    <span class="footer-meta">
      Showing {students.length} active students in cohort roster.
    </span>
    <button
      type="button"
      class="btn btn-secondary btn-sm"
      onclick={() => onDispatchScaffold?.()}
    >
      🚀 Dispatch Targeted Socratic Micro-Scaffold
    </button>
  </div>
</div>

<style>
  .roster-wrapper {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .roster-table-scroll {
    width: 100%;
    overflow-x: auto;
  }

  .roster-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  .roster-table th {
    background: var(--color-graphite-card);
    padding: 12px 18px;
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-slate-light);
    border-bottom: 1px solid var(--color-graphite-border);
    white-space: nowrap;
  }

  .roster-table td {
    padding: 14px 18px;
    border-bottom: 1px solid var(--color-graphite-border);
    color: var(--color-slate-bright);
    vertical-align: middle;
  }

  .roster-table tr:hover td {
    background: var(--color-graphite-hover);
  }

  .roster-empty {
    text-align: center;
    padding: 36px !important;
    color: var(--color-slate-muted);
    font-style: italic;
  }

  .student-cell {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .student-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10.5px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
  }

  .student-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .student-id {
    font-weight: 600;
    color: var(--color-heading);
    font-size: 12.5px;
  }

  .student-sub {
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .milestone-text {
    font-size: 12.5px;
    color: var(--color-slate-light);
  }

  .hint-rate-chip {
    font-size: 11.5px;
    font-family: var(--font-mono);
    color: var(--color-slate-bright);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 7px;
    border-radius: var(--radius-xs);
  }

  .struggle-warning {
    color: var(--color-rose);
    font-weight: 600;
    font-size: 12px;
  }

  .no-struggle {
    color: var(--color-signal-green);
    font-size: 12px;
  }

  .roster-footer {
    padding: 12px 20px;
    background: var(--color-graphite-card);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .footer-meta {
    font-size: 12px;
    color: var(--color-slate-light);
  }

  .btn-sm {
    padding: 5px 12px;
    font-size: 11.5px;
  }

  .btn-xs {
    padding: 4px 10px;
    font-size: 11px;
  }
</style>
