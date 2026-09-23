<script>
  let { variant = "application" } = $props();

  const FIOSRA_LOCKUP_URL = "/fiosra-lockup.png";
  const ATU_LOGO_URL = "/atu-logo.png";

  let isPublic = $derived(variant === "public");
</script>

<footer class="institutional-footer" class:public-variant={isPublic}>
  <div class="footer-container">
    <div class="footer-brand-side">
      <img
        src={FIOSRA_LOCKUP_URL}
        alt="Fiosra · Learning in Motion"
        class="footer-logo"
      />
      <p class="footer-tagline">
        Make the thinking between first draft and final work visible.
      </p>
      <p class="footer-subtext">
        Structured learning environments for context-rich work, considered exploration, and meaningful development.
      </p>
    </div>

    <div class="footer-institution-side">
      <div class="institution-meta">
        <span class="institution-label">Academic Partnership</span>
        <strong class="institution-name">Atlantic Technological University</strong>
        <span class="institution-note">Pedagogical Evaluation & Reasoning Prototype</span>
      </div>
      <img
        src={ATU_LOGO_URL}
        alt="Atlantic Technological University"
        class="institution-logo"
      />
    </div>
  </div>
  
  <div class="footer-legal-bar">
    <div class="legal-inner">
      <span>© {new Date().getFullYear()} Fiosra Architecture · Principles of Marketing (BUS C150)</span>
      <span class="legal-separator">•</span>
      <span>Signals provide an invitation to consider, not a judgement about a learner.</span>
    </div>
  </div>
</footer>

<style>
  .institutional-footer {
    border-top: 1px solid var(--color-graphite-border, #e2e4dc);
    background: var(--m-color-bone, #F6F5F1);
    color: var(--m-color-slate, #6D7378);
    font-family: var(--font-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    margin-top: auto;
    transition: background-color 0.2s ease, border-color 0.2s ease;
  }

  .footer-container {
    max-width: 1140px;
    margin: 0 auto;
    padding: 32px 24px;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 24px;
  }

  .footer-brand-side {
    max-width: 480px;
  }

  .footer-logo {
    height: 32px;
    width: auto;
    object-fit: contain;
    display: block;
    margin-bottom: 8px;
  }

  .footer-tagline {
    font-size: 13px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
    margin: 6px 0 2px;
  }

  .footer-subtext {
    font-size: 11px;
    color: var(--m-color-slate, #6D7378);
    line-height: 1.45;
    margin: 0;
  }

  .footer-institution-side {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .institution-meta {
    display: flex;
    flex-direction: column;
    text-align: right;
    gap: 2px;
  }

  .institution-label {
    font-size: 9px;
    font-family: var(--font-mono, monospace);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--m-color-horizon-blue, #4F6BFF);
    font-weight: 600;
  }

  .institution-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--m-color-obsidian, #111315);
  }

  .institution-note {
    font-size: 10px;
    color: var(--m-color-slate-light, #8A9096);
  }

  .institution-logo {
    height: 38px;
    width: auto;
    max-width: 140px;
    object-fit: contain;
  }

  .footer-legal-bar {
    border-top: 1px solid rgba(0, 0, 0, 0.06);
    padding: 12px 24px;
    font-size: 10.5px;
    color: var(--m-color-slate, #6D7378);
    background: rgba(0, 0, 0, 0.02);
  }

  .legal-inner {
    max-width: 1140px;
    margin: 0 auto;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  .legal-separator {
    opacity: 0.4;
  }

  :global([data-theme="dark"]) .institutional-footer {
    background: #15181c;
    border-top-color: #272c34;
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .footer-logo,
  :global([data-theme="dark"]) .institution-logo {
    filter: brightness(0) invert(1);
    opacity: 0.9;
  }

  :global([data-theme="dark"]) .footer-tagline,
  :global([data-theme="dark"]) .institution-name {
    color: #f1f5f9;
  }

  :global([data-theme="dark"]) .footer-legal-bar {
    border-top-color: rgba(255, 255, 255, 0.05);
    background: rgba(0, 0, 0, 0.25);
  }
</style>
