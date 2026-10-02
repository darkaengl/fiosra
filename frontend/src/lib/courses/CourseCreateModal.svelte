<script lang="ts">
  import Modal from '../Modal.svelte';

  let {
    isOpen = false,
    onClose = () => {},
    onCreated = (course: any) => {},
  } = $props<{
    isOpen?: boolean;
    onClose?: () => void;
    onCreated?: (course: any) => void;
  }>();

  let isCreating = $state(false);
  let createFeedback = $state('');

  let newCourseCode = $state('');
  let newCourseTitle = $state('');
  let newCourseDomain = $state('History');
  let newCourseInstructor = $state('Dr. Vance');
  let newCourseSyllabus = $state('');

  async function handleCreateCourse(e: Event) {
    e.preventDefault();
    if (!newCourseTitle.trim()) return;
    isCreating = true;
    createFeedback = '';
    try {
      const res = await fetch('/courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newCourseCode.trim() ? `${newCourseCode.trim()}: ${newCourseTitle.trim()}` : newCourseTitle.trim(),
          domain: newCourseDomain,
          created_by: newCourseInstructor.trim() || 'Dr. Vance',
          syllabus_context: newCourseSyllabus.trim() || null,
        }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const newCourse = await res.json();
      onCreated(newCourse);
      newCourseCode = '';
      newCourseTitle = '';
      newCourseSyllabus = '';
      onClose();
    } catch (err: any) {
      createFeedback = 'Failed: ' + err.message;
    } finally {
      isCreating = false;
    }
  }
</script>

<Modal {isOpen} title="🏛️ Create New Course Workspace" {onClose}>
  <p class="modal-desc">
    Set a clear course identity and teaching context. You can then create modules, attach source material, and test a student-safe assignment before publication.
  </p>
  <form onsubmit={handleCreateCourse} class="create-form">
    <div class="form-row">
      <div class="form-field">
        <label for="newCourseCode" class="field-label">Course Code</label>
        <input id="newCourseCode" type="text" class="field-input" placeholder="e.g. HIST-302" bind:value={newCourseCode} />
      </div>
      <div class="form-field">
        <label for="newCourseTitle" class="field-label">Course Title <span class="req">*</span></label>
        <input id="newCourseTitle" type="text" class="field-input" placeholder="e.g. Revolutions in the Atlantic World" bind:value={newCourseTitle} required />
      </div>
    </div>
    <div class="form-row">
      <div class="form-field">
        <label for="newCourseDomain" class="field-label">Academic Domain <span class="req">*</span></label>
        <select id="newCourseDomain" class="field-input" bind:value={newCourseDomain}>
          <option>History</option>
          <option>Philosophy</option>
          <option>Computer Science</option>
          <option>Physics</option>
          <option>Economics</option>
          <option>Literature</option>
        </select>
      </div>
      <div class="form-field">
        <label for="newCourseInstructor" class="field-label">Lead Instructor</label>
        <input id="newCourseInstructor" type="text" class="field-input" bind:value={newCourseInstructor} />
      </div>
    </div>
    <div class="form-field">
      <label for="newCourseSyllabus" class="field-label">Introductory Syllabus Context (Optional)</label>
      <textarea id="newCourseSyllabus" class="field-input" rows="3" bind:value={newCourseSyllabus} placeholder="Key topics, preliminary reading units..."></textarea>
    </div>
    {#if createFeedback}<div class="feedback-error">{createFeedback}</div>{/if}
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" onclick={onClose}>Cancel</button>
      <button type="submit" class="btn btn-primary" disabled={isCreating}>
        {isCreating ? 'Creating Workspace...' : '+ Create Course Workspace'}
      </button>
    </div>
  </form>
</Modal>

<style>
  .modal-desc {
    font-size: 13px;
    color: var(--color-slate-light);
    line-height: 1.5;
    margin: 0 0 20px;
  }

  .create-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }

  .field-label {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--color-slate-light);
    letter-spacing: 0.4px;
  }

  .req {
    color: var(--color-rose);
  }

  .field-input {
    background: var(--input-bg);
    border: 1px solid var(--input-border);
    color: var(--color-slate-bright);
    padding: 10px 14px;
    border-radius: var(--radius-sm);
    font-size: 13.5px;
    font-family: var(--font-ui);
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.15s;
  }
  .field-input:focus {
    outline: none;
    border-color: var(--input-focus-border);
  }

  textarea.field-input {
    resize: vertical;
  }

  .feedback-error {
    font-size: 12px;
    padding: 8px 12px;
    border-radius: var(--radius-xs);
    background: var(--color-rose-bg);
    color: var(--color-rose-text);
    border: 1px solid var(--color-rose);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    border-top: 1px solid var(--color-graphite-border);
    padding-top: 16px;
  }
</style>
