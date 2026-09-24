<script>
  import { onMount, onDestroy } from 'svelte';
  import {
    forceSimulation,
    forceManyBody,
    forceLink,
    forceCenter,
    forceCollide
  } from 'd3-force';

  let {
    graph = { nodes: [], edges: [], probes: [] },
    selectedConceptId = '',
    onSelect = () => {},
    theme = $bindable('light'),
    viewMode = 'standard', // 'standard' | 'cohort' | 'student'
    activeStudent = null, // StudentConceptState object
    bottlenecksOnly = false,
    bottlenecks = [],
    showHud = true
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
  let hudOpen = $state(false);
  let activeTab = $state('filters'); // 'filters' | 'display' | 'forces'

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

  // Authentic Obsidian Color Palettes (Light matching screenshot, Dark as classic Obsidian)
  const PALETTES = {
    light: {
      bg: '#ffffff',
      gridDot: 'rgba(0, 0, 0, 0.04)',
      link: 'rgba(0, 0, 0, 0.16)',
      linkHighlight: '#222222',
      linkFade: 'rgba(0, 0, 0, 0.03)',
      text: '#4a4a4a',
      textHighlight: '#0a0a0a',
      textHalo: 'rgba(255, 255, 255, 0.92)',
      selectRing: '#2563eb',
      hoverRing: 'rgba(0, 0, 0, 0.35)',
      // Node colors matching the user's Obsidian graph screenshot
      module: '#242424',            // Major Course Modules / Hubs
      course_theme: '#242424',
      hub_kc: '#444444',            // Prominent Hub Knowledge Components
      pedagogical_kc: '#5c5c5c',    // Standard KCs
      atomic_concept: '#707070',    // Concepts
      topic: '#5c5c5c',
      subtopic: '#787878',
      leaf: '#a3a3a3',              // Small peripheral notes
      misconception: '#e05252',     // Coral Red (matches red nodes in screenshot)
      socratic_probe: '#e59b2c',    // Warm Amber Gold (matches amber nodes in screenshot)
      default: '#707070'
    },
    dark: {
      bg: '#161616',
      gridDot: 'rgba(255, 255, 255, 0.04)',
      link: 'rgba(255, 255, 255, 0.16)',
      linkHighlight: '#f4f4f5',
      linkFade: 'rgba(255, 255, 255, 0.03)',
      text: '#a1a1aa',
      textHighlight: '#ffffff',
      textHalo: 'rgba(22, 22, 22, 0.92)',
      selectRing: '#60a5fa',
      hoverRing: 'rgba(255, 255, 255, 0.55)',
      module: '#f4f4f5',
      course_theme: '#f4f4f5',
      hub_kc: '#d4d4d8',
      pedagogical_kc: '#a1a1aa',
      atomic_concept: '#71717a',
      topic: '#a1a1aa',
      subtopic: '#71717a',
      leaf: '#52525b',
      misconception: '#ef5350',
      socratic_probe: '#f59e0b',
      default: '#a1a1aa'
    }
  };

  function getNodeColor(node, currentTheme) {
    const palette = PALETTES[currentTheme] || PALETTES.light;
    const type = node.raw?.concept_type || node.concept_type || node.raw?.level || node.level;
    if (type === 'misconception') return palette.misconception;
    if (type === 'socratic_probe') return palette.socratic_probe;
    if (type === 'module' || type === 'course_theme') return palette.module;

    // 1. Cohort Heatmap Mode
    if (viewMode === 'cohort') {
      const raw = node.raw || node;
      const rate = raw.cohort_mastery_rate ?? 1.0;
      const struggling = raw.struggling_count || 0;
      if (struggling > 0 && rate < 0.60) return '#e11d48'; // Rose: High struggle / cognitive trap
      if (struggling > 0 || rate < 0.80) return '#d97706'; // Amber: Partial friction
      return '#059669'; // Emerald: Mastered by cohort
    }

    // 2. Individual Student Focus Mode
    if (viewMode === 'student' && activeStudent) {
      const cId = node.id || node.concept_id;
      const st = activeStudent.concept_states?.[cId] || 'frontier';
      if (st === 'mastered') return '#059669'; // Emerald: Mastered
      if (st === 'trapped') return '#e11d48';  // Rose: Trapped in active misconception
      if (st === 'frontier') return '#2563eb'; // Electric Blue: Learning frontier
      return currentTheme === 'dark' ? '#52525b' : '#94a3b8'; // Muted: Locked by prerequisites
    }

    // 3. Default Curriculum View (Obsidian hierarchical tones)
    const deg = node.degree || 0;
    if (deg >= 5) return palette.hub_kc;
    if (deg >= 2) return palette.pedagogical_kc;
    return palette.leaf;
  }

  function getNodeRadius(degree, type, rank = 2) {
    let base = 6.5;
    if (rank === 0 || type === 'strand' || type === 'course_theme' || type === 'module') {
      base = 12;
    } else if (rank === 1 || type === 'topic' || type === 'domain') {
      base = 9;
    } else if (rank === 3 || type === 'misconception') {
      base = 7.5;
    } else {
      base = 6.5;
    }
    return base * nodeSizeMultiplier;
  }

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

  // Ids within `depth` hops of `rootId`, walking the raw edges so the result
  // does not depend on what the simulation happens to hold right now.
  function neighbourhoodIds(rootId, edges, depth) {
    const adjacency = new Map();
    const link = (a, b) => {
      if (!adjacency.has(a)) adjacency.set(a, []);
      adjacency.get(a).push(b);
    };
    for (const edge of edges) { link(edge.source, edge.target); link(edge.target, edge.source); }
    const seen = new Set([rootId]);
    let frontier = [rootId];
    for (let hop = 0; hop < depth; hop++) {
      const next = [];
      for (const id of frontier) {
        for (const other of adjacency.get(id) || []) {
          if (!seen.has(other)) { seen.add(other); next.push(other); }
        }
      }
      frontier = next;
      if (!frontier.length) break;
    }
    return seen;
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
        const radius = getNodeRadius(degree, type, r);
        const x = startX + r * colWidth;
        const y = nodeYMap.get(node.concept_id) ?? 150;

        return {
          id: node.concept_id,
          raw: node,
          degree,
          radius,
          rank: r,
          color: getNodeColor({ ...node, degree }, theme),
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
      const radius = getNodeRadius(degree, type, 2);
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
        color: getNodeColor({ ...node, degree }, theme),
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
      node.color = getNodeColor(node, currentTheme);
      node.radius = getNodeRadius(node.degree, node.raw?.concept_type || node.raw?.level);
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
    <div class="obsidian-hud" class:collapsed={!hudOpen}>
      <header class="hud-header">
        <div class="hud-title">
          <span class="hud-icon">✦</span>
          <span>Graph View</span>
        </div>
        <div class="hud-header-actions">
          <!-- Theme Switcher: Light (Screenshot) vs Dark -->
          <div class="theme-toggle-group">
            <button
              type="button"
              class="theme-btn"
              class:active={theme === 'light'}
              onclick={() => toggleTheme('light')}
              title="Obsidian Light Mode (as in reference)"
            >
              ☀ Light
            </button>
            <button
              type="button"
              class="theme-btn"
              class:active={theme === 'dark'}
              onclick={() => toggleTheme('dark')}
              title="Obsidian Dark Mode"
            >
              ☾ Dark
            </button>
          </div>
          <button type="button" class="hud-toggle-btn" onclick={() => hudOpen = !hudOpen} aria-label="Toggle Controls">
            {hudOpen ? '−' : '+'}
          </button>
        </div>
      </header>

      {#if hudOpen}
        <div class="hud-body">
          <!-- Tab navigation -->
          <nav class="hud-tabs">
            <button type="button" class="tab-btn" class:active={activeTab === 'filters'} onclick={() => activeTab = 'filters'}>Filters</button>
            <button type="button" class="tab-btn" class:active={activeTab === 'display'} onclick={() => activeTab = 'display'}>Display</button>
            <button type="button" class="tab-btn" class:active={activeTab === 'forces'} onclick={() => activeTab = 'forces'}>Forces</button>
          </nav>

          {#if activeTab === 'filters'}
            <!-- Search filter -->
            <div class="hud-section">
              <label for="graph-search">Search</label>
              <input
                id="graph-search"
                type="text"
                placeholder="Search concepts or notes..."
                bind:value={searchQuery}
              />
            </div>

            <div class="hud-section">
              <span class="section-label">Focus</span>
              <label class="checkbox-pill focus">
                <input type="checkbox" bind:checked={focusMode} />
                <span>Only the selected node</span>
              </label>
              {#if focusMode}
                <div class="focus-depth">
                  <button type="button" class:on={focusDepth === 1} onclick={() => (focusDepth = 1)}>Direct links</button>
                  <button type="button" class:on={focusDepth === 2} onclick={() => (focusDepth = 2)}>Two hops</button>
                </div>
                {#if !selectedConceptId}
                  <p class="focus-hint">Click a node to focus on it.</p>
                {/if}
              {/if}
            </div>

            <!-- Color Groups / Toggles (matching the screenshot) -->
            <div class="hud-section">
              <span class="section-label">Groups & Categories</span>
              <div class="toggle-group">
                <label class="checkbox-pill kc">
                  <input type="checkbox" bind:checked={showKCs} />
                  <span class="dot kc-dot"></span>
                  <span>Concepts & KCs</span>
                </label>
                <label class="checkbox-pill misc">
                  <input type="checkbox" bind:checked={showMisconceptions} />
                  <span class="dot misc-dot"></span>
                  <span>Cognitive Traps (Red)</span>
                </label>
                <label class="checkbox-pill probe">
                  <input type="checkbox" bind:checked={showProbes} />
                  <span class="dot probe-dot"></span>
                  <span>Diagnostic Probes (Gold)</span>
                </label>
                <label class="checkbox-pill module">
                  <input type="checkbox" bind:checked={showModules} />
                  <span class="dot module-dot"></span>
                  <span>Curriculum Modules</span>
                </label>
              </div>
            </div>
          {:else if activeTab === 'display'}
            <!-- Display Controls -->
            <div class="hud-section">
              <div class="slider-row">
                <span>Node Size</span>
                <input type="range" min="0.6" max="2.2" step="0.1" bind:value={nodeSizeMultiplier} />
              </div>
              <div class="slider-row">
                <span>Link Thickness</span>
                <input type="range" min="0.5" max="3.0" step="0.25" bind:value={linkThickness} />
              </div>
              <div class="slider-row">
                <span>Text Size</span>
                <input type="range" min="8" max="16" step="1" bind:value={textSize} />
              </div>
              <div class="checkbox-row">
                <label class="toggle-label">
                  <input type="checkbox" bind:checked={showArrows} />
                  <span>Show Directional Arrows</span>
                </label>
              </div>
              <div class="checkbox-row">
                <label class="toggle-label">
                  <input type="checkbox" bind:checked={showAllLabels} />
                  <span>Show All Text Labels</span>
                </label>
              </div>
            </div>
          {:else if activeTab === 'forces'}
            <!-- Force Simulation Controls -->
            <div class="hud-section">
              <div class="slider-row">
                <span>Center Force</span>
                <input type="range" min="0.01" max="0.25" step="0.01" bind:value={centerGravity} />
              </div>
              <div class="slider-row">
                <span>Repulsion (Charge)</span>
                <input type="range" min="-550" max="-80" step="20" bind:value={repulsion} />
              </div>
              <div class="slider-row">
                <span>Link Distance</span>
                <input type="range" min="40" max="200" step="10" bind:value={linkDistance} />
              </div>
            </div>
          {/if}

          <!-- Quick Actions -->
          <div class="hud-actions">
            <button type="button" class="btn-hud" onclick={recenterGraph}>
              ⟲ Reset View
            </button>
            <button type="button" class="btn-hud" onclick={() => { if (simulation) simulation.alpha(0.6).restart(); }}>
              ⚡ Reheat
            </button>
          </div>
        </div>
      {/if}
    </div>
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
  {#if hoveredNode}
    <div
      class="node-tooltip"
      style="left: {mousePos.x + 14}px; top: {mousePos.y - 12}px;"
    >
      <div class="tooltip-header">
        <span
          class="tooltip-tag"
          style="background: {hoveredNode.color}22; color: {hoveredNode.color}; border: 1px solid {hoveredNode.color}44;"
        >
          {hoveredNode.raw.concept_type || hoveredNode.raw.level}
        </span>
        <span class="tooltip-degree">{hoveredNode.degree} {hoveredNode.degree === 1 ? 'connection' : 'connections'}</span>
      </div>
      <strong class="tooltip-title">{hoveredNode.raw.label}</strong>

      {#if viewMode === 'cohort' && hoveredNode.raw.cohort_mastery_rate !== undefined}
        <div class="tooltip-metric-pill" style="border-left: 3px solid {hoveredNode.color};">
          <span class="metric-rate">{Math.round((hoveredNode.raw.cohort_mastery_rate ?? 1) * 100)}% Cohort Mastery</span>
          {#if (hoveredNode.raw.struggling_count || 0) > 0}
            <span class="struggle-tag">⚠️ {hoveredNode.raw.struggling_count} trapped</span>
          {/if}
        </div>
      {/if}

      {#if viewMode === 'student' && activeStudent}
        {@const cState = activeStudent.concept_states?.[hoveredNode.id] || 'locked'}
        <div class="tooltip-metric-pill" style="border-left: 3px solid {hoveredNode.color};">
          <span class="metric-rate">{activeStudent.name}:</span>
          <strong style="text-transform: capitalize; color: {hoveredNode.color}; font-size: 10px;">{cState}</strong>
        </div>
      {/if}

      {#if hoveredNode.raw.definition}
        <p class="tooltip-def">{hoveredNode.raw.definition}</p>
      {/if}
      <span class="tooltip-hint">Click node to inspect details</span>
    </div>
  {/if}
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

  /* Obsidian Graph Settings Floating Panel */
  .obsidian-hud {
    position: absolute;
    top: 14px;
    right: 14px;
    width: 260px;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    font-size: 11px;
    z-index: 20;
    transition: width 0.2s ease, opacity 0.2s ease;
  }

  .light-mode .obsidian-hud {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(0, 0, 0, 0.12);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    color: #334155;
  }

  .dark-mode .obsidian-hud {
    background: rgba(24, 24, 27, 0.88);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55);
    color: #e2e8f0;
  }

  .obsidian-hud.collapsed {
    width: auto;
  }

  .hud-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  }
  .dark-mode .hud-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .hud-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    font-size: 11.5px;
    letter-spacing: 0.2px;
  }
  .hud-icon {
    font-size: 11px;
    color: #e59b2c;
  }

  .hud-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .theme-toggle-group {
    display: flex;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 4px;
    padding: 2px;
    gap: 2px;
  }
  .dark-mode .theme-toggle-group {
    background: rgba(255, 255, 255, 0.08);
  }

  .theme-btn {
    background: transparent;
    border: none;
    border-radius: 3px;
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 6px;
    cursor: pointer;
    color: #64748b;
    transition: all 0.15s ease;
  }
  .dark-mode .theme-btn {
    color: #94a3b8;
  }
  .theme-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  }
  .dark-mode .theme-btn.active {
    background: #27272a;
    color: #f8fafc;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }

  .hud-toggle-btn {
    background: transparent;
    border: none;
    color: #64748b;
    cursor: pointer;
    font-size: 13px;
    padding: 0 3px;
  }
  .hud-toggle-btn:hover {
    color: #0f172a;
  }
  .dark-mode .hud-toggle-btn:hover {
    color: #ffffff;
  }

  .hud-body {
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .hud-tabs {
    display: flex;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    gap: 4px;
    padding-bottom: 6px;
  }
  .dark-mode .hud-tabs {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .tab-btn {
    background: transparent;
    border: none;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 8px;
    cursor: pointer;
    color: #64748b;
    transition: all 0.15s ease;
  }
  .tab-btn:hover {
    color: #0f172a;
  }
  .dark-mode .tab-btn {
    color: #94a3b8;
  }
  .dark-mode .tab-btn:hover {
    color: #f8fafc;
  }
  .tab-btn.active {
    background: rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }
  .dark-mode .tab-btn.active {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
  }

  .hud-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .section-label,
  .hud-section label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    color: #64748b;
  }
  .dark-mode .section-label,
  .dark-mode .hud-section label {
    color: #94a3b8;
  }

  .hud-section input[type="text"] {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    color: #0f172a;
    font-size: 11px;
    padding: 5px 8px;
    outline: none;
    transition: border-color 0.15s ease;
  }
  .hud-section input[type="text"]:focus {
    border-color: #2563eb;
  }
  .dark-mode .hud-section input[type="text"] {
    background: #18181b;
    border: 1px solid #3f3f46;
    color: #f8fafc;
  }
  .dark-mode .hud-section input[type="text"]:focus {
    border-color: #60a5fa;
  }

  .toggle-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .focus-depth { display: flex; gap: 6px; margin-top: 8px; }
  .focus-depth button {
    flex: 1; font: inherit; font-size: 11px; cursor: pointer;
    padding: 4px 8px; border-radius: 6px;
    border: 1px solid rgba(148, 163, 184, 0.45);
    background: transparent; color: inherit; opacity: 0.75;
  }
  .focus-depth button.on { opacity: 1; border-color: #38bdf8; background: rgba(56, 189, 248, 0.14); }
  .focus-hint { margin: 8px 0 0; font-size: 11px; opacity: 0.7; }

  .checkbox-pill {
    display: flex;
    align-items: center;
    gap: 7px;
    cursor: pointer;
    font-size: 11px;
    color: #475569;
    padding: 2px 0;
  }
  .checkbox-pill:hover {
    color: #0f172a;
  }
  .dark-mode .checkbox-pill {
    color: #cbd5e1;
  }
  .dark-mode .checkbox-pill:hover {
    color: #ffffff;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .kc-dot { background: #5c5c5c; }
  .misc-dot { background: #e05252; }
  .probe-dot { background: #e59b2c; }
  .module-dot { background: #242424; }
  .dark-mode .kc-dot { background: #a1a1aa; }
  .dark-mode .misc-dot { background: #ef5350; }
  .dark-mode .probe-dot { background: #f59e0b; }
  .dark-mode .module-dot { background: #f4f4f5; }

  .slider-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-size: 10px;
    color: #475569;
  }
  .dark-mode .slider-row {
    color: #94a3b8;
  }
  .slider-row input[type="range"] {
    width: 115px;
    accent-color: #475569;
    cursor: pointer;
  }
  .dark-mode .slider-row input[type="range"] {
    accent-color: #a1a1aa;
  }

  .checkbox-row {
    display: flex;
    align-items: center;
    padding: 2px 0;
  }
  .toggle-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10.5px;
    color: #475569;
    cursor: pointer;
  }
  .dark-mode .toggle-label {
    color: #cbd5e1;
  }

  .hud-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 4px;
    padding-top: 6px;
    border-top: 1px solid rgba(0, 0, 0, 0.08);
  }
  .dark-mode .hud-actions {
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .btn-hud {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    color: #334155;
    cursor: pointer;
    font-size: 10px;
    font-weight: 500;
    padding: 5px 8px;
    text-align: center;
    transition: all 0.15s ease;
  }
  .btn-hud:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
    color: #0f172a;
  }
  .dark-mode .btn-hud {
    background: rgba(39, 39, 42, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #f1f5f9;
  }
  .dark-mode .btn-hud:hover {
    background: rgba(63, 63, 70, 0.9);
    border-color: #a1a1aa;
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

  /* Node Hover Tooltip */
  .node-tooltip {
    position: fixed;
    pointer-events: none;
    border-radius: 6px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    max-width: 270px;
    padding: 9px 12px;
    z-index: 50;
    transition: opacity 0.1s ease;
  }
  .light-mode .node-tooltip {
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.14);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
    color: #1e293b;
  }
  .dark-mode .node-tooltip {
    background: rgba(24, 24, 27, 0.94);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.65);
    color: #f8fafc;
  }

  .tooltip-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 5px;
  }
  .tooltip-tag {
    border-radius: 3px;
    font-size: 8.5px;
    font-weight: 700;
    letter-spacing: 0.3px;
    padding: 2px 5px;
    text-transform: uppercase;
  }
  .tooltip-degree {
    font-size: 9px;
    color: #64748b;
  }
  .dark-mode .tooltip-degree {
    color: #94a3b8;
  }

  .tooltip-title {
    display: block;
    font-size: 12px;
    line-height: 1.35;
    margin-bottom: 4px;
    color: #0f172a;
  }
  .dark-mode .tooltip-title {
    color: #ffffff;
  }

  .tooltip-def {
    font-size: 10.5px;
    line-height: 1.4;
    color: #475569;
    margin: 0 0 5px 0;
  }
  .dark-mode .tooltip-def {
    color: #cbd5e1;
  }

  .tooltip-hint {
    color: #2563eb;
    font-size: 9px;
    font-style: italic;
  }
  .dark-mode .tooltip-hint {
    color: #60a5fa;
  }

  .tooltip-metric-pill {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 3px 6px;
    margin: 4px 0 6px 0;
    border-radius: 4px;
    font-size: 10px;
    background: rgba(0, 0, 0, 0.04);
  }
  .dark-mode .tooltip-metric-pill {
    background: rgba(255, 255, 255, 0.06);
  }
  .metric-rate {
    font-weight: 600;
  }
  .struggle-tag {
    color: #e11d48;
    font-weight: 600;
  }
</style>
