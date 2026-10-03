<script>
  import { onMount, onDestroy } from 'svelte';
  import LongFormDocumentEditor from '../lib/LongFormDocumentEditor.svelte';
  import RightWorkbenchGutter from '../lib/RightWorkbenchGutter.svelte';
  import PrimarySourcesSidebar from '../lib/PrimarySourcesSidebar.svelte';
  import WorkspaceFlyoutPanel from '../lib/workspace/WorkspaceFlyoutPanel.svelte';
  import WorkspaceCanvasGrid from '../lib/workspace/WorkspaceCanvasGrid.svelte';
  import WorkspaceEmptyView from '../lib/workspace/WorkspaceEmptyView.svelte';
  import { fiosraContext } from '../lib/contextStore.svelte.js';
  import {
    getStudentId,
    responseError,
    routeParams,
    sessionAccessTokenStorageKey,
  } from '../lib/session.js';
  import { discoverAndInitializeSession } from '../lib/workspace/workspaceSessionLoader';
  import {
    enterZenMode,
    exitZenMode,
    isTypingTarget,
  } from '../lib/workspace/workspaceZenManager';
  import {
    logActionCapsuleCommit,
    logSocraticMove,
    submitMilestoneSession,
  } from '../lib/workspace/workspaceActions';
  import { learnerErrorSummary, responseErrorDetails } from '../lib/api-error.js';
  import {
    buildDefaultChatForStudent,
    createNewChatSession,
    loadStoredChatSessions,
    persistChatSessions,
    sendSocraticMessage,
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

  // Sidebar widths
  let sourcesWidth = $state(
    (typeof localStorage !== 'undefined' && Number(localStorage.getItem('fiosra_sources_width'))) || 480
  );
  let gutterWidth = $state(
    (typeof localStorage !== 'undefined' && Number(localStorage.getItem('fiosra_gutter_width'))) || 440
  );

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
    const newSession = createNewChatSession(chatSessions.length);
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
    const routeCourseId = params.get('course_id') || '';
    const routeAssignmentId = params.get('assignment_id') || '';

    // If navigating to student workspace without a course, redirect to Courses & Enrollment portal
    if (!routeCourseId && !routeAssignmentId) {
      window.location.hash = '#/student/portal';
      return;
    }

    studentId = getStudentId();
    const sessionData = await discoverAndInitializeSession({
      routeCourseId,
      routeAssignmentId,
      studentId,
    });

    if (!sessionData) return;

    courseId = sessionData.courseId;
    assignmentId = sessionData.assignmentId;
    assignment = sessionData.assignment;
    sessionId = sessionData.sessionId;
    sessionAccessToken = sessionData.sessionAccessToken;
    sessionStatus = sessionData.sessionStatus;
    submittedRevision = sessionData.submittedRevision;
    submittedAt = sessionData.submittedAt;

    loadChatSessionsForStudent(assignmentId, studentId);
    learningDocument = null;
    probes = [];
    sessionEvents = [];

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
      const result = await sendSocraticMessage({
        sessionId,
        studentId,
        assignmentId,
        assignment,
        learningDocument,
        studentInput,
        hintRequested,
        sessionHeaders,
      });
      if (sessionIdx >= 0) {
        chatSessions[sessionIdx].turns = [...chatSessions[sessionIdx].turns, result.tutorTurn];
      }
      if (result.success && typeof result.hintRung === 'number') {
        fiosraContext.setEpistemicState(null, result.hintRung);
        await loadSessionEvents();
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
    await logSocraticMove({
      sessionId,
      blockId,
      text,
      moveType,
      pressure: oraclePressure,
      sessionHeaders,
    });
    await loadSessionEvents();
  }

  async function submitSession() {
    if (!sessionId || sessionStatus !== 'active' || isSubmitting) return;
    isSubmitting = true;
    submissionError = null;
    submissionNotice = 'Submitting your saved revision…';
    const res = await submitMilestoneSession({
      sessionId,
      learningDocument,
      pendingSubmissionKey,
      sessionHeaders,
    });
    isSubmitting = false;
    submissionNotice = res.submissionNotice;
    submissionError = res.submissionError;
    pendingSubmissionKey = res.pendingSubmissionKey;
    if (res.success) {
      sessionStatus = res.sessionStatus || 'submitted';
      submittedRevision = res.submittedRevision ?? null;
      submittedAt = res.submittedAt || '';
      await loadSessionEvents();
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
    await logActionCapsuleCommit({
      sessionId,
      studentId,
      questionId: assignment?.question_id || 'q1',
      capsule,
      textToInsert,
      sessionHeaders,
    });
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
    const res = enterZenMode({
      isSourcesCollapsed,
      isSourcesExpanded,
      isGutterCollapsed,
    });
    savedLayoutState = res.savedLayout;
    isSourcesCollapsed = true;
    isSourcesExpanded = false;
    isGutterCollapsed = true;
  }

  function exitZenFullscreen() {
    if (!isZenFullscreen) return;
    isZenFullscreen = false;
    exitZenMode();
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

{#if isLoading || !assignment || error}
  <WorkspaceEmptyView {isLoading} {error} {assignment} {courseId} />
{:else}
  <div class="workspace-viewport" class:zen-mode={isZenFullscreen}>
    <!-- Workspace Content Body -->
    <div class="workspace-content-body">
      <!-- Zone 1, 2, 3 Grid -->
      <div class="canvas-tab-wrapper">
        <WorkspaceCanvasGrid
          bind:sourcesWidth
          bind:gutterWidth
          {isSourcesCollapsed}
          {isGutterCollapsed}
        >
          {#snippet sources()}
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
          {/snippet}

          {#snippet canvas()}
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
          {/snippet}

          {#snippet gutter()}
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
          {/snippet}
        </WorkspaceCanvasGrid>
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
</style>
