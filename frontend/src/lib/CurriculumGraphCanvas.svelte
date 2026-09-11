<script>
  let { graph = { nodes: [], edges: [] }, selectedConceptId = '', onSelect = () => {} } = $props();
  let scale = $state(1);

  const levelOrder = ['course_theme', 'strand', 'topic', 'subtopic', 'atomic_concept'];
  const levelLabels = {
    course_theme: 'Course theme', strand: 'Strand', topic: 'Topic',
    subtopic: 'Subtopic', atomic_concept: 'Atomic concept',
  };
  const colors = {
    course_theme: '#a855f7', strand: '#6366f1', topic: '#3b82f6',
    subtopic: '#14b8a6', atomic_concept: '#10b981',
  };

  function nodeColor(level) { return colors[level] || '#64748b'; }
  function nodeLabel(level) { return levelLabels[level] || level?.replaceAll('_', ' ') || 'Concept'; }

  function wrapLabel(label) {
    const words = String(label || '').split(/\s+/);
    const lines = [''];
    for (const word of words) {
      const candidate = `${lines.at(-1)} ${word}`.trim();
      if (candidate.length > 23 && lines.length < 3) lines.push(word);
      else lines[lines.length - 1] = candidate;
    }
    return lines.map((line) => line.length > 27 ? `${line.slice(0, 26)}…` : line);
  }

  let positionedNodes = $derived.by(() => {
    const nodes = graph?.nodes || [];
    const parents = new Map();
    for (const edge of graph?.edges || []) {
      if (edge.relation === 'CONTAINS') parents.set(edge.target, edge.source);
    }
    const cache = new Map();
    function depth(id, seen = new Set()) {
      if (cache.has(id)) return cache.get(id);
      const node = nodes.find((item) => item.concept_id === id);
      const structuralDepth = Math.max(0, levelOrder.indexOf(node?.level));
      const parent = parents.get(id);
      if (!parent || seen.has(id)) { cache.set(id, structuralDepth); return structuralDepth; }
      const value = Math.max(structuralDepth, depth(parent, new Set([...seen, id])) + 1);
      cache.set(id, value);
      return value;
    }
    const lanes = new Map();
    for (const node of nodes) {
      const lane = Math.min(4, depth(node.concept_id));
      if (!lanes.has(lane)) lanes.set(lane, []);
      lanes.get(lane).push(node);
    }
    const layout = [];
    for (const [lane, laneNodes] of lanes) {
      laneNodes.sort((a, b) => a.label.localeCompare(b.label));
      const verticalGap = 620 / (laneNodes.length + 1);
      laneNodes.forEach((node, index) => layout.push({
        ...node,
        x: 130 + lane * 245,
        y: 50 + verticalGap * (index + 1),
        lines: wrapLabel(node.label),
      }));
    }
    return layout;
  });

  function nodeFor(id) { return positionedNodes.find((node) => node.concept_id === id); }
  function edgePath(edge) {
    const source = nodeFor(edge.source);
    const target = nodeFor(edge.target);
    if (!source || !target) return '';
    const sx = source.x + 91;
    const sy = source.y;
    const tx = target.x - 91;
    const ty = target.y;
    const bend = Math.max(65, Math.abs(tx - sx) * 0.45);
    return `M ${sx} ${sy} C ${sx + bend} ${sy}, ${tx - bend} ${ty}, ${tx} ${ty}`;
  }

  function zoom(delta) { scale = Math.max(0.72, Math.min(1.35, Number((scale + delta).toFixed(2)))); }
</script>

<div class="canvas-shell">
  <div class="canvas-toolbar">
    <div class="canvas-key"><span><i class="hierarchy"></i> Contains</span><span><i class="prerequisite"></i> Prerequisite</span></div>
    <div class="zoom-controls"><button type="button" onclick={() => zoom(-0.1)} aria-label="Zoom out">−</button><span>{Math.round(scale * 100)}%</span><button type="button" onclick={() => zoom(0.1)} aria-label="Zoom in">+</button></div>
  </div>

  {#if !positionedNodes.length}
    <div class="empty-canvas"><strong>No active concepts yet</strong><span>Generate and validate a course concept graph to see its hierarchy here.</span></div>
  {:else}
    <div class="canvas-scroll">
      <svg class="graph-canvas" viewBox="0 0 1200 720" role="img" aria-label="Course concept graph">
        <defs>
          <marker id="contains-arrow" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8Z" fill="#60a5fa" /></marker>
          <marker id="prereq-arrow" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8Z" fill="#c084fc" /></marker>
        </defs>
        <rect width="1200" height="720" fill="#0d1119" />
        <g transform="translate(600 360) scale({scale}) translate(-600 -360)">
          {#each graph.edges || [] as edge}
            {@const related = !selectedConceptId || edge.source === selectedConceptId || edge.target === selectedConceptId}
            {#if edgePath(edge)}
              <path class:muted={!related} class:prerequisite={edge.relation === 'PREREQUISITE_OF'} d={edgePath(edge)} marker-end={edge.relation === 'PREREQUISITE_OF' ? 'url(#prereq-arrow)' : 'url(#contains-arrow)'} />
            {/if}
          {/each}
          {#each positionedNodes as node}
            {@const selected = node.concept_id === selectedConceptId}
            <g class:selected class:unrelated={selectedConceptId && !graph.edges.some((edge) => edge.source === selectedConceptId && edge.target === node.concept_id || edge.target === selectedConceptId && edge.source === node.concept_id) && !selected} class="graph-node" transform="translate({node.x},{node.y})" role="button" tabindex="0" onclick={() => onSelect(node.concept_id)} onkeydown={(event) => event.key === 'Enter' && onSelect(node.concept_id)}>
              <rect x="-91" y="-42" width="182" height="84" rx="12" fill="#161b22" stroke={nodeColor(node.level)} stroke-width={selected ? 3 : 1.5} />
              <circle cx="-72" cy="-21" r="5" fill={nodeColor(node.level)} />
              <text x="-60" y="-17" class="node-level">{nodeLabel(node.level)}</text>
              {#each node.lines as line, index}
                <text x="0" y={index * 15 + (node.lines.length === 1 ? 11 : 3)} text-anchor="middle" class="node-label">{line}</text>
              {/each}
            </g>
          {/each}
        </g>
      </svg>
    </div>
  {/if}
</div>

<style>
  .canvas-shell { background: #0d1119; display: flex; flex: 1; flex-direction: column; min-height: 520px; overflow: hidden; }
  .canvas-toolbar { align-items: center; background: rgba(22,27,34,.88); border-bottom: 1px solid var(--color-graphite-border); display: flex; justify-content: space-between; padding: 10px 14px; }
  .canvas-key { color: var(--color-slate-light); display: flex; font-size: 10px; gap: 14px; }
  .canvas-key span { align-items: center; display: flex; gap: 5px; }
  .canvas-key i { border-radius: 50%; display: inline-block; height: 7px; width: 7px; }.canvas-key .hierarchy { background: #60a5fa; }.canvas-key .prerequisite { background: #c084fc; }
  .zoom-controls { align-items: center; color: var(--color-slate-light); display: flex; font-family: var(--font-mono); font-size: 10px; gap: 7px; }.zoom-controls button { background: var(--color-obsidian); border: 1px solid var(--color-graphite-border); border-radius: 4px; color: var(--color-heading); cursor: pointer; font-size: 16px; height: 23px; line-height: 16px; width: 23px; }
  .canvas-scroll { flex: 1; min-height: 460px; overflow: auto; }.graph-canvas { display: block; height: 100%; min-height: 520px; min-width: 900px; width: 100%; }
  :global(.graph-canvas path) { fill: none; marker-end: url(#contains-arrow); stroke: #60a5fa; stroke-width: 2; opacity: .72; }.graph-canvas path.prerequisite { marker-end: url(#prereq-arrow); stroke: #c084fc; stroke-dasharray: 6 5; }.graph-canvas path.muted { opacity: .15; }
  .graph-node { cursor: pointer; transition: opacity .15s; }.graph-node:hover rect { filter: brightness(1.3); }.graph-node.selected rect { filter: drop-shadow(0 0 8px rgba(96,165,250,.58)); }.graph-node.unrelated { opacity: .35; }
  .node-level { fill: #94a3b8; font-family: var(--font-ui); font-size: 9px; font-weight: 700; letter-spacing: .3px; text-transform: uppercase; }.node-label { fill: #f1f5f9; font-family: var(--font-ui); font-size: 11.5px; font-weight: 650; }
  .empty-canvas { align-items: center; color: var(--color-slate-muted); display: flex; flex: 1; flex-direction: column; font-size: 12px; gap: 7px; justify-content: center; text-align: center; }.empty-canvas strong { color: var(--color-heading); font-size: 14px; }
</style>
