import type { GraphEdge, GraphNode, MasteryData, Probe, Student } from './rosterTypes';

export interface ScopedGraphResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  probes: Probe[];
}

/**
 * Computes tree-preserving hierarchical scoping of the curriculum graph:
 * Filters out dormant misconceptions/probes, identifies root strands for the module,
 * prioritizes topics and bottlenecks, scopes atomic concepts according to quota,
 * and maintains connected edges.
 */
export function computeScopedGraph(
  masteryData: MasteryData | null,
  selectedModuleId: string = 'all',
  showBottlenecksOnly: boolean = false,
  maxNodesLimit: number | string = 'all'
): ScopedGraphResult {
  if (!masteryData?.graph) {
    return { nodes: [], edges: [], probes: [] };
  }

  const fullGraph = masteryData.graph;
  const allNodes = fullGraph.nodes || [];
  const allEdges = fullGraph.edges || [];

  // 1. Filter out probes and dormant misconceptions (0 student triggers)
  const activeNodes = allNodes.filter((n) => {
    const type = n.concept_type || n.level;
    if (type === 'socratic_probe') return false;
    if (type === 'misconception') {
      const triggers = n.active_trigger_count || n.struggling_count || 0;
      if (triggers === 0) return false;
    }
    return true;
  });

  const bottleneckSet = new Set(masteryData?.bottlenecks || []);

  // 2. Select root / strand nodes
  let rootStrands: GraphNode[] = [];
  const strandNodes = activeNodes.filter((n) => n.level === 'strand');
  if (selectedModuleId !== 'all') {
    rootStrands = strandNodes.filter((n) => n.module_id === selectedModuleId);
    if (rootStrands.length === 0) {
      rootStrands = activeNodes.filter((n) => n.module_id === selectedModuleId && n.rank === 0);
    }
    if (rootStrands.length === 0) {
      rootStrands = strandNodes.slice(0, 1);
    }
  } else {
    rootStrands = strandNodes.length > 0 ? strandNodes : activeNodes.filter((n) => n.rank === 0);
  }

  const selectedIds = new Set(rootStrands.map((r) => r.concept_id || r.id).filter(Boolean) as string[]);
  const strandIds = new Set(selectedIds);

  // 3. Select Topics (Rank 1) under chosen strands
  let candidateTopics = activeNodes.filter((n) => {
    const isTopic = n.level === 'topic' || n.rank === 1;
    if (!isTopic) return false;
    if (selectedModuleId !== 'all') {
      return (n.module_id === selectedModuleId) || (n.parent_id && strandIds.has(n.parent_id));
    }
    return true;
  });

  // If Bottlenecks Only filter is checked, prioritize topics that are bottlenecks or have bottleneck children
  if (showBottlenecksOnly && bottleneckSet.size > 0) {
    const filteredTopics = candidateTopics.filter((t) => {
      const tid = t.concept_id || t.id;
      if (tid && bottleneckSet.has(tid)) return true;
      return activeNodes.some((c) => c.parent_id === tid && bottleneckSet.has((c.concept_id || c.id) as string));
    });
    if (filteredTopics.length > 0) candidateTopics = filteredTopics;
  }

  // Sort topics by bottleneck status & struggle count
  candidateTopics.sort((a, b) => {
    const aId = a.concept_id || a.id || '';
    const bId = b.concept_id || b.id || '';
    const aB = bottleneckSet.has(aId) ? 1 : 0;
    const bB = bottleneckSet.has(bId) ? 1 : 0;
    if (aB !== bB) return bB - aB;
    return (b.struggling_count || 0) - (a.struggling_count || 0);
  });

  for (const t of candidateTopics) {
    const tid = t.concept_id || t.id;
    if (tid) selectedIds.add(tid);
  }
  const topicIds = new Set(candidateTopics.map((t) => t.concept_id || t.id).filter(Boolean) as string[]);

  // 4. Select Knowledge Components / Subconcepts (Rank 2) under chosen topics
  const candidateKCs = activeNodes.filter((n) => {
    const isKC = n.level === 'atomic_concept' || n.rank === 2;
    return isKC && n.parent_id && topicIds.has(n.parent_id);
  });

  candidateKCs.sort((a, b) => {
    const aStruggle = (a.struggling_count || 0) > 0 ? 1 : 0;
    const bStruggle = (b.struggling_count || 0) > 0 ? 1 : 0;
    if (aStruggle !== bStruggle) return bStruggle - aStruggle;
    return (b.struggling_count || 0) - (a.struggling_count || 0);
  });

  const limit = maxNodesLimit === 'all' ? Infinity : Number(maxNodesLimit);
  const availableKCSlots = maxNodesLimit === 'all' ? candidateKCs.length : Math.max(4, limit - selectedIds.size);
  const chosenKCs = candidateKCs.slice(0, availableKCSlots);

  for (const kc of chosenKCs) {
    const kid = kc.concept_id || kc.id;
    if (kid) selectedIds.add(kid);
  }
  const kcIds = new Set(chosenKCs.map((k) => k.concept_id || k.id).filter(Boolean) as string[]);

  // 5. Select Active Misconceptions (Rank 3) attached to the chosen KCs or Topics
  const activeMisconceptions = activeNodes.filter((n) => {
    const isMisc = n.level === 'misconception' || n.concept_type === 'misconception';
    if (!isMisc) return false;
    const pid = n.parent_id;
    return Boolean(pid && (kcIds.has(pid) || topicIds.has(pid)));
  });

  for (const m of activeMisconceptions) {
    const mid = m.concept_id || m.id;
    if (mid) selectedIds.add(mid);
  }

  // Filter final nodes & edges preserving connections
  const scopedNodes = activeNodes.filter((n) => selectedIds.has((n.concept_id || n.id) as string));
  const scopedEdges = allEdges.filter(
    (e) => selectedIds.has(e.source) && selectedIds.has(e.target)
  );

  return {
    nodes: scopedNodes,
    edges: scopedEdges,
    probes: fullGraph.probes || [],
  };
}

export function getPrerequisites(masteryData: MasteryData | null, selectedConceptId: string): string[] {
  if (!masteryData?.graph?.edges || !selectedConceptId) return [];
  return masteryData.graph.edges
    .filter((e) => (e.relation === 'REQUIRES' || e.relation === 'PREREQUISITE_OF') && e.target === selectedConceptId)
    .map((e) => masteryData.graph?.nodes?.find((n) => (n.concept_id || n.id) === e.source)?.label || e.source)
    .filter(Boolean) as string[];
}

export function getDownstreamDependents(masteryData: MasteryData | null, selectedConceptId: string): string[] {
  if (!masteryData?.graph?.edges || !selectedConceptId) return [];
  return masteryData.graph.edges
    .filter((e) => (e.relation === 'REQUIRES' || e.relation === 'PREREQUISITE_OF') && e.source === selectedConceptId)
    .map((e) => masteryData.graph?.nodes?.find((n) => (n.concept_id || n.id) === e.target)?.label || e.target)
    .filter(Boolean) as string[];
}

export function getStrugglingStudentsForConcept(masteryData: MasteryData | null, selectedConceptId: string): Student[] {
  if (!masteryData?.students || !selectedConceptId) return [];
  return masteryData.students.filter((s) => s.concept_states?.[selectedConceptId] === 'trapped');
}

export function getLinkedProbes(masteryData: MasteryData | null, selectedConceptId: string): Probe[] {
  if (!masteryData?.graph?.probes || !selectedConceptId) return [];
  return masteryData.graph.probes.filter((p) => p.kc_id === selectedConceptId || p.concept_id === selectedConceptId);
}
