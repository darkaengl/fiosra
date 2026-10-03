import { blockTypes, normalizedNode } from './tiptapBlockExtensions';

export interface DocumentBlock {
  block_id: string;
  block_type: string;
  content: any;
  plaintext?: string;
  position: number;
  section_id: string | null;
  author_type: string;
}

export function currentEditorBlocks(editor: any, pageIdx: number): DocumentBlock[] {
  if (!editor) return [];
  const p = pageIdx;
  const rawNodes = editor.getJSON().content || [];
  return rawNodes
    .map(normalizedNode)
    .map((node: any, index: number) => {
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

export function currentBlocks(
  editor: any,
  pagesMap: Record<number, DocumentBlock[]>,
  currentPageIndex: number
): DocumentBlock[] {
  if (!editor) return [];
  pagesMap[currentPageIndex] = currentEditorBlocks(editor, currentPageIndex);

  const allBlocks: DocumentBlock[] = [];
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

export function blockSignature(block: DocumentBlock): string {
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

export function extractDocumentHeadings(
  editor: any,
  pagesMap: Record<number, DocumentBlock[]>,
  currentPageIndex: number
) {
  const headings = [];
  const pageNumbers = Object.keys(pagesMap).map(Number).sort((a, b) => a - b);
  for (const p of pageNumbers) {
    const pBlocks = (p === currentPageIndex && editor)
      ? currentEditorBlocks(editor, p)
      : (pagesMap[p] || []);
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
  return headings;
}

export function createBlankPage(nextPageNum: number): DocumentBlock[] {
  const newHeadingId = crypto.randomUUID();
  const newParaId = crypto.randomUUID();
  return [
    {
      block_id: newHeadingId,
      block_type: 'heading',
      content: {
        type: 'heading',
        attrs: { level: 2, blockId: newHeadingId, authorType: 'student', sectionId: `page_${nextPageNum}`, pageNumber: nextPageNum },
        content: [{ type: 'text', text: `Section ${nextPageNum}` }]
      },
      plaintext: `Section ${nextPageNum}`,
      position: 1,
      section_id: `page_${nextPageNum}`,
      author_type: 'student'
    },
    {
      block_id: newParaId,
      block_type: 'paragraph',
      content: {
        type: 'paragraph',
        attrs: { blockId: newParaId, authorType: 'student', sectionId: `page_${nextPageNum}`, pageNumber: nextPageNum },
        content: []
      },
      plaintext: '',
      position: 2,
      section_id: `page_${nextPageNum}`,
      author_type: 'student'
    }
  ];
}

export function reindexPagesAfterDeletion(
  pagesMap: Record<number, DocumentBlock[]>,
  pageToDelete: number
): Record<number, DocumentBlock[]> {
  const newMap: Record<number, DocumentBlock[]> = {};
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
  return newMap;
}
