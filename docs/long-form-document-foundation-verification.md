# Long-Form Document Foundation Verification

**Date:** 2026-09-10  
**Scope:** Approved Slice 1 only: protected block-document storage, backward-compatible canvas import, and a minimal writer-first Tiptap workspace. AI probing, brainstorming, grammar/reformatting, and evidence-gated drafting remain unimplemented future slices.

## Browser walkthrough

The rebuilt Fiosra student route was opened locally against a published, source-grounded assignment. The session-bound long-form document loaded with the legacy canvas content imported as a continuous sequence of heading and paragraph blocks. The workspace visually prioritised the editable document and kept formatting controls compact above it.

The visible document included the imported **Working claim**, **Source observations**, **Reasoning**, **Alternative explanation**, and **Revision reflection** outline anchors, while the previous student-written claim was retained as document text. The interface displayed **unlimited document length** rather than a section character allowance.

Selecting **Add section** inserted a new heading and paragraph at the end of the document. After the debounced save completed, the status changed from **Unsaved changes** to **Saved**, and the new **New section** heading remained visible. This confirms that a learner can extend the assignment outline without an artificial fixed-section or page limit.

## Automated checks planned for release gate

The regression suite will cover session-capability protection, legacy import, revision conflict handling, rejection of malformed/unidentified blocks, post-submission immutability, and a synthetic document comprising 125 independently persisted paragraphs containing more than 200,000 characters. The final release gate will also run the complete backend suite, production frontend build, visual browser reload check, linting, and compilation.

## Reload verification

A cache-busted browser reload restored the same protected session and retained the newly added **New section** heading. The saved document state therefore survives a browser reload through the session-capability-protected API rather than relying on browser-only editor state.

## Complete release validation

The final release gate completed successfully:

| Check | Result |
|---|---:|
| Ruff | Passed for all `fiosra` modules and tests |
| Python compilation | Passed for all application modules |
| Backend regression suite | **73 passed** |
| Long-form API tests | **2 passed**, including a 125-paragraph document above 200,000 characters |
| Svelte/Vite production build | Passed; the Tiptap workspace is lazy-loaded as a route chunk |
| Git whitespace check | Passed |
| Browser console after persisted reload | No console output/errors |

The API tests additionally verified that document state cannot be loaded without the session capability, an imported long-form document retains stable block identifiers, stale updates receive `409`, malformed block identities receive `422`, and submitted sessions reject subsequent document writes.

## Rich-text identity repair validation

Browser testing revealed that splitting a rich-text paragraph could initially duplicate a ProseMirror block identity. The editor extension was corrected to detect duplicated inherited identities and replace each duplicate with a new UUID before synchronization. The production build was regenerated and the same multi-paragraph overwrite was repeated. Browser DOM inspection then reported **9 blocks and 9 unique block IDs**, and the workspace returned to **Saved** without an API error. This repair is important because stable unique block identities prevent ambiguous updates in a long document.

A final cache-busted browser reload restored the edited three-paragraph rich-text document and showed **Saved**, confirming that the repaired block identities and multi-paragraph prose persisted through the protected server API.
