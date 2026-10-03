<script lang="ts">
  import { formatProbeTier } from './subgraphUtils';

  let {
    selectedConcept,
    selectedConceptId = '',
    graph = { nodes: [], edges: [], module_links: [], probes: [] },
    course = null,
    onSelectNode = () => {},
    onClose = () => {}
  } = $props<{
    selectedConcept: any;
    selectedConceptId?: string;
    graph?: any;
    course?: any;
    onSelectNode?: (id: string) => void;
    onClose?: () => void;
  }>();

  let isMisconception = $derived(
    selectedConcept?.concept_type === 'misconception' || selectedConcept?.level === 'misconception'
  );
  let parents = $derived(
    graph.edges
      ?.filter((edge: any) => edge.relation === 'CONTAINS' && edge.target === selectedConceptId)
      .map((edge: any) => graph.nodes?.find((node: any) => node.concept_id === edge.source)?.label)
      .filter(Boolean) || []
  );
  let children = $derived(
    graph.edges
      ?.filter((edge: any) => edge.relation === 'CONTAINS' && edge.source === selectedConceptId)
      .map((edge: any) => graph.nodes?.find((node: any) => node.concept_id === edge.target)?.label)
      .filter(Boolean) || []
  );
  let prerequisites = $derived(
    graph.edges
      ?.filter((edge: any) => (edge.relation === 'PREREQUISITE_OF' || edge.relation === 'REQUIRES') && edge.target === selectedConceptId)
      .map((edge: any) => graph.nodes?.find((node: any) => node.concept_id === edge.source)?.label)
      .filter(Boolean) || []
  );
  let moduleRoles = $derived(
    graph.module_links
      ?.filter((link: any) => link.concept_id === selectedConceptId)
      .map((link: any) => ({
        ...link,
        title: course?.modules?.find((module: any) => module.module_id === link.module_id)?.title || 'Course module'
      })) || []
  );
  let associatedKCs = $derived(
    graph.edges
      ?.filter((edge: any) => edge.relation === 'ASSOCIATED_WITH' && edge.target === selectedConceptId)
      .map((edge: any) => graph.nodes?.find((node: any) => node.concept_id === edge.source))
      .filter(Boolean) || []
  );
  let associatedMisconceptions = $derived(
    graph.edges
      ?.filter((edge: any) => edge.relation === 'ASSOCIATED_WITH' && edge.source === selectedConceptId)
      .map((edge: any) => graph.nodes?.find((node: any) => node.concept_id === edge.target))
      .filter(Boolean) || []
  );
  let linkedProbes = $derived(
    graph.probes?.filter((probe: any) => probe.misconception_id === selectedConceptId) || []
  );
</script>

<aside
  class="node-popup-drawer"
  role="dialog"
  aria-modal="true"
  aria-label="Node Details"
>
  <header class="drawer-header">
    <div class="drawer-header-left">
      {#if isMisconception}
        <span class="drawer-category-tag trap">⚠️ Cognitive Trap</span>
      {:else if selectedConcept.concept_type === 'socratic_probe'}
        <span class="drawer-category-tag probe">✦ Socratic Probe</span>
      {:else if selectedConcept.concept_type === 'module'}
        <span class="drawer-category-tag module">📚 Module Unit</span>
      {:else}
        <span class="drawer-category-tag kc">🎯 Knowledge Component</span>
      {/if}
      {#if selectedConcept.status === 'pending_review'}
        <span class="review-badge">Review Pending</span>
      {/if}
    </div>

    <button
      type="button"
      class="drawer-close-btn"
      onclick={onClose}
      aria-label="Close inspector"
      title="Close (Esc)"
    >
      ✕
    </button>
  </header>

  <div class="drawer-content">
    {#if isMisconception}
      <!-- Misconception Cognitive Trap View -->
      <h2 class="drawer-title">{selectedConcept.label}</h2>
      <span class="level-pill trap-pill">Misconception Trap</span>

      <div class="trap-box">
        <h3>Flawed Student Assumption</h3>
        <p>{selectedConcept.definition}</p>
      </div>

      {#if selectedConcept.remediation_hint}
        <div class="remediation-box">
          <h3>Socratic Remediation Strategy</h3>
          <p>{selectedConcept.remediation_hint}</p>
        </div>
      {/if}

      <section class="drawer-section">
        <h3>Target Knowledge Component</h3>
        {#if associatedKCs.length}
          <div class="chip-container">
            {#each associatedKCs as kc}
              <button type="button" class="kc-chip" onclick={() => onSelectNode(kc.concept_id)}>
                🎯 <strong>{kc.label}</strong>
              </button>
            {/each}
          </div>
        {:else}
          <p class="muted-text">Associated directly with course domain.</p>
        {/if}
      </section>

      <section class="drawer-section">
        <h3>Socratic Diagnostic Probes ({linkedProbes.length})</h3>
        {#if linkedProbes.length}
          <div class="probes-list">
            {#each linkedProbes as probe}
              <div class="probe-card">
                <div class="probe-header">
                  <span class="rung-badge">{formatProbeTier(probe.rung)}</span>
                  {#if probe.rationale}
                    <span class="probe-rationale">{probe.rationale}</span>
                  {/if}
                </div>
                <p class="probe-text">"{probe.probe_text}"</p>
              </div>
            {/each}
          </div>
        {:else}
          <p class="muted-text">No active Socratic diagnostic probes attached.</p>
        {/if}
      </section>

    {:else if selectedConcept.concept_type === 'socratic_probe'}
      <!-- Socratic Diagnostic Probe View -->
      <h2 class="drawer-title">{formatProbeTier(selectedConcept.rung ?? 0)} Probe</h2>
      <span class="level-pill probe-pill">Diagnostic Inquiry</span>

      <div class="probe-box">
        <h3>Diagnostic Inquiry</h3>
        <p>"{selectedConcept.definition}"</p>
      </div>

      {#if selectedConcept.rationale}
        <div class="remediation-box">
          <h3>Pedagogical Rationale</h3>
          <p>{selectedConcept.rationale}</p>
        </div>
      {/if}

      {#if selectedConcept.misconception_id}
        {@const targetMisc = graph.nodes?.find((n: any) => n.concept_id === selectedConcept.misconception_id)}
        {#if targetMisc}
          <section class="drawer-section">
            <h3>Probed Misconception Trap</h3>
            <button type="button" class="trap-chip" onclick={() => onSelectNode(targetMisc.concept_id)}>
              <div class="trap-chip-title">⚠️ <strong>{targetMisc.label}</strong></div>
              <span class="trap-chip-def">{targetMisc.definition}</span>
            </button>
          </section>
        {/if}
      {/if}

    {:else if selectedConcept.concept_type === 'module'}
      <!-- Course Module Unit View -->
      <h2 class="drawer-title">{selectedConcept.label}</h2>
      <span class="level-pill module-pill">Course Module</span>
      <p class="definition">{selectedConcept.definition}</p>

    {:else}
      <!-- Standard Knowledge Component / Concept View -->
      <h2 class="drawer-title">{selectedConcept.label}</h2>
      <span class="level-pill kc-pill">{selectedConcept.level?.replaceAll('_', ' ') || 'Concept'}</span>
      <p class="definition">{selectedConcept.definition}</p>

      <div class="stat-grid">
        <div><span>Type</span><strong>{selectedConcept.concept_type}</strong></div>
        <div><span>Bloom Level</span><strong>{selectedConcept.bloom_level || 'Apply'}</strong></div>
      </div>

      {#if associatedMisconceptions.length}
        <section class="drawer-section misconception-alerts">
          <h3>Cognitive Traps ({associatedMisconceptions.length})</h3>
          <div class="chip-container-vertical">
            {#each associatedMisconceptions as misc}
              <button type="button" class="trap-chip" onclick={() => onSelectNode(misc.concept_id)}>
                <div class="trap-chip-title">⚠️ <strong>{misc.label}</strong></div>
                <span class="trap-chip-def">{misc.definition}</span>
              </button>
            {/each}
          </div>
        </section>
      {/if}

      <section class="drawer-section">
        <h3>Hierarchy & Prerequisites</h3>
        <p><strong>Parent</strong>{parents.length ? parents.join(' · ') : 'Top-level concept'}</p>
        <p><strong>Children</strong>{children.length ? children.join(' · ') : 'No lower-level concepts'}</p>
        <p><strong>Prerequisites</strong>{prerequisites.length ? prerequisites.join(' · ') : 'None'}</p>
      </section>

      <section class="drawer-section">
        <h3>Module Roles</h3>
        {#if moduleRoles.length}
          <div class="roles-list">
            {#each moduleRoles as role}
              <p><span class={`role ${role.role}`}>{role.role}</span>{role.title}</p>
            {/each}
          </div>
        {:else}
          <p class="muted-text">No explicit course module role set.</p>
        {/if}
      </section>
    {/if}
  </div>
</aside>

<style>
  .node-popup-drawer {
    position: absolute;
    top: 14px;
    right: 14px;
    bottom: 14px;
    width: 410px;
    max-width: calc(100vw - 28px);
    z-index: 35;
    border-radius: 10px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: slideIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(0, 0, 0, 0.14);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.14);
    color: #0f172a;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(18px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  :global(.dark-mode) .node-popup-drawer {
    background: rgba(20, 20, 24, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.65);
    color: #f1f5f9;
  }

  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  }
  :global(.dark-mode) .drawer-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .drawer-header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .drawer-category-tag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    padding: 3px 7px;
    border-radius: 4px;
  }
  .drawer-category-tag.kc { background: rgba(92, 92, 92, 0.14); color: #475569; }
  :global(.dark-mode) .drawer-category-tag.kc { background: rgba(161, 161, 170, 0.16); color: #d4d4d8; }
  .drawer-category-tag.trap { background: rgba(224, 82, 82, 0.14); color: #dc2626; }
  :global(.dark-mode) .drawer-category-tag.trap { background: rgba(239, 83, 80, 0.2); color: #fca5a5; }
  .drawer-category-tag.probe { background: rgba(229, 155, 44, 0.14); color: #d97706; }
  :global(.dark-mode) .drawer-category-tag.probe { background: rgba(245, 158, 11, 0.2); color: #fde047; }
  .drawer-category-tag.module { background: rgba(36, 36, 36, 0.14); color: #1e293b; }
  :global(.dark-mode) .drawer-category-tag.module { background: rgba(244, 244, 245, 0.16); color: #f4f4f5; }

  .review-badge {
    font-size: 8.5px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
  }

  .drawer-close-btn {
    background: transparent;
    border: none;
    font-size: 14px;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    transition: all 0.15s ease;
  }
  .drawer-close-btn:hover {
    background: rgba(0, 0, 0, 0.08);
    color: #0f172a;
  }
  :global(.dark-mode) .drawer-close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }

  .drawer-content {
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .drawer-title {
    font-size: 18px;
    font-weight: 600;
    line-height: 1.3;
    margin: 0;
  }

  .level-pill {
    align-self: flex-start;
    border-radius: 99px;
    display: inline-block;
    font-size: 9px;
    font-weight: 700;
    padding: 3px 8px;
    text-transform: uppercase;
  }
  .kc-pill { background: rgba(59, 130, 246, 0.12); color: #2563eb; }
  :global(.dark-mode) .kc-pill { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
  .trap-pill { background: rgba(224, 82, 82, 0.12); color: #dc2626; }
  :global(.dark-mode) .trap-pill { background: rgba(239, 83, 80, 0.2); color: #fca5a5; }
  .probe-pill { background: rgba(229, 155, 44, 0.12); color: #d97706; }
  :global(.dark-mode) .probe-pill { background: rgba(245, 158, 11, 0.2); color: #fde047; }
  .module-pill { background: rgba(36, 36, 36, 0.12); color: #1e293b; }
  :global(.dark-mode) .module-pill { background: rgba(244, 244, 245, 0.2); color: #f4f4f5; }

  .definition {
    font-size: 12.5px;
    line-height: 1.5;
    margin: 0;
    color: #475569;
  }
  :global(.dark-mode) .definition {
    color: #cbd5e1;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .stat-grid > div {
    padding: 8px 10px;
    border-radius: 6px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
  }
  :global(.dark-mode) .stat-grid > div {
    background: #18181b;
    border: 1px solid #27272a;
  }
  .stat-grid span {
    display: block;
    font-size: 8.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
  }
  .stat-grid strong {
    font-size: 11.5px;
  }

  .trap-box {
    border-radius: 6px;
    padding: 10px 12px;
    background: #fef2f2;
    border: 1px solid #fecaca;
  }
  :global(.dark-mode) .trap-box {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .trap-box h3 {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin: 0 0 4px;
    color: #dc2626;
  }
  :global(.dark-mode) .trap-box h3 {
    color: #f87171;
  }
  .trap-box p {
    font-size: 11.5px;
    line-height: 1.45;
    margin: 0;
    color: #991b1b;
  }
  :global(.dark-mode) .trap-box p {
    color: #fecaca;
  }

  .probe-box {
    border-radius: 6px;
    padding: 10px 12px;
    background: #fffbeb;
    border: 1px solid #fde68a;
  }
  :global(.dark-mode) .probe-box {
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }
  .probe-box h3 {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin: 0 0 4px;
    color: #d97706;
  }
  :global(.dark-mode) .probe-box h3 {
    color: #fbbf24;
  }
  .probe-box p {
    font-size: 11.5px;
    line-height: 1.45;
    margin: 0;
    color: #92400e;
  }
  :global(.dark-mode) .probe-box p {
    color: #fef3c7;
  }

  .remediation-box {
    border-radius: 6px;
    padding: 10px 12px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
  }
  :global(.dark-mode) .remediation-box {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  .remediation-box h3 {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin: 0 0 4px;
    color: #16a34a;
  }
  :global(.dark-mode) .remediation-box h3 {
    color: #34d399;
  }
  .remediation-box p {
    font-size: 11px;
    line-height: 1.45;
    margin: 0;
    color: #166534;
  }
  :global(.dark-mode) .remediation-box p {
    color: #d1fae5;
  }

  .drawer-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .drawer-section h3 {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin: 0;
    color: #64748b;
  }
  :global(.dark-mode) .drawer-section h3 {
    color: #94a3b8;
  }
  .drawer-section p {
    font-size: 11.5px;
    line-height: 1.45;
    margin: 3px 0;
    color: #334155;
  }
  :global(.dark-mode) .drawer-section p {
    color: #cbd5e1;
  }
  .drawer-section p strong {
    display: block;
    font-size: 8.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
  }
  :global(.dark-mode) .drawer-section p strong {
    color: #94a3b8;
  }

  .chip-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .kc-chip {
    align-items: center;
    border-radius: 5px;
    cursor: pointer;
    display: inline-flex;
    font-size: 11px;
    gap: 5px;
    padding: 5px 9px;
    text-align: left;
    transition: all 0.15s ease;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    color: #0f172a;
  }
  .kc-chip:hover {
    background: #e2e8f0;
    border-color: #94a3b8;
  }
  :global(.dark-mode) .kc-chip {
    background: #27272a;
    border: 1px solid #3f3f46;
    color: #f1f5f9;
  }
  :global(.dark-mode) .kc-chip:hover {
    background: #3f3f46;
    border-color: #60a5fa;
  }

  .chip-container-vertical {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .trap-chip {
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 8px 10px;
    text-align: left;
    transition: all 0.15s ease;
    width: 100%;
    background: #fff5f5;
    border: 1px solid #fed7d7;
  }
  .trap-chip:hover {
    background: #fee2e2;
    border-color: #f87171;
  }
  :global(.dark-mode) .trap-chip {
    background: #1f1315;
    border: 1px solid rgba(239, 68, 68, 0.25);
  }
  :global(.dark-mode) .trap-chip:hover {
    background: #2b171a;
    border-color: #ef4444;
  }
  .trap-chip-title {
    font-size: 11px;
    color: #dc2626;
  }
  :global(.dark-mode) .trap-chip-title {
    color: #fca5a5;
  }
  .trap-chip-def {
    font-size: 10px;
    line-height: 1.35;
    color: #64748b;
  }
  :global(.dark-mode) .trap-chip-def {
    color: #94a3b8;
  }

  .probes-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .probe-card {
    border-radius: 5px;
    padding: 8px 10px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #e59b2c;
  }
  :global(.dark-mode) .probe-card {
    background: #18181b;
    border: 1px solid #27272a;
    border-left: 3px solid #f59e0b;
  }

  .probe-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 3px;
  }

  .rung-badge {
    border-radius: 3px;
    font-size: 8.5px;
    font-weight: 700;
    padding: 2px 5px;
    background: rgba(229, 155, 44, 0.15);
    color: #d97706;
  }
  :global(.dark-mode) .rung-badge {
    background: rgba(245, 158, 11, 0.2);
    color: #fde047;
  }

  .probe-rationale {
    font-size: 9px;
    font-style: italic;
    color: #64748b;
  }
  :global(.dark-mode) .probe-rationale {
    color: #94a3b8;
  }

  .probe-text {
    font-size: 11px;
    font-weight: 500;
    line-height: 1.4;
    margin: 2px 0 0;
    color: #1e293b;
  }
  :global(.dark-mode) .probe-text {
    color: #f1f5f9;
  }

  .roles-list p {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .role {
    border-radius: 99px;
    font-size: 8.5px;
    font-weight: 700;
    padding: 2px 6px;
    text-transform: uppercase;
    background: rgba(16, 185, 129, 0.12);
    color: #059669;
  }
  :global(.dark-mode) .role {
    color: #34d399;
  }
  .role.develops {
    background: rgba(59, 130, 246, 0.14);
    color: #2563eb;
  }
  :global(.dark-mode) .role.develops {
    color: #60a5fa;
  }
  .role.assesses {
    background: rgba(168, 85, 247, 0.14);
    color: #7c3aed;
  }
  :global(.dark-mode) .role.assesses {
    color: #c084fc;
  }

  .muted-text {
    font-size: 11px;
    color: #94a3b8;
    margin: 0;
  }

  @media (max-width: 768px) {
    .node-popup-drawer {
      top: auto;
      bottom: 0;
      left: 0;
      right: 0;
      width: 100%;
      max-width: 100%;
      max-height: 60vh;
      border-radius: 12px 12px 0 0;
    }
  }
</style>
