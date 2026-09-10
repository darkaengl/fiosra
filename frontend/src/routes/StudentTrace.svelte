<script>
  import { onMount } from 'svelte';
  import {
    formatDate,
    getStudentId,
    responseError,
    routeParams,
    sessionAccessTokenStorageKey,
    sessionStorageKey,
  } from '../lib/session.js';

  let courseId = $state('');
  let assignmentId = $state('');
  let sessionId = $state('');
  let sessionAccessToken = $state('');
  let trace = $state([]);
  let dossier = $state(null);
  let activeNode = $state(null);
  let isLoading = $state(true);
  let isSubmitting = $state(false);
  let status = $state('');
  let error = $state('');

  function eventTitle(event) {
    const titles = {
      student_prompt_submitted: 'Reasoning attempt',
      tutor_turn_completed: 'Socratic probe',
      hint_delivered: 'Requested scaffold',
      adversarial_probe_defended: 'Integrity boundary',
      misconception_flagged: 'Misconception signal',
      canvas_section_saved: 'Canvas section revised',
      canvas_suggestion_offered: 'Optional support offered',
      canvas_suggestion_accepted: 'Support frame applied and edited',
      canvas_suggestion_dismissed: 'Support frame dismissed',
      student_submitted_for_review: 'Submitted for educator review',
      grade_finalised_by_educator: 'Educator finalization',
    };
    return titles[event.event_type] || event.event_type.replaceAll('_', ' ');
  }

  function eventClass(event) {
    if (event.event_type === 'student_prompt_submitted') return 'student';
    if (event.event_type === 'hint_delivered') return 'hint';
    if (event.event_type.startsWith('canvas_')) return 'canvas';
    if (event.event_type === 'adversarial_probe_defended') return 'guardrail';
    if (event.event_type.includes('submitted') || event.event_type.includes('finalised')) return 'complete';
    return 'tutor';
  }

  async function loadTrace() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    assignmentId = params.get('assignment_id') || '';
    sessionId = params.get('session_id') || '';
    if (!sessionId) return;
    const persistedSessionId = localStorage.getItem(sessionStorageKey(assignmentId, getStudentId()));
    if (persistedSessionId !== sessionId) {
      throw new Error('Open the protected canvas from this browser to view this reasoning trace.');
    }
    sessionAccessToken = localStorage.getItem(sessionAccessTokenStorageKey(sessionId)) || '';
    if (!sessionAccessToken) {
      throw new Error('This browser no longer holds access to the protected reasoning session.');
    }
    const sessionHeaders = { 'X-Fiosra-Session-Token': sessionAccessToken };

    const [traceResponse, dossierResponse, sessionResponse] = await Promise.all([
      fetch(`/evidence/trace/${sessionId}`),
      fetch(`/evidence/dossier/${sessionId}`),
      fetch(`/events/session/${sessionId}`, { headers: sessionHeaders }),
    ]);
    if (!traceResponse.ok) throw new Error(await responseError(traceResponse, 'The reasoning trace could not be loaded.'));
    if (!dossierResponse.ok) throw new Error(await responseError(dossierResponse, 'The evidence dossier could not be loaded.'));
    trace = (await traceResponse.json()).trace_nodes || [];
    dossier = await dossierResponse.json();
    if (sessionResponse.ok) status = (await sessionResponse.json()).session.status;
    activeNode = trace[trace.length - 1]?.event_id || null;
  }

  async function submitForReview() {
    if (!sessionId || status !== 'active') return;
    isSubmitting = true;
    error = '';
    try {
      const response = await fetch(`/events/session/${sessionId}/submit`, {
        method: 'POST',
        headers: { 'X-Fiosra-Session-Token': sessionAccessToken },
      });
      if (!response.ok) throw new Error(await responseError(response, 'The work could not be submitted.'));
      status = 'submitted';
      await loadTrace();
    } catch (err) {
      error = err.message || 'The work could not be submitted.';
    } finally {
      isSubmitting = false;
    }
  }

  onMount(async () => {
    try {
      await loadTrace();
    } catch (err) {
      error = err.message || 'The reasoning trace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

<main class="trace-page">
  {#if isLoading}
    <div class="loading"><div class="spinner"></div><span>Assembling your evidence packet…</span></div>
  {:else if !sessionId}
    <div class="empty"><h1>No active reasoning trace</h1><p>Open a student canvas and begin a reasoning session to build an evidence trace.</p><a class="btn btn-primary" href="#/courses">Choose a course</a></div>
  {:else if error && !dossier}
    <div class="empty"><h1>Trace unavailable</h1><p>{error}</p><a class="btn btn-secondary" href="#/student">Return to canvas</a></div>
  {:else}
    <header class="trace-header">
      <div><div class="eyebrow">Student evidence packet</div><h1>A path made visible</h1><p>Review the chronological record of your claims, requested support, and revisions before sharing it with your educator.</p></div>
      <div class="score-card"><span>Suggested AutoSCORE</span><strong>{dossier?.executive_summary?.suggested_grade || '—'}</strong><small>{dossier?.executive_summary?.autonomy_rating || 'No score yet'}</small></div>
    </header>

    <section class="metric-grid">
      <div><span>Reasoning events</span><strong>{trace.length}</strong></div>
      <div><span>Hint dependency</span><strong>{Math.round((dossier?.aggregate_metrics?.hint_dependency_ratio || 0) * 100)}%</strong></div>
      <div><span>Misconceptions encountered</span><strong>{dossier?.aggregate_metrics?.total_misconceptions_encountered || 0}</strong></div>
      <div><span>Session status</span><strong class:active={status === 'active'} class:submitted={status === 'submitted'}>{status || 'unknown'}</strong></div>
    </section>

    <section class="trace-card">
      <div class="card-heading"><div><h2>Chronological reasoning trace</h2><p>Each entry is drawn from the append-only flight recorder.</p></div><span>{trace.length} nodes</span></div>
      {#if trace.length === 0}
        <div class="empty-trace">No reasoning events have been recorded yet. Return to the canvas and articulate an initial claim.</div>
      {:else}
        <div class="timeline">
          {#each trace as event, index (event.event_id)}
            <button class:active={activeNode === event.event_id} class={`timeline-row ${eventClass(event)}`} onclick={() => activeNode = event.event_id}>
              <span class="node">{index + 1}</span>
              <span class="event-copy"><strong>{eventTitle(event)}</strong><small>{formatDate(event.timestamp)}</small><span>{event.summary}</span></span>
            </button>
          {/each}
        </div>
      {/if}
    </section>

    {#if activeNode}
      {@const selected = trace.find((event) => event.event_id === activeNode)}
      {#if selected}
        <section class="detail-card">
          <div class="eyebrow">Selected trace evidence</div>
          <h2>{eventTitle(selected)}</h2>
          <p>{selected.summary}</p>
          {#if selected.payload?.thoughts_of_tutorbot}<div class="reflection"><strong>Socratic strategy</strong><span>{selected.payload.thoughts_of_tutorbot.strategy_selected}</span></div>{/if}
        </section>
      {/if}
    {/if}

    <section class="submission-card">
      <div><h2>{status === 'completed' ? 'Educator review completed' : status === 'submitted' ? 'Submitted for educator review' : 'Ready for educator review?'}</h2><p>{status === 'active' ? 'Submitting sends your complete event trace and evidence dossier to the educator’s review queue. It does not assign a grade.' : status === 'submitted' ? 'Your reasoning trace is now waiting for a sovereign educator decision.' : 'The educator has recorded a final outcome for this session.'}</p></div>
      <div class="submission-actions">
        <a class="btn btn-secondary" href={`#/student?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}`}>Back to canvas</a>
        {#if status === 'active'}<button class="btn btn-success" onclick={submitForReview} disabled={isSubmitting || trace.length === 0}>{isSubmitting ? 'Submitting…' : 'Submit for review'}</button>{/if}
        {#if status === 'submitted'}<a class="btn btn-primary" href={`#/review?course_id=${encodeURIComponent(courseId)}`}>Open review queue →</a>{/if}
      </div>
    </section>
    {#if error}<div class="error-banner">{error}</div>{/if}
  {/if}
</main>

<style>
  .trace-page{background:var(--color-obsidian);color:var(--color-slate-bright);min-height:calc(100vh - 56px);padding:38px 24px 80px}.trace-header,.metric-grid,.trace-card,.detail-card,.submission-card{max-width:1120px;margin-left:auto;margin-right:auto}.trace-header{border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;gap:28px;padding-bottom:24px}.eyebrow{color:var(--color-slate-muted);font-size:11px;font-weight:700;letter-spacing:.55px;text-transform:uppercase}.trace-header h1{color:#fff;font-family:var(--font-brand);font-size:29px;margin:5px 0 6px}.trace-header p{color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;max-width:720px}.score-card{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:3px;min-width:160px;padding:15px;text-align:right}.score-card span,.score-card small{color:var(--color-slate-muted);font-size:10px;text-transform:uppercase}.score-card strong{color:#6ee7b7;font-family:var(--font-brand);font-size:30px}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:24px}.metric-grid>div{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:5px;padding:15px}.metric-grid span{color:var(--color-slate-muted);font-size:10px;font-weight:700;text-transform:uppercase}.metric-grid strong{color:#fff;font-family:var(--font-brand);font-size:20px;text-transform:capitalize}.metric-grid strong.active{color:#6ee7b7}.metric-grid strong.submitted{color:#fcd34d}.trace-card,.detail-card,.submission-card{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);margin-top:20px;padding:22px}.card-heading{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;gap:15px;padding-bottom:14px}.card-heading h2,.detail-card h2,.submission-card h2{color:#fff;font-size:16px;margin:0 0 4px}.card-heading p,.submission-card p{color:var(--color-slate-muted);font-size:12px;margin:0}.card-heading>span{color:var(--color-horizon-bright);font-size:11px;font-weight:700}.timeline{display:flex;flex-direction:column;margin-top:8px}.timeline-row{align-items:flex-start;background:transparent;border:0;border-left:2px solid var(--color-graphite-border);color:inherit;cursor:pointer;display:flex;gap:13px;padding:13px 0 13px 16px;text-align:left;width:100%}.timeline-row:hover,.timeline-row.active{background:rgba(59,130,246,.07);border-left-color:var(--color-horizon-bright)}.node{align-items:center;background:var(--color-graphite-card);border:1px solid var(--color-graphite-border);border-radius:50%;color:var(--color-slate-light);display:flex;flex:0 0 28px;font-size:11px;font-weight:700;height:28px;justify-content:center}.student .node{border-color:#0ea5e9;color:#7dd3fc}.hint .node{border-color:#f59e0b;color:#fcd34d}.guardrail .node{border-color:#ef4444;color:#fca5a5}.complete .node{border-color:#10b981;color:#6ee7b7}.event-copy{display:flex;flex-direction:column;gap:2px;min-width:0}.event-copy strong{color:#e2e8f0;font-size:12px;text-transform:capitalize}.event-copy small{color:var(--color-slate-muted);font-size:10px}.event-copy>span{color:var(--color-slate-light);font-size:12px;line-height:1.5;margin-top:3px;overflow-wrap:anywhere}.detail-card p{color:var(--color-slate-light);font-size:13px;line-height:1.6;margin:9px 0}.reflection{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:flex;flex-direction:column;gap:4px;padding:12px}.reflection strong{color:var(--color-horizon-bright);font-size:11px;text-transform:uppercase}.reflection span{color:var(--color-slate-light);font-size:12px}.submission-card{align-items:center;background:linear-gradient(135deg,rgba(16,185,129,.11),rgba(59,130,246,.1));border-color:rgba(16,185,129,.3);display:flex;justify-content:space-between;gap:22px}.submission-card p{line-height:1.5;max-width:650px}.submission-actions{display:flex;gap:10px;flex-shrink:0}.error-banner{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:var(--radius-sm);color:#fca5a5;font-size:12px;margin:12px auto 0;max-width:1120px;padding:10px 12px}.empty-trace{color:var(--color-slate-muted);font-size:13px;padding:28px 0;text-align:center}.loading,.empty{align-items:center;display:flex;flex-direction:column;gap:13px;justify-content:center;min-height:calc(100vh - 160px);text-align:center}.empty h1{color:#fff;font-family:var(--font-brand);font-size:25px}.empty p{color:var(--color-slate-light);max-width:500px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:28px;width:28px}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:780px){.trace-page{padding:26px 16px 60px}.trace-header,.submission-card{align-items:flex-start;flex-direction:column}.metric-grid{grid-template-columns:repeat(2,1fr)}.submission-actions{width:100%}.submission-actions .btn{flex:1}}@media(max-width:460px){.metric-grid{grid-template-columns:1fr}.submission-actions{flex-direction:column}.score-card{text-align:left;width:100%}}
</style>
