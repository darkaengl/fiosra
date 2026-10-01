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
      // Deterministic Hierarchical Rank (Sugiyama) Layout
      const rankMap = new Map();
      for (const n of activeNodes) {
        let r = n.rank ?? n.raw?.rank;
        if (r == null) {
          const type = n.concept_type || n.level || n.raw?.concept_type || n.raw?.level;
          if (type === 'strand' || type === 'course_theme' || type === 'module') r = 0;
          else if (type === 'topic' || type === 'domain') r = 1;
          else if (type === 'atomic_concept' || type === 'subtopic' || type === 'leaf') r = 2;
          else if (type === 'misconception') r = 3;
          else r = 2;
        }
        rankMap.set(n.concept_id, r);
      }

      // Build childToParent map
      const childToParent = new Map();
      for (const e of activeEdges) {
        if (e.relation === 'CONTAINS' || e.relation === 'ASSOCIATED_WITH') {
          childToParent.set(e.target, e.source);
        }
      }
      for (const n of activeNodes) {
        const pid = n.parent_id || n.raw?.parent_id;
        if (pid && !childToParent.has(n.concept_id)) {
          childToParent.set(n.concept_id, pid);
        }
      }

      const rank0 = activeNodes.filter(n => rankMap.get(n.concept_id) === 0);
      const rank1 = activeNodes.filter(n => rankMap.get(n.concept_id) === 1);
      const rank2 = activeNodes.filter(n => rankMap.get(n.concept_id) === 2);
      const rank3 = activeNodes.filter(n => rankMap.get(n.concept_id) === 3);

      const colWidth = 350;
      const startX = 140;

      columnHeaders = [
        { rank: 0, label: 'UNIT / STRAND', x: startX },
        { rank: 1, label: 'CORE TOPICS', x: startX + colWidth },
        { rank: 2, label: 'KNOWLEDGE COMPONENTS', x: startX + 2 * colWidth },
        { rank: 3, label: 'COGNITIVE TRAPS', x: startX + 3 * colWidth },
      ];

      // Vertical tree-based placement
      const nodeYMap = new Map();
      let currentY = 130;
      const rowHeightKC = 48;
      const rowHeightTopic = 64;
      const rowHeightStrand = 94;

      const roots = rank0.length > 0 ? rank0 : (rank1.length > 0 ? rank1 : activeNodes);

      for (const root of roots) {
        const rootId = root.concept_id;
        const rootTopics = rank1.filter(t => childToParent.get(t.concept_id) === rootId || !childToParent.has(t.concept_id));
        const topicsToProcess = rootTopics.length > 0 ? rootTopics : (rankMap.get(rootId) === 1 ? [root] : []);

        const rootStartY = currentY;

        if (topicsToProcess.length === 0) {
          nodeYMap.set(rootId, currentY);
          currentY += rowHeightStrand;
        } else {
          for (const topic of topicsToProcess) {
            const topicId = topic.concept_id;
            const topicKCs = rank2.filter(k => childToParent.get(k.concept_id) === topicId);
            const topicStartY = currentY;

            if (topicKCs.length === 0) {
              nodeYMap.set(topicId, currentY);
              currentY += rowHeightTopic;
            } else {
              for (const kc of topicKCs) {
                const kcId = kc.concept_id;
                const kcMiscs = rank3.filter(m => childToParent.get(m.concept_id) === kcId);
                nodeYMap.set(kcId, currentY);

                for (const misc of kcMiscs) {
                  nodeYMap.set(misc.concept_id, currentY);
                  currentY += rowHeightKC;
                }
                if (kcMiscs.length === 0) {
                  currentY += rowHeightKC;
                }
              }
              const topicEndY = currentY - rowHeightKC;
              nodeYMap.set(topicId, (topicStartY + topicEndY) / 2);
              currentY += 16;
            }
          }
          const rootEndY = currentY - 16;
          nodeYMap.set(rootId, (rootStartY + rootEndY) / 2);
          currentY += 36;
        }
      }

      // Any remaining nodes not captured in tree traversal
      for (const n of activeNodes) {
        if (!nodeYMap.has(n.concept_id)) {
          nodeYMap.set(n.concept_id, currentY);
          currentY += rowHeightKC;
        }
      }

      simNodes = activeNodes.map((node) => {
        const degree = degreeMap.get(node.concept_id) || node.degree || 0;
        const type = node.raw?.concept_type || node.concept_type || node.raw?.level || node.level;
        const r = rankMap.get(node.concept_id) ?? 2;
        const radius = getNodeRadius(degree, type, r, nodeSizeMultiplier);
        const x = startX + r * colWidth;
        const y = nodeYMap.get(node.concept_id) ?? 150;

        return {
          id: node.concept_id,
          raw: node,
          degree,
          radius,
          rank: r,
          color: getNodeColor({ ...node, degree }, theme, viewMode, activeStudent),
          x,
          y,
          fx: x,
          fy: y,
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

  function drawArrowhead(ctx, sourceX, sourceY, targetX, targetY, targetRadius, color, alpha) {
    const dx = targetX - sourceX;
    const dy = targetY - sourceY;
    const dist = Math.hypot(dx, dy);
    const arrowLen = Math.max(6, Math.min(10, 8 * Math.min(1.2, scale)));
    const arrowWidth = Math.max(5, Math.min(8, 6 * Math.min(1.2, scale)));

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

    // 1. Clean Canvas Background
    ctx.fillStyle = palette.bg;
    ctx.fillRect(0, 0, width, height);

    // Subtle faint micro-grid dots
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

    // 1b. Draw Hierarchical Column Headers
    if (layoutMode === 'rank') {
      for (const col of columnHeaders) {
        if (!simNodes.some(n => n.rank === col.rank)) continue;
        ctx.save();
        const badgeW = 200;
        const badgeH = 26;
        const bx = col.x - 20;
        const by = 40;

        ctx.fillStyle = theme === 'dark' ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.05)';
        ctx.strokeStyle = theme === 'dark' ? 'rgba(255, 255, 255, 0.14)' : 'rgba(15, 23, 42, 0.12)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(bx, by, badgeW, badgeH, 6);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = theme === 'dark' ? '#cbd5e1' : '#475569';
        ctx.font = '700 10.5px Inter, -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(col.label, bx + badgeW / 2, by + badgeH / 2);
        ctx.restore();
      }
    }

    // Neighborhood spotlight set
    const spotlightIds = hoveredNode ? getNeighborIds(hoveredNode.id) : null;
    const searchLower = searchQuery.trim().toLowerCase();

    // 2. Draw Links & Arrowheads (Bezier Curves with high-contrast visible strokes)
    for (const link of simLinks) {
      const source = typeof link.source === 'object' ? link.source : simNodes.find(n => n.id === link.source);
      const target = typeof link.target === 'object' ? link.target : simNodes.find(n => n.id === link.target);
      if (!source || !target) continue;

      const isConnectedToHover = hoveredNode && (source.id === hoveredNode.id || target.id === hoveredNode.id);
      const isConnectedToSelected = selectedConceptId && (source.id === selectedConceptId || target.id === selectedConceptId);

      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const cp1x = source.x + dx * 0.45;
      const cp1y = source.y;
      const cp2x = target.x - dx * 0.45;
      const cp2y = target.y;

      let strokeColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.35)' : 'rgba(71, 85, 105, 0.45)';
      let width = Math.max(1.8, linkThickness * 1.6);
      let alpha = 0.75;
      let isDashed = false;

      if (link.relation === 'ASSOCIATED_WITH') {
        strokeColor = '#e11d48'; // Rose alert for misconception trap
        width = Math.max(2.0, linkThickness * 1.8);
        isDashed = true;
      } else if (link.relation === 'PREREQUISITE_OF' || link.relation === 'REQUIRES') {
        strokeColor = '#2563eb'; // Electric blue for learning progression
        width = Math.max(2.2, linkThickness * 2.0);
      }

      if (hoveredNode) {
        if (isConnectedToHover) {
          alpha = 1.0;
          strokeColor = palette.linkHighlight;
          width *= 1.8;
          isDashed = false;
        } else {
          alpha = 0.08;
        }
      } else if (isConnectedToSelected) {
        alpha = 1.0;
        strokeColor = palette.linkHighlight;
        width *= 1.5;
      }

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, target.x, target.y);

      if (isDashed) {
        ctx.setLineDash([5, 4]);
      }
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = width;
      ctx.stroke();
      ctx.restore();

      if (showArrows) {
        drawArrowhead(ctx, cp2x, cp2y, target.x, target.y, target.radius, strokeColor, alpha);
      }
    }

    // 3. Draw Nodes and Labels
    for (const node of simNodes) {
      const isSelected = node.id === selectedConceptId;
      const isHovered = hoveredNode && node.id === hoveredNode.id;
      const isNeighbor = spotlightIds ? spotlightIds.has(node.id) : false;
      const matchesSearch = searchLower && (node.raw.label?.toLowerCase().includes(searchLower) || node.raw.definition?.toLowerCase().includes(searchLower));

      let alpha = 1.0;
      if (hoveredNode) {
        alpha = isHovered || isNeighbor ? 1.0 : 0.15;
      } else if (searchLower && !matchesSearch) {
        alpha = 0.15;
      } else if (bottlenecksOnly && bottlenecks.length > 0 && !bottlenecks.includes(node.id)) {
        alpha = 0.18;
      }

      ctx.save();
      ctx.globalAlpha = alpha;

      // Draw Node Circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.fill();

      // Border ring
      ctx.strokeStyle = theme === 'dark' ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.25)';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Selection ring
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 4.5, 0, Math.PI * 2);
        ctx.strokeStyle = palette.selectRing;
        ctx.lineWidth = 2.4;
        ctx.stroke();
      } else if (isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 3.5, 0, Math.PI * 2);
        ctx.strokeStyle = palette.hoverRing;
        ctx.lineWidth = 2.0;
        ctx.stroke();
      }

      // Student Mode indicators
      if (viewMode === 'student' && activeStudent) {
        const cState = activeStudent.concept_states?.[node.id];
        if (cState === 'frontier') {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 3.5, 0, Math.PI * 2);
          ctx.strokeStyle = '#2563eb';
          ctx.lineWidth = 2.0;
          ctx.stroke();
        } else if (cState === 'trapped') {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 4.5, 0, Math.PI * 2);
          ctx.strokeStyle = '#e11d48';
          ctx.lineWidth = 2.4;
          ctx.stroke();
        }
      }

      // Cohort Mode: struggle count badge
      if (viewMode === 'cohort') {
        const struggling = node.raw?.struggling_count || 0;
        if (struggling > 0) {
          ctx.save();
          ctx.fillStyle = '#e11d48';
          const badgeX = node.x + node.radius - 2;
          const badgeY = node.y - node.radius + 2;
          ctx.beginPath();
          ctx.arc(badgeX, badgeY, 6.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 8.5px Inter, -apple-system, sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${struggling}`, badgeX, badgeY);
          ctx.restore();
        }
      }

      // Draw Node Label to the right of the node
      const rawText = node.raw?.label || node.id;
      const isRank0 = node.rank === 0;
      const isRank1 = node.rank === 1;
      const isMisc = node.rank === 3;

      let fontSize = isRank0 ? 12.5 : isRank1 ? 11.5 : 10.5;
      let fontWeight = isRank0 ? '700' : isRank1 ? '600' : isSelected || isHovered ? '600' : '400';
      ctx.font = `${fontWeight} ${fontSize}px Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`;

      const maxChars = isRank0 ? 38 : isRank1 ? 34 : 28;
      const displayText = rawText.length > maxChars ? rawText.slice(0, maxChars) + '…' : rawText;

      const labelX = node.x + node.radius + 7;
      const labelY = node.y + 0.5;

      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';

      // Text halo for contrast
      ctx.strokeStyle = palette.textHalo;
      ctx.lineWidth = 3.5;
      ctx.lineJoin = 'round';
      ctx.strokeText(displayText, labelX, labelY);

      // Text fill
      ctx.fillStyle = isMisc
        ? '#e11d48'
        : isHovered || isSelected
        ? palette.textHighlight
        : isNeighbor
        ? palette.textHighlight
        : palette.text;
      ctx.fillText(displayText, labelX, labelY);

      ctx.restore();
    }

    ctx.restore();
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
