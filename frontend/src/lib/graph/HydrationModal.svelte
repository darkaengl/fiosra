<script lang="ts">
  let {
    isHydrating = false,
    hydrationStage = '',
    hydrationProgress = 0
  } = $props<{
    isHydrating?: boolean;
    hydrationStage?: string;
    hydrationProgress?: number;
  }>();
</script>

{#if isHydrating}
  <div class="hydration-overlay" role="dialog" aria-modal="true" aria-label="Hydrating knowledge graph">
    <div class="hydration-modal-card">
      <div class="hydration-pulse-icon">
        <span class="bolt">⚡</span>
      </div>
      <h3>Hydrating Knowledge Graph</h3>
      <p class="hydration-stage-label">{hydrationStage}</p>

      <div class="progress-bar-track">
        <div class="progress-bar-fill" style="width: {hydrationProgress}%;"></div>
      </div>

      <div class="progress-meta-row">
        <span class="progress-pct">{hydrationProgress}% complete</span>
        <span class="progress-badge">Grounded in Primary Sources</span>
      </div>
    </div>
  </div>
{/if}

<style>
  .hydration-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .hydration-modal-card {
    background: #181b20;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 34px 28px;
    width: 90%;
    max-width: 480px;
    text-align: center;
    color: #f8fafc;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  }

  .hydration-pulse-icon {
    width: 58px;
    height: 58px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(37, 99, 235, 0.3) 0%, rgba(124, 58, 237, 0.1) 70%);
    border: 1px solid rgba(96, 165, 250, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 1.8s infinite ease-in-out;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); box-shadow: 0 0 10px rgba(37, 99, 235, 0.2); }
    50% { transform: scale(1.08); box-shadow: 0 0 24px rgba(124, 58, 237, 0.45); }
  }

  .hydration-pulse-icon .bolt {
    font-size: 26px;
  }

  .hydration-modal-card h3 {
    margin: 0 0 8px;
    font-size: 19px;
    font-weight: 700;
  }

  .hydration-stage-label {
    font-size: 13px;
    color: #94a3b8;
    margin: 0 0 22px;
    min-height: 20px;
  }

  .progress-bar-track {
    height: 10px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    overflow: hidden;
    position: relative;
    margin-bottom: 14px;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  .progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #2563eb, #38bdf8, #818cf8);
    border-radius: 999px;
    transition: width 0.5s ease;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
  }

  .progress-meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    color: #64748b;
  }

  .progress-pct {
    font-weight: 600;
    color: #38bdf8;
  }

  .progress-badge {
    background: rgba(37, 99, 235, 0.15);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.3);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10.5px;
  }
</style>
