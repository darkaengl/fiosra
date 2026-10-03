<script lang="ts">
  import ScoreMeter from '../ScoreMeter.svelte';
  import type { Student } from './rosterTypes';

  let {
    students = [],
    totalCount = 0,
    onEvaluateStudentAssignment,
    onDispatchScaffold,
    onInspectStudentInGraph,
  } = $props<{
    students?: Student[];
    totalCount?: number;
    onEvaluateStudentAssignment?: (assignmentId: string, title?: string, studentId?: string, sessionId?: string) => void;
    onDispatchScaffold?: () => void;
    onInspectStudentInGraph?: (studentId: string) => void;
  }>();
</script>

<div class="roster-table-scroll">
  <table class="roster-table">
    <thead>
      <tr>
        <th style="min-width: 200px;">Student Learner</th>
        <th style="min-width: 220px;">Current Assignment</th>
        <th style="min-width: 140px;">Diagnostic Status</th>
        <th style="min-width: 130px;">Autonomy Score</th>
        <th style="min-width: 110px;">Hint Rate</th>
        <th style="min-width: 220px;">Identified Flags &amp; Frontier</th>
      </tr>
    </thead>
    <tbody>
      {#if students.length === 0}
        <tr>
          <td colspan="6" class="roster-empty">
            No students found matching the selected filter.
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
                  <div class="student-id">{stu.name || stu.student_id}</div>
                  <div class="student-sub">{stu.session_count || 0} Sessions Logged</div>
                </div>
              </div>
            </td>
            <td>
              {#if stu.assignment_id}
                <button
                  type="button"
                  class="assignment-link-btn"
                  title="Inspect {stu.student_id}'s work on this assignment"
                  onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id!, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                >
                  {stu.assignment_title || 'Course Module Task'} ↗
                </button>
              {:else}
                <span class="assignment-text">
                  {stu.assignment_title || 'Course Module Task'}
                </span>
              {/if}
            </td>
            <td>
              {#if stu.status === 'completed' || ((stu.completed_assignments ?? 0) > 0 && stu.status !== 'submitted')}
                {#if stu.assignment_id}
                  <button
                    type="button"
                    class="status-badge badge-completed clickable"
                    title="Inspect {stu.student_id}'s completed reasoning trace"
                    onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id!, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                  >
                    ✓ Completed ↗
                  </button>
                {:else}
                  <span class="status-badge badge-completed">
                    ✓ Completed
                  </span>
                {/if}
              {:else if stu.status === 'submitted'}
                {#if stu.assignment_id}
                  <button
                    type="button"
                    class="status-badge badge-submitted clickable"
                    title="Evaluate {stu.student_id}'s submission"
                    onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id!, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                  >
                    ✓ Submitted ↗
                  </button>
                {:else}
                  <span class="status-badge badge-submitted">
                    ✓ Submitted
                  </span>
                {/if}
              {:else if stu.active_struggle}
                {#if stu.assignment_id}
                  <button
                    type="button"
                    class="status-badge badge-scaffold clickable"
                    title="Inspect {stu.student_id}'s struggle trace"
                    onclick={() => onEvaluateStudentAssignment?.(stu.assignment_id!, stu.assignment_title, stu.student_id, stu.latest_session_id)}
                  >
                    ⚠️ Needs Scaffolding ↗
                  </button>
                {:else}
                  <span class="status-badge badge-scaffold">
                    ⚠️ Needs Scaffolding
                  </span>
                {/if}
              {:else}
                <span class="status-badge badge-progressing">
                  ● In Progress
                </span>
              {/if}
            </td>
            <td>
              <ScoreMeter score={stu.average_autonomy_score ?? 0.85} />
            </td>
            <td>
              <span class="hint-rate-chip">
                {Math.round((stu.hint_frequency ?? 0.1) * 100)}%
              </span>
            </td>
            <td>
              <div class="flags-cell">
                {#if stu.active_struggle}
                  <span class="struggle-warning">
                    ⚠️ At frontier: {stu.frontier_concept || 'Root Axiom'}
                  </span>
                {:else if (stu.critical_thinking_flags || []).length > 0}
                  <span class="struggle-warning">
                    {stu.critical_thinking_flags?.[0]}
                  </span>
                {:else}
                  <span class="no-struggle">Nominal progress</span>
                {/if}
                <button
                  type="button"
                  class="btn-inspect-graph-icon"
                  title="Inspect {stu.student_id}'s frontier in Concept Graph"
                  onclick={() => onInspectStudentInGraph?.(stu.student_id)}
                >
                  Graph ↗
                </button>
              </div>
            </td>
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>

<div class="roster-footer">
  <span class="footer-meta">
    Showing {students.length} of {totalCount} enrolled students.
  </span>
  <button
    type="button"
    class="btn btn-secondary btn-sm"
    onclick={() => onDispatchScaffold?.()}
  >
    🚀 Dispatch Targeted Socratic Micro-Scaffold
  </button>
</div>

<style>
  .roster-table-scroll {
    overflow-x: auto;
    width: 100%;
  }

  .roster-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }

  .roster-table th {
    padding: 10px 18px;
    background: var(--color-graphite, #23272b);
    color: var(--color-slate-light, #6d7378);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
  }

  .roster-table td {
    padding: 12px 18px;
    border-bottom: 1px solid var(--color-graphite-border, #dddcd5);
    vertical-align: middle;
  }

  .roster-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }

  .roster-empty {
    text-align: center;
    padding: 40px;
    color: var(--color-slate-muted, #6d7378);
    font-style: italic;
  }

  .student-cell {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .student-avatar {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-sm, 6px);
    background: var(--color-horizon-muted, #1e293b);
    color: var(--color-horizon-bright, #38bdf8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 11px;
    flex-shrink: 0;
  }

  .student-id {
    font-weight: 600;
    color: var(--color-heading, #111315);
    font-size: 13px;
  }

  .student-sub {
    font-size: 11px;
    color: var(--color-slate-muted, #6d7378);
  }

  .assignment-link-btn {
    background: none;
    border: none;
    padding: 0;
    color: var(--color-horizon-bright, #4f6bff);
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
    transition: color 0.15s;
  }

  .assignment-link-btn:hover {
    color: #60a5fa;
    text-decoration: underline;
  }

  .assignment-text {
    color: var(--color-slate-bright, #111315);
    font-size: 12.5px;
  }

  .status-badge {
    display: inline-flex;
    padding: 3px 8px;
    border-radius: var(--radius-xs, 4px);
    font-size: 11px;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }

  .badge-completed {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #059669;
    font-weight: 700;
  }

  .badge-submitted {
    background: rgba(59, 130, 246, 0.12);
    border: 1px solid rgba(59, 130, 246, 0.28);
    color: #2563eb;
  }

  .status-badge.clickable {
    cursor: pointer;
    border: 1px solid rgba(16, 185, 129, 0.4);
    transition: all 0.15s;
  }

  .status-badge.clickable:hover {
    background: rgba(16, 185, 129, 0.25);
    transform: translateY(-1px);
  }

  .badge-scaffold {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.28);
    color: #f59e0b;
  }

  .badge-progressing {
    background: rgba(59, 130, 246, 0.12);
    border: 1px solid rgba(59, 130, 246, 0.28);
    color: #3b82f6;
  }

  .hint-rate-chip {
    font-size: 11.5px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-bright, #111315);
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 7px;
    border-radius: var(--radius-xs, 4px);
  }

  .flags-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .struggle-warning {
    color: var(--color-rose, #e11d48);
    font-weight: 600;
    font-size: 12px;
  }

  .no-struggle {
    color: var(--color-slate-muted, #6d7378);
    font-size: 12px;
  }

  .btn-inspect-graph-icon {
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid var(--color-graphite-border, #dddcd5);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light, #6d7378);
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }

  .btn-inspect-graph-icon:hover {
    background: #0b4a4f;
    color: #ffffff;
    border-color: #0b4a4f;
  }

  .roster-footer {
    padding: 12px 20px;
    background: var(--color-graphite-card, #ffffff);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .footer-meta {
    font-size: 12px;
    color: var(--color-slate-light, #6d7378);
  }

  .btn-sm {
    padding: 5px 12px;
    font-size: 11.5px;
  }
</style>
