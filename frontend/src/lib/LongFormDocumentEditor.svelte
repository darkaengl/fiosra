<script>
  import { onDestroy, onMount } from 'svelte';
  import { Editor, Extension } from '@tiptap/core';
  import { Plugin } from '@tiptap/pm/state';
  import StarterKit from '@tiptap/starter-kit';

  let {
    learningDocument = null,
    assignment = null,
    disabled = false,
    onSync = async () => null,
    onSynced = () => null,
    onOpenSources = () => null,
    onOpenAssist = () => null,
    onOpenQuestions = () => null,
    onHeadingsChange = () => null,
    probeCount = 0,
  } = $props();

  const blockTypes = {
    heading: 'heading',
    paragraph: 'paragraph',
    blockquote: 'blockquote',
    bulletList: 'bullet_list',
    orderedList: 'ordered_list',
  };
  const supportedTopLevelTypes = new Set(Object.keys(blockTypes));

  const BlockIdentity = Extension.create({
    name: 'fiosraBlockIdentity',
    addGlobalAttributes() {
      return [{
        types: Object.keys(blockTypes),
        attributes: {
          blockId: {
            default: null,
            parseHTML: (element) => element.getAttribute('data-block-id'),
            renderHTML: (attributes) => attributes.blockId ? { 'data-block-id': attributes.blockId } : {},
          },
          sectionId: { default: null },
          authorType: { default: 'student' },
        },
      }];
    },
    addProseMirrorPlugins() {
      return [new Plugin({
        appendTransaction(transactions, _oldState, newState) {
          if (!transactions.some((transaction) => transaction.docChanged)) return null;
          const transaction = newState.tr;
          const seenBlockIds = new Set();
          newState.doc.forEach((node, offset) => {
            const duplicatedIdentity = node.attrs.blockId && seenBlockIds.has(node.attrs.blockId);
            if (supportedTopLevelTypes.has(node.type.name) && (!node.attrs.blockId || duplicatedIdentity)) {
              transaction.setNodeMarkup(offset, undefined, {
                ...node.attrs,
                blockId: crypto.randomUUID(),
                authorType: 'student',
              });
            }
            seenBlockIds.add(node.attrs.blockId);
          });
          return transaction.docChanged ? transaction : null;
        },
      })];
    },
  });

  let editorElement;
  let editor = null;
  let editorState = $state({ editor: null });
  let baseRevision = $state(0);
  let baseline = {};
  let isSaving = $state(false);
  let isDirty = $state(false);
  let saveError = $state('');
  let wordCount = $state(0);
  let readingTimeMin = $derived(Math.max(1, Math.ceil(wordCount / 200)));
  let saveTimer;
  let loadedDocumentId = '';

  let isAssistPaletteOpen = $state(false);
  let documentHeadings = $state([]);

  function createBlockId() {
    return crypto.randomUUID();
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function normalizedNode(node, index) {
    const safeType = supportedTopLevelTypes.has(node?.type) ? node.type : 'paragraph';
    const attrs = { ...(node?.attrs || {}) };
    attrs.blockId = attrs.blockId || createBlockId();
    attrs.authorType = attrs.authorType === 'student_edited_assistance'
      ? 'student_edited_assistance'
      : 'student';
    if (safeType === 'heading' && ![1, 2, 3].includes(attrs.level)) attrs.level = 2;
    return {
      ...clone(node || { type: safeType }),
      type: safeType,
      attrs,
      content: node?.content || [],
      position: index + 1,
    };
  }

  function documentContentFromState(state) {
    const blocks = (state?.blocks || []).map((block) => {
      const content = clone(block.content);
      content.attrs = {
        ...(content.attrs || {}),
        blockId: block.block_id,
        sectionId: block.section_id || null,
        authorType: block.author_type || 'student',
      };
      return content;
    });
    return { type: 'doc', content: blocks.length ? blocks : [{ type: 'paragraph' }] };
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
  }

  function extractHeadings() {
    if (!editor) return;
    const headings = [];
    editor.state.doc.descendants((node, pos) => {
      if (node.type.name === 'heading') {
        headings.push({
          pos,
          level: node.attrs.level || 2,
          text: node.textContent || 'Untitled section',
          blockId: node.attrs.blockId,
        });
      }
    });
    documentHeadings = headings;
    onHeadingsChange(headings);
  }

  export function scrollToHeading(pos) {
    if (!editor) return;
    editor.chain().focus().setTextSelection(pos).scrollIntoView().run();
  }

  function initialiseEditor(state) {
    if (!editor || !state) return;
    loadedDocumentId = state.document_id;
    editor.commands.setContent(documentContentFromState(state), { emitUpdate: false });
    syncBaseline(state);
    isDirty = false;
    saveError = '';
  }

  function currentBlocks() {
    if (!editor) return [];
    return (editor.getJSON().content || [])
      .map(normalizedNode)
      .map((node) => ({
        block_id: node.attrs.blockId,
        block_type: blockTypes[node.type],
        content: {
          type: node.type,
          attrs: node.attrs,
          ...(node.content?.length ? { content: node.content } : {}),
        },
        position: node.position,
        section_id: node.attrs.sectionId || null,
        author_type: node.attrs.authorType || 'student',
      }));
  }

  function blockSignature(block) {
    return JSON.stringify(block);
  }

  function updateEditorMetrics() {
    wordCount = editor?.getText().trim().split(/\s+/).filter(Boolean).length || 0;
    extractHeadings();
  }

  function scheduleSync() {
    if (disabled || !editor) return;
    isDirty = true;
    saveError = '';
    updateEditorMetrics();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => syncNow(), 900);
  }

  async function syncNow() {
    clearTimeout(saveTimer);
    if (!editor || disabled || isSaving || !isDirty) return;
    const blocks = currentBlocks();
    const next = Object.fromEntries(blocks.map((block) => [block.block_id, blockSignature(block)]));
    const upserts = blocks.filter((block) => baseline[block.block_id] !== next[block.block_id]);
    const deletedBlockIds = Object.keys(baseline).filter((blockId) => !next[blockId]);
    if (!upserts.length && !deletedBlockIds.length) {
      isDirty = false;
      return;
    }
    isSaving = true;
    saveError = '';
    try {
      const synced = await onSync({
        base_revision: baseRevision,
        upserts,
        deleted_block_ids: deletedBlockIds,
      });
      if (!synced) return;
      syncBaseline(synced);
      isDirty = false;
      onSynced(synced);
    } catch (error) {
      saveError = error?.message || 'This document could not be saved.';
    } finally {
      isSaving = false;
    }
  }

  export function addSection(title = 'New Section') {
    if (!editor || disabled) return;
    const sectionId = `section_${Date.now().toString(36)}`;
    editor.chain().focus('end').insertContent([
      {
        type: 'heading',
        attrs: { blockId: createBlockId(), sectionId, authorType: 'student', level: 2 },
        content: [{ type: 'text', text: title }],
      },
      {
        type: 'paragraph',
        attrs: { blockId: createBlockId(), sectionId, authorType: 'student' },
      },
    ]).run();
  }

  function setBlock(type, attrs = {}) {
    editor?.chain().focus().setNode(type, attrs).run();
  }

  function toggleMark(mark) {
    if (!editor || disabled) return;
    if (mark === 'bold') editor.chain().focus().toggleBold().run();
    if (mark === 'italic') editor.chain().focus().toggleItalic().run();
  }

  export function insertSourceQuote(source) {
    if (!editor || disabled) return;
    const title = source.title || 'Course Evidence';
    const excerpt = source.excerpt || '';
    editor.chain().focus().insertContent([
      {
        type: 'blockquote',
        attrs: { blockId: createBlockId(), authorType: 'student' },
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: `“${excerpt}” — [Source: ${title}]` }]
        }]
      },
      {
        type: 'paragraph',
        attrs: { blockId: createBlockId(), authorType: 'student' },
        content: [{ type: 'text', text: 'Based on this evidence, ' }]
      }
    ]).run();
  }

  export function insertWritingFrame(frameType) {
    if (!editor || disabled) return;
    let title = 'Working Claim';
    let prompt = 'State your clear, defensible provisional claim.';
    if (frameType === 'evidence') {
      title = 'Source Observations';
      prompt = 'Record what the approved primary source directly demonstrates before drawing an inference.';
    } else if (frameType === 'reasoning') {
      title = 'Reasoning & Causal Mechanism';
      prompt = 'Explain how the specific source evidence connects to and justifies your main claim.';
    } else if (frameType === 'alternative') {
      title = 'Alternative Explanation';
      prompt = 'Consider an alternative interpretation or counter-evidence that could qualify your thesis.';
    } else if (frameType === 'reflection') {
      title = 'Revision Reflection';
      prompt = 'Reflect on how your argument evolved in response to evidence and Socratic questions.';
    }

    const sectionId = `section_${Date.now().toString(36)}`;
    editor.chain().focus('end').insertContent([
      {
        type: 'heading',
        attrs: { blockId: createBlockId(), sectionId, authorType: 'student_edited_assistance', level: 2 },
        content: [{ type: 'text', text: title }],
      },
      {
        type: 'paragraph',
        attrs: { blockId: createBlockId(), sectionId, authorType: 'student_edited_assistance' },
        content: [{ type: 'text', text: prompt }],
      },
    ]).run();
    isAssistPaletteOpen = false;
  }

  onMount(() => {
    editor = new Editor({
      element: editorElement,
      extensions: [
        StarterKit.configure({
          heading: { levels: [1, 2, 3] },
          codeBlock: false,
          horizontalRule: false,
          link: false,
        }),
        BlockIdentity,
      ],
      content: { type: 'doc', content: [{ type: 'paragraph' }] },
      editorProps: {
        attributes: {
          class: 'long-form-prosemirror',
          'aria-label': 'Long-form student document editor',
        },
      },
      onUpdate: () => {
        editorState = { editor };
        scheduleSync();
      },
      onTransaction: () => {
        editorState = { editor };
        extractHeadings();
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

  onDestroy(() => {
    clearTimeout(saveTimer);
    editor?.destroy();
  });
</script>

<section class="document-shell" aria-label="Long-form reasoning document">
  <!-- Clean Focused Formatting Toolbar -->
  <header class="document-toolbar">
    <div class="toolbar-left">
      <!-- Formatting Tools -->
      <div class="format-group" role="group" aria-label="Text formatting">
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('paragraph')} 
          onclick={() => setBlock('paragraph')} 
          disabled={disabled}
          title="Normal paragraph text"
        >
          P
        </button>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('heading', { level: 1 })} 
          onclick={() => editorState.editor?.chain().focus().toggleHeading({ level: 1 }).run()} 
          disabled={disabled}
          title="Heading 1"
        >
          H1
        </button>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('heading', { level: 2 })} 
          onclick={() => editorState.editor?.chain().focus().toggleHeading({ level: 2 }).run()} 
          disabled={disabled}
          title="Heading 2 (Section Title)"
        >
          H2
        </button>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('heading', { level: 3 })} 
          onclick={() => editorState.editor?.chain().focus().toggleHeading({ level: 3 }).run()} 
          disabled={disabled}
          title="Heading 3 (Sub-heading)"
        >
          H3
        </button>
        <div class="divider-subtle"></div>
        <button 
          class="tool-btn font-bold" 
          class:active={editorState.editor?.isActive('bold')} 
          onclick={() => toggleMark('bold')} 
          disabled={disabled}
          title="Bold (Cmd+B)"
        >
          B
        </button>
        <button 
          class="tool-btn font-italic" 
          class:active={editorState.editor?.isActive('italic')} 
          onclick={() => toggleMark('italic')} 
          disabled={disabled}
          title="Italic (Cmd+I)"
        >
          I
        </button>
        <div class="divider-subtle"></div>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('bulletList')} 
          onclick={() => editorState.editor?.chain().focus().toggleBulletList().run()} 
          disabled={disabled}
          title="Bullet list"
        >
          • List
        </button>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('orderedList')} 
          onclick={() => editorState.editor?.chain().focus().toggleOrderedList().run()} 
          disabled={disabled}
          title="Numbered list"
        >
          1. List
        </button>
        <button 
          class="tool-btn" 
          class:active={editorState.editor?.isActive('blockquote')} 
          onclick={() => editorState.editor?.chain().focus().toggleBlockquote().run()} 
          disabled={disabled}
          title="Blockquote citation"
        >
          “ ”
        </button>
      </div>
    </div>

    <!-- Right Side Tools: AI Tools & Add Section -->
    <div class="toolbar-right">
      <button 
        class="tool-btn assist-btn"
        class:active={isAssistPaletteOpen}
        onclick={() => isAssistPaletteOpen = !isAssistPaletteOpen}
        disabled={disabled}
        title="Bounded Socratic writing tools & frames"
      >
        <span class="slash-symbol">/</span>
        <span>AI Tools</span>
      </button>

      <button 
        class="tool-btn add-sec-btn" 
        onclick={() => addSection('New Section')} 
        disabled={disabled}
        title="Add a new structured section heading"
      >
        + Add Section
      </button>
    </div>
  </header>

  <!-- Interactive AI Tools Palette Drawer -->
  {#if isAssistPaletteOpen}
    <div class="assist-palette" role="dialog" aria-label="Bounded AI Assistance Palette">
      <div class="palette-header">
        <div>
          <h4>Bounded Reasoning Tools</h4>
          <p>AI helps question and structure your work. It will never write your answer for you.</p>
        </div>
        <button class="close-mini-btn" onclick={() => isAssistPaletteOpen = false}>✕</button>
      </div>
      <div class="palette-grid">
        <button class="palette-card" onclick={() => insertWritingFrame('claim')}>
          <div class="palette-icon">🎯</div>
          <div>
            <strong>/frame: Working Claim</strong>
            <span>Insert a structured section to articulate your provisional thesis.</span>
          </div>
        </button>

        <button class="palette-card" onclick={() => insertWritingFrame('evidence')}>
          <div class="palette-icon">📜</div>
          <div>
            <strong>/frame: Source Observations</strong>
            <span>Insert an evidence section to document direct observations.</span>
          </div>
        </button>

        <button class="palette-card" onclick={() => insertWritingFrame('reasoning')}>
          <div class="palette-icon">⚡</div>
          <div>
            <strong>/frame: Causal Mechanism</strong>
            <span>Insert an analytical section connecting evidence to claims.</span>
          </div>
        </button>

        <button class="palette-card" onclick={() => insertWritingFrame('alternative')}>
          <div class="palette-icon">🔄</div>
          <div>
            <strong>/frame: Alternative Explanation</strong>
            <span>Consider competing hypotheses or historical counter-arguments.</span>
          </div>
        </button>

        <button class="palette-card" onclick={() => { onOpenQuestions(); isAssistPaletteOpen = false; }}>
          <div class="palette-icon">❓</div>
          <div>
            <strong>/check-understanding: Socratic Probes</strong>
            <span>Open Socratic questions testing the claims in your saved paragraphs.</span>
          </div>
        </button>
      </div>
    </div>
  {/if}

  <!-- Focused Academic Document Sheet -->
  <div class="document-page">
    <div class="document-guidance-bar">
      <div class="guidance-left">
        <span class="guidance-badge">Reasoning Document</span>
        <p>Organize your claim, primary evidence, and causal reasoning in a continuous long-form essay.</p>
      </div>
      <div class="guidance-shortcuts">
        <span class="shortcut-pill"><code>/</code> AI tools</span>
        <span class="shortcut-pill"><code>Sidebar</code> Sources & Outline</span>
      </div>
    </div>

    <div bind:this={editorElement} class="tiptap-container"></div>
  </div>

  <!-- Document Status & Metrics Footer -->
  <footer class="document-status">
    <div class="status-metrics">
      <span class="metric-pill">
        <strong>{wordCount.toLocaleString()}</strong> words
      </span>
      <span class="metric-pill">
        ~<strong>{readingTimeMin}</strong> min read
      </span>
      <span class="metric-pill">
        <strong>{documentHeadings.length}</strong> sections
      </span>
      <span class="save-state-pill" class:saving={isSaving} class:problem={saveError} class:dirty={isDirty}>
        {#if saveError}
          ⚠️ {saveError}
        {:else if isSaving}
          🔄 Saving document blocks…
        {:else if isDirty}
          ✏️ Unsaved changes (autosaving)
        {:else}
          ✓ All blocks saved
        {/if}
      </span>
    </div>

    <button 
      class="save-now-btn" 
      onclick={syncNow} 
      disabled={disabled || isSaving || !isDirty}
    >
      {isSaving ? 'Saving…' : isDirty ? 'Save Now (Cmd+S)' : 'Saved'}
    </button>
  </footer>
</section>

<style>
  .document-shell {
    margin: 0 auto;
    max-width: 960px;
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* Top Toolbar */
  .document-toolbar {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    box-shadow: var(--shadow-sm);
    flex-wrap: wrap;
  }

  .toolbar-left, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .divider-subtle {
    width: 1px;
    height: 16px;
    background: var(--color-graphite-border);
    margin: 0 2px;
    opacity: 0.6;
  }

  .format-group {
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .tool-btn {
    background: var(--color-bone-surface, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    color: var(--color-slate-light);
    font-family: var(--font-ui);
    font-size: 12px;
    font-weight: 600;
    padding: 5px 9px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: all 0.15s ease;
    min-height: 30px;
  }

  .tool-btn:hover:not(:disabled) {
    background: var(--color-graphite-hover);
    color: var(--color-heading);
    border-color: var(--color-slate-subtle);
  }

  .tool-btn.active {
    background: var(--pill-active-bg, rgba(217, 119, 6, 0.12));
    border-color: var(--color-horizon-blue);
    color: var(--color-horizon-blue);
  }

  .tool-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .font-bold { font-weight: 800; }
  .font-italic { font-style: italic; }

  .assist-btn {
    background: rgba(217, 119, 6, 0.08);
    border-color: rgba(217, 119, 6, 0.3);
    color: var(--color-horizon-blue);
  }
  .assist-btn:hover:not(:disabled), .assist-btn.active {
    background: rgba(217, 119, 6, 0.16);
    border-color: var(--color-horizon-blue);
    color: var(--color-horizon-blue);
  }
  .slash-symbol {
    font-weight: 800;
    font-size: 13px;
  }

  .add-sec-btn {
    background: var(--color-bone-muted);
    border-color: var(--color-graphite-border);
    color: var(--color-heading);
    font-weight: 700;
  }

  /* Assist Palette Drawer */
  .assist-palette {
    background: var(--color-graphite-card, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 16px;
    box-shadow: var(--shadow-lg);
    display: flex;
    flex-direction: column;
    gap: 14px;
    animation: slideDown 0.18s ease-out;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .palette-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .palette-header h4 {
    margin: 0 0 4px;
    font-family: var(--font-brand);
    font-size: 15px;
    font-weight: 700;
    color: var(--color-heading);
  }

  .palette-header p {
    margin: 0;
    font-size: 12px;
    color: var(--color-slate-muted);
    line-height: 1.4;
  }

  .close-mini-btn {
    background: transparent;
    border: none;
    color: var(--color-slate-subtle);
    font-size: 16px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: var(--radius-xs);
  }
  .close-mini-btn:hover {
    color: var(--color-heading);
    background: var(--color-graphite-hover);
  }

  .palette-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 10px;
  }

  .palette-card {
    background: var(--color-graphite-card, var(--color-graphite));
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-sm);
    padding: 11px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    text-align: left;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .palette-card:hover {
    border-color: var(--color-horizon-blue);
    background: var(--color-graphite-hover);
    transform: translateY(-1px);
  }

  .palette-icon {
    font-size: 20px;
    line-height: 1;
  }

  .palette-card strong {
    display: block;
    font-size: 12px;
    color: var(--color-heading);
    margin-bottom: 2px;
  }

  .palette-card span {
    display: block;
    font-size: 11px;
    color: var(--color-slate-muted);
    line-height: 1.35;
  }

  /* Clean Academic Sheet Page */
  .document-page {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    min-height: 680px;
    padding: clamp(24px, 5vw, 56px);
    display: flex;
    flex-direction: column;
    gap: 20px;
    transition: background 0.2s ease, border-color 0.2s ease;
  }

  .document-guidance-bar {
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }

  .guidance-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .guidance-badge {
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--pill-bg);
    border: 1px solid var(--pill-border);
    color: var(--color-heading);
    padding: 2px 8px;
    border-radius: 99px;
  }

  .guidance-left p {
    margin: 0;
    font-size: 12px;
    color: var(--color-slate-light);
  }

  .guidance-shortcuts {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .shortcut-pill {
    font-size: 11px;
    color: var(--color-slate-muted);
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .shortcut-pill code {
    background: var(--color-bone-muted);
    border: 1px solid var(--color-graphite-border);
    padding: 1px 5px;
    border-radius: var(--radius-xs);
    font-size: 10px;
    font-weight: 700;
    color: var(--color-heading);
  }

  /* ProseMirror / Tiptap styling with design tokens */
  .tiptap-container :global(.long-form-prosemirror) {
    color: var(--color-slate-bright);
    font-family: var(--font-ui);
    font-size: 16px;
    line-height: 1.8;
    min-height: 520px;
    outline: none;
  }

  .tiptap-container :global(.long-form-prosemirror h1) {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 1.85em;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 1.6em 0 0.4em;
    border-bottom: 1px solid var(--color-graphite-border);
    padding-bottom: 6px;
  }

  .tiptap-container :global(.long-form-prosemirror h2) {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 1.45em;
    font-weight: 700;
    letter-spacing: -0.3px;
    margin: 1.4em 0 0.4em;
  }

  .tiptap-container :global(.long-form-prosemirror h3) {
    color: var(--color-heading);
    font-family: var(--font-brand);
    font-size: 1.2em;
    font-weight: 600;
    margin: 1.2em 0 0.3em;
  }

  .tiptap-container :global(.long-form-prosemirror p) {
    margin: 0 0 1.1em;
    color: var(--color-slate-bright);
  }

  .tiptap-container :global(.long-form-prosemirror p.is-editor-empty:first-child::before) {
    color: var(--color-slate-subtle);
    content: 'Start writing your reasoning argument here... Type / for AI writing frames or cite sources from the left sidebar';
    float: left;
    height: 0;
    pointer-events: none;
    font-style: italic;
  }

  .tiptap-container :global(.long-form-prosemirror blockquote) {
    background: var(--color-bone-muted);
    border-left: 3px solid var(--color-horizon-blue);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    color: var(--color-slate-light);
    margin: 1.3em 0;
    padding: 10px 16px;
    font-style: italic;
  }

  .tiptap-container :global(.long-form-prosemirror ul),
  .tiptap-container :global(.long-form-prosemirror ol) {
    margin: 0 0 1.1em;
    padding-left: 1.6em;
    color: var(--color-slate-bright);
  }

  .tiptap-container :global(.long-form-prosemirror li) {
    margin-bottom: 0.35em;
  }

  .tiptap-container :global(.long-form-prosemirror li p) {
    margin: 0;
  }

  /* Status Footer */
  .document-status {
    background: var(--color-graphite);
    border: 1px solid var(--color-graphite-border);
    border-radius: var(--radius-md);
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    box-shadow: var(--shadow-sm);
    flex-wrap: wrap;
  }

  .status-metrics {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .metric-pill {
    font-size: 12px;
    color: var(--color-slate-muted);
  }

  .metric-pill strong {
    color: var(--color-heading);
  }

  .save-state-pill {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-signal-green, #059669);
    background: var(--color-signal-green-bg, #ecfdf5);
    border: 1px solid rgba(5, 150, 105, 0.2);
    padding: 2px 8px;
    border-radius: 99px;
  }

  .save-state-pill.saving {
    color: var(--color-aurora, #0284c7);
    background: rgba(2, 132, 199, 0.1);
    border-color: rgba(2, 132, 199, 0.25);
  }

  .save-state-pill.dirty {
    color: var(--color-amber, #d97706);
    background: var(--color-amber-bg, #fef3c7);
    border-color: rgba(217, 119, 6, 0.25);
  }

  .save-state-pill.problem {
    color: var(--color-rose, #dc2626);
    background: var(--color-rose-bg, #fef2f2);
    border-color: rgba(220, 38, 38, 0.25);
  }

  .save-now-btn {
    background: var(--color-horizon-blue);
    border: 1px solid var(--color-horizon-bright);
    border-radius: var(--radius-sm);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .save-now-btn:hover:not(:disabled) {
    background: var(--color-horizon-bright);
  }

  .save-now-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media print {
    .document-toolbar, .document-status, .document-guidance-bar {
      display: none !important;
    }
    .document-shell {
      margin: 0;
      max-width: 100%;
    }
    .document-page {
      border: none;
      box-shadow: none;
      padding: 0;
      min-height: 0;
    }
    .tiptap-container :global(.long-form-prosemirror) {
      color: #000;
      font-size: 12pt;
      line-height: 1.6;
    }
  }
</style>
