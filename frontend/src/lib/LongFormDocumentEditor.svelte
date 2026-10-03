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
  import DocumentRecoveryBanner from './editor/DocumentRecoveryBanner.svelte';
  import DocumentPageFooter from './editor/DocumentPageFooter.svelte';
  import './editor/editorContent.css';
  import {
    fetchLLMEpistemicClassification,
    fetchSentenceInquiry,
  } from './editor/editorProbes';
  import {
    insertEvidenceBlock as doInsertEvidenceBlock,
    insertCapsuleText as doInsertCapsuleText,
    insertWritingFrame as doInsertWritingFrame,
    insertSourceQuote as doInsertSourceQuote,
  } from './editor/editorInsertHelpers';
  import {
    currentEditorBlocks as getCurrentEditorBlocks,
    currentBlocks as getCurrentBlocks,
    blockSignature as getBlockSignature,
    extractDocumentHeadings,
    createBlankPage,
    reindexPagesAfterDeletion,
  } from './editor/editorPageManager';

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
    doInsertEvidenceBlock(editor, { quoteText, sourceTitle, author, sourceId, sourceUrl }, scheduleSync);
  }

  export function insertCapsuleText({ text = '', role = 'qualification', sourceTitle = '' } = {}) {
    doInsertCapsuleText(editor, { text, role, sourceTitle }, scheduleSync);
  }

  export function insertWritingFrame(frameType = 'claim') {
    doInsertWritingFrame(editor, frameType, scheduleSync);
  }

  export function insertSourceQuote(source) {
    doInsertSourceQuote(editor, source, scheduleSync);
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
    pagesMap[nextP] = createBlankPage(nextP);
    goToPage(nextP);
    scheduleSync();
  }

  function deletePage(pageToDelete) {
    if (isLocked || totalPages <= 1) return;
    saveCurrentPageEdits();
    pagesMap = reindexPagesAfterDeletion(pagesMap, pageToDelete);
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
    const data = await fetchLLMEpistemicClassification({
      sessionId,
      sessionAccessToken,
      paragraphText,
      oraclePressure,
    });
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
  }

  // --- On-Demand Socratic Dialectic Agent Inquiry ---
  async function requestSentenceInquiry(sentenceText, moveType = 'challenge', epistemicType = 'claim') {
    isOracleThinking = true;
    try {
      const data = await fetchSentenceInquiry({
        sessionId,
        sessionAccessToken,
        sentenceText,
        moveType,
        epistemicType,
        oraclePressure,
      });
      if (!data) return;
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
    const headings = extractDocumentHeadings(editor, pagesMap, currentPageIndex);
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
    return getCurrentEditorBlocks(editor, pageIdx || currentPageIndex);
  }

  export function currentBlocks() {
    return getCurrentBlocks(editor, pagesMap, currentPageIndex);
  }

  function blockSignature(block) {
    return getBlockSignature(block);
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
        <DocumentRecoveryBanner
          {recoverySnapshot}
          onRestore={restoreLocalRecovery}
          onDiscard={discardLocalRecovery}
        />
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
        <DocumentPageFooter
          {wordCount}
          {readingTimeMin}
          {totalPages}
          {currentPageIndex}
          documentHeadingsCount={documentHeadings.length}
          {isLocked}
          {pagesMap}
          onAddNewPage={addNewBlankPage}
          onPrevPage={prevPage}
          onNextPage={nextPage}
          onGoToPage={goToPage}
          onDeletePage={deletePage}
        />
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
</style>
