<script lang="ts">
  let { lockupUrl = "./fiosra-lockup.png" } = $props<{ lockupUrl?: string }>();
</script>

<header class="landing-header">
  <div class="landing-header-inner">
    <a href="#/" class="brand-link" aria-label="Fiosra home">
      <img src={lockupUrl} alt="Fiosra · Learning in Motion" class="brand-logo" />
    </a>

    <nav class="landing-nav" aria-label="Homepage navigation">
      <a href="#how-it-works" class="nav-link">How it works</a>
      <a href="#/courses" class="nav-link">Educator View</a>
      <a href="#/student/home" class="nav-link">Student View</a>
    </nav>

    <div class="header-cta-group">
      <a href="#/courses" class="btn-header-secondary">
        Educator Studio
      </a>
      <a href="#/student/home" class="btn-header-cta">
        <span class="btn-text-full">Explore the experience</span>
        <span class="btn-text-short">Explore</span>
        <svg class="icon-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
        </svg>
      </a>
    </div>
  </div>
</header>

<style>
  .landing-header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(246, 245, 241, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(221, 220, 213, 0.9);
  }

  .landing-header-inner {
    max-width: 1140px;
    height: 76px;
    margin: 0 auto;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .brand-link {
    display: inline-flex;
    align-items: center;
    text-decoration: none;
  }

  .brand-logo {
    height: 48px;
    width: auto;
    object-fit: contain;
  }

  .landing-nav {
    display: flex;
    align-items: center;
    gap: 28px;
  }

  .nav-link {
    font-size: 13px;
    font-weight: 500;
    color: var(--m-color-slate, #6D7378);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .nav-link:hover {
    color: var(--m-color-obsidian, #111315);
  }

  .header-cta-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .btn-header-secondary {
    display: inline-flex;
    align-items: center;
    background: transparent;
    border: 1px solid var(--border, #DDDCD5);
    color: var(--m-color-obsidian, #111315);
    font-size: 12px;
    font-weight: 600;
    padding: 9px 14px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .btn-header-secondary:hover {
    background: #ffffff;
    border-color: #C9D7FF;
  }

  .btn-header-cta {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--m-color-obsidian, #111315);
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 18px;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s ease, transform 0.1s ease;
  }

  .btn-header-cta:hover {
    background: #000000;
  }

  .btn-header-cta:active {
    transform: scale(0.98);
  }

  .btn-text-short {
    display: none;
  }

  @media (max-width: 640px) {
    .landing-header-inner {
      height: 64px;
      padding: 0 16px;
    }

    .landing-nav {
      display: none;
    }

    .btn-text-full {
      display: none;
    }

    .btn-text-short {
      display: inline;
    }
  }
</style>
