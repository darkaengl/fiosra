<script>
  import { onDestroy, onMount } from 'svelte';
  import { Editor, Extension } from '@tiptap/core';
  import { Plugin } from '@tiptap/pm/state';
  import StarterKit from '@tiptap/starter-kit';

  let {
    learningDocument = null,
    disabled = false,
    onSync = async () => null,
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
  let saveTimer;
  let loadedDocumentId = '';

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
    } catch (error) {
      saveError = error?.message || 'This document could not be saved.';
    } finally {
      isSaving = false;
    }
  }

  function addSection() {
    if (!editor || disabled) return;
    const sectionId = `section_${Date.now().toString(36)}`;
    editor.chain().focus('end').insertContent([
      {
        type: 'heading',
        attrs: { blockId: createBlockId(), sectionId, authorType: 'student', level: 2 },
        content: [{ type: 'text', text: 'New section' }],
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
      onTransaction: () => editorState = { editor },
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
  <header class="document-toolbar">
    <div class="toolbar-primary">
      <span class="document-label">Long-form document</span>
      <span class="save-state" class:saving={isSaving} class:problem={saveError}>
        {#if saveError}Save needs attention{:else if isSaving}Saving…{:else if isDirty}Unsaved changes{:else}Saved{/if}
      </span>
    </div>
    <div class="format-controls" aria-label="Document formatting">
      <button onclick={() => setBlock('paragraph')} class:active={editorState.editor?.isActive('paragraph')} disabled={disabled}>Text</button>
      <button onclick={() => editorState.editor?.chain().focus().toggleHeading({ level: 2 }).run()} class:active={editorState.editor?.isActive('heading', { level: 2 })} disabled={disabled}>Heading</button>
      <button onclick={() => editorState.editor?.chain().focus().toggleBulletList().run()} class:active={editorState.editor?.isActive('bulletList')} disabled={disabled}>List</button>
      <button onclick={() => editorState.editor?.chain().focus().toggleBlockquote().run()} class:active={editorState.editor?.isActive('blockquote')} disabled={disabled}>Quote</button>
      <button class="add-section" onclick={addSection} disabled={disabled}>+ Add section</button>
    </div>
  </header>

  <div class="document-page">
    <div class="document-guidance">
      <strong>Write in your own words.</strong> Organize a continuous document with headings and paragraphs. The assignment outline is your starting point, not a character limit.
    </div>
    <div bind:this={editorElement}></div>
  </div>

  <footer class="document-status">
    <span>{wordCount.toLocaleString()} words · unlimited document length</span>
    <button class="save-now" onclick={syncNow} disabled={disabled || isSaving || !isDirty}>{isSaving ? 'Saving…' : 'Save now'}</button>
  </footer>
  {#if saveError}<p class="save-error" role="alert">{saveError}</p>{/if}
</section>

<style>
  .document-shell{margin:32px auto 0;max-width:920px}.document-toolbar{align-items:center;display:flex;gap:16px;justify-content:space-between;margin-bottom:12px}.toolbar-primary,.format-controls{align-items:center;display:flex;gap:7px}.document-label{color:#e2e8f0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.35px}.save-state{color:#86efac;font-size:11px}.save-state.saving{color:#bae6fd}.save-state.problem{color:#fca5a5}.format-controls{flex-wrap:wrap;justify-content:flex-end}.format-controls button,.save-now{background:#111b27;border:1px solid var(--color-graphite-border);border-radius:var(--radius-sm);color:#cbd5e1;cursor:pointer;font-size:11px;font-weight:700;padding:7px 9px}.format-controls button:hover:not(:disabled),.format-controls button.active{border-color:var(--color-horizon-blue);color:#fff}.format-controls button:disabled,.save-now:disabled{cursor:not-allowed;opacity:.5}.format-controls .add-section,.save-now{background:rgba(59,130,246,.14);border-color:rgba(96,165,250,.42);color:#dbeafe}.document-page{background:#101923;border:1px solid var(--color-graphite-border);border-radius:var(--radius-lg);box-shadow:0 24px 70px rgba(0,0,0,.16);min-height:680px;padding:clamp(26px,6vw,72px)}.document-guidance{border-bottom:1px solid var(--color-graphite-border);color:#94a3b8;font-size:12px;line-height:1.55;margin-bottom:28px;padding-bottom:18px}.document-guidance strong{color:#bae6fd}.document-page :global(.long-form-prosemirror){color:#f8fafc;font-family:var(--font-body);font-size:17px;line-height:1.82;min-height:560px;outline:none}.document-page :global(.long-form-prosemirror h1),.document-page :global(.long-form-prosemirror h2),.document-page :global(.long-form-prosemirror h3){color:#fff;font-family:var(--font-brand);letter-spacing:-.35px;margin:2.1em 0 .55em}.document-page :global(.long-form-prosemirror h1){font-size:2em}.document-page :global(.long-form-prosemirror h2){font-size:1.48em}.document-page :global(.long-form-prosemirror h3){font-size:1.2em}.document-page :global(.long-form-prosemirror p){margin:0 0 1.1em}.document-page :global(.long-form-prosemirror p.is-editor-empty:first-child::before){color:#64748b;content:'Begin writing your argument here…';float:left;height:0;pointer-events:none}.document-page :global(.long-form-prosemirror blockquote){border-left:3px solid var(--color-horizon-blue);color:#cbd5e1;margin:1.4em 0;padding-left:18px}.document-page :global(.long-form-prosemirror ul),.document-page :global(.long-form-prosemirror ol){margin:0 0 1.1em;padding-left:1.45em}.document-page :global(.long-form-prosemirror li p){margin:0}.document-status{align-items:center;color:var(--color-slate-muted);display:flex;font-size:11px;justify-content:space-between;padding:12px 2px}.save-error{color:#fca5a5;font-size:12px;margin:0}.active{border-color:var(--color-horizon-blue)}@media(max-width:780px){.document-shell{margin-top:22px}.document-toolbar{align-items:flex-start;flex-direction:column}.format-controls{justify-content:flex-start}.document-page{border-radius:var(--radius-md);min-height:560px;padding:26px 20px}.document-page :global(.long-form-prosemirror){font-size:16px;min-height:470px}.document-status{align-items:flex-start;flex-direction:column;gap:10px}.save-now{width:100%}}@media print{.document-toolbar,.document-status,.document-guidance{display:none}.document-shell{max-width:none}.document-page{border:0;box-shadow:none;min-height:0;padding:0}.document-page :global(.long-form-prosemirror){color:#111;font-size:11pt;line-height:1.5}}
</style>
