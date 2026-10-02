<script>
  import ThinkingTimeline from '../ThinkingTimeline.svelte';

  let {
    sessionId = '',
    reasoningNodes = [],
    activityNodes = [],
  } = $props();

  let activeReviewTimelineTab = $state('reasoning'); // 'reasoning' | 'activity'
  let expandedReasoningNode = $state(-1);
  let expandedActivityNode = $state(-1);
</script>

<div class="trace-inspector">
  <div class="trace-sub-toolbar">
    <div class="trace-toggle-buttons">
      <button
        type="button"
        class="btn-trace-sub"
        class:active={activeReviewTimelineTab === 'reasoning'}
        onclick={() => (activeReviewTimelineTab = 'reasoning')}
      >
        Milestones ({reasoningNodes.length})
      </button>
      <button
        type="button"
        class="btn-trace-sub"
        class:active={activeReviewTimelineTab === 'activity'}
        onclick={() => (activeReviewTimelineTab = 'activity')}
      >
        Log ({activityNodes.length})
      </button>
    </div>
    <a
      class="btn-flight-recorder"
      href={`#/student/trace?session_id=${sessionId}`}
      target="_blank"
      rel="noopener noreferrer"
    >
      Recorder ↗
    </a>
  </div>

  <div class="trace-timeline-area">
    {#if activeReviewTimelineTab === 'reasoning'}
      {#if reasoningNodes.length === 0}
        <p class="tab-empty-msg">
          No reasoning milestones logged yet.
        </p>
      {:else}
        <ThinkingTimeline
          nodes={reasoningNodes}
          expandedNodeIndex={expandedReasoningNode}
          onToggleNode={(idx) => {
            expandedReasoningNode =
              expandedReasoningNode === idx ? -1 : idx;
          }}
        />
      {/if}
    {:else if activityNodes.length === 0}
      <p class="tab-empty-msg">No activity events logged.</p>
    {:else}
      <ThinkingTimeline
        nodes={activityNodes}
        expandedNodeIndex={expandedActivityNode}
        onToggleNode={(idx) => {
          expandedActivityNode =
            expandedActivityNode === idx ? -1 : idx;
        }}
      />
    {/if}
  </div>
</div>

<style>
  .trace-inspector {
    display: flex;
    flex-direction: column;
  }

  .trace-sub-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--color-graphite-border, #cbd5e1);
    margin-bottom: 10px;
    gap: 6px;
  }

  .trace-toggle-buttons {
    display: flex;
    gap: 4px;
  }

  .btn-trace-sub {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #cbd5e1);
    border-radius: 4px;
    color: var(--color-slate-muted, #64748b);
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 6px;
    cursor: pointer;
  }

  .btn-trace-sub.active {
    background: rgba(217, 119, 6, 0.12);
    border-color: rgba(217, 119, 6, 0.35);
    color: #92400e;
  }

  .btn-flight-recorder {
    background: #ecfdf5;
    border: 1px solid rgba(5, 150, 105, 0.25);
    border-radius: 4px;
    color: #065f46;
    font-size: 10.5px;
    font-weight: 600;
    padding: 3px 6px;
    text-decoration: none;
  }

  .trace-timeline-area {
    display: flex;
    flex-direction: column;
  }

  .tab-empty-msg {
    color: var(--color-slate-muted, #94a3b8);
    font-size: 11.5px;
    font-style: italic;
    text-align: center;
    padding: 24px 8px;
  }
</style>
