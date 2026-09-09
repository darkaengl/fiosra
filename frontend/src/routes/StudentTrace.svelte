<script>
  let activeNode = $state(4);
  let isSubmitted = $state(false);

  function handleSubmit() {
    isSubmitted = true;
  }
</script>

<div class="trace-page">
  <main class="trace-container">
    
    <div class="trace-header">
      <div class="trace-title-group">
        <h1 class="trace-title">The Emergent Path: Cognitive Trajectory</h1>
        <p class="trace-subtitle">
          Review your evolution across turns before submitting your final synthesis to Dr. Vance.
        </p>
      </div>

      <div style="display: flex; gap: 12px; align-items: center;">
        <div style="text-align: right;">
          <div style="font-size: 11px; color: var(--color-slate-muted); text-transform: uppercase;">Earned Autonomy</div>
          <div style="font-size: 20px; font-weight: 700; color: var(--color-signal-green); font-family: var(--font-brand);">82% (Qualified)</div>
        </div>
      </div>
    </div>

    <!-- The Emergent Path Visualization -->
    <div class="emergent-path-card">
      <div class="path-label-row">
        <span class="path-heading">Trajectory Nodes (Exploration ➔ Self-Correction ➔ Synthesis)</span>
        <span class="badge badge-info">Turn {activeNode} Active</span>
      </div>

      <div class="nodes-track">
        <!-- Node 1 -->
        <button type="button" class="path-step-node completed" onclick={() => activeNode = 1}>
          <div class="node-circle">1</div>
          <div class="node-meta">
            <span class="node-phase">Initial Hypothesis</span>
            <span class="node-sub">10:14:02 • Moral Claim</span>
          </div>
        </button>

        <!-- Node 2 -->
        <button type="button" class="path-step-node completed" onclick={() => activeNode = 2}>
          <div class="node-circle">2</div>
          <div class="node-meta">
            <span class="node-phase">Socratic Probe</span>
            <span class="node-sub">10:14:08 • Fiscal Nudge</span>
          </div>
        </button>

        <!-- Node 3 -->
        <button type="button" class="path-step-node completed" onclick={() => activeNode = 3}>
          <div class="node-circle">3</div>
          <div class="node-meta">
            <span class="node-phase">Source Alignment</span>
            <span class="node-sub">10:17:15 • Arthur Young</span>
          </div>
        </button>

        <!-- Node 4 -->
        <button type="button" class="path-step-node current" onclick={() => activeNode = 4}>
          <div class="node-circle">4</div>
          <div class="node-meta">
            <span class="node-phase">Autonomous Revision</span>
            <span class="node-sub">10:19:42 • 82% Autonomy</span>
          </div>
        </button>

        <!-- Node 5 -->
        <button type="button" class="path-step-node future" onclick={() => activeNode = 5}>
          <div class="node-circle">5</div>
          <div class="node-meta">
            <span class="node-phase">Final Submission</span>
            <span class="node-sub">Packet Z Verification</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Detailed Turn Diff Comparison -->
    <div class="trace-detail-grid">
      <!-- Attempt 1 -->
      <div class="diff-card">
        <div class="diff-header">
          <span class="diff-title">Attempt 1 (Turn 1 • 10:14:02)</span>
          <span class="badge badge-warning">Informal Grievance</span>
        </div>
        <div class="diff-content">
          <span class="highlight-removed">The French Revolution started because the King was evil and treated poor people badly without reason.</span> Everyone was starving and furious at the monarchy.
        </div>
        <div style="font-size: 11.5px; color: var(--color-slate-muted);">
          Integrity Agent triggered <code>MISC_MORAL_VERSUS_INST</code>. NLI verification rejected entailment (0.12). Socratic Rung 1 deployed.
        </div>
      </div>

      <!-- Current Turn 4 -->
      <div class="diff-card" style="border-color: var(--color-signal-green-dark);">
        <div class="diff-header">
          <span class="diff-title">Attempt 2 (Turn 4 • 10:19:42)</span>
          <span class="badge badge-success">Self-Corrected Synthesis</span>
        </div>
        <div class="diff-content">
          <span class="highlight-added">The French Revolution erupted because the Crown was bankrupt after funding the American War of Independence and Seven Years' War.</span><br><br>
          <span class="highlight-added">Under the Ancien Régime, the 1st and 2nd Estates paid no direct taxes, leaving the Third Estate (97% of people) to shoulder the entire taille burden.</span><br><br>
          Philosophers like Rousseau inspired people to want freedom from kings.
        </div>
        <div style="font-size: 11.5px; color: var(--color-signal-green);">
          Criteria A &amp; B verified by NLI entailment (94% &amp; 91% confidence). Packet Z generated with 82% autonomy.
        </div>
      </div>
    </div>

    <!-- Final Submission Bar -->
    <div class="submission-bar">
      <div class="submission-info">
        <h3 class="submission-heading">
          {isSubmitted ? '✓ Assignment Submitted Successfully' : 'Ready for Sovereign Educator Review?'}
        </h3>
        <p class="submission-note">
          {isSubmitted 
            ? 'Packet Z has been sent to Dr. Vance. Verification ID: #PKT-Z-98821' 
            : 'Your reasoning trajectory, 82% autonomy score, and verbatim citations will be packaged into AutoSCORE Light Dossier Packet Z.'}
        </p>
      </div>
      <div style="display: flex; gap: 12px;">
        <a href="#/student" class="btn btn-secondary">
          Continue Editing
        </a>
        {#if !isSubmitted}
          <button class="btn btn-success" style="padding: 10px 24px; font-size: 13.5px;" onclick={handleSubmit}>
            ✓ Confirm &amp; Submit Assignment
          </button>
        {:else}
          <a href="#/review" class="btn btn-primary" style="padding: 10px 24px; font-size: 13.5px;">
            Open Educator Review →
          </a>
        {/if}
      </div>
    </div>

  </main>
</div>

<style>
  .trace-page {
    background-color: var(--color-obsidian);
    min-height: calc(100vh - 56px);
    color: var(--color-slate-bright);
  }

  .trace-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 24px 80px 24px;
    display: flex;
    flex-direction: column;
    gap: 36px;
  }

  .trace-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 24px;
  }

  .trace-title-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .trace-title {
    font-family: var(--font-brand);
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
  }

  .trace-subtitle {
    font-size: 14px;
    color: var(--color-slate-light);
    margin: 0;
  }

  .emergent-path-card {
    background-color: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 32px;
    display: flex;
    flex-direction: column;
    gap: 28px;
    box-shadow: var(--shadow-md);
  }

  .path-label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .path-heading {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .nodes-track {
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    margin: 16px 20px;
  }

  .nodes-track::before {
    content: '';
    position: absolute;
    left: 30px;
    right: 30px;
    top: 22px;
    height: 3px;
    background: var(--color-graphite-border);
    z-index: 1;
  }

  .path-step-node {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
  }

  .node-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background-color: var(--color-graphite-card);
    border: 2px solid var(--color-graphite-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    color: var(--color-slate-light);
    transition: all 0.2s ease;
  }

  .path-step-node.completed .node-circle {
    background: rgba(16, 185, 129, 0.15);
    border-color: var(--color-signal-green);
    color: var(--color-signal-green);
  }

  .path-step-node.current .node-circle {
    background: var(--color-horizon-blue);
    border-color: #60a5fa;
    color: #ffffff;
    box-shadow: 0 0 16px var(--color-horizon-blue);
    transform: scale(1.1);
  }

  .path-step-node.future .node-circle {
    border-style: dashed;
  }

  .node-meta {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    text-align: center;
  }

  .node-phase {
    font-size: 12px;
    font-weight: 600;
    color: #ffffff;
  }

  .node-sub {
    font-size: 10.5px;
    color: var(--color-slate-muted);
  }

  .trace-detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

  .diff-card {
    background-color: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .diff-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 12px;
  }

  .diff-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
  }

  .diff-content {
    font-size: 13.5px;
    line-height: 1.7;
    color: var(--color-slate-bright);
    background-color: var(--color-obsidian);
    padding: 16px 18px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-graphite-border);
    font-family: var(--font-ui);
  }

  .highlight-removed {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    padding: 2px 4px;
    border-radius: 2px;
    text-decoration: line-through;
  }

  .highlight-added {
    background: rgba(16, 185, 129, 0.2);
    color: #86efac;
    padding: 2px 4px;
    border-radius: 2px;
    font-weight: 500;
  }

  .submission-bar {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: var(--radius-md);
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .submission-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .submission-heading {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
  }

  .submission-note {
    font-size: 12.5px;
    color: var(--color-slate-light);
    margin: 0;
  }
</style>
