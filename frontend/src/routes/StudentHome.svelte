<script>
  import { onMount } from 'svelte';

  let courseProgress = 75;
</script>

<div class="home-page">
  <main class="home-container">
    
    <!-- Greeting -->
    <div class="greeting-header">
      <div class="greeting-title-group">
        <h1 class="greeting-title">Welcome back, Julian</h1>
        <p class="greeting-sub">HIST-201 • Module 1: The Outbreak of the Revolution (1789)</p>
      </div>

      <span class="badge badge-info" style="font-size: 11px; padding: 6px 12px;">
        Course Progress: {courseProgress}%
      </span>
    </div>

    <!-- 1. What should I work on now? -->
    <section class="focus-section">
      <span class="section-eyebrow">Active Focus • What to work on now</span>
      
      <div class="hero-focus-card">
        <div class="focus-card-top">
          <div class="focus-info">
            <span class="badge badge-warning" style="width: fit-content;">In Progress • Turn 4</span>
            <h2 class="focus-assignment-title">Assignment 4: Economic &amp; Social Causes of the French Revolution</h2>
            <p class="focus-desc">
              Synthesize primary source evidence from Arthur Young with historical analysis of Crown bankruptcy, Three Estates tax inequality (the <em>taille</em>), and Rousseau's Social Contract.
            </p>
          </div>
          <a href="#/student" class="btn btn-primary" style="padding: 12px 24px; font-size: 13.5px; white-space: nowrap;">
            Resume Reasoning Canvas →
          </a>
        </div>

        <div class="focus-status-row">
          <div class="focus-stat-item">
            <span class="focus-stat-label">Autonomy Score</span>
            <span class="focus-stat-value" style="color: var(--color-signal-green-dark);">82% (Qualified)</span>
          </div>

          <div class="divider"></div>

          <div class="focus-stat-item">
            <span class="focus-stat-label">Rubric Entailment</span>
            <span class="focus-stat-value">2 / 3 Criteria Met</span>
          </div>

          <div class="divider"></div>

          <div class="focus-stat-item">
            <span class="focus-stat-label">Socratic Hint Dependency</span>
            <span class="focus-stat-value">0.25 (1 hint used)</span>
          </div>

          <div class="divider"></div>

          <div class="focus-stat-item">
            <span class="focus-stat-label">Last Activity</span>
            <span class="focus-stat-value" style="color: var(--color-slate-muted);">Today at 10:19:42</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Where am I? Curriculum Knowledge Mastery -->
    <section class="progress-section">
      <span class="section-eyebrow">Curriculum Mastery • Where am I?</span>

      <div class="kc-progress-grid">
        <!-- Node 1 -->
        <div class="kc-progress-card">
          <div class="kc-card-top">
            <span class="badge badge-success">Mastered</span>
            <span class="kc-card-code">KC_01</span>
          </div>
          <h3 class="kc-card-name">Ancien Régime Absolutism</h3>
          <div class="kc-status-bar">
            <div class="kc-status-fill" style="width: 100%; background: var(--color-signal-green-dark);"></div>
          </div>
        </div>

        <!-- Node 2 -->
        <div class="kc-progress-card">
          <div class="kc-card-top">
            <span class="badge badge-success">Mastered</span>
            <span class="kc-card-code">KC_02</span>
          </div>
          <h3 class="kc-card-name">Three Estates &amp; Taille Exemption</h3>
          <div class="kc-status-bar">
            <div class="kc-status-fill" style="width: 100%; background: var(--color-signal-green-dark);"></div>
          </div>
        </div>

        <!-- Node 3 -->
        <div class="kc-progress-card">
          <div class="kc-card-top">
            <span class="badge badge-info">In Synthesis</span>
            <span class="kc-card-code">KC_03</span>
          </div>
          <h3 class="kc-card-name">Crown War Debt &amp; Fiscal Deficit</h3>
          <div class="kc-status-bar">
            <div class="kc-status-fill" style="width: 85%; background: var(--color-horizon-blue);"></div>
          </div>
        </div>

        <!-- Node 4 -->
        <div class="kc-progress-card" style="border-color: #fde68a; background: #fffbeb;">
          <div class="kc-card-top">
            <span class="badge badge-warning">Active Probe</span>
            <span class="kc-card-code">KC_04</span>
          </div>
          <h3 class="kc-card-name">Social Contract &amp; Popular Sovereignty</h3>
          <div class="kc-status-bar">
            <div class="kc-status-fill" style="width: 45%; background: var(--color-amber);"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. What's next? -->
    <section class="next-section">
      <span class="section-eyebrow">Upcoming Milestones • What's next?</span>

      <div class="upcoming-card">
        <div class="upcoming-info">
          <span class="badge badge-info" style="width: fit-content;">Module 2 • Next Assignment</span>
          <h3 class="upcoming-title">The Summoning of the Estates-General &amp; The Tennis Court Oath</h3>
          <p class="upcoming-meta">Unlocks automatically upon final sovereign approval of Assignment 4 by Dr. Vance.</p>
        </div>
        <span style="font-size: 13px; color: var(--color-slate-muted); font-weight: 500;">🔒 Locked</span>
      </div>
    </section>

  </main>
</div>

<style>
  .home-page {
    background-color: var(--color-bone);
    min-height: calc(100vh - 56px);
  }

  .home-container {
    max-width: 1060px;
    margin: 0 auto;
    padding: 40px 24px 80px 24px;
    display: flex;
    flex-direction: column;
    gap: 40px;
  }

  .greeting-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--color-bone-border);
    padding-bottom: 24px;
  }

  .greeting-title-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .greeting-title {
    font-family: var(--font-brand);
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .greeting-sub {
    font-size: 14px;
    color: var(--color-slate-muted);
    margin: 0;
  }

  .focus-section, .progress-section, .next-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .section-eyebrow {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-horizon-blue);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .hero-focus-card {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-left: 5px solid var(--color-horizon-blue);
    border-radius: var(--radius-md);
    padding: 28px 32px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    box-shadow: var(--shadow-md);
  }

  .focus-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
  }

  .focus-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .focus-assignment-title {
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .focus-desc {
    font-size: 13.5px;
    color: #475569;
    line-height: 1.5;
    max-width: 680px;
    margin: 0;
  }

  .focus-status-row {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 14px 18px;
    background: #f8fafc;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-bone-border);
  }

  .focus-stat-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .focus-stat-label {
    font-size: 10.5px;
    color: var(--color-slate-muted);
    text-transform: uppercase;
    font-weight: 600;
  }

  .focus-stat-value {
    font-size: 13.5px;
    font-weight: 600;
    color: #0f172a;
  }

  .divider {
    width: 1px;
    height: 28px;
    background: var(--color-bone-border);
  }

  .kc-progress-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
  }

  .kc-progress-card {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .kc-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .kc-card-code {
    font-size: 10.5px;
    font-family: monospace;
    color: var(--color-slate-muted);
  }

  .kc-card-name {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
  }

  .kc-status-bar {
    height: 6px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
  }

  .kc-status-fill {
    height: 100%;
    border-radius: 999px;
  }

  .upcoming-card {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .upcoming-info {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .upcoming-title {
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
  }

  .upcoming-meta {
    font-size: 12.5px;
    color: var(--color-slate-muted);
    margin: 0;
  }
</style>
