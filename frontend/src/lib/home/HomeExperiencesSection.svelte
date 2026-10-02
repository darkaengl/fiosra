<script lang="ts">
</script>

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
              <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 2.5"/>
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

<style>
  .experiences-section {
    padding: 88px 0 96px;
  }

  .experiences-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .section-kicker {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    margin: 0;
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

  @media (max-width: 960px) {
    .experiences-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
