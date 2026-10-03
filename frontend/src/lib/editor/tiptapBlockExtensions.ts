import { Extension } from '@tiptap/core';
import { Plugin } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { EpistemicClassification, SentenceItem } from './editorTypes';
import { EPISTEMIC_CONFIG, splitIntoSentences } from './epistemicClassifier';

export const blockTypes: Record<string, string> = {
  heading: 'heading',
  paragraph: 'paragraph',
  blockquote: 'blockquote',
  bulletList: 'bullet_list',
  orderedList: 'ordered_list',
};

export const supportedTopLevelTypes = new Set(Object.keys(blockTypes));

export function createBlockId(): string {
  return crypto.randomUUID();
}

export function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}

export function normalizedNode(node: any, index: number): any {
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

export function partitionStateBlocks(blocks: any[]): Record<number, any[]> {
  const map: Record<number, any[]> = {};
  let currentP = 1;
  map[currentP] = [];

  for (const block of blocks || []) {
    let targetP: number | null = null;
    if (block.section_id && block.section_id.startsWith('page_')) {
      const num = parseInt(block.section_id.replace('page_', ''), 10);
      if (!isNaN(num) && num >= 1) targetP = num;
    } else if (block.content?.attrs?.pageNumber) {
      const num = Number(block.content.attrs.pageNumber);
      if (!isNaN(num) && num >= 1) targetP = num;
    } else if (block.content?.attrs?.isPageBreak) {
      currentP++;
      targetP = currentP;
    }

    if (targetP !== null) {
      currentP = targetP;
    }

    if (!map[currentP]) {
      map[currentP] = [];
    }

    const cleanedBlock = clone(block);
    if (cleanedBlock.content?.attrs?.isPageBreak) {
      delete cleanedBlock.content.attrs.isPageBreak;
    }
    cleanedBlock.section_id = `page_${currentP}`;
    map[currentP].push(cleanedBlock);
  }

  if (Object.keys(map).length === 0 || !map[1] || map[1].length === 0) {
    if (!map[1]) map[1] = [];
  }
  return map;
}

export function documentContentFromBlocks(blocks: any[]): { type: string; content: any[] } {
  const contentList = (blocks || []).map((block) => {
    const content = clone(block.content || { type: block.block_type || 'paragraph' });
    content.attrs = {
      ...(content.attrs || {}),
      blockId: block.block_id || createBlockId(),
      sectionId: block.section_id || null,
      authorType: block.author_type || 'student',
    };
    if (content.attrs?.isPageBreak) {
      delete content.attrs.isPageBreak;
    }
    return content;
  });
  return { type: 'doc', content: contentList.length ? contentList : [{ type: 'paragraph' }] };
}

export const BlockIdentity = Extension.create({
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
        isPageBreak: {
          default: false,
          parseHTML: (element) => element.getAttribute('data-page-break') === 'true',
          renderHTML: (attributes) => attributes.isPageBreak ? { 'data-page-break': 'true', class: 'document-page-break' } : {},
        },
        pageNumber: {
          default: null,
          parseHTML: (element) => element.getAttribute('data-page-number') ? parseInt(element.getAttribute('data-page-number')) : null,
          renderHTML: (attributes) => attributes.pageNumber ? { 'data-page-number': attributes.pageNumber } : {},
        },
      },
    }];
  },
  addProseMirrorPlugins() {
    return [
      new Plugin({
        appendTransaction(transactions, _oldState, newState) {
          if (!transactions.some((tr) => tr.docChanged)) return null;
          const tr = newState.tr;
          const seenBlockIds = new Set();
          newState.doc.forEach((node, offset) => {
            if (!supportedTopLevelTypes.has(node.type.name)) return;
            const duplicated = node.attrs.blockId && seenBlockIds.has(node.attrs.blockId);
            if (!node.attrs.blockId || duplicated) {
              tr.setNodeMarkup(offset, undefined, {
                ...node.attrs,
                blockId: createBlockId(),
                authorType: 'student',
              });
            }
            if (node.attrs.blockId) seenBlockIds.add(node.attrs.blockId);
          });
          return tr.docChanged ? tr : null;
        },
      }),
    ];
  },
});

export function createEpistemicInlineHighlighter(options: {
  getActiveSentence: () => any;
  getSentenceMap: () => Record<string, EpistemicClassification>;
  onFocusedBlockChange?: (info: { blockId: string; offsetTop: number }) => void;
}) {
  return Extension.create({
    name: 'fiosraEpistemicInlineHighlighter',
    addProseMirrorPlugins() {
      return [
        new Plugin({
          props: {
            decorations(state) {
              const decos: Decoration[] = [];
              const activeSentence = options.getActiveSentence();
              const sentenceMap = options.getSentenceMap();

              state.doc.descendants((node, pos) => {
                if ((node.type.name === 'paragraph' || node.type.name === 'blockquote') && node.isTextblock) {
                  const text = node.textContent;
                  const sentences = splitIntoSentences(text, pos + 1, sentenceMap);
                  for (const s of sentences) {
                    if (s.from < s.to) {
                      const isActive = activeSentence && activeSentence.text === s.text;
                      decos.push(
                        Decoration.inline(s.from, s.to, {
                          class: `epistemic-sentence ${s.epistemic_type} ${isActive ? 'is-active-sentence' : ''}`,
                          'data-epistemic-type': s.epistemic_type,
                          title: `${EPISTEMIC_CONFIG[s.epistemic_type]?.label || s.epistemic_type}`,
                        })
                      );
                    }
                  }
                }
              });
              return DecorationSet.create(state.doc, decos);
            },
            handleClick(view, pos, event) {
              const target = (event.target as HTMLElement)?.closest('.epistemic-sentence');
              if (target) {
                const blockEl = target.closest('[data-block-id]') as HTMLElement;
                if (blockEl && options.onFocusedBlockChange) {
                  const blockId = blockEl.getAttribute('data-block-id');
                  if (blockId) {
                    options.onFocusedBlockChange({
                      blockId,
                      offsetTop: blockEl.offsetTop,
                    });
                  }
                }
                return false; // Allow standard cursor positioning
              }
              return false;
            },
          },
        }),
      ];
    },
  });
}
