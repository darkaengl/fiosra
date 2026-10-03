<script lang="ts">
  import Modal from '../Modal.svelte';

  let {
    isOpen = false,
    onClose = () => {},
  } = $props<{
    isOpen?: boolean;
    onClose?: () => void;
  }>();
</script>

<Modal {isOpen} title="📄 Ground course materials" {onClose}>
  <p class="modal-desc">
    Materials must be attached to a curriculum module so their provenance is visible in assignment design. Create or open a course, add a module, and use <strong>Ingest Material</strong> from that module.
  </p>
  <div class="pipeline-preview">
    <div class="pipeline-title">What grounding records</div>
    <div class="pipeline-step"><span>1. The selected course and module</span><span class="step-ok">Required</span></div>
    <div class="pipeline-step"><span>2. Source title, excerpt, and link when supplied</span><span class="step-ok">Visible to educators</span></div>
    <div class="pipeline-step"><span>3. Knowledge-component mapping when available</span><span class="step-ok">Reviewable</span></div>
  </div>
  <div class="modal-footer">
    <button type="button" class="btn btn-secondary" onclick={onClose}>Cancel</button>
    <a href="#/modules" class="btn btn-primary" onclick={onClose}>Open curriculum</a>
  </div>
</Modal>

<style>
  .modal-desc {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.5;
    margin: 0 0 20px;
  }

  .pipeline-preview {
    background: var(--pill-bg);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 14px;
    font-size: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .pipeline-title {
    font-weight: 600;
    color: var(--color-heading);
  }

  .pipeline-step {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--color-slate-light);
  }

  .step-ok {
    color: var(--color-signal-green);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 16px;
  }
</style>
