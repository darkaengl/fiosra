import type { Editor } from '@tiptap/core';

export interface InsertEvidenceOptions {
  quoteText: string;
  sourceTitle?: string;
  author?: string;
  sourceId?: string;
  sourceUrl?: string;
}

export function insertEvidenceBlock(editor: Editor | null, {
  quoteText,
  sourceTitle = '',
  author = '',
  sourceId = '',
  sourceUrl = ''
}: InsertEvidenceOptions, onDone?: () => void) {
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
  onDone?.();
}

export function insertCapsuleText(
  editor: Editor | null,
  { text = '', role = 'qualification', sourceTitle = '' } = {},
  onDone?: () => void
) {
  if (!editor) return;
  const cleanText = (text || '').trim();
  if (!cleanText) return;

  if (role === 'evidence') {
    insertEvidenceBlock(editor, { quoteText: cleanText, sourceTitle: sourceTitle || 'Primary Source' }, onDone);
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
  onDone?.();
}

export function insertWritingFrame(editor: Editor | null, frameType = 'claim', onDone?: () => void) {
  if (!editor) return;
  const frameScaffolds: Record<string, { placeholder: string; semanticType: string }> = {
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
  onDone?.();
}

export function insertSourceQuote(editor: Editor | null, source: any, onDone?: () => void) {
  if (!source) return;
  insertEvidenceBlock(editor, {
    quoteText: source.excerpt || source.quote || source.text || '',
    sourceTitle: source.title || source.source_title || 'Assigned Exhibit',
    author: source.author || '',
    sourceId: source.id || source.source_id || '',
    sourceUrl: source.url || '',
  }, onDone);
}
