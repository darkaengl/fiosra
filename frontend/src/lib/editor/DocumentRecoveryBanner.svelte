<script lang="ts">
  let {
    recoverySnapshot = null,
    onRestore = () => {},
    onDiscard = () => {},
  } = $props<{
    recoverySnapshot: any;
    onRestore?: () => void;
    onDiscard?: () => void;
  }>();
</script>

{#if recoverySnapshot}
  <aside class="document-recovery-banner" role="status">
    <div>
      <strong>Unsaved local draft found</strong>
      <p>
        A copy from {new Date(recoverySnapshot.savedAt).toLocaleString()} is stored on this device.
        Restore it only if it is the version you want to save.
      </p>
    </div>
    <div class="document-recovery-actions">
      <button type="button" class="recovery-restore-btn" onclick={onRestore}>Restore local draft</button>
      <button type="button" class="recovery-discard-btn" onclick={onDiscard}>Discard copy</button>
    </div>
  </aside>
{/if}

<style>
  .document-recovery-banner {
    width: min(var(--canvas-width, 820px), 100%);
    margin: 0 auto 12px;
    border: 1px solid #f0c36d;
    background: #fffbeb;
    border-radius: 8px;
    padding: 12px 14px;
    color: #78350f;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .document-recovery-banner strong {
    font-size: 12px;
  }

  .document-recovery-banner p {
    margin: 3px 0 0;
    font-size: 11px;
    line-height: 1.35;
  }

  .document-recovery-actions {
    display: flex;
    flex: 0 0 auto;
    gap: 12px;
    font-size: 11px;
  }

  .recovery-restore-btn,
  .recovery-discard-btn {
    border: 0;
    background: transparent;
    font: inherit;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .recovery-restore-btn {
    color: #1d4ed8;
    font-weight: 700;
  }

  .recovery-discard-btn {
    color: #78350f;
  }
</style>
