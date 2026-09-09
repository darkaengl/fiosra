<script>
  import { onMount } from 'svelte';

  let svgEl;
  let activeFilter = $state('all');

  const nodes = [
    { id: 'KC_HIST_FISCAL_CRISIS', label: 'Royal Fiscal Crisis 1786', x: 300, y: 200, type: 'root' },
    { id: 'KC_HIST_ESTATE_SYSTEM', label: 'Three Estates System', x: 180, y: 350, type: 'prereq' },
    { id: 'KC_HIST_SOCIAL_CONTRACT', label: 'Social Contract Theory', x: 450, y: 130, type: 'prereq' },
    { id: 'KC_HIST_POPULAR_SOV', label: 'Popular Sovereignty', x: 580, y: 300, type: 'target' },
    { id: 'KC_HIST_CONSTITUTIONAL', label: 'Constitutional Crisis', x: 400, y: 420, type: 'downstream' },
    { id: 'KC_HIST_TERROR', label: 'Reign of Terror', x: 620, y: 450, type: 'downstream' },
    { id: 'KC_HIST_NAPOLEON', label: 'Napoleonic Order', x: 740, y: 330, type: 'downstream' },
  ];

  const edges = [
    { from: 'KC_HIST_FISCAL_CRISIS', to: 'KC_HIST_POPULAR_SOV' },
    { from: 'KC_HIST_ESTATE_SYSTEM', to: 'KC_HIST_FISCAL_CRISIS' },
    { from: 'KC_HIST_SOCIAL_CONTRACT', to: 'KC_HIST_POPULAR_SOV' },
    { from: 'KC_HIST_POPULAR_SOV', to: 'KC_HIST_CONSTITUTIONAL' },
    { from: 'KC_HIST_CONSTITUTIONAL', to: 'KC_HIST_TERROR' },
    { from: 'KC_HIST_TERROR', to: 'KC_HIST_NAPOLEON' },
  ];

  function nodeColor(type) {
    if (type === 'root') return '#3b82f6';
    if (type === 'prereq') return '#8b5cf6';
    if (type === 'target') return '#10b981';
    return '#64748b';
  }

  function getNode(id) { return nodes.find(n => n.id === id); }
</script>

<div class="kg-layout">
  <!-- Graph Canvas -->
  <div class="graph-viewport">
    <div class="graph-toolbar">
      <div class="toolbar-group">
        <span style="font-size: 12px; color: var(--color-slate-muted); font-weight: 600;">FILTER:</span>
        {#each ['all', 'prereq', 'target', 'downstream'] as f}
          <button class="toggle-chip {activeFilter === f ? 'active' : ''}" onclick={() => activeFilter = f}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        {/each}
      </div>
      <div class="toolbar-group">
        <span style="font-size: 11.5px; color: var(--color-slate-light);">📊 7 Nodes • 6 Edges • HIST-201</span>
      </div>
    </div>

    <svg class="graph-svg" viewBox="0 0 960 600" bind:this={svgEl}>
      <!-- Grid background -->
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
        </pattern>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" opacity="0.7"/>
        </marker>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      <!-- Edges -->
      {#each edges as e}
        {@const from = getNode(e.from)}
        {@const to = getNode(e.to)}
        {#if from && to}
          <line
            x1={from.x} y1={from.y}
            x2={to.x} y2={to.y}
            stroke="rgba(59,130,246,0.4)" stroke-width="2"
            marker-end="url(#arrowhead)"
          />
        {/if}
      {/each}

      <!-- Nodes -->
      {#each nodes as node}
        <g class="graph-node" transform="translate({node.x},{node.y})">
          <circle r="28" fill={nodeColor(node.type)} opacity="0.9" />
          <circle r="28" fill="none" stroke={nodeColor(node.type)} stroke-width="2" opacity="0.4" />
          <text y="46" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.8)" font-weight="600"
            style="font-family: var(--font-mono);">
            {node.id.replace('KC_HIST_', '').slice(0, 12)}
          </text>
        </g>
      {/each}
    </svg>

    <!-- Legend -->
    <div class="graph-legend">
      <div class="legend-title">Node Types</div>
      {#each [
        { type: 'prereq', color: '#8b5cf6', label: 'Prerequisite KC' },
        { type: 'root', color: '#3b82f6', label: 'Root Concept' },
        { type: 'target', color: '#10b981', label: 'Target KC' },
        { type: 'downstream', color: '#64748b', label: 'Downstream' },
      ] as l}
        <div class="legend-row">
          <div class="legend-dot" style="background: {l.color}"></div>
          <span>{l.label}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- Right Panel: KC Inspector -->
  <aside class="kg-inspector">
    <div class="inspector-header">
      <div class="inspector-title">KC Inspector</div>
      <div class="inspector-sub">Click a node to inspect</div>
    </div>

    <div class="inspector-section">
      <div class="section-label">Selected: HIST-201 • Fall 2026</div>
      <div class="inspector-stat-grid">
        <div class="inspector-stat"><div class="is-val">7</div><div class="is-label">Total KCs</div></div>
        <div class="inspector-stat"><div class="is-val">6</div><div class="is-label">DAG Edges</div></div>
        <div class="inspector-stat"><div class="is-val">14</div><div class="is-label">Misc. Traps</div></div>
        <div class="inspector-stat"><div class="is-val">3</div><div class="is-label">Modules</div></div>
      </div>
    </div>

    <div class="inspector-section">
      <div class="section-label">Knowledge Components</div>
      <div class="kc-list">
        {#each nodes as node}
          <div class="kc-list-item">
            <div class="kc-dot" style="background: {nodeColor(node.type)}"></div>
            <div>
              <div class="kc-id">{node.id}</div>
              <div class="kc-label-sm">{node.label}</div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="inspector-section">
      <button class="btn btn-primary" style="width: 100%;">Export Graph (JSON)</button>
      <button class="btn btn-secondary" style="width: 100%; margin-top: 8px;">Sync to Neo4j</button>
    </div>
  </aside>
</div>

<style>
  .kg-layout { display: grid; grid-template-columns: 1fr 360px; height: calc(100vh - 56px); }
  .graph-viewport { position: relative; background: #0b0f17; border-right: 1px solid var(--color-graphite-border); overflow: hidden; }
  .graph-toolbar { position: absolute; top: 20px; left: 24px; right: 24px; display: flex; justify-content: space-between; align-items: center; z-index: 10; }
  .toolbar-group { display: flex; align-items: center; gap: 8px; background: rgba(22,27,34,.85); backdrop-filter: blur(12px); border: 1px solid var(--color-graphite-border); padding: 6px 12px; border-radius: var(--radius-sm); }
  .toggle-chip { background: transparent; border: 1px solid transparent; color: var(--color-slate-light); font-size: 11.5px; font-weight: 500; padding: 4px 10px; border-radius: var(--radius-xs); cursor: pointer; transition: all .15s; }
  .toggle-chip:hover { color: #fff; background: var(--color-graphite-card); }
  .toggle-chip.active { background: rgba(59,130,246,.15); border-color: var(--color-horizon-blue); color: var(--color-horizon-bright); font-weight: 600; }
  .graph-svg { width: 100%; height: 100%; }
  .graph-node { cursor: pointer; }
  .graph-node:hover circle:first-child { opacity: 1; }
  .graph-legend { position: absolute; bottom: 24px; left: 24px; background: rgba(22,27,34,.85); backdrop-filter: blur(12px); border: 1px solid var(--color-graphite-border); padding: 12px 16px; border-radius: var(--radius-sm); display: flex; flex-direction: column; gap: 8px; }
  .legend-title { font-size: 11px; font-weight: 700; color: var(--color-slate-muted); text-transform: uppercase; margin-bottom: 4px; }
  .legend-row { display: flex; align-items: center; gap: 8px; font-size: 11.5px; color: var(--color-slate-light); }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
  .kg-inspector { background: var(--color-graphite); display: flex; flex-direction: column; gap: 0; overflow-y: auto; }
  .inspector-header { padding: 24px 20px; border-bottom: 1px solid var(--color-graphite-border); }
  .inspector-title { font-size: 14px; font-weight: 700; color: #fff; }
  .inspector-sub { font-size: 11.5px; color: var(--color-slate-muted); margin-top: 2px; }
  .inspector-section { padding: 20px; border-bottom: 1px solid var(--color-graphite-border); display: flex; flex-direction: column; gap: 12px; }
  .section-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--color-slate-muted); letter-spacing: .5px; }
  .inspector-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .inspector-stat { background: var(--color-graphite-card); border: 1px solid var(--color-graphite-border); border-radius: var(--radius-sm); padding: 12px 14px; }
  .is-val { font-family: var(--font-brand); font-size: 22px; font-weight: 700; color: #fff; }
  .is-label { font-size: 10.5px; color: var(--color-slate-muted); text-transform: uppercase; margin-top: 2px; }
  .kc-list { display: flex; flex-direction: column; gap: 8px; }
  .kc-list-item { display: flex; align-items: flex-start; gap: 8px; }
  .kc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 3px; }
  .kc-id { font-family: var(--font-mono); font-size: 10px; color: var(--color-aurora-bright); }
  .kc-label-sm { font-size: 11.5px; color: #e2e8f0; margin-top: 2px; }
</style>
