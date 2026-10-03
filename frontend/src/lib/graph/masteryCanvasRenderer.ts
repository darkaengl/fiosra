import type { SugiyamaColumnHeader } from './masterySugiyamaLayout';

export function drawArrowhead(
  ctx: CanvasRenderingContext2D,
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  targetRadius: number,
  color: string,
  alpha: number,
  scale: number
) {
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

export interface RenderCanvasParams {
  ctx: CanvasRenderingContext2D;
  canvasWidth: number;
  canvasHeight: number;
  dpr: number;
  palette: any;
  panX: number;
  panY: number;
  scale: number;
  layoutMode: string;
  columnHeaders: SugiyamaColumnHeader[];
  simNodes: any[];
  simLinks: any[];
  theme: 'light' | 'dark';
  viewMode: string;
  activeStudent: any;
  hoveredNode: any;
  selectedConceptId: string;
  showArrows: boolean;
  linkThickness: number;
  searchQuery: string;
  bottlenecksOnly: boolean;
  bottlenecks: any[];
  getNeighborIds: (id: string) => Set<string>;
}

export function renderMasteryCanvas(params: RenderCanvasParams) {
  const {
    ctx,
    canvasWidth,
    canvasHeight,
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
  } = params;

  const width = canvasWidth / dpr;
  const height = canvasHeight / dpr;

  // Clear canvas
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

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
      if (!simNodes.some((n) => n.rank === col.rank)) continue;
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

  // 2. Draw Links & Arrowheads
  for (const link of simLinks) {
    const source = typeof link.source === 'object' ? link.source : simNodes.find((n) => n.id === link.source);
    const target = typeof link.target === 'object' ? link.target : simNodes.find((n) => n.id === link.target);
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
    let widthLine = Math.max(1.8, linkThickness * 1.6);
    let alpha = 0.75;
    let isDashed = false;

    if (link.relation === 'ASSOCIATED_WITH') {
      strokeColor = '#e11d48';
      widthLine = Math.max(2.0, linkThickness * 1.8);
      isDashed = true;
    } else if (link.relation === 'PREREQUISITE_OF' || link.relation === 'REQUIRES') {
      strokeColor = '#2563eb';
      widthLine = Math.max(2.2, linkThickness * 2.0);
    }

    if (hoveredNode) {
      if (isConnectedToHover) {
        alpha = 1.0;
        strokeColor = palette.linkHighlight;
        widthLine *= 1.8;
        isDashed = false;
      } else {
        alpha = 0.08;
      }
    } else if (isConnectedToSelected) {
      alpha = 1.0;
      strokeColor = palette.linkHighlight;
      widthLine *= 1.5;
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
    ctx.lineWidth = widthLine;
    ctx.stroke();
    ctx.restore();

    if (showArrows) {
      drawArrowhead(ctx, cp2x, cp2y, target.x, target.y, target.radius, strokeColor, alpha, scale);
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

    const fontSize = isRank0 ? 12.5 : isRank1 ? 11.5 : 10.5;
    const fontWeight = isRank0 ? '700' : isRank1 ? '600' : isSelected || isHovered ? '600' : '400';
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
