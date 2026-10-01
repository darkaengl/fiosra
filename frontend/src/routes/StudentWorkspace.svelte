<script>
  import { onMount, onDestroy } from 'svelte';
  import LongFormDocumentEditor from '../lib/LongFormDocumentEditor.svelte';
  import RightWorkbenchGutter from '../lib/RightWorkbenchGutter.svelte';
  import PrimarySourcesSidebar from '../lib/PrimarySourcesSidebar.svelte';
  import WorkspaceFlyoutPanel from '../lib/workspace/WorkspaceFlyoutPanel.svelte';
  import { fiosraContext } from '../lib/contextStore.svelte.js';
  import {
    getStudentId,
    responseError,
    routeParams,
    sessionAccessTokenStorageKey,
    sessionStorageKey,
  } from '../lib/session.js';
  import { learnerErrorSummary, responseErrorDetails } from '../lib/api-error.js';
  import {
    buildDefaultChatForStudent,
    loadStoredChatSessions,
    persistChatSessions,
  } from '../lib/workspace/workspaceConsultations';
  import {
    canonicalBlockAnalysis,
    computeGraphMetrics,
    normalizeAssignmentSources,
  } from '../lib/workspace/workspaceBlockUtils';

  let isSourcesCollapsed = $state(true);
  let isSourcesExpanded = $state(false);
  let isGutterCollapsed = $state(true);
  let activeGutterTab = $state('marginalia'); // 'marginalia' | 'agent'
  let isMacroBusy = $state(false);
  let isZenFullscreen = $state(false);
  let savedLayoutState = $state(null);

  // Draggable sidebar widths (Margin Sliders)
  let sourcesWidth = $state(
    (typeof localStorage !== 'undefined' && Number(localStorage.getItem('fiosra_sources_width'))) || 480
  );
  let gutterWidth = $state(
    (typeof localStorage !== 'undefined' && Number(localStorage.getItem('fiosra_gutter_width'))) || 440
  );
  let isResizingLeft = $state(false);
  let isResizingRight = $state(false);

  function startResizeLeft(e) {
    e.preventDefault();
    isResizingLeft = true;
    const startX = e.clientX;
    const startWidth = sourcesWidth;

    function onPointerMove(moveEvent) {
      const deltaX = moveEvent.clientX - startX;
      const maxAllowed = Math.max(300, window.innerWidth - 450);
      const newWidth = Math.min(maxAllowed, Math.max(260, startWidth + deltaX));
      sourcesWidth = Math.round(newWidth);
    }

    function onPointerUp() {
      isResizingLeft = false;
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      try {
        localStorage.setItem('fiosra_sources_width', String(sourcesWidth));
      } catch {}
    }

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  }

  function startResizeRight(e) {
    e.preventDefault();
    isResizingRight = true;
    const startX = e.clientX;
    const startWidth = gutterWidth;

    function onPointerMove(moveEvent) {
      const deltaX = startX - moveEvent.clientX;
      const maxAllowed = Math.max(300, window.innerWidth - 450);
      const newWidth = Math.min(maxAllowed, Math.max(260, startWidth + deltaX));
      gutterWidth = Math.round(newWidth);
    }

    function onPointerUp() {
      isResizingRight = false;
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      try {
        localStorage.setItem('fiosra_gutter_width', String(gutterWidth));
      } catch {}
    }

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  }

  function saveCurrentChatSessions() {
    persistChatSessions(chatSessions, assignmentId, studentId);
  }

  function loadChatSessionsForStudent(aid, sid) {
    chatSessions = loadStoredChatSessions(aid, sid);
    activeChatSessionId = chatSessions[0]?.id || `chat_${sid}_1`;
    saveCurrentChatSessions();
  }

  // Socratic Consultation Chat Threads
  let chatSessions = $state(buildDefaultChatForStudent(typeof window !== 'undefined' ? getStudentId() : 'julian_hayes'));
  let activeChatSessionId = $state(chatSessions[0]?.id || 'chat_init');

  let currentChatSession = $derived(
    chatSessions.find((cs) => cs.id === activeChatSessionId) || chatSessions[0]
  );
  let macroTurns = $derived(currentChatSession?.turns || []);

  function handleStartNewChatSession() {
    const nextNum = chatSessions.length + 1;
    const newSession = {
      id: `chat_${crypto.randomUUID().slice(0, 8)}`,
      title: `Consultation ${nextNum}`,
      startedAt: new Date().toISOString(),
      turns: [
        {
          role: 'tutor',
          text: `Welcome to Consultation ${nextNum}. How can I assist your critical inquiry today?`,
          thoughts: 'Fresh session initialization',
          hint_rung: 1,
          is_adversarial: false,
          action_capsules: [],
          radar: null,
          prompt_launchers: [
            { text: "Help me evaluate my evidence", category: "evidence" },
            { text: "Check my argument structure", category: "reasoning" }
          ]
        }
      ]
    };
    chatSessions = [...chatSessions, newSession];
    activeChatSessionId = newSession.id;
    saveCurrentChatSessions();
  }

  function handleSwitchChatSession(id) {
    activeChatSessionId = id;
    saveCurrentChatSessions();
  }

  let courseId = $state('');
  let assignmentId = $state('');
  let assignment = $state(null);
  let studentId = $state('');
  let sessionId = $state('');
  let sessionAccessToken = $state('');
  let sessionStatus = $state('active');
  let learningDocument = $state(null);
  let probes = $state([]);
  let evidenceSummary = $state({ pending_questions: 0, evidence_submitted: 0 });
  let sessionEvents = $state([]);
  let sessionInterventions = $state([]);
  let documentHeadings = $state([]);
  let isLoading = $state(true);

  let isTutorPanelOpen = $state(false);
  let activeProbeId = $state('');
  let currentProbe = $derived(probes.find((p) => p.probe_id === activeProbeId) || probes[0] || null);
  let probeResponse = $state('');
  let probeNotice = $state('');
  let isProbeBusy = $state(false);
  let error = $state('');
  let editorRef = $state(null);
  let supportResult = $state(null);
  let isSupportBusy = $state(false);
  let liveBlocks = $state([]);
  let oraclePressure = $state('socratic'); // 'socratic' | 'adversarial' | 'brainstorm' | 'structural' | 'hint' | 'assumptions'
  let isDrawerOpen = $state(false);
  let isSubmitting = $state(false);
  let submissionNotice = $state('');
  let submissionError = $state(null);
  let submittedRevision = $state(null);
  let submittedAt = $state('');
  let pendingSubmissionKey = $state('');
  let selectedSourceId = $state('');
  let sourceActionNotice = $state('');
  let sourceActionError = $state(null);
  let sourceActionBusy = $state(false);

  function handleToggleSourcesCollapse(val) {
    const willCollapse = val !== undefined ? val : !isSourcesCollapsed;
    isSourcesCollapsed = willCollapse;
    if (!willCollapse) {
      isSourcesExpanded = true;
    }
  }

  function handleToggleSourcesExpand() {
    if (isSourcesExpanded && !isSourcesCollapsed) {
      isSourcesExpanded = false;
      isSourcesCollapsed = true;
    } else {
      isSourcesExpanded = true;
      isSourcesCollapsed = false;
      isGutterCollapsed = true;
    }
  }

  function handleSelectGutterTab(tab) {
    activeGutterTab = tab;
    isGutterCollapsed = false;
    if (tab === 'submission' && gutterWidth < 540) {
      gutterWidth = 580;
    } else if ((tab === 'engagement' || tab === 'reasoning' || tab === 'activity') && gutterWidth < 480) {
      gutterWidth = 500;
    }
    if (isSourcesExpanded) {
      isSourcesExpanded = false;
      isSourcesCollapsed = true;
    }
  }

  function handleToggleGutterCollapse(val) {
    const willCollapse = val !== undefined ? val : !isGutterCollapsed;
    isGutterCollapsed = willCollapse;
    if (!willCollapse && isSourcesExpanded) {
      isSourcesExpanded = false;
      isSourcesCollapsed = true;
    }
  }

  let allDocumentBlocks = $derived.by(() => {
    if (liveBlocks && liveBlocks.length > 0) return liveBlocks;
    return (learningDocument?.blocks || []).map((b) => ({
      block_id: b.block_id,
      block_type: b.block_type,
      plaintext: b.plaintext || '',
      semantic_type: b.semantic_type || b.content?.attrs?.semanticType || 'claim',
      position: b.position,
      section_id: b.section_id,
    }));
  });

  let canonicalBlocks = $derived.by(() => allDocumentBlocks.map(canonicalBlockAnalysis));

  let graphMetrics = $derived.by(() => computeGraphMetrics(canonicalBlocks, probes));

  let published = $derived(assignment?.published || null);
  let assignmentSources = $derived.by(() => normalizeAssignmentSources(assignment));

  let activeSourceExhibit = $derived(
    assignmentSources.find((s) => s.source_id === selectedSourceId) || assignmentSources[0] || null
  );

  function sessionHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Fiosra-Session-Token': sessionAccessToken,
    };
  }

  function activeProbe() {
    return probes.find((probe) => probe.probe_id === activeProbeId) || probes[0] || null;
  }

  async function loadDocument() {
    let response = await fetch(`/learning-documents/sessions/${sessionId}`, { headers: sessionHeaders() });
    if ((response.status === 401 || response.status === 403) && studentId && sessionId) {
      try {
        const recRes = await fetch(`/events/session/${sessionId}/reconnect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: studentId }),
        });
        if (recRes.ok) {
          const recData = await recRes.json();
          sessionAccessToken = recData.access_token;
          localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
          response = await fetch(`/learning-documents/sessions/${sessionId}`, { headers: sessionHeaders() });
        }
      } catch (err) {
        console.warn('Reconnect error in loadDocument:', err);
      }
    }
    if (!response.ok) throw new Error(await responseError(response, 'Your long-form document could not be restored.'));
    learningDocument = await response.json();
    sessionStatus = learningDocument.status;
    if (!selectedSourceId && learningDocument.source_references?.length) {
      selectedSourceId = learningDocument.source_references.at(-1).source_id;
    }
  }

  async function loadProbes() {
    if (!sessionId || sessionStatus !== 'active') return;
    const response = await fetch(`/learning-documents/sessions/${sessionId}/probes`, { headers: sessionHeaders() });
    if (!response.ok) throw new Error(await responseError(response, 'Your evidence questions could not be restored.'));
    const result = await response.json();
    probes = result.probes || [];
    evidenceSummary = result.evidence_summary || evidenceSummary;
    if (!activeProbeId && probes[0]) activeProbeId = probes[0].probe_id;
  }

  async function loadSessionEvents() {
    if (!sessionId) return;
    try {
      const response = await fetch(`/events/session/${sessionId}`, { headers: sessionHeaders() });
      if (response.ok) {
        const data = await response.json();
        sessionEvents = data.events || [];
        if (data.session?.status === 'submitted') {
          sessionStatus = 'submitted';
          submittedRevision = data.session.submitted_document_revision ?? submittedRevision;
          submittedAt = data.session.submitted_at || submittedAt;
          submissionNotice = submittedAt
            ? `Submitted ${new Date(submittedAt).toLocaleString()}.`
            : 'Submitted for educator review.';
        }
      }
    } catch (err) {
      console.warn('Loading session events for sidebar trace:', err);
    }
  }

  async function loadAssignment() {
    const params = routeParams();
    courseId = params.get('course_id') || '';
    assignmentId = params.get('assignment_id') || '';

    // If navigating to student workspace without a course, redirect to Courses & Enrollment portal
    if (!courseId && !assignmentId) {
      window.location.hash = '#/student/portal';
      return;
    }

    if (assignmentId) {
      const response = await fetch(`/assignments/${assignmentId}`);
      if (!response.ok) throw new Error(await responseError(response, 'The requested assignment could not be loaded.'));
      const found = await response.json();
      if (found.status === 'published') {
        assignment = found;
      } else {
        assignment = null;
      }
    } else if (courseId) {
      const response = await fetch(`/assignments?course_id=${encodeURIComponent(courseId)}&status=published`);
      if (response.ok) {
        const assignments = await response.json();
        const pub = assignments.filter((a) => a.status === 'published');
        assignment = pub[0] || null;
        assignmentId = assignment?.assignment_id || '';
      }
    }

    if (!assignment && !courseId) {
      try {
        const coursesRes = await fetch('/courses');
        if (coursesRes.ok) {
          const coursesList = await coursesRes.json();
          const courses = Array.isArray(coursesList) ? coursesList : coursesList.courses || [];
          for (const c of courses) {
            const cid = c.course_id || c.id;
            if (!cid) continue;
            const res = await fetch(`/assignments?course_id=${encodeURIComponent(cid)}&status=published`);
            if (res.ok) {
              const list = await res.json();
              const pubList = list.filter((a) => a.status === 'published');
              if (pubList.length > 0) {
                assignment = pubList[0];
                assignmentId = assignment.assignment_id;
                courseId = cid;
                break;
              }
            }
          }
        }
      } catch (err) {
        console.warn('Auto-discovering published assignment:', err);
      }
    }

    if (!assignment && !courseId) {
      try {
        const directRes = await fetch('/assignments');
        if (directRes.ok) {
          const allList = await directRes.json();
          const pubList = allList.filter((a) => a.status === 'published');
          if (pubList.length > 0) {
            assignment = pubList[0];
            assignmentId = assignment.assignment_id;
          }
        }
      } catch (err) {
        console.warn('Direct assignment fallback fetch:', err);
      }
    }

    if (!assignment) return;

    studentId = getStudentId();
    loadChatSessionsForStudent(assignmentId, studentId);
    sessionId = '';
    sessionAccessToken = '';
    sessionStatus = '';
    submittedRevision = null;
    submittedAt = '';
    learningDocument = null;
    probes = [];
    sessionEvents = [];

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
        if (['active', 'submitted', 'completed'].includes(session.status) && session.assignment_id === assignmentId) {
          sessionId = persistedSessionId;
          sessionAccessToken = persistedAccessToken;
          sessionStatus = session.status;
          submittedRevision = session.submitted_document_revision ?? null;
          submittedAt = session.submitted_at || '';
        } else {
          localStorage.removeItem(key);
        }
      } else {
        localStorage.removeItem(key);
      }
    }

    if (!sessionId) {
      try {
        const listRes = await fetch(`/events/sessions?student_id=${encodeURIComponent(studentId)}&assignment_id=${encodeURIComponent(assignmentId)}`);
        if (listRes.ok) {
          const sData = await listRes.json();
          const existingList = sData.sessions || [];
          if (existingList.length > 0) {
            const targetSess = existingList[existingList.length - 1];
            const recRes = await fetch(`/events/session/${targetSess.session_id}/reconnect`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ student_id: studentId }),
            });
            if (recRes.ok) {
              const recData = await recRes.json();
              sessionId = recData.session_id;
              sessionAccessToken = recData.access_token;
              sessionStatus = recData.status;
              submittedRevision = targetSess.submitted_document_revision ?? null;
              submittedAt = targetSess.submitted_at || '';
              localStorage.setItem(key, sessionId);
              localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
            }
          }
        }
      } catch (e) {
        console.warn('Could not reconnect to existing student session:', e);
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

    fiosraContext.setCourse(courseId, assignment?.course_title || '');
    fiosraContext.setAssignment(
      assignmentId,
      assignment?.title || assignment?.published?.title || '',
      assignment?.target_kcs || [],
      assignment?.bloom_level || 'evaluate'
    );
    fiosraContext.setSession(sessionId, sessionAccessToken, sessionStatus);

    await loadDocument();
    await loadProbes();
    await loadSessionEvents();
    await loadSessionInterventions();
  }

  async function loadSessionInterventions() {
    if (!sessionId) return;
    try {
      const response = await fetch(`/interventions/session/${sessionId}`);
      if (response.ok) {
        sessionInterventions = await response.json();
      }
    } catch (err) {
      console.warn('Failed to load session interventions:', err);
    }
  }

  async function handleRespondIntervention(interventionId, responseText) {
    try {
      const response = await fetch(`/interventions/${interventionId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_response: responseText }),
      });
      if (response.ok) {
        const updated = await response.json();
        sessionInterventions = sessionInterventions.map((i) =>
          i.intervention_id === updated.intervention_id ? updated : i
        );
        sourceActionNotice = 'Your reflection has been sent to your instructor.';
      }
    } catch (err) {
      console.error('Failed to submit intervention response:', err);
    }
  }

  async function syncDocument(patch) {
    const response = await fetch(`/learning-documents/sessions/${sessionId}`, {
      method: 'PUT',
      headers: sessionHeaders(),
      body: JSON.stringify(patch),
    });
    if (!response.ok) {
      const details = await responseErrorDetails(response, 'This document could not be saved.');
      const saveError = new Error(learnerErrorSummary(details, { draftPreserved: true }));
      saveError.fiosraError = details;
      throw saveError;
    }
    learningDocument = await response.json();
    return learningDocument;
  }

  async function offerConceptProbes(request) {
    if (!sessionId || sessionStatus !== 'active') return;
    try {
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/evaluate`, {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify(request),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Writing help is unavailable right now.'));
      const result = await response.json();
      probes = result.pending || [];
      evidenceSummary = result.evidence_summary || evidenceSummary;
      if (!activeProbeId && probes[0]) activeProbeId = probes[0].probe_id;
      if (result.availability_notice) probeNotice = result.availability_notice;
    } catch (err) {
      console.warn('Offering concept-aware Socratic question:', err);
    }
  }

  function documentExcerpt() {
    return (learningDocument?.blocks || [])
      .map((block) => block.plaintext || '')
      .join('\n')
      .slice(-12000);
  }

  async function requestCompletionSupport(actionId) {
    if (!assignmentId) return;
    isSupportBusy = true;
    probeNotice = '';
    try {
      const response = await fetch(`/assignments/${assignmentId}/support`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_id: actionId, document_excerpt: documentExcerpt() }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'Writing support is unavailable right now.'));
      supportResult = await response.json();
      isTutorPanelOpen = true;
    } catch (err) {
      probeNotice = err.message || 'Writing support is unavailable right now.';
    } finally {
      isSupportBusy = false;
    }
  }

  async function writeWithSource(source) {
    if (!sessionId || !source || sessionStatus !== 'active') return;
    sourceActionBusy = true;
    sourceActionError = null;
    sourceActionNotice = '';
    try {
      const response = await fetch(`/learning-documents/sessions/${sessionId}/source-references`, {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify({ source_id: source.source_id }),
      });
      if (!response.ok) {
        sourceActionError = await responseErrorDetails(response, 'This source could not be added to your writing context.');
        sourceActionNotice = learnerErrorSummary(sourceActionError, { draftPreserved: true });
        return;
      }
      learningDocument = await response.json();
      selectedSourceId = source.source_id;
      sourceActionNotice = `Writing with ${source.title}. This reference does not change your draft.`;
    } catch (err) {
      sourceActionError = { code: 'NETWORK_UNAVAILABLE', retryable: true };
      sourceActionNotice = learnerErrorSummary(sourceActionError, { draftPreserved: true });
    } finally {
      sourceActionBusy = false;
    }
  }

  async function linkSourceToBlock(source, blockId) {
    if (!sessionId || !source || !blockId || sessionStatus !== 'active') return;
    sourceActionBusy = true;
    sourceActionError = null;
    try {
      const response = await fetch(
        `/learning-documents/sessions/${sessionId}/source-references/${encodeURIComponent(source.source_id)}/links`,
        {
          method: 'POST',
          headers: sessionHeaders(),
          body: JSON.stringify({ block_id: blockId }),
        },
      );
      if (!response.ok) {
        sourceActionError = await responseErrorDetails(response, 'This source could not be linked to the claim.');
        sourceActionNotice = learnerErrorSummary(sourceActionError, { draftPreserved: true });
        return;
      }
      learningDocument = await response.json();
      selectedSourceId = source.source_id;
      sourceActionNotice = `${source.title} is linked beside this claim for your review.`;
    } catch (err) {
      sourceActionError = { code: 'NETWORK_UNAVAILABLE', retryable: true };
      sourceActionNotice = learnerErrorSummary(sourceActionError, { draftPreserved: true });
    } finally {
      sourceActionBusy = false;
    }
  }

  async function changeProbe(probeId, action, body = null) {
    isProbeBusy = true;
    probeNotice = '';
    try {
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/${probeId}/${action}`, {
        method: 'POST',
        headers: sessionHeaders(),
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
      if (!response.ok) throw new Error(await responseError(response, 'This question could not be updated.'));
      const result = await response.json();
      probeNotice = result.message;
      probeResponse = '';
      await loadProbes();
      await loadSessionEvents();
      activeProbeId = probes[0]?.probe_id || '';
      if (!probes.length) isTutorPanelOpen = false;
    } catch (err) {
      probeNotice = err.message || 'This question could not be updated.';
    } finally {
      isProbeBusy = false;
    }
  }

  async function submitProbeResponse() {
    const probe = activeProbe();
    if (!probe || probeResponse.trim().length < 10) {
      probeNotice = 'Write at least a short explanation before saving your response.';
      return;
    }
    await changeProbe(probe.probe_id, 'responses', { response_text: probeResponse.trim() });
  }

  function handleFocusedBlockChange({ blockId, semanticType, text, offsetTop }) {
    fiosraContext.setFocusedBlock(blockId, semanticType, text, offsetTop);
    const matchingProbe = probes.find((p) => p.block_id === blockId && p.status !== 'dismissed');
    activeProbeId = matchingProbe ? matchingProbe.probe_id : '';
  }

  async function handleQuoteEvidenceFromSidebar({ quoteText, sourceId, sourceTitle, author, sourceUrl }) {
    if (editorRef && typeof editorRef.insertEvidenceBlock === 'function') {
      editorRef.insertEvidenceBlock({ quoteText, sourceTitle, author, sourceId, sourceUrl });
    }
    const sourceObj = assignmentSources.find(
      (s) => s.source_id === sourceId || s.id === sourceId
    ) || { source_id: sourceId, title: sourceTitle || author, source_url: sourceUrl };
    if (fiosraContext.activeBlockId) {
      await linkSourceToBlock(sourceObj, fiosraContext.activeBlockId);
    } else {
      await writeWithSource(sourceObj);
    }
    sourceActionNotice = `Quoted excerpt from ${sourceTitle || author} inserted into Canvas.`;
  }

  async function submitProbeExplanation(probeId, responseText) {
    if (!probeId || !responseText.trim()) return;
    await changeProbe(probeId, 'responses', { response_text: responseText.trim() });
    fiosraContext.setEpistemicState('STATE_4_EVIDENTIARY_SYNTHESIS');
  }

  async function handleMacroSendMessage(studentInput, hintRequested = false) {
    if (!sessionId || isMacroBusy) return;
    isMacroBusy = true;
    let sessionIdx = chatSessions.findIndex((cs) => cs.id === activeChatSessionId);
    if (sessionIdx < 0 && chatSessions.length > 0) {
      sessionIdx = 0;
    }
    if (sessionIdx >= 0) {
      chatSessions[sessionIdx].turns = [
        ...chatSessions[sessionIdx].turns,
        { role: 'student', text: studentInput }
      ];
      if (chatSessions[sessionIdx].title.startsWith('Consultation') && chatSessions[sessionIdx].turns.length <= 2) {
        const snippet = studentInput.slice(0, 30).trim();
        if (snippet) chatSessions[sessionIdx].title = snippet.length >= 28 ? `${snippet}…` : snippet;
      }
      saveCurrentChatSessions();
    }
    try {
      const prompt = assignment?.published?.task?.prompt || assignment?.task?.prompt || assignment?.prompt || 'Explore structural historical causation';
      const qId = learningDocument?.question_id || assignment?.question_id || 'q1';
      const res = await fetch('/dialogue/message', {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          question_id: qId,
          student_input: studentInput,
          question_prompt: prompt,
          domain: assignment?.domain || 'history',
          hint_requested: hintRequested,
          assignment_id: assignmentId || null,
        }),
      });
      if (!res.ok) throw new Error(await responseError(res, 'Dialogue service unavailable'));
      const data = await res.json();
      const tutorTurn = {
        role: 'tutor',
        text: data.response_text,
        thoughts: data.thoughts_of_tutorbot,
        hint_rung: data.hint_rung,
        is_adversarial: data.is_adversarial,
        action_capsules: data.action_capsules || [],
        radar: data.learner_radar || null,
        prompt_launchers: data.prompt_launchers || [],
      };
      if (sessionIdx >= 0) {
        chatSessions[sessionIdx].turns = [...chatSessions[sessionIdx].turns, tutorTurn];
      }
      fiosraContext.setEpistemicState(null, data.hint_rung);
      await loadSessionEvents();
    } catch (err) {
      console.error('Macro dialogue error:', err);
      if (sessionIdx >= 0) {
        const errorTurn = {
          role: 'tutor',
          text: `⚠️ Socratic Tutor is currently unavailable: ${err.message || 'LLM service connection required'}. Please ensure your LLM provider is configured and running.`,
          is_adversarial: false,
          hint_rung: 0,
          action_capsules: [],
          radar: null,
        };
        chatSessions[sessionIdx].turns = [
          ...chatSessions[sessionIdx].turns,
          errorTurn
        ];
      }
    } finally {
      saveCurrentChatSessions();
      isMacroBusy = false;
    }
  }

  async function handleMacroRequestHint() {
    await handleMacroSendMessage("I would like a Socratic hint to guide my reasoning.", true);
  }

  async function handleChallengeIdea(blockId, text, moveType = 'challenge') {
    if (!sessionId) return;
    try {
      await fetch(`/events/session/${sessionId}`, {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify({
          event_type: 'socratic_move_triggered',
          payload: { block_id: blockId, move_type: moveType, text: text.slice(0, 200), pressure: oraclePressure },
        }),
      });
      await loadSessionEvents();
    } catch (e) {
      console.warn('Logging Socratic move:', e);
    }
  }

  async function submitSession() {
    if (!sessionId || sessionStatus !== 'active' || isSubmitting) return;
    const documentRevision = learningDocument?.document_revision;
    if (typeof documentRevision !== 'number') {
      submissionError = {
        code: 'SUBMISSION_BLOCKED',
        message: 'Your document must finish loading before it can be submitted.',
        retryable: false,
      };
      return;
    }
    if (!pendingSubmissionKey) pendingSubmissionKey = crypto.randomUUID();
    isSubmitting = true;
    submissionError = null;
    submissionNotice = 'Submitting your saved revision…';
    try {
      const res = await fetch(`/events/session/${sessionId}/submit`, {
        method: 'POST',
        headers: {
          ...sessionHeaders(),
          'Idempotency-Key': pendingSubmissionKey,
        },
        body: JSON.stringify({ document_revision: documentRevision }),
      });
      if (!res.ok) {
        submissionError = await responseErrorDetails(res, 'Your milestone could not be submitted.');
        submissionNotice = learnerErrorSummary(submissionError, { draftPreserved: true });
        return;
      }
      const submitted = await res.json();
      sessionStatus = 'submitted';
      submittedRevision = submitted.document_revision;
      submittedAt = submitted.submitted_at;
      submissionNotice = submitted.idempotent_replay
        ? `This revision was already submitted ${new Date(submitted.submitted_at).toLocaleString()}.`
        : `Submitted ${new Date(submitted.submitted_at).toLocaleString()}.`;
      pendingSubmissionKey = '';
      await loadSessionEvents();
    } catch (e) {
      submissionError = {
        code: 'NETWORK_UNAVAILABLE',
        message: 'The submission service is temporarily unavailable.',
        retryable: true,
      };
      submissionNotice = learnerErrorSummary(submissionError, { draftPreserved: true });
    } finally {
      isSubmitting = false;
    }
  }

  async function handleCommitActionCapsule(capsule) {
    if (!capsule) return;
    const textToInsert = capsule.suggested_student_text || capsule.text_payload || '';
    if (editorRef?.insertCapsuleText) {
      editorRef.insertCapsuleText({
        text: textToInsert,
        role: capsule.role || 'qualification',
        sourceTitle: capsule.source_title || 'Assigned Exhibit',
      });
    } else if (editorRef?.insertEvidenceBlock && capsule.role === 'evidence') {
      editorRef.insertEvidenceBlock({
        quoteText: textToInsert,
        sourceTitle: capsule.source_title || 'Assigned Exhibit',
      });
    } else if (editorRef?.insertWritingFrame) {
      editorRef.insertWritingFrame(capsule.role || 'claim');
    }
    try {
      await fetch('/events/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...sessionHeaders(),
        },
        body: JSON.stringify({
          session_id: sessionId,
          student_id: studentId,
          question_id: assignment?.question_id || 'q1',
          event_type: 'action_capsule_committed',
          payload: {
            capsule_id: capsule.capsule_id,
            target_block_id: capsule.target_block_id,
            text: textToInsert,
            provenance: 'action_capsule',
            role: capsule.role || 'claim',
          }
        })
      });
    } catch (err) {
      console.warn('Failed to log action capsule commit event:', err);
    }
  }

  function handleEscalateToAgent(probe) {
    activeGutterTab = 'agent';
    if (isGutterCollapsed) isGutterCollapsed = false;
    if (probe) {
      handleMacroSendMessage(`Regarding paragraph "${probe.claim_text || 'my claim'}": ${probe.question}. How can I best ground this in the evidence?`);
    }
  }

  function enterZenFullscreen() {
    if (isZenFullscreen) return;
    isZenFullscreen = true;
    savedLayoutState = {
      isSourcesCollapsed,
      isSourcesExpanded,
      isGutterCollapsed,
    };
    isSourcesCollapsed = true;
    isSourcesExpanded = false;
    isGutterCollapsed = true;

    if (typeof document !== 'undefined') {
      document.body.classList.add('fiosra-zen-mode');
      const elem = document.documentElement;
      if (elem.requestFullscreen) {
        elem.requestFullscreen().catch(() => {});
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
      }
      window.dispatchEvent(new CustomEvent('fiosra:zen-change', { detail: { active: true } }));
    }
  }

  function exitZenFullscreen() {
    if (!isZenFullscreen) return;
    isZenFullscreen = false;

    if (typeof document !== 'undefined') {
      document.body.classList.remove('fiosra-zen-mode');
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      } else if (document.webkitFullscreenElement) {
        document.webkitExitFullscreen();
      }
      window.dispatchEvent(new CustomEvent('fiosra:zen-change', { detail: { active: false } }));
    }

    if (savedLayoutState) {
      isSourcesCollapsed = savedLayoutState.isSourcesCollapsed;
      isSourcesExpanded = savedLayoutState.isSourcesExpanded;
      isGutterCollapsed = savedLayoutState.isGutterCollapsed;
      savedLayoutState = null;
    }
  }

  function toggleZenFullscreen() {
    if (isZenFullscreen) {
      exitZenFullscreen();
    } else {
      enterZenFullscreen();
    }
  }

  function isTypingTarget(target) {
    if (!target) return false;
    const tagName = target.tagName ? target.tagName.toUpperCase() : '';
    if (tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT') return true;
    if (target.isContentEditable) return true;
    if (typeof target.closest === 'function') {
      if (target.closest('[contenteditable="true"], .prose-mirror, .cm-editor, input, textarea, [role="textbox"]')) {
        return true;
      }
    }
    return false;
  }

  function handleWorkspaceKeyDown(e) {
    if (e.key === 'Escape') {
      if (isTutorPanelOpen) isTutorPanelOpen = false;
      if (isZenFullscreen) {
        exitZenFullscreen();
        e.preventDefault();
        return;
      }
    }

    const isCmdShiftF = (e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'f' || e.key === 'F');
    const isF11 = e.key === 'F11';
    const isStandaloneF = (e.key === 'f' || e.key === 'F') && !e.metaKey && !e.ctrlKey && !e.altKey && !isTypingTarget(e.target);

    if (isCmdShiftF || isF11 || isStandaloneF) {
      e.preventDefault();
      toggleZenFullscreen();
    }
  }

  const handleNativeFullscreenChange = () => {
    const isNative = Boolean(document.fullscreenElement || document.webkitFullscreenElement);
    if (!isNative && isZenFullscreen) {
      exitZenFullscreen();
    }
  };

  function handleToggleZenEvent() {
    toggleZenFullscreen();
  }

  async function handleStudentChanged(e) {
    const newStudentId = e?.detail?.studentId || getStudentId();
    if (newStudentId !== studentId) {
      saveCurrentChatSessions();
      studentId = newStudentId;
      loadChatSessionsForStudent(assignmentId, newStudentId);
      isLoading = true;
      try {
        await loadAssignment();
      } catch (err) {
        error = err.message || 'Could not load student workspace';
      } finally {
        isLoading = false;
      }
    }
  }

  onMount(async () => {
    document.addEventListener('fullscreenchange', handleNativeFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleNativeFullscreenChange);
    window.addEventListener('fiosra:toggle-zen', handleToggleZenEvent);
    window.addEventListener('fiosra:student-changed', handleStudentChanged);
    window.addEventListener('hashchange', handleStudentChanged);
    try {
      await loadAssignment();
    } catch (err) {
      error = err.message || 'The reasoning workspace could not be initialized.';
    } finally {
      isLoading = false;
    }
  });

  onDestroy(() => {
    saveCurrentChatSessions();
    window.removeEventListener('fiosra:toggle-zen', handleToggleZenEvent);
    window.removeEventListener('fiosra:student-changed', handleStudentChanged);
    window.removeEventListener('hashchange', handleStudentChanged);
    if (typeof document !== 'undefined') {
      document.removeEventListener('fullscreenchange', handleNativeFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleNativeFullscreenChange);
      if (isZenFullscreen) {
        document.body.classList.remove('fiosra-zen-mode');
        window.dispatchEvent(new CustomEvent('fiosra:zen-change', { detail: { active: false } }));
      }
    }
  });
</script>

<svelte:window onkeydown={handleWorkspaceKeyDown} />

{#if isLoading}
  <main class="loading-view">
    <div class="spinner"></div>
    <p>Opening your reasoning canvas…</p>
  </main>
{:else if error && !assignment}
  <main class="empty-view">
    <h1>Workspace unavailable</h1>
    <p>{error}</p>
    <div style="display: flex; gap: 12px; margin-top: 14px;">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Return to Courses</a>
    </div>
  </main>
{:else if !assignment}
  <main class="empty-view">
    <h1>{courseId ? 'No published assignment in this course yet' : 'No active assignment selected'}</h1>
    <p>
      {courseId 
        ? 'Your instructor has not published an active reasoning assignment for this course yet.' 
        : 'Open an active milestone from your enrolled courses to start a protected reasoning session.'}
    </p>
    <div style="display: flex; gap: 12px; margin-top: 14px;">
      {#if courseId}
        <a class="btn btn-secondary" href={`#/student/home?course_id=${encodeURIComponent(courseId)}`}>View Course Map</a>
      {/if}
      <a class="btn btn-primary" href="#/student/portal">Browse Available Courses</a>
    </div>
  </main>
{:else}
  <div class="workspace-viewport" class:zen-mode={isZenFullscreen}>
    <!-- Workspace Content Body -->
    <div class="workspace-content-body">
      <!-- Zone 1, 2, 3 Grid -->
      <div class="canvas-tab-wrapper">
        <div
          class="in-situ-workbench-grid"
          class:sources-collapsed={isSourcesCollapsed}
          class:sources-expanded={!isSourcesCollapsed}
          class:gutter-collapsed={isGutterCollapsed}
          class:gutter-open={!isGutterCollapsed}
          class:is-resizing={isResizingLeft || isResizingRight}
          style="--sources-width: {isSourcesCollapsed ? '48px' : `${sourcesWidth}px`}; --gutter-width: {isGutterCollapsed ? '44px' : `${gutterWidth}px`};"
        >
          <!-- Zone 1: Primary Source Exhibits / Evidentiary Well -->
          <div
            class="workbench-col-sources"
            class:collapsed={isSourcesCollapsed}
            class:expanded={!isSourcesCollapsed}
            class:no-transition={isResizingLeft}
            style="width: var(--sources-width);"
          >
            <PrimarySourcesSidebar
              sources={assignmentSources}
              assignment={published || assignment}
              courseTitle={published?.course_title || assignment?.course_title || published?.title || assignment?.title || ''}
              courseId={courseId}
              isCollapsed={isSourcesCollapsed}
              isExpanded={!isSourcesCollapsed}
              onToggleCollapse={handleToggleSourcesCollapse}
              onToggleExpand={handleToggleSourcesExpand}
              onQuoteEvidence={handleQuoteEvidenceFromSidebar}
            />
          </div>

          <!-- Left Margin Slider (Draggable Split-Resizer) -->
          {#if !isSourcesCollapsed}
            <div
              class="workbench-resizer-handle resizer-left"
              class:is-dragging={isResizingLeft}
              onpointerdown={startResizeLeft}
              ondblclick={() => sourcesWidth = 480}
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize left sources sidebar"
              title="Drag to resize sources sidebar (Double-click to reset to 480px)"
            >
              <div class="resizer-knob"></div>
            </div>
          {/if}

          <!-- Zone 2: Structured Reasoning Canvas -->
          <main class="workbench-col-canvas">
            {#if error}<p class="error-banner" role="alert">{error}</p>{/if}
            {#if sourceActionNotice}
              <p class:source-action-error={Boolean(sourceActionError)} class="source-action-notice" role="status">
                {sourceActionNotice}
                {#if sourceActionError?.correlationId}
                  <span>Support ID: {sourceActionError.correlationId}</span>
                {/if}
              </p>
            {/if}
            {#if probeNotice}
              <div class="probe-alert-bar">
                💡 {probeNotice}
              </div>
            {/if}

            {#if learningDocument}
              <LongFormDocumentEditor
                bind:this={editorRef}
                {learningDocument}
                {assignment}
                {sessionId}
                {sessionAccessToken}
                disabled={sessionStatus !== 'active'}
                onSync={syncDocument}
                onSynced={loadSessionEvents}
                onStableDocument={offerConceptProbes}
                proactiveProbes={probes}
                onProbeAction={(probeId, action) => changeProbe(probeId, action)}
                onOpenSources={handleToggleSourcesExpand}
                onHeadingsChange={(h) => documentHeadings = h}
                onBlocksChange={(b) => liveBlocks = b}
                oraclePressure={oraclePressure}
                onChallengeIdea={handleChallengeIdea}
                onDrawerStateChange={(open) => isDrawerOpen = open}
                onPressureChange={(p) => oraclePressure = p}
                onFocusedBlockChange={handleFocusedBlockChange}
                isZenFullscreen={isZenFullscreen}
                onToggleZen={toggleZenFullscreen}
              />
            {/if}
          </main>

          <!-- Right Margin Slider (Draggable Split-Resizer) -->
          {#if !isGutterCollapsed}
            <div
              class="workbench-resizer-handle resizer-right"
              class:is-dragging={isResizingRight}
              onpointerdown={startResizeRight}
              ondblclick={() => gutterWidth = 440}
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize right AI tutor sidebar"
              title="Drag to resize AI tutor sidebar (Double-click to reset to 440px)"
            >
              <div class="resizer-knob"></div>
            </div>
          {/if}

          <!-- Zone 3: Socratic Gutter (Marginalia + Agent + Reasoning + Activity) -->
          <div
            class="workbench-col-gutter"
            class:collapsed={isGutterCollapsed}
            class:no-transition={isResizingRight}
            style="width: var(--gutter-width);"
          >
            <RightWorkbenchGutter
              {probes}
              documentBlocks={canonicalBlocks}
              activeProbeId={activeProbeId}
              focusedBlockId={fiosraContext.activeBlockId}
              focusedBlockOffsetTop={fiosraContext.activeBlockOffsetTop}
              focusedBlockTitle={fiosraContext.activeBlockText ? (fiosraContext.activeBlockText.slice(0, 45) + '…') : ''}
              openExhibitTitle={activeSourceExhibit?.title || ''}
              onRespond={(probeId, text) => submitProbeExplanation(probeId, text)}
              onDismiss={(probeId) => changeProbe(probeId, 'dismiss')}
              onDefer={(probeId) => changeProbe(probeId, 'defer')}
              onSelectBlock={(blockId) => { if (editorRef?.scrollToBlock) editorRef.scrollToBlock(blockId); }}
              onEscalateToAgent={handleEscalateToAgent}
              onCommitCapsule={handleCommitActionCapsule}
              isProbeBusy={isProbeBusy}
              probeNotice={probeNotice}
              sessionId={sessionId}
              assignment={assignment}
              currentRung={fiosraContext.currentHintRung}
              turns={macroTurns}
              chatSessions={chatSessions}
              activeChatSessionId={activeChatSessionId}
              onNewChatSession={handleStartNewChatSession}
              onSwitchChatSession={handleSwitchChatSession}
              onSendMessage={handleMacroSendMessage}
              onRequestHint={handleMacroRequestHint}
              isAgentBusy={isMacroBusy}
              activeTab={activeGutterTab}
              isCollapsed={isGutterCollapsed}
              onToggleCollapse={handleToggleGutterCollapse}
              onSelectTab={handleSelectGutterTab}
              sessionEvents={sessionEvents}
              graphMetrics={graphMetrics}
              sessionStatus={sessionStatus}
              interventions={sessionInterventions}
              onRespondIntervention={handleRespondIntervention}
              submittedAt={submittedAt}
              isSubmitting={isSubmitting}
              onSubmitMilestone={submitSession}
              submissionError={submissionError}
              submissionNotice={submissionNotice}
            />
          </div>
        </div>
      </div>

      <!-- Optional Flyout Support Panel (Toggleable from Top Bar) -->
      <WorkspaceFlyoutPanel
        isOpen={isTutorPanelOpen}
        published={published || assignment}
        {isSupportBusy}
        {supportResult}
        {currentProbe}
        bind:probeResponse
        {isProbeBusy}
        {probeNotice}
        {evidenceSummary}
        onRequestSupport={requestCompletionSupport}
        onClearSupportResult={() => supportResult = null}
        onSubmitProbeResponse={submitProbeResponse}
        onChangeProbe={changeProbe}
        onClose={() => isTutorPanelOpen = false}
      />
    </div>
  </div>
{/if}

<style>
  :global(body.fiosra-zen-mode) {
    overflow: hidden !important;
  }

  .workspace-viewport {
    position: relative;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 56px);
    background: var(--color-obsidian);
    overflow: hidden;
  }

  .workspace-viewport.zen-mode {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh !important;
    max-height: 100vh !important;
    z-index: 9999;
  }

  .workspace-viewport.zen-mode .workspace-content-body {
    height: 100% !important;
    max-height: 100% !important;
    flex: 1 1 100%;
  }

  .workspace-viewport.zen-mode .canvas-tab-wrapper {
    height: 100% !important;
    max-height: 100% !important;
    flex: 1 1 100%;
  }

  .workspace-viewport.zen-mode .in-situ-workbench-grid {
    height: 100% !important;
    max-height: 100% !important;
    flex: 1 1 100%;
  }

  .workspace-content-body {
    flex: 1;
    min-height: 0;
    display: flex;
    position: relative;
    overflow: hidden;
  }

  /* Canvas Tab Wrapper (Always mounted to preserve cursor/undo/state) */
  .canvas-tab-wrapper {
    flex: 1;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .in-situ-workbench-grid {
    display: flex;
    flex-direction: row;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    position: relative;
  }

  .in-situ-workbench-grid.is-resizing {
    user-select: none !important;
    cursor: col-resize !important;
  }

  .in-situ-workbench-grid.is-resizing :global(*) {
    user-select: none !important;
    pointer-events: none !important;
  }

  .in-situ-workbench-grid.is-resizing .workbench-resizer-handle {
    pointer-events: auto !important;
  }

  .workbench-col-sources {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    flex-grow: 0;
    transition: width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .workbench-col-sources.no-transition {
    transition: none !important;
  }

  .workbench-col-sources.collapsed {
    width: 48px;
  }

  .workbench-col-canvas {
    flex: 1 1 0;
    min-width: 320px;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    position: relative;
    background: var(--color-obsidian, #f8f8f5);
  }

  .workbench-col-gutter {
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
    flex-grow: 0;
    position: relative;
    transition: width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .workbench-col-gutter.no-transition {
    transition: none !important;
  }

  .workbench-col-gutter.collapsed {
    width: 44px;
  }

  /* Resizer Handles (Margin Sliders) */
  .workbench-resizer-handle {
    width: 10px;
    margin: 0 -5px;
    height: 100%;
    cursor: col-resize;
    position: relative;
    z-index: 30;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    user-select: none;
    touch-action: none;
  }

  .workbench-resizer-handle::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 4px;
    width: 2px;
    background: var(--color-graphite-border, #e2e4dc);
    transition: all 0.15s ease;
  }

  .workbench-resizer-handle:hover::before,
  .workbench-resizer-handle.is-dragging::before {
    background: #2563eb;
    width: 3px;
    left: 3.5px;
    box-shadow: 0 0 8px rgba(37, 99, 235, 0.4);
  }

  .resizer-knob {
    width: 4px;
    height: 36px;
    border-radius: 4px;
    background: var(--color-slate-muted, #94a3b8);
    opacity: 0;
    transition: opacity 0.15s ease, background 0.15s ease, height 0.15s ease;
    z-index: 2;
  }

  .workbench-resizer-handle:hover .resizer-knob,
  .workbench-resizer-handle.is-dragging .resizer-knob {
    opacity: 1;
    background: #2563eb;
    height: 52px;
  }

  @media (max-width: 1200px) {
    .workbench-col-sources {
      display: none;
    }
    .resizer-left {
      display: none !important;
    }
  }

  @media (max-width: 860px) {
    .workbench-col-gutter {
      display: none;
    }
    .resizer-right {
      display: none !important;
    }
  }

  .error-banner {
    margin: 12px 24px 0;
    padding: 10px 14px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: var(--radius-sm);
    color: #fca5a5;
    font-size: 12px;
  }

  .probe-alert-bar {
    margin: 12px 24px 0;
    padding: 10px 16px;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: var(--radius-sm);
    color: #c4b5fd;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }

  .probe-alert-bar:hover {
    background: rgba(139, 92, 246, 0.25);
  }

  .source-action-notice {
    margin: 12px 24px 0;
    color: var(--color-slate-light);
    font-size: 12px;
  }

  .source-action-notice.source-action-error {
    color: #fbbf24;
  }

  .source-action-notice span {
    display: block;
    margin-top: 2px;
    color: var(--color-slate-muted);
    font-family: var(--font-mono, monospace);
    font-size: 10px;
  }

  .loading-view, .empty-view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 56px);
    background: var(--color-obsidian);
    color: var(--color-slate-light);
    padding: 24px;
    text-align: center;
  }

  .empty-view h1 {
    font-family: var(--font-brand);
    font-size: 20px;
    font-weight: 700;
    color: var(--color-heading);
    margin: 0 0 8px;
  }

  .empty-view p {
    font-size: 13px;
    color: var(--color-slate-muted);
    max-width: 480px;
    margin: 0 0 16px;
    line-height: 1.5;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(217, 119, 6, 0.2);
    border-top-color: var(--color-horizon-blue);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: pointer;
  }

  .btn-primary {
    background: var(--color-horizon-blue);
    color: #fff;
    border: 1px solid var(--color-horizon-blue);
  }

  .btn-primary:hover {
    filter: brightness(1.1);
  }

  .btn-secondary {
    background: var(--color-graphite);
    color: var(--color-slate-light);
    border: 1px solid var(--color-graphite-border);
  }

  .btn-secondary:hover {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
  }
</style>
