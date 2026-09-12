<script>
  import { onDestroy } from 'svelte';
  import { Network, DataSet } from 'vis-network/standalone';

  let { graph = { nodes: [], edges: [] }, selectedConceptId = '', onSelect = () => {} } = $props();

  const levelLabels = {
    course_theme: 'Course theme', strand: 'Strand', topic: 'Topic',
    subtopic: 'Subtopic', atomic_concept: 'Atomic concept',
  };
  // Same five-level palette the graph has always used - level is the one
  // dimension every concept carries, so it stays the primary color key.
  const levelColor = {
    course_theme: { bg: '#7c3aed', border: '#c4b5fd' },
    strand: { bg: '#4f46e5', border: '#a5b4fc' },
    topic: { bg: '#2563eb', border: '#93c5fd' },
    subtopic: { bg: '#0d9488', border: '#5eead4' },
    atomic_concept: { bg: '#059669', border: '#6ee7b7' },
  };
  const levelSize = { course_theme: 30, strand: 25, topic: 21, subtopic: 18, atomic_concept: 15 };
  const DEFAULT_COLOR = { bg: '#475569', border: '#94a3b8' };

  const CONTAINS_COLOR = '#60a5fa';
  const PREREQ_COLOR = '#c084fc';

  let canvasEl = $state(null);
  let network = null;
  let nodesData = null;
  let edgesData = null;
  let physicsOn = $state(true);
  let hoveredId = $state('');

  function degreeOf(conceptId, edges) {
    return edges.filter((edge) => edge.source === conceptId || edge.target === conceptId).length;
  }

  function buildDatasets(currentGraph) {
    const nodes = currentGraph?.nodes || [];
    const edges = currentGraph?.edges || [];
    const visNodes = nodes.map((node) => {
      const palette = levelColor[node.level] || DEFAULT_COLOR;
      const size = (levelSize[node.level] || 16) + Math.min(6, degreeOf(node.concept_id, edges));
      return {
        id: node.concept_id,
        label: node.label,
        title: node.definition,
        shape: 'dot',
        size,
        color: {
          background: palette.bg,
          border: palette.border,
          highlight: { background: palette.border, border: '#ffffff' },
          hover: { background: palette.border, border: '#ffffff' },
        },
        font: { color: '#f8fafc', face: 'Inter, sans-serif', size: 13, vadjust: -(size + 10), strokeWidth: 3, strokeColor: 'rgba(10,14,20,0.85)' },
        borderWidth: 2,
        borderWidthSelected: 3,
        shadow: { enabled: true, color: `${palette.bg}99`, size: 14, x: 0, y: 0 },
        level: node.level,
        concept_type: node.concept_type,
      };
    });
    const visEdges = edges.map((edge, index) => {
      const isPrereq = edge.relation === 'PREREQUISITE_OF';
      return {
        id: `${edge.source}->${edge.target}-${index}`,
        from: edge.source,
        to: edge.target,
        arrows: 'to',
        color: { color: isPrereq ? PREREQ_COLOR : CONTAINS_COLOR, opacity: 0.65, highlight: isPrereq ? PREREQ_COLOR : CONTAINS_COLOR },
        dashes: isPrereq ? [6, 5] : false,
        width: 1.75,
        smooth: { type: 'curvedCW', roundness: 0.15 },
        relation: edge.relation,
      };
    });
    return { visNodes, visEdges };
  }

  function applyFocus(id) {
    if (!network || !nodesData || !edgesData) return;
    if (!id) {
      nodesData.update(nodesData.getIds().map((nodeId) => ({ id: nodeId, opacity: 1 })));
      edgesData.update(edgesData.get().map((edge) => ({ id: edge.id, color: { ...edge.color, opacity: 0.65 } })));
      return;
    }
    const connectedNodeIds = new Set([id, ...network.getConnectedNodes(id)]);
    const connectedEdgeIds = new Set(network.getConnectedEdges(id));
    nodesData.update(
      nodesData.getIds().map((nodeId) => ({ id: nodeId, opacity: connectedNodeIds.has(nodeId) ? 1 : 0.18 }))
    );
    edgesData.update(
      edgesData.get().map((edge) => ({
        id: edge.id,
        color: { ...edge.color, opacity: connectedEdgeIds.has(edge.id) ? 0.9 : 0.06 },
      }))
    );
  }

  function renderNetwork() {
    const { visNodes, visEdges } = buildDatasets(graph);
    nodesData = new DataSet(visNodes);
    edgesData = new DataSet(visEdges);

    if (network) network.destroy();
    network = new Network(
      canvasEl,
      { nodes: nodesData, edges: edgesData },
      {
        autoResize: true,
        nodes: { shape: 'dot', scaling: { min: 12, max: 36 } },
        edges: { selectionWidth: 2, hoverWidth: 1 },
        physics: {
          enabled: physicsOn,
          solver: 'barnesHut',
          barnesHut: { gravitationalConstant: -900, centralGravity: 0.6, springLength: 110, springConstant: 0.09, damping: 0.4, avoidOverlap: 0.6 },
          stabilization: { iterations: 400, fit: false },
        },
        interaction: { hover: true, tooltipDelay: 150, selectConnectedEdges: false },
      }
    );

    network.on('selectNode', (params) => onSelect(params.nodes[0] || ''));
    network.on('deselectNode', () => onSelect(''));
    network.on('hoverNode', (params) => { hoveredId = params.node; applyFocus(selectedConceptId || params.node); });
    network.on('blurNode', () => { hoveredId = ''; applyFocus(selectedConceptId); });
    network.once('stabilizationIterationsDone', () => {
      network.fit({ animation: false });
      // Small graphs can otherwise fit() into a tiny, barely-visible cluster;
      // never let the initial view be zoomed out past a comfortable minimum.
      const scale = network.getScale();
      if (scale > 1.4) network.moveTo({ scale: 1.4, animation: { duration: 300, easingFunction: 'easeOutQuad' } });
      else if (scale < 0.6) network.moveTo({ scale: 0.6, animation: { duration: 300, easingFunction: 'easeOutQuad' } });
    });

    if (selectedConceptId) {
      network.selectNodes([selectedConceptId]);
      applyFocus(selectedConceptId);
    }
  }

  onDestroy(() => network?.destroy());

  $effect(() => {
    // Re-render whenever the underlying graph data actually changes shape.
    void graph;
    if (canvasEl) renderNetwork();
  });

  $effect(() => {
    if (network && !hoveredId) applyFocus(selectedConceptId);
  });

  function togglePhysics() {
    physicsOn = !physicsOn;
    network?.setOptions({ physics: { enabled: physicsOn } });
  }
  function zoom(factor) {
    if (!network) return;
    const scale = network.getScale() * factor;
    network.moveTo({ scale, animation: { duration: 150 } });
  }
  function fit() {
    network?.fit({ animation: { duration: 300, easingFunction: 'easeOutQuad' } });
  }
</script>

<div class="canvas-shell">
  <div class="canvas-toolbar">
    <div class="canvas-key">
      <span><i class="hierarchy"></i> Contains</span>
      <span><i class="prerequisite"></i> Prerequisite</span>
    </div>
    <div class="toolbar-actions">
      <button type="button" class="physics-toggle" class:active={physicsOn} onclick={togglePhysics}>
        <span class="dot"></span> Physics
      </button>
      <div class="zoom-controls">
        <button type="button" onclick={() => zoom(0.8)} aria-label="Zoom out">−</button>
        <button type="button" onclick={fit} aria-label="Fit graph" title="Fit to screen">⤢</button>
        <button type="button" onclick={() => zoom(1.25)} aria-label="Zoom in">+</button>
      </div>
    </div>
  </div>

  {#if !graph?.nodes?.length}
    <div class="empty-canvas"><strong>No active concepts yet</strong><span>Generate and validate a course concept graph to see its hierarchy here.</span></div>
  {:else}
    <div class="canvas-viewport" bind:this={canvasEl}></div>
  {/if}
</div>

<style>
  .canvas-shell { background: #0a0e14; display: flex; flex: 1; flex-direction: column; min-height: 520px; overflow: hidden; position: relative; }
  .canvas-toolbar { align-items: center; background: rgba(15,18,26,.9); border-bottom: 1px solid rgba(255,255,255,.08); display: flex; justify-content: space-between; padding: 10px 14px; position: relative; z-index: 2; }
  .canvas-key { color: #9ca3af; display: flex; font-size: 10px; gap: 14px; }
  .canvas-key span { align-items: center; display: flex; gap: 5px; }
  .canvas-key i { border-radius: 50%; display: inline-block; height: 7px; width: 7px; }
  .canvas-key .hierarchy { background: #60a5fa; }
  .canvas-key .prerequisite { background: #c084fc; }
  .toolbar-actions { align-items: center; display: flex; gap: 10px; }
  .physics-toggle { align-items: center; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); border-radius: 999px; color: #9ca3af; cursor: pointer; display: flex; font-size: 10px; font-weight: 600; gap: 6px; letter-spacing: .3px; padding: 5px 10px; text-transform: uppercase; transition: all .15s; }
  .physics-toggle .dot { background: #4b5563; border-radius: 50%; height: 6px; width: 6px; transition: all .15s; }
  .physics-toggle.active { background: rgba(96,165,250,.14); border-color: rgba(96,165,250,.4); color: #93c5fd; }
  .physics-toggle.active .dot { background: #60a5fa; box-shadow: 0 0 6px #60a5fa; }
  .zoom-controls { align-items: center; color: #9ca3af; display: flex; font-family: var(--font-mono, monospace); font-size: 13px; gap: 6px; }
  .zoom-controls button { background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); border-radius: 5px; color: #e5e7eb; cursor: pointer; height: 24px; line-height: 1; width: 24px; }
  .zoom-controls button:hover { background: rgba(255,255,255,.12); }
  /* vis-network's injected .vis-network div is height:100% of this element, but a
     percentage height never resolves against a flex-grown ancestor that has no
     explicit `height` (only `flex: 1`) - a well-known CSS gotcha. Absolutely
     positioning it against this `position: relative` box sidesteps that entirely,
     since absolute sizing resolves against the padding box directly instead of
     going through percentage-height resolution. */
  .canvas-viewport { flex: 1; min-height: 460px; width: 100%; position: relative; }
  .canvas-viewport :global(.vis-network) { position: absolute !important; inset: 0; }
  .canvas-viewport :global(canvas) { outline: none; }
  .empty-canvas { align-items: center; color: #6b7280; display: flex; flex: 1; flex-direction: column; font-size: 12px; gap: 7px; justify-content: center; text-align: center; }
  .empty-canvas strong { color: #e5e7eb; font-size: 14px; }
</style>
