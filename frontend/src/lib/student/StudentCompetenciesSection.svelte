<script lang="ts">
  let { modules = [] } = $props<{ modules?: any[] }>();
</script>

<section class="competencies-section">
  <span class="eyebrow-text">ACADEMIC FOUNDATION</span>
  <h2 class="section-headline">Active Curriculum Competencies</h2>

  <div class="kc-progress-grid">
    {#if modules[0]?.learning_objectives?.length}
      {#each modules[0].learning_objectives.slice(0, 4) as objective, oIdx}
        <div class="kc-progress-card">
          <div class="kc-card-top">
            <span class="badge {oIdx === 0 ? 'badge-success' : oIdx === 1 ? 'badge-info' : 'badge-warning'}">
              {oIdx === 0 ? 'Mastered' : oIdx === 1 ? 'In Synthesis' : 'In Practice'}
            </span>
            <span class="kc-card-code">M1.OBJ_{oIdx + 1}</span>
          </div>
          <h3 class="kc-card-name">{objective}</h3>
          <div class="kc-status-bar">
            <div
              class="kc-status-fill"
              style="width: {oIdx === 0 ? '100%' : oIdx === 1 ? '85%' : '50%'}; background: {oIdx === 0 ? 'var(--color-signal-green-dark, #2D6340)' : oIdx === 1 ? 'var(--color-horizon-blue, #4F6BFF)' : 'var(--color-amber, #D97706)'};"
            ></div>
          </div>
        </div>
      {/each}
    {:else}
      <div class="kc-progress-card">
        <div class="kc-card-top">
          <span class="badge badge-success">Enrolled</span>
          <span class="kc-card-code">MKT_01</span>
        </div>
        <h3 class="kc-card-name">The Marketing Mix and 4Ps Orchestration</h3>
        <div class="kc-status-bar">
          <div class="kc-status-fill" style="width: 85%; background: var(--color-horizon-blue, #4F6BFF);"></div>
        </div>
      </div>
    {/if}
  </div>
</section>

<style>
  .competencies-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 8px;
  }

  .eyebrow-text {
    font-size: 10.5px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--color-slate-subtle, #8A9096);
  }

  .section-headline {
    font-size: 19px;
    font-weight: 700;
    color: var(--color-heading, #111315);
    margin: 4px 0 0;
  }

  .kc-progress-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 14px;
  }

  .kc-progress-card {
    background: var(--surface, #ffffff);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .kc-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .badge {
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    text-transform: uppercase;
  }

  .badge-success {
    background: #EBF7F0;
    color: #2D6340;
    border: 1px solid rgba(95, 175, 122, 0.4);
  }

  .badge-info {
    background: #EBF0FF;
    color: var(--color-horizon-blue, #4F6BFF);
    border: 1px solid #C9D7FF;
  }

  .badge-warning {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FCD34D;
  }

  .kc-card-code {
    font-size: 10.5px;
    font-weight: 700;
    color: var(--color-slate-subtle, #8A9096);
  }

  .kc-card-name {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--color-heading, #111315);
    margin: 0;
    line-height: 1.35;
    flex: 1;
  }

  .kc-status-bar {
    height: 4px;
    background: var(--color-cloud-subtle, #F0EFEA);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 4px;
  }

  .kc-status-fill {
    height: 100%;
    border-radius: 999px;
  }
</style>
