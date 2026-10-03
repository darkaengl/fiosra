<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    sourcesWidth = $bindable(480),
    gutterWidth = $bindable(440),
    isSourcesCollapsed = false,
    isGutterCollapsed = false,
    sources,
    canvas,
    gutter,
  } = $props<{
    sourcesWidth?: number;
    gutterWidth?: number;
    isSourcesCollapsed?: boolean;
    isGutterCollapsed?: boolean;
    sources: Snippet;
    canvas: Snippet;
    gutter: Snippet;
  }>();

  let isResizingLeft = $state(false);
  let isResizingRight = $state(false);

  function startResizeLeft(e: MouseEvent | PointerEvent) {
    e.preventDefault();
    isResizingLeft = true;
    const startX = e.clientX;
    const startWidth = sourcesWidth;

    function onPointerMove(moveEvent: MouseEvent | PointerEvent) {
      const deltaX = moveEvent.clientX - startX;
      const maxAllowed = Math.max(300, window.innerWidth - 450);
      const newWidth = Math.min(maxAllowed, Math.max(260, startWidth + deltaX));
      sourcesWidth = Math.round(newWidth);
    }

    function onPointerUp() {
      isResizingLeft = false;
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      try {
        localStorage.setItem('fiosra_sources_width', String(sourcesWidth));
      } catch {}
    }

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  }

  function startResizeRight(e: MouseEvent | PointerEvent) {
    e.preventDefault();
    isResizingRight = true;
    const startX = e.clientX;
    const startWidth = gutterWidth;

    function onPointerMove(moveEvent: MouseEvent | PointerEvent) {
      const deltaX = startX - moveEvent.clientX;
      const maxAllowed = Math.max(300, window.innerWidth - 450);
      const newWidth = Math.min(maxAllowed, Math.max(260, startWidth + deltaX));
      gutterWidth = Math.round(newWidth);
    }

    function onPointerUp() {
      isResizingRight = false;
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      try {
        localStorage.setItem('fiosra_gutter_width', String(gutterWidth));
      } catch {}
    }

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  }
</script>

<div
  class="in-situ-workbench-grid"
  class:sources-collapsed={isSourcesCollapsed}
  class:sources-expanded={!isSourcesCollapsed}
  class:gutter-collapsed={isGutterCollapsed}
  class:gutter-open={!isGutterCollapsed}
  class:is-resizing={isResizingLeft || isResizingRight}
  style="--sources-width: {isSourcesCollapsed ? '48px' : `${sourcesWidth}px`}; --gutter-width: {isGutterCollapsed ? '44px' : `${gutterWidth}px`};"
>
  <!-- Zone 1: Primary Source Exhibits / Evidentiary Well -->
  <div
    class="workbench-col-sources"
    class:collapsed={isSourcesCollapsed}
    class:expanded={!isSourcesCollapsed}
    class:no-transition={isResizingLeft}
    style="width: var(--sources-width);"
  >
    {@render sources()}
  </div>

  <!-- Left Margin Slider (Draggable Split-Resizer) -->
  {#if !isSourcesCollapsed}
    <div
      class="workbench-resizer-handle resizer-left"
      class:is-dragging={isResizingLeft}
      onpointerdown={startResizeLeft}
      ondblclick={() => sourcesWidth = 480}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize left sources sidebar"
      title="Drag to resize sources sidebar (Double-click to reset to 480px)"
    >
      <div class="resizer-knob"></div>
    </div>
  {/if}

  <!-- Zone 2: Structured Reasoning Canvas -->
  <main class="workbench-col-canvas">
    {@render canvas()}
  </main>

  <!-- Right Margin Slider (Draggable Split-Resizer) -->
  {#if !isGutterCollapsed}
    <div
      class="workbench-resizer-handle resizer-right"
      class:is-dragging={isResizingRight}
      onpointerdown={startResizeRight}
      ondblclick={() => gutterWidth = 440}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize right AI tutor sidebar"
      title="Drag to resize AI tutor sidebar (Double-click to reset to 440px)"
    >
      <div class="resizer-knob"></div>
    </div>
  {/if}

  <!-- Zone 3: Socratic Gutter (Marginalia + Agent + Reasoning + Activity) -->
  <div
    class="workbench-col-gutter"
    class:collapsed={isGutterCollapsed}
    class:no-transition={isResizingRight}
    style="width: var(--gutter-width);"
  >
    {@render gutter()}
  </div>
</div>

<style>
  .in-situ-workbench-grid {
    display: flex;
    flex-direction: row;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    position: relative;
  }

  .in-situ-workbench-grid.is-resizing {
    user-select: none !important;
    cursor: col-resize !important;
  }

  .in-situ-workbench-grid.is-resizing :global(*) {
    user-select: none !important;
    pointer-events: none !important;
  }

  .in-situ-workbench-grid.is-resizing .workbench-resizer-handle {
    pointer-events: auto !important;
  }

  .workbench-col-sources {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    flex-grow: 0;
    transition: width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .workbench-col-sources.no-transition {
    transition: none !important;
  }

  .workbench-col-sources.collapsed {
    width: 48px;
  }

  .workbench-col-canvas {
    flex: 1 1 0;
    min-width: 320px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    position: relative;
    background: var(--color-obsidian, #f8f8f5);
  }

  .workbench-col-gutter {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    flex-grow: 0;
    position: relative;
    transition: width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .workbench-col-gutter.no-transition {
    transition: none !important;
  }

  .workbench-col-gutter.collapsed {
    width: 44px;
  }

  /* Resizer Handles (Margin Sliders) */
  .workbench-resizer-handle {
    width: 10px;
    margin: 0 -5px;
    height: 100%;
    cursor: col-resize;
    position: relative;
    z-index: 30;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    user-select: none;
    touch-action: none;
  }

  .workbench-resizer-handle::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 4px;
    width: 2px;
    background: var(--color-graphite-border, #e2e4dc);
    transition: all 0.15s ease;
  }

  .workbench-resizer-handle:hover::before,
  .workbench-resizer-handle.is-dragging::before {
    background: #2563eb;
    width: 3px;
    left: 3.5px;
    box-shadow: 0 0 8px rgba(37, 99, 235, 0.4);
  }

  .resizer-knob {
    width: 4px;
    height: 36px;
    border-radius: 4px;
    background: var(--color-slate-muted, #94a3b8);
    opacity: 0;
    transition: opacity 0.15s ease, background 0.15s ease, height 0.15s ease;
    z-index: 2;
  }

  .workbench-resizer-handle:hover .resizer-knob,
  .workbench-resizer-handle.is-dragging .resizer-knob {
    opacity: 1;
    background: #2563eb;
    height: 52px;
  }

  @media (max-width: 1200px) {
    .workbench-col-sources {
      display: none;
    }
    .resizer-left {
      display: none !important;
    }
  }

  @media (max-width: 860px) {
    .workbench-col-gutter {
      display: none;
    }
    .resizer-right {
      display: none !important;
    }
  }
</style>
