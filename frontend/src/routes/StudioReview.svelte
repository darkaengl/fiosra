<script>
  import { onMount } from 'svelte';
  import { formatDate, responseError, routeParams } from '../lib/session.js';

  let courseId = $state('');
  let queue = $state([]);
  let selected = $state(null);
  let dossier = $state(null);
  let trace = $state([]);
  let grade = $state('');
  let feedback = $state('');
  let teacherId = $state('educator_workspace');
  let isLoading = $state(true);
  let isFinalizing = $state(false);
  let notice = $state('');
  let error = $state('');

  async function loadQueue() {
    error = '';
    const suffix = courseId ? `?course_id=${encodeURIComponent(courseId)}` : '';
    const response = await fetch(`/evidence/review-queue${suffix}`);
    if (!response.ok) throw new Error(await responseError(response, 'The educator review queue could not be loaded.'));
    queue = await response.json();
    if (selected) selected = queue.find((item) => item.session_id === selected.session_id) || null;
    if (!selected && queue.length) await selectItem(queue[0]);
  }

  async function selectItem(item) {
    selected = item;
    dossier = null;
    trace = [];
    feedback = '';
    grade = '';
    error = '';
    const [dossierResponse, traceResponse] = await Promise.all([
      fetch(`/evidence/dossier/${item.session_id}`),
      fetch(`/evidence/trace/${item.session_id}`),
    ]);
    if (!dossierResponse.ok) {
      error = await responseError(dossierResponse, 'The evidence dossier could not be loaded.');
      return;
    }
    dossier = await dossierResponse.json();
    if (traceResponse.ok) trace = (await traceResponse.json()).trace_nodes || [];
  }

  async function finalise() {
    if (!selected || !grade.trim()) return;
    isFinalizing = true;
    error = '';
    notice = '';
    try {
      const response = await fetch(`/evidence/dossier/${selected.session_id}/finalise-grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved_grade: grade.trim(),
          teacher_id: teacherId.trim() || 'educator_workspace',
          teacher_override: grade.trim() !== selected.suggested_grade,
          feedback_comments: feedback.trim(),
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The final grade could not be recorded.'));
      notice = `Grade ${grade.trim()} has been finalized. The session is now sealed in the event record.`;
      selected = null;
      dossier = null;
      await loadQueue();
    } catch (err) {
      error = err.message || 'The final grade could not be recorded.';
    } finally {
      isFinalizing = false;
    }
  }

  onMount(async () => {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    try {
      await loadQueue();
    } catch (err) {
      error = err.message || 'The review queue could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

<main class="review-main">
  <header class="review-header">
    <div><div class="eyebrow">Educator workspace</div><h1>AutoSCORE review queue</h1><p>Review cited student evidence and exercise final grade authority. Fiosra prepares evidence; it does not make the final decision.</p></div>
    <div class="queue-count"><span>Awaiting review</span><strong>{queue.length}</strong></div>
  </header>

  {#if isLoading}
    <div class="loading"><div class="spinner"></div><span>Loading submitted reasoning traces…</span></div>
  {:else if error && queue.length === 0}
    <section class="load-error" role="alert">
      <strong>The review queue could not be determined.</strong>
      <p>{error}</p>
      <button class="btn btn-secondary" onclick={loadQueue}>Try again</button>
    </section>
  {:else}
    <div class="review-grid">
      <section class="queue-card">
        <div class="card-heading"><h2>Submitted sessions</h2><button class="refresh" onclick={loadQueue}>Refresh</button></div>
        {#if queue.length === 0}
          <div class="empty-queue"><strong>Nothing is waiting for review.</strong><p>When a student submits a reasoning trace, it will appear here with an evidence dossier.</p></div>
        {:else}
          <div class="queue-list">
            {#each queue as item (item.session_id)}
              <button class:active={selected?.session_id === item.session_id} class="queue-item" onclick={() => selectItem(item)}>
                <span class="student-mark">{item.student_id.slice(0, 2).toUpperCase()}</span>
                <span class="item-copy"><strong>{item.student_id}</strong><small>{item.assignment_title}</small><small>{formatDate(item.submitted_at)}</small></span>
                <span class="grade-pill">Review</span>
              </button>
            {/each}
          </div>
        {/if}
      </section>

      <section class="dossier-card">
        {#if !selected}
          <div class="empty-dossier"><strong>Select a submitted session</strong><p>The cited reasoning trace and suggested score will appear here.</p></div>
        {:else if !dossier}
          <div class="loading small"><div class="spinner"></div><span>Opening evidence dossier…</span></div>
        {:else}
          <header class="dossier-header"><div><div class="eyebrow">Evidence packet</div><h2>{selected.student_id}</h2><p>{selected.assignment_title}</p></div><div class="suggestion"><span>Final decision</span><strong>Teacher review</strong></div></header>
          <div class="summary-strip"><div><span>Autonomy</span><strong>{dossier.executive_summary?.autonomy_rating}</strong></div><div><span>Hint dependency</span><strong>{Math.round((dossier.aggregate_metrics?.hint_dependency_ratio || 0) * 100)}%</strong></div><div><span>Misconceptions</span><strong>{dossier.aggregate_metrics?.total_misconceptions_encountered || 0}</strong></div></div>
          {@const studentRevisions = trace.filter((event) => event.event_type === 'canvas_section_saved')}
          {@const supportActions = trace.filter((event) => event.event_type.startsWith('canvas_suggestion_'))}
          {@const proactiveEvidence = dossier.proactive_socratic_evidence || []}
          {#if studentRevisions.length || supportActions.length}
            <section class="canvas-provenance"><div class="canvas-provenance-heading"><div><h3>Canvas authorship record</h3><p>Student revisions and optional co-pilot actions are shown separately.</p></div><span>{studentRevisions.length} student revisions · {supportActions.length} support actions</span></div>
              <div class="provenance-columns">
                <div><h4>Student-authored revisions</h4>{#if studentRevisions.length}{#each studentRevisions as event (event.event_id)}<p class="provenance-item"><strong>{event.payload?.section_id?.replaceAll('_', ' ') || 'Canvas section'}</strong><span>{event.summary}</span></p>{/each}{:else}<p class="provenance-empty">No saved canvas revisions.</p>{/if}</div>
                <div><h4>Optional co-pilot support</h4>{#if supportActions.length}{#each supportActions as event (event.event_id)}<p class="provenance-item support"><strong>{event.event_type === 'canvas_suggestion_accepted' ? 'Applied after learner edit' : event.event_type === 'canvas_suggestion_dismissed' ? 'Dismissed by learner' : 'Offered for learner review'}</strong><span>{event.summary}</span></p>{/each}{:else}<p class="provenance-empty">No optional support cards used.</p>{/if}</div>
              </div>
            </section>
          {/if}
          {#if proactiveEvidence.length}
            <section class="probe-evidence"><div class="probe-evidence-heading"><div><h3>Proactive reasoning evidence</h3><p>Questions test a learner’s paragraph. Responses are evidence submitted for review—not an automated grade.</p></div><span>{proactiveEvidence.length} question{proactiveEvidence.length === 1 ? '' : 's'}</span></div>
              <div class="probe-evidence-list">{#each proactiveEvidence as probe (probe.probe_id)}<article class:responded={probe.evidence_state === 'evidence_submitted'} class="probe-evidence-card"><div class="probe-card-meta"><span>{probe.section_label}</span><strong>{probe.focus_type.replaceAll('_', ' ')}</strong><em>{probe.status}</em></div><p class="probe-question">{probe.question}</p>{#if probe.response_text}<div class="probe-response"><span>Learner response</span><p>{probe.response_text}</p></div>{:else}<p class="probe-no-response">No learner response was submitted for this question.</p>{/if}</article>{/each}</div>
            </section>
          {/if}
          <section class="evidence-section"><h3>Evidence by published rubric criterion</h3>{#each dossier.per_question_evidence || [] as question}{#each Object.entries(question.rubric_evidence || {}) as [, criterion]}<article class:met={criterion.met} class="criterion"><div><strong>{criterion.label || (criterion.met ? 'Evidence found' : 'Needs review')}</strong><span>{Math.round((criterion.confidence || 0) * 100)}% evidence confidence</span></div><p class="criterion-description">{criterion.description}</p><p>{criterion.evidence}</p><small>{criterion.explanation}</small></article>{/each}{/each}</section>
          <section class="grade-form"><h3>Educator finalization</h3><div class="form-grid"><label>Approved grade<input bind:value={grade} placeholder="A, B+, 88%" /></label><label>Educator identifier<input bind:value={teacherId} /></label></div><label>Formative feedback<textarea bind:value={feedback} rows="3" placeholder="Optional feedback for the student’s next reasoning cycle."></textarea></label><button class="btn btn-success" onclick={finalise} disabled={isFinalizing}>{isFinalizing ? 'Finalizing…' : 'Finalize grade and seal session'}</button></section>
        {/if}
      </section>
    </div>
  {/if}
  {#if notice}<div class="notice success">{notice}</div>{/if}{#if error && queue.length > 0}<div class="notice error">{error}</div>{/if}
</main>

<style>
  .review-main{max-width:1280px;margin:0 auto;padding:36px 28px 80px;display:flex;flex-direction:column;gap:24px}
  .review-header{border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;gap:20px;padding-bottom:22px}
  .eyebrow{color:var(--color-slate-muted);font-size:11px;font-weight:700;letter-spacing:.55px;text-transform:uppercase}
  .review-header h1{color:var(--color-heading);font-family:var(--font-brand);font-size:27px;margin:4px 0 7px}
  .review-header p{color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;max-width:740px}
  .queue-count{align-self:flex-end;background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.28);border-radius:var(--radius-md);display:flex;flex-direction:column;padding:10px 14px;text-align:right}
  .queue-count span{color:var(--color-slate-muted);font-size:10px;text-transform:uppercase}
  .queue-count strong{color:var(--color-horizon-bright);font-family:var(--font-brand);font-size:24px}
  .load-error{align-items:center;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.32);border-radius:var(--radius-lg);display:flex;flex-direction:column;gap:10px;min-height:250px;justify-content:center;text-align:center}
  .load-error strong{color:#fecaca}
  .load-error p{color:var(--color-slate-light);font-size:12px;margin:0;max-width:540px}
  .review-grid{display:grid;grid-template-columns:minmax(270px,.7fr) minmax(0,1.5fr);gap:22px;align-items:start}
  .queue-card,.dossier-card{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);padding:20px}
  .dossier-card{min-height:460px}
  .card-heading{align-items:center;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;padding-bottom:12px}
  .card-heading h2,.dossier-header h2{color:var(--color-heading);font-size:16px;margin:0}
  .refresh{background:none;border:0;color:var(--color-horizon-bright);cursor:pointer;font-size:11px;font-weight:700}
  .queue-list{display:flex;flex-direction:column;gap:8px;margin-top:12px}
  .queue-item{align-items:center;background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:inherit;cursor:pointer;display:flex;gap:10px;padding:10px;text-align:left;width:100%}
  .queue-item:hover,.queue-item.active{border-color:var(--color-horizon-bright);background:rgba(59,130,246,.11)}
  .student-mark{align-items:center;background:linear-gradient(135deg,var(--color-horizon-blue),var(--color-aurora));border-radius:50%;color:#fff;display:flex;flex:0 0 30px;font-size:10px;font-weight:700;height:30px;justify-content:center}
  .item-copy{display:flex;flex:1;flex-direction:column;gap:1px;min-width:0}
  .item-copy strong{color:var(--color-heading);font-size:12px}
  .item-copy small{color:var(--color-slate-muted);font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .grade-pill{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.25);border-radius:99px;color:#6ee7b7;font-size:11px;font-weight:700;padding:3px 7px}
  .empty-queue,.empty-dossier{color:var(--color-slate-muted);font-size:12px;line-height:1.6;padding:30px 10px;text-align:center}
  .empty-queue strong,.empty-dossier strong{color:var(--color-heading);display:block;font-size:13px}
  .empty-queue p,.empty-dossier p{margin:6px 0 0}
  .dossier-header{border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;gap:15px;padding-bottom:16px}
  .dossier-header p{color:var(--color-slate-muted);font-size:12px;margin:3px 0 0}
  .suggestion{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);border-radius:var(--radius-sm);display:flex;flex-direction:column;padding:8px 12px;text-align:right}
  .suggestion span{color:var(--color-slate-muted);font-size:9px;text-transform:uppercase}
  .suggestion strong{color:#6ee7b7;font-family:var(--font-brand);font-size:23px}
  .summary-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px}
  .summary-strip>div{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:flex;flex-direction:column;gap:3px;padding:9px}
  .summary-strip span{color:var(--color-slate-muted);font-size:9px;font-weight:700;text-transform:uppercase}
  .summary-strip strong{color:var(--color-heading);font-size:11px}
  .canvas-provenance,.evidence-section,.grade-form{border-top:1px solid var(--color-graphite-border);margin-top:18px;padding-top:15px}
  .canvas-provenance-heading{align-items:flex-start;display:flex;gap:12px;justify-content:space-between}
  .canvas-provenance h3,.evidence-section h3,.grade-form h3{color:var(--color-heading);font-size:13px;margin:0 0 5px}
  .canvas-provenance-heading p{color:var(--color-slate-muted);font-size:11px;margin:0}
  .canvas-provenance-heading>span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;white-space:nowrap}
  .provenance-columns{display:grid;gap:10px;grid-template-columns:1fr 1fr;margin-top:12px}
  .provenance-columns>div{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);padding:10px}
  .provenance-columns h4{color:var(--color-slate-light);font-size:10px;letter-spacing:.35px;margin:0 0 6px;text-transform:uppercase}
  .provenance-item{border-top:1px solid var(--color-graphite-border);display:flex;flex-direction:column;gap:3px;margin:0;padding:7px 0}
  .provenance-item strong{color:var(--color-aurora-bright);font-size:11px;text-transform:capitalize}
  .provenance-item.support strong{color:#8b5cf6}
  .provenance-item span,.provenance-empty{color:var(--color-slate-muted);font-size:10px;line-height:1.4;margin:0}
  .criterion{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-left:3px solid var(--color-amber);border-radius:var(--radius-sm);margin-top:8px;padding:10px}
  .criterion.met{border-left-color:var(--color-signal-green)}
  .criterion>div{display:flex;justify-content:space-between;gap:10px}
  .criterion strong{color:#fcd34d;font-size:11px;text-transform:uppercase}
  .criterion.met strong{color:#6ee7b7}
  .criterion span{color:var(--color-slate-muted);font-size:10px}
  .criterion p{color:var(--color-slate-light);font-size:11px;line-height:1.5;margin:6px 0}
  .criterion small{color:var(--color-slate-muted);font-size:10px}
  .grade-form{display:flex;flex-direction:column;gap:10px}
  .grade-form label{color:var(--color-slate-light);display:flex;flex-direction:column;font-size:10px;font-weight:700;gap:5px;letter-spacing:.35px;text-transform:uppercase}
  .form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .grade-form input,.grade-form textarea{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-bright);font:inherit;font-size:12px;padding:9px}
  .grade-form input:focus,.grade-form textarea:focus{border-color:var(--color-horizon-blue);outline:none}
  .notice{border-radius:var(--radius-sm);font-size:12px;padding:11px 14px}
  .notice.success{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);color:#86efac}
  .notice.error{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#fca5a5}
  .loading{align-items:center;color:var(--color-slate-light);display:flex;gap:12px;justify-content:center;min-height:280px}
  .loading.small{min-height:390px}
  .spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:26px;width:26px}
  @keyframes spin{to{transform:rotate(360deg)}}
  @media(max-width:850px){.review-grid{grid-template-columns:1fr}.review-header{flex-direction:column}.queue-count{align-self:flex-start}}
  @media(max-width:520px){.review-main{padding:26px 16px}.form-grid,.summary-strip,.provenance-columns{grid-template-columns:1fr}.dossier-header,.canvas-provenance-heading{align-items:flex-start;flex-direction:column}.suggestion{text-align:left}}

  .probe-evidence{border-top:1px solid var(--color-graphite-border);margin-top:18px;padding-top:15px}
  .probe-evidence-heading{align-items:flex-start;display:flex;gap:12px;justify-content:space-between}
  .probe-evidence h3{color:var(--color-heading);font-size:13px;margin:0 0 5px}
  .probe-evidence-heading p{color:var(--color-slate-muted);font-size:11px;margin:0}
  .probe-evidence-heading>span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;white-space:nowrap}
  .probe-evidence-list{display:flex;flex-direction:column;gap:8px;margin-top:12px}
  .probe-evidence-card{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-left:3px solid var(--color-amber);border-radius:var(--radius-sm);padding:11px}
  .probe-evidence-card.responded{border-left-color:var(--color-signal-green)}
  .probe-card-meta{align-items:center;display:flex;flex-wrap:wrap;gap:6px}
  .probe-card-meta span{color:var(--color-slate-muted);font-size:10px}
  .probe-card-meta strong{background:rgba(139,92,246,.14);border-radius:99px;color:#c4b5fd;font-size:9px;padding:3px 6px;text-transform:capitalize}
  .probe-card-meta em{color:var(--color-slate-muted);font-size:9px;font-style:normal;text-transform:capitalize}
  .probe-question{color:var(--color-slate-bright);font-size:12px;line-height:1.5;margin:8px 0}
  .probe-response{background:rgba(16,185,129,.07);border-left:2px solid var(--color-signal-green);padding:8px 10px}
  .probe-response span{color:#6ee7b7;font-size:9px;font-weight:700;letter-spacing:.3px;text-transform:uppercase}
  .probe-response p{color:var(--color-slate-light);font-size:11px;line-height:1.5;margin:4px 0 0}
  .probe-no-response{color:#fcd34d;font-size:10px;margin:0}
  @media(max-width:520px){.probe-evidence-heading{align-items:flex-start;flex-direction:column}}
</style>
