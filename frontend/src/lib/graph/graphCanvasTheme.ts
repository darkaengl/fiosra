export interface PaletteColors {
  bg: string;
  gridDot: string;
  link: string;
  linkHighlight: string;
  linkFade: string;
  text: string;
  textHighlight: string;
  textHalo: string;
  selectRing: string;
  hoverRing: string;
  module: string;
  course_theme: string;
  hub_kc: string;
  pedagogical_kc: string;
  atomic_concept: string;
  topic: string;
  subtopic: string;
  leaf: string;
  misconception: string;
  socratic_probe: string;
  default: string;
}

export const PALETTES: Record<'light' | 'dark', PaletteColors> = {
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
    module: '#242424',
    course_theme: '#242424',
    hub_kc: '#444444',
    pedagogical_kc: '#5c5c5c',
    atomic_concept: '#707070',
    topic: '#5c5c5c',
    subtopic: '#787878',
    leaf: '#a3a3a3',
    misconception: '#e05252',
    socratic_probe: '#e59b2c',
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

export function getNodeColor(
  node: any,
  currentTheme: 'light' | 'dark',
  viewMode: string = 'standard',
  activeStudent: any = null
): string {
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
    if (struggling > 0 && rate < 0.60) return '#e11d48'; // Rose: High struggle
    if (struggling > 0 || rate < 0.80) return '#d97706'; // Amber: Partial friction
    return '#059669'; // Emerald: Mastered by cohort
  }

  // 2. Individual Student Focus Mode
  if (viewMode === 'student' && activeStudent) {
    const cId = node.id || node.concept_id;
    const st = activeStudent.concept_states?.[cId] || 'frontier';
    if (st === 'mastered') return '#059669'; // Emerald: Mastered
    if (st === 'trapped') return '#e11d48';  // Rose: Trapped
    if (st === 'frontier') return '#2563eb'; // Electric Blue: Learning frontier
    return currentTheme === 'dark' ? '#52525b' : '#94a3b8'; // Muted: Locked
  }

  // 3. Default Curriculum View (Obsidian hierarchical tones)
  const deg = node.degree || 0;
  if (deg >= 5) return palette.hub_kc;
  if (deg >= 2) return palette.pedagogical_kc;
  return palette.leaf;
}

export function getNodeRadius(
  degree: number,
  type: string,
  rank: number = 2,
  nodeSizeMultiplier: number = 1.1
): number {
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

export function neighbourhoodIds(rootId: string, edges: any[], depth: number): Set<string> {
  const adjacency = new Map<string, string[]>();
  const link = (a: string, b: string) => {
    if (!adjacency.has(a)) adjacency.set(a, []);
    adjacency.get(a)!.push(b);
  };
  for (const edge of edges) {
    link(edge.source, edge.target);
    link(edge.target, edge.source);
  }
  const seen = new Set<string>([rootId]);
  let frontier = [rootId];
  for (let hop = 0; hop < depth; hop++) {
    const next: string[] = [];
    for (const id of frontier) {
      for (const other of adjacency.get(id) || []) {
        if (!seen.has(other)) {
          seen.add(other);
          next.push(other);
        }
      }
    }
    frontier = next;
    if (!frontier.length) break;
  }
  return seen;
}
