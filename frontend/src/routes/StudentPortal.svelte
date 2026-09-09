<script>
  let activeTab = $state('courses'); // 'courses' | 'reader' | 'portfolio'
  let activeReaderDoc = $state('young');

  function setTab(tab) {
    activeTab = tab;
  }
</script>

<div class="portal-page">
  <main class="portal-main">

    <!-- Greeting Banner -->
    <div class="greeting-banner">
      <div class="greeting-left">
        <h1 class="greeting-name">Welcome back, Elena</h1>
        <p class="greeting-sub">
          You are enrolled in 3 courses for Fall 2026. Next milestone due: <strong>Storming the Bastille: Sovereign Violence</strong> (HIST-201).
        </p>
      </div>

      <div class="portfolio-pill">
        <span>🛡️</span>
        <span>Autonomy Rating: <strong>88.4% (Level 4 Independent)</strong></span>
      </div>
    </div>

    <!-- Portal Navigation Tabs -->
    <div class="portal-nav">
      <button class="portal-tab-btn" class:active={activeTab === 'courses'} onclick={() => setTab('courses')}>
        <span>📚</span> Enrolled Courses &amp; Milestones
      </button>
      <button class="portal-tab-btn" class:active={activeTab === 'reader'} onclick={() => setTab('reader')}>
        <span>📖</span> Primary Source Grounding &amp; Syllabus
      </button>
      <button class="portal-tab-btn" class:active={activeTab === 'portfolio'} onclick={() => setTab('portfolio')}>
        <span>🎓</span> Verified Reasoning Portfolio &amp; Transcript
      </button>
    </div>

    <!-- VIEW 1: ENROLLED COURSES -->
    {#if activeTab === 'courses'}
      <div class="courses-grid">
        <!-- Course 1: HIST-201 -->
        <div class="student-course-card">
          <div class="card-top-row">
            <div>
              <span class="course-meta-code">HIST-201</span>
              <h2 class="course-title">The French Revolution &amp; Modern Statehood</h2>
            </div>
            <span class="badge badge-success">Unit 1 Active</span>
          </div>

          <div class="instructor-line">Instructor: Dr. Vance • 24 Students</div>

          <div class="active-task-box">
            <span class="active-task-label">Current Active Reasoning Task</span>
            <div class="active-task-title">Storming the Bastille: Violence as Sovereign Instrument</div>
            <div class="active-task-meta">⏱️ ~45m remaining • Sectional Scaffold: 2/3 Drafted</div>
          </div>

          <div class="card-footer">
            <a href="#/student/home" class="link-subtle">
              View Course Map →
            </a>
            <a href="#/student" class="btn btn-primary" style="padding: 7px 14px; font-size: 12px;">
              Resume Reasoning Canvas →
            </a>
          </div>
        </div>

        <!-- Course 2: PHIL-102 -->
        <div class="student-course-card">
          <div class="card-top-row">
            <div>
              <span class="course-meta-code">PHIL-102</span>
              <h2 class="course-title">Moral Reasoning &amp; Epistemology</h2>
            </div>
            <span class="badge" style="background: rgba(148,163,184,0.15); color: #475569;">Up to Date</span>
          </div>

          <div class="instructor-line">Instructor: Prof. Gallagher • 28 Students</div>

          <div class="active-task-box" style="border-left-color: var(--color-signal-green);">
            <span class="active-task-label" style="color: var(--color-signal-green-dark);">Last Evaluation Completed</span>
            <div class="active-task-title">Deontological Boundaries in Epistemic Injustice</div>
            <div class="active-task-meta">Approved Grade: 94% (Packet Z Verified)</div>
          </div>

          <div class="card-footer">
            <span style="font-size: 12px; color: #94a3b8;">Next unit unlocks Monday</span>
            <a href="#/student/trace" class="btn btn-secondary" style="padding: 7px 14px; font-size: 12px;">
              View Evidence Trace ↗
            </a>
          </div>
        </div>

        <!-- Course 3: LIT-304 -->
        <div class="student-course-card">
          <div class="card-top-row">
            <div>
              <span class="course-meta-code">LIT-304</span>
              <h2 class="course-title">Modernist Narratives &amp; Deconstruction</h2>
            </div>
            <span class="badge badge-info">Seminar</span>
          </div>

          <div class="instructor-line">Instructor: Dr. Al-Mansoor • 18 Students</div>

          <div class="active-task-box" style="border-left-color: var(--color-aurora);">
            <span class="active-task-label" style="color: var(--color-aurora);">Upcoming Sectional Inquiry</span>
            <div class="active-task-title">Temporal Dislocation in Virginia Woolf's To the Lighthouse</div>
            <div class="active-task-meta">Opens Sep 12 • 4 Primary Texts Grounded</div>
          </div>

          <div class="card-footer" style="justify-content: flex-end;">
            <button class="btn btn-secondary" style="padding: 7px 14px; font-size: 12px;" onclick={() => setTab('reader')}>
              Read Primary Texts 📖
            </button>
          </div>
        </div>
      </div>
    {/if}

    <!-- VIEW 2: PRIMARY SOURCE READER -->
    {#if activeTab === 'reader'}
      <div class="reader-grid">
        <div class="reader-sidebar">
          <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px;">
            HIST-201 Grounded Corpus
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            <button class="btn" class:btn-primary={activeReaderDoc === 'young'} class:btn-secondary={activeReaderDoc !== 'young'} style="justify-content: flex-start; text-align: left; font-size: 12px; padding: 8px 12px;" onclick={() => activeReaderDoc = 'young'}>
              📄 Arthur Young: Travels in France (1789)
            </button>
            <button class="btn" class:btn-primary={activeReaderDoc === 'sieyes'} class:btn-secondary={activeReaderDoc !== 'sieyes'} style="justify-content: flex-start; text-align: left; font-size: 12px; padding: 8px 12px;" onclick={() => activeReaderDoc = 'sieyes'}>
              📄 Abbé Sieyès: What is the Third Estate? (1789)
            </button>
            <button class="btn" class:btn-primary={activeReaderDoc === 'necker'} class:btn-secondary={activeReaderDoc !== 'necker'} style="justify-content: flex-start; text-align: left; font-size: 12px; padding: 8px 12px;" onclick={() => activeReaderDoc = 'necker'}>
              📄 Necker's Compte Rendu au Roi (1781)
            </button>
          </div>
        </div>

        <div class="reader-content">
          {#if activeReaderDoc === 'young'}
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
              <h2 class="reading-source-title">Arthur Young: Travels in France (July 1789 Excerpt)</h2>
              <span style="font-size: 11px; font-family: var(--font-mono); color: #64748b;">SHA-256: 4f98...e1b2</span>
            </div>

            <p style="font-size: 13.5px; color: #475569; line-height: 1.6;">
              Arthur Young, an English agricultural observer, recorded meticulous first-hand accounts of agrarian poverty and the institutional inequalities that sparked rural insurrections in the summer of 1789.
            </p>

            <div class="reading-passage">
              "The abuses attending the levy of the taille and the corvée are of a magnitude that foreigners can scarcely conceive. The nobility and clergy are exempt from the former; and the whole weight falls upon the peasantry, who are crushed beneath the load while privileged orders enjoy the fruits of fertile land without contributing a sol to the public treasury."
            </div>

            <div style="display: flex; gap: 12px; margin-top: 12px;">
              <a href="#/student" class="btn btn-primary" style="font-size: 12px;">
                📎 Clip Excerpt to Reasoning Canvas
              </a>
            </div>
          {:else if activeReaderDoc === 'sieyes'}
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
              <h2 class="reading-source-title">Abbé Sieyès: What is the Third Estate? (January 1789)</h2>
              <span style="font-size: 11px; font-family: var(--font-mono); color: #64748b;">SHA-256: 9ac3...77d1</span>
            </div>
            <p style="font-size: 13.5px; color: #475569; line-height: 1.6;">
              Emmanuel-Joseph Sieyès issued the definitive political manifesto defining national sovereignty against feudal privilege.
            </p>
            <div class="reading-passage">
              "What is the Third Estate? Everything. What has it been heretofore in the political order? Nothing. What does it demand? To become something."
            </div>
            <div style="display: flex; gap: 12px; margin-top: 12px;">
              <a href="#/student" class="btn btn-primary" style="font-size: 12px;">
                📎 Clip Excerpt to Reasoning Canvas
              </a>
            </div>
          {:else}
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
              <h2 class="reading-source-title">Jacques Necker: Compte Rendu au Roi (1781)</h2>
              <span style="font-size: 11px; font-family: var(--font-mono); color: #64748b;">SHA-256: db81...00f4</span>
            </div>
            <p style="font-size: 13.5px; color: #475569; line-height: 1.6;">
              Necker made public the state budget for the first time in French royal history, concealing extraordinary military war debts.
            </p>
            <div class="reading-passage">
              "A state whose credit is sound can find resources in extraordinary crises; but when mystery shrouds finances, distrust multiplies and rates become ruinous."
            </div>
            <div style="display: flex; gap: 12px; margin-top: 12px;">
              <a href="#/student" class="btn btn-primary" style="font-size: 12px;">
                📎 Clip Excerpt to Reasoning Canvas
              </a>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- VIEW 3: VERIFIED REASONING PORTFOLIO -->
    {#if activeTab === 'portfolio'}
      <div class="portfolio-view">
        <div class="portfolio-ribbon">
          <div class="portfolio-stat">
            <span class="portfolio-stat-label">Autonomy Index</span>
            <span class="portfolio-stat-val" style="color: var(--color-horizon-blue);">88.4%</span>
            <span class="portfolio-stat-sub">Top Decile Independent</span>
          </div>

          <div class="portfolio-stat">
            <span class="portfolio-stat-label">Verifiable Claims Entailed</span>
            <span class="portfolio-stat-val" style="color: var(--color-signal-green-dark);">18 / 20</span>
            <span class="portfolio-stat-sub">90% Entailment (DeBERTa-v3)</span>
          </div>

          <div class="portfolio-stat">
            <span class="portfolio-stat-label">Autonomous Self-Corrections</span>
            <span class="portfolio-stat-val" style="color: #7c3aed;">4 Nodes</span>
            <span class="portfolio-stat-sub">Zero Teacher Interventions</span>
          </div>

          <div class="portfolio-stat">
            <span class="portfolio-stat-label">Avg Hint Ceiling</span>
            <span class="portfolio-stat-val">0.18</span>
            <span class="portfolio-stat-sub">Minimal Scaffolding Used</span>
          </div>
        </div>

        <div class="endorsement-card">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 12px;">
              <div class="avatar" style="background: #1e293b; color: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700;">DV</div>
              <div>
                <div style="font-weight: 700; color: #0f172a;">Dr. Vance • Department of History</div>
                <div style="font-size: 11.5px; color: #64748b;">Formal Reasoning Trace Endorsement (HIST-201)</div>
              </div>
            </div>
            <span class="badge badge-success">Cryptographically Signed</span>
          </div>

          <p class="endorsement-quote">
            "Elena demonstrated exceptional conceptual maturity during the Fiscal Insolvency reasoning canvas. When initially tempted by the moralized 'luxury spending' trope, she autonomously revised her claim upon inspecting Necker's Compte Rendu data, framing the crisis around systemic debt servicing and fiscal exemption. Her reasoning trace reflects authentic scholarly discipline."
          </p>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--color-bone-border); padding-top: 14px;">
            <span style="font-size: 11px; font-family: monospace; color: #64748b;">
              Evidence Packet: Z-HIST201-STU081-REV24 • Verified via AAAI-2026 AutoSCORE Protocol
            </span>
            <button class="btn btn-secondary" style="font-size: 11.5px; padding: 6px 12px;" onclick={() => alert('Downloading W3C Verifiable Credential (JSON-LD)...')}>
              📄 Export Verifiable Proof of Reasoning (.json-ld)
            </button>
          </div>
        </div>
      </div>
    {/if}

  </main>
</div>

<style>
  .portal-page {
    background-color: var(--color-bone);
    min-height: calc(100vh - 56px);
  }

  .portal-main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 36px 24px 80px 24px;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  .greeting-banner {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-lg);
    padding: 28px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: var(--shadow-sm);
  }

  .greeting-left {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .greeting-name {
    font-family: var(--font-brand);
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .greeting-sub {
    font-size: 13.5px;
    color: #64748b;
    margin: 0;
  }

  .portfolio-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: var(--radius-full);
    font-size: 13px;
    font-weight: 600;
    color: #065f46;
  }

  .portal-nav {
    display: flex;
    gap: 12px;
    border-bottom: 2px solid var(--color-bone-border);
    padding-bottom: 2px;
  }

  .portal-tab-btn {
    background: none;
    border: none;
    font-family: var(--font-ui);
    font-size: 14.5px;
    font-weight: 600;
    color: #64748b;
    padding: 10px 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    transition: all 0.15s ease;
    position: relative;
  }

  .portal-tab-btn:hover {
    color: #0f172a;
    background: rgba(0, 0, 0, 0.02);
  }

  .portal-tab-btn.active {
    color: var(--color-horizon-blue);
  }

  .portal-tab-btn.active::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--color-horizon-blue);
  }

  .courses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 24px;
  }

  .student-course-card {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .student-course-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: #cbd5e1;
  }

  .card-top-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .course-meta-code {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-horizon-blue);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .course-title {
    font-family: var(--font-brand);
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.3;
    margin: 0;
  }

  .instructor-line {
    font-size: 12.5px;
    color: #64748b;
  }

  .active-task-box {
    background: #f8fafc;
    border: 1px solid var(--color-bone-border);
    border-left: 4px solid var(--color-horizon-blue);
    border-radius: var(--radius-xs);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .active-task-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-horizon-blue);
    letter-spacing: 0.5px;
  }

  .active-task-title {
    font-size: 13.5px;
    font-weight: 600;
    color: #0f172a;
  }

  .active-task-meta {
    font-size: 11.5px;
    color: #64748b;
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
    padding-top: 12px;
  }

  .link-subtle {
    font-size: 12.5px;
    font-weight: 600;
    color: #64748b;
    text-decoration: none;
  }
  .link-subtle:hover {
    color: #0f172a;
  }

  .reader-grid {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 24px;
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    min-height: 540px;
  }

  .reader-sidebar {
    background: #f8fafc;
    border-right: 1px solid var(--color-bone-border);
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .reader-content {
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
  }

  .reading-source-title {
    font-family: var(--font-brand);
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .reading-passage {
    font-family: Georgia, serif;
    font-size: 16px;
    line-height: 1.7;
    color: #334155;
    background: #ffffff;
    border-left: 3px solid var(--color-horizon-blue);
    padding: 16px 20px;
    margin: 8px 0;
  }

  .portfolio-ribbon {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }

  .portfolio-stat {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    box-shadow: var(--shadow-sm);
  }

  .portfolio-stat-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
  }

  .portfolio-stat-val {
    font-family: var(--font-brand);
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
  }

  .portfolio-stat-sub {
    font-size: 12px;
    color: var(--color-signal-green-dark);
    font-weight: 600;
  }

  .endorsement-card {
    background: #ffffff;
    border: 1px solid var(--color-bone-border);
    border-radius: var(--radius-md);
    padding: 24px 28px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    box-shadow: var(--shadow-sm);
  }

  .endorsement-quote {
    font-style: italic;
    font-size: 14px;
    color: #334155;
    line-height: 1.6;
    border-left: 3px solid var(--color-signal-green);
    padding-left: 14px;
    margin: 4px 0;
  }
</style>
