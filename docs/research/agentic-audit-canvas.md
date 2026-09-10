# Audit: Guided Student Reasoning Canvas (GitHub Issue #40)

**Author:** Manus AI  
**Scope:** Guided student reasoning canvas only; GitHub issue #40  
**Repository state audited:** `feat/end-to-end-learning-workflow` at `59036e5d6fc97b42a9a23aa80736d5c6009bae8e`  
**Method:** Static inspection of the current Svelte workspace and trace views, FastAPI dialogue/event/evidence routes, assignment models and persistence, source-resource contracts, and focused automated checks. This report treats the code at the revision above as ground truth. **Verified** statements describe inspected behavior. **Proposal** statements describe recommended future work; they are not claims about the current implementation.

## Executive conclusion

Issue #40 identifies a real product boundary. The current application has a **durable dialogue-and-trace workflow**, not a student-owned claim–evidence–reasoning (CER) canvas. `StudentWorkspace.svelte` labels its center column “Socratic Reasoning Canvas,” but the interaction model is one free-form chat composer and a chronological message list. It has no assignment-declared sections, no section draft state, no source-reference object, no revision representation, no suggestion object, and no Accept/Edit/Dismiss flow. The learner can develop an argument in dialogue, but cannot construct, inspect, revise, or submit it as a structured argument artifact. [2]

The existing foundations are valuable. A public assignment projection removes the vault token; the dialogue route resolves an assignment-bound prompt server-side when a session has an assignment; the hint rung is derived from recorded events rather than trusted from the browser; and the LLM enhancement layer returns deterministic fallback copy on provider failures. These foundations make a safe canvas increment feasible. They do **not**, however, yet establish student ownership or trustworthy attribution: identity is client-declared, several event and read routes lack authorization checks, and the generic event-write route accepts arbitrary event types and payloads even after a session has been submitted. [5] [8] [9] [12]

> **Audit verdict:** Implement a contract-first vertical slice: an assignment-declared CER section schema, server-reconstructed section drafts, and deterministic, section-scoped suggestion cards with an immutable offer/action trail. Make the browser a renderer of server-authoritative canvas state rather than the authority for assignment, actor, section version, or suggestion outcome. This is the smallest slice that turns “canvas” from a label into a reviewable learning artifact while preserving the current answer-isolation model.

## Audit scope and verification record

| Area | Inspected ground truth | Verification outcome |
|---|---|---|
| Issue intent | GitHub issue #40: section schema, persistent drafts, scoped tutor context, attributable reversible suggestions, trace distinction, and deterministic provider-failure behavior. | **Verified.** The issue is open and its acceptance criteria remain unmet in full. [1] |
| Student experience | `frontend/src/routes/StudentWorkspace.svelte`, `StudentTrace.svelte`, `lib/session.js`, and `StudioReview.svelte`. | **Verified.** The workspace is dialogue-centered; trace and review visualize chronological turns and rubric evidence, not a structured canvas. [2] [3] [13] [14] |
| Assignment specification | Runtime Pydantic models in `assignment_designer/schemas.py`, JSON schema in `data/schemas/assignment_spec.schema.json`, and public-projection code in `generator.py`. | **Verified.** Neither contract defines a canvas section schema or completion guidance. [6] [7] [8] |
| Dialogue and LLM safety | `dialogue_router.py`, `dialogue_engine.py`, `llm/orchestrator.py`, and focused guardrail tests. | **Verified.** Assignment-bound dialogue is answer-isolated and hint rungs are server-derived; the deterministic fallback exists. Eleven pure guardrail assertions passed locally. [5] [10] [12] |
| Event and review evidence | `event_store.py`, `events_router.py`, `evidence_dossier/router.py`, and `evidence_dossier/synthesizer.py`. | **Verified.** The application appends and replays events, but it has no canvas event types, canvas-state projection, or author/assistance distinction. [4] [9] [11] |
| Local verification | `npm run build`; focused Ruff check; pure deterministic dialogue guardrail tests. | **Verified.** Svelte build completed successfully; Ruff reported no issues for the focused backend files; `11 passed` for pure guardrail tests. No local FastAPI service was listening on port 8000, so no live browser/API journey was executed. PostgreSQL was listening, but it was intentionally not used because the task prohibited database-data changes. |

## Current student journey: what a learner can do now

The following journey is **verified from the current code**, rather than inferred from UX mockups.

| Journey step | Current implementation | Pedagogical and product implication |
|---|---|---|
| 1. Select an assignment | `loadAssignment()` reads `assignment_id` or `course_id` from the hash. It fetches `GET /assignments/{id}`, or chooses the first published assignment from `GET /assignments?course_id=…&status=published`. | The workspace can enter a published assignment from an appropriate URL. Selecting the first result when only a course is supplied is not a learner choice mechanism. [2] |
| 2. Restore or create a session | The client creates a pseudo-student ID in `localStorage`, looks up a locally stored session ID, and calls `GET /events/session/{id}`. If needed, it calls `POST /events/session`. | This restores dialogue history per browser/assignment pseudo-identity. It is not authenticated student ownership. The server does not validate that the requesting browser owns the returned session. [2] [4] [9] |
| 3. Read assignment and sources | The left rail shows prompt, target KCs, and current hint rung. The right rail fetches up to five course syllabus chunks and shows excerpts. | The learner sees relevant material, which supports evidence-oriented reasoning. The source list is not assignment-section-specific. [2] [15] |
| 4. Add source material | `citeSource(source)` concatenates a title and the first 240 characters of a source into the free-form message textbox. | This is text insertion, not citation selection. No `chunk_id`, selected-span offsets, or source-selection event is persisted; the learner may edit or delete the pasted provenance. [2] |
| 5. Write and ask for guidance | `sendMessage()` submits one `student_input` string to `POST /dialogue/message`; it optimistically appends a user chat bubble and then appends an assistant response. A separate button makes a generic hint request. | The student can reason in prose and receive bounded Socratic questions. The system cannot tell whether a sentence is a claim, observation, inference, alternative explanation, or revision reflection. [2] [5] |
| 6. Resume later | Workspace replay reconstructs only `student_prompt_submitted` events and tutor/hint events as chat bubbles. | A learner can resume the conversation, but cannot restore a draft of a structured argument because no such draft is stored. [2] [4] |
| 7. Inspect and submit trace | `StudentTrace` fetches `/evidence/trace/{session}`, `/evidence/dossier/{session}`, and `/events/session/{session}`. It presents chronological nodes and allows submission if active. | The trace makes turn chronology visible, which is a useful precursor to metacognition. It does not show section-level before/after revisions, accepted assistance, source selections, or final canvas state. [3] [11] |
| 8. Educator review | `StudioReview` fetches the dossier and shows rubric evidence derived from student prompts, hint dependency, and misconceptions. | Educators can inspect quoted chat attempts and finalize a grade. They cannot distinguish student-authored canvas text from accepted AI assistance because neither category exists in current data. [13] [14] |

The source-controlled UX specification anticipates a section-by-section decomposed inquiry model, a stepper, distinct active/completed sections, source clipping, and turn-by-turn diffs. The production Svelte implementation does not yet implement those features. That specification is evidence of intended design, **not evidence of delivered behavior**. [16]

## Verified current-state findings

### 1. The runtime assignment contract cannot declare a canvas

`QuestionSpec` and `PublicQuestionSpec` currently contain `question_id`, prompt/domain/KCs, subproblems, hint ladder, rubric criteria, publication state, grounding information, and generation metadata. They contain no `canvas_sections`, `completion_guidance`, section ordering, requirement flag, text bound, allowed assistance type, or schema version. `_to_public_spec()` makes a shallow copy and removes only `vault_token`; it therefore has no canvas-specific projection or sensitive-field policy to enforce. [7] [8]

The broader JSON `assignment_spec.schema.json` similarly supports questions, scaffolding trees, hint ladders, misconceptions, and rubrics but lacks a CER section definition. Its hint object uses `text`, while the runtime `HintRung` uses `content`; that is a separate schema-alignment consideration if assignment schema changes are made. Neither artifact presently defines the issue’s requested assignment-level canvas contract. [6] [7]

### 2. The actual workspace is a single local composer, not persistent argument state

`StudentWorkspace` has exactly one editable state value, `userMessage`. It is bound to the dialogue textarea and cleared before a successful dialogue request. The restored state is derived from old message events; it is not a durable editor draft. On request failure, the optimistic bubble is removed and the textarea value is restored locally, but a reload or device change has no canvas draft to retrieve. [2]

This structure makes the required pedagogical separation impossible. A student cannot see the difference between an observation from a source and a conclusion drawn from it, cannot revise one component without rereading chat, and cannot give an educator a final, bounded argument assembled from identifiable components.

### 3. Current source use is not attributable evidence use

Course chunks already have durable IDs and source metadata (`chunk_id`, title, KC, resource type, optional URL, and creation time), and the course APIs can list or search those chunks. This is an appropriate substrate for source attribution. [15]

The workspace does not preserve that substrate when a learner clicks “Add as a citation.” It copies a display string into a chat message. The event created later by the dialogue route records only that entire `student_input` string and `hint_requested`; it does not separately record source ID, selected excerpt, selection range, or student rationale. Thus a trace can show that pasted text existed, but cannot reliably establish which resource was selected or how the learner used it. [2] [5]

### 4. The dialogue path has meaningful answer-isolation and bounded-hint foundations

For an assignment-bound session, `handle_dialogue_turn()` retrieves the assignment using the session’s `assignment_id`, rejects a mismatched requested assignment ID, and uses the retrieved public prompt, domain, hint ladder, and target KCs. The client-supplied `current_rung` is documented as legacy and ignored; the server reads the maximum previous rung from the event stream. This is a meaningful control against browser-authored escalation. [5] [4]

`SocraticDialogueEngine.generate_response()` does not receive a vault token or reference solution. It detects a defined set of direct answer/jailbreak patterns, caps hint advancement at rung 3, and asks an answer-blind Socratic question. The focused pure tests for the detection patterns and benign examples passed locally (`11 passed`). The live enhancement prompt receives only public assignment context and a server-selected hint, and `LLMOrchestrator.enhance()` returns deterministic fallback copy if the provider is deterministic, unavailable, malformed, oversized, cooling down, or disallowed. [10] [12]

These controls satisfy an important part of the issue’s safety premise, but only for **dialogue turns**. They do not create an active-section boundary because the product has no section state. A canvas-specific suggestion endpoint should retain this server-side context resolution rather than extending the current browser-posted message contract.

### 5. Event append/replay is useful infrastructure, but it is not a canvas provenance model

`EventStore.log_event()` writes JSON payloads into `session_events`, and `get_session_events()` returns them in chronological/event-ID order. The current dialogue path appends a student prompt before generation and then appends a tutor, hint, or adversarial-defense event. This provides a workable event substrate for reconstructing state. [4] [5]

No existing event type represents: a section becoming active; a saved student draft; source excerpt selected; a suggestion offered; suggestion accepted, edited, or dismissed; a proposed diff; a student revision; or a final per-section snapshot. Searches across the production source and tests found no canvas-section, suggestion-lifecycle, source-selection, accepted-assistance, revision, or diff event implementation. Consequently, `StudentTrace.eventTitle()` and the evidence trace API only recognize the current dialogue-oriented event vocabulary. [3] [11]

The implementation is append-only **at the application-method level**: no update/delete event method or API route was found. The inspected initial migration does not add a database trigger, immutable ledger constraint, content hash chain, or database privilege policy preventing a privileged direct `UPDATE`/`DELETE`. Therefore, cryptographic or database-enforced immutability is **not verified** by the current code; it should not be assumed when making integrity claims. [4] [17]

### 6. The trace and dossier cannot presently distinguish learner text from assistance

`get_student_reasoning_trace()` creates a generic summary from `student_input`, `response_text`, or grade. `StudentTrace` maps event types to generic labels and shows the selected event’s payload. `EvidenceDossierSynthesizer` treats every `student_prompt_submitted` payload as a student attempt, evaluates those strings against rubric hypotheses, and uses the last such message as `final_answer`. [3] [11] [14]

That behavior is coherent for a chat tutor. It is not sufficient for an attributable canvas: the synthesis has no concept of a final student section, suggestion identity, assistance provenance, accepted-versus-rejected state, source reference, or revision lineage. An AI-inserted diff would be indistinguishable from a student message if implemented by merely logging it as a prompt.

## Gap assessment against Issue #40 acceptance criteria

| Issue #40 acceptance criterion | Current status | Ground-truth assessment | Required direction |
|---|---|---|---|
| Assignment specifications declare a section schema and completion guidance. | **Missing** | Neither `QuestionSpec`/`PublicQuestionSpec` nor the JSON assignment schema has section fields. [6] [7] | Add a typed, public `CanvasSectionSpec` and validate it in both relevant assignment artifacts. |
| Workspace persists draft section text and restores it by session. | **Missing** | Only dialogue messages are restored; `userMessage` has no server persistence. [2] | Add server-authoritative section snapshots/revisions keyed to session and section. |
| Tutor requests contain only active public section, assignment context, and server-selected hint—not Answer Vault. | **Partial** | Dialogue is vault-isolated and resolves public assignment context for bound sessions, but there is no active section and the browser sends a whole free-form `student_input`. [5] [10] | Create a canvas-specific request contract; derive assignment/actor/context server-side; transmit active section text only. |
| Suggestions render as diff/cards with Accept, Edit, and Dismiss. | **Missing** | Assistant output is a chat bubble; no suggestion identity, proposal, diff, or actions exist. [2] | Introduce first-class suggestion objects and explicit action commands. |
| Every offered and accepted suggestion is appended to the immutable event trace. | **Missing** | Current events cover prompts, tutor turns, hints, misconceptions, submission, and grade. [3] [4] | Add controlled canvas events and state reconstruction; do not rely on arbitrary client event logging. |
| Trace and educator review distinguish student text from accepted AI assistance. | **Missing** | Trace and dossier categorize by dialogue event only; rubric extraction treats prompts as student attempts. [3] [13] [14] | Project author type and assistance references explicitly in trace, dossier, and review UI. |
| Provider failure leaves canvas usable with deterministic section prompts. | **Partial foundation; missing canvas behavior** | The LLM orchestrator reliably falls back to deterministic dialogue copy, but the canvas and section prompts do not exist. [10] [12] | Make deterministic section prompts the base implementation, not merely an exception path. |

## Pedagogical assessment

The present product has three strong pedagogical properties. First, the welcome state explicitly asks for a provisional claim, evidence, and explanation. Second, course sources remain visible while a learner develops a response. Third, the dialogue engine’s hint ladder prompts distinctions between observation, inference, alternative explanation, and bounded synthesis. These are appropriate moves for developing historical and analytical reasoning. [2] [10]

The problem is that the system asks for CER thinking without giving learners an external representation of CER thinking. A single chat textbox increases the working-memory burden: the student must remember which sentence is evidence, what claim it supports, what alternative they considered, and whether a tutor suggestion was incorporated. The chat chronology preserves conversational history but does not make argument structure inspectable. This makes self-correction harder and converts an intended “reasoning canvas” into a succession of messages.

The issue’s section approach is pedagogically sound when it remains **student-owned and reversible**. A small, explicit set of sections—working claim, source observations, inference/reasoning, alternative explanation, and revision reflection—would make disciplinary moves visible without dictating the conclusion. Completion guidance should describe the purpose of a section rather than supply its content. For example, “record what the source directly states before explaining what you infer” supports epistemic discipline; “add this conclusion” would not.

The most important restraint is that assistance must be a proposal, never silent content. A suggestion card should preserve the pre-action text, proposed patch or prompt, and student choice. “Accept” must be an explicit write; “Edit” must let the learner change the proposal before any write; and “Dismiss” must leave the draft unchanged. A later learner revision must remain possible even after acceptance. The visual representation and educator trace should identify **that assistance was accepted** without recasting the student’s subsequent editable text as fixed AI text.

## Engineering-safety assessment

### Existing strengths to preserve

| Control | Verified implementation | Canvas implication |
|---|---|---|
| Public assignment projection | `_to_public_spec()` strips `vault_token`; student assignment endpoints return `PublicQuestionSpec`. [8] | Canvas schemas must remain in this public projection, while answers, rubric-internal fields, and vault material remain excluded. |
| Server-owned hint rung | Dialogue reads prior event state and ignores client `current_rung`. [4] [5] | A canvas endpoint should similarly derive active assignment, section policy, prompt, and suggestion eligibility on the server. |
| Provider containment | The orchestrator has validation, cooldown, bounded output, prompt-free telemetry, and deterministic fallback. [12] | Keep deterministic suggestion planning available even when no provider is configured. |
| Lifecycle boundary for dialogue | Dialogue rejects non-active sessions. [5] | Canvas writes, suggestion actions, and draft reads must honor the same active/submitted/completed state model. |
| Source identities exist | Syllabus chunk API includes UUIDs and source metadata. [15] | Store source references, not copied citations, in canvas state and events. |

### Safety gaps that must be addressed before claiming student-owned provenance

1. **No authenticated or server-derived actor is present.** `getStudentId()` creates a browser-local random string. Session creation accepts `student_id` from the client. Dialogue and generic event logging also accept client-supplied student IDs. `GET /events/session/{id}`, trace, and dossier routes return session data with no ownership or role check. A person who knows or obtains a session UUID can request records, and a caller can name another student ID in a write request. Current documentation separately acknowledges that identity fields are simple client identifiers rather than authenticated role-bound access control. [2] [5] [9] [11] [18]

2. **The generic event API bypasses the submitted-session write boundary.** `POST /events/log` forwards arbitrary `event_type` and JSON payload directly to `EventStore.log_event()` without checking session existence, owner, assignment consistency, or whether status is active. In contrast, `/dialogue/message` does check session status. This means the assertion tested for dialogue—no further student dialogue after submission—does not apply to generic event writes. A canvas must not expose its authoritative events through this unrestricted route. [5] [9] [19]

3. **Assignment binding is incomplete at API boundaries.** `get_public_assignment()` retrieves a specification by ID without a published-status predicate, and `GET /assignments/{assignment_id}` uses it directly. A session can also be created with an optional, client-supplied assignment ID, while unbound dialogue trusts the request’s prompt and domain. The Svelte route normally lists published assignments, but direct API use is less constrained. A canvas must bind each session to a published, public assignment before accepting draft or suggestion activity. [8] [9]

4. **Versioning and conflict handling do not exist.** Two tabs or devices could not safely edit a future section using the current event API because it exposes no revision number, idempotency key, expected version, or conflict response. A suggestion diff must include the exact base revision it was generated against; accepting it after the student has edited the section must return a conflict, not overwrite newer learner work.

5. **The current UI’s source insertion weakens provenance.** Copying an excerpt into an unstructured message permits content to be altered while still appearing citation-like. Canvas source attachment should record the source chunk ID and optional immutable excerpt/range at selection time, while keeping the student’s explanation distinct.

6. **The dossier’s final-answer heuristic will mis-score a canvas if reused unchanged.** The current final answer is simply the last chat prompt. A future canvas must designate a final draft projection deliberately and must not grade a tutor proposal as student evidence. [14]

## Single highest-leverage first implementation slice

### Proposal: Server-authoritative CER draft canvas with deterministic, attributable section prompts

This slice should be a **vertical contract-and-interaction increment**, not a visual reskin of the chat. It should deliver one default five-section CER canvas: `working_claim`, `source_observations`, `reasoning`, `alternative_explanation`, and `revision_reflection`. Assignment authors may configure the schema, but the initial user interface should support only this clear, finite section model. The co-pilot should offer **deterministic** scoped cards—an empty-required-section prompt, a section-specific question, a neutral outline, or a previously selected source excerpt—rather than introducing free-form LLM-generated edits in the first release.

This is the highest-leverage slice because it creates the missing data model and learner artifact while already exercising every non-negotiable control: public assignment context, active-section scope, persisted student text, source references, explicit learner action, event provenance, trace visibility, lifecycle controls, and provider-independent usability. A later LLM diff capability can use the same schemas and event lifecycle without inventing new provenance semantics under time pressure.

### Proposed scope and contract

| Layer | First-slice behavior | Safety and pedagogy rationale |
|---|---|---|
| Assignment | Add `CanvasSectionSpec` to runtime draft/public models and the assignment JSON schema. Suggested fields: stable `id`, student-facing `label`, `purpose`, `required`, `completion_guidance`, `max_characters`, `order`, and bounded `allowed_suggestion_kinds`; include `canvas_schema_version`. | Makes structure educator-configurable, visible to the student, and safely public. Guidance explains the epistemic move but does not contain an answer. |
| Session/canvas API | Add canvas-specific read and command endpoints. The server resolves the session’s published assignment and trusted actor, reconstructs canvas state, and ignores browser-supplied assignment prompt/domain/vault-related context. | Avoids letting the browser author the learning context or cross-assignment state. |
| Draft persistence | On intentional save/blur and bounded debounce—not each keystroke—append `canvas_section_saved` with `section_id`, monotonic `revision`, full `student_text`, `source_refs`, and `author_type: "student"`. Reconstruct latest state from events. | Supports reload/resume and revision history without turning ordinary keystrokes into surveillance. Full revision snapshots make replay straightforward in the small initial scope. |
| Source selection | Store a source reference object (`chunk_id`, title snapshot, optional selected excerpt/range, and student-attached section) separately from prose. Do not paste citation strings as the authoritative link. | Preserves evidence provenance and lets the student explain, rather than merely quote, the source. |
| Suggestions | A server-issued card has a UUID, section ID, kind, base revision, deterministic text or neutral patch, any source references, and `author_type: "copilot"`. Offer only one unresolved card per active section. | Bounded scope prevents conversational ghostwriting and makes each assistance action attributable. |
| Explicit learner action | **Accept** issues a command with suggestion ID and base revision; **Edit** opens the proposed text/outline in an editable review before acceptance; **Dismiss** records non-use and never changes section text. No card may mutate the draft when rendered. | Makes help reversible and learner-controlled. A stale base revision returns `409 Conflict`, preserving newer student work. |
| Event provenance | Append `canvas_suggestion_offered`; append `canvas_suggestion_accepted` or `canvas_suggestion_dismissed`; for edited acceptance, retain both the original proposal and learner-confirmed applied patch. Record `base_revision`, resulting revision, deterministic/provider metadata, and source refs. | Establishes an auditable assistance chain. Keeping original and applied forms prevents edited acceptance from being misrepresented as verbatim AI text. |
| UI | Make the active section editor the dominant surface. Place the Socratic prompt/card adjacent to it, retain source selection in a rail, and show “student draft” plus “assistance history” separately. Preserve existing dialogue as a secondary help transcript only if it can be scoped to the active section. | Restores the intended cognitive center of gravity: student reasoning, not chat. |
| Trace and review | Project section saves and assistance actions as distinct timeline nodes. Show current final student text, prior versions, source refs, and assistance history. Update dossier extraction to grade the selected final student section projection only, while reporting assistance separately. | Gives the learner and educator a comprehensible record of development without conflating assistance with authored reasoning. |

### Explicit first-slice boundaries

The first slice should **not** attempt autonomous paragraph writing, automatic synthesis into a final essay, LLM grading, unbounded chat editing, or reference-answer retrieval. It should not silently backfill existing dialogue into canvas sections. It should not infer source spans from pasted text. Learners should create or deliberately move their work into the new sections.

Generated edit diffs are deliberately deferred. The initial neutral outline card may contain structure such as “Observation: [what the source directly says]” and “Inference: [what this supports],” but it must be treated as a proposal with the exact same explicit action, revision, and provenance rules. This makes the provider-failure requirement easy to meet: the deterministic planner is the normal path, not a degraded substitute.

### Preconditions and acceptance criteria for the slice

The implementation should be considered complete only when all of the following are demonstrably true.

1. A published public assignment can declare ordered required CER sections and completion guidance, and its student-facing response contains no vault token, reference solution, or answer-bearing internal field.
2. A student can create, edit, reload, and resume each section by session; the restored text and source references exactly match the latest server-authoritative revision.
3. The server, not the browser, derives session actor, published assignment, active section policy, source eligibility, and context sent to any co-pilot provider. The provider receives only active public-section text, public assignment context needed for that section, and a server-selected bounded prompt.
4. Rendering a suggestion does not write to the draft. Accept, edited acceptance, and dismiss each have an explicit command; stale suggestions cannot overwrite a changed draft.
5. Every offered and accepted suggestion is present in chronological replay with stable IDs, base/result revisions, assistance attribution, and deterministic/provider metadata. Recording dismissals is also recommended for a complete learner-choice record.
6. Trace and review render student-authored revisions separately from co-pilot proposals and accepted assistance. Rubric evidence selects a deliberate final student projection rather than the last arbitrary event.
7. A provider outage, validation failure, cooldown, or absent provider leaves save/restore and deterministic section prompts fully usable.
8. Canvas reads and writes reject unauthenticated or mismatched actors, non-active sessions, draft/unpublished assignments, cross-session source IDs, and direct arbitrary event injection. The generic event logger must be narrowed, internalized, or protected before canvas provenance relies on it.
9. Contract tests cover vault non-exposure, actor/role enforcement, published-assignment binding, save/replay fidelity, idempotent writes, stale-revision conflict, submit-time write rejection, no-silent-population behavior, event sequence fidelity, and deterministic failure mode. Browser tests cover reload, Accept/Edit/Dismiss, accessible focus flow, and a visually distinguishable assistance history.

## Recommended sequencing after the first slice

| Priority | Recommendation | Rationale and completion signal |
|---|---|---|
| P0 | Establish trusted actor and session authorization for canvas reads/writes, and prevent generic arbitrary event writes from bypassing lifecycle rules. | Student ownership and attributable assistance are not credible while actor IDs and event payloads are client-asserted. Completion means all canvas and trace endpoints derive actor/role server-side and reject mismatches. |
| P0 | Implement the proposed deterministic CER canvas vertical slice. | It converts the product’s principal learning interaction from chat history into a persistent structured argument with an auditable assistance lifecycle. Completion means all first-slice criteria above pass. |
| P1 | Add server-generated edit diffs only on top of the completed suggestion contract. | Diffs become safe once base revisions, explicit actions, source references, attribution, and display semantics already exist. Completion means no generated patch can apply without an explicit accepted command and stale patches fail safely. |
| P1 | Extend assignment authoring UI with section-schema editing and educator preview. | Assignment-level configurability needs a usable author workflow and a preview that exercises the exact public student contract. Completion means authors can configure, validate, preview, and publish section schemas. |
| P2 | Improve durable-integrity guarantees appropriate to the deployment threat model. | Application append-only behavior is useful but not database-enforced immutability. Completion may include restricted database roles, audit triggers, or hash-linked event verification, depending on operational requirements. |

## Verification notes and limitations

The audit did not alter application code, settings, GitHub records, or database data. `npm run build` completed cleanly for the existing Svelte code. Ruff completed cleanly for the focused backend files. Pure pattern-level dialogue guardrail tests completed with **11 passing assertions**. These checks establish compilation and selected deterministic guardrail behavior; they do not establish the missing canvas behavior.

A local FastAPI service was not listening on port 8000 during the audit, and Docker was not available in this sandbox. Therefore, the current browser/API journey was verified through code paths, test contracts, and successful frontend compilation rather than by creating a live student session. This limitation does not affect the findings that the current models, UI state, API contracts, and event vocabulary lack canvas sections and attributable suggestion lifecycle support.

## References

[1]: https://github.com/darkaengl/fiosra/issues/40 "Issue #40: Guided Evidence Canvas with Attributed Co-Pilot Suggestions"
[2]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudentWorkspace.svelte "Current StudentWorkspace implementation"
[3]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudentTrace.svelte "Current StudentTrace implementation"
[4]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/event_store.py "EventStore implementation"
[5]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_router.py "Dialogue API router"
[6]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/data/schemas/assignment_spec.schema.json "Assignment specification JSON schema"
[7]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/schemas.py "Assignment designer runtime schemas"
[8]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/generator.py "Assignment generation and public projection"
[9]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/events_router.py "Event API router"
[10]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_engine.py "Socratic dialogue engine"
[11]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/router.py "Evidence and trace API router"
[12]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/llm/orchestrator.py "LLM orchestration and deterministic fallback"
[13]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudioReview.svelte "Educator review UI"
[14]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/synthesizer.py "Evidence dossier synthesizer"
[15]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/schemas.py "Course resource response schemas"
[16]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/ui-ux/student-experience/README.md "Student experience specification"
[17]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/migrations/001_initial_schema.sql "Initial PostgreSQL schema migration"
[18]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/docs/end-to-end-refinement-report.md "End-to-end refinement report"
[19]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_student_workflow_contract.py "Student workflow contract tests"
