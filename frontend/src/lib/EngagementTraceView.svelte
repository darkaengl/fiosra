<script>
  import { onMount } from 'svelte';
  import ThinkingTimeline from './ThinkingTimeline.svelte';

  let {
    graphMetrics = { claims: 0, evidence: 0, warrants: 0, assumptions: 0, probes: 0 },
    sessionId = '',
    sessionEvents = [],
    activeTraceSubTab = 'reasoning',
    onSubTabChange = () => null,
  } = $props();

  let localSubTab = $state(null);
  let currentSubTab = $derived(localSubTab ?? activeTraceSubTab);

  // Dual timeline data
  let reasoningNodes = $state([]);
  let activityNodes = $state([]);
  let expandedReasoningNode = $state(-1);
  let expandedActivityNode = $state(-1);
  let timelineLoading = $state(false);

  async function loadTimelines() {
    if (!sessionId) return;
    timelineLoading = true;
    try {
      const [reasoningRes, activityRes] = await Promise.all([
        fetch(`/evidence/trace/${sessionId}/reasoning`),
        fetch(`/evidence/trace/${sessionId}/activity`),
      ]);
      if (reasoningRes.ok) {
        const data = await reasoningRes.json();
        reasoningNodes = data.nodes || [];
      }
      if (activityRes.ok) {
        const data = await activityRes.json();
        activityNodes = data.nodes || [];
      }
    } catch (err) {
      console.warn('Loading thinking timelines:', err);
    } finally {
      timelineLoading = false;
    }
  }

  // Load timelines on mount
  onMount(() => {
    loadTimelines();
  });

  // Reactively reload when session events change (new activity)
  $effect(() => {
    if (sessionEvents.length > 0 && sessionId) {
      loadTimelines();
    }
  });
</script>

<div class="engagement-trace-root" aria-label="Reasoning & Activity Timeline">
  <!-- Sub-tabs to easily switch between Reasoning Trace and Activity Log -->
  <div class="trace-subtab-bar">
    <button
      type="button"
      class="subtab-btn"
      class:active={currentSubTab === 'reasoning'}
      onclick={() => { localSubTab = 'reasoning'; onSubTabChange('reasoning'); }}
    >
      💡 Reasoning
    </button>
    <button
      type="button"
      class="subtab-btn"
      class:active={currentSubTab === 'activity'}
      onclick={() => { localSubTab = 'activity'; onSubTabChange('activity'); }}
    >
      ⏱️ Activity
    </button>
  </div>

  <div class="trace-scrollable-content">
    <!-- Top Metrics Summary (Compact 4-Tile Grid) -->
    <div class="trace-metrics-grid">
      <div class="metric-tile claims">
        <span class="metric-val">{graphMetrics.claims || 0}</span>
        <span class="metric-lbl">Claims Drafted</span>
      </div>
      <div class="metric-tile evidence">
        <span class="metric-val">{graphMetrics.evidence || 0}</span>
        <span class="metric-lbl">Evidence Grounded</span>
      </div>
      <div class="metric-tile warrants">
        <span class="metric-val">{graphMetrics.warrants || 0}</span>
        <span class="metric-lbl">Causal Warrants</span>
      </div>
      <div class="metric-tile assumptions">
        <span class="metric-val">{graphMetrics.assumptions || 0}</span>
        <span class="metric-lbl">Assumptions</span>
      </div>
    </div>

    {#if currentSubTab === 'reasoning'}
      <!-- TAB 1: CURATED REASONING TRACE -->
      <section class="trace-panel-card timeline-panel-card">
        <header class="panel-card-header">
          <div class="header-titles">
            <span class="card-eyebrow">Intellectual Evolution</span>
            <h4>Curated Reasoning Trace</h4>
          </div>
          <span class="node-count-badge">{reasoningNodes.length} milestones</span>
        </header>
        <p class="timeline-intro">Key moments where hypotheses formed, met friction, and evolved.</p>
        {#if timelineLoading}
          <div class="timeline-loading-state"><div class="spinner"></div><span>Tracing reasoning path…</span></div>
        {:else}
          <ThinkingTimeline
            nodes={reasoningNodes}
            showContent={true}
            showDiff={true}
            expandedNodeIndex={expandedReasoningNode}
            onNodeClick={(idx) => {
              expandedReasoningNode = expandedReasoningNode === idx ? -1 : idx;
            }}
          />
        {/if}
      </section>
    {:else if currentSubTab === 'activity'}
      <!-- TAB 2: CHRONOLOGICAL ACTIVITY LOG -->
      <section class="trace-panel-card timeline-panel-card">
        <header class="panel-card-header">
          <div class="header-titles">
            <span class="card-eyebrow">Append-Only Audit</span>
            <h4>Mechanical Activity Log</h4>
          </div>
          <span class="node-count-badge">{activityNodes.length} events</span>
        </header>
        <p class="timeline-intro">Complete chronological event record of draft saves, tutor exchanges, and marginalia probes.</p>
        {#if timelineLoading}
          <div class="timeline-loading-state"><div class="spinner"></div><span>Loading activity log…</span></div>
        {:else}
          <ThinkingTimeline
            nodes={activityNodes}
            showContent={true}
            showDiff={false}
            expandedNodeIndex={expandedActivityNode}
            onNodeClick={(idx) => {
              expandedActivityNode = expandedActivityNode === idx ? -1 : idx;
            }}
          />
        {/if}
      </section>
    {/if}
  </div>
</div>

<style>
  .engagement-trace-root {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    background: var(--color-obsidian, #ffffff);
    overflow: hidden;
  }

  :global([data-theme="dark"]) .engagement-trace-root {
    background: #0d1117;
  }

  .trace-subtab-bar {
    display: flex;
    gap: 4px;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.03);
    border-bottom: 1px solid var(--color-graphite-border, #e2e8f0);
    flex-shrink: 0;
  }

  :global([data-theme="dark"]) .trace-subtab-bar {
    background: rgba(255, 255, 255, 0.03);
    border-color: #30363d;
  }

  .subtab-btn {
    flex: 1;
    padding: 6px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    color: var(--color-slate-subtle, #64748b);
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
  }

  :global([data-theme="dark"]) .subtab-btn {
    color: #8b949e;
  }

  .subtab-btn:hover {
    color: var(--color-slate-bright, #0f172a);
    background: rgba(0, 0, 0, 0.04);
  }

  :global([data-theme="dark"]) .subtab-btn:hover {
    color: #f0f6fc;
    background: rgba(255, 255, 255, 0.06);
  }

  .subtab-btn.active {
    background: var(--color-surface, #ffffff);
    color: var(--color-aurora, #0284c7);
    border-color: var(--color-graphite-border, #cbd5e1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  :global([data-theme="dark"]) .subtab-btn.active {
    background: #21262d;
    color: #38bdf8;
    border-color: #30363d;
  }

  .trace-scrollable-content {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px 40px 14px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  /* Metric 4-Tile Grid */
  .trace-metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    flex-shrink: 0;
  }

  .metric-tile {
    background: var(--color-surface, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: 8px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  }

  :global([data-theme="dark"]) .metric-tile {
    background: #161b22;
    border-color: #30363d;
  }

  .metric-val {
    font-size: 1.3rem;
    font-weight: 800;
    line-height: 1.1;
  }

  .metric-tile.claims .metric-val { color: #0284c7; }
  .metric-tile.evidence .metric-val { color: #059669; }
  .metric-tile.warrants .metric-val { color: #7c3aed; }
  .metric-tile.assumptions .metric-val { color: #d97706; }

  :global([data-theme="dark"]) .metric-tile.claims .metric-val { color: #38bdf8; }
  :global([data-theme="dark"]) .metric-tile.evidence .metric-val { color: #34d399; }
  :global([data-theme="dark"]) .metric-tile.warrants .metric-val { color: #a78bfa; }
  :global([data-theme="dark"]) .metric-tile.assumptions .metric-val { color: #fbbf24; }

  .metric-lbl {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-slate-subtle, #64748b);
  }

  :global([data-theme="dark"]) .metric-lbl {
    color: #8b949e;
  }

  /* Card */
  .trace-panel-card {
    background: var(--color-surface, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e8f0);
    border-radius: 10px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  :global([data-theme="dark"]) .trace-panel-card {
    background: #161b22;
    border-color: #30363d;
  }

  .panel-card-header {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
  }

  .header-titles {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .card-eyebrow {
    font-size: 0.62rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-aurora, #0284c7);
  }

  .panel-card-header h4 {
    margin: 0;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--color-slate-bright, #0f172a);
  }

  :global([data-theme="dark"]) .panel-card-header h4 {
    color: #f0f6fc;
  }

  .node-count-badge {
    font-size: 0.68rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 99px;
    background: rgba(2, 132, 199, 0.08);
    color: var(--color-aurora, #0284c7);
    border: 1px solid rgba(2, 132, 199, 0.2);
    white-space: nowrap;
  }

  :global([data-theme="dark"]) .node-count-badge {
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.25);
  }

  .timeline-intro {
    font-size: 0.76rem;
    color: var(--color-slate-muted, #64748b);
    line-height: 1.45;
    margin: -4px 0 6px 0;
  }

  :global([data-theme="dark"]) .timeline-intro {
    color: #8b949e;
  }

  .timeline-loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 36px 12px;
    color: var(--color-slate-muted, #64748b);
    font-size: 0.8rem;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(2, 132, 199, 0.2);
    border-top-color: var(--color-aurora, #0284c7);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
