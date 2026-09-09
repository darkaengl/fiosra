<script>
  import Modal from './Modal.svelte';

  let {
    isOpen = false,
    courseId = '',
    nextPosition = 1,
    onClose,
    onSuccess,
  } = $props();

  let title = $state('');
  let description = $state('');
  let objectivesRaw = $state('');
  let isSubmitting = $state(false);
  let feedbackMessage = $state('');

  $effect(() => {
    if (isOpen) {
      title = '';
      description = '';
      objectivesRaw = '';
      feedbackMessage = '';
    }
  });

  async function handleSubmit(e) {
    e.preventDefault();
    if (!courseId || !title.trim()) return;

    isSubmitting = true;
    feedbackMessage = '';

    const objectives = objectivesRaw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const res = await fetch(`/courses/${courseId}/modules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim() || null,
          learning_objectives: objectives,
          position: nextPosition,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned HTTP ${res.status}`);
      }

      onSuccess?.();
      onClose?.();
    } catch (err) {
      feedbackMessage = err.message || 'Failed to add module.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<Modal {isOpen} title="🗺️ Add Curriculum Unit Module" width="580px" {onClose}>
  <p class="modal-intro">
    Define a new sequential learning unit. Modules anchor student reasoning tasks, track prerequisite knowledge components, and unlock downstream concepts in Neo4j.
  </p>

  <form onsubmit={handleSubmit} class="module-form">
    <div class="field-group">
      <label for="mod-title">Module Title <span style="color: var(--color-rose);">*</span></label>
      <input
        id="mod-title"
        type="text"
        bind:value={title}
        placeholder="e.g. Unit 01: The Indus Valley Civilization &amp; Early Urban Planning"
        required
      />
    </div>

    <div class="field-group">
      <label for="mod-desc">Pedagogical Scope &amp; Summary</label>
      <textarea
        id="mod-desc"
        rows="3"
        bind:value={description}
        placeholder="Core historical concepts, primary sources to analyze, and prerequisite dependencies..."
      ></textarea>
    </div>

    <div class="field-group">
      <label for="mod-obj">Learning Objectives (comma-separated)</label>
      <input
        id="mod-obj"
        type="text"
        bind:value={objectivesRaw}
        placeholder="e.g. Analyze urban sanitation, Evaluate trade routes, Contrast Harappan seals"
      />
    </div>

    {#if feedbackMessage}
      <div class="feedback-banner error">
        {feedbackMessage}
      </div>
    {/if}

    <div class="form-actions">
      <button type="button" class="btn btn-secondary" onclick={onClose}>
        Cancel
      </button>
      <button type="submit" class="btn btn-primary" disabled={isSubmitting}>
        <span>{isSubmitting ? '⏳ Writing to Neo4j & PostgreSQL...' : '+ Add Unit to Curriculum'}</span>
      </button>
    </div>
  </form>
</Modal>

<style>
  .modal-intro {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.5;
  }

  .module-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  label {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-light);
  }

  input[type='text'],
  textarea {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    color: #fff;
    padding: 10px 14px;
    border-radius: var(--radius-sm);
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s ease;
  }

  input:focus,
  textarea:focus {
    border-color: var(--color-horizon-bright);
  }

  .feedback-banner.error {
    font-size: 12px;
    padding: 8px 12px;
    border-radius: var(--radius-xs);
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 16px;
  }
</style>
