<script>
  import { onMount } from 'svelte';

  let { open = $bindable(false) } = $props();
  let courses = $state([]);
  let courseId = $state('');
  let moduleId = $state('');
  let mode = $state('assignment');
  let instruction = $state('');

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

{#if open}
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
  .assistant-panel{background:var(--color-graphite);border-left:1px solid var(--color-graphite-border);display:flex;flex-direction:column;min-height:0;overflow:hidden;width:100%}.assistant-header{border-bottom:1px solid var(--color-graphite-border);display:flex;gap:16px;justify-content:space-between;padding:24px 24px 20px}.eyebrow{color:var(--color-horizon-bright);font-size:10px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}.assistant-header h2{color:var(--color-heading);font-family:var(--font-brand);font-size:22px;margin:5px 0}.assistant-header p{color:var(--color-slate-light);font-size:12px;line-height:1.5;margin:0;max-width:390px}.close{background:transparent;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-light);cursor:pointer;font-size:20px;height:30px;line-height:20px;width:30px}.mode-tabs{border-bottom:1px solid var(--color-graphite-border);display:grid;grid-template-columns:repeat(3,1fr);padding:10px;gap:6px}.mode-tabs button{background:transparent;border:1px solid transparent;border-radius:var(--radius-sm);color:var(--color-slate-light);cursor:pointer;font-size:11px;font-weight:600;padding:9px 4px}.mode-tabs button.active{background:rgba(59,130,246,.14);border-color:rgba(59,130,246,.3);color:var(--color-horizon-bright)}.assistant-body{display:flex;flex:1;flex-direction:column;gap:16px;overflow:auto;padding:22px 24px}.assistant-body label{color:var(--color-slate-light);display:flex;flex-direction:column;font-size:10px;font-weight:700;gap:6px;letter-spacing:.35px;text-transform:uppercase}.assistant-body select,.assistant-body textarea{background:var(--color-obsidian);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-bright);font:inherit;font-size:12px;padding:10px}.assistant-body textarea{line-height:1.55;resize:vertical}.assistant-guidance{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.22);border-radius:var(--radius-sm);padding:12px}.assistant-guidance span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;text-transform:uppercase}.assistant-guidance p{color:var(--color-slate-light);font-size:11.5px;line-height:1.5;margin:5px 0 0}.suggestion{align-self:flex-start;background:transparent;border:0;color:var(--color-aurora-bright);cursor:pointer;font-size:11px;padding:0;text-decoration:underline}.assistant-footer{align-items:center;border-top:1px solid var(--color-graphite-border);color:var(--color-slate-muted);display:flex;font-size:10px;gap:14px;justify-content:space-between;line-height:1.4;padding:16px 24px}.assistant-footer span{max-width:240px}@media(max-width:940px){.assistant-panel{border-left:0;border-top:1px solid var(--color-graphite-border);min-height:580px}.assistant-footer{align-items:stretch;flex-direction:column}.assistant-footer span{max-width:none}.assistant-footer .btn{width:100%}}
</style>
