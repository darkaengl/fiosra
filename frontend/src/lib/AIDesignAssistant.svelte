<script>
  import { onMount } from 'svelte';
  import { router } from 'svelte-spa-router';

  let { open = $bindable(false) } = $props();
  let courses = $state([]);
  let courseId = $state('');
  let moduleId = $state('');
  let mode = $state('assignment');
  let instruction = $state('');

  let isStudent = $derived(Boolean(router.location && router.location.startsWith('/student')));

  $effect(() => {
    if (isStudent && open) {
      open = false;
    }
  });

  let activeCourse = $derived(courses.find((course) => course.course_id === courseId) || null);
  let suggestedInstruction = $derived(
    mode === 'assignment'
      ? `Draft a source-grounded Socratic assignment for ${activeCourse?.modules?.find((module) => module.module_id === moduleId)?.title || 'the selected module'}. Focus on a contestable claim, evidence use, and likely misconceptions.`
      : mode === 'graph'
        ? `Review the course concept graph. Strengthen the genuine semantic hierarchy and identify prerequisite relationships that students must understand before later concepts.`
        : `Help me design a coherent course sequence with high-level themes, concepts, evidence-rich modules, and progressive inquiry.`,
  );

  function courseFromHash() {
    const queryIndex = window.location.hash.indexOf('?');
    if (queryIndex < 0) return '';
    return new URLSearchParams(window.location.hash.slice(queryIndex + 1)).get('course_id') || '';
  }

  function openAssistant() {
    if (isStudent) return;
    open = true;
    const contextualCourseId = courseFromHash();
    if (contextualCourseId) selectCourse(contextualCourseId);
  }

  function closeAssistant() { open = false; }

  function selectCourse(nextCourseId) {
    courseId = nextCourseId;
    moduleId = courses.find((course) => course.course_id === nextCourseId)?.modules?.[0]?.module_id || '';
  }

  function beginWork() {
    const direction = instruction.trim() || suggestedInstruction;
    const encodedDirection = encodeURIComponent(direction);
    const courseQuery = courseId ? `course_id=${encodeURIComponent(courseId)}` : '';
    if (mode === 'assignment') {
      const moduleQuery = moduleId ? `&module_id=${encodeURIComponent(moduleId)}` : '';
      window.location.hash = `#/designer?${courseQuery}${moduleQuery}&assistant=draft&assistant_instruction=${encodedDirection}`;
    } else if (mode === 'graph') {
      window.location.hash = `#/modules?${courseQuery}&assistant=graph&assistant_instruction=${encodedDirection}`;
    } else {
      window.location.hash = `#/studio/course?assistant=course&assistant_instruction=${encodedDirection}`;
    }
    closeAssistant();
  }

  function useSuggestion() { instruction = suggestedInstruction; }

  onMount(async () => {
    window.addEventListener('fiosra:assistant-toggle', openAssistant);
    try {
      const response = await fetch('/courses');
      if (response.ok) {
        courses = await response.json();
        selectCourse(courseFromHash() || courses[0]?.course_id || '');
      }
    } catch {
      // The assistant remains usable for new-course work if course context is unavailable.
    }
    return () => window.removeEventListener('fiosra:assistant-toggle', openAssistant);
  });
</script>

{#if open && !isStudent}
  <aside class="assistant-panel" aria-label="AI Design Assistant">
    <header class="assistant-header"><div><span class="eyebrow">Fiosra design intelligence</span><h2>AI Design Assistant</h2><p>Set a direction once; the right workspace opens with the course and module context already attached.</p></div><button type="button" class="close" onclick={closeAssistant} aria-label="Close AI assistant">×</button></header>
    <div class="mode-tabs" role="tablist"><button type="button" class:active={mode === 'course'} onclick={() => (mode = 'course')}>Course design</button><button type="button" class:active={mode === 'assignment'} onclick={() => (mode = 'assignment')}>Assignment draft</button><button type="button" class:active={mode === 'graph'} onclick={() => (mode = 'graph')}>Concept graph</button></div>
    <section class="assistant-body">
      {#if mode !== 'course'}
        <label>Course context<select bind:value={courseId} onchange={() => selectCourse(courseId)}><option value="">Select a course</option>{#each courses as course}<option value={course.course_id}>{course.title}</option>{/each}</select></label>
      {/if}
      {#if mode === 'assignment' && activeCourse}
        <label>Module context<select bind:value={moduleId}><option value="">Choose a module</option>{#each activeCourse.modules || [] as module}<option value={module.module_id}>Unit {module.position}: {module.title}</option>{/each}</select></label>
      {/if}
      <div class="assistant-guidance"><span>{mode === 'assignment' ? 'Proactive assignment brief' : mode === 'graph' ? 'Graph refinement brief' : 'Course design brief'}</span><p>{mode === 'assignment' ? 'The assistant will draft a Socratic task with objectives, source boundaries, hint ladder, misconceptions, and rubric criteria. You review before saving or publishing.' : mode === 'graph' ? 'The assistant will create a teacher-reviewable concept, hierarchy, and prerequisite proposal. Nothing becomes active until you validate it.' : 'The assistant will open the course studio with a design direction ready to synthesize into an editable curriculum draft.'}</p></div>
      <label>Your direction<textarea rows="7" bind:value={instruction} placeholder={suggestedInstruction}></textarea></label>
      <button type="button" class="suggestion" onclick={useSuggestion}>Use a focused starting brief</button>
    </section>
    <footer class="assistant-footer"><span>AI prepares a proposal; the educator remains the approving authority.</span><button type="button" class="btn btn-primary" disabled={mode !== 'course' && !courseId} onclick={beginWork}>{mode === 'assignment' ? 'Draft assignment' : mode === 'graph' ? 'Propose graph update' : 'Open course studio'}</button></footer>
  </aside>
{/if}

<style>
  .assistant-panel {
    background: var(--surface, #ffffff);
    border-left: 1px solid var(--border, #DDDCD5);
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    width: 100%;
  }

  .assistant-header {
    background: var(--color-bone, #F6F5F1);
    border-bottom: 1px solid var(--border, #DDDCD5);
    display: flex;
    gap: 16px;
    justify-content: space-between;
    padding: 24px 24px 20px;
  }

  .eyebrow {
    color: var(--color-horizon-blue, #4F6BFF);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .5px;
    text-transform: uppercase;
  }

  .assistant-header h2 {
    color: var(--color-heading, #111315);
    font-family: var(--font-brand, inherit);
    font-size: 22px;
    margin: 5px 0;
  }

  .assistant-header p {
    color: var(--color-slate, #6D7378);
    font-size: 12px;
    line-height: 1.5;
    margin: 0;
    max-width: 390px;
  }

  .close {
    background: transparent;
    border: 1px solid var(--border, #DDDCD5);
    border-radius: var(--radius-sm, 6px);
    color: var(--color-slate, #6D7378);
    cursor: pointer;
    font-size: 20px;
    height: 30px;
    line-height: 20px;
    width: 30px;
    transition: all 0.15s ease;
  }

  .close:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
    color: var(--color-heading, #111315);
  }

  .mode-tabs {
    background: var(--color-bone, #F6F5F1);
    border-bottom: 1px solid var(--border, #DDDCD5);
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    padding: 10px;
    gap: 6px;
  }

  .mode-tabs button {
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--radius-sm, 6px);
    color: var(--color-slate, #6D7378);
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    padding: 9px 4px;
    transition: all 0.15s ease;
  }

  .mode-tabs button:hover {
    background: var(--color-cloud-subtle, #F0EFEA);
    color: var(--color-heading, #111315);
  }

  .mode-tabs button.active {
    background: var(--color-horizon-blue-soft, #EBF0FF);
    border-color: rgba(79, 107, 255, 0.35);
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .assistant-body {
    background: var(--surface, #ffffff);
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 16px;
    overflow: auto;
    padding: 22px 24px;
  }

  .assistant-body label {
    color: var(--color-slate, #6D7378);
    display: flex;
    flex-direction: column;
    font-size: 10px;
    font-weight: 700;
    gap: 6px;
    letter-spacing: .35px;
    text-transform: uppercase;
  }

  .assistant-body select,
  .assistant-body textarea {
    background: var(--color-cloud-subtle, #F0EFEA);
    border: 1px solid var(--border, #DDDCD5);
    border-radius: var(--radius-sm, 6px);
    color: var(--color-heading, #111315);
    font: inherit;
    font-size: 12px;
    padding: 10px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .assistant-body select:focus,
  .assistant-body textarea:focus {
    outline: none;
    border-color: var(--color-horizon-blue, #4F6BFF);
    box-shadow: 0 0 0 2px var(--color-horizon-glow, rgba(79, 107, 255, 0.15));
  }

  .assistant-body textarea {
    line-height: 1.55;
    resize: vertical;
  }

  .assistant-guidance {
    background: var(--color-horizon-blue-soft, #EBF0FF);
    border: 1px solid rgba(79, 107, 255, 0.25);
    border-radius: var(--radius-sm, 6px);
    padding: 12px;
  }

  .assistant-guidance span {
    color: var(--color-horizon-blue, #4F6BFF);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .assistant-guidance p {
    color: var(--color-slate, #6D7378);
    font-size: 11.5px;
    line-height: 1.5;
    margin: 5px 0 0;
  }

  .suggestion {
    align-self: flex-start;
    background: transparent;
    border: 0;
    color: var(--color-horizon-blue, #4F6BFF);
    cursor: pointer;
    font-size: 11px;
    padding: 0;
    text-decoration: underline;
    transition: color 0.15s ease;
  }

  .suggestion:hover {
    color: var(--color-horizon-bright, #3D5AFE);
  }

  .assistant-footer {
    align-items: center;
    background: var(--color-bone, #F6F5F1);
    border-top: 1px solid var(--border, #DDDCD5);
    color: var(--color-slate, #6D7378);
    display: flex;
    font-size: 10px;
    gap: 14px;
    justify-content: space-between;
    line-height: 1.4;
    padding: 16px 24px;
  }

  .assistant-footer span {
    max-width: 240px;
  }

  .assistant-footer .btn-primary {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
    border: 1px solid var(--color-horizon-bright, #3D5AFE);
    border-radius: var(--radius-sm, 6px);
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 1px 3px var(--color-horizon-glow, rgba(79, 107, 255, 0.2));
    transition: all 0.15s ease;
  }

  .assistant-footer .btn-primary:hover:not(:disabled) {
    background: var(--color-horizon-bright, #3D5AFE);
    transform: translateY(-1px);
    box-shadow: 0 2px 6px var(--color-horizon-glow, rgba(79, 107, 255, 0.3));
  }

  .assistant-footer .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  @media(max-width: 940px) {
    .assistant-panel {
      border-left: 0;
      border-top: 1px solid var(--border, #DDDCD5);
      min-height: 580px;
    }
    .assistant-footer {
      align-items: stretch;
      flex-direction: column;
    }
    .assistant-footer span {
      max-width: none;
    }
    .assistant-footer .btn {
      width: 100%;
    }
  }
</style>
