<script>
  import { onMount } from 'svelte';
  import { responseError, routeParams } from '../lib/session.js';
  import AssignmentDesignerHeader from '../lib/authoring/AssignmentDesignerHeader.svelte';
  import AssignmentTaskSection from '../lib/authoring/AssignmentTaskSection.svelte';
  import AssignmentSourcesSection from '../lib/authoring/AssignmentSourcesSection.svelte';
  import RubricDesigner from '../lib/authoring/RubricDesigner.svelte';
  import AssignmentAdvancedSection from '../lib/authoring/AssignmentAdvancedSection.svelte';
  import AssignmentStudentPreview from '../lib/authoring/AssignmentStudentPreview.svelte';
  import AssignmentBriefHandout from '../lib/sources/AssignmentBriefHandout.svelte';
  import { sourceCards, publicRubric, createContract } from '../lib/authoring/designerUtils.js';

  let courseId = $state('');
  let moduleId = $state('');
  let course = $state(null);
  let courseDocuments = $state([]);
  let domain = $state('history');

  // Theme state: defaults to 'light' (academic light mode)
  let currentTheme = $state('light');

  // Core state
  let topic = $state('');
  let prompt = $state('');
  let contract = $state(null);
  let evaluationPlan = $state(null);
  let scaffold = $state(null);
  let draft = $state(null);
  let readiness = $state({ is_publishable: false, items: [] });

  // View & UI state
  let viewMode = $state('editor'); // 'editor' | 'preview' | 'pdf'
  let activePdfViewer = $state(null); // { title: string, url: string } | null
  let isLoading = $state(true);
  let isProposing = $state(false);
  let isSynthesizingRubric = $state(false);
  let isSaving = $state(false);
  let notice = $state('');
  let error = $state('');

  const activeModule = $derived(
    course?.modules?.find((mod) => String(mod.module_id) === String(moduleId)) || course?.modules?.[0] || null
  );

  const totalRubricWeight = $derived(
    (contract?.public_rubric || []).reduce((acc, curr) => acc + Number(curr.weight || 0), 0)
  );

  function materializeContract(nextScaffold) {
    const res = createContract(topic, prompt, activeModule, nextScaffold);
    contract = res.contract;
    evaluationPlan = res.evaluationPlan;
  }

  async function loadContext() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    moduleId = params.get('module_id') || '';
    if (!courseId) return;

    const [courseRes, docRes] = await Promise.all([
      fetch(`/courses/${courseId}`),
      fetch(`/courses/${courseId}/documents`),
    ]);

    if (!courseRes.ok) throw new Error(await responseError(courseRes, 'Course context could not be loaded.'));
    course = await courseRes.json();
    if (docRes.ok) {
      courseDocuments = await docRes.json();
    }

    if (!moduleId && course.modules?.length) {
      moduleId = course.modules[0].module_id;
    }
    domain = course.domain?.toLowerCase() || 'history';

    const assignmentId = params.get('assignment_id');
    if (assignmentId) {
      await restoreAssignment(assignmentId);
    } else {
      materializeContract(null);
    }
  }

  async function restoreAssignment(assignmentId) {
    try {
      const res = await fetch(`/assignments/${assignmentId}/authoring`);
      if (res.ok) {
        const authoring = await res.json();
        const pub = authoring.published || {};
        contract = {
          title: pub.title || '',
          purpose: pub.purpose || '',
          task: {
            prompt: pub.task?.prompt || '',
            scope: pub.task?.scope || '',
            deliverable: pub.task?.deliverable || '',
            requirements: pub.task?.requirements || [],
          },
          learning_goals: pub.learning_goals || [],
          source_pack: pub.source_pack || [],
          public_rubric: publicRubric(pub.public_rubric || []),
          support_menu: pub.support_menu || [
            { mode: 'source_grounding', title: 'Source Grounding', description: 'Prompts to ground claims directly in primary texts.' },
            { mode: 'counterargument', title: 'Counterargument Probe', description: 'Challenges student reasoning with historical counter-evidence.' },
            { mode: 'structural_organization', title: 'Rhetorical Organization', description: 'Guidance on thesis placement, topic sentences, and synthesis.' },
          ],
          completion_checklist: pub.completion_checklist || [
            'All core claims explicitly cite evidence from assigned primary sources.',
            'Historical counterarguments and institutional complexities are addressed.',
            'Deliverable satisfies scope and tone requirements before final review.',
          ],
          integrity_notice: pub.integrity_notice || 'All primary evidence and quotes must originate from assigned course texts or authenticated sources. External generative synthesis is monitored.',
        };
        evaluationPlan = authoring.evaluation_plan || {
          evaluator_mode: 'deterministic_rubric_with_critique',
          rubric_id: 'rubric_published',
          source_catalog: [],
          concept_coverage_targets: [],
          evidence_rules: [],
          public_rubric_map: [],
        };
        draft = { assignment_id: assignmentId, status: authoring.status || 'draft' };
        readiness = authoring.readiness || { is_publishable: true, items: [] };
      }
    } catch (err) {
      console.error('Failed to restore assignment authoring contract', err);
    }
  }

  async function proposeAssignment() {
    isProposing = true;
    error = '';
    notice = '';
    try {
      const activeModuleKcs = (activeModule?.knowledge_components || []).map((k) =>
        typeof k === 'string'
          ? { kc_id: k, label: k.replace(/^KC_[A-Z]+_/, '').replace(/_/g, ' ') }
          : k
      );
      const res = await fetch('/authoring/assignments/propose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_topic: topic.trim() || `Inquiry for ${activeModule?.title || 'this module'}`,
          course_id: courseId,
          module_id: moduleId,
          domain: course?.domain || domain,
          pedagogical_focus: `Source-grounded inquiry task for ${activeModule?.title || 'this module'} grounded in course documents.`,
          module_objectives: activeModule?.learning_objectives || [],
          target_concepts: activeModuleKcs,
        }),
      });

      if (!res.ok) throw new Error(await responseError(res, 'AI assignment proposal could not be synthesized.'));
      const proposal = await res.json();

      topic = proposal.draft?.title || proposal.scaffold?.clarified_prompt?.slice(0, 60) || topic;
      prompt = proposal.scaffold?.clarified_prompt || prompt;
      scaffold = proposal.scaffold;

      materializeContract(scaffold);
      draft = null;
      notice = '✦ AI synthesized an authentic, source-grounded assignment draft! Review the prompt, readings, and rubric below.';
    } catch (err) {
      error = err.message || 'AI assignment drafting failed.';
    } finally {
      isProposing = false;
    }
  }

  function addSourceCard() {
    if (!contract) return;
    contract.source_pack = [
      ...contract.source_pack,
      {
        source_id: `source_${contract.source_pack.length + 1}`,
        title: 'New Primary Source Document',
        excerpt: 'Add an authentic passage or historical excerpt for students to interrogate...',
        source_url: '',
        citation: 'Primary Source Archive',
        relevance_guidance: 'Analyze how this document provides evidence for the task.',
      },
    ];
  }

  function attachCourseDocument(doc) {
    if (!contract) return;
    const docUrl = doc.download_url || `/courses/${courseId}/documents/${doc.document_id}/file`;
    contract.source_pack = [
      ...contract.source_pack,
      {
        source_id: `source_${contract.source_pack.length + 1}`,
        title: doc.title || doc.filename,
        excerpt: `[Attached Course Document: ${doc.title || doc.filename} — see full document via original PDF link]`,
        source_url: docUrl,
        citation: doc.title || doc.filename,
        relevance_guidance: 'Read the assigned sections of this course reading to substantiate your claims.',
      },
    ];
    notice = `Attached "${doc.title || doc.filename}" to the assignment source pack.`;
  }

  function removeSourceCard(index) {
    if (!contract) return;
    contract.source_pack = contract.source_pack.filter((_, i) => i !== index);
  }

  function addCriterion() {
    if (!contract) return;
    const count = contract.public_rubric.length + 1;
    contract.public_rubric = [
      ...contract.public_rubric,
      {
        criterion_id: `criterion_${count}`,
        title: `Criterion ${count}`,
        description: 'Describe the historical reasoning skill or standard evaluated here.',
        concept_id: null,
        concept_label: null,
        weight: 20,
        levels: [
          { level_id: 'developing', label: 'Developing', description: 'Beginning to demonstrate standard.' },
          { level_id: 'secure', label: 'Secure', description: 'Clearly demonstrates standard with citations.' },
          { level_id: 'strong', label: 'Strong', description: 'Nuanced, masterful execution of the standard.' },
        ],
        self_review_prompt: 'Where does your writing satisfy this criterion?',
      },
    ];
  }

  function removeCriterion(index) {
    if (!contract) return;
    contract.public_rubric = contract.public_rubric.filter((_, i) => i !== index);
  }

  function autoBalanceRubric() {
    if (!contract || !contract.public_rubric.length) return;
    const count = contract.public_rubric.length;
    const base = Math.floor(100 / count);
    const remainder = 100 - base * count;
    contract.public_rubric.forEach((c, idx) => {
      c.weight = base + (idx === count - 1 ? remainder : 0);
    });
  }

  async function synthesizeRubricWithAi() {
    if (!contract) return;
    isSynthesizingRubric = true;
    error = '';
    notice = '';
    try {
      const moduleObjectives = activeModule?.learning_objectives || [];
      const targetConcepts = (activeModule?.knowledge_components || []).map((k) =>
        typeof k === 'string'
          ? { kc_id: k, label: k.replace(/^KC_[A-Z]+_/, '').replace(/_/g, ' ') }
          : k
      );
      const res = await fetch('/authoring/assignments/synthesize-rubric', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: contract.title || topic || 'Assignment Inquiry',
          prompt: contract.task?.prompt || prompt || 'Inquiry task',
          deliverable: contract.task?.deliverable || 'Analytical essay',
          scope: contract.task?.scope || '',
          domain: course?.domain || domain,
          course_id: courseId || null,
          module_id: moduleId || null,
          module_objectives: moduleObjectives,
          target_concepts: targetConcepts,
          sources: (contract.source_pack || []).map((s) => ({ title: s.title, citation: s.citation, excerpt: s.excerpt })),
          learning_goals: contract.learning_goals || [],
        }),
      });

      if (!res.ok) throw new Error(await responseError(res, 'Could not synthesize rubric with AI.'));
      const data = await res.json();

      if (data.public_rubric && data.public_rubric.length > 0) {
        contract.public_rubric = publicRubric(data.public_rubric);
        if (data.learning_goals?.length) {
          contract.learning_goals = data.learning_goals;
        }
        notice = `✦ AI synthesized ${data.public_rubric.length} domain-specific, concept-grounded rubric criteria!`;
      }
    } catch (err) {
      error = err.message || 'AI rubric synthesis failed.';
    } finally {
      isSynthesizingRubric = false;
    }
  }

  async function saveStudio() {
    if (!contract || !evaluationPlan) return;
    isSaving = true;
    error = '';
    notice = '';
    try {
      if (evaluationPlan && contract.public_rubric) {
        evaluationPlan.public_rubric_map = contract.public_rubric.map((rule, index) => {
          const existing = (evaluationPlan.public_rubric_map || []).find(
            (m) => m.public_criterion_id === rule.criterion_id
          );
          const conceptIds = rule.concept_id ? [rule.concept_id] : (existing?.concept_ids || []);
          return {
            ...(existing || {}),
            public_criterion_id: rule.criterion_id || `criterion_${index + 1}`,
            concept_ids: conceptIds,
            source_chunk_ids: existing?.source_chunk_ids || (contract.source_pack || []).map((s) => s.source_id),
            evidence_expectation: rule.description || existing?.evidence_expectation || 'Collect citations relevant to this standard.',
          };
        });
      }

      if (!draft) {
        const response = await fetch('/assignments/draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: contract.title,
            domain,
            course_id: courseId || null,
            module_id: moduleId || null,
            created_by: 'educator_studio',
            raw_prompt: prompt || contract.task.prompt,
            answers: {},
            clarified_prompt: contract.task.prompt,
            target_kcs: scaffold?.target_kcs || [],
            hint_ladder: scaffold?.hint_ladder || [],
            rubric_rules: scaffold?.rubric_rules || [],
            grounding_mode: scaffold?.grounding_mode || 'generic',
            grounding_sources: scaffold?.grounding_sources || [],
            generation_metadata: scaffold?.generation_metadata || null,
            canvas_sections: scaffold?.canvas_sections || [],
            published: contract,
            evaluation_plan: evaluationPlan,
          }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The assignment draft could not be saved.'));
        draft = await response.json();
      } else {
        const response = await fetch(`/assignments/${draft.assignment_id}/authoring`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            published: contract,
            evaluation_plan: evaluationPlan,
            canvas_sections: scaffold?.canvas_sections || [],
          }),
        });
        if (!response.ok) throw new Error(await responseError(response, 'The assignment changes could not be saved.'));
      }

      const authRes = await fetch(`/assignments/${draft.assignment_id}/authoring`);
      if (authRes.ok) {
        const authoring = await authRes.json();
        readiness = authoring.readiness || { is_publishable: true, items: [] };
      }
      notice = draft?.status === 'published'
        ? '✓ Assignment changes updated and saved live.'
        : '✓ Assignment draft saved successfully.';
    } catch (err) {
      error = err.message || 'Failed to save assignment.';
    } finally {
      isSaving = false;
    }
  }

  async function publish() {
    await saveStudio();
    if (!draft?.assignment_id) return;
    isSaving = true;
    error = '';
    notice = '';
    try {
      const res = await fetch(`/assignments/${draft.assignment_id}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_id: moduleId || null }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Assignment could not be published.'));
      draft = { ...draft, status: 'published' };
      notice = '🎉 Assignment published! Students can now access this task in their learning canvas.';
    } catch (err) {
      error = err.message || 'Failed to publish assignment.';
    } finally {
      isSaving = false;
    }
  }

  function printAssignmentSheet() {
    window.print();
  }

  onMount(() => {
    let observer;
    try {
      const savedTheme = localStorage.getItem('fiosra_theme');
      currentTheme = savedTheme || document.documentElement.getAttribute('data-theme') || 'light';

      observer = new MutationObserver(() => {
        const dt = document.documentElement.getAttribute('data-theme');
        if (dt && dt !== currentTheme) {
          currentTheme = dt;
        }
      });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

      loadContext().finally(() => { isLoading = false; });
    } catch (err) {
      error = err.message || 'Context loading failed.';
      isLoading = false;
    }

    return () => {
      if (observer) observer.disconnect();
    };
  });
</script>

<svelte:head>
  <title>{contract?.title ? `${contract.title} · Assignment Studio` : 'Assignment Studio'}</title>
</svelte:head>

<main class="studio-workspace" class:dark-mode={currentTheme === 'dark'} class:light-mode={currentTheme === 'light'}>
  <AssignmentDesignerHeader
    {courseId}
    {course}
    bind:moduleId
    {contract}
    bind:viewMode
    {isProposing}
    {isSaving}
    {draft}
    onPropose={proposeAssignment}
    onSave={saveStudio}
    onPublish={publish}
  />

  <!-- Notification Banner -->
  {#if notice}
    <div class="notice-banner success">
      <span>✓</span>
      <p>{notice}</p>
      {#if draft?.status === 'published' && draft?.assignment_id && viewMode !== 'preview'}
        <button
          type="button"
          class="notice-action-link"
          onclick={() => viewMode = 'preview'}
        >
          Preview Student Canvas ➔
        </button>
      {/if}
      <button type="button" class="close-btn" onclick={() => notice = ''}>✕</button>
    </div>
  {/if}
  {#if error}
    <div class="notice-banner error">
      <span>⚠️</span>
      <p>{error}</p>
      <button type="button" class="close-btn" onclick={() => error = ''}>✕</button>
    </div>
  {/if}

  {#if isLoading}
    <div class="loading-screen">
      <div class="spinner"></div>
      <p>Loading educator assignment studio…</p>
    </div>
  {:else if contract}
    <div class="content-container">

      <!-- VIEW MODE 1: STREAMLINED SINGLE-CANVAS EDITOR -->
      {#if viewMode === 'editor'}
        <div class="editor-streamlined-canvas">
          <!-- Section 1: Core Task & Instructions -->
          <AssignmentTaskSection bind:contract />

          <!-- Section 2: Grounded Primary Sources & Course Documents -->
          <AssignmentSourcesSection
            bind:contract
            {courseDocuments}
            onAddSource={addSourceCard}
            onRemoveSource={removeSourceCard}
            onAttachCourseDoc={attachCourseDocument}
            onViewPdf={(pdf) => activePdfViewer = pdf}
          />

          <!-- Section 3: Transparent Public Rubric -->
          <RubricDesigner
            bind:rubric={contract.public_rubric}
            {activeModule}
            isSynthesizing={isSynthesizingRubric}
            onSynthesize={synthesizeRubricWithAi}
            onAutoBalance={autoBalanceRubric}
            onAddCriterion={addCriterion}
            onRemoveCriterion={removeCriterion}
          />

          <!-- Section 4: Collapsible Advanced Settings -->
          <AssignmentAdvancedSection bind:contract />
        </div>

      <!-- VIEW MODE 2: STUDENT REASONING CANVAS PREVIEW -->
      {:else if viewMode === 'preview'}
        <AssignmentStudentPreview
          {contract}
          onViewPdf={(pdf) => activePdfViewer = pdf}
        />

      <!-- VIEW MODE 3: PRINTABLE ACADEMIC PDF SHEET -->
      {:else if viewMode === 'pdf'}
        <div class="pdf-sheet-wrapper">
          <div class="pdf-control-bar no-print">
            <div class="pdf-info">
              <span>📄 Academic Assignment Handout</span>
              <p>Ready to distribute or save as PDF via your browser print dialog.</p>
            </div>
            <button type="button" class="btn-print-pdf" onclick={printAssignmentSheet}>
              🖨️ Save as PDF / Print
            </button>
          </div>

          <AssignmentBriefHandout
            assignment={{ published: contract }}
            courseTitle={course?.title}
            sources={contract.source_pack}
          />
        </div>
      {/if}

    </div>
  {/if}

  <!-- PDF Drawer / Inline Viewer Modal -->
  {#if activePdfViewer}
    <div class="pdf-modal-backdrop" role="dialog" aria-modal="true" aria-label="Course PDF Document Viewer">
      <div class="pdf-modal-card">
        <div class="pdf-modal-header">
          <div class="pdf-title-row">
            <span class="pdf-icon">📕</span>
            <h3>{activePdfViewer.title || 'Primary Source Document'}</h3>
          </div>
          <div class="pdf-modal-actions">
            <a href={activePdfViewer.url} target="_blank" rel="noopener noreferrer" class="btn-secondary btn-xs">
              Open Fullscreen ↗
            </a>
            <button type="button" class="btn-close-modal" onclick={() => activePdfViewer = null}>
              ✕
            </button>
          </div>
        </div>
        <div class="pdf-modal-body">
          <iframe
            src={activePdfViewer.url}
            title={activePdfViewer.title}
            class="pdf-frame"
          ></iframe>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  .studio-workspace {
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding-bottom: 80px;
    transition: background-color 0.2s ease, color 0.2s ease;
  }

  .studio-workspace.light-mode {
    background: #f6f8fa;
    color: #1f2328;
  }

  .studio-workspace.dark-mode {
    background: #0d1117;
    color: #e6edf3;
  }

  /* Notifications */
  .notice-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: 980px;
    margin: 16px auto 0;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 500;
  }
  .light-mode .notice-banner.success {
    background: #dafbe1;
    border: 1px solid #4ac26b;
    color: #116329;
  }
  .dark-mode .notice-banner.success {
    background: rgba(35, 134, 54, 0.15);
    border: 1px solid rgba(46, 160, 67, 0.4);
    color: #3fb950;
  }
  .light-mode .notice-banner.error {
    background: #ffebe9;
    border: 1px solid #ff8182;
    color: #cf222e;
  }
  .dark-mode .notice-banner.error {
    background: rgba(248, 81, 73, 0.15);
    border: 1px solid rgba(248, 81, 73, 0.4);
    color: #f85149;
  }
  .notice-banner p { flex: 1; margin: 0; }
  .close-btn { background: none; border: 0; color: inherit; cursor: pointer; font-size: 13px; }

  .notice-action-link {
    font-weight: 700;
    text-decoration: underline;
    color: inherit;
    margin-left: 8px;
    cursor: pointer;
  }
  .notice-action-link:hover { opacity: 0.85; }

  /* Container */
  .content-container {
    max-width: 1040px;
    margin: 24px auto;
    padding: 0 20px;
  }

  .editor-streamlined-canvas {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .loading-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 20px;
    gap: 16px;
    color: var(--color-slate, #6D7378);
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(79, 107, 255, 0.2);
    border-top-color: var(--color-horizon-blue, #4F6BFF);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* PDF Sheet */
  .pdf-sheet-wrapper {
    max-width: 900px;
    margin: 0 auto;
  }

  .pdf-control-bar {
    border-radius: 8px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .light-mode .pdf-control-bar {
    background: #ffffff;
    border: 1px solid #d0d7de;
  }
  .dark-mode .pdf-control-bar {
    background: #161b22;
    border: 1px solid #30363d;
  }

  .pdf-info span {
    font-size: 13px;
    font-weight: 700;
  }
  .light-mode .pdf-info span { color: #1f2328; }
  .dark-mode .pdf-info span { color: #f0f6fc; }

  .pdf-info p {
    font-size: 12px;
    margin: 2px 0 0;
  }
  .light-mode .pdf-info p { color: #57606a; }
  .dark-mode .pdf-info p { color: #8b949e; }

  .btn-print-pdf {
    background: #1a7f37;
    border: 0;
    border-radius: 6px;
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    padding: 8px 16px;
    cursor: pointer;
  }

  /* PDF Modal / Drawer */
  .pdf-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(6px);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .pdf-modal-card {
    border-radius: 12px;
    width: 90vw;
    max-width: 1200px;
    height: 88vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  }
  .light-mode .pdf-modal-card {
    background: #ffffff;
    border: 1px solid #d0d7de;
  }
  .dark-mode .pdf-modal-card {
    background: #161b22;
    border: 1px solid #30363d;
  }

  .pdf-modal-header {
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .light-mode .pdf-modal-header { border-bottom: 1px solid #d0d7de; }
  .dark-mode .pdf-modal-header { border-bottom: 1px solid #30363d; }

  .pdf-title-row { display: flex; align-items: center; gap: 8px; }
  .pdf-title-row h3 { font-size: 14px; margin: 0; }
  .light-mode .pdf-title-row h3 { color: #1f2328; }
  .dark-mode .pdf-title-row h3 { color: #f0f6fc; }

  .pdf-modal-actions { display: flex; align-items: center; gap: 12px; }
  .btn-secondary {
    background: #ffffff;
    border: 1px solid #d0d7de;
    color: #24292f;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 13px;
    cursor: pointer;
    text-decoration: none;
  }
  .dark-mode .btn-secondary {
    background: #21262d;
    border-color: #30363d;
    color: #c9d1d9;
  }
  .btn-xs { font-size: 11px; padding: 3px 8px; }

  .btn-close-modal {
    background: none;
    border: 0;
    cursor: pointer;
    font-size: 16px;
  }
  .light-mode .btn-close-modal { color: #57606a; }
  .light-mode .btn-close-modal:hover { color: #1f2328; }
  .dark-mode .btn-close-modal { color: #8b949e; }
  .dark-mode .btn-close-modal:hover { color: #f0f6fc; }

  .pdf-modal-body {
    flex: 1;
  }
  .light-mode .pdf-modal-body { background: #f6f8fa; }
  .dark-mode .pdf-modal-body { background: #0d1117; }

  .pdf-frame { width: 100%; height: 100%; border: 0; }

  @media print {
    body, html, .studio-workspace {
      background: #ffffff !important;
      color: #000000 !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    .no-print, .notice-banner, .pdf-control-bar {
      display: none !important;
    }
    .content-container, .pdf-sheet-wrapper {
      max-width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
    }
  }
</style>
