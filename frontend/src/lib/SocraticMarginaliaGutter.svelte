<script lang="ts">
  import InstructorInterventionCard from './marginalia/InstructorInterventionCard.svelte';
  import SocraticProbeCard from './marginalia/SocraticProbeCard.svelte';
  import type { SocraticProbe, InstructorIntervention } from './marginalia/marginaliaTypes';

  let {
    probes = [],
    interventions = [],
    documentBlocks = [],
    activeProbeId = '',
    focusedBlockId = '',
    focusedBlockOffsetTop = 0,
    onRespond = async () => null,
    onRespondIntervention = async () => null,
    onDismiss = async () => null,
    onDefer = async () => null,
    onSelectBlock = () => null,
    onEscalateToAgent = () => null,
    onAssumptionAction = async () => null,
    isBusy = false,
    notice = '',
  } = $props<{
    probes?: SocraticProbe[];
    interventions?: InstructorIntervention[];
    documentBlocks?: any[];
    activeProbeId?: string;
    focusedBlockId?: string;
    focusedBlockOffsetTop?: number;
    onRespond?: (probeId: string, text: string) => Promise<any>;
    onRespondIntervention?: (interventionId: string, text: string) => Promise<any>;
    onDismiss?: (probeId: string) => Promise<any>;
    onDefer?: (probeId: string) => Promise<any>;
    onSelectBlock?: (blockId: string) => void;
    onEscalateToAgent?: (probe: SocraticProbe) => void;
    onAssumptionAction?: (probe: SocraticProbe, action: string) => Promise<any>;
    isBusy?: boolean;
    notice?: string;
  }>();

  let containerEl = $state<HTMLElement | null>(null);

  let blockIndexMap = $derived.by(() => {
    const map = new Map<string, number>();
    (documentBlocks || []).forEach((b: any, idx: number) => {
      if (b.block_id) map.set(b.block_id, idx);
    });
    return map;
  });

  // Probes belonging to the currently focused paragraph
  let focusedBlockProbes = $derived.by(() => {
    if (!focusedBlockId) return [];
    return probes.filter((p) => p && p.status !== 'dismissed' && p.block_id === focusedBlockId);
  });

  // Visible probes: prioritize active focused paragraph at top, then status, then document reading order
  let visibleProbes = $derived.by(() => {
    const list = probes.filter((p) => p && p.status !== 'dismissed');
    return list.sort((a, b) => {
      // 1. Probes for the currently focused paragraph always float to the top
      if (focusedBlockId) {
        const aActive = a.block_id === focusedBlockId;
        const bActive = b.block_id === focusedBlockId;
        if (aActive && !bActive) return -1;
        if (!aActive && bActive) return 1;
      }

      // 2. Status: offered first, then deferred, then responded
      const order: Record<string, number> = { offered: 1, deferred: 2, responded: 3 };
      const statusDiff = (order[a.status] || 99) - (order[b.status] || 99);
      if (statusDiff !== 0) return statusDiff;

      // 3. Document reading order
      const aIdx = blockIndexMap.get(a.block_id || '') ?? 999;
      const bIdx = blockIndexMap.get(b.block_id || '') ?? 999;
      return aIdx - bIdx;
    });
  });

  let activeProbeCount = $derived(
    visibleProbes.filter((p) => p.status === 'offered').length
  );

  let activeInterventionCount = $derived(
    interventions.filter((i) => i.status === 'dispatched').length
  );

  // Auto-scroll the matching card into view inside the gutter without dislodging anything
  $effect(() => {
    if (focusedBlockId && containerEl) {
      const interventionCard = containerEl.querySelector(`[data-intervention-block-id="${focusedBlockId}"]`);
      if (interventionCard) {
        interventionCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        const card = containerEl.querySelector(`[data-probe-block-id="${focusedBlockId}"]`);
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }
    }
  });
</script>

<aside class="marginalia-gutter" bind:this={containerEl} aria-label="Socratic Marginalia Gutter">
  <div class="gutter-header">
    <div class="gutter-title">
      <span class="gutter-icon">🧠</span>
      <span>Socratic Marginalia</span>
    </div>
    <div class="gutter-header-pills">
      {#if activeInterventionCount > 0}
        <span class="intervention-count-pill" title="Targeted instructor feedback awaiting your reflection">
          👨‍🏫 {activeInterventionCount} {activeInterventionCount === 1 ? 'instructor nudge' : 'instructor nudges'}
        </span>
      {/if}
      {#if activeProbeCount > 0}
        <span class="probe-count-pill">{activeProbeCount} active</span>
      {:else if visibleProbes.length > 0}
        <span class="probe-count-pill subtle">All resolved</span>
      {/if}
    </div>
  </div>

  {#if notice}
    <div class="gutter-notice" role="status">
      <span>ℹ️</span> <span>{notice}</span>
    </div>
  {/if}

  <!-- Contextual status banner indicating current block alignment -->
  {#if focusedBlockId}
    <div class="focus-context-banner" class:has-probe={focusedBlockProbes.length > 0}>
      {#if focusedBlockProbes.length > 0}
        <span class="context-icon">🎯</span>
        <span class="context-text">
          {focusedBlockProbes.length === 1 ? '1 inquiry' : `${focusedBlockProbes.length} inquiries`} for active paragraph
        </span>
      {:else}
        <span class="context-icon">✍️</span>
        <span class="context-text">Active paragraph · No inquiries yet (state a claim or reason to prompt a Socratic nudge)</span>
      {/if}
    </div>
  {/if}

  <div class="gutter-stream">
    <!-- Instructor Interventions (High-Priority Cognitive Activities) -->
    {#if interventions.length > 0}
      {#each interventions as intervention (intervention.intervention_id)}
        <InstructorInterventionCard
          {intervention}
          isTargeted={Boolean(focusedBlockId && intervention.block_id === focusedBlockId)}
          {onSelectBlock}
          {onRespondIntervention}
        />
      {/each}
    {/if}

    <!-- Socratic Inquiries -->
    {#if visibleProbes.length > 0}
      {#each visibleProbes as probe (probe.probe_id)}
        <SocraticProbeCard
          {probe}
          isTargeted={(focusedBlockId && probe.block_id === focusedBlockId) || probe.probe_id === activeProbeId}
          {isBusy}
          {onSelectBlock}
          {onRespond}
          {onDefer}
          {onDismiss}
          {onEscalateToAgent}
          {onAssumptionAction}
        />
      {/each}
    {:else if interventions.length === 0}
      <div class="empty-gutter-state">
        <div class="empty-icon">💭</div>
        <p class="empty-text">Reasoning Gutter Clear</p>
        <span class="empty-subtext">No active Socratic inquiries or cognitive challenges at this stage. Keep writing or select a paragraph.</span>
      </div>
    {/if}
  </div>
</aside>

<style>
  .marginalia-gutter {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
  }

  .gutter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--color-graphite-border);
    flex-shrink: 0;
  }

  .gutter-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-slate-bright);
  }

  .gutter-icon { font-size: 1rem; }

  .gutter-header-pills {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .intervention-count-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    color: #92400e;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 999px;
    padding: 2px 8px;
  }

  :global([data-theme="dark"]) .intervention-count-pill {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border-color: rgba(245, 158, 11, 0.3);
  }

  .probe-count-pill {
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--color-aurora-glow, rgba(2, 132, 199, 0.15));
    color: var(--color-aurora, #0284c7);
    border: 1px solid rgba(2, 132, 199, 0.28);
    font-weight: 600;
  }

  .probe-count-pill.subtle {
    background: rgba(5, 150, 105, 0.12);
    color: var(--color-signal-green, #10b981);
    border-color: rgba(5, 150, 105, 0.25);
  }

  .gutter-notice {
    font-size: 0.8rem;
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(2, 132, 199, 0.08);
    border: 1px solid rgba(2, 132, 199, 0.2);
    color: var(--color-slate-light);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }

  .focus-context-banner {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.75rem;
    padding: 6px 10px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.03);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-subtle);
    margin-bottom: 12px;
    flex-shrink: 0;
    transition: all 0.2s ease;
  }

  :global([data-theme="dark"]) .focus-context-banner {
    background: rgba(255, 255, 255, 0.03);
  }

  .focus-context-banner.has-probe {
    background: rgba(2, 132, 199, 0.08);
    border-color: rgba(2, 132, 199, 0.28);
    color: var(--color-aurora, #0284c7);
    font-weight: 500;
  }

  .gutter-stream {
    display: flex;
    flex-direction: column;
    gap: 14px;
    flex: 1;
    min-height: 0;
  }

  .empty-gutter-state {
    padding: 32px 14px;
    text-align: center;
    background: rgba(0, 0, 0, 0.02);
    border: 1px dashed var(--color-graphite-border);
    border-radius: 8px;
    margin-top: 12px;
  }

  :global([data-theme="dark"]) .empty-gutter-state {
    background: rgba(255, 255, 255, 0.02);
  }

  .empty-icon { font-size: 1.8rem; margin-bottom: 8px; }
  .empty-text { font-size: 0.88rem; font-weight: 600; color: var(--color-slate-bright); margin: 0 0 6px 0; }
  .empty-subtext { font-size: 0.78rem; color: var(--color-slate-subtle); line-height: 1.4; display: block; }
</style>
