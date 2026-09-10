# Chapter 6: Long-Form Learning Documents and Bounded Assistance

Fiosra’s student workspace is now a **writer-first, long-form learning document** rather than a collection of character-limited response boxes. A learner can organise one continuous document with headings, paragraphs, quotations, and lists, adding their own sections as their reasoning grows. Assignment sections become starting outline anchors, not the maximum shape or length of the work.

> **Core invariant:** Fiosra may help a learner clarify expression, investigate an idea, and demonstrate understanding. It may not silently author assessed work, disclose Answer Vault material, make a grading decision, or claim that a learner understands content without transparent evidence.

This chapter documents the delivered **Slice 1 document foundation** and **Slice 2 proactive Socratic probes**. Answer-blind brainstorming, grammar/reformat patches, and evidence-gated drafting remain planned capabilities; they are not available in the workspace until their individually approved implementation slices ship.

## 1. Student workspace architecture

`StudentWorkspace.svelte` is the controller for `#/student`. It restores an assignment-bound session capability, loads the public assignment, and then loads the session-bound long-form document. `LongFormDocumentEditor.svelte` owns the Tiptap/ProseMirror editor lifecycle and performs a debounced incremental save of changed blocks. The `/student` route is lazy-loaded so the Tiptap runtime is not part of the initial educator application bundle.

| Surface | Default presentation | Responsibility | Server authority preserved |
|---|---|---|---|
| **Assignment bar** | Compact header | Identifies the active work and opens the full public brief. | Assignment state and public projection are loaded from the server and exclude Answer Vault data. |
| **Continuous editor** | Dominant centred writing surface | Lets a learner write, format, and add sections within one document. | The browser sends typed blocks, not trusted HTML; the server validates the structure and identity of each block. |
| **Formatting controls** | Small peripheral toolbar | Applies paragraph, heading, list, quote, and add-section operations. | A generated block UUID is validated on each save; controls never grant new server permissions. |
| **Save status** | Quiet status line | Displays saved, saving, unsaved, or recoverable error state. | Server document revision controls the authoritative saved state. |
| **Assignment brief** | Modal, on request | Shows public prompt, target KCs, and approved-source excerpts. | No hidden educator prompt, answer key, vault token, provider configuration, or session credential is shown. |
| **Questions indicator** | Small count in the assignment bar | Announces only that a paragraph-specific question is ready. | The client never supplies question text, focus, source data, or eligibility; the server evaluates canonical saved blocks. |
| **Evidence & Questions drawer** | Closed right-side drawer | Lets the learner answer, defer, or dismiss one question without changing the essay. | Probe responses are separately stored as learner evidence, never inserted into document text, and never treated as an automatic grade. |
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

## 5. Delivered proactive Socratic probes and assistance roadmap

After a successful incremental document sync, the editor starts a five-second local quiet timer. A subsequent edit cancels that timer. When it expires, the browser asks the protected probe API to evaluate only the synchronized block IDs and document revision. The service independently re-reads the active session, published assignment, canonical blocks, block revisions, and prior probe history before it decides whether a question is warranted.

The first probe planner is deterministic. It recognizes only five bounded focus types—direct observation, warrant, causal bridge, alternative explanation, and qualification—and selects its fallback question from a server-owned allow-list. LiteLLM may rephrase that question through a configured provider, but cannot decide the focus, change document text, see Answer Vault material, or create workflow state. A rephrase must be one question under 260 characters and pass answer-isolation, conclusion, and bounded-vocabulary checks; otherwise Fiosra presents the original deterministic question.

The writer remains in control. The indicator and drawer never steal focus or block composition. A learner may answer a question in the separately labelled field, defer it, dismiss it, or continue writing. An answer becomes `evidence_submitted`, not demonstrated mastery or an automatic grade. Deferment and dismissal remain visible in the trace; they do not deduct marks automatically, but leave the associated claim without a response record for a human evaluator.

| Delivered interaction | Trigger | Result | Non-negotiable safeguard |
|---|---|---|---|
| **Proactive Socratic probe** | A materially changed, learner-authored paragraph or quotation survives the five-second quiet period. | At most one compact question about a claim, source use, warrant, causal bridge, alternative, or qualification. | Non-blocking; answer-blind; capability-protected; server rate limited; learner response recorded separately and verbatim for review. |
| **Question response / Later / Dismiss** | Learner action in the optional drawer. | Creates a transparent evidence, deferral, or dismissal record while leaving the essay editable. | Cannot alter the document or grade. A submitted session cannot receive a new question or mutation. |

The long-form product design reserves the editor’s future `@` and `/` interactions for bounded help without allowing AI to become the primary author.

| Planned interaction | Trigger | Permitted result | Non-negotiable safeguard |
|---|---|---|---|
| **`/brainstorm`** | Learner request | Three to five neutral inquiry prompts, evidence gaps, or counterargument categories | No thesis, conclusion, factual assertion, source interpretation/quotation, citation, or submission-ready prose. |
| **`/grammar`, `/reformat`, `/clarify`** | Learner selects their own text | A reviewable meaning-preserving patch | Proposed diff only; it cannot add facts, named entities, numbers, citations, or source claims outside the selected context. |
| **`/draft-from-evidence`** | Learner request with qualifying demonstrated-evidence records | A labelled proposed passage from that finite evidence bundle | Never enabled for unverified claims; must map every proposition to approved sources and the learner’s recorded demonstration; learner acceptance is explicit. |

LiteLLM is the provider-neutral transport layer for the optional probe rephrasing call and any later approved live calls. The same server policy controls apply whether it routes to Ollama, OpenRouter, OpenAI-compatible endpoints, Gemini, or the deterministic fallback. Provider output is never a permission grant and never mutates document text without server validation plus learner acceptance.

### Probe API sequence

All probe requests require the opaque `X-Fiosra-Session-Token` capability. The public learner projection omits provider prompts and any hidden assignment or Answer Vault material.

| Method and path | Purpose | Key lifecycle checks |
|---|---|---|
| `POST /learning-documents/sessions/{session_id}/probes/evaluate` | Evaluates up to 20 recently synchronized canonical block IDs after the quiet period. | Active authorized session, current document revision, ownership, material text, stability, one open probe per block revision, session budget, and cooldown. |
| `GET /learning-documents/sessions/{session_id}/probes` | Restores only open or deferred questions and a small evidence count. | Capability and active published-assignment checks. |
| `POST /learning-documents/sessions/{session_id}/probes/{probe_id}/responses` | Saves a learner’s 10–6,000-character explanation as evaluator evidence. | Session/probe/document ownership and open/deferred lifecycle state. |
| `POST /learning-documents/sessions/{session_id}/probes/{probe_id}/defer` and `/dismiss` | Makes the learner’s non-blocking disposition explicit. | The essay and grade remain untouched; closed states are idempotent. |

The educator evidence dossier adds `proactive_socratic_evidence`, an ordered record of the section label, focus, exact question, status, response (when supplied), timestamps, and prompt-free generation metadata. The AutoSCORE review screen renders this separately from the legacy rubric evidence, so a human evaluator can distinguish a learner’s document from their explanatory response.

## 6. Safe modification guidance

When extending the long-form workspace, preserve all of the following:

1. Keep document writing central; do not make AI chat a permanent competing panel.
2. Preserve session capability checks on every document/probe/action endpoint.
3. Keep `document_revision` on every mutation and reject stale-tab overwrites.
4. Never put the Answer Vault, reference solution, hidden rubric answer, session token/digest, learner identity, or entire document in an LLM request by default.
5. Send and validate stable `blockId` values. Never accept a client-supplied unknown block type or arbitrary HTML as canonical content.
6. Log document events without raw student prose. Evidence/provenance records must be scoped, versioned, and visible to the correct evaluator flow.
7. Do not reinterpret a grammar patch or brainstorming card as proof of conceptual understanding.
8. Preserve the probe’s one-question, canonical-block, quiet-period, budget, cooldown, and vocabulary guardrails. Never let a provider manufacture question context or its own lifecycle state.
9. Do not release educator document/PDF access until course-scoped reviewer authorization from Issue #41 exists.

## 7. Local validation workflow

Apply the migrations to an existing development database in order, rebuild the frontend, and validate both the API contracts and the browser journey.

```bash
# From the repository root
psql -h localhost -U fiosra -d fiosra_db -f fiosra/mvp/migrations/006_long_form_document.sql
psql -h localhost -U fiosra -d fiosra_db -f fiosra/mvp/migrations/007_proactive_socratic_probes.sql

uv run ruff check fiosra tests
uv run python -m compileall -q fiosra
uv run pytest tests/test_learning_documents.py -q
uv run pytest tests/test_socratic_probes.py tests/test_llm_orchestration.py -q
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
4. Save a meaningful paragraph, wait five seconds without editing, and confirm a compact **Questions** indicator appears without opening the drawer or moving the editor cursor.
5. Open the drawer. Confirm the question is answer-blind, grounded to the assigned writing section, and does not insert or replace essay prose.
6. Answer, defer, and dismiss through separate test sessions. Confirm these outcomes are chronologically visible in the trace and that only an answer appears as evaluator evidence.
7. Exercise an API test with a synthetic 125-paragraph document exceeding 200,000 characters. Confirm no document-wide character-limit error occurs.
8. Submit the session and confirm further document edits or probe actions are rejected with `409`.

## References

[1]: https://github.com/darkaengl/fiosra/blob/main/frontend/src/routes/StudentWorkspace.svelte "Student document route controller"
[2]: https://github.com/darkaengl/fiosra/blob/main/frontend/src/lib/LongFormDocumentEditor.svelte "Tiptap document editor and incremental synchronization"
[3]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/learning_document_service.py "Capability-protected document persistence service"
[4]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/migrations/006_long_form_document.sql "Long-form document migration"
[5]: https://tiptap.dev/docs/editor/getting-started/install/svelte "Tiptap Svelte integration documentation"
