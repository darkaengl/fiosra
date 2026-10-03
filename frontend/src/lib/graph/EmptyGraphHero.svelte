<script lang="ts">
  let {
    course = null,
    selectedModuleId = $bindable(''),
    isHydrating = false,
    onStartHydration = () => {}
  } = $props<{
    course?: any;
    selectedModuleId?: string;
    isHydrating?: boolean;
    onStartHydration?: () => void;
  }>();
</script>

<div class="empty-graph-hero">
  <div class="hero-icon-ring">
    <span class="hero-bolt">⚡</span>
  </div>
  <span class="hero-eyebrow">Pedagogical Concept Graph</span>
  <h2 class="hero-title">Graph Not Hydrated Yet</h2>
  <p class="hero-desc">
    This course contains <strong>{course?.modules?.length || 0} modules</strong> with source materials in Neo4j.
    Select a target unit below and hydrate the knowledge graph to synthesize curriculum concepts and evidence links.
  </p>

  <div class="hero-controls-box">
    <label class="hero-select-label">
      <span>Target Scope:</span>
      <select bind:value={selectedModuleId} class="hero-select" disabled={isHydrating}>
        <option value="">All Units (Entire Course)</option>
        {#each (course?.modules || []).slice().sort((a: any, b: any) => a.position - b.position) as mod}
          <option value={mod.module_id}>Unit {mod.position}: {mod.title}</option>
        {/each}
      </select>
    </label>

    <button
      type="button"
      class="hero-hydrate-btn"
      onclick={onStartHydration}
      disabled={isHydrating}
    >
      <span>⚡</span> Hydrate Knowledge Graph
    </button>
  </div>
</div>

<style>
  .empty-graph-hero {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 520px;
    width: 90%;
    padding: 34px 30px;
    border-radius: 16px;
    text-align: center;
    z-index: 20;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(16px);
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(226, 232, 240, 0.9);
    color: #1e293b;
  }

  :global(.dark-mode) .empty-graph-hero {
    background: rgba(22, 22, 22, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f1f5f9;
  }

  .hero-icon-ring {
    width: 54px;
    height: 54px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(124, 58, 237, 0.15));
    border: 1px solid rgba(37, 99, 235, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .hero-bolt {
    font-size: 24px;
  }

  .hero-eyebrow {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #2563eb;
    margin-bottom: 8px;
  }

  .hero-title {
    font-size: 21px;
    font-weight: 700;
    margin: 0 0 10px;
  }

  .hero-desc {
    font-size: 13.5px;
    line-height: 1.55;
    color: #64748b;
    margin: 0 0 24px;
  }
  :global(.dark-mode) .hero-desc {
    color: #94a3b8;
  }

  .hero-controls-box {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .hero-select-label {
    display: flex;
    flex-direction: column;
    text-align: left;
    gap: 5px;
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
  }

  .hero-select {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    color: inherit;
    outline: none;
  }

  .hero-hydrate-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
  }
  .hero-hydrate-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #1d4ed8, #6d28d9);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.4);
  }
</style>
