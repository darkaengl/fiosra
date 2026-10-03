<script lang="ts">
  import InstitutionalFooter from '../lib/InstitutionalFooter.svelte';
  import HomeHeader from '../lib/home/HomeHeader.svelte';
  import HomeHeroSection from '../lib/home/HomeHeroSection.svelte';
  import HomeThesisSection from '../lib/home/HomeThesisSection.svelte';
  import HomeLoopSection from '../lib/home/HomeLoopSection.svelte';
  import HomeExperiencesSection from '../lib/home/HomeExperiencesSection.svelte';
  import HomeCtaBanner from '../lib/home/HomeCtaBanner.svelte';

  const FIOSRA_LOCKUP_URL = "./fiosra-lockup.png";
  const FIOSRA_SYMBOL_URL = "./fiosra-symbol.png";
</script>

<div class="landing-page">
  <!-- Public Sticky Navigation Header -->
  <HomeHeader lockupUrl={FIOSRA_LOCKUP_URL} />

  <main>
    <!-- Hero Section with Live Workspace Preview -->
    <HomeHeroSection symbolUrl={FIOSRA_SYMBOL_URL} />

    <!-- The Product Thesis -->
    <HomeThesisSection />

    <!-- The Fiosra Pedagogical Loop -->
    <HomeLoopSection />

    <!-- Two Connected Experiences -->
    <HomeExperiencesSection />

    <!-- Deep Obsidian CTA Banner -->
    <HomeCtaBanner />
  </main>

  <!-- Public Institutional Footer -->
  <InstitutionalFooter variant="public" />
</div>

<style>
  .landing-page {
    min-height: 100vh;
    background-color: var(--m-color-bone, #F6F5F1);
    color: var(--m-color-obsidian, #111315);
    font-family: var(--font-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    overflow-x: hidden;
  }
</style>
