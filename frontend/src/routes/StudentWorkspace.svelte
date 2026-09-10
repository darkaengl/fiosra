<script>
  import { onMount } from 'svelte';
  import {
    getStudentId,
    responseError,
    routeParams,
    sessionAccessTokenStorageKey,
    sessionStorageKey,
  } from '../lib/session.js';

  let courseId = $state('');
  let assignmentId = $state('');
  let assignment = $state(null);
  let sources = $state([]);
  let studentId = $state('');
  let sessionId = $state('');
  let sessionAccessToken = $state('');
  let sessionStatus = $state('active');
  let userMessage = $state('');
  let currentRung = $state(0);
  let isLoading = $state(true);
  let isTyping = $state(false);
  let isSavingCanvas = $state(false);
  let isRequestingSupport = $state(false);
  let error = $state('');
  let messages = $state([]);
  let canvasSections = $state([]);
  let canvasDrafts = $state({});
  let canvasSuggestions = $state({});
  let activeSectionId = $state('working_claim');
  let activeSuggestion = $state(null);
  let activeSectionText = $state('');
  let activeSourceReferences = $state([]);
  let isAssistDrawerOpen = $state(false);
  let isBriefOpen = $state(false);
  let isCommandMenuOpen = $state(false);
  let isSourcePickerOpen = $state(false);
  let commandQuery = $state('');
  let sourceQuery = $state('');
  let highlightedMenuIndex = $state(0);

  const commandDefinitions = [
    {
      id: 'question',
      shortcut: '/question',
      label: 'Ask a section question',
      detail: 'Request one answer-blind question about this section.',
      kind: 'support',
      supportKind: 'section_question',
    },
    {
      id: 'frame',
      shortcut: '/frame',
      label: 'Request a writing frame',
      detail: 'Open a neutral, editable structure—not a completed answer.',
      kind: 'support',
      supportKind: 'writing_frame',
    },
    {
      id: 'source',
      shortcut: '/source',
      label: 'Recall approved sources',
      detail: 'Ask for a source-oriented prompt for the active section.',
      kind: 'support',
      supportKind: 'source_reminder',
    },
    {
      id: 'hint',
      shortcut: '/hint',
      label: 'Request a bounded hint',
      detail: 'Ask the server for the next available Socratic support rung.',
      kind: 'hint',
    },
    {
      id: 'brief',
      shortcut: '/brief',
      label: 'Show assignment brief',
      detail: 'Review the task, sources, and support policy without leaving your draft.',
      kind: 'brief',
    },
  ];

  let activeSection = $derived(
    canvasSections.find((section) => section.section_id === activeSectionId) || canvasSections[0] || null,
  );
  let activeDraft = $derived(
    canvasDrafts[activeSectionId] || {
      section_id: activeSectionId,
      text: '',
      revision: 0,
      source_references: [],
    },
  );
  let sourceById = $derived(Object.fromEntries(sources.map((source) => [source.chunk_id, source])));
  let filteredCommands = $derived(
    commandDefinitions.filter((command) => {
      const query = commandQuery.toLowerCase();
      return !query || command.id.includes(query) || command.label.toLowerCase().includes(query);
    }),
  );
  let filteredSources = $derived(
    sources.filter((source) => {
      const query = sourceQuery.toLowerCase();
      return !query || `${source.title || ''} ${source.excerpt || ''}`.toLowerCase().includes(query);
    }),
  );
  let savedSectionCount = $derived(
    canvasSections.filter((section) => canvasDrafts[section.section_id]?.text?.trim()).length,
  );

  function appendMessage(role, content, meta = {}) {
    messages = [...messages, { role, content, ...meta }];
  }

  function canvasHeaders() {
    return { 'X-Fiosra-Session-Token': sessionAccessToken, 'Content-Type': 'application/json' };
  }

  function resetActiveEditor(sectionId) {
    activeSectionId = sectionId;
    const draft = canvasDrafts[sectionId] || { text: '', source_references: [] };
    activeSectionText = draft.text || '';
    activeSourceReferences = draft.source_references || [];
    activeSuggestion = canvasSuggestions[sectionId] || null;
    isCommandMenuOpen = false;
    isSourcePickerOpen = false;
    commandQuery = '';
    sourceQuery = '';
  }

  async function loadCanvas() {
    if (!sessionId || !sessionAccessToken) return;
    const response = await fetch(`/learning-canvas/sessions/${sessionId}`, { headers: canvasHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your evidence canvas could not be restored.'));
    const canvas = await response.json();
    sessionStatus = canvas.status;
    canvasSections = canvas.sections || [];
    canvasDrafts = Object.fromEntries((canvas.drafts || []).map((draft) => [draft.section_id, draft]));
    canvasSuggestions = Object.fromEntries(
      (canvas.suggestions || []).map((suggestion) => [suggestion.section_id, suggestion]),
    );
    const visibleSection = canvasSections.some((section) => section.section_id === activeSectionId)
      ? activeSectionId
      : canvasSections[0]?.section_id;
    if (visibleSection) resetActiveEditor(visibleSection);
  }

  async function loadAssignment() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    assignmentId = params.get('assignment_id') || '';

    if (assignmentId) {
      const response = await fetch(`/assignments/${assignmentId}`);
      if (!response.ok) throw new Error(await responseError(response, 'The requested assignment could not be loaded.'));
      assignment = await response.json();
    } else if (courseId) {
      const response = await fetch(`/assignments?course_id=${encodeURIComponent(courseId)}&status=published`);
      if (!response.ok) throw new Error(await responseError(response, 'Published assignments could not be loaded.'));
      const assignments = await response.json();
      assignment = assignments[0] || null;
      assignmentId = assignment?.assignment_id || '';
    }

    if (!assignment) return;
    studentId = getStudentId();
    sources = assignment.grounding_sources || [];
    const key = sessionStorageKey(assignmentId, studentId);
    const persistedSessionId = localStorage.getItem(key);
    const persistedAccessToken = persistedSessionId
      ? localStorage.getItem(sessionAccessTokenStorageKey(persistedSessionId))
      : '';

    if (persistedSessionId && persistedAccessToken) {
      const existing = await fetch(`/events/session/${persistedSessionId}`, {
        headers: { 'X-Fiosra-Session-Token': persistedAccessToken },
      });
      if (existing.ok) {
        const session = (await existing.json()).session;
        if (session.status === 'active') {
          sessionId = persistedSessionId;
          sessionAccessToken = persistedAccessToken;
          sessionStatus = session.status;
        }
      }
    }

    if (!sessionId) {
      const response = await fetch('/events/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          assignment_id: assignmentId,
          current_question_id: assignment.question_id,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'A reasoning session could not be started.'));
      const created = await response.json();
      sessionId = created.session_id;
      sessionAccessToken = created.access_token;
      sessionStatus = created.status;
      localStorage.setItem(key, sessionId);
      localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
    }

    const replay = await fetch(`/events/session/${sessionId}`, {
      headers: { 'X-Fiosra-Session-Token': sessionAccessToken },
    });
    if (replay.ok) {
      const { events } = await replay.json();
      const restored = [];
      for (const event of events) {
        if (event.event_type === 'student_prompt_submitted') {
          restored.push({ role: 'user', content: event.payload.student_input });
        }
        if (['tutor_turn_completed', 'hint_delivered', 'adversarial_probe_defended'].includes(event.event_type)) {
          restored.push({
            role: 'assistant',
            content: event.payload.response_text,
            hintRung: event.payload.hint_rung,
            isAdversarial: event.event_type === 'adversarial_probe_defended',
          });
          currentRung = Math.max(currentRung, event.payload.hint_rung || 0);
        }
      }
      messages = restored;
    }
    await loadCanvas();
  }

  async function sendMessage({ hintRequested = false } = {}) {
    const draft = hintRequested ? 'I need a hint to continue developing my argument.' : userMessage.trim();
    if (!draft || !assignment || !sessionId || sessionStatus !== 'active') return;

    if (!hintRequested) userMessage = '';
    appendMessage('user', draft);
    isTyping = true;
    error = '';
    isAssistDrawerOpen = true;
    try {
      const response = await fetch('/dialogue/message', {
        method: 'POST',
        headers: canvasHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          assignment_id: assignmentId,
          question_id: assignment.question_id,
          active_section_id: activeSectionId,
          question_prompt: assignment.prompt,
          domain: assignment.domain,
          student_input: draft,
          current_rung: currentRung,
          hint_requested: hintRequested,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The Socratic guide could not respond.'));
      const result = await response.json();
      currentRung = Math.max(currentRung, result.hint_rung || 0);
      appendMessage('assistant', result.response_text, {
        hintRung: result.hint_rung,
        isAdversarial: result.is_adversarial,
      });
    } catch (err) {
      error = err.message || 'The message could not be sent.';
      messages = messages.slice(0, -1);
      if (!hintRequested) userMessage = draft;
    } finally {
      isTyping = false;
    }
  }

  function selectSection(sectionId) {
    if (isSavingCanvas || isRequestingSupport) return;
    resetActiveEditor(sectionId);
  }

  function citeSource(source) {
    if (!activeSection) return;
    if (activeSourceReferences.some((reference) => reference.chunk_id === source.chunk_id)) return;
    activeSourceReferences = [
      ...activeSourceReferences,
      {
        chunk_id: source.chunk_id,
        quote: source.excerpt || '',
        rationale: `Selected for ${activeSection.label.toLowerCase()}.`,
      },
    ];
  }

  function selectSourceFromEditor(source) {
    citeSource(source);
    activeSectionText = activeSectionText.replace(/(?:^|\s)@[^\s]*$/, ' ').replace(/\s{2,}/g, ' ');
    isSourcePickerOpen = false;
    sourceQuery = '';
  }

  function removeSourceReference(chunkId) {
    activeSourceReferences = activeSourceReferences.filter((reference) => reference.chunk_id !== chunkId);
  }

  async function saveActiveSection({ fromSuggestion = false } = {}) {
    if (!activeSection || !sessionId || sessionStatus !== 'active') return;
    isSavingCanvas = true;
    error = '';
    try {
      let response;
      if (fromSuggestion && activeSuggestion) {
        response = await fetch(
          `/learning-canvas/sessions/${sessionId}/suggestions/${activeSuggestion.suggestion_id}/accept`,
          {
            method: 'POST',
            headers: canvasHeaders(),
            body: JSON.stringify({ text: activeSectionText, source_references: activeSourceReferences }),
          },
        );
      } else {
        response = await fetch(`/learning-canvas/sessions/${sessionId}/sections/${activeSection.section_id}`, {
          method: 'PUT',
          headers: canvasHeaders(),
          body: JSON.stringify({
            text: activeSectionText,
            base_revision: activeDraft.revision || 0,
            source_references: activeSourceReferences,
            author_type: 'student',
          }),
        });
      }
      if (!response.ok) throw new Error(await responseError(response, 'This section could not be saved.'));
      const result = await response.json();
      const updatedDraft = fromSuggestion ? result.draft : result;
      canvasDrafts = { ...canvasDrafts, [activeSection.section_id]: updatedDraft };
      if (fromSuggestion) canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: null };
      activeSuggestion = null;
      activeSectionText = updatedDraft.text;
      activeSourceReferences = updatedDraft.source_references || [];
    } catch (err) {
      error = err.message || 'This section could not be saved.';
    } finally {
      isSavingCanvas = false;
    }
  }

  async function requestSectionSupport(kind) {
    if (!activeSection || !sessionId || sessionStatus !== 'active') return;
    isRequestingSupport = true;
    error = '';
    isAssistDrawerOpen = true;
    try {
      const response = await fetch(`/learning-canvas/sessions/${sessionId}/suggestions`, {
        method: 'POST',
        headers: canvasHeaders(),
        body: JSON.stringify({
          section_id: activeSection.section_id,
          kind,
          base_revision: activeDraft.revision || 0,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Section support could not be prepared.'));
      activeSuggestion = await response.json();
      canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: activeSuggestion };
    } catch (err) {
      error = err.message || 'Section support could not be prepared.';
    } finally {
      isRequestingSupport = false;
    }
  }

  function editSuggestion() {
    if (!activeSuggestion) return;
    activeSectionText = activeSuggestion.content;
    isAssistDrawerOpen = false;
  }

  async function dismissSuggestion() {
    if (!activeSuggestion || !sessionId) return;
    isRequestingSupport = true;
    try {
      const response = await fetch(
        `/learning-canvas/sessions/${sessionId}/suggestions/${activeSuggestion.suggestion_id}/dismiss`,
        {
          method: 'POST',
          headers: canvasHeaders(),
          body: JSON.stringify({ reason: 'Student chose to continue independently.' }),
        },
      );
      if (!response.ok) throw new Error(await responseError(response, 'The support card could not be dismissed.'));
      canvasSuggestions = { ...canvasSuggestions, [activeSection.section_id]: null };
      activeSuggestion = null;
    } catch (err) {
      error = err.message || 'The support card could not be dismissed.';
    } finally {
      isRequestingSupport = false;
    }
  }

  function openCommandMenu() {
    isSourcePickerOpen = false;
    isCommandMenuOpen = true;
    commandQuery = '';
    highlightedMenuIndex = 0;
  }

  function openSourcePicker() {
    isCommandMenuOpen = false;
    isSourcePickerOpen = true;
    sourceQuery = '';
    highlightedMenuIndex = 0;
  }

  async function executeEditorCommand(command) {
    if (!command) return;
    activeSectionText = activeSectionText.replace(/(?:^|\s)\/[a-zA-Z ]*$/, ' ').replace(/\s{2,}/g, ' ');
    isCommandMenuOpen = false;
    commandQuery = '';
    if (command.kind === 'support') await requestSectionSupport(command.supportKind);
    if (command.kind === 'hint') await sendMessage({ hintRequested: true });
    if (command.kind === 'brief') isBriefOpen = true;
  }

  function handleEditorInput(event) {
    activeSectionText = event.currentTarget.value;
    const beforeCaret = activeSectionText.slice(0, event.currentTarget.selectionStart || activeSectionText.length);
    const commandMatch = beforeCaret.match(/(?:^|\s)\/([a-zA-Z ]*)$/);
    const sourceMatch = beforeCaret.match(/(?:^|\s)@([^\s]*)$/);
    if (commandMatch) {
      commandQuery = commandMatch[1].trim();
      isCommandMenuOpen = true;
      isSourcePickerOpen = false;
      highlightedMenuIndex = 0;
    } else if (sourceMatch) {
      sourceQuery = sourceMatch[1].trim();
      isSourcePickerOpen = true;
      isCommandMenuOpen = false;
      highlightedMenuIndex = 0;
    } else {
      isCommandMenuOpen = false;
      isSourcePickerOpen = false;
    }
  }

  function handleEditorKeydown(event) {
    const currentMenu = isCommandMenuOpen ? filteredCommands : isSourcePickerOpen ? filteredSources : [];
    if (event.key === 'Escape') {
      isCommandMenuOpen = false;
      isSourcePickerOpen = false;
      isBriefOpen = false;
      return;
    }
    if (!currentMenu.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      highlightedMenuIndex = (highlightedMenuIndex + 1) % currentMenu.length;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      highlightedMenuIndex = (highlightedMenuIndex - 1 + currentMenu.length) % currentMenu.length;
    }
    if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault();
      if (isCommandMenuOpen) executeEditorCommand(currentMenu[highlightedMenuIndex]);
      if (isSourcePickerOpen) selectSourceFromEditor(currentMenu[highlightedMenuIndex]);
    }
  }

  onMount(async () => {
    try {
      await loadAssignment();
    } catch (err) {
      error = err.message || 'The learning workspace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });
</script>

{#if isLoading}
  <main class="loading-view"><div class="spinner"></div><p>Opening your writing workspace…</p></main>
{:else if error && !assignment}
  <main class="empty-view"><h1>Workspace unavailable</h1><p>{error}</p><a class="btn btn-primary" href="#/courses">Return to courses</a></main>
{:else if !assignment}
  <main class="empty-view"><h1>No published assignment selected</h1><p>Open a published assignment from a curriculum module to start a protected reasoning session.</p><a class="btn btn-primary" href="#/courses">Choose a course</a></main>
{:else}
  <div class:drawer-open={isAssistDrawerOpen} class="writer-layout">
    <aside class="section-rail" aria-label="Reasoning sections">
      <a class="trace-link" href={`#/student/trace?course_id=${encodeURIComponent(courseId)}&assignment_id=${encodeURIComponent(assignmentId)}&session_id=${encodeURIComponent(sessionId)}`} aria-label="View reasoning trace">↗</a>
      <div class="rail-progress"><strong>{savedSectionCount}</strong><span>of {canvasSections.length}</span></div>
      <nav class="section-nav" aria-label="Canvas sections">
        {#each canvasSections as section}
          {@const draft = canvasDrafts[section.section_id] || { text: '' }}
          <button class:active={section.section_id === activeSectionId} class:complete={draft.text?.trim()} onclick={() => selectSection(section.section_id)} aria-label={`${section.label}: ${draft.text?.trim() ? 'saved draft' : section.required ? 'required' : 'optional'}`}>
            <span>{section.position}</span><small>{section.label}</small>
          </button>
        {/each}
      </nav>
    </aside>

    <main class="writer-column">
      <header class="assignment-bar">
        <div class="assignment-identity"><span class="eyebrow">Active writing</span><h1>{assignment.title || 'Reasoning assignment'}</h1><span class="active-section-label">{activeSection?.label || 'Canvas'}</span></div>
        <div class="assignment-actions"><button class="quiet-control" onclick={() => isBriefOpen = true}>View brief</button><button class:active={isAssistDrawerOpen} class="assist-toggle" onclick={() => isAssistDrawerOpen = !isAssistDrawerOpen} aria-expanded={isAssistDrawerOpen}>Assist <span>⌘</span></button><span class:submitted={sessionStatus !== 'active'} class="session-badge">{sessionStatus}</span></div>
      </header>

      {#if activeSection}
        <section class="focus-canvas" aria-label={`${activeSection.label} editor`}>
          <header class="focus-heading"><div><div class="eyebrow">Student-authored section</div><h2>{activeSection.label}</h2><p>{activeSection.purpose}</p></div><span>Revision {activeDraft.revision || 0}</span></header>
          <p class="section-guidance">{activeSection.completion_guidance}</p>
          <div class="editor-toolbar" aria-label="Editor tools"><div><button class="editor-tool" onclick={openCommandMenu} disabled={sessionStatus !== 'active'}><kbd>/</kbd> Assist</button><button class="editor-tool" onclick={openSourcePicker} disabled={sessionStatus !== 'active'}><kbd>@</kbd> Sources</button></div><span>Type <kbd>/</kbd> for support or <kbd>@</kbd> for an approved source</span></div>
          <div class="editor-wrap">
            <textarea class="canvas-input" rows="18" maxlength={activeSection.max_characters} bind:value={activeSectionText} disabled={isSavingCanvas || sessionStatus !== 'active'} placeholder={`Write your ${activeSection.label.toLowerCase()} in your own words…`} oninput={handleEditorInput} onkeydown={handleEditorKeydown}></textarea>
            {#if isCommandMenuOpen}
              <div class="editor-menu" role="listbox" aria-label="Writing assistance commands">
                <div class="menu-heading">Bounded writing support <span>Esc to close</span></div>
                {#each filteredCommands as command, index}
                  <button class:highlighted={index === highlightedMenuIndex} onclick={() => executeEditorCommand(command)} role="option" aria-selected={index === highlightedMenuIndex}><kbd>{command.shortcut}</kbd><span><strong>{command.label}</strong><small>{command.detail}</small></span></button>
                {:else}
                  <p>No supported command matches. Try <kbd>/question</kbd>, <kbd>/frame</kbd>, or <kbd>/hint</kbd>.</p>
                {/each}
              </div>
            {:else if isSourcePickerOpen}
              <div class="editor-menu source-menu" role="listbox" aria-label="Approved assignment sources">
                <div class="menu-heading">Approved assignment sources <span>Esc to close</span></div>
                {#each filteredSources as source, index (source.chunk_id)}
                  <button class:highlighted={index === highlightedMenuIndex} onclick={() => selectSourceFromEditor(source)} role="option" aria-selected={index === highlightedMenuIndex}><kbd>@</kbd><span><strong>{source.title || 'Course material'}</strong><small>{source.excerpt || 'No excerpt available.'}</small></span></button>
                {:else}
                  <p>No approved source matches this search.</p>
                {/each}
              </div>
            {/if}
          </div>
          <div class="canvas-status"><span>{activeSectionText.length} / {activeSection.max_characters} characters</span>{#if activeDraft.author_type === 'student_edited_assistance'}<span class="assistance-label">You edited an optional support frame</span>{:else if activeDraft.author_type === 'student'}<span>Student-authored</span>{/if}</div>
          {#if activeSourceReferences.length}
            <div class="selected-sources" aria-label="Sources attached to this draft"><strong>Attached evidence</strong>{#each activeSourceReferences as reference}<span><button aria-label="Remove source reference" onclick={() => removeSourceReference(reference.chunk_id)}>×</button>{sourceById[reference.chunk_id]?.title || 'Approved course source'}</span>{/each}</div>
          {/if}
          {#if error}<div class="error-banner" role="alert">{error}</div>{/if}
          <footer class="canvas-footer"><span>Your draft remains yours. Assistance is optional and tracked separately.</span><button class="btn btn-primary" onclick={() => saveActiveSection()} disabled={isSavingCanvas || sessionStatus !== 'active'}>{isSavingCanvas ? 'Saving…' : 'Save my section'}</button></footer>
        </section>
      {/if}
    </main>

    <aside class="assist-drawer" aria-label="Optional writing assistance" aria-hidden={!isAssistDrawerOpen} onkeydown={(event) => { if (event.key === 'Escape') isAssistDrawerOpen = false; }}>
      <header class="drawer-header"><div><div class="eyebrow">Optional assistant</div><h2>{activeSection?.label || 'Writing support'}</h2><p>Ask, structure, or inspect your work. The guide does not complete it.</p></div><button class="drawer-close" onclick={() => isAssistDrawerOpen = false} aria-label="Close assistance drawer">×</button></header>
      <section class="drawer-policy"><span>Support rung {currentRung} / 3</span><p>Hints advance only after an explicit request. The bottom-out solution is locked.</p></section>
      {#if activeSuggestion}
        <section class="support-card"><div class="support-card-heading"><span>{activeSuggestion.kind === 'section_question' ? 'Socratic question' : activeSuggestion.kind === 'source_reminder' ? 'Source reminder' : 'Optional writing frame'}</span><small>Nothing has been saved automatically.</small></div><p>{activeSuggestion.content}</p><div><button class="btn btn-secondary" onclick={editSuggestion}>Use as editable frame</button><button class="btn btn-primary" onclick={() => saveActiveSection({ fromSuggestion: true })} disabled={!activeSectionText.trim() || isSavingCanvas}>Apply & save my edit</button><button class="btn-link" onclick={dismissSuggestion} disabled={isRequestingSupport}>Dismiss</button></div></section>
      {:else}
        <section class="quick-assists"><h3>Choose a bounded assist</h3><button onclick={() => requestSectionSupport('section_question')} disabled={isRequestingSupport || sessionStatus !== 'active'}>Ask a section question</button><button onclick={() => requestSectionSupport('writing_frame')} disabled={isRequestingSupport || sessionStatus !== 'active'}>Request a writing frame</button><button onclick={() => requestSectionSupport('source_reminder')} disabled={isRequestingSupport || sessionStatus !== 'active'}>Recall approved sources</button></section>
      {/if}
      <section class="dialogue-history"><h3>Recent Socratic dialogue</h3>{#if messages.length === 0}<p class="drawer-empty">No guidance has been requested. Keep writing, then invoke <kbd>/</kbd> when you want help.</p>{:else}{#each messages.slice(-6) as msg}<article class:student={msg.role === 'user'} class:guide={msg.role === 'assistant'}><span>{msg.role === 'assistant' ? 'Fiosra' : 'You'}</span>{#if msg.isAdversarial}<strong>Integrity boundary</strong>{/if}<p>{msg.content}</p></article>{/each}{/if}</section>
      <section class="ask-guide"><label for="guide-question">Think aloud with the guide</label><textarea id="guide-question" placeholder="Ask about an assumption, source observation, or your reasoning…" rows="3" bind:value={userMessage} disabled={isTyping || sessionStatus !== 'active'} onkeydown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); } }}></textarea><div><button class="btn btn-secondary" onclick={() => sendMessage({ hintRequested: true })} disabled={isTyping || sessionStatus !== 'active' || currentRung >= 3}>Request a hint</button><button class="btn btn-primary" onclick={() => sendMessage()} disabled={!userMessage.trim() || isTyping || sessionStatus !== 'active'}>{isTyping ? 'Thinking…' : 'Send question'}</button></div></section>
    </aside>
  </div>

  {#if isBriefOpen}
    <div class="brief-overlay" role="presentation" onclick={() => isBriefOpen = false}>
      <dialog class="brief-dialog" open aria-label="Assignment brief" onclick={(event) => event.stopPropagation()} onkeydown={(event) => { if (event.key === 'Escape') isBriefOpen = false; }}><header><div><div class="eyebrow">Assignment brief</div><h2>{assignment.title || 'Reasoning assignment'}</h2></div><button onclick={() => isBriefOpen = false} aria-label="Close assignment brief">×</button></header><p class="brief-prompt">{assignment.prompt}</p><div class="brief-grid"><div><h3>Target knowledge components</h3>{#each assignment.target_kcs || [] as kc}<code>{kc}</code>{/each}</div><div><h3>Approved sources</h3>{#each sources as source}<p><strong>{source.title || 'Course material'}</strong><span>{source.excerpt || ''}</span></p>{:else}<p>No source excerpts are available.</p>{/each}</div></div><footer><span>AI tools can question, structure, or locate evidence. They cannot complete your answer.</span><button class="btn btn-primary" onclick={() => isBriefOpen = false}>Return to writing</button></footer></dialog>
    </div>
  {/if}
{/if}

<style>
  .writer-layout{background:var(--color-obsidian);display:grid;grid-template-columns:84px minmax(0,1fr) 0;min-height:calc(100vh - 56px);transition:grid-template-columns .22s ease}.writer-layout.drawer-open{grid-template-columns:84px minmax(0,1fr) minmax(320px,380px)}.section-rail{align-items:center;background:var(--color-graphite);border-right:1px solid var(--color-graphite-border);display:flex;flex-direction:column;gap:22px;padding:18px 10px}.trace-link{align-items:center;border:1px solid var(--color-graphite-border);border-radius:50%;color:var(--color-horizon-bright);display:flex;font-size:18px;height:32px;justify-content:center;text-decoration:none;width:32px}.trace-link:hover{border-color:var(--color-horizon-bright)}.rail-progress{align-items:center;border-bottom:1px solid var(--color-graphite-border);color:var(--color-slate-muted);display:flex;flex-direction:column;padding-bottom:15px;width:100%}.rail-progress strong{color:#fff;font-family:var(--font-brand);font-size:22px}.rail-progress span{font-size:9px;text-transform:uppercase}.section-nav{display:flex;flex-direction:column;gap:6px;width:100%}.section-nav button{align-items:center;background:transparent;border:1px solid transparent;border-radius:var(--radius-sm);color:var(--color-slate-muted);cursor:pointer;display:flex;flex-direction:column;gap:4px;min-height:54px;padding:6px 2px}.section-nav button:hover,.section-nav button.active{background:rgba(59,130,246,.1);border-color:rgba(59,130,246,.28);color:#fff}.section-nav button.complete>span{border-color:#34d399;color:#6ee7b7}.section-nav button>span{align-items:center;border:1px solid var(--color-graphite-border);border-radius:50%;display:flex;font-size:10px;font-weight:700;height:22px;justify-content:center;width:22px}.section-nav small{font-size:8px;line-height:1.1;max-width:62px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.writer-column{min-width:0;padding:0 clamp(18px,4vw,68px) 56px}.assignment-bar{align-items:center;border-bottom:1px solid var(--color-graphite-border);display:flex;gap:18px;justify-content:space-between;min-height:82px}.assignment-identity{align-items:baseline;display:flex;gap:11px;min-width:0}.eyebrow{color:var(--color-slate-muted);font-size:10px;font-weight:700;letter-spacing:.55px;text-transform:uppercase}.assignment-identity h1{color:#fff;font-family:var(--font-brand);font-size:16px;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.active-section-label{color:var(--color-horizon-bright);font-size:11px;font-weight:700;white-space:nowrap}.assignment-actions{align-items:center;display:flex;gap:8px}.quiet-control,.assist-toggle{background:transparent;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:var(--color-slate-light);cursor:pointer;font-size:11px;font-weight:700;padding:8px 10px}.quiet-control:hover,.assist-toggle:hover,.assist-toggle.active{border-color:var(--color-horizon-bright);color:#fff}.assist-toggle{color:#bae6fd}.assist-toggle span{font-size:10px;margin-left:4px;opacity:.7}.session-badge{background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.25);border-radius:99px;color:#34d399;font-size:10px;font-weight:700;padding:5px 9px;text-transform:capitalize;white-space:nowrap}.session-badge.submitted{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.25);color:var(--color-amber)}.focus-canvas{display:flex;flex-direction:column;gap:14px;margin:clamp(24px,6vh,66px) auto 0;max-width:1000px}.focus-heading{align-items:flex-start;display:flex;gap:18px;justify-content:space-between}.focus-heading h2{color:#fff;font-family:var(--font-brand);font-size:clamp(26px,3.2vw,38px);letter-spacing:-.6px;margin:5px 0 8px}.focus-heading p{color:var(--color-slate-light);font-size:14px;line-height:1.55;margin:0;max-width:670px}.focus-heading>span{color:var(--color-horizon-bright);font-size:10px;font-weight:700;margin-top:5px;white-space:nowrap}.section-guidance{border-left:2px solid var(--color-horizon-blue);color:var(--color-slate-light);font-size:13px;line-height:1.5;margin:0;padding:7px 11px}.editor-toolbar{align-items:center;color:var(--color-slate-muted);display:flex;font-size:11px;justify-content:space-between;margin-top:10px}.editor-toolbar>div{display:flex;gap:7px}.editor-tool{background:rgba(30,41,59,.65);border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:#cbd5e1;cursor:pointer;font-size:11px;font-weight:700;padding:6px 8px}.editor-tool:hover:not(:disabled){border-color:var(--color-horizon-blue);color:#fff}.editor-tool:disabled{cursor:not-allowed;opacity:.5}kbd{background:rgba(59,130,246,.16);border:1px solid rgba(59,130,246,.24);border-radius:3px;color:#bae6fd;font:inherit;font-size:10px;padding:1px 4px}.editor-wrap{position:relative}.canvas-input{background:#101923;border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);box-sizing:border-box;color:#f8fafc;font-family:var(--font-body);font-size:16px;line-height:1.75;min-height:430px;padding:28px 30px;resize:vertical;width:100%}.canvas-input:focus{border-color:var(--color-horizon-blue);box-shadow:0 0 0 3px rgba(59,130,246,.09);outline:none}.canvas-input::placeholder{color:#64748b}.editor-menu{background:#172334;border:1px solid rgba(96,165,250,.45);border-radius:var(--radius-md);box-shadow:0 20px 50px rgba(0,0,0,.35);left:18px;max-width:580px;padding:7px;position:absolute;top:18px;width:calc(100% - 36px);z-index:10}.menu-heading{color:#94a3b8;display:flex;font-size:10px;font-weight:700;justify-content:space-between;letter-spacing:.35px;padding:7px 9px;text-transform:uppercase}.menu-heading span{color:#64748b;font-weight:500;letter-spacing:0;text-transform:none}.editor-menu button{align-items:flex-start;background:transparent;border:1px solid transparent;border-radius:var(--radius-sm);color:#e2e8f0;cursor:pointer;display:flex;gap:10px;padding:9px;text-align:left;width:100%}.editor-menu button:hover,.editor-menu button.highlighted{background:rgba(59,130,246,.13);border-color:rgba(59,130,246,.25)}.editor-menu button>span{display:flex;flex-direction:column;gap:2px;min-width:0}.editor-menu strong{font-size:12px}.editor-menu small{color:#94a3b8;font-size:11px;line-height:1.35;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.editor-menu>p{color:#94a3b8;font-size:11px;margin:8px}.canvas-status{color:var(--color-slate-muted);display:flex;font-size:10px;justify-content:space-between}.assistance-label{color:#c4b5fd}.selected-sources{align-items:center;color:var(--color-slate-light);display:flex;flex-wrap:wrap;font-size:11px;gap:6px}.selected-sources strong{color:var(--color-slate-muted);font-size:10px;text-transform:uppercase}.selected-sources span{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);border-radius:99px;color:#bae6fd;padding:4px 7px}.selected-sources button{background:none;border:0;color:#7dd3fc;cursor:pointer;font-size:14px;padding:0 3px}.canvas-footer{align-items:center;border-top:1px solid var(--color-graphite-border);color:var(--color-slate-muted);display:flex;font-size:11px;justify-content:space-between;margin-top:10px;padding-top:14px}.error-banner{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:var(--radius-sm);color:#fca5a5;font-size:12px;padding:9px 12px}.assist-drawer{background:var(--color-graphite);border-left:1px solid var(--color-graphite-border);display:flex;flex-direction:column;overflow:hidden;padding:22px 18px;transition:opacity .15s ease,visibility .15s ease;visibility:hidden}.drawer-open .assist-drawer{visibility:visible}.drawer-header{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;gap:9px;justify-content:space-between;padding-bottom:15px}.drawer-header h2{color:#fff;font-size:16px;margin:4px 0}.drawer-header p{color:var(--color-slate-muted);font-size:11px;line-height:1.5;margin:0;max-width:270px}.drawer-close{background:none;border:0;color:#94a3b8;cursor:pointer;font-size:24px;line-height:1;padding:0}.drawer-close:hover{color:#fff}.drawer-policy{background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.2);border-radius:var(--radius-sm);margin-top:15px;padding:10px}.drawer-policy span{color:#7dd3fc;font-size:11px;font-weight:700}.drawer-policy p{color:#94a3b8;font-size:10px;line-height:1.45;margin:5px 0 0}.support-card{background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.35);border-radius:var(--radius-md);display:flex;flex-direction:column;gap:10px;margin-top:15px;padding:13px}.support-card-heading{align-items:center;color:#ddd6fe;display:flex;font-size:10px;font-weight:700;justify-content:space-between;text-transform:uppercase}.support-card-heading small{color:#c4b5fd;font-size:9px;font-weight:500;text-transform:none}.support-card p{color:#ede9fe;font-size:12px;line-height:1.55;margin:0;white-space:pre-wrap}.support-card>div:last-child{display:flex;flex-wrap:wrap;gap:7px}.btn-link{background:none;border:0;color:#c4b5fd;cursor:pointer;font-size:11px;text-decoration:underline}.quick-assists{display:flex;flex-direction:column;gap:7px;margin-top:15px}.quick-assists h3,.dialogue-history h3{color:#e2e8f0;font-size:11px;letter-spacing:.25px;margin:0;text-transform:uppercase}.quick-assists button{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:#cbd5e1;cursor:pointer;font-size:11px;padding:9px;text-align:left}.quick-assists button:hover:not(:disabled){border-color:var(--color-horizon-blue);color:#fff}.quick-assists button:disabled{cursor:not-allowed;opacity:.5}.dialogue-history{border-top:1px solid var(--color-graphite-border);display:flex;flex:1;flex-direction:column;gap:8px;margin-top:17px;min-height:110px;overflow-y:auto;padding-top:15px}.dialogue-history article{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);padding:8px}.dialogue-history article.student{border-left:2px solid #10b981}.dialogue-history article.guide{border-left:2px solid var(--color-horizon-blue)}.dialogue-history article>span{color:#94a3b8;font-size:9px;font-weight:700;text-transform:uppercase}.dialogue-history article>strong{color:var(--color-amber);display:block;font-size:9px;margin-top:4px;text-transform:uppercase}.dialogue-history article p{color:#cbd5e1;font-size:11px;line-height:1.42;margin:4px 0 0}.drawer-empty{color:#94a3b8;font-size:11px;line-height:1.5;margin:0}.ask-guide{border-top:1px solid var(--color-graphite-border);display:flex;flex-direction:column;gap:7px;margin-top:14px;padding-top:14px}.ask-guide label{color:#cbd5e1;font-size:10px;font-weight:700;text-transform:uppercase}.ask-guide textarea{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:#fff;font:inherit;font-size:11px;line-height:1.45;padding:8px;resize:vertical}.ask-guide textarea:focus{border-color:var(--color-horizon-blue);outline:none}.ask-guide>div{display:flex;gap:7px;justify-content:space-between}.brief-overlay{align-items:center;background:rgba(2,6,23,.75);display:flex;inset:0;justify-content:center;padding:24px;position:fixed;z-index:30}.brief-dialog{background:var(--color-graphite);border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);box-shadow:0 24px 70px rgba(0,0,0,.5);max-width:820px;padding:24px;width:min(100%,820px)}.brief-dialog header{align-items:flex-start;border-bottom:1px solid var(--color-graphite-border);display:flex;justify-content:space-between;padding-bottom:14px}.brief-dialog h2{color:#fff;font-size:20px;margin:4px 0 0}.brief-dialog header button{background:none;border:0;color:#94a3b8;cursor:pointer;font-size:25px;line-height:1}.brief-prompt{color:#e2e8f0;font-size:14px;line-height:1.65;margin:18px 0}.brief-grid{display:grid;gap:15px;grid-template-columns:.8fr 1.2fr}.brief-grid>div{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);display:flex;flex-direction:column;gap:7px;padding:13px}.brief-grid h3{color:#e2e8f0;font-size:11px;letter-spacing:.35px;margin:0;text-transform:uppercase}.brief-grid code{color:#c4b5fd;font-size:10px;overflow-wrap:anywhere}.brief-grid p{color:#94a3b8;font-size:11px;line-height:1.4;margin:0}.brief-grid p strong{color:#bae6fd;display:block;font-size:11px}.brief-grid p span{display:block;margin-top:3px}.brief-dialog footer{align-items:center;color:#94a3b8;display:flex;font-size:11px;gap:14px;justify-content:space-between;margin-top:17px}.loading-view,.empty-view{align-items:center;background:var(--color-obsidian);color:var(--color-slate-light);display:flex;flex-direction:column;gap:14px;justify-content:center;min-height:calc(100vh - 56px);padding:24px;text-align:center}.empty-view h1{color:#fff;font-family:var(--font-brand);font-size:24px}.empty-view p{max-width:520px}.spinner{animation:spin .8s linear infinite;border:3px solid rgba(59,130,246,.2);border-radius:50%;border-top-color:var(--color-horizon-bright);height:32px;width:32px}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:1080px){.writer-layout.drawer-open{grid-template-columns:70px minmax(0,1fr) minmax(290px,340px)}.writer-layout{grid-template-columns:70px minmax(0,1fr) 0}.section-rail{padding:14px 6px}.canvas-input{min-height:390px}.writer-column{padding-left:clamp(16px,3vw,32px);padding-right:clamp(16px,3vw,32px)}}@media(max-width:780px){.writer-layout,.writer-layout.drawer-open{display:block}.section-rail{align-items:center;border-bottom:1px solid var(--color-graphite-border);border-right:0;display:flex;flex-direction:row;gap:10px;overflow-x:auto;padding:10px 14px}.trace-link{flex:0 0 30px}.rail-progress{border-bottom:0;border-right:1px solid var(--color-graphite-border);flex:0 0 auto;padding:0 10px 0 0}.section-nav{display:flex;flex:1;flex-direction:row;min-width:max-content}.section-nav button{flex:0 0 74px;min-height:42px}.writer-column{padding:0 16px 42px}.assignment-bar{align-items:flex-start;flex-direction:column;gap:10px;padding:14px 0}.assignment-identity{align-items:flex-start;flex-wrap:wrap}.assignment-actions{width:100%}.focus-canvas{margin-top:28px}.canvas-input{font-size:15px;min-height:330px;padding:20px}.editor-toolbar,.canvas-footer{align-items:flex-start;flex-direction:column;gap:8px}.assist-drawer{bottom:0;border:1px solid var(--color-graphite-border);border-bottom:0;border-radius:var(--radius-lg) var(--radius-lg) 0 0;box-shadow:0 -18px 50px rgba(0,0,0,.38);display:none;left:0;max-height:78vh;position:fixed;right:0;z-index:20}.drawer-open .assist-drawer{display:flex}.brief-grid{grid-template-columns:1fr}.brief-dialog footer{align-items:stretch;flex-direction:column}.brief-dialog footer .btn{width:100%}}@media(max-width:480px){.assignment-actions{flex-wrap:wrap}.focus-heading{flex-direction:column;gap:4px}.focus-heading h2{font-size:27px}.editor-menu{left:8px;width:calc(100% - 16px)}.canvas-footer .btn{width:100%}.canvas-footer{align-items:stretch}.section-nav button{flex-basis:66px}.section-nav small{max-width:54px}.editor-toolbar>span{display:none}}
</style>
