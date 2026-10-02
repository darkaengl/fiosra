<script lang="ts">
</script>

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

<style>
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

  .section-kicker {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    margin: 0;
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

  @media (max-width: 960px) {
    .thesis-container {
      grid-template-columns: 1fr;
      gap: 24px;
    }
  }
</style>
