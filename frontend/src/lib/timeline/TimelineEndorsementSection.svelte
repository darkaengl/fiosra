<script lang="ts">
  let { onExport = () => {} } = $props<{ onExport?: () => void }>();
</script>

<section class="endorsement-section">
  <div class="endorsement-card">
    <div class="endorsement-header">
      <div class="endorser-info">
        <div class="faculty-avatar">DV</div>
        <div>
          <h3 class="faculty-name">Dr. Vance • Department of History</h3>
          <p class="faculty-title">Longitudinal Epistemic Assessment & Endorsement</p>
        </div>
      </div>
      <div class="crypto-seal">
        <span class="seal-icon">🔏</span>
        <span>Cryptographically Endorsed</span>
      </div>
    </div>

    <blockquote class="endorsement-body">
      "Elena demonstrated exceptional conceptual maturity during her reasoning progression across the French Revolutionary fiscal inquiries. When initially tempted by the moralized 'luxury spending' trope, she autonomously revised her claim upon inspecting Necker's Compte Rendu data, framing the crisis around systemic debt servicing and fiscal exemption. Her reasoning trace reflects authentic scholarly discipline and genuine independent synthesis."
    </blockquote>

    <div class="endorsement-footer">
      <div class="proof-hash">
        <span>Evidence Packet: Z-HIST201-STU081-REV24</span>
        <span class="hash-bullet">•</span>
        <span>Verified via AAAI-2026 AutoSCORE Protocol</span>
      </div>
      <button type="button" class="btn btn-secondary" onclick={onExport} style="font-size: 12px; padding: 6px 14px;">
        📄 Export W3C Verifiable Credential
      </button>
    </div>
  </div>
</section>

<style>
  .endorsement-section {
    margin-top: 8px;
  }

  .endorsement-card {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    padding: 26px 30px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    box-shadow: var(--shadow-sm);
  }

  .endorsement-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .endorser-info {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .faculty-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: var(--color-obsidian);
    border: 1.5px solid var(--color-horizon-bright);
    color: var(--color-horizon-bright);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
  }

  .faculty-name {
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
  }

  .faculty-title {
    font-size: 11.5px;
    color: var(--color-slate-muted);
    margin: 2px 0 0;
  }

  .crypto-seal {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-signal-green);
    background: var(--color-signal-green-bg);
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 4px 10px;
    border-radius: var(--radius-full);
  }

  .endorsement-body {
    font-family: var(--font-serif, "Newsreader", Georgia, serif);
    font-size: 14.5px;
    line-height: 1.6;
    color: var(--color-slate-bright);
    font-style: italic;
    margin: 0;
    padding: 12px 18px;
    background: var(--color-obsidian);
    border-left: 3px solid var(--color-horizon-blue);
    border-radius: var(--radius-xs);
  }

  .endorsement-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    font-size: 11px;
    color: var(--color-slate-muted);
    padding-top: 10px;
    border-top: 1px solid var(--color-graphite-border);
    flex-wrap: wrap;
  }

  .proof-hash {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .hash-bullet {
    color: var(--color-slate-subtle);
  }

  .btn {
    border-radius: var(--radius-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid transparent;
  }

  .btn-secondary {
    background: var(--color-graphite);
    border-color: var(--color-graphite-border);
    color: var(--color-slate-bright);
  }
  .btn-secondary:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }
</style>
