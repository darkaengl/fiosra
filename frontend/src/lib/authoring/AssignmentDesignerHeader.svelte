<script lang="ts">
  let {
    courseId,
    course,
    moduleId = $bindable(),
    contract,
    viewMode = $bindable('editor'),
    isProposing = false,
    isSaving = false,
    draft = null,
    onPropose = () => {},
    onSave = () => {},
    onPublish = () => {},
  } = $props<{
    courseId: string;
    course: any;
    moduleId: string;
    contract: any;
    viewMode: 'editor' | 'preview' | 'pdf';
    isProposing?: boolean;
    isSaving?: boolean;
    draft?: any;
    onPropose?: () => void;
    onSave?: () => void;
    onPublish?: () => void;
  }>();
</script>

<header class="top-nav-bar">
  <div class="nav-left">
    <a href={`#/modules?course_id=${encodeURIComponent(courseId)}`} class="back-link" title="Return to course modules">
      ← Modules
    </a>
    <div class="divider"></div>
    <div class="title-group">
      <span class="studio-badge">Assignment Studio</span>
      <h1 class="course-name">{course?.title || 'Course'}</h1>
    </div>
    <div class="unit-selector-wrapper">
      <label for="module-select" class="unit-label">Unit:</label>
      <select
        id="module-select"
        class="unit-select"
        bind:value={moduleId}
        onchange={() => {
          const mod = course?.modules?.find((m: any) => String(m.module_id) === String(moduleId));
          if (mod && contract) {
            contract.task.scope = `Chronological and institutional boundaries of Unit ${mod.position}: ${mod.title}`;
          }
        }}
      >
        {#each (course?.modules || []).slice().sort((a: any, b: any) => a.position - b.position) as mod}
          <option value={mod.module_id}>Unit {mod.position}: {mod.title}</option>
        {/each}
      </select>
    </div>
  </div>

  <!-- Mode Switcher Pills: Editor | Student Preview | PDF Sheet -->
  <div class="mode-switch-pills" role="tablist">
    <button
      type="button"
      role="tab"
      class:active={viewMode === 'editor'}
      onclick={() => viewMode = 'editor'}
    >
      <span>✏️</span> Designer
    </button>
    <button
      type="button"
      role="tab"
      class:active={viewMode === 'preview'}
      onclick={() => viewMode = 'preview'}
    >
      <span>👁️</span> Student Canvas
    </button>
    <button
      type="button"
      role="tab"
      class:active={viewMode === 'pdf'}
      onclick={() => viewMode = 'pdf'}
    >
      <span>📄</span> Printable PDF Sheet
    </button>
  </div>

  <!-- Actions -->
  <div class="nav-actions">
    <button
      type="button"
      class="btn-ai-draft"
      disabled={isProposing || !moduleId}
      onclick={onPropose}
      title="Synthesize task prompt, primary source pack, and rubric with AI"
    >
      <span class="sparkle {isProposing ? 'pulsing' : ''}">✦</span>
      {isProposing ? 'Drafting…' : 'Draft with AI'}
    </button>

    <button
      type="button"
      class="btn-secondary"
      disabled={!contract || isSaving}
      onclick={onSave}
    >
      {isSaving ? 'Saving…' : draft ? 'Save Changes' : 'Save Draft'}
    </button>

    <button
      type="button"
      class="btn-primary"
      disabled={!contract || isSaving || draft?.status === 'published'}
      onclick={onPublish}
    >
      {draft?.status === 'published' ? '✓ Published' : '🚀 Publish'}
    </button>

    {#if draft?.status === 'published' && draft?.assignment_id}
      <button
        type="button"
        class="btn-student-live"
        title="Preview student reasoning canvas inside Studio"
        onclick={() => viewMode = 'preview'}
      >
        👁️ Preview Student View
      </button>
    {/if}
  </div>
</header>

<style>
  .top-nav-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    backdrop-filter: blur(14px);
    background: rgba(255, 255, 255, 0.92);
    border-bottom: 1px solid #d0d7de;
    transition: background 0.2s ease, border-color 0.2s ease;
  }

  :global(.dark-mode) .top-nav-bar {
    background: rgba(13, 17, 23, 0.9);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .nav-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .back-link {
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    color: #57606a;
    transition: color 0.15s;
  }
  .back-link:hover { color: #0969da; }

  :global(.dark-mode) .back-link { color: #8b949e; }
  :global(.dark-mode) .back-link:hover { color: #58a6ff; }

  .divider {
    width: 1px;
    height: 22px;
    background: #d0d7de;
  }
  :global(.dark-mode) .divider { background: rgba(255, 255, 255, 0.1); }

  .title-group {
    display: flex;
    flex-direction: column;
  }

  .studio-badge {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: #6366f1;
  }
  :global(.dark-mode) .studio-badge { color: #a5b4fc; }

  .course-name {
    font-size: 14px;
    font-weight: 700;
    margin: 0;
    color: #1f2328;
  }
  :global(.dark-mode) .course-name { color: #f0f6fc; }

  .unit-selector-wrapper {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: 12px;
  }

  .unit-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: #57606a;
  }
  :global(.dark-mode) .unit-label { color: #8b949e; }

  .unit-select {
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 8px;
    outline: none;
    cursor: pointer;
    background: #ffffff;
    border: 1px solid #d0d7de;
    color: #0969da;
  }
  :global(.dark-mode) .unit-select {
    background: #161b22;
    border: 1px solid #30363d;
    color: #58a6ff;
  }

  .mode-switch-pills {
    display: flex;
    border-radius: 8px;
    padding: 3px;
    gap: 4px;
    background: #eaeef2;
    border: 1px solid #d0d7de;
  }
  :global(.dark-mode) .mode-switch-pills {
    background: #161b22;
    border: 1px solid #30363d;
  }

  .mode-switch-pills button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    color: #57606a;
    transition: all 0.15s ease;
  }
  .mode-switch-pills button:hover { color: #1f2328; }
  .mode-switch-pills button.active {
    background: #0969da;
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  }
  :global(.dark-mode) .mode-switch-pills button { color: #8b949e; }
  :global(.dark-mode) .mode-switch-pills button:hover { color: #f0f6fc; }
  :global(.dark-mode) .mode-switch-pills button.active {
    background: #238636;
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  }

  .nav-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .btn-ai-draft {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 700;
    padding: 7px 14px;
    cursor: pointer;
    transition: all 0.15s ease;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
  }
  .btn-ai-draft:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
  }
  .btn-ai-draft:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .sparkle.pulsing {
    animation: pulse 1s infinite alternate;
  }
  @keyframes pulse {
    from { opacity: 0.4; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1.15); }
  }

  .btn-secondary {
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 13px;
    cursor: pointer;
    transition: all 0.15s;
    background: #ffffff;
    border: 1px solid #d0d7de;
    color: #24292f;
  }
  .btn-secondary:hover:not(:disabled) {
    background: #f3f4f6;
  }
  :global(.dark-mode) .btn-secondary {
    background: #21262d;
    border: 1px solid #30363d;
    color: #c9d1d9;
  }
  :global(.dark-mode) .btn-secondary:hover:not(:disabled) {
    background: #30363d;
    color: #f0f6fc;
  }

  .btn-primary {
    background: #0969da;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 6px;
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 700;
    padding: 7px 15px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-primary:hover:not(:disabled) {
    background: #1158c7;
  }

  .btn-student-live {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #1a7f37;
    color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 700;
    padding: 7px 14px;
    text-decoration: none;
    transition: all 0.15s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  }
  .btn-student-live:hover {
    background: #1f883d;
    box-shadow: 0 2px 8px rgba(26, 127, 55, 0.35);
  }
</style>
