<script lang="ts">
</script>

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

<style>
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

  @media (max-width: 960px) {
    .cta-banner-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 32px;
    }
  }
</style>
