# Teacher and Student Tutor Journey Evaluation

**Audit subject:** GitHub issue #44, *Multi-Provider Tutor Journey Acceptance Harness*  
**Repository state reviewed:** `feat/end-to-end-learning-workflow` at `59036e5d6fc97b42a9a23aa80736d5c6009bae8e`  
**Author:** Manus AI  
**Date:** 10 September 2026

## Executive conclusion

The branch implements a credible **workflow skeleton** for the intended journey: an educator can create a course and module, attach a source, generate a grounded scaffold, publish an assignment, open a student workspace, record turns, submit a trace, and display an educator review queue. The selected deterministic safety and provider-validation checks passed, and the Svelte source builds successfully. The code therefore supports a useful **development demonstration** of the journey.

It is **not yet safe to treat as an end-to-end learning product or as satisfying issue #44**. The application has no authentication or authorization boundary. Consequently, a caller can impersonate a learner, append arbitrary events to another learner’s trace, submit work, retrieve traces and dossiers, or finalize a grade. In addition, the dossier route does not load the assignment’s rubric and the synthesizer uses fixed history-oriented criteria and several constant metrics. This makes the review evidence and suggested grade pedagogically unreliable for the actual assignment. The student entry and diagnostic surfaces also contain hard-coded sample learners and outcomes that are not connected to live course data.

> **Release position:** Do not enable real learner activity, educator grade decisions, or any live provider until the P0 controls and the sealed acceptance harness below are implemented and pass. The answer-blind architecture is a good direction, but answer isolation alone does not establish identity, record integrity, truthful analytics, or valid assessment.

## Scope, method, and confidence

This audit covers exactly the teacher-to-student tutor journey requested in issue #44: teacher setup, course grounding, assignment design, student interaction, trace submission, and educator review. It evaluates both engineering safety and pedagogical quality against the **current code**, rather than against the UI vision documents.

| Activity | Result | Confidence and limitation |
|---|---|---|
| Static inspection of FastAPI routes, services, persistence schema, Svelte routes, and the existing test suite | Completed at the revision above | **Verified code behavior** where a route/function is cited. Static inspection cannot prove a browser interaction or a provider response. |
| Selected read-only deterministic test execution | `25 passed in 4.87s` | **Executed verification.** The command covered LLM orchestration, ambiguity classification, adversarial-pattern detection, benign prompt classification, and the deterministic text-claim verifier. It deliberately excluded database-writing integration tests to honor the instruction not to change database data. |
| Svelte production build to an isolated job directory | Passed; 152 modules transformed | **Executed verification** that `frontend/src` compiles. Output was directed to `/home/ubuntu/jobs/job_3KIgWCaR_a4/frontend-build`, not the repository’s served build directory. |
| Optional local Ollama check | Not available; `127.0.0.1:11434` refused the connection | No live model was invoked. Issue #44’s optional local-Ollama smoke case remains unverified in this environment. |
| Browser/API database journey execution | Not run in this audit | The existing API integration tests create durable course, assignment, session, and event rows. Docker is not installed in this sandbox, so an isolated database service could not be provisioned without changing data. Existing tests and historical verification notes were reviewed as codebase evidence, but were not re-run. |

The focused test command was:

```bash
.venv/bin/pytest -q \
  tests/test_llm_orchestration.py \
  tests/test_assignment_designer.py::test_ambiguity_evaluator_triggers_interview \
  tests/test_assignment_designer.py::test_ambiguity_evaluator_accepts_precise_prompt \
  tests/test_dialogue_guardrails.py::test_jailbreak_prompts_detected \
  tests/test_dialogue_guardrails.py::test_benign_pedagogical_prompts_not_flagged \
  tests/test_evidence_dossier.py::test_text_claim_verifier_entailment \
  tests/test_evidence_dossier.py::test_text_claim_verifier_contradiction \
  tests/test_evidence_dossier.py::test_text_claim_verifier_neutral \
  tests/test_evidence_dossier.py::test_text_claim_verifier_latency_sla
```

The passing result is meaningful but narrow. It does **not** verify a complete course fixture, browser state, database isolation, source-to-citation fidelity, authorization, grade lifecycle, or a live provider. This distinction is material because issue #44 explicitly requests a repeatable sealed evaluation harness rather than only unit-level contracts.[1]

## Current journey: verified behavior and observed friction

### 1. Teacher setup and course grounding

**Verified behavior.** The backend can create courses and sequential modules, ingest pasted text, uploaded PDF/text/Markdown content, and educator-supplied external-link summaries into `syllabus_chunks`. The source parser extracts text, chunks it, assigns a deterministic embedding, attempts a knowledge-component (KC) match, and stores title, excerpt content, resource type, URL, and optional KC ID. The Svelte course and module views provide course creation, module creation, source attachment, setup-readiness indicators, and source deletion with an API dependency check.[2] [3] [4]

For a module-bound assignment, publication is blocked if the stored spec is not `course_grounded` or has no recorded grounding source. The public assignment projection removes `vault_token`, and a published source cannot be deleted while a published assignment’s stored provenance cites it. The existing grounded-workflow test directly asserts these behaviors, including a student public projection that has no vault token.[5] [6]

**Usability friction.** The course-portfolio action labelled “Ground course materials” only presents instructions and sends the educator to the module screen. The educator must infer the required ordering—course, module, source, assignment—from several pages. The module card visibly reports whether objectives, sources, and a student task exist, which helps, but neither server validation nor UI readiness requires learning objectives, a successful KC mapping, source adequacy, or a source-to-outcome rationale. The resource form allows an external URL but asks the educator to supply the summary/excerpt; it does not retrieve, verify, or snapshot the linked material. This can produce a provenance record without reliable source content.[3] [4]

**Pedagogical and engineering risk.** `AssignmentGenerator._load_grounding_sources()` selects the first five chunks by `created_at`, rather than chunks relevant to the teacher’s prompt or a teacher-approved selection. `SyllabusParser.match_kc_for_text()` is a keyword heuristic with a French-Revolution fallback catalogue. A source can therefore be labelled as grounded although its KC mapping is absent, weak, or irrelevant. The frontend accurately displays “KC mapping pending” in that case, but publication still accepts a source with no KC. Grounding currently means **stored provenance exists**, not that the learning task is demonstrably aligned to appropriate evidence and objectives.[2] [7]

### 2. Assignment design

**Verified behavior.** The designer implements an ambiguity interview, produces a five-entry ladder (rungs 0–3 plus locked rung 4), creates three rubric rules, and persists the draft. A precise public student representation can be fetched through `GET /assignments/{id}` with the vault token removed. A server-side publication check confirms that the public projection returns `published`. The generator treats the selected course material as public context and records provider/model/latency/token/fallback metadata without retaining the raw provider prompts.[5] [8]

**Verified safety control.** The default provider is deterministic. `LLMOrchestrator.enhance()` returns caller-chosen deterministic text without attempting a network call in that mode. The executed tests also verify pseudonymous provider `user` metadata, rejected empty/overlong/prohibited outputs, deterministic fallback after a provider error or cooldown, and the specific regression guard against a mocked Ollama worked-answer style output.[8] [9]

**Usability friction.** The educator is shown a generated task, target KCs, hint ladder, rubric, and source excerpts, but there is no editing, approval, versioning, or comparison step for the generated ladder and rubric. More importantly, the UI never sends `reference_solution` when it drafts an assignment. `draft_question()` therefore silently creates a generic default answer-vault payload rather than a teacher-authored reference solution. The educator has no displayed ability to select or approve misconception traps; distractors are returned in the scaffold response but are neither shown in the designer nor persisted in `QuestionSpec`.[5] [10]

**Pedagogical risk.** In the “not ambiguous” UI path, `AssignmentDesigner.svelte` pre-populates the clarification answers with French-Revolution-specific wording, including fiscal pressures and primary evidence. This is an explicit cross-domain contamination path for an otherwise precise task in any subject. The scope de-ambiguator itself uses only word count plus generic contextual and causal anchors; it does not assess whether the requested task is coherent with the selected course or grade level. These weaknesses make the design assistance appear more pedagogically authoritative than its actual basis.[4] [11]

**Live-provider risk.** The response validator checks certain prohibited phrases and forms, but it is lexical rather than semantic. A provider can return a leading imperative and still embed a task-specific answer in the rest of the text. Similarly, a question-mark ending is insufficient to prove that a tutor question does not reveal a thesis or evidence conclusion. The issue description specifically reports an answer-like authoring output from local Ollama; the current mocked regression is useful but not a sufficient response-quality gate for arbitrary model variants.[1] [8] [9]

### 3. Student tutor interaction and source use

**Verified behavior.** `StudentWorkspace.svelte` fetches an assignment, creates or resumes a browser-local session, replays recorded dialogue, sends each new turn to `/dialogue/message`, and displays server-reported hint progression. The server obtains the authoritative assignment from the session when one exists; it refuses a request whose supplied assignment ID does not match that session and ignores a stale client question prompt in favor of the stored public assignment prompt. It reads the maximum stored hint rung, advances a requested hint one rung only, caps at 3, and resets the engine’s context to rung 0 for an adversarial attempt. The response and the preceding student input are recorded in the event stream.[5] [12] [13]

The selected tests confirmed deterministic detection of ten listed jailbreak/answer-seeking phrasings and confirmed that five listed legitimate history questions are not flagged. Existing integration tests additionally assert monotonically increasing server-controlled hint rungs and a bottom-out ceiling. These are positive engineering controls, although only the pure pattern checks were freshly run in this audit.[14] [15]

**Usability friction.** The workspace asks students to use source evidence, but the evidence rail loads the first five **course-wide** chunks through `GET /courses/{course_id}/syllabus`; it does not use the published assignment’s `grounding_sources`, does not filter to the selected module, and does not rank by assignment relevance. Clicking “Add as a citation” simply pastes a truncated source excerpt into the chat text. It neither creates a structured citation event nor records the chunk ID, location, or a student explanation of the source’s relevance. The tutor receives the public assignment prompt and one selected hint, not the cited source passages. These design choices undermine the claim that the subsequent trace can demonstrate source-grounded reasoning.[2] [12]

**Pedagogical risk.** A course-grounded assignment with an assignment hint ladder suppresses the taxonomy search completely: `traps = []` in `SocraticDialogueEngine.generate_response()`. This avoids unrelated domain traps, which is desirable, but it also means a grounded learner will not receive detected misconception-specific remediation or generate a `misconception_flagged` event through this path. The promise of educator-approved misconception diagnosis is not implemented. The generic ladder is constructive, but it is reused across subjects and does not adapt to the teacher’s intended misconception or the learner’s evidence use.[10] [13]

**Safety risk.** Student identity comes from an unverified `localStorage` value generated on the client. The dialogue request accepts `student_id` from that client and records it without checking it against the session’s student. There is no authentication or route-level authorization in the inspected backend or frontend. This permits client-side identity spoofing and makes a learner’s trace and privacy boundaries non-authoritative.[12] [13] [16]

### 4. Trace submission and record integrity

**Verified behavior.** The intended path exposes a chronological trace, displays per-event titles, lets an active learner submit, adds a `student_submitted_for_review` event, and moves the session from `active` to `submitted`. The dialogue route rejects further dialogue once the session is not active. The existing student contract test asserts this dialogue block after submission. Events are queried by `(created_at, event_id)`, which gives stable replay ordering for events that have the same timestamp.[12] [17]

**Usability friction.** The trace UI opens an evidence dossier and exposes a suggested score before submission. Formative feedback can be appropriate, but the product does not explain the scoring limitations or distinguish private formative guidance from the grade recommendation shown to the educator. The API permits submission of a zero-event active session; only the UI disables its submission button when the loaded trace is empty. The trace view includes a direct “Open review queue” route even in the student context, which further blurs roles.[16] [17]

**Engineering risk.** “Append-only” is a convention, not an enforced trust boundary. `POST /events/log` accepts an arbitrary session ID, student ID, assignment ID, question ID, event type, and JSON payload. `EventStore.log_event()` inserts the event and refreshes the session marker without confirming that the session exists, belongs to the student, matches the assignment, or is still active. The generic logging endpoint can therefore add fabricated or post-submission events, including events that influence a dossier. A database `INSERT` restriction, authorization, signed server events, and lifecycle validation are required before the trace can serve as assessment evidence.[17] [18]

### 5. Educator review and cohort diagnosis

**Verified behavior.** The review queue selects sessions whose status is `submitted`, optionally filters them by a course, synthesizes a dossier, and exposes finalization. The review UI displays criterion-level evidence, a suggested grade, a teacher-entered grade and feedback field, then calls the finalization endpoint. The endpoint records a grade event and completes the session. Existing tests cover the queue’s empty filtered response and verify that finalization adds an event and marks the session completed.[6] [16] [19]

**Pedagogical risk: dossier assignment mismatch.** The evidence routes call `synthesize_dossier()` without passing the assignment’s `rubric_criteria`. As a result, every dossier defaults to two fixed French-history rubrics, regardless of the published task’s three teacher-facing rules, course domain, sources, or KCs. `final_answer_correct` is also set to true whenever there is at least one attempt and no adversarial event; it does not evaluate the answer. This is a release-blocking validity defect because the UI presents the resulting `suggested_grade`, autonomy rating, and criterion evidence as if they were assignment-specific.[19]

**Pedagogical risk: invented metrics.** The synthesizer returns fixed values for `overall_mastery_delta` (`+18% KC Confidence`), `average_time_per_question_seconds` (`95.0`), `engagement_score` (`0.88`), and marks all triggered misconceptions as resolved. The cohort service returns a hard-coded sample roster when no live sessions exist. `CohortDiagnostics.svelte`, `StudentHome.svelte`, and `StudentPortal.svelte` also embed fictional students, courses, scores, and actions that are not wired to the API. These displays risk falsely representing demonstrations as learner analytics.[19] [20] [21]

**Safety risk: grade authority is not enforced.** `POST /evidence/dossier/{session_id}/finalise-grade` has no identity or educator-role check; `teacher_id` is client supplied. It can finalize an **active** session directly because it only rejects an already completed session, not a non-submitted one. The `approved_grade` field accepts any non-empty string. These facts, combined with unrestricted dossier and trace reads, mean no trustworthy distinction exists between learner, educator, or unauthorized caller.[16] [19]

## Risk register

The following prioritization separates verified implementation facts from the product consequence they create. “Risk” is an assessment based on the cited code, not a claim that exploitation or pedagogical harm occurred during this audit.

| Priority | Verified condition | Engineering safety consequence | Pedagogical consequence |
|---|---|---|---|
| **P0 — release blocker** | No authentication/authorization middleware or role checks; identifiers are client supplied. Grade finalization, dossier retrieval, trace retrieval, session creation, and event logging are publicly reachable. | Any caller can impersonate actors, inspect sensitive work, alter evidence, submit sessions, and finalize grades. FERPA-/privacy-like controls cannot be asserted. | The “sovereign educator” decision is not sovereign. Learners can be misattributed or assessed on forged traces. |
| **P0 — release blocker** | `POST /events/log` and `EventStore.log_event()` accept arbitrary event data and do not enforce identity, session ownership, assignment linkage, or active status. | The evidence record is mutable by unauthorized insertion despite being described as append-only. | Trace-based assessment and autonomy measures are not valid evidence of a learner’s process. |
| **P0 — release blocker** | Evidence dossier routes omit assignment rubric retrieval; `synthesize_dossier()` uses defaults and treats a non-adversarial attempt as correct. | Grade recommendations are based on unrelated rules and simplistic lexical matching. | Educator review can be anchored to incorrect criteria, invalid confidence, false mastery change, and fabricated engagement metrics. |
| **P0 — release blocker** | `get_public_assignment()` returns a draft as well as a published assignment; session creation does not validate the assignment’s existence, publication state, or question. | Direct URLs can bypass the intended published-only student discovery path. | Students can work from an unapproved or incomplete task, and their work may enter a trace. |
| **P1 — high** | Grounding selects early chunks, permits unmapped sources, and the workspace shows course-wide sources rather than assignment-selected sources. | Provenance is incomplete and weakly tied to what the learner saw. | “Grounded” tutor support and citation evidence can be irrelevant to the task; teachers cannot reliably interpret source use. |
| **P1 — high** | The provider output gate is form/phrase based; source relevance and semantic answer leakage are not validated. Local Ollama is not available for a fresh smoke test. | A model variant can return answer-like or irrelevant content while passing superficial guards. | Learner agency and the stated answer-blind tutoring policy can be compromised. |
| **P1 — high** | The Answer Vault is a process-local dictionary; it stores the solution in memory, accepts arbitrary `teacher_id` in its method, and persists an opaque vault token in the draft spec. | Solutions are lost on restart and educator access is not authorization-backed. The token is not encryption. | Reliable teacher review against an approved answer standard is unavailable across restarts. |
| **P1 — high** | Grounded assignments suppress misconception taxonomy matching; traps are neither teacher-approved in UI nor persisted in the assignment spec. | Expected diagnostic signals are absent or generic. | The product cannot substantiate targeted misconception remediation or cohort intervention claims. |
| **P2 — medium** | Static Student Home, Student Portal, and Cohort Diagnostics present fabricated people, grades, and interventions; the roster has fallback demo learners. | Users can confuse demonstrative content with live data. | Students and teachers can be misled about progress, equity signals, and intervention status. |
| **P2 — medium** | No browser test framework/scripts are present, and current integration tests use a real configured database with no sealed fixture teardown. | Regression coverage is vulnerable to shared data, order dependence, and UI/API drift. | Important learning-quality behavior is not repeatably evaluated across teacher and learner surfaces. |

## What the existing tests do and do not establish

The repository already contains valuable API-oriented coverage. `test_grounded_teacher_workflow.py` validates source grounding, publication blocking, public assignment projection, protected source deletion, and stale client prompt resistance. `test_hint_ceiling.py` validates the server-controlled ladder. `test_dialogue_guardrails.py` validates its enumerated regular-expression defences. `test_llm_orchestration.py` validates mock-provider metadata and deterministic fallback. `test_evidence_dossier.py` verifies that event IDs appear in quoted evidence and that finalization changes session status.[6] [9] [14] [15] [19]

These tests do **not** constitute issue #44’s requested acceptance harness. They do not create one sealed representative course fixture with teacher-approved KCs/misconceptions and expected tutor moves. They have no browser runner. They do not test malicious identity/event/grade requests, draft assignment access, post-submission generic event writes, rubric-to-dossier consistency, source citation attribution, dynamic student discovery, semantic answer leakage, overly long/malformed provider outputs at the route journey level, or an opt-in real Ollama suite. The issue’s requested separation between pedagogical-quality observations and automated security/contract assertions is also not represented in machine-readable test reporting.[1]

## Recommendations and acceptance tests for the improved journey

### P0. Establish an authenticated, role-authorized, sealed journey boundary

Implement server-derived learner and educator identity. Define at least learner, assigned educator, course editor, and privileged operational roles. Every route must authorize both role and resource relationship. Remove `student_id`, `teacher_id`, and authoritatively selected assignment identity from client authority wherever a session or authenticated context already supplies them. Restrict trace/dossier reads to the learner, assigned educators, and explicitly authorized reviewers.

**Acceptance tests**

1. A learner token for Student A cannot read, submit, append to, or dialogue in Student B’s session; every attempt returns `403` or a deliberately non-enumerating `404`.
2. A learner cannot call grade finalization. An educator assigned to a different course cannot read the dossier or finalise it. The assigned educator can finalize only a submitted session.
3. The server records the authenticated principal as the event author and ignores/rejects conflicting body identifiers.
4. Grade input follows an approved grade schema or institution-defined score range. Attempts to finalize `active` or `completed` sessions return `409`.
5. Authorization tests run against the complete browser/API journey and retain no real learner identifiers in snapshots, logs, or provider metadata.

### P0. Make the evidence record and assessment basis trustworthy

Replace the unrestricted generic event write with narrow, server-owned event commands or a validated event allowlist. Enforce session lifecycle, assignment/question linkage, actor ownership, and event schema. Load the persisted public assignment specification for every dossier, pass its rubric criteria explicitly to the evaluator, and label any non-validated metric as unavailable rather than fabricating a number. Treat pre-score as decision support only, with visible limitations and a requirement for teacher review.

**Acceptance tests**

1. The harness creates a session for one published fixture assignment, then attempts mismatched student ID, assignment ID, question ID, unknown event type, and post-submission generic writes. All fail and event count/order remain unchanged.
2. The dossier for a history fixture and a non-history fixture each uses the stored assignment rubric IDs and labels, never the hard-coded French-history defaults.
3. A one-attempt irrelevant response is not represented as `final_answer_correct=True`, mastery gain, resolved misconception, or a high-confidence grade recommendation.
4. `time_spent`, engagement, and mastery fields are either computed from timestamps/defined formulas or returned as `null`/“not assessed”; no constants are displayed as learner measurements.
5. A teacher can see exact event-linked evidence and the source/rubric provenance that supports every automated judgment. Finalization preserves the original event stream and creates one signed educator decision event.

### P0. Create the sealed deterministic acceptance harness required by issue #44

Create a dedicated fixture and test suite that runs against an isolated database per run or rolls back all changes. The fixture should include a course, module, selected source snippets, valid KCs, teacher-approved misconception targets, a teacher-authored rubric/reference solution retained in a secure server-side store, a published assignment, and a table of expected safe tutor moves. The default suite must use deterministic mode and must not require network access.

**Acceptance tests**

1. One browser/API test follows the entire successful path: educator setup → source grounding → teacher review/edit/approval → publish → learner discovery/start → source-attributed attempt → bounded hints → trace review/submit → authorized educator review/finalize.
2. The test asserts the student sees only a published public projection and cannot obtain a vault token, reference solution, private evaluation prompt, or another learner’s information.
3. The final review asserts that every displayed rubric and source citation comes from that exact fixture assignment; teacher-approved misconception handling is exercised and visible.
4. The harness is repeatable from an empty isolated store, cleans up automatically, and produces a structured report separating contract/security assertions from qualitative pedagogical observations.
5. The test is executable through a documented single command in continuous integration and does not depend on shared local database contents.

### P1. Make source grounding assignment-specific and learner-meaningful

Require an educator to select approved source chunks and state their relationship to objectives and rubric criteria. Preserve immutable source version/digest information. In the workspace, show only the assignment-selected materials by default. Replace “paste excerpt into chat” with a structured citation action that records source chunk ID, quoted span/location, and learner explanation; make that structure visible to the tutor and dossier.

**Acceptance tests**

1. A course with relevant and irrelevant sources yields a task whose approved source list is the educator-selected/retrieved relevant set, not simply the first five rows.
2. The learner workspace displays only the selected assignment sources and can add a citation event that contains chunk ID, quote/span, and learner rationale.
3. The dossier maps each criterion’s evidence to both an event ID and source provenance. An unrelated source cannot be presented as support for the selected assignment.
4. An unmapped or inadequately described source produces an explicit readiness warning and prevents publication when the course policy requires KC/objective alignment.

### P1. Strengthen multi-provider response quality and optional Ollama coverage

Keep deterministic text as the final authority. Add semantic, fixture-based validation for authoring and tutor outputs: response relevance to the selected source/task, absence of task-specific answer content, no invented evidence, question/probe form for tutor turns, and bounded length. Record only approved operational metadata. Run Ollama only through an explicit opt-in marker and a compact declared local model; skip cleanly if the service/model is unavailable.

**Acceptance tests**

1. Deterministic mode proves no provider endpoint is called and produces a stable transcript snapshot for the fixture journey.
2. Mock and live-optional suites cover timeout, malformed output, empty output, overly long output, irrelevant context, answer-key request, answer-like authoring output, and a question-form answer leak. Each returns the deterministic fallback with an appropriate non-secret reason.
3. A provider transcript is rejected if it introduces a fact/source absent from the selected public assignment context, even if it ends in a question mark or begins with an imperative.
4. When `FIOSRA_LLM_PROVIDER=ollama` and the requested local model is installed, the opt-in test records provider, resolved model, latency, and token counts if supplied; it records no raw prompt, secret, vault token, reference solution, student identifier, or full trace. If Ollama is unavailable, the test is reported as skipped—not silently passed.
5. A pedagogical review rubric evaluates a fixed sample of accepted tutor moves for cognitive demand, source relevance, calibration, respectful deflection, and absence of answer substitution. That qualitative judgment is reported separately from the security assertions.

### P2. Remove or unmistakably isolate demonstration data and complete journey usability

Replace static student pages and the static diagnostic heatmap with live, authorized data, or mark each as an explicit non-production mock inaccessible from the learning workflow. Provide a course-aware learner assignment list and clear state transitions. Provide educator controls to review/edit scaffold, rubric, source list, and misconception targets before publication. Implement real dispatch/export actions only when their privacy, consent, and audit behavior are defined.

**Acceptance tests**

1. A new learner sees only their enrolled, published assignments and correct resume state; no named static persona or fabricated metric appears in a production route.
2. The readiness UI blocks or clearly explains missing objectives, selected sources, approved misconception targets, rubric approval, and publication state.
3. Cohort metrics come only from authorized course sessions. With no sessions, the roster is empty with an explanatory state, not populated with sample learners.
4. Every visible primary action performs the labelled server operation or is absent/explicitly disabled with an accessible explanation.

## Recommended first delivery slice

The first implementation slice should be a **deterministic, isolated API acceptance fixture plus authorization and dossier-rubric wiring**. It is deliberately smaller than a full browser/live-provider rollout, but it removes the most consequential false trust: untrusted actor identity and ungrounded assessment. The slice should create one representative course/module/source/assignment fixture, require authenticated learner and educator principals, enforce session ownership/status transitions, pass the assignment’s stored rubric into dossier synthesis, and prove the outcome with security-negative and successful-path tests. Only after this slice passes should browser automation, source-span citation, and opt-in Ollama smoke tests be added.

## References

[1]: https://github.com/darkaengl/fiosra/issues/44 "Issue #44: Multi-Provider Tutor Journey Acceptance Harness"
[2]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/router.py "Course, module, resource, grounding, and roster routes"
[3]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/ingestion.py "Syllabus source ingestion, KC matching, retrieval, and dependency implementation"
[4]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/Courses.svelte "Educator course portfolio and grounding guidance UI"
[5]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/generator.py "Assignment generation, public projection, and publication implementation"
[6]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_grounded_teacher_workflow.py "Grounded teacher workflow API contract tests"
[7]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/lib/ModuleCard.svelte "Module readiness and source provenance UI"
[8]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/llm/orchestrator.py "Deterministic fallback and live-provider output guard implementation"
[9]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_llm_orchestration.py "LLM orchestration and mocked provider safety tests"
[10]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/distractor_engine.py "Misconception distractor retrieval implementation"
[11]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/AssignmentDesigner.svelte "Educator assignment designer UI"
[12]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudentWorkspace.svelte "Student reasoning workspace UI"
[13]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_router.py "Authoritative assignment context and dialogue event route"
[14]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_dialogue_guardrails.py "Dialogue jailbreak and answer-seeking guardrail tests"
[15]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_hint_ceiling.py "Server-controlled hint progression tests"
[16]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudioReview.svelte "Educator review queue and finalization UI"
[17]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/events_router.py "Student session, generic event, submission, and replay routes"
[18]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/event_store.py "Learning event persistence and session lifecycle implementation"
[19]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/synthesizer.py "Evidence dossier scoring and metrics implementation"
[20]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/StudentPortal.svelte "Static student portal demonstration UI"
[21]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/CohortDiagnostics.svelte "Static cohort diagnostics demonstration UI"
