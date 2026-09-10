# Chapter 6: Long-Form Learning Documents and Bounded Assistance

Fiosra’s student workspace is now a **writer-first, long-form learning document** rather than a collection of character-limited response boxes. A learner can organise one continuous document with headings, paragraphs, quotations, and lists, adding their own sections as their reasoning grows. Assignment sections become starting outline anchors, not the maximum shape or length of the work.

> **Core invariant:** Fiosra may help a learner clarify expression, investigate an idea, and demonstrate understanding. It may not silently author assessed work, disclose Answer Vault material, make a grading decision, or claim that a learner understands content without transparent evidence.

This chapter documents the delivered **Slice 1 document foundation**. Proactive Socratic probes, answer-blind brainstorming, grammar/reformat patches, and evidence-gated drafting are planned capabilities; they are not available in the production workspace until their individually approved implementation slices ship.

## 1. Student workspace architecture

`StudentWorkspace.svelte` is the controller for `#/student`. It restores an assignment-bound session capability, loads the public assignment, and then loads the session-bound long-form document. `LongFormDocumentEditor.svelte` owns the Tiptap/ProseMirror editor lifecycle and performs a debounced incremental save of changed blocks. The `/student` route is lazy-loaded so the Tiptap runtime is not part of the initial educator application bundle.

| Surface | Default presentation | Responsibility | Server authority preserved |
|---|---|---|---|
| **Assignment bar** | Compact header | Identifies the active work and opens the full public brief. | Assignment state and public projection are loaded from the server and exclude Answer Vault data. |
| **Continuous editor** | Dominant centred writing surface | Lets a learner write, format, and add sections within one document. | The browser sends typed blocks, not trusted HTML; the server validates the structure and identity of each block. |
| **Formatting controls** | Small peripheral toolbar | Applies paragraph, heading, list, quote, and add-section operations. | A generated block UUID is validated on each save; controls never grant new server permissions. |
| **Save status** | Quiet status line | Displays saved, saving, unsaved, or recoverable error state. | Server document revision controls the authoritative saved state. |
| **Assignment brief** | Modal, on request | Shows public prompt, target KCs, and approved-source excerpts. | No hidden educator prompt, answer key, vault token, provider configuration, or session credential is shown. |
| **Reasoning trace link** | Secondary navigation | Opens the existing protected trace review experience. | Append-only session evidence is separate from editable document content. |

The editor initially imports the assignment’s five legacy canvas section definitions as headings and preserves every pre-existing `canvas_section_drafts` value as a paragraph below its matching heading. Legacy canvas data is retained as history and is never deleted by the import.

## 2. Document model and size policy

Migration `006_long_form_document.sql` introduces two tables:

| Table | Important fields | Purpose |
|---|---|---|
| `learning_documents` | unique `session_id`, `assignment_id`, `schema_version`, `document_revision`, timestamps | Creates one protected canonical document per learner session. |
| `learning_document_blocks` | stable `block_id`, document ID, section ID, position, typed JSON content, plaintext projection, author type, revision | Stores independently addressable document blocks so a large essay does not require a fixed-size field. |

The document schema accepts only the initial learning-editor node set: `heading`, `paragraph`, `blockquote`, `bulletList`, `orderedList`, `listItem`, `text`, and `hardBreak`. Each synchronized top-level block has a stable UUID in `attrs.blockId`; the API rejects unsupported node types, inconsistent IDs, malformed nesting, invalid block labels, and block payloads beyond safe per-request bounds.

The platform deliberately has **no low document-wide character cap**. A learner can create a 100-page essay through many independently persisted blocks. For operational resilience, the server limits individual block plaintext to 50,000 characters, block JSON to 100,000 bytes, and a synchronization request to 300 upserts/deletions. These are transport safeguards, not an essay-length policy. A client should send changed blocks only; it must not upload the complete document after each keystroke.

## 3. Protected API sequence

A valid learner receives a session capability only after starting a session for a published assignment and published question. PostgreSQL stores only the capability digest. All learning-document requests supply the raw opaque value through `X-Fiosra-Session-Token`.

```mermaid
sequenceDiagram
    autonumber
    actor Learner
    participant UI as Student Workspace + Tiptap
    participant Events as Event API
    participant Docs as Learning Document API
    participant DB as PostgreSQL

    Learner->>UI: Open a published assignment
    UI->>Events: POST /events/session
    Events->>DB: Create assignment-bound active session + capability digest
    Events-->>UI: session_id + opaque access token
    UI->>Docs: GET /learning-documents/sessions/{id} + capability
    Docs->>DB: Verify capability, session, assignment, and published status
    alt First document request
        Docs->>DB: Create document and import legacy canvas blocks
        Docs->>Events: Append learning_document_initialized
    end
    Docs-->>UI: Revisioned typed blocks
    Learner->>UI: Add/edit/reorder document blocks
    UI->>Docs: PUT /learning-documents/sessions/{id} + capability + changed blocks + base revision
    Docs->>DB: Validate node types and UUIDs; lock document revision
    Docs->>DB: Save changed blocks atomically and increment revision
    Docs->>Events: Append learning_document_synced without learner prose
    Docs-->>UI: Canonical document state
```

### Delivered endpoints

| Method and path | Required capability | Purpose | Important rejection cases |
|---|---:|---|---|
| `GET /learning-documents/sessions/{session_id}` | Yes | Loads the authorized session’s document, creating/importing it on first request. | Missing/wrong capability: `403`; unavailable/unpublished assignment: `422`. |
| `PUT /learning-documents/sessions/{session_id}` | Yes | Persists a batch of changed and deleted typed blocks using document-level optimistic concurrency. | Stale document revision: `409`; submitted/completed session: `409`; malformed node, duplicate position, ID mismatch, or unsupported node: `422`. |

A document revision is independent of a legacy per-section revision. If a concurrent tab saves first, the next document sync receives `409` and must reload rather than overwriting the newer work. The initial editor surfaces a recoverable save error; a later conflict-resolution slice will add a three-way merge workflow.

## 4. Client persistence rules

The Tiptap component converts the API’s canonical JSON into a `doc` node and retains the server-provided stable block IDs. A small ProseMirror extension gives newly created top-level blocks a UUID before they are synchronized. The client calculates the changed-block set against the last canonical response, waits 900 milliseconds after local edits, and sends only changed blocks. **Save now** flushes the same patch immediately.

Do not bypass this component by treating arbitrary HTML as a persisted source of truth. HTML is an unsafe and lossy transport for provenance-sensitive learning work. The backend stores validated JSON, derives plaintext only for safe search/verification/rendering use, and the future evidence packet will snapshot this server-owned document model.

## 5. Assistance roadmap and future safeguards

The approved long-form product design reserves the editor’s `@` and `/` interactions for bounded help without allowing AI to become the primary author.

| Planned interaction | Trigger | Permitted result | Non-negotiable safeguard |
|---|---|---|---|
| **Proactive Socratic probe** | A meaningful, stable learner-authored block after a server-side quiet period | One paragraph-specific question about a claim, source use, warrant, alternative, or qualification | Non-blocking; answer-blind; rate-limited; learner response recorded verbatim. A deferral leaves the claim not yet evidenced but does not trigger an automatic grade penalty. |
| **`/brainstorm`** | Learner request | Three to five neutral inquiry prompts, evidence gaps, or counterargument categories | No thesis, conclusion, factual assertion, source interpretation/quotation, citation, or submission-ready prose. |
| **`/grammar`, `/reformat`, `/clarify`** | Learner selects their own text | A reviewable meaning-preserving patch | Proposed diff only; it cannot add facts, named entities, numbers, citations, or source claims outside the selected context. |
| **`/draft-from-evidence`** | Learner request with qualifying demonstrated-evidence records | A labelled proposed passage from that finite evidence bundle | Never enabled for unverified claims; must map every proposition to approved sources and the learner’s recorded demonstration; learner acceptance is explicit. |

LiteLLM is the provider-neutral transport layer for any later live calls. The same server policy controls apply whether it routes to Ollama, OpenRouter, OpenAI-compatible endpoints, Gemini, or the deterministic fallback. Provider output is never a permission grant and never mutates document text without server validation plus learner acceptance.

## 6. Safe modification guidance

When extending the long-form workspace, preserve all of the following:

1. Keep document writing central; do not make AI chat a permanent competing panel.
2. Preserve session capability checks on every document/probe/action endpoint.
3. Keep `document_revision` on every mutation and reject stale-tab overwrites.
4. Never put the Answer Vault, reference solution, hidden rubric answer, session token/digest, learner identity, or entire document in an LLM request by default.
5. Send and validate stable `blockId` values. Never accept a client-supplied unknown block type or arbitrary HTML as canonical content.
6. Log document events without raw student prose. Evidence/provenance records must be scoped, versioned, and visible to the correct evaluator flow.
7. Do not reinterpret a grammar patch or brainstorming card as proof of conceptual understanding.
8. Do not release educator document/PDF access until course-scoped reviewer authorization from Issue #41 exists.

## 7. Local validation workflow

Apply the migrations to an existing development database in order, rebuild the frontend, and validate both the API contracts and the browser journey.

```bash
# From the repository root
psql -h localhost -U fiosra -d fiosra_db -f fiosra/mvp/migrations/006_long_form_document.sql

uv run ruff check fiosra tests
uv run python -m compileall -q fiosra
uv run pytest tests/test_learning_documents.py -q
uv run pytest tests -q

cd frontend
npm install
npm run build
cd ..

FIOSRA_LLM_PROVIDER=deterministic uv run uvicorn fiosra.mvp.main:app --host 0.0.0.0 --port 8000
```

Browser acceptance checks for this foundation:

1. Open a published assignment with the student route and confirm a centred continuous editor is the primary visual surface.
2. Confirm existing legacy canvas drafts appear under imported outline headings.
3. Add a section, wait for **Saved**, and reload. Confirm the heading survives the reload.
4. Confirm the assignment brief still exposes only public assignment context.
5. Exercise an API test with a synthetic 125-paragraph document exceeding 200,000 characters. Confirm no document-wide character-limit error occurs.
6. Submit the session and confirm further document edits are rejected with `409`.

## References

[1]: https://github.com/darkaengl/fiosra/blob/main/frontend/src/routes/StudentWorkspace.svelte "Student document route controller"
[2]: https://github.com/darkaengl/fiosra/blob/main/frontend/src/lib/LongFormDocumentEditor.svelte "Tiptap document editor and incremental synchronization"
[3]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/learning_document_service.py "Capability-protected document persistence service"
[4]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/migrations/006_long_form_document.sql "Long-form document migration"
[5]: https://tiptap.dev/docs/editor/getting-started/install/svelte "Tiptap Svelte integration documentation"
