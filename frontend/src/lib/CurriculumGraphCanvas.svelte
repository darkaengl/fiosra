<script>
  import { onMount, onDestroy } from 'svelte';
  import {
    forceSimulation,
    forceManyBody,
    forceLink,
    forceCenter,
    forceCollide
  } from 'd3-force';
  import { PALETTES, neighbourhoodIds } from './graph/graphCanvasTheme';
  import GraphSettingsHud from './graph/GraphSettingsHud.svelte';
  import GraphNodeTooltip from './graph/GraphNodeTooltip.svelte';

  let {
    graph = { nodes: [], edges: [], probes: [] },
    selectedConceptId = '',
    onSelect = () => {},
    theme = $bindable('light')
  } = $props();

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
  let hudOpen = $state(true);
  let activeTab = $state('filters'); // 'filters' | 'display' | 'forces'

  // Display toggles & sliders (matching Obsidian Graph settings)
  let nodeSizeMultiplier = $state(1.1);
  let linkThickness = $state(1.0);
  let textSize = $state(10);
  let showArrows = $state(true);
  let showAllLabels = $state(false);

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



  function getNodeColor(node, currentTheme) {
    const palette = PALETTES[currentTheme] || PALETTES.light;
    const type = node.concept_type || node.level;
    if (type === 'misconception') return palette.misconception;
    if (type === 'socratic_probe') return palette.socratic_probe;
    if (type === 'module' || type === 'course_theme') return palette.module;
    
    // Scale tone based on connectivity (degree)
    const deg = node.degree || 0;
    if (deg >= 5) return palette.hub_kc;
    if (deg >= 2) return palette.pedagogical_kc;
    return palette.leaf;
  }

  function getNodeRadius(degree, type) {
    const deg = Math.max(0, degree);
    let base = 5.5;
    if (type === 'module' || type === 'course_theme') {
      base = 11;
    } else if (type === 'misconception') {
      base = 7.5;
    } else if (type === 'socratic_probe') {
      base = 6;
    } else {
      base = 6;
    }
    // Organic growth based on degree
    const growth = Math.min(18, Math.sqrt(deg) * 4.2);
    return (base + growth) * nodeSizeMultiplier;
  }

  function filterNode(node) {
    const type = node.concept_type || node.level;
    if (type === 'module' && !showModules) return false;
    if (type === 'misconception' && !showMisconceptions) return false;
    if (type === 'socratic_probe' && !showProbes) return false;
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

    // Then, if focusing, keep only the selected node's neighbourhood. Focus
    // with nothing selected would blank the canvas, so it is a no-op until a
    // node is clicked.
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

    // Reuse existing positions if node was already in simulation
    const existingPos = new Map(simNodes.map(n => [n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy }]));

    simNodes = activeNodes.map(node => {
      const prev = existingPos.get(node.concept_id);
      const degree = degreeMap.get(node.concept_id) || node.degree || 0;
      const type = node.concept_type || node.level;
      const radius = getNodeRadius(degree, type);
      return {
        id: node.concept_id,
        raw: node,
        degree,
        radius,
        color: getNodeColor({ ...node, degree }, theme),
        x: prev ? prev.x : width / 2 + (Math.random() - 0.5) * 240,
        y: prev ? prev.y : height / 2 + (Math.random() - 0.5) * 240,
        vx: prev ? prev.vx : 0,
        vy: prev ? prev.vy : 0
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
      .force('collision', forceCollide().radius(d => d.radius + 6))
      .alpha(0.6)
      .restart();
  }

  function drawArrowhead(ctx, sourceX, sourceY, targetX, targetY, targetRadius, color, alpha) {
    const dx = targetX - sourceX;
    const dy = targetY - sourceY;
    const dist = Math.hypot(dx, dy);
    const arrowLen = Math.max(5, Math.min(8, 6.5 * Math.min(1.2, scale)));
    const arrowWidth = Math.max(4, Math.min(7, 5 * Math.min(1.2, scale)));

    if (dist <= targetRadius + arrowLen) return;

    const ux = dx / dist;
    const uy = dy / dist;

    // The tip of the arrowhead sits right on the outer boundary of the target circle
    const tipX = targetX - ux * (targetRadius + 1);
    const tipY = targetY - uy * (targetRadius + 1);

    const baseX = tipX - ux * arrowLen;
    const baseY = tipY - uy * arrowLen;

    const nx = -uy;
    const ny = ux;

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(baseX + nx * (arrowWidth / 2), baseY + ny * (arrowWidth / 2));
    ctx.lineTo(baseX - nx * (arrowWidth / 2), baseY - ny * (arrowWidth / 2));
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function render() {
    if (isDestroyed || !canvasRef) return;
    const ctx = canvasRef.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const pw = canvasRef.width;
    const ph = canvasRef.height;
    const width = pw / dpr;
    const height = ph / dpr;

    const palette = PALETTES[theme] || PALETTES.light;

    // Clear canvas
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, pw, ph);

    ctx.save();
    ctx.scale(dpr, dpr);

    // 1. Clean Obsidian Canvas Background (pure white in light mode, pure dark in dark mode)
    ctx.fillStyle = palette.bg;
    ctx.fillRect(0, 0, width, height);

    // Subtle faint micro-grid dots (Obsidian canvas style)
    ctx.fillStyle = palette.gridDot;
    const gridSize = 40 * scale;
    const gridOffX = ((panX % gridSize) + gridSize) % gridSize;
    const gridOffY = ((panY % gridSize) + gridSize) % gridSize;
    for (let gx = gridOffX; gx < width; gx += gridSize) {
      for (let gy = gridOffY; gy < height; gy += gridSize) {
        ctx.fillRect(gx, gy, 1.2, 1.2);
      }
    }

    // Apply viewport transform (pan & zoom)
    ctx.translate(panX, panY);
    ctx.scale(scale, scale);

    // Neighborhood spotlight set
    const spotlightIds = hoveredNode ? getNeighborIds(hoveredNode.id) : null;
    const searchLower = searchQuery.trim().toLowerCase();

    // 2. Draw Links & Arrowheads
    for (const link of simLinks) {
      const source = typeof link.source === 'object' ? link.source : simNodes.find(n => n.id === link.source);
      const target = typeof link.target === 'object' ? link.target : simNodes.find(n => n.id === link.target);
      if (!source || !target) continue;

      const isConnectedToHover = hoveredNode && (source.id === hoveredNode.id || target.id === hoveredNode.id);
      const isConnectedToSelected = selectedConceptId && (source.id === selectedConceptId || target.id === selectedConceptId);

      let alpha = 0.55;
      let strokeColor = palette.link;
      let width = linkThickness;

      if (hoveredNode) {
        if (isConnectedToHover) {
          alpha = 0.95;
          strokeColor = palette.linkHighlight;
          width = linkThickness * 1.8;
        } else {
          alpha = 0.05;
          strokeColor = palette.linkFade;
        }
      } else if (isConnectedToSelected) {
        alpha = 0.92;
        strokeColor = palette.linkHighlight;
        width = linkThickness * 1.6;
      }

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);

      // Stop line at arrowhead base if arrows are enabled
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const dist = Math.hypot(dx, dy);
      const targetR = target.radius;
      const arrowLen = Math.max(5, Math.min(8, 6.5 * Math.min(1.2, scale)));

      let endX = target.x;
      let endY = target.y;
      if (showArrows && dist > targetR + arrowLen) {
        const ux = dx / dist;
        const uy = dy / dist;
        endX = target.x - ux * (targetR + arrowLen);
        endY = target.y - uy * (targetR + arrowLen);
      }

      ctx.lineTo(endX, endY);
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = width;
      ctx.stroke();
      ctx.restore();

      if (showArrows) {
        drawArrowhead(ctx, source.x, source.y, target.x, target.y, targetR, strokeColor, alpha);
      }
    }

    // 3. Draw Nodes (Flat Matte Circles matching Obsidian Graph screenshot)
    for (const node of simNodes) {
      const isSelected = node.id === selectedConceptId;
      const isHovered = hoveredNode && node.id === hoveredNode.id;
      const isNeighbor = spotlightIds ? spotlightIds.has(node.id) : false;
      const matchesSearch = searchLower && (node.raw.label?.toLowerCase().includes(searchLower) || node.raw.definition?.toLowerCase().includes(searchLower));

      let alpha = 1.0;
      if (hoveredNode) {
        alpha = isHovered || isNeighbor ? 1.0 : 0.12;
      } else if (searchLower && !matchesSearch) {
        alpha = 0.15;
      }

      ctx.save();
      ctx.globalAlpha = alpha;

      // Solid flat circular disc (Obsidian hallmark)
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.fill();

      // Selection indicator ring
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = palette.selectRing;
        ctx.lineWidth = 2.2;
        ctx.stroke();
      }

      // Hover spotlight ring
      if (isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 3, 0, Math.PI * 2);
        ctx.strokeStyle = palette.hoverRing;
        ctx.lineWidth = 1.8;
        ctx.stroke();
      }

      // Search match highlight ring
      if (matchesSearch) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5, 0, Math.PI * 2);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 4. Floating Typography / Labels (Obsidian style: clean floating text without boxes)
      const isHub = (node.degree || 0) >= 3 || node.raw.concept_type === 'module';
      const showLabel = showAllLabels || isSelected || isHovered || isNeighbor || matchesSearch || (isHub && scale > 0.55) || (scale > 1.25);

      if (showLabel) {
        const currentFontSize = Math.max(8, Math.min(16, textSize * (0.88 + 0.12 / Math.max(0.6, scale))));
        ctx.font = `${isHovered || isSelected || isHub ? '600' : '400'} ${currentFontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif`;

        const rawText = node.raw.label || node.id;
        const maxChars = Math.floor(34 / Math.max(0.6, scale));
        const displayText = rawText.length > maxChars ? rawText.slice(0, maxChars) + '…' : rawText;

        const textY = node.y + node.radius + 12;

        ctx.textAlign = 'center';
        ctx.textBaseline = 'alphabetic';

        // Subtle contrast halo to ensure legibility when intersecting link lines
        ctx.strokeStyle = palette.textHalo;
        ctx.lineWidth = 3.2;
        ctx.lineJoin = 'round';
        ctx.strokeText(displayText, node.x, textY);

        // Crisp text fill
        ctx.fillStyle = isHovered || isSelected ? palette.textHighlight : (isNeighbor ? palette.textHighlight : palette.text);
        ctx.fillText(displayText, node.x, textY);
      }

      ctx.restore();
    }

    ctx.restore();

    animFrameId = requestAnimationFrame(render);
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
      if (simulation) simulation.alphaTarget(0.25).restart();
    } else {
      isPanning = true;
      startPan = { x: e.clientX - panX, y: e.clientY - panY };
    }
  }

  function handlePointerMove(e) {
    mousePos = { x: e.clientX, y: e.clientY };
    const world = screenToWorld(e.clientX, e.clientY);

    if (draggedNode) {
      draggedNode.fx = world.x;
      draggedNode.fy = world.y;
    } else if (isPanning) {
      panX = e.clientX - startPan.x;
      panY = e.clientY - startPan.y;
    } else {
      hoveredNode = findNodeAt(world.x, world.y);
    }
  }

  function handlePointerUp(e) {
    const dist = Math.hypot(e.clientX - startClient.x, e.clientY - startClient.y);
    if (draggedNode) {
      if (dist < 5) {
        onSelect(draggedNode.id);
      }
      draggedNode.fx = null;
      draggedNode.fy = null;
      draggedNode = null;
      if (simulation) simulation.alphaTarget(0);
    } else if (isPanning) {
      // If user clicked the canvas background without panning, dismiss open selection
      if (dist < 5 && selectedConceptId) {
        onSelect('');
      }
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
  }

  function recenterGraph() {
    if (!containerRef || simNodes.length === 0) {
      scale = 1.0;
      panX = 0;
      panY = 0;
      return;
    }
    const W = containerRef.clientWidth;
    const H = containerRef.clientHeight;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of simNodes) {
      if (n.x == null || n.y == null) continue;
      const r = n.radius + 28;
      minX = Math.min(minX, n.x - r);
      maxX = Math.max(maxX, n.x + r);
      minY = Math.min(minY, n.y - r);
      maxY = Math.max(maxY, n.y + r);
    }

    if (!isFinite(minX)) {
      scale = 1.0;
      panX = 0;
      panY = 0;
      if (simulation) simulation.alpha(0.5).restart();
      return;
    }

    const bw = Math.max(100, maxX - minX);
    const bh = Math.max(100, maxY - minY);
    const newScale = Math.max(0.25, Math.min(1.8, Math.min(W / bw, H / bh) * 0.88));
    scale = newScale;
    panX = (W - bw * newScale) / 2 - minX * newScale;
    panY = (H - bh * newScale) / 2 - minY * newScale;

    if (simulation) {
      simulation.alpha(0.5).restart();
    }
  }

  function updatePhysics() {
    if (!simulation) return;
    simulation.force('charge', forceManyBody().strength(repulsion));
    simulation.force('link', forceLink(simLinks).id(d => d.id).distance(linkDistance));
    simulation.force('center', forceCenter(containerRef.clientWidth / 2, containerRef.clientHeight / 2).strength(centerGravity));
    simulation.force('collision', forceCollide().radius(d => d.radius + 6));
    simulation.alpha(0.35).restart();
  }

  // Update node colors/radii when theme or nodeSizeMultiplier changes
  $effect(() => {
    const currentTheme = theme;
    const currentMult = nodeSizeMultiplier;
    for (const node of simNodes) {
      node.color = getNodeColor(node, currentTheme);
      node.radius = getNodeRadius(node.degree, node.raw.concept_type || node.raw.level);
    }
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
    updateSize();
    animFrameId = requestAnimationFrame(render);

    return () => {
      isDestroyed = true;
      window.removeEventListener('resize', updateSize);
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

  <!-- Zoom & Count badge in bottom left -->
  <div class="zoom-badge">
    <span>Zoom: {Math.round(scale * 100)}%</span>
    <span>{nodeCount} Nodes · {linkCount} Links</span>
  </div>

  <!-- Interactive Node Hover Tooltip -->
  <GraphNodeTooltip {hoveredNode} {mousePos} />
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
    border-radius: 4px;
    display: flex;
    gap: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", monospace;
    font-size: 10px;
    padding: 4px 8px;
    pointer-events: none;
    transition: all 0.2s ease;
  }
  .light-mode .zoom-badge {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
    color: #64748b;
  }
  .dark-mode .zoom-badge {
    background: rgba(24, 24, 27, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8;
  }

</style>
