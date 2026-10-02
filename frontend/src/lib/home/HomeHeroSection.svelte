<script lang="ts">
  let { symbolUrl = "./fiosra-symbol.png" } = $props<{ symbolUrl?: string }>();
</script>

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
        <a href="#/courses" class="btn-hero-educator">
          Explore an educator journey
          <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
          </svg>
        </a>
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
              <img src={symbolUrl} alt="" class="symbol-pill-img" />
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
            <img src={symbolUrl} alt="" class="companion-aside-symbol" />
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

<style>
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

  .btn-hero-educator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #ffffff;
    border: 1.5px solid var(--m-color-horizon-blue, #4F6BFF);
    color: var(--m-color-obsidian, #111315);
    font-size: 13px;
    font-weight: 600;
    padding: 12px 20px;
    border-radius: 6px;
    text-decoration: none;
    box-shadow: 0 1px 3px rgba(79, 107, 255, 0.12);
    transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
  }

  .btn-hero-educator:hover {
    background: var(--m-color-horizon-blue-soft, #EBF0FF);
    border-color: #3857E8;
  }

  .btn-hero-educator:active {
    transform: scale(0.98);
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

  @media (max-width: 960px) {
    .hero-container {
      grid-template-columns: 1fr;
      gap: 40px;
    }
  }

  @media (max-width: 640px) {
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
