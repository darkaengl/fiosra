<script>
  let { score = 0 } = $props();

  let percentage = $derived(Math.round(score * 100));
  let level = $derived(percentage >= 80 ? 'high' : percentage >= 60 ? 'medium' : 'low');
  let color = $derived(percentage >= 80 ? 'var(--color-signal-green)' : percentage >= 60 ? 'var(--color-amber)' : 'var(--color-rose)');
</script>

<div class="score-meter">
  <div class="score-bar">
    <div class="score-fill {level}" style="width: {percentage}%;"></div>
  </div>
  <span class="score-value" style="color: {color};">{percentage}%</span>
</div>

<style>
  .score-meter {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .score-bar {
    width: 70px;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }

  .score-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .score-fill.high {
    background: var(--color-signal-green);
  }

  .score-fill.medium {
    background: var(--color-amber);
  }

  .score-fill.low {
    background: var(--color-rose);
  }

  .score-value {
    font-size: 12px;
    font-weight: 700;
  }
</style>
