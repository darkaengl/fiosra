import { getNodeColor, getNodeRadius } from './graphCanvasTheme';

export interface SugiyamaColumnHeader {
  rank: number;
  label: string;
  x: number;
}

export interface SugiyamaResult {
  simNodes: any[];
  simLinks: any[];
  columnHeaders: SugiyamaColumnHeader[];
}

export function computeSugiyamaRankLayout(
  activeNodes: any[],
  activeEdges: any[],
  degreeMap: Map<string, number>,
  theme: 'light' | 'dark',
  viewMode: string,
  activeStudent: any,
  nodeSizeMultiplier: number
): SugiyamaResult {
  // Deterministic Hierarchical Rank (Sugiyama) Layout
  const rankMap = new Map<string, number>();
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
  const childToParent = new Map<string, string>();
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

  const columnHeaders: SugiyamaColumnHeader[] = [
    { rank: 0, label: 'UNIT / STRAND', x: startX },
    { rank: 1, label: 'CORE TOPICS', x: startX + colWidth },
    { rank: 2, label: 'KNOWLEDGE COMPONENTS', x: startX + 2 * colWidth },
    { rank: 3, label: 'COGNITIVE TRAPS', x: startX + 3 * colWidth },
  ];

  // Vertical tree-based placement
  const nodeYMap = new Map<string, number>();
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

  const simNodes = activeNodes.map((node) => {
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

  const simLinks = activeEdges.map((edge) => ({
    source: edge.source,
    target: edge.target,
    relation: edge.relation
  }));

  return { simNodes, simLinks, columnHeaders };
}
