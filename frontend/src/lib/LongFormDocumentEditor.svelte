<script>
  import { onDestroy, onMount, untrack } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import { learnerErrorSummary } from './api-error.js';
  import {
    clearDocumentRecovery,
    loadDocumentRecovery,
    saveDocumentRecovery,
  } from './document-recovery.js';
  import {
    EPISTEMIC_CONFIG,
    localSentenceClassify,
    splitIntoSentences,
  } from './editor/epistemicClassifier';
  export { EPISTEMIC_CONFIG };
  import {
    BlockIdentity,
    createEpistemicInlineHighlighter,
    blockTypes,
    supportedTopLevelTypes,
    normalizedNode,
    partitionStateBlocks,
    documentContentFromBlocks,
    createBlockId,
    clone,
  } from './editor/tiptapBlockExtensions';
  import DocumentEditorHeader from './editor/DocumentEditorHeader.svelte';
  import DocumentOutlineSidebar from './editor/DocumentOutlineSidebar.svelte';

  let {
    learningDocument = null,
    assignment = null,
    disabled = false,
    sessionId = '',
    sessionAccessToken = '',
    onSync = async () => null,
    onSynced = () => null,
    onStableDocument = async () => null,
    proactiveProbes = [],
    onProbeAction = async () => null,
    onOpenSources = () => null,
    onHeadingsChange = () => null,
    onBlocksChange = () => null,
    oraclePressure = 'socratic',
    onProbeResponse = async () => null,
    onChallengeIdea = async () => null,
    onDrawerStateChange = () => null,
    onPressureChange = () => null,
    onFocusedBlockChange = () => null,
    isZenFullscreen = false,
    onToggleZen = () => null,
    sessionStatus = 'active',
    submittedAt = '',
    isSubmitting = false,
    onSubmitMilestone = async () => null,
  } = $props();

  let isCanvasUnlocked = $state(false);
  let hasUserToggledLock = $state(false);

  let isLocked = $derived(
    hasUserToggledLock ? !isCanvasUnlocked : disabled
  );

  function toggleCanvasLock() {
    hasUserToggledLock = true;
    isCanvasUnlocked = isLocked;
  }

  // State
  let editorElement;
  let editor = null;
  let editorState = $state({ editor: null });
  let baseRevision = $state(0);
  let baseline = {};
  let isSaving = $state(false);
  let isDirty = $state(false);
  let saveError = $state('');
  let saveErrorDetails = $state(null);
  let recoverySnapshot = $state(null);
  let lastConfirmedSaveAt = $state('');
  let wordCount = $state(0);
  let readingTimeMin = $derived(Math.max(1, Math.ceil(wordCount / 200)));
  let saveTimer;
  let classifyTimer;
  let probeTimer;
  let loadedDocumentId = '';

  let documentHeadings = $state([]);
  let isEpistemicLens = $state(true); // Default ON for subtle continuous truth guidance
  let canvasWidthMode = $state(
    (typeof localStorage !== 'undefined' && localStorage.getItem('fiosra_canvas_width_mode')) || 'wide'
  );

  function setCanvasWidthMode(mode) {
    canvasWidthMode = mode;
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('fiosra_canvas_width_mode', mode);
      } catch {
        // Ignore localStorage quota/security errors
      }
    }
  }
  // Learner-controlled assistant drawer state.
  let activeSentence = $state(null);
  let chatMessages = $state([]);
  let chatInputText = $state('');
  let showSlashTools = $state(false);
  let selectedSlashToolIndex = $state(-1);
  let activeSlashTool = $state('');
  let isOracleThinking = $state(false);
  let isOracleSatisfied = $state(false);
  let oracleSatisfactionReason = $state('');
  let suggestedRevision = $state(null);
  let epistemicProgress = $state(0.4);
  let activeMoveType = $state('challenge');
  let chatMessagesContainer = $state(null);
  export function toggleSocraticDrawer() {
    if (activeSentence) {
      closeSentenceChat();
    } else if (proactiveProbes.length) {
      openProactiveProbe(proactiveProbes[0]);
    } else {
      openGeneralInquiry();
    }
  }

  export function insertEvidenceBlock({ quoteText, sourceTitle = '', author = '', sourceId = '', sourceUrl = '' }) {
    if (!editor) return;
    const cleanQuote = (quoteText || '').trim().replace(/^["“']+|["”']+$/g, '');
    const citation = author && sourceTitle && author !== sourceTitle
      ? `${author}, ${sourceTitle}`
      : (sourceTitle || author || 'Primary Source');

    editor.chain().focus().insertContent([
      {
        type: 'blockquote',
        attrs: { semanticType: 'evidence', authorType: 'student', sourceId, sourceUrl },
        content: [
          {
            type: 'paragraph',
            content: [{ type: 'text', text: `“${cleanQuote}”` }]
          },
          {
            type: 'paragraph',
            content: [{ type: 'text', marks: [{ type: 'italic' }], text: `— ${citation}` }]
          }
        ]
      },
      {
        type: 'paragraph',
        attrs: { semanticType: 'reasoning', authorType: 'student' },
        content: []
      }
    ]).run();
    scheduleSync();
  }

  export function insertCapsuleText({ text = '', role = 'qualification', sourceTitle = '' } = {}) {
    if (!editor) return;
    const cleanText = (text || '').trim();
    if (!cleanText) return;

    if (role === 'evidence') {
      insertEvidenceBlock({ quoteText: cleanText, sourceTitle: sourceTitle || 'Primary Source' });
      return;
    }

    editor.chain().focus().insertContent([
      {
        type: 'paragraph',
        attrs: { semanticType: role || 'qualification', authorType: 'assisted' },
        content: [{ type: 'text', text: cleanText }],
      },
      {
        type: 'paragraph',
        attrs: { semanticType: 'reasoning', authorType: 'student' },
        content: [],
      },
    ]).run();
    scheduleSync();
  }

  export function insertWritingFrame(frameType = 'claim') {
    if (!editor) return;
    const frameScaffolds = {
      claim: {
        placeholder: '[State your bounded historical claim or provisional thesis here...]',
        semanticType: 'claim',
      },
      evidence: {
        placeholder: '[Cite primary accounting data or exhibit excerpt supporting this assertion...]',
        semanticType: 'evidence',
      },
      warrant: {
        placeholder: '[Articulate the causal mechanism connecting the evidence to the claim...]',
        semanticType: 'reasoning',
      },
      qualification: {
        placeholder: '[State the necessary qualification, exception, or counter-condition to this claim...]',
        semanticType: 'qualification',
      },
      counterargument: {
        placeholder: '[Examine an opposing historical interpretation or counter-hypothesis...]',
        semanticType: 'counterargument',
      },
    };
    const scaffold = frameScaffolds[frameType] || frameScaffolds.claim;
    editor.chain().focus().insertContent([
      {
        type: 'paragraph',
        attrs: { semanticType: scaffold.semanticType, authorType: 'student' },
        content: [{ type: 'text', text: scaffold.placeholder }],
      },
    ]).run();
    scheduleSync();
  }

  export function insertSourceQuote(source) {
    if (!source) return;
    insertEvidenceBlock({
      quoteText: source.excerpt || source.quote || source.text || '',
      sourceTitle: source.title || source.source_title || 'Assigned Exhibit',
      author: source.author || '',
      sourceId: source.id || source.source_id || '',
      sourceUrl: source.url || '',
    });
  }

  function openGeneralInquiry() {
    const promptText = assignment?.published?.task?.prompt || assignment?.task?.prompt || 'This assignment';
    activeSentence = {
      text: promptText,
      epistemic_type: 'reasoning',
      surrounding_context: assignment?.purpose || '',
      is_general_inquiry: true,
    };
    isOracleSatisfied = false;
    oracleSatisfactionReason = '';
    suggestedRevision = null;
    epistemicProgress = 0.0;
    activeMoveType = 'socratic';
    chatInputText = '';
    // Student initiates the conversation cleanly (no unprompted Oracle greeting)
    chatMessages = [];
    if (onDrawerStateChange) onDrawerStateChange(true);
    triggerDecorationsUpdate();
  }

  function updateChatInput(event) {
    chatInputText = event.currentTarget.value;
    showSlashTools = !activeSlashTool && chatInputText.startsWith('/');
    if (!showSlashTools) selectedSlashToolIndex = -1;
  }

  function selectSlashTool(tool) {
    activeSlashTool = tool;
    chatInputText = '';
    showSlashTools = false;
    selectedSlashToolIndex = -1;
  }

  function clearSlashTool() {
    activeSlashTool = '';
    showSlashTools = false;
    selectedSlashToolIndex = -1;
  }

  // Sentence-level epistemic registry: key = sentence text or fingerprint -> classification
  let sentenceMap = $state({});

  const EpistemicInlineHighlighter = createEpistemicInlineHighlighter({
    getActiveSentence: () => activeSentence,
    getSentenceMap: () => sentenceMap,
    onFocusedBlockChange,
  });

  // Derived metrics across all identified sentences
  let epistemicMetrics = $derived.by(() => {
    let c = 0, e = 0, r = 0, a = 0, p = 0;
    for (const item of Object.values(sentenceMap)) {
      if (item.epistemic_type === 'claim') c++;
      else if (item.epistemic_type === 'evidence') e++;
      else if (item.epistemic_type === 'reasoning') r++;
      else if (item.epistemic_type === 'assumption') a++;
      else if (item.epistemic_type === 'premature_closure') p++;
    }
    return { claim: c, evidence: e, reasoning: r, assumption: a, premature: p };
  });

  // Multi-Page Canvas & Outline Navigation State
  let currentPageIndex = $state(1);
  let pagesMap = $state({ 1: [] });
  let totalPages = $derived(Math.max(1, Object.keys(pagesMap).length));
  let isOutlineOpen = $state(false);

  // Canvas Width: Permanently Max (100% End-to-End A4)

  function saveCurrentPageEdits() {
    if (!editor) return;
    pagesMap[currentPageIndex] = currentEditorBlocks(currentPageIndex);
  }

  function goToPage(targetPage) {
    if (targetPage === currentPageIndex || targetPage < 1 || targetPage > totalPages) return;
    saveCurrentPageEdits();
    currentPageIndex = targetPage;
    const targetBlocks = pagesMap[targetPage] || [];
    editor.commands.setContent(documentContentFromBlocks(targetBlocks), { emitUpdate: false });
    editor.chain().focus('start').run();
    updateEditorMetrics();
    triggerDecorationsUpdate();
  }

  function prevPage() {
    if (currentPageIndex > 1) goToPage(currentPageIndex - 1);
  }

  function nextPage() {
    if (currentPageIndex < totalPages) goToPage(currentPageIndex + 1);
  }

  function addNewBlankPage() {
    if (isLocked) return;
    saveCurrentPageEdits();
    const nextP = totalPages + 1;
    const newHeadingId = crypto.randomUUID();
    const newParaId = crypto.randomUUID();
    pagesMap[nextP] = [
      {
        block_id: newHeadingId,
        block_type: 'heading',
        content: {
          type: 'heading',
          attrs: { level: 2, blockId: newHeadingId, authorType: 'student', sectionId: `page_${nextP}`, pageNumber: nextP },
          content: [{ type: 'text', text: `Section ${nextP}` }]
        },
        plaintext: `Section ${nextP}`,
        position: 1,
        section_id: `page_${nextP}`,
        author_type: 'student'
      },
      {
        block_id: newParaId,
        block_type: 'paragraph',
        content: {
          type: 'paragraph',
          attrs: { blockId: newParaId, authorType: 'student', sectionId: `page_${nextP}`, pageNumber: nextP },
          content: []
        },
        plaintext: '',
        position: 2,
        section_id: `page_${nextP}`,
        author_type: 'student'
      }
    ];
    goToPage(nextP);
    scheduleSync();
  }

  function deletePage(pageToDelete) {
    if (isLocked || totalPages <= 1) return;
    saveCurrentPageEdits();
    const newMap = {};
    let newIdx = 1;
    const sortedKeys = Object.keys(pagesMap).map(Number).sort((a, b) => a - b);
    for (const p of sortedKeys) {
      if (p === pageToDelete) continue;
      newMap[newIdx] = (pagesMap[p] || []).map((b) => ({
        ...b,
        section_id: `page_${newIdx}`,
        content: {
          ...b.content,
          attrs: { ...(b.content?.attrs || {}), sectionId: `page_${newIdx}`, pageNumber: newIdx }
        }
      }));
      newIdx++;
    }
    pagesMap = newMap;
    const targetPage = Math.min(currentPageIndex, Object.keys(pagesMap).length);
    currentPageIndex = targetPage;
    editor.commands.setContent(documentContentFromBlocks(pagesMap[targetPage] || []), { emitUpdate: false });
    updateEditorMetrics();
    scheduleSync();
  }

  function jumpToOutlineHeading(item) {
    if (item.page !== currentPageIndex) {
      goToPage(item.page);
    }
    setTimeout(() => {
      scrollToBlock(item.blockId);
    }, 100);
  }

  // --- Backend LLM Epistemic Refinement ---
  async function requestLLMEpistemicClassification(paragraphText) {
    if (!sessionId || !paragraphText || paragraphText.trim().length < 20) return;
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(sessionAccessToken ? { 'X-Fiosra-Session-Token': sessionAccessToken } : {}),
      };
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/epistemic-classify`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          text: paragraphText.trim(),
          oracle_pressure: oraclePressure,
        }),
      });
      if (!response.ok) return;
      const data = await response.json();
      if (data?.sentences?.length) {
        for (const item of data.sentences) {
          if (item.sentence && item.epistemic_type) {
            sentenceMap[item.sentence.trim()] = {
              epistemic_type: item.epistemic_type,
              confidence: item.confidence || 0.9,
              oracle_probe: item.oracle_probe,
              source_grounded: Boolean(item.source_grounded),
            };
          }
        }
        triggerDecorationsUpdate();
        broadcastBlocks();
      }
    } catch (err) {
      console.warn('LLM epistemic classification background notice:', err);
    }
  }

  // --- On-Demand Socratic Dialectic Agent Inquiry ---
  async function requestSentenceInquiry(sentenceText, moveType = 'challenge', epistemicType = 'claim') {
    if (!sessionId || !sentenceText) return;
    isOracleThinking = true;
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(sessionAccessToken ? { 'X-Fiosra-Session-Token': sessionAccessToken } : {}),
      };
      const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/sentence-inquire`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          sentence: sentenceText.trim(),
          epistemic_type: epistemicType,
          move_type: moveType,
          oracle_pressure: oraclePressure,
        }),
      });
      if (!response.ok) return;
      const data = await response.json();
      if (activeSentence && activeSentence.text === sentenceText) {
        activeSentence.oracle_probe = data.oracle_probe;
        activeSentence.epistemic_type = data.epistemic_type || epistemicType;
        activeSentence.targeted_vulnerability = data.targeted_vulnerability;
        activeSentence.socratic_moves = data.socratic_moves || [];
        activeMoveType = moveType;
      }
      if (sentenceMap[sentenceText]) {
        sentenceMap[sentenceText].oracle_probe = data.oracle_probe;
        sentenceMap[sentenceText].targeted_vulnerability = data.targeted_vulnerability;
        sentenceMap[sentenceText].socratic_moves = data.socratic_moves;
      }
    } catch (err) {
      console.warn('Sentence inquiry notice:', err);
    } finally {
      isOracleThinking = false;
    }
  }

  function scheduleLLMClassification() {
    clearTimeout(classifyTimer);
    classifyTimer = setTimeout(() => {
      // Drafting remains local and uninterrupted. The deterministic labels can
      // suggest an inquiry opportunity, but no model call or visible probe is
      // created until a learner opens the Enquirer and asks for assistance.
      triggerDecorationsUpdate();
    }, 1200);
  }

  function scheduleConceptProbeOffer(synced) {
    clearTimeout(probeTimer);
    const changedBlockIds = synced?.changed_block_ids || [];
    if (!synced?.document_revision || changedBlockIds.length === 0) return;
    // This quiet period means a question is offered after the learner pauses, not while they type.
    probeTimer = setTimeout(() => {
      onStableDocument({
        document_revision: synced.document_revision,
        changed_block_ids: changedBlockIds,
      });
    }, 5500);
  }

  function triggerDecorationsUpdate() {
    if (!editor?.view) return;
    editor.view.dispatch(editor.state.tr.setMeta('fiosra_inline_decorations_refresh', Date.now()));
  }

  function openSentenceChat(item, domElement) {
    if (activeSentence && activeSentence.text === item.text) return;

    activeSentence = { ...item };
    isOracleSatisfied = false;
    oracleSatisfactionReason = '';
    suggestedRevision = null;
    epistemicProgress = 0.0;
    const initialCategory = item.targeted_vulnerability ? 'assumptions' : 'challenge';
    activeMoveType = initialCategory;
    chatInputText = '';
    // Student initiates the conversation cleanly
    chatMessages = [];

    if (onDrawerStateChange) onDrawerStateChange(true);
    triggerDecorationsUpdate();

    // Smoothly scroll the sentence into view if needed
    if (domElement) {
      setTimeout(() => {
        domElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    }
  }

  function closeSentenceChat() {
    activeSentence = null;
    chatMessages = [];
    chatInputText = '';
    isOracleSatisfied = false;
    suggestedRevision = null;
    if (onDrawerStateChange) onDrawerStateChange(false);
    triggerDecorationsUpdate();
  }

  function openProactiveProbe(probe) {
    if (!probe?.question) return;
    activeSentence = {
      text: probe.claim_text || 'Your saved claim',
      epistemic_type: 'claim',
      surrounding_context: '',
      proactive_probe_id: probe.probe_id,
      concept_label: probe.concept_label,
    };
    chatMessages = [{ role: 'oracle', content: probe.question, category: probe.focus_type }];
    isOracleSatisfied = false;
    suggestedRevision = null;
    epistemicProgress = 0.0;
    activeMoveType = probe.focus_type || 'challenge';
    if (onDrawerStateChange) onDrawerStateChange(true);
  }

  async function deferActiveProbe() {
    if (!activeSentence?.proactive_probe_id) return;
    await onProbeAction(activeSentence.proactive_probe_id, 'defer');
    closeSentenceChat();
  }

  export function openConceptProbe(probeId) {
    const probe = proactiveProbes.find((item) => item.probe_id === probeId);
    if (probe) openProactiveProbe(probe);
  }


  function syncBaseline(state) {
    baseline = Object.fromEntries(
      (state?.blocks || []).map((block) => [
        block.block_id,
        JSON.stringify({
          block_id: block.block_id,
          block_type: block.block_type,
          content: block.content,
          position: block.position,
          section_id: block.section_id || null,
          author_type: block.author_type || 'student',
        }),
      ]),
    );
    baseRevision = state?.document_revision || 0;
    wordCount = (state?.blocks || [])
      .map((block) => block.plaintext || '')
      .join(' ')
      .trim()
      .split(/\s+/)
      .filter(Boolean).length;
    extractHeadings();
    broadcastBlocks();
  }

  function extractHeadings() {
    const headings = [];
    const pageNumbers = Object.keys(pagesMap).map(Number).sort((a, b) => a - b);
    for (const p of pageNumbers) {
      const pBlocks = (p === currentPageIndex && editor) ? currentEditorBlocks(p) : (pagesMap[p] || []);
      for (const b of pBlocks) {
        if (b.block_type === 'heading' || b.content?.type === 'heading') {
          headings.push({
            page: p,
            level: b.content?.attrs?.level || 2,
            text: b.plaintext || b.content?.content?.[0]?.text || 'Untitled section',
            blockId: b.block_id,
          });
        }
      }
    }
    documentHeadings = headings;
    onHeadingsChange(headings);
  }

  function broadcastBlocks() {
    if (!editor) return;
    const blocks = currentBlocks();
    onBlocksChange(blocks);
  }

  export function scrollToHeading(pos) {
    if (!editor) return;
    editor.chain().focus().setTextSelection(pos).scrollIntoView().run();
  }

  export function scrollToBlock(blockId) {
    let targetPage = null;
    const pageNumbers = Object.keys(pagesMap).map(Number).sort((a, b) => a - b);
    for (const p of pageNumbers) {
      const pBlocks = (p === currentPageIndex && editor) ? currentEditorBlocks(p) : (pagesMap[p] || []);
      if (pBlocks.some((b) => b.block_id === blockId)) {
        targetPage = p;
        break;
      }
    }

    if (targetPage && targetPage !== currentPageIndex) {
      goToPage(targetPage);
    }

    setTimeout(() => {
      if (!editorElement) return;
      const el = editorElement.querySelector(`[data-block-id="${blockId}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('sentence-pulse-highlight');
        setTimeout(() => el.classList.remove('sentence-pulse-highlight'), 1800);
      }
    }, 100);
  }

  export function expandBlockProbe(blockId) {
    if (!editorElement) return;
    const blockEl = editorElement.querySelector(`[data-block-id="${blockId}"]`);
    if (blockEl) {
      blockEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      blockEl.classList.add('sentence-pulse-highlight');
      setTimeout(() => blockEl.classList.remove('sentence-pulse-highlight'), 1800);
      if (onFocusedBlockChange) {
        onFocusedBlockChange({
          blockId,
          offsetTop: blockEl.offsetTop,
        });
      }
    }
  }

  async function loadRecoverySnapshot(state) {
    if (!state?.document_id || !sessionId) return;
    try {
      const snapshot = await loadDocumentRecovery(sessionId, state.document_id);
      if (snapshot?.blocks?.length) {
        recoverySnapshot = snapshot;
      }
    } catch (error) {
      console.warn('Local document recovery could not be loaded:', error);
    }
  }

  async function preserveLocalRecovery(blocks) {
    if (!learningDocument?.document_id || !sessionId) return;
    try {
      recoverySnapshot = await saveDocumentRecovery({
        sessionId,
        documentId: learningDocument.document_id,
        baseRevision,
        blocks,
      });
    } catch (error) {
      console.warn('Local document recovery could not be stored:', error);
    }
  }

  async function removeLocalRecovery() {
    if (!learningDocument?.document_id || !sessionId) return;
    try {
      await clearDocumentRecovery(sessionId, learningDocument.document_id);
      recoverySnapshot = null;
    } catch (error) {
      console.warn('Local document recovery could not be cleared:', error);
    }
  }

  function restoreLocalRecovery() {
    if (!recoverySnapshot?.blocks?.length || !editor) return;
    pagesMap = partitionStateBlocks(recoverySnapshot.blocks);
    currentPageIndex = 1;
    editor.commands.setContent(documentContentFromBlocks(pagesMap[1] || []), { emitUpdate: false });
    updateEditorMetrics();
    isDirty = true;
    saveErrorDetails = {
      code: 'NETWORK_UNAVAILABLE',
      retryable: true,
      correlationId: null,
    };
    saveError = 'Stored on this device — retry needed before your local changes are saved online.';
  }

  async function discardLocalRecovery() {
    await removeLocalRecovery();
    saveError = '';
    saveErrorDetails = null;
  }

  function initialiseEditor(state) {
    if (!editor || !state) return;
    loadedDocumentId = state.document_id;
    pagesMap = partitionStateBlocks(state.blocks);
    currentPageIndex = 1;
    const page1Blocks = pagesMap[1] || [];
    editor.commands.setContent(documentContentFromBlocks(page1Blocks), { emitUpdate: false });
    syncBaseline(state);
    isDirty = false;
    saveError = '';
    saveErrorDetails = null;
    lastConfirmedSaveAt = new Date().toISOString();
    void loadRecoverySnapshot(state);
    scheduleLLMClassification();
  }

  function currentEditorBlocks(pageIdx) {
    if (!editor) return [];
    const p = pageIdx || currentPageIndex;
    const rawNodes = editor.getJSON().content || [];
    return rawNodes
      .map(normalizedNode)
      .map((node, index) => {
        let text = '';
        try {
          const pmNode = editor.state.doc.maybeChild(index);
          text = pmNode ? pmNode.textContent : '';
        } catch {
          text = '';
        }
        return {
          block_id: node.attrs.blockId,
          block_type: blockTypes[node.type] || 'paragraph',
          content: {
            type: node.type,
            attrs: {
              ...node.attrs,
              sectionId: `page_${p}`,
              pageNumber: p,
            },
            ...(node.content?.length ? { content: node.content } : {}),
          },
          plaintext: text,
          position: index + 1,
          section_id: `page_${p}`,
          author_type: node.attrs.authorType || 'student',
        };
      });
  }

  export function currentBlocks() {
    if (!editor) return [];
    pagesMap[currentPageIndex] = currentEditorBlocks(currentPageIndex);

    const allBlocks = [];
    let globalPos = 1;
    const pageNumbers = Object.keys(pagesMap).map(Number).sort((a, b) => a - b);
    for (const p of pageNumbers) {
      const pBlocks = pagesMap[p] || [];
      for (const b of pBlocks) {
        allBlocks.push({
          ...b,
          position: globalPos++,
          section_id: `page_${p}`,
          content: {
            ...b.content,
            attrs: {
              ...(b.content?.attrs || {}),
              sectionId: `page_${p}`,
              pageNumber: p,
            },
          },
        });
      }
    }
    return allBlocks;
  }

  function blockSignature(block) {
    return JSON.stringify({
      block_id: block.block_id,
      block_type: block.block_type,
      content: {
        ...block.content,
        attrs: {
          ...(block.content?.attrs || {}),
          blockId: block.block_id,
          sectionId: block.section_id || null,
        },
      },
      position: block.position,
      section_id: block.section_id || null,
      author_type: block.author_type || 'student',
    });
  }

  function updateEditorMetrics() {
    saveCurrentPageEdits();
    pruneStaleSentenceClassifications();
    let totalWords = 0;
    const pageNumbers = Object.keys(pagesMap).map(Number);
    for (const p of pageNumbers) {
      const pBlocks = (p === currentPageIndex && editor) ? currentEditorBlocks(p) : (pagesMap[p] || []);
      for (const b of pBlocks) {
        if (b.plaintext) {
          totalWords += b.plaintext.trim().split(/\s+/).filter(Boolean).length;
        }
      }
    }
    wordCount = totalWords;
    extractHeadings();
    broadcastBlocks();
  }

  function pruneStaleSentenceClassifications() {
    const liveSentences = new Set();
    const sentencePattern = /[^.!?]+(?:[.!?]+["'”’]?|\s*$)/g;

    for (const blocks of Object.values(pagesMap)) {
      for (const block of blocks || []) {
        const content = (block.plaintext || '').trim();
        if (!content) continue;
        for (const match of content.matchAll(sentencePattern)) {
          const sentence = match[0].trim();
          if (sentence.length >= 10) liveSentences.add(sentence);
        }
      }
    }

    for (const sentence of Object.keys(sentenceMap)) {
      if (!liveSentences.has(sentence)) delete sentenceMap[sentence];
    }
  }

  function scheduleSync() {
    if (isLocked || !editor) return;
    isDirty = true;
    saveError = '';
    updateEditorMetrics();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => syncNow(), 900);
    scheduleLLMClassification();
  }

  export async function syncNow() {
    clearTimeout(saveTimer);
    if (!editor || isLocked || isSaving || !isDirty) return;
    const blocks = currentBlocks();
    const next = Object.fromEntries(blocks.map((block) => [block.block_id, blockSignature(block)]));
    const changedBlocks = blocks.filter((block) => baseline[block.block_id] !== next[block.block_id]);
    const deletedBlockIds = Object.keys(baseline).filter((blockId) => !next[blockId]);
    if (!changedBlocks.length && !deletedBlockIds.length) {
      isDirty = false;
      return;
    }
    // Clean upserts to strictly conform to DocumentBlockInput (no extra fields like plaintext)
    const upserts = changedBlocks.map((b) => ({
      block_id: b.block_id,
      block_type: b.block_type,
      content: {
        ...b.content,
        attrs: {
          ...(b.content?.attrs || {}),
          blockId: b.block_id,
          sectionId: b.section_id || null,
        },
      },
      position: b.position,
      section_id: b.section_id || null,
      author_type: b.author_type || 'student',
    }));
    isSaving = true;
    saveError = '';
    saveErrorDetails = null;
    await preserveLocalRecovery(blocks);
    try {
      const synced = await onSync({
        base_revision: baseRevision,
        upserts,
        deleted_block_ids: deletedBlockIds,
      });
      if (!synced) return;
      syncBaseline(synced);
      isDirty = false;
      lastConfirmedSaveAt = new Date().toISOString();
      await removeLocalRecovery();
      onSynced(synced);
      scheduleConceptProbeOffer(synced);
    } catch (error) {
      saveErrorDetails = error?.fiosraError || {
        code: 'NETWORK_UNAVAILABLE',
        retryable: true,
        correlationId: null,
      };
      saveError = error?.message || learnerErrorSummary(saveErrorDetails, { draftPreserved: true });
    } finally {
      isSaving = false;
    }
  }

  function setBlock(type, attrs = {}) {
    editor?.chain().focus().setNode(type, attrs).run();
  }

  function toggleMark(mark) {
    if (!editor || isLocked) return;
    if (mark === 'bold') editor.chain().focus().toggleBold().run();
    if (mark === 'italic') editor.chain().focus().toggleItalic().run();
  }

  // Assistant drawer replaced by Zone 3 Socratic Marginalia Gutter & Top Bar Copilot

  onMount(() => {
    editor = new Editor({
      element: editorElement,
      editable: !isLocked,
      extensions: [
        StarterKit.configure({
          heading: { levels: [1, 2, 3] },
          codeBlock: false,
          horizontalRule: false,
          link: false,
        }),
        BlockIdentity,
        EpistemicInlineHighlighter,
      ],
      content: { type: 'doc', content: [{ type: 'paragraph' }] },
      editorProps: {
        attributes: {
          class: 'notion-minimal-prosemirror',
          'aria-label': 'Notion-style long-form reasoning canvas',
        },
      },
      onUpdate: () => {
        editorState = { editor };
        scheduleSync();
        triggerDecorationsUpdate();
      },
      onTransaction: () => {
        editorState = { editor };
        extractHeadings();
      },
      onSelectionUpdate: ({ editor: ed }) => {
        if (!ed || !editorElement) return;
        const { from } = ed.state.selection;
        const resolved = ed.state.doc.resolve(from);
        const blockNode = resolved.node(1);
        if (blockNode) {
          const blockId = blockNode.attrs?.blockId || null;
          const semanticType = blockNode.attrs?.semanticType || blockNode.type.name;
          const text = blockNode.textContent || '';
          let offsetTop = 0;
          try {
            const domPos = ed.view.nodeDOM(resolved.before(1));
            if (domPos && domPos.getBoundingClientRect && editorElement) {
              const editorRect = editorElement.getBoundingClientRect();
              const blockRect = domPos.getBoundingClientRect();
              offsetTop = Math.max(0, blockRect.top - editorRect.top);
            }
          } catch (err) {
            // Ignore DOM measurement errors during rapid edits
          }
          onFocusedBlockChange?.({ blockId, semanticType, text, offsetTop });
        }
      },
    });
    editorState = { editor };
    if (learningDocument) initialiseEditor(learningDocument);
  });

  $effect(() => {
    if (editor && learningDocument && learningDocument.document_id !== loadedDocumentId) {
      initialiseEditor(learningDocument);
    }
  });

  $effect(() => {
    const shouldBeEditable = !isLocked;
    if (editor && editor.isEditable !== shouldBeEditable) {
      untrack(() => {
        editor.setEditable(shouldBeEditable);
      });
    }
  });

  onDestroy(() => {
    clearTimeout(saveTimer);
    clearTimeout(classifyTimer);
    clearTimeout(probeTimer);
    editor?.destroy();
  });
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') closeSentenceChat(); }} />

<div class="canvas-split-container" class:has-chat-open={Boolean(activeSentence)} class:has-outline-open={isOutlineOpen}>
  <!-- Left Document Outline Navigation Panel -->
  <DocumentOutlineSidebar
    isOpen={isOutlineOpen}
    {totalPages}
    {documentHeadings}
    {pagesMap}
    {currentPageIndex}
    onGoToPage={goToPage}
    onJumpToHeading={jumpToOutlineHeading}
    onClose={() => (isOutlineOpen = false)}
  />

  <!-- Main Canvas Pane (Pushes to left when chat drawer is open) -->
  <main class="editor-main-pane">
    <section 
      class="minimal-notion-shell width-{canvasWidthMode}" 
      aria-label="Paginated A4 Socratic Canvas"
    >
      <!-- Minimalist Top Navigation & Status -->
      <DocumentEditorHeader
        bind:isOutlineOpen
        editor={editorState.editor}
        {isLocked}
        onToggleCanvasLock={toggleCanvasLock}
        bind:isEpistemicLens
        {epistemicMetrics}
        bind:canvasWidthMode
        onSetCanvasWidthMode={setCanvasWidthMode}
        {isZenFullscreen}
        {onToggleZen}
        {isSaving}
        {isDirty}
        {saveError}
        {saveErrorDetails}
        {lastConfirmedSaveAt}
        onSyncNow={syncNow}
        onSetBlock={setBlock}
        onToggleHeading={(level) => editorState.editor?.chain().focus().toggleHeading({ level }).run()}
        onToggleMark={toggleMark}
      />

      {#if recoverySnapshot && !isDirty}
        <aside class="document-recovery-banner" role="status">
          <div>
            <strong>Unsaved local draft found</strong>
            <p>
              A copy from {new Date(recoverySnapshot.savedAt).toLocaleString()} is stored on this device.
              Restore it only if it is the version you want to save.
            </p>
          </div>
          <div class="document-recovery-actions">
            <button type="button" class="recovery-restore-btn" onclick={restoreLocalRecovery}>Restore local draft</button>
            <button type="button" class="recovery-discard-btn" onclick={discardLocalRecovery}>Discard copy</button>
          </div>
        </aside>
      {/if}

      <!-- Pristine A4 Document Page (Strict A4 Aspect Ratio 210 / 297 with Integrated Header & Footer) -->
      <div class="document-page" class:epistemic-active={isEpistemicLens}>
        <div class="document-page-header">
          <span class="page-watermark">
            {#if totalPages > 1}
              Page {currentPageIndex} of {totalPages}
              <span class="page-watermark-dim">• A4</span>
            {:else}
              <span class="page-watermark-dim">A4</span>
            {/if}
          </span>
        </div>

        <div bind:this={editorElement} class="notion-editor-container"></div>

        <!-- Integrated A4 Document Footer (Inside the page, zero external margins) -->
        <footer class="document-page-footer">
          <div class="page-footer-stats">
            <span>{wordCount.toLocaleString()} words</span>
            <span>•</span>
            <span>{readingTimeMin} min read</span>
            {#if totalPages > 1}
              <span>•</span>
              <span>Page {currentPageIndex} of {totalPages}</span>
            {/if}
            {#if documentHeadings.length > 0}
              <span>•</span>
              <span>{documentHeadings.length} {documentHeadings.length === 1 ? 'section' : 'sections'}</span>
            {/if}
            {#if !isLocked}
              <span>•</span>
              <button type="button" class="page-footer-add-btn" onclick={addNewBlankPage} title="Add a new page">＋ Add page</button>
            {/if}
          </div>

          {#if totalPages > 1}
            <div class="page-footer-pagination">
              <button 
                type="button" 
                class="page-nav-mini-btn" 
                onclick={prevPage}
                disabled={currentPageIndex <= 1}
                title="Previous page"
              >
                ‹
              </button>
              {#each Object.keys(pagesMap).map(Number).sort((a, b) => a - b) as p}
                <button 
                  type="button" 
                  class="page-mini-pill" 
                  class:active={p === currentPageIndex}
                  onclick={() => goToPage(p)}
                  title="Go to Page {p}"
                >
                  {p}
                </button>
              {/each}
              <button 
                type="button" 
                class="page-nav-mini-btn" 
                onclick={nextPage}
                disabled={currentPageIndex >= totalPages}
                title="Next page"
              >
                ›
              </button>
              {#if totalPages > 1 && !isLocked}
                <button 
                  type="button" 
                  class="page-delete-mini-btn" 
                  onclick={() => deletePage(currentPageIndex)}
                  title="Delete current page ({currentPageIndex})"
                >
                  ✕
                </button>
              {/if}
            </div>
          {/if}
        </footer>
      </div>
    </section>
  </main>

  <!-- Assistant drawer replaced by Zone 3 Socratic Marginalia Gutter & Top Bar Copilot -->
</div>

<style>
  /* -------------------------------------------------------------
     Notion-Style Minimal Shell & Typography
     ------------------------------------------------------------- */
  .minimal-notion-shell {
    margin: 0 auto 0;
    padding-bottom: 0;
    width: 100%;
    max-width: 860px;
    --canvas-font-size: 17.5px;
    --canvas-padding: clamp(40px, 4.5vw, 60px) clamp(36px, 4vw, 56px) clamp(20px, 2.5vw, 30px);
    display: flex;
    flex-direction: column;
    gap: 0;
    flex-shrink: 0;
    min-height: min-content;
    height: auto;
    transition: max-width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .minimal-notion-shell.width-narrow {
    max-width: 680px;
  }

  .minimal-notion-shell.width-wide {
    max-width: 860px;
  }

  .minimal-notion-shell.width-max {
    max-width: 1140px;
  }

  .canvas-width-picker {
    display: inline-flex;
    align-items: center;
    position: relative;
  }

  .canvas-width-select {
    appearance: none;
    -webkit-appearance: none;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: var(--radius-xs, 4px);
    color: var(--color-heading, #334155);
    font-family: inherit;
    font-size: 11px;
    font-weight: 600;
    height: 24px;
    line-height: 22px;
    padding: 0 18px 0 7px;
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 5px center;
    background-size: 8px 8px;
    transition: all 0.15s ease;
  }

  .canvas-width-select:hover {
    border-color: var(--color-aurora, #0284c7);
    color: var(--color-heading, #0f172a);
  }

  .canvas-width-select:focus {
    outline: none;
    border-color: var(--color-aurora, #0284c7);
    box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.15);
  }

  :global([data-theme="dark"]) .canvas-width-select {
    background-color: var(--color-graphite-card, #1e293b);
    border-color: var(--color-graphite-border, #334155);
    color: var(--color-slate-bright, #e2e8f0);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  }

  .btn-zen-canvas-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: var(--radius-xs, 4px);
    color: var(--color-slate-subtle, #64748b);
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
    line-height: 1;
  }

  .btn-zen-canvas-toggle:hover {
    border-color: var(--color-aurora, #0284c7);
    color: var(--color-aurora, #0284c7);
    background: rgba(2, 132, 199, 0.08);
  }

  .btn-zen-canvas-toggle.active {
    background: rgba(45, 212, 191, 0.14);
    border-color: rgba(45, 212, 191, 0.6);
    color: var(--color-teal-dark, #0f766e);
  }

  :global([data-theme="dark"]) .btn-zen-canvas-toggle.active {
    background: rgba(45, 212, 191, 0.2);
    border-color: rgba(45, 212, 191, 0.6);
    color: var(--color-teal-bright, #2dd4bf);
  }

  .minimal-toolbar {
    background: var(--color-bone-muted, #f4f5f0);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: var(--radius-md, 8px);
    padding: 6px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }

  .toolbar-left, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .v-divider {
    width: 1px;
    height: 16px;
    background: var(--color-graphite-border, #e2e4dc);
    margin: 0 4px;
  }

  .tool-btn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: var(--radius-xs, 4px);
    color: var(--color-slate-light, #474d5a);
    font-family: var(--font-ui, sans-serif);
    font-size: 12px;
    font-weight: 600;
    padding: 4px 8px;
    cursor: pointer;
    transition: all 0.12s ease;
  }

  .tool-btn.lock-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: var(--radius-xs, 4px);
    transition: all 0.15s ease;
    cursor: pointer;
  }

  .tool-btn.lock-toggle-btn.locked {
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #92400e;
  }

  .tool-btn.lock-toggle-btn.locked:hover {
    background: #fde68a;
    color: #78350f;
  }

  .tool-btn.lock-toggle-btn.unlocked {
    background: #dcfce7;
    border: 1px solid #bbf7d0;
    color: #166534;
  }

  .tool-btn.lock-toggle-btn.unlocked:hover {
    background: #bbf7d0;
    color: #14532d;
  }

  :global([data-theme="dark"]) .tool-btn.lock-toggle-btn.locked {
    background: rgba(245, 158, 11, 0.2);
    border-color: rgba(245, 158, 11, 0.4);
    color: #fbbf24;
  }

  :global([data-theme="dark"]) .tool-btn.lock-toggle-btn.unlocked {
    background: rgba(34, 197, 94, 0.2);
    border-color: rgba(34, 197, 94, 0.4);
    color: #4ade80;
  }

  .tool-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #e8eae3);
    color: var(--color-heading, #121418);
  }

  .tool-btn.active {
    background: rgba(2, 132, 199, 0.12);
    border-color: rgba(2, 132, 199, 0.3);
    color: var(--color-aurora, #0284c7);
  }

  .add-page-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--color-heading, #121418);
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
  }

  .add-page-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #e8eae3);
    border-color: var(--color-aurora, #0284c7);
    color: var(--color-aurora, #0284c7);
  }

  .page-count-badge {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-muted, #646a78);
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.04);
    white-space: nowrap;
  }

  .toolbar-center {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  /* Clean, High-Contrast Truth Highlights Toggle */
  .truth-highlights-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 28px;
    padding: 0 10px;
    border-radius: 6px;
    font-family: var(--font-ui, sans-serif);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    background: var(--color-graphite, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    color: var(--color-slate-light, #474d5a);
  }

  .truth-highlights-toggle:hover {
    background: var(--color-graphite-hover, #e8eae3);
    border-color: var(--color-horizon-blue, #4F6BFF);
    color: var(--color-heading, #121418);
  }

  .truth-highlights-toggle.active {
    background: var(--color-horizon-blue-soft, #EBF0FF);
    border-color: rgba(79, 107, 255, 0.4);
    color: var(--color-horizon-blue, #4F6BFF);
    box-shadow: none;
  }

  .truth-toggle-ring {
    width: 10px;
    height: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .truth-toggle-pip {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #94a3b8;
    transition: all 0.15s ease;
  }

  .truth-highlights-toggle.active .truth-toggle-pip {
    background: var(--color-horizon-blue, #4F6BFF);
  }

  .truth-toggle-pill {
    font-size: 9.5px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 4px;
    letter-spacing: 0.04em;
    background: rgba(0, 0, 0, 0.06);
    color: var(--color-slate-muted, #646a78);
    transition: all 0.15s ease;
  }

  .truth-highlights-toggle.active .truth-toggle-pill {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
  }

  .epistemic-sentence-strip {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .strip-pill {
    font-size: 11px;
    font-family: var(--font-mono, monospace);
    color: var(--color-slate-muted, #646a78);
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .strip-pill strong {
    color: var(--color-heading, #121418);
  }

  .strip-pill.premature strong {
    color: #dc2626;
  }

  .save-status-text {
    font-size: 11px;
    color: var(--color-slate-muted, #646a78);
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    justify-content: flex-end;
    text-align: right;
    max-width: 390px;
  }

  .save-status-message {
    color: #b45309;
  }

  .save-status-action,
  .recovery-restore-btn,
  .recovery-discard-btn {
    border: 0;
    background: transparent;
    font: inherit;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .save-status-action,
  .recovery-restore-btn {
    color: #1d4ed8;
    font-weight: 700;
  }

  .save-status-action:disabled {
    cursor: wait;
    opacity: 0.65;
  }

  .save-status-correlation {
    color: var(--color-slate-muted, #646a78);
    font-family: var(--font-mono, monospace);
  }

  .btn-toolbar-submit {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    border-radius: var(--radius-xs, 4px);
    background: #0284c7;
    color: #ffffff;
    font-size: 11.5px;
    font-weight: 700;
    font-family: var(--font-ui, sans-serif);
    border: none;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }

  .btn-toolbar-submit:hover:not(:disabled) {
    background: #0369a1;
  }

  .btn-toolbar-submit:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .toolbar-submission-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .toolbar-submitted-chip,
  .toolbar-completed-chip {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
    background: rgba(5, 150, 105, 0.12);
    color: #059669;
    white-space: nowrap;
  }

  .toolbar-dl-pdf {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 600;
    color: #0284c7;
    background: rgba(2, 132, 199, 0.08);
    border: 1px solid rgba(2, 132, 199, 0.25);
    padding: 2px 7px;
    border-radius: 4px;
    text-decoration: none;
    transition: all 0.15s ease;
  }

  .toolbar-dl-pdf:hover {
    background: rgba(2, 132, 199, 0.16);
    color: #0369a1;
  }

  .document-recovery-banner {
    width: min(var(--canvas-width, 820px), 100%);
    margin: 0 auto 12px;
    border: 1px solid #f0c36d;
    background: #fffbeb;
    border-radius: 8px;
    padding: 12px 14px;
    color: #78350f;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .document-recovery-banner strong {
    font-size: 12px;
  }

  .document-recovery-banner p {
    margin: 3px 0 0;
    font-size: 11px;
    line-height: 1.35;
  }

  .document-recovery-actions {
    display: flex;
    flex: 0 0 auto;
    gap: 12px;
    font-size: 11px;
  }

  .recovery-discard-btn {
    color: #78350f;
  }

  /* Pristine Document Page (Responsive Paper Sheet with Auto Height and Minimum Vertical Stature) */
  .document-page {
    position: relative;
    background: var(--color-bone-surface, #ffffff);
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: var(--radius-lg, 12px);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    width: 100%;
    max-width: 100%;
    min-height: max(297mm, 1050px);
    height: auto;
    flex-shrink: 0;
    padding: var(--canvas-padding, clamp(48px, 6vw, 72px) clamp(36px, 5vw, 64px) clamp(24px, 3.5vw, 40px));
    transition: width 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    margin-bottom: 40px;
  }

  .document-page-header {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 24px;
    user-select: none;
  }

  .page-watermark {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--color-slate-muted, #94a3b8);
  }

  .page-watermark-dim {
    opacity: 0.7;
    font-weight: 500;
    margin-left: 4px;
  }

  /* Integrated Document Page Footer (Inside A4 Page) */
  .document-page-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 20px;
    border-top: 1px solid var(--color-graphite-border, #e2e4dc);
    font-size: 11px;
    color: var(--color-slate-muted, #94a3b8);
    user-select: none;
    flex-shrink: 0;
  }

  .page-footer-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .page-footer-add-btn {
    background: transparent;
    border: none;
    font-size: inherit;
    font-weight: 600;
    color: var(--color-slate-light, #64748b);
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
    padding: 0;
    transition: color 0.15s ease;
  }

  .page-footer-add-btn:hover {
    color: var(--color-horizon-blue, #4F6BFF);
  }

  .page-footer-pagination {
    display: inline-flex;
    align-items: center;
    gap: 3px;
  }

  .page-nav-mini-btn {
    background: transparent;
    border: 1px solid var(--color-graphite-border, #e2e4dc);
    border-radius: 4px;
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    color: var(--color-heading, #121418);
    cursor: pointer;
  }

  .page-nav-mini-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover, #e8eae3);
  }

  .page-nav-mini-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .page-mini-pill {
    min-width: 22px;
    height: 22px;
    padding: 0 4px;
    border-radius: 4px;
    border: 1px solid transparent;
    background: transparent;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-slate-light, #474d5a);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .page-mini-pill:hover:not(.active) {
    background: var(--color-graphite-hover, #e8eae3);
  }

  .page-mini-pill.active {
    background: var(--color-horizon-blue, #4F6BFF);
    color: #ffffff;
  }

  .page-delete-mini-btn {
    background: transparent;
    border: none;
    font-size: 11px;
    color: #dc2626;
    cursor: pointer;
    margin-left: 2px;
    padding: 2px 4px;
  }

  .notion-editor-container {
    flex: 1 0 auto;
    display: flex;
    flex-direction: column;
    height: auto;
  }

  .notion-editor-container :global(.notion-minimal-prosemirror) {
    color: var(--color-slate-bright);
    font-family: var(--font-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    font-size: var(--canvas-font-size, 16.5px);
    line-height: 1.8;
    flex: 1 0 auto;
    height: auto;
    outline: none;
    transition: font-size 0.2s ease;
  }

  .notion-editor-container :global(.notion-minimal-prosemirror p) {
    margin: 0 0 1.25em;
    color: var(--color-slate-bright);
  }

  .notion-editor-container :global(.notion-minimal-prosemirror h1) {
    color: var(--color-heading);
    font-size: 1.85em;
    font-weight: 800;
    letter-spacing: -0.4px;
    margin: 1.6em 0 0.5em;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 8px;
  }

  .notion-editor-container :global(.notion-minimal-prosemirror h2) {
    color: var(--color-heading);
    font-size: 1.4em;
    font-weight: 700;
    letter-spacing: -0.2px;
    margin: 1.4em 0 0.4em;
  }

  .notion-editor-container :global(.notion-minimal-prosemirror blockquote) {
    border-left: 3px solid var(--color-horizon-blue, #4F6BFF);
    margin: 1.2em 0;
    padding: 8px 18px;
    color: var(--color-slate-light);
    font-style: italic;
    background: var(--color-horizon-blue-soft, #EBF0FF);
    border-radius: 0 6px 6px 0;
  }

  .notion-editor-container :global(.notion-minimal-prosemirror p.is-editor-empty:first-child::before) {
    color: var(--color-slate-subtle);
    content: 'Start writing, or open the Enquirer to plan your next step.';
    float: left;
    height: 0;
    pointer-events: none;
    font-style: italic;
  }

  /* -------------------------------------------------------------
     Sentence-Level Epistemic Highlighting (Native Inline Spans)
     ------------------------------------------------------------- */
  .document-page.epistemic-active :global(.epistemic-sentence) {
    transition: all 0.15s ease;
    border-radius: 2px;
    padding: 1px 2px;
    margin: 0 1px;
    cursor: pointer;
  }

  /* 🔵 Claims: Defensible assertions under test */
  .document-page.epistemic-active :global(.epistemic-sentence.claim) {
    border-bottom: 2px solid rgba(79, 107, 255, 0.55);
  }
  .document-page.epistemic-active :global(.epistemic-sentence.claim:hover) {
    background: rgba(79, 107, 255, 0.1);
    border-bottom-color: var(--color-horizon-blue, #4F6BFF);
  }

  /* 🟢 Grounded Evidence: Primary source data / citations */
  .document-page.epistemic-active :global(.epistemic-sentence.evidence) {
    border-bottom: 2px solid rgba(95, 175, 122, 0.65);
    background: rgba(95, 175, 122, 0.08);
  }
  .document-page.epistemic-active :global(.epistemic-sentence.evidence:hover) {
    background: rgba(95, 175, 122, 0.15);
    border-bottom-color: var(--color-signal-green, #5FAF7A);
  }

  /* 🟣 Causal Reasoning: Warrants & connective mechanisms */
  .document-page.epistemic-active :global(.epistemic-sentence.reasoning) {
    border-bottom: 2px solid rgba(139, 92, 246, 0.6);
  }
  .document-page.epistemic-active :global(.epistemic-sentence.reasoning:hover) {
    background: rgba(139, 92, 246, 0.1);
    border-bottom-color: var(--color-aurora, #8b5cf6);
  }

  /* 🟡 Assumptions: Presuppositions taken for granted */
  .document-page.epistemic-active :global(.epistemic-sentence.assumption) {
    border-bottom: 2px solid rgba(216, 154, 58, 0.65);
    background: rgba(216, 154, 58, 0.08);
  }
  .document-page.epistemic-active :global(.epistemic-sentence.assumption:hover) {
    background: rgba(216, 154, 58, 0.16);
    border-bottom-color: var(--color-amber, #D89A3A);
  }

  /* 🔴 Premature Closures: Unsupported conclusion leaps */
  .document-page.epistemic-active :global(.epistemic-sentence.premature_closure) {
    border-bottom: 2px dashed var(--color-rose, #B74C4C);
    background: rgba(183, 76, 76, 0.08);
  }
  .document-page.epistemic-active :global(.epistemic-sentence.premature_closure:hover) {
    background: rgba(183, 76, 76, 0.16);
  }

  :global(.sentence-pulse-highlight) {
    animation: pulseSentence 1.5s ease-out;
  }

  @keyframes pulseSentence {
    0% { background: rgba(139, 92, 246, 0.35); }
    100% { background: transparent; }
  }

  /* -------------------------------------------------------------
     Split-Pane Layout: Editor (Left) & Socratic Oracle Chat Drawer (Right)
     ------------------------------------------------------------- */
  .canvas-split-container {
    display: flex;
    width: 100%;
    height: 100%;
    flex: 1;
    min-height: 0;
    overflow: hidden;
    position: relative;
    transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  }

  /* -------------------------------------------------------------
     Main Editor Pane Layout
     ------------------------------------------------------------- */


  .editor-main-pane {
    flex: 1;
    min-width: 0;
    height: 100%;
    overflow-y: auto;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 16px 20px 48px;
    transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .canvas-split-container.has-chat-open .editor-main-pane {
    padding-right: 16px;
  }
  /* Socratic chat drawer removed in favor of RightWorkbenchGutter */

  /* Active Sentence in Editor */
  :global(.epistemic-sentence.is-active-sentence) {
    background: rgba(217, 119, 6, 0.16) !important;
    outline: 2px solid var(--color-horizon-blue, #2563eb) !important;
    outline-offset: 2px;
    border-radius: 3px;
    box-shadow: 0 0 12px rgba(37, 99, 235, 0.25);
  }

  /* Minimal Footer */
  .minimal-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 12px;
    color: var(--color-slate-muted, #64748b);
    padding: 8px 0;
  }

  .footer-add-page-btn {
    background: transparent;
    border: none;
    font-size: inherit;
    font-weight: 600;
    color: var(--color-slate-light, #64748b);
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
    padding: 0;
    transition: color 0.15s ease;
  }

  .footer-add-page-btn:hover {
    color: var(--color-horizon-blue, #4F6BFF);
  }
</style>
