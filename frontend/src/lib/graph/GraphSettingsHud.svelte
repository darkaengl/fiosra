<script lang="ts">
  let {
    hudOpen = $bindable(false),
    theme = $bindable<'light' | 'dark'>('light'),
    activeTab = $bindable<'filters' | 'display' | 'forces'>('filters'),
    searchQuery = $bindable(''),
    focusMode = $bindable(false),
    focusDepth = $bindable(1),
    selectedConceptId = '',
    showKCs = $bindable(true),
    showMisconceptions = $bindable(true),
    showProbes = $bindable(true),
    showModules = $bindable(true),
    nodeSizeMultiplier = $bindable(1.1),
    linkThickness = $bindable(1.0),
    textSize = $bindable(10),
    showArrows = $bindable(true),
    showAllLabels = $bindable(true),
    centerGravity = $bindable(0.08),
    repulsion = $bindable(-260),
    linkDistance = $bindable(80),
    onRecenter,
    onReheat,
  } = $props<{
    hudOpen?: boolean;
    theme?: 'light' | 'dark';
    activeTab?: 'filters' | 'display' | 'forces';
    searchQuery?: string;
    focusMode?: boolean;
    focusDepth?: number;
    selectedConceptId?: string;
    showKCs?: boolean;
    showMisconceptions?: boolean;
    showProbes?: boolean;
    showModules?: boolean;
    nodeSizeMultiplier?: number;
    linkThickness?: number;
    textSize?: number;
    showArrows?: boolean;
    showAllLabels?: boolean;
    centerGravity?: number;
    repulsion?: number;
    linkDistance?: number;
    onRecenter?: () => void;
    onReheat?: () => void;
  }>();

  function toggleTheme(newTheme: 'light' | 'dark') {
    theme = newTheme;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('obsidian_graph_theme', newTheme);
    }
  }
</script>

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
      <button
        type="button"
        class="hud-toggle-btn"
        onclick={() => (hudOpen = !hudOpen)}
        aria-label="Toggle Controls"
      >
        {hudOpen ? '−' : '+'}
      </button>
    </div>
  </header>

  {#if hudOpen}
    <div class="hud-body">
      <!-- Tab navigation -->
      <nav class="hud-tabs">
        <button
          type="button"
          class="tab-btn"
          class:active={activeTab === 'filters'}
          onclick={() => (activeTab = 'filters')}
        >
          Filters
        </button>
        <button
          type="button"
          class="tab-btn"
          class:active={activeTab === 'display'}
          onclick={() => (activeTab = 'display')}
        >
          Display
        </button>
        <button
          type="button"
          class="tab-btn"
          class:active={activeTab === 'forces'}
          onclick={() => (activeTab = 'forces')}
        >
          Forces
        </button>
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
              <button
                type="button"
                class:on={focusDepth === 1}
                onclick={() => (focusDepth = 1)}
              >
                Direct links
              </button>
              <button
                type="button"
                class:on={focusDepth === 2}
                onclick={() => (focusDepth = 2)}
              >
                Two hops
              </button>
            </div>
            {#if !selectedConceptId}
              <p class="focus-hint">Click a node to focus on it.</p>
            {/if}
          {/if}
        </div>

        <!-- Color Groups / Toggles -->
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
        <button type="button" class="btn-hud" onclick={() => onRecenter?.()}>
          ⟲ Reset View
        </button>
        <button type="button" class="btn-hud" onclick={() => onReheat?.()}>
          ⚡ Reheat
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .obsidian-hud {
    position: absolute;
    top: 14px;
    right: 14px;
    z-index: 10;
    width: 280px;
    background: rgba(255, 255, 255, 0.94);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(0, 0, 0, 0.12);
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-size: 11.5px;
    color: #0f172a;
    transition: width 0.2s ease, box-shadow 0.2s ease;
  }

  :global(.dark-mode) .obsidian-hud {
    background: rgba(24, 24, 28, 0.9);
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5);
    color: #f1f5f9;
  }

  .obsidian-hud.collapsed {
    width: auto;
  }

  .hud-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    gap: 8px;
  }

  :global(.dark-mode) .hud-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .hud-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    font-size: 11.5px;
  }

  .hud-icon {
    font-size: 11px;
    color: #2563eb;
  }

  .hud-header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .theme-toggle-group {
    display: flex;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
    padding: 2px;
  }

  :global(.dark-mode) .theme-toggle-group {
    background: rgba(255, 255, 255, 0.08);
  }

  .theme-btn {
    border: none;
    background: transparent;
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    cursor: pointer;
    color: #64748b;
  }

  :global(.dark-mode) .theme-btn {
    color: #94a3b8;
  }

  .theme-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  :global(.dark-mode) .theme-btn.active {
    background: #27272a;
    color: #ffffff;
  }

  .hud-toggle-btn {
    border: none;
    background: transparent;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    color: #64748b;
    padding: 0 4px;
    line-height: 1;
  }

  .hud-body {
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 480px;
    overflow-y: auto;
  }

  .hud-tabs {
    display: flex;
    gap: 4px;
    background: rgba(0, 0, 0, 0.04);
    padding: 2px;
    border-radius: 4px;
  }

  :global(.dark-mode) .hud-tabs {
    background: rgba(255, 255, 255, 0.06);
  }

  .tab-btn {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 10px;
    font-weight: 600;
    padding: 3px 0;
    border-radius: 3px;
    cursor: pointer;
    color: #64748b;
    text-align: center;
    transition: all 0.15s ease;
  }

  .tab-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }

  :global(.dark-mode) .tab-btn.active {
    background: #27272a;
    color: #ffffff;
  }

  .hud-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .hud-section label,
  .section-label {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
    letter-spacing: 0.4px;
  }

  .hud-section input[type="text"] {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    padding: 4px 7px;
    font-size: 11px;
    color: inherit;
    outline: none;
  }

  :global(.dark-mode) .hud-section input[type="text"] {
    background: #18181b;
    border-color: rgba(255, 255, 255, 0.15);
  }

  .toggle-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .checkbox-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-size: 10.5px;
  }

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }

  .kc-dot { background: #5c5c5c; }
  .misc-dot { background: #e05252; }
  .probe-dot { background: #e59b2c; }
  .module-dot { background: #242424; }

  :global(.dark-mode) .kc-dot { background: #a1a1aa; }
  :global(.dark-mode) .misc-dot { background: #ef5350; }
  :global(.dark-mode) .probe-dot { background: #f59e0b; }
  :global(.dark-mode) .module-dot { background: #f4f4f5; }

  .focus-depth {
    display: flex;
    gap: 4px;
    margin-top: 4px;
  }

  .focus-depth button {
    font-size: 9.5px;
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: transparent;
    padding: 2px 6px;
    border-radius: 3px;
    cursor: pointer;
  }

  .focus-depth button.on {
    background: #2563eb;
    color: #ffffff;
    border-color: #2563eb;
  }

  .focus-hint {
    font-size: 9.5px;
    color: #94a3b8;
    margin: 2px 0 0;
  }

  .slider-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 10.5px;
    gap: 8px;
  }

  .slider-row input[type="range"] {
    flex: 1;
    max-width: 120px;
    accent-color: #2563eb;
  }

  .checkbox-row {
    font-size: 10.5px;
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
  }

  .hud-actions {
    display: flex;
    gap: 6px;
    margin-top: 4px;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
    padding-top: 8px;
  }

  :global(.dark-mode) .hud-actions {
    border-top: 1px solid rgba(255, 255, 255, 0.06);
  }

  .btn-hud {
    flex: 1;
    font-size: 10.5px;
    font-weight: 600;
    padding: 4px 6px;
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    background: rgba(0, 0, 0, 0.03);
    color: inherit;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-hud:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  :global(.dark-mode) .btn-hud {
    border-color: rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
  }

  :global(.dark-mode) .btn-hud:hover {
    background: rgba(255, 255, 255, 0.1);
  }
</style>
