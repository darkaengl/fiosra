<script>
  import InstitutionalFooter from '../lib/InstitutionalFooter.svelte';

  const FIOSRA_LOCKUP_URL = "./fiosra-lockup.png";
  const FIOSRA_SYMBOL_URL = "./fiosra-symbol.png";

  const loop = [
    { number: "01", title: "Context", text: "Course, assignment, materials, rubric and policy create a credible place to begin." },
    { number: "02", title: "Learning", text: "Students write, inspect and explore within the work rather than leaving it for a generic chat." },
    { number: "03", title: "Development", text: "Fiosra recognises meaningful changes in reasoning without claiming to observe everything." },
    { number: "04", title: "Evidence", text: "Qualifying work is captured with provenance so it can be interpreted in academic context." },
    { number: "05", title: "Understanding", text: "Students review their Development Trace. Educators see evidence with context, not an activity dashboard." },
  ];
</script>

<div class="landing-page">
  <!-- Public Sticky Navigation Header -->
  <header class="landing-header">
    <div class="landing-header-inner">
      <a href="#/" class="brand-link" aria-label="Fiosra home">
        <img src={FIOSRA_LOCKUP_URL} alt="Fiosra · Learning in Motion" class="brand-logo" />
      </a>

      <nav class="landing-nav" aria-label="Homepage navigation">
        <a href="#how-it-works" class="nav-link">How it works</a>
        <a href="#for-learning" class="nav-link">For learning</a>
        <a href="#for-educators" class="nav-link">For educators</a>
      </nav>

      <a href="#/student/home" class="btn-header-cta">
        <span class="btn-text-full">Explore the experience</span>
        <span class="btn-text-short">Explore</span>
        <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
        </svg>
      </a>
    </div>
  </header>

  <main>
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-background-rings" aria-hidden="true"></div>
      
      <div class="hero-container">
        <!-- Hero Left Pitch -->
        <div class="hero-copy">
          <h1 class="hero-title">
            Make the thinking between first draft and final work visible.
          </h1>
          <p class="hero-subtitle">
            Fiosra is a structured learning environment for context-rich work, considered exploration, meaningful development and clearer understanding.
          </p>
          <div class="hero-actions">
            <a href="#/student/home" class="btn-hero-primary">
              Explore a student journey
              <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
              </svg>
            </a>
            <a href="#how-it-works" class="btn-hero-secondary">
              See how Fiosra works
              <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>
              </svg>
            </a>
          </div>
          <p class="hero-footnote">
            Designed around real assignment work. AI support is present only when it helps the student think.
          </p>
        </div>

        <!-- Hero Right Preview Window -->
        <div class="workspace-preview-card" aria-label="Illustration of the Fiosra Learning Workspace and Thinking Companion">
          <div class="preview-chrome">
            <span class="preview-dots" aria-hidden="true">
              <i></i><i></i><i></i>
            </span>
            <span class="preview-course-title">Strategic Decision-Making in Organisations</span>
            <span class="preview-badge">Fiosra Learning Workspace</span>
          </div>

          <div class="preview-body">
            <div class="preview-doc-area">
              <div class="preview-doc-inner">
                <span class="preview-eyebrow">Active intellectual area</span>
                <h3 class="preview-area-title">Strategic alternatives</h3>
                <div class="preview-skeleton-lines" aria-hidden="true">
                  <span class="skeleton-line line-100"></span>
                  <span class="skeleton-line line-77"></span>
                  <span class="skeleton-line line-64"></span>
                </div>
                <blockquote class="preview-quote">
                  “The UK route reduces customer concentration, but it may also expose Atlantic Edge Foods to greater operational complexity.”
                </blockquote>
                <div class="preview-action-pill">
                  <img src={FIOSRA_SYMBOL_URL} alt="" class="symbol-pill-img" />
                  <span>Think from this passage</span>
                  <svg class="icon-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                  </svg>
                </div>
              </div>
            </div>

            <!-- Thinking Companion Floating Panel -->
            <aside class="preview-companion-aside">
              <div class="companion-callout-header">
                <img src={FIOSRA_SYMBOL_URL} alt="" class="companion-aside-symbol" />
                <div>
                  <div class="companion-name">Thinking Companion</div>
                  <div class="companion-status">Grounded in your writing</div>
                </div>
              </div>
              <blockquote class="companion-quote">
                “...expose Atlantic Edge Foods to greater operational complexity.”
              </blockquote>
              <span class="companion-step-tag">Examining the assumption</span>
              <p class="companion-inquiry">
                The claim assumes the business has the operational capacity to support UK distribution. Which details in the case would test that before you rely on this route?
              </p>
              <div class="companion-card-box">
                <span class="card-box-label">Assumption to test</span>
                <p class="card-box-text">Whether distribution capability can scale without destabilising margin or service levels.</p>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </section>

    <!-- The Product Thesis -->
    <section class="thesis-section">
      <div class="thesis-container">
        <div class="thesis-header">
          <p class="section-kicker">The product thesis</p>
          <h2 class="thesis-title">Learning is more than the final answer.</h2>
        </div>
        <div class="thesis-body">
          <p>
            Final work matters, but it cannot show everything a student learned on the way there. Fiosra brings the assignment context, the student’s developing work and purposeful exploration together in one environment.
          </p>
          <p>
            <strong>It does not turn every action into data.</strong> It distinguishes meaningful development from raw activity, so evidence supports human understanding rather than surveillance.
          </p>
        </div>
      </div>
    </section>

    <!-- The Fiosra Loop (How It Works) -->
    <section id="how-it-works" class="loop-section">
      <div class="loop-container">
        <div class="loop-header-row">
          <div>
            <p class="section-kicker">The Fiosra loop</p>
            <h2 class="loop-title">A continuous route from context to understanding.</h2>
          </div>
          <p class="loop-subtitle">
            The loop is designed to be lived within assignment work, not administered around it.
          </p>
        </div>

        <div class="loop-steps-grid">
          {#each loop as item, index}
            <article class="loop-step-card">
              <span class="step-num">{item.number}</span>
              <h3 class="step-title">{item.title}</h3>
              <p class="step-desc">{item.text}</p>
              {#if index < loop.length - 1}
                <span aria-hidden="true" class="step-connector">→</span>
              {/if}
            </article>
          {/each}
        </div>
      </div>
    </section>

    <!-- Two Connected Experiences -->
    <section class="experiences-section">
      <div class="experiences-container">
        <p class="section-kicker">Two connected experiences</p>
        <h2 class="experiences-title">Designed around the work, for the people doing it.</h2>

        <div class="experiences-grid">
          <!-- Student Card -->
          <article id="for-learning" class="experience-card">
            <span aria-hidden="true" class="card-bg-ring"></span>
            <div class="card-content">
              <div class="card-icon-badge">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>
                  <path d="M9 18h6"/>
                  <path d="M10 22h4"/>
                </svg>
              </div>
              <p class="card-audience">For students</p>
              <h3 class="card-heading">A calmer place to develop judgement.</h3>
              <p class="card-description">
                Work from the actual assignment context. Explore uncertainty in your own words. Return to writing without losing the thread of your thinking.
              </p>
              <a href="#/student/home" class="card-action-link">
                Explore student learning
                <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                </svg>
              </a>
            </div>
          </article>

          <!-- Educator Card -->
          <article id="for-educators" class="experience-card">
            <span aria-hidden="true" class="card-bg-ring"></span>
            <div class="card-content">
              <div class="card-icon-badge">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>
                  <path d="M22 10v6"/>
                  <path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>
                </svg>
              </div>
              <p class="card-audience">For educators</p>
              <h3 class="card-heading">See the development behind the final work.</h3>
              <p class="card-description">
                Review meaningful evidence, the Development Trace and final submissions together. Signals provide an invitation to consider, not a judgement about a learner.
              </p>
              <a href="#/courses" class="card-action-link">
                Explore educator visibility
                <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                </svg>
              </a>
            </div>
          </article>
        </div>
      </div>
    </section>

    <!-- Deep Obsidian CTA Banner -->
    <section class="cta-banner-section">
      <span aria-hidden="true" class="banner-bg-ring"></span>
      <div class="cta-banner-container">
        <div class="cta-banner-copy">
          <p class="banner-kicker">Fiosra · Learning in Motion</p>
          <h2 class="banner-title">The work moves forward. So should the learning around it.</h2>
          <p class="banner-subtitle">
            Enter the learning environment to see how students, course context, evidence and educator understanding connect in the Fiosra MVP.
          </p>
        </div>
        <div class="cta-banner-actions">
          <a href="#/student/home" class="btn-banner-light">
            Enter student experience
            <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
          </a>
          <a href="#/courses" class="btn-banner-ghost">
            View educator experience
            <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
            </svg>
          </a>
        </div>
      </div>
    </section>
  </main>

  <!-- Public Institutional Footer -->
  <InstitutionalFooter variant="public" />
</div>

<style>
  /* Base typography & palette */
  .landing-page {
    min-height: 100vh;
    background-color: var(--m-color-bone, #F6F5F1);
    color: var(--m-color-obsidian, #111315);
    font-family: var(--font-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    overflow-x: hidden;
  }

  /* Public Sticky Header */
  .landing-header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(246, 245, 241, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(221, 220, 213, 0.9);
  }

  .landing-header-inner {
    max-width: 1140px;
    height: 76px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .brand-link {
    display: inline-flex;
    align-items: center;
    text-decoration: none;
  }

  .brand-logo {
    height: 48px;
    width: auto;
    object-fit: contain;
  }

  .landing-nav {
    display: flex;
    align-items: center;
    gap: 28px;
  }

  .nav-link {
    font-size: 13px;
    font-weight: 500;
    color: var(--m-color-slate, #6D7378);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .nav-link:hover {
    color: var(--m-color-obsidian, #111315);
  }

  .btn-header-cta {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--m-color-obsidian, #111315);
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 18px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease, transform 0.1s ease;
  }

  .btn-header-cta:hover {
    background: #000000;
  }

  .btn-header-cta:active {
    transform: scale(0.98);
  }

  .btn-text-short {
    display: none;
  }

  /* Hero Section */
  .hero-section {
    position: relative;
    border-bottom: 1px solid var(--border, #DDDCD5);
    padding: 64px 0 80px;
    overflow: hidden;
  }

  .hero-background-rings {
    pointer-events: none;
    position: absolute;
    right: -16rem;
    top: -10rem;
    width: 42rem;
    height: 42rem;
    border-radius: 50%;
    border: 1px solid rgba(79, 107, 255, 0.14);
    box-shadow: 0 0 0 76px rgba(79, 107, 255, 0.025), 0 0 0 152px rgba(79, 107, 255, 0.015);
  }

  .hero-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
    display: grid;
    grid-template-columns: 1fr 1.12fr;
    gap: 56px;
    align-items: center;
  }

  .hero-copy {
    max-width: 520px;
  }

  .hero-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 54px;
    line-height: 1.02;
    letter-spacing: -0.04em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 0;
  }

  .hero-subtitle {
    margin: 24px 0 0;
    font-size: 16px;
    line-height: 1.6;
    color: var(--m-color-graphite, #23272B);
  }

  .hero-actions {
    margin-top: 32px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .btn-hero-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--m-color-obsidian, #111315);
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    padding: 12px 20px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease, transform 0.1s ease;
  }

  .btn-hero-primary:hover {
    background: #000000;
  }

  .btn-hero-secondary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: transparent;
    border: 1px solid var(--border, #DDDCD5);
    color: var(--m-color-obsidian, #111315);
    font-size: 13px;
    font-weight: 600;
    padding: 12px 20px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .btn-hero-secondary:hover {
    background: #ffffff;
    border-color: #C9D7FF;
  }

  .hero-footnote {
    margin: 20px 0 0;
    font-size: 12px;
    line-height: 1.5;
    color: var(--m-color-slate, #6D7378);
  }

  /* Workspace Preview Card */
  .workspace-preview-card {
    position: relative;
    border-radius: 16px;
    border: 1px solid #D7D9DF;
    background: #FCFCFD;
    box-shadow: 0 28px 64px rgba(16, 22, 47, 0.12);
    overflow: hidden;
  }

  .preview-chrome {
    height: 42px;
    border-bottom: 1px solid #E7E7EA;
    background: #ffffff;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    color: var(--m-color-slate, #6D7378);
  }

  .preview-dots {
    display: flex;
    gap: 6px;
  }

  .preview-dots i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #D5D6DA;
  }

  .preview-course-title {
    font-weight: 500;
    color: var(--m-color-graphite, #23272B);
  }

  .preview-badge {
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .preview-body {
    position: relative;
    display: flex;
  }

  .preview-doc-area {
    flex: 1;
    padding-right: 38%;
  }

  .preview-doc-inner {
    padding: 24px;
  }

  .preview-eyebrow {
    display: block;
    font-family: var(--font-mono, monospace);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .preview-area-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
    margin: 8px 0 12px;
  }

  .preview-skeleton-lines {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 18px;
  }

  .skeleton-line {
    display: block;
    height: 8px;
    border-radius: 4px;
    background: #E9E9E7;
  }

  .line-100 { width: 100%; }
  .line-77 { width: 77%; }
  .line-64 { width: 64%; }

  .preview-quote {
    margin: 0 0 16px;
    border-left: 3px solid var(--m-color-horizon-blue, #4F6BFF);
    background: linear-gradient(to right, #EBF0FF, transparent);
    padding: 10px 12px;
    font-family: var(--font-serif, "Newsreader", Georgia, serif);
    font-size: 13px;
    font-style: italic;
    line-height: 1.5;
    color: var(--m-color-graphite, #23272B);
  }

  .preview-action-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--m-color-obsidian, #111315);
    color: #ffffff;
    font-size: 11px;
    font-weight: 500;
    padding: 8px 14px;
    border-radius: 6px;
  }

  .symbol-pill-img {
    height: 14px;
    width: auto;
    filter: brightness(0) invert(1);
  }

  /* Aside / Companion Panel */
  .preview-companion-aside {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 38%;
    background: #FAFBFF;
    border-left: 3px solid var(--m-color-horizon-blue, #4F6BFF);
    padding: 18px;
    box-sizing: border-box;
  }

  .companion-callout-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .companion-aside-symbol {
    height: 24px;
    width: auto;
  }

  .companion-name {
    font-size: 11px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
  }

  .companion-status {
    font-family: var(--font-mono, monospace);
    font-size: 8px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .companion-quote {
    margin: 12px 0 10px;
    border-left: 2px solid var(--m-color-horizon-blue, #4F6BFF);
    background: linear-gradient(to right, #EEF3FF, transparent);
    padding: 6px 8px;
    font-family: var(--font-serif, "Newsreader", Georgia, serif);
    font-size: 10px;
    font-style: italic;
    line-height: 1.4;
    color: var(--m-color-graphite, #23272B);
  }

  .companion-step-tag {
    display: block;
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--m-color-horizon-blue, #4F6BFF);
  }

  .companion-inquiry {
    margin: 4px 0 10px;
    font-size: 10px;
    line-height: 1.45;
    color: var(--m-color-graphite, #23272B);
  }

  .companion-card-box {
    border-radius: 6px;
    border: 1px solid #C9D7FF;
    background: #ffffff;
    padding: 8px 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }

  .card-box-label {
    display: block;
    font-family: var(--font-mono, monospace);
    font-size: 8px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .card-box-text {
    margin: 4px 0 0;
    font-size: 10px;
    line-height: 1.4;
    color: var(--m-color-graphite, #23272B);
  }

  /* Section Kicker */
  .section-kicker {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    margin: 0;
  }

  /* Thesis Section */
  .thesis-section {
    padding: 80px 0 96px;
  }

  .thesis-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 48px;
  }

  .thesis-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 36px;
    line-height: 1.05;
    letter-spacing: -0.035em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 12px 0 0;
  }

  .thesis-body {
    max-width: 680px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    font-size: 17px;
    line-height: 1.6;
    color: var(--m-color-graphite, #23272B);
  }

  .thesis-body p {
    margin: 0;
  }

  .thesis-body strong {
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
  }

  /* Loop Section (How It Works) */
  .loop-section {
    border-top: 1px solid var(--border, #DDDCD5);
    border-bottom: 1px solid var(--border, #DDDCD5);
    background: #FFFEFA;
    padding: 80px 0;
  }

  .loop-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .loop-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 32px;
  }

  .loop-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 38px;
    line-height: 1.05;
    letter-spacing: -0.035em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 12px 0 0;
    max-width: 580px;
  }

  .loop-subtitle {
    font-size: 13px;
    line-height: 1.5;
    color: var(--m-color-slate, #6D7378);
    max-width: 340px;
    margin: 0;
  }

  .loop-steps-grid {
    margin-top: 48px;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    border-top: 1px solid #D5D4CD;
    border-bottom: 1px solid #D5D4CD;
  }

  .loop-step-card {
    position: relative;
    padding: 24px 20px 24px 0;
    min-height: 170px;
    border-right: 1px solid #D5D4CD;
  }

  .loop-step-card:last-child {
    border-right: none;
    padding-right: 0;
  }

  .loop-step-card:not(:first-child) {
    padding-left: 20px;
  }

  .step-num {
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .step-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
    margin: 20px 0 8px;
  }

  .step-desc {
    font-size: 12px;
    line-height: 1.5;
    color: var(--m-color-slate, #6D7378);
    margin: 0;
  }

  .step-connector {
    position: absolute;
    right: -8px;
    top: 56px;
    z-index: 10;
    background: #FFFEFA;
    padding: 0 4px;
    font-family: var(--font-serif, serif);
    font-size: 16px;
    color: var(--m-color-horizon-blue, #4F6BFF);
  }

  /* Experiences Section */
  .experiences-section {
    padding: 88px 0 96px;
  }

  .experiences-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .experiences-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 38px;
    line-height: 1.05;
    letter-spacing: -0.035em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 12px 0 0;
    max-width: 680px;
  }

  .experiences-grid {
    margin-top: 40px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

  .experience-card {
    position: relative;
    border-radius: 12px;
    border: 1px solid var(--border, #DDDCD5);
    background: #ffffff;
    padding: 32px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  .card-bg-ring {
    position: absolute;
    right: -3rem;
    bottom: -3rem;
    width: 12rem;
    height: 12rem;
    border-radius: 50%;
    border: 1px solid rgba(79, 107, 255, 0.18);
  }

  .card-content {
    position: relative;
    z-index: 2;
  }

  .card-icon-badge {
    width: 36px;
    height: 36px;
    border-radius: 6px;
    background: #EBF0FF;
    color: var(--m-color-horizon-blue, #4F6BFF);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .card-audience {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--m-color-slate, #6D7378);
    margin: 20px 0 8px;
  }

  .card-heading {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 28px;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-weight: 500;
    color: var(--m-color-obsidian, #111315);
    margin: 0;
  }

  .card-description {
    margin: 14px 0 24px;
    font-size: 13px;
    line-height: 1.55;
    color: var(--m-color-slate, #6D7378);
    max-width: 440px;
  }

  .card-action-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-bottom: 1px solid var(--m-color-horizon-blue, #4F6BFF);
    padding-bottom: 2px;
    font-size: 13px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .card-action-link:hover {
    color: var(--m-color-horizon-blue, #4F6BFF);
  }

  /* Deep Obsidian CTA Banner */
  .cta-banner-section {
    position: relative;
    background: var(--m-color-obsidian, #111315);
    color: #ffffff;
    padding: 80px 0;
    overflow: hidden;
  }

  .banner-bg-ring {
    position: absolute;
    left: 60%;
    top: -12rem;
    width: 32rem;
    height: 32rem;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 0 0 78px rgba(255, 255, 255, 0.025);
  }

  .cta-banner-container {
    position: relative;
    z-index: 2;
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 48px;
  }

  .cta-banner-copy {
    max-width: 620px;
  }

  .banner-kicker {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #A9BBFF;
    margin: 0;
  }

  .banner-title {
    font-family: var(--font-serif, "Newsreader", Charter, Georgia, serif);
    font-size: 40px;
    line-height: 1.05;
    letter-spacing: -0.04em;
    font-weight: 500;
    color: #ffffff;
    margin: 12px 0 16px;
  }

  .banner-subtitle {
    font-size: 14px;
    line-height: 1.6;
    color: #D5D9DF;
    margin: 0;
  }

  .cta-banner-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .btn-banner-light {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #ffffff;
    color: var(--m-color-obsidian, #111315);
    font-size: 12px;
    font-weight: 600;
    padding: 12px 18px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease;
    white-space: nowrap;
  }

  .btn-banner-light:hover {
    background: #F0EFEA;
  }

  .btn-banner-ghost {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: transparent;
    border: 1px solid #666C73;
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    padding: 12px 18px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease;
    white-space: nowrap;
  }

  .btn-banner-ghost:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  /* Responsive Breakpoints */
  @media (max-width: 960px) {
    .hero-container {
      grid-template-columns: 1fr;
      gap: 40px;
    }

    .thesis-container {
      grid-template-columns: 1fr;
      gap: 24px;
    }

    .loop-header-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }

    .loop-steps-grid {
      grid-template-columns: 1fr;
      border-top: none;
    }

    .loop-step-card {
      border-right: none;
      border-bottom: 1px solid #D5D4CD;
      padding: 16px 0;
      min-height: auto;
    }

    .loop-step-card:not(:first-child) {
      padding-left: 0;
    }

    .step-connector {
      display: none;
    }

    .experiences-grid {
      grid-template-columns: 1fr;
    }

    .cta-banner-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 32px;
    }
  }

  @media (max-width: 640px) {
    .landing-header-inner {
      height: 64px;
      padding: 0 16px;
    }

    .landing-nav {
      display: none;
    }

    .btn-text-full {
      display: none;
    }

    .btn-text-short {
      display: inline;
    }

    .hero-title {
      font-size: 38px;
    }

    .preview-doc-area {
      padding-right: 0;
    }

    .preview-companion-aside {
      position: static;
      width: 100%;
      border-left: none;
      border-top: 3px solid var(--m-color-horizon-blue, #4F6BFF);
    }

    .preview-body {
      flex-direction: column;
    }
  }
</style>
