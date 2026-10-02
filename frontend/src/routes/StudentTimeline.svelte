<script lang="ts">
  import { onMount } from 'svelte';
  import { getStudentId } from '../lib/session.js';
  import TimelineKpiRibbon from '../lib/timeline/TimelineKpiRibbon.svelte';
  import TimelinePathwayCard from '../lib/timeline/TimelinePathwayCard.svelte';
  import TimelineMilestoneEntry from '../lib/timeline/TimelineMilestoneEntry.svelte';
  import TimelineEndorsementSection from '../lib/timeline/TimelineEndorsementSection.svelte';

  let enrolledCourses = $state<any[]>([]);
  let selectedCourseFilter = $state('all');
  let selectedTypeFilter = $state('all');
  let isLoading = $state(true);
  let studentId = '';

  const progressionMilestones = [
    {
      id: 'm-4',
      courseId: 'HIST-201',
      courseName: 'French Revolution & Sovereign Debt',
      title: 'Milestone 4: The Fiscal Breakdown: Sovereign Debt & Estates-General',
      date: 'Fall 2026 • Recent',
      timestamp: '2026-09-10',
      type: 'finalized',
      autonomyScore: 88.4,
      autonomyLevel: 'Level 4 Independent',
      hintRatio: 0.18,
      hintsUsed: 1,
      selfCorrections: 2,
      score: '94 / 100',
      status: 'Educator Finalized',
      badgeClass: 'badge-success',
      growthNote: 'Autonomously caught and revised the "luxury spending" moralized trope upon inspecting Necker\'s Compte Rendu data. Structured the final argument around structural interest burdens.',
      evidenceQuote: 'When mystery shrouds finances, distrust multiplies. The debt burden was structural rather than purely courtiers’ indulgence.',
      verifiedProtocol: 'AAAI-2026 AutoSCORE • SHA-256: 9ac3...77d1',
      signedBy: 'Dr. Vance (Educator)',
    },
    {
      id: 'm-3',
      courseId: 'HIST-201',
      courseName: 'French Revolution & Sovereign Debt',
      title: 'Milestone 3: Abbé Sieyès: National Sovereignty & The Third Estate',
      date: '2 weeks ago',
      timestamp: '2026-08-27',
      type: 'finalized',
      autonomyScore: 84.2,
      autonomyLevel: 'Level 4 Independent',
      hintRatio: 0.25,
      hintsUsed: 1,
      selfCorrections: 1,
      score: '91 / 100',
      status: 'Educator Finalized',
      badgeClass: 'badge-success',
      growthNote: 'Synthesized legal sovereignty with socio-economic grievances. Resisted leading Socratic counter-probes regarding aristocratic constitutionalism.',
      evidenceQuote: 'What is the Third Estate? Everything. What has it been heretofore in the political order? Nothing.',
      verifiedProtocol: 'AAAI-2026 AutoSCORE • SHA-256: 4f12...b981',
      signedBy: 'Dr. Vance (Educator)',
    },
    {
      id: 'm-2',
      courseId: 'HIST-201',
      courseName: 'French Revolution & Sovereign Debt',
      title: 'Milestone 2: Provincial Agrarian Distress & Arthur Young Travel Diaries',
      date: '4 weeks ago',
      timestamp: '2026-08-14',
      type: 'finalized',
      autonomyScore: 78.5,
      autonomyLevel: 'Level 3 Transitional',
      hintRatio: 0.45,
      hintsUsed: 2,
      selfCorrections: 1,
      score: '86 / 100',
      status: 'Educator Finalized',
      badgeClass: 'badge-info',
      growthNote: 'Required tutor prompting to connect regional bread price disparities to Parisian insurrectionary pressure; demonstrated solid primary source extraction.',
      evidenceQuote: 'The price of bread was a constant threat of ruin to the laborer, rendering taxation intolerable.',
      verifiedProtocol: 'AAAI-2026 AutoSCORE • SHA-256: 7d4a...31ce',
      signedBy: 'Dr. Vance (Educator)',
    },
    {
      id: 'm-1',
      courseId: 'HIST-201',
      courseName: 'French Revolution & Sovereign Debt',
      title: 'Milestone 1: Diagnostic Baseline: Pre-Revolutionary Institutional Crises',
      date: '6 weeks ago • Baseline',
      timestamp: '2026-07-30',
      type: 'baseline',
      autonomyScore: 62.0,
      autonomyLevel: 'Level 2 Supervised',
      hintRatio: 0.85,
      hintsUsed: 4,
      selfCorrections: 0,
      score: '78 / 100',
      status: 'Baseline Assessment',
      badgeClass: 'badge-neutral',
      growthNote: 'Initial baseline assessment. High hint dependency initially observed (0.85). Significant upward trajectory established over subsequent reasoning cycles.',
      evidenceQuote: 'Initial hypothesis heavily relied on generalized secondary interpretations without direct grounding in fiscal records.',
      verifiedProtocol: 'AAAI-2026 AutoSCORE • SHA-256: 1b92...8842',
      signedBy: 'Dr. Vance (Educator)',
    },
  ];

  onMount(async () => {
    studentId = getStudentId();
    try {
      const res = await fetch(`/courses/enrolled?student_id=${encodeURIComponent(studentId)}`);
      if (res.ok) {
        enrolledCourses = await res.json();
      }
    } catch (err) {
      console.error('Failed to load courses for timeline:', err);
    } finally {
      isLoading = false;
    }
  });

  let filteredMilestones = $derived.by(() => {
    return progressionMilestones.filter((m) => {
      if (selectedCourseFilter !== 'all' && m.courseId !== selectedCourseFilter) return false;
      if (selectedTypeFilter !== 'all' && m.type !== selectedTypeFilter) return false;
      return true;
    });
  });

  function exportCredentials() {
    const cred = {
      '@context': ['https://www.w3.org/2018/credentials/v1'],
      type: ['VerifiableCredential', 'ReasoningProgressionCredential'],
      issuer: 'did:fiosra:institution:univ-history-dept',
      issuanceDate: new Date().toISOString(),
      credentialSubject: {
        id: `did:fiosra:student:${studentId || 'elena_rostova'}`,
        autonomyIndex: 0.884,
        progressionSummary: 'Demonstrated transition from Supervised to Level 4 Independent reasoning over 4 milestones.',
        verifiableClaimsRatio: 0.90,
        hintCeilingReduction: '0.85 -> 0.18',
        endorsedBy: 'Dr. Vance',
      },
    };
    const blob = new Blob([JSON.stringify(cred, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fiosra-progression-credential-${studentId || 'student'}.json-ld`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="timeline-page">
  <main class="timeline-container">
    <!-- Header & Progression Overview -->
    <header class="progression-header">
      <div class="header-main">
        <div class="header-breadcrumbs">
          <span class="eyebrow">Student Longitudinal Records</span>
          <span class="crumb-separator">•</span>
          <span class="crumb-text">Reasoning Progression Timeline</span>
        </div>
        <h1 class="page-title">Reasoning Progression & Autonomy Growth</h1>
        <p class="page-desc">
          Longitudinal flight-recorder tracing your epistemic evolution, Socratic independence, and verifiable milestones across Fall 2026.
        </p>
      </div>

      <div class="autonomy-status-card">
        <div class="autonomy-level-tag">CURRENT AUTONOMY LEVEL</div>
        <div class="autonomy-grade-display">
          <span class="level-num">Level 4</span>
          <span class="level-title">Independent</span>
        </div>
        <div class="autonomy-progress-track">
          <div class="autonomy-progress-fill" style="width: 88.4%;"></div>
        </div>
        <div class="autonomy-stats-sub">
          <span>88.4% Autonomy Index</span>
          <span class="growth-delta">+26.4% growth</span>
        </div>
      </div>
    </header>

    <!-- Progression Summary KPIs -->
    <TimelineKpiRibbon />

    <!-- Trajectory Pathway Visualization -->
    <TimelinePathwayCard onExport={exportCredentials} />

    <!-- Filters and Timeline Stream -->
    <section class="stream-section">
      <div class="stream-header">
        <div class="stream-title-group">
          <h2 class="stream-title">Chronological Milestones & Evidence</h2>
          <span class="stream-count">{filteredMilestones.length} Milestones Recorded</span>
        </div>

        <div class="stream-controls">
          <div class="filter-group">
            <label for="filter-course">Course:</label>
            <select id="filter-course" bind:value={selectedCourseFilter} class="select-filter">
              <option value="all">All Courses</option>
              <option value="HIST-201">HIST-201: French Revolution</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="filter-type">Type:</label>
            <select id="filter-type" bind:value={selectedTypeFilter} class="select-filter">
              <option value="all">All Milestones</option>
              <option value="finalized">Educator Finalized</option>
              <option value="baseline">Baseline Assessments</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Vertical Timeline List -->
      <div class="timeline-stream">
        {#each filteredMilestones as item, idx (item.id)}
          <TimelineMilestoneEntry
            {item}
            index={idx}
            totalCount={filteredMilestones.length}
          />
        {/each}
      </div>
    </section>

    <!-- Faculty Endorsement & Verifiable Record -->
    <TimelineEndorsementSection onExport={exportCredentials} />
  </main>
</div>

<style>
  .timeline-page {
    background-color: var(--color-obsidian);
    min-height: calc(100vh - 56px);
    color: var(--color-slate-bright);
  }

  .timeline-container {
    max-width: 1160px;
    margin: 0 auto;
    padding: 36px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  /* Header */
  .progression-header {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    padding: 28px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    box-shadow: var(--shadow-sm);
  }

  .header-main {
    max-width: 680px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .header-breadcrumbs {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.6px;
    color: var(--color-horizon-bright);
  }

  .crumb-separator {
    color: var(--color-slate-subtle);
  }

  .crumb-text {
    color: var(--color-slate-muted);
  }

  .page-title {
    font-family: var(--font-brand);
    font-size: 26px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
  }

  .page-desc {
    font-size: 13.5px;
    color: var(--color-slate-light);
    line-height: 1.5;
    margin: 0;
  }

  /* Autonomy Status Badge */
  .autonomy-status-card {
    background: var(--color-obsidian);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 16px 20px;
    min-width: 240px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .autonomy-level-tag {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--color-slate-muted);
  }

  .autonomy-grade-display {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .level-num {
    font-family: var(--font-brand);
    font-size: 22px;
    font-weight: 800;
    color: var(--color-signal-green);
  }

  .level-title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--color-heading);
  }

  .autonomy-progress-track {
    height: 6px;
    background: var(--pill-bg);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-top: 4px;
  }

  .autonomy-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--color-signal-green), #10b981);
    border-radius: var(--radius-full);
  }

  .autonomy-stats-sub {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--color-slate-muted);
  }

  .growth-delta {
    color: var(--color-signal-green);
    font-weight: 600;
  }

  /* Stream Section */
  .stream-section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .stream-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .stream-title-group {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .stream-title {
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0;
  }

  .stream-count {
    font-size: 12px;
    color: var(--color-slate-muted);
  }

  .stream-controls {
    display: flex;
    gap: 12px;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--color-slate-light);
  }

  .select-filter {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    color: var(--color-slate-bright);
    padding: 6px 12px;
    border-radius: var(--radius-sm);
    font-size: 12px;
    cursor: pointer;
  }

  .timeline-stream {
    display: flex;
    flex-direction: column;
  }
</style>
