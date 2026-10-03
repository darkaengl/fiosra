<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import {
    forceSimulation,
    forceManyBody,
    forceLink,
    forceCenter,
    forceCollide
  } from 'd3-force';
  import { PALETTES, getNodeColor, getNodeRadius, neighbourhoodIds } from './graph/graphCanvasTheme';
  import GraphSettingsHud from './graph/GraphSettingsHud.svelte';
  import GraphNodeTooltip from './graph/GraphNodeTooltip.svelte';
  import { computeSugiyamaRankLayout } from './graph/masterySugiyamaLayout';
  import { renderMasteryCanvas } from './graph/masteryCanvasRenderer';

  let {
    graph = { nodes: [], edges: [], probes: [] },
    selectedConceptId = '',
    onSelect = () => {},
    theme = $bindable<'light' | 'dark'>('light'),
    viewMode = 'standard', // 'standard' | 'cohort' | 'student'
    activeStudent = null, // StudentConceptState object
    bottlenecksOnly = false,
    bottlenecks = [],
    showHud = true
  } = $props<{
    graph?: any;
    selectedConceptId?: string;
    onSelect?: (id: string, node?: any) => void;
    theme?: 'light' | 'dark';
    viewMode?: string;
    activeStudent?: any;
    bottlenecksOnly?: boolean;
    bottlenecks?: any[];
    showHud?: boolean;
  }>();

  let canvasRef = $state(null);
  let containerRef = $state(null);

  // Viewport Pan & Zoom
  let scale = $state(1.0);
  let panX = $state(0);
  let panY = $state(0);
  let isPanning = $state(false);
  let startPan = { x: 0, y: 0 };
  let startClient = { x: 0, y: 0 };

  // Filter toggles
  let showKCs = $state(true);
  let showMisconceptions = $state(true);
  let showProbes = $state(true);
  let showModules = $state(true);
  // Focus mode: collapse the canvas to the selected node's neighbourhood.
  // On a course-sized graph a single concept is invisible among thousands, so
  // this is how one concept and its traps can actually be shown.
  let focusMode = $state(false);
  let focusDepth = $state(1);
  let searchQuery = $state('');
  let hudOpen = $state(false);
  let activeTab = $state<'filters' | 'display' | 'forces'>('filters');

  // Display toggles & sliders (matching Obsidian Graph settings)
  let nodeSizeMultiplier = $state(1.1);
  let linkThickness = $state(1.0);
  let textSize = $state(10);
  let showArrows = $state(true);
  let showAllLabels = $state(true);
  let layoutMode = $state('rank'); // 'rank' (Sugiyama layout) | 'force'
  let columnHeaders = $state([]);

  // Physics params
  let repulsion = $state(-260);
  let linkDistance = $state(80);
  let centerGravity = $state(0.08);

  // Hover & selection state
  let hoveredNode = $state(null);
  let mousePos = $state({ x: 0, y: 0 });
  let draggedNode = null;

  // Simulation & animation refs
  let simulation = null;
  let animFrameId = null;
  let isDestroyed = false;
  let simNodes = [];
  let simLinks = [];
  let nodeCount = $state(0);
  let linkCount = $state(0);



  function filterNode(node) {
    const type = node.raw?.concept_type || node.concept_type || node.raw?.level || node.level;
    if (type === 'module' && !showModules) return false;
    // Always hide micro Socratic probe nodes from the main canvas; they belong in the Inspector
    if (type === 'socratic_probe') return false;

    // Filter misconceptions: ONLY show if actually triggered by students
    if (type === 'misconception') {
      if (!showMisconceptions) return false;
      const cId = node.id || node.concept_id;

      if (viewMode === 'cohort') {
        const triggers = node.active_trigger_count || node.raw?.active_trigger_count || node.raw?.struggling_count || 0;
        if (triggers === 0) return false;
      } else if (viewMode === 'student' && activeStudent) {
        const isTrapped = activeStudent.trapped_concepts?.includes(cId) || activeStudent.concept_states?.[cId] === 'trapped';
        if (!isTrapped) return false;
      }
    }

    if (type !== 'module' && type !== 'misconception' && type !== 'socratic_probe' && !showKCs) return false;
    return true;
  }


  function getNeighborIds(nodeId) {
    const set = new Set([nodeId]);
    for (const link of simLinks) {
      const sId = typeof link.source === 'object' ? link.source.id : link.source;
      const tId = typeof link.target === 'object' ? link.target.id : link.target;
      if (sId === nodeId) set.add(tId);
      if (tId === nodeId) set.add(sId);
    }
    return set;
  }

  function toggleTheme(newTheme) {
    theme = newTheme;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('obsidian_graph_theme', newTheme);
    }
  }

  function rebuildSimulation() {
    if (!canvasRef || !containerRef) return;
    const width = containerRef.clientWidth || 900;
    const height = containerRef.clientHeight || 650;

    const rawNodes = graph?.nodes || [];
    const rawEdges = graph?.edges || [];

    // Filter nodes according to toggle buttons
    let activeNodes = rawNodes.filter(filterNode);

    // If focusing, keep only the selected node's neighbourhood
    if (focusMode && selectedConceptId) {
      const keep = neighbourhoodIds(selectedConceptId, rawEdges, focusDepth);
      const focused = activeNodes.filter(n => keep.has(n.concept_id));
      if (focused.length) activeNodes = focused;
    }
    const activeNodeIds = new Set(activeNodes.map(n => n.concept_id));

    // Filter edges whose endpoints are both visible
    const activeEdges = rawEdges.filter(e => activeNodeIds.has(e.source) && activeNodeIds.has(e.target));

    // Compute actual node degrees from active edges
    const degreeMap = new Map();
    for (const e of activeEdges) {
      degreeMap.set(e.source, (degreeMap.get(e.source) || 0) + 1);
      degreeMap.set(e.target, (degreeMap.get(e.target) || 0) + 1);
    }

    if (layoutMode === 'rank') {
      const res = computeSugiyamaRankLayout(
        activeNodes,
        activeEdges,
        degreeMap,
        theme,
        viewMode,
        activeStudent,
        nodeSizeMultiplier
      );
      columnHeaders = res.columnHeaders;
      simNodes = res.simNodes;
      simLinks = res.simLinks;
      nodeCount = simNodes.length;
      linkCount = simLinks.length;

      if (simulation) {
        simulation.stop();
        simulation = null;
      }

      recenterGraph();
      requestRender();
      return;
    }

    // Fallback: Force simulation
    simNodes = activeNodes.map((node, idx) => {
      const degree = degreeMap.get(node.concept_id) || node.degree || 0;
      const type = node.raw?.concept_type || node.concept_type || node.raw?.level || node.level;
      const radius = getNodeRadius(degree, type, 2, nodeSizeMultiplier);
      const angle = (idx / Math.max(1, activeNodes.length)) * 2 * Math.PI;
      const radiusInit = 140 + (idx % 4) * 40;
      const initX = width / 2 + Math.cos(angle) * radiusInit;
      const initY = height / 2 + Math.sin(angle) * radiusInit;

      return {
        id: node.concept_id,
        raw: node,
        degree,
        radius,
        rank: 2,
        color: getNodeColor({ ...node, degree }, theme, viewMode, activeStudent),
        x: initX,
        y: initY,
        vx: 0,
        vy: 0
      };
    });

    simLinks = activeEdges.map(edge => ({
      source: edge.source,
      target: edge.target,
      relation: edge.relation
    }));

    nodeCount = simNodes.length;
    linkCount = simLinks.length;

    if (simulation) {
      simulation.stop();
    }

    simulation = forceSimulation(simNodes)
      .force('charge', forceManyBody().strength(repulsion))
      .force('link', forceLink(simLinks).id(d => d.id).distance(linkDistance))
      .force('center', forceCenter(width / 2, height / 2).strength(centerGravity))
      .force('collision', forceCollide().radius(d => d.radius + 8));

    simulation.alpha(0.8);
    for (let i = 0; i < 220; ++i) {
      simulation.tick();
    }
    simulation.stop();

    for (const node of simNodes) {
      node.fx = node.x;
      node.fy = node.y;
      node.vx = 0;
      node.vy = 0;
    }

    recenterGraph();
    requestRender();
  }

  function render() {
    if (isDestroyed || !canvasRef) return;
    const ctx = canvasRef.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const palette = PALETTES[theme] || PALETTES.light;

    renderMasteryCanvas({
      ctx,
      canvasWidth: canvasRef.width,
      canvasHeight: canvasRef.height,
      dpr,
      palette,
      panX,
      panY,
      scale,
      layoutMode,
      columnHeaders,
      simNodes,
      simLinks,
      theme,
      viewMode,
      activeStudent,
      hoveredNode,
      selectedConceptId,
      showArrows,
      linkThickness,
      searchQuery,
      bottlenecksOnly,
      bottlenecks,
      getNeighborIds,
    });
  }

  let renderQueued = false;
  function requestRender() {
    if (renderQueued || isDestroyed || !canvasRef) return;
    renderQueued = true;
    requestAnimationFrame(() => {
      renderQueued = false;
      render();
    });
  }

  function screenToWorld(clientX, clientY) {
    if (!canvasRef) return { x: 0, y: 0 };
    const rect = canvasRef.getBoundingClientRect();
    const x = (clientX - rect.left - panX) / scale;
    const y = (clientY - rect.top - panY) / scale;
    return { x, y };
  }

  function findNodeAt(worldX, worldY) {
    for (let i = simNodes.length - 1; i >= 0; i--) {
      const node = simNodes[i];
      const dx = worldX - node.x;
      const dy = worldY - node.y;
      if (dx * dx + dy * dy <= (node.radius + 6) * (node.radius + 6)) {
        return node;
      }
    }
    return null;
  }

  function handlePointerDown(e) {
    startClient = { x: e.clientX, y: e.clientY };
    const world = screenToWorld(e.clientX, e.clientY);
    const hit = findNodeAt(world.x, world.y);

    if (hit) {
      draggedNode = hit;
      draggedNode.fx = hit.x;
      draggedNode.fy = hit.y;
    } else {
      isPanning = true;
      startPan = { x: e.clientX - panX, y: e.clientY - panY };
    }
  }

  function handlePointerMove(e) {
    mousePos = { x: e.clientX, y: e.clientY };
    const world = screenToWorld(e.clientX, e.clientY);

    if (draggedNode) {
      draggedNode.x = world.x;
      draggedNode.y = world.y;
      draggedNode.fx = world.x;
      draggedNode.fy = world.y;
      requestRender();
    } else if (isPanning) {
      panX = e.clientX - startPan.x;
      panY = e.clientY - startPan.y;
      requestRender();
    } else {
      const prevHover = hoveredNode;
      hoveredNode = findNodeAt(world.x, world.y);
      if (prevHover !== hoveredNode) {
        requestRender();
      }
    }
  }

  function handlePointerUp(e) {
    const dist = Math.hypot(e.clientX - startClient.x, e.clientY - startClient.y);
    if (draggedNode) {
      if (dist < 5) {
        onSelect(draggedNode.id);
      }
      draggedNode.fx = draggedNode.x;
      draggedNode.fy = draggedNode.y;
      draggedNode = null;
      requestRender();
    } else if (isPanning) {
      // If user clicked the canvas background without panning, dismiss open selection
      if (dist < 5 && selectedConceptId) {
        onSelect('');
      }
      requestRender();
    }
    isPanning = false;
  }

  function handleWheel(e) {
    e.preventDefault();
    if (!canvasRef) return;
    const rect = canvasRef.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const newScale = Math.max(0.2, Math.min(3.8, scale * zoomFactor));

    // Zoom towards mouse pointer
    panX = mouseX - (mouseX - panX) * (newScale / scale);
    panY = mouseY - (mouseY - panY) * (newScale / scale);
    scale = newScale;
    requestRender();
  }

  function recenterGraph() {
    if (!containerRef || simNodes.length === 0) {
      scale = 1.0;
      panX = 0;
      panY = 0;
      requestRender();
      return;
    }
    const W = containerRef.clientWidth || 900;
    const H = containerRef.clientHeight || 650;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of simNodes) {
      if (n.x == null || n.y == null) continue;
      const r = n.radius + 200; // account for right-aligned text label width
      minX = Math.min(minX, n.x - 30);
      maxX = Math.max(maxX, n.x + r);
      minY = Math.min(minY, n.y - 50);
      maxY = Math.max(maxY, n.y + 50);
    }

    if (!isFinite(minX)) {
      scale = 1.0;
      panX = 0;
      panY = 0;
      requestRender();
      return;
    }

    const bw = Math.max(100, maxX - minX);
    const bh = Math.max(100, maxY - minY);
    const newScale = Math.max(0.38, Math.min(1.2, Math.min((W - 80) / bw, (H - 120) / bh)));
    scale = newScale;
    panX = Math.max(50 - minX * newScale, (W - bw * newScale) / 2 - minX * newScale);
    panY = (H - bh * newScale) / 2 - minY * newScale + 20;
    requestRender();
  }

  function updatePhysics() {
    if (!simulation) return;
    simulation.force('charge', forceManyBody().strength(repulsion));
    simulation.force('link', forceLink(simLinks).id(d => d.id).distance(linkDistance));
    simulation.force('center', forceCenter(containerRef.clientWidth / 2, containerRef.clientHeight / 2).strength(centerGravity));
    simulation.force('collision', forceCollide().radius(d => d.radius + 6));
    simulation.alpha(0.35).restart();
  }

  // Update node colors/radii when theme, viewMode, or student selection changes
  $effect(() => {
    const currentTheme = theme;
    const currentMult = nodeSizeMultiplier;
    viewMode;
    activeStudent;
    bottlenecksOnly;
    for (const node of simNodes) {
      node.color = getNodeColor(node, currentTheme, viewMode, activeStudent);
      node.radius = getNodeRadius(node.degree, node.raw?.concept_type || node.raw?.level, node.rank ?? 2, currentMult);
    }
    requestRender();
  });

  $effect(() => {
    // Re-run simulation when graph structure or filter toggles change
    graph;
    showKCs;
    showMisconceptions;
    showProbes;
    showModules;
    focusMode;
    focusDepth;
    selectedConceptId;
    rebuildSimulation();
  });

  $effect(() => {
    // Update physics forces when sliders move
    repulsion;
    linkDistance;
    centerGravity;
    updatePhysics();
  });

  onMount(() => {
    const updateSize = () => {
      if (!canvasRef || !containerRef) return;
      const dpr = window.devicePixelRatio || 1;
      const w = containerRef.clientWidth || 900;
      const h = containerRef.clientHeight || 650;
      canvasRef.width = w * dpr;
      canvasRef.height = h * dpr;
      recenterGraph();
      rebuildSimulation();
    };

    window.addEventListener('resize', updateSize);
    let resizeObserver = null;
    if (typeof ResizeObserver !== 'undefined' && containerRef) {
      resizeObserver = new ResizeObserver(() => {
        updateSize();
      });
      resizeObserver.observe(containerRef);
    }
    updateSize();
    requestRender();

    return () => {
      isDestroyed = true;
      window.removeEventListener('resize', updateSize);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      if (animFrameId) {
        cancelAnimationFrame(animFrameId);
        animFrameId = null;
      }
      if (simulation) {
        simulation.stop();
        simulation = null;
      }
    };
  });

  onDestroy(() => {
    isDestroyed = true;
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    if (simulation) {
      simulation.stop();
      simulation = null;
    }
  });
</script>

<div class="obsidian-graph-shell" class:light-mode={theme === 'light'} class:dark-mode={theme === 'dark'} bind:this={containerRef}>
  <canvas
    bind:this={canvasRef}
    class="obsidian-canvas"
    onpointerdown={handlePointerDown}
    onpointermove={handlePointerMove}
    onpointerup={handlePointerUp}
    onwheel={handleWheel}
  ></canvas>

  <!-- Obsidian Graph Settings HUD Panel -->
  {#if showHud}
    <GraphSettingsHud
      bind:hudOpen
      bind:theme
      bind:activeTab
      bind:searchQuery
      bind:focusMode
      bind:focusDepth
      {selectedConceptId}
      bind:showKCs
      bind:showMisconceptions
      bind:showProbes
      bind:showModules
      bind:nodeSizeMultiplier
      bind:linkThickness
      bind:textSize
      bind:showArrows
      bind:showAllLabels
      bind:centerGravity
      bind:repulsion
      bind:linkDistance
      onRecenter={recenterGraph}
      onReheat={() => { if (simulation) simulation.alpha(0.6).restart(); }}
    />
  {/if}

  <!-- Zoom & Count badge in bottom left -->
  <div class="zoom-badge">
    <button type="button" class="btn-canvas-action" onclick={recenterGraph} title="Recenter and fit graph">
      ⟲ Recenter
    </button>
    <span class="badge-sep">·</span>
    <span>{Math.round(scale * 100)}%</span>
    <span class="badge-sep">·</span>
    <span>{nodeCount} Nodes · {linkCount} Links</span>
  </div>

  <!-- Interactive Node Hover Tooltip -->
  <GraphNodeTooltip
    {hoveredNode}
    {mousePos}
    {viewMode}
    {activeStudent}
  />
</div>

<style>
  .obsidian-graph-shell {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 650px;
    overflow: hidden;
    user-select: none;
    transition: background-color 0.25s ease;
  }

  .obsidian-graph-shell.light-mode {
    background-color: #ffffff;
    color: #1e293b;
  }

  .obsidian-graph-shell.dark-mode {
    background-color: #161616;
    color: #f1f5f9;
  }

  .obsidian-canvas {
    display: block;
    width: 100%;
    height: 100%;
    cursor: grab;
  }
  .obsidian-canvas:active {
    cursor: grabbing;
  }

  .zoom-badge {
    position: absolute;
    bottom: 14px;
    left: 14px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, monospace;
    font-size: 10px;
    padding: 4px 10px;
    pointer-events: auto;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.2s ease;
    z-index: 20;
  }
  .light-mode .zoom-badge {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(0, 0, 0, 0.12);
    color: #475569;
  }
  .dark-mode .zoom-badge {
    background: rgba(24, 24, 27, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #94a3b8;
  }

  .btn-canvas-action {
    background: transparent;
    border: none;
    font-size: 10px;
    font-weight: 600;
    color: #2563eb;
    cursor: pointer;
    padding: 1px 4px;
    border-radius: 3px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    transition: background-color 0.15s ease;
  }
  .dark-mode .btn-canvas-action {
    color: #60a5fa;
  }
  .btn-canvas-action:hover {
    background: rgba(37, 99, 235, 0.1);
  }
  .badge-sep {
    color: rgba(148, 163, 184, 0.5);
  }
</style>
