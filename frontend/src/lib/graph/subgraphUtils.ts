/**
 * Knowledge graph filtering and subgraph utilities.
 */

export function subgraphForUnit(full: any, moduleId: string): any {
  if (!moduleId) return full;

  const nodeById = new Map((full.nodes || []).map((n: any) => [n.concept_id, n]));
  const edges = full.edges || [];

  // Seed: concepts this module introduces, develops or assesses.
  const keep = new Set<string>(
    (full.module_links || [])
      .filter((link: any) => link.module_id === moduleId)
      .map((link: any) => link.concept_id)
  );

  // A module with no concept links would otherwise render an empty canvas,
  // which reads as a broken page rather than an empty unit. Show everything
  // and let the banner explain instead.
  if (keep.size === 0) return full;

  // Walk up CONTAINS so each kept concept keeps its ancestry and the
  // hierarchy still reads top-down rather than as a floating cloud.
  const parentsOf = new Map<string, string[]>();
  for (const edge of edges) {
    if (edge.relation !== 'CONTAINS') continue;
    if (!parentsOf.has(edge.target)) parentsOf.set(edge.target, []);
    parentsOf.get(edge.target)!.push(edge.source);
  }
  const stack = [...keep];
  while (stack.length) {
    for (const parent of parentsOf.get(stack.pop()!) || []) {
      if (!keep.has(parent)) {
        keep.add(parent);
        stack.push(parent);
      }
    }
  }

  // Pull in the misconceptions hanging off kept concepts, then the probes
  // hanging off those misconceptions. A trap without its concept is noise.
  for (const edge of edges) {
    if (edge.relation === 'ASSOCIATED_WITH' && keep.has(edge.source)) keep.add(edge.target);
  }
  for (const edge of edges) {
    if (edge.relation === 'PROBED_BY' && keep.has(edge.source)) keep.add(edge.target);
  }

  // The module node itself, so the unit has a visible anchor.
  if (nodeById.has(moduleId)) keep.add(moduleId);

  return {
    ...full,
    nodes: (full.nodes || []).filter((n: any) => keep.has(n.concept_id)),
    edges: edges.filter((e: any) => keep.has(e.source) && keep.has(e.target)),
    module_links: (full.module_links || []).filter((l: any) => l.module_id === moduleId),
    source_links: (full.source_links || []).filter((l: any) => keep.has(l.concept_id)),
    probes: (full.probes || []).filter((p: any) => keep.has(p.misconception_id)),
    stats: {},
  };
}

export function formatProbeTier(rung: number | string): string {
  const r = Number(rung);
  if (r === 0) return 'Orienting Inquiry';
  if (r === 1) return 'Critical Challenge';
  if (r === 2) return 'Strategic Framework';
  return `Inquiry Level ${r + 1}`;
}
