# Misconception Lifecycle and Validation Audit

**Issue:** [#42 — Misconception Authoring, Validation, and Tutor Effectiveness][1]  
**Repository state audited:** `feat/end-to-end-learning-workflow` at `59036e5d6fc97b42a9a23aa80736d5c6009bae8e`  
**Audited:** 2026-09-10  
**Author:** Manus AI

## Executive conclusion

The current implementation is a **static, seed-backed misconception catalogue**, not an educator-governed misconception lifecycle. A developer-maintained JSON record is loaded into PostgreSQL, deterministically vectorized, and immediately eligible for retrieval. There is no candidate state, provenance evidence, validation gate, human review, version history, publication control, retirement control, or effectiveness measurement for misconception records. The record's only runtime status is its presence in the table.

The seed cards show promising instructional design: they usually name a plausible flawed rule, give a triggering context and learner-language example, and provide a graduated remediation ladder. However, their instructional authority is not demonstrated in the code or source data. Several later-rung hints disclose correct operations or claims; seed provenance is a category label rather than a citable evidence trail; frequency values lack cohort/time definitions; and source/card quality is not subject to any enforceable review.

The most urgent engineering safety issue is diagnosis precision. The live generic-dialogue path selects the top same-domain result when cosine similarity is merely greater than `0.01`. The vectors are generated from independent SHA-256 hashes of the complete text rather than a semantic embedding model. A reproducible, source-equivalent read-only check found unrelated and nonsensical inputs above that gate in history, algebra, and language. The current system can therefore attach a taxonomy label to unrelated student language. Course-grounded assignment turns avoid that particular failure by suppressing taxonomy retrieval whenever a hint ladder is present, rather than by safely selecting a published, assignment/KC-constrained record. This makes the desired course-grounded diagnostic behavior unavailable in the principal grounded path.

> **Audit judgment:** Do not use present retrieval output for high-stakes learner profiling, mastery penalties, automated intervention measurement, or catalogue growth. Treat it as a prototype authoring aid until publication controls, context-bounded validation, educator review, and calibrated evaluation are implemented.

## Scope, method, and evidence boundaries

This audit covers exactly the misconception lifecycle: stored representation, seed creation and ingestion, vector search, dialogue matching, assignment/distractor use, event/effectiveness handling, source data, and related tests. “**Verified**” means directly observed in the checked-out source or reproduced by a read-only local check. “**Proposal**” identifies a recommended future design, not behavior that exists today.

The audit used source inspection; static seed-card and JSON Schema validation; source-equivalent deterministic-vector calculations; `pytest --collect-only` (67 tests collected); and focused tests that do not write database data. The following focused suites passed: `tests/test_dialogue_guardrails.py::test_jailbreak_prompts_detected`, `tests/test_dialogue_guardrails.py::test_benign_pedagogical_prompts_not_flagged` (**11 passed**), plus `tests/test_hint_ceiling.py` and `tests/test_llm_orchestration.py` (**11 passed**). Database-backed integration tests were deliberately not run because the task prohibits changing database data. No production code, settings, database data, or GitHub records were changed.

## Verified current lifecycle

### What creates a misconception today

A misconception is created today by adding an object to one of two committed seed files: `fiosra/knowledge/seeds/misconceptions_language_history.seed.json` or `fiosra/knowledge/seeds/misconceptions_algebra_geometry.seed.json`. `seed_postgres_misconceptions()` reads those exact files, combines their arrays, and upserts every item into PostgreSQL. The loader maps `knowledge_component` to `kc_id`, `label` to `name`, derives `flawed_rule` from `flawed_rule`, `remediation_strategy`, or `description`, joins hint-rung text into one field, and overwrites any existing row with the same ID. It builds the index text from label, description, and derived flawed rule, then generates a vector locally. [2]

There is no application endpoint, database table, background workflow, or test that creates a candidate misconception from course material or student patterns. No executable code loads `misconception.schema.json` or validates the seed records before hydration. The design reference describes a future “Generate → Retrieve → Rerank” pipeline and an HDBSCAN-assisted novel-error review queue, but that is reference documentation rather than runtime behavior. [3]

The complete verified path is summarized below.

| Lifecycle stage | Current behavior | Exact implementation | Audit classification |
|---|---|---|---|
| Authoring | A developer manually edits committed JSON seed objects. | `knowledge/seeds/misconceptions_*.seed.json` | **Verified** |
| Record validation | JSON is parsed; no schema, provenance, duplicate, KC, remediation, or factual validation is invoked. | `seed_pipeline.seed_postgres_misconceptions()` [2] | **Verified gap** |
| Persistence | Six descriptive fields plus an embedding are stored in `misconceptions`; an ID conflict overwrites the old values. | `migrations/001_initial_schema.sql`, lines 29–43; `seed_pipeline.py`, lines 77–133 [2] [4] | **Verified** |
| Publication | A row is usable as soon as it exists. There is no `status`, author, reviewer, version, effective date, or retirement field. | Same migration and retrieval SQL [2] [4] | **Verified gap** |
| Retrieval | Query text is deterministically hashed into a 1,536-element vector; pgvector returns nearest rows, optional same-domain only. | `generate_deterministic_embedding()` and `search_nearest_misconceptions()` [2] | **Verified** |
| Tutor use | Generic turns call retrieval for one result and accept it when similarity is `> 0.01`; grounded turns with a ladder suppress retrieval. | `SocraticDialogueEngine.generate_response()` [5] | **Verified** |
| Assignment use | Planning can retrieve same-domain, target-KC table rows as “distractor traps,” but these traps do not persist in `QuestionSpec`. | `DistractorEngine.get_distractors_for_kcs()`; `AssignmentGenerator.generate_scaffolding_plan()` and `draft_question()` [6] [7] | **Verified** |
| Observation | A dialogue match is written to the response event and a second `misconception_flagged` event. | `dialogue_router.handle_dialogue_turn()` [8] | **Verified** |
| Effectiveness | Dossier logic counts some hint-associated IDs but does not establish a valid resolution or causal intervention effect. | `EvidenceDossierSynthesizer.synthesize_dossier()` [9] | **Verified gap** |

### Stored model and data loss

The database table contains only `misconception_id`, one string `kc_id`, `domain`, `name`, `flawed_rule`, `remediation_hint`, and `embedding`; only the identifier is a key. `kc_id` has no foreign key to a KC table. [4] During hydration, the richer seed-card fields are not persisted: related KCs, learner error example, correct-response example, trigger, remediation strategy, severity, frequency percentile, and source category are discarded. [2]

This loss makes the stored runtime record insufficient for issue #42’s required provenance, learner-language examples, target-KC plurality, reviewer, status, and version. It also makes later review difficult because an educator looking at a stored match cannot reconstruct the particular evidence, card version, or validation decision behind it.

The seed files currently contain **25 records**: 4 algebra, 1 geometry, 5 language, and 15 history. They cover 21 primary KCs. The curriculum graph seed includes history and language KCs, but it does not include the five primary algebra/geometry KCs nor their related KCs. Because the misconception schema stores KC IDs as free strings, all of those records can still be loaded into PostgreSQL without referential validation. [2] [10]

### Source data quality and schema conformance

The source cards are materially richer than the database. The algebra/geometry file illustrates a strong card pattern: label, description, trigger, concrete erroneous response, correct response, remediation strategy, rungs, severity, frequency, and source category. [11] The language/history file follows the same pattern for argument, evidence, historical causation, and French Revolution examples. [12] This is a useful starting format for instructional authoring, but it is not a verified evidence base.

A read-only validation of all 25 seed objects against the repository’s own `misconception.schema.json` found **20 invalid records**. All 20 language/history IDs fail the schema pattern `^MISC_[0-9]{4}` because their IDs use `MISC_LANG_*` or `MISC_HIST_*`. Nine records use `severity: "moderate"`, which is absent from the schema’s severity enum. Ten history records use `source: "curriculum"`, which is absent from the schema’s source enum. The schema is not invoked by the seed pipeline, so these defects do not prevent loading. [2] [13]

The check also found that the five algebra/geometry records omit `flawed_rule`. This does not violate the current schema because the field is optional, and the pipeline silently substitutes `remediation_strategy` as the stored flawed rule. That substitution mixes two different concepts: the learner’s erroneous rule and the educator’s proposed intervention. The geometry record `MISC_0305` is also the only card with three rather than four remediation rungs. [2] [11] [13]

The seed category `source` is not traceable provenance. The values are currently `literature` (15 records) and `curriculum` (10 records), with no author, title, edition, page/section, URL, course/module source, evidence excerpt, review date, or license. Likewise, `frequency_percentile` is a hard-coded number with no population, method, period, confidence interval, or educator confirmation. Such fields must not be represented to educators as measured prevalence.

### Vector search and diagnosis quality

`generate_deterministic_embedding()` does not tokenize or encode semantic relationships. It derives each coordinate from `SHA-256(f"{text}:{i}")`, rescales the hash, and L2-normalizes the result. Similar text does not obtain similarity because of shared meanings; rather, changing the complete input changes all hash inputs. The function is deterministic and convenient for offline tests, but it is not a semantic embedding model. [2]

`search_nearest_misconceptions()` always returns the closest rows under the optional exact-domain filter, with no minimum threshold, no target-KC filter, no published-status filter, no source/course filter, no duplicate suppression, and no reranker. The public `/knowledge/misconceptions/search` endpoint directly exposes the same retrieval, including `flawed_rule` and remediation text, and has no assignment context parameter. [2] [14]

The dialogue engine imposes a gate, but it is only `traps[0]["similarity"] > 0.01`. [5] A source-equivalent read-only calculation replicated the exact hash-vector formula and stored index text. It produced the following top same-domain similarities, each above the current match gate:

| Probe type | Query text | Top retrieved ID | Similarity | Current disposition |
|---|---|---:|---:|---|
| Unrelated history | “I need help organizing my backpack before school tomorrow.” | `MISC_HIST_001` | 0.071403 | Would be labeled on a generic history turn |
| Unrelated algebra | “The rainforest has many endangered species and colourful birds.” | `MISC_0102` | 0.029730 | Would be labeled on a generic algebra turn |
| Unrelated language | “My bicycle chain needs oil after a rainy commute.” | `MISC_LANG_002` | 0.014672 | Would be labeled on a generic language turn |
| Nonsensical history | “qzxv blorp 17 marbles beneath violet satellite” | `MISC_HIST_009` | 0.050596 | Would be labeled on a generic history turn |

These values do not claim a live database result; they are a reproducible calculation of the exact deterministic function and cosine criterion in the checked-out code. The source-level conclusion is unambiguous: the production condition accepts any one of these values. The existing pgvector test checks that results are nonempty, have expected keys, are sorted, and share the requested domain. It does **not** assert the expected record for a positive example, any minimum calibrated score, a false negative, a false positive, or a target-KC restriction. [2] [15]

### Dialogue matching and grounding behavior

The current dialogue code has two materially different modes.

1. **Generic or ungrounded turn.** `generate_response()` calls `search_nearest_misconceptions(student_input, limit=1, domain=domain)`, and selects the result above `0.01`. It then gives the matching remediation rung to the student. It does not establish that the learner made an error, reproduce the stated flawed rule from the work, inspect the active subproblem, use recent attempts, or limit records to target KCs. [5]

2. **Course-grounded turn with an assignment hint ladder.** The expression `[] if hint_ladder and is_course_grounded else ...` skips taxonomy retrieval. Generated assignments contain a five-rung ladder, so the usual grounded path supplies an assignment hint rather than a misconception-specific hint. The subsequent target-KC check is therefore ordinarily bypassed, not an active safety control. [5] [7]

The router correctly obtains assignment prompt, domain, ladder, and target KCs from the assignment associated with the session rather than trusting client-supplied prompt/domain values. [8] This protects the assignment context. It does not, however, enforce issue #42’s “published only” rule: `get_public_assignment()` loads an assignment by ID without requiring `spec.status == "published"`, and session creation accepts an arbitrary assignment ID without verifying assignment publication. [7] [16]

A match causes the router to log a `misconception_flagged` event with `kc_id: "unmapped"`, although the retrieved row has an actual KC. [8] The cohort roster later treats every `misconception_flagged.payload.kc_id` as a struggling KC, so dialogue-produced diagnostics can show teachers an artificial “unmapped” KC rather than the relevant instructional concept. [17]

The intended reference design differs substantially: it specifies a step context, pre-seeded traps, target KC, recent history, target-KC/ancestor filtering, a top-five candidate set, reranking against actual work, and a confidence threshold of 0.75 with an abstention path. None of those steps appears in the executable dialogue pipeline. [3]

### Assignment and distractor path

`DistractorEngine.get_distractors_for_kcs()` does use a SQL KC filter. It retrieves up to three static rows for the requested domain and target KCs, but lacks `ORDER BY`, publication/status checks, version pinning, validation state, source relevance, and educator choice. Its output is a textual “diagnostic_probe,” not a constructed answer option. [6]

`generate_scaffolding_plan()` calls this engine and returns `distractor_traps` in an in-memory `ScaffoldingPlan`. [7] Yet `QuestionSpec` and `PublicQuestionSpec` have no `distractor_traps` or `misconception_probes` field, and `draft_question()` does not persist them. Thus an educator’s planning response can display candidate traps, but a resulting assignment does not retain selected misconception IDs for later tutor matching. The separate JSON assignment schema documents `misconception_probes` and `distractors`, but the active Pydantic/runtime model does not implement that contract. [7] [18]

The educator’s free-text answer to `Q2_MISCONCEPTIONS` is also used as prompt/rubric wording, not parsed or validated as a taxonomic selection. For example, a string containing an ID in a test remains free text; no code resolves it to a record or writes it into a published assignment. [7] [19]

### Outcomes, effectiveness, auditability, and access safety

The event store is append-only in the normal internal flow and preserves raw student input in `student_prompt_submitted` payloads. [8] [20] It is useful trace data, but it does not create a validated misconception evidence chain.

The dossier synthesizer only adds a misconception to its per-question list when it appears in a `hint_delivered` event. It ignores a `matched_misconception_id` in `tutor_turn_completed` and ignores the dedicated `misconception_flagged` event. It defines `solved_correctly` as “there was at least one attempt and no adversarial prompt,” then marks a triggered misconception resolved when `len(q_misconceptions) > 0 and solved_correctly`. Finally, its aggregate `total_misconceptions_resolved` is set exactly equal to `len(all_misconceptions_triggered)`. [9]

Accordingly, the current outcome fields do **not** demonstrate that a learner revised the particular flawed rule, answered a criterion correctly after intervention, retained the learning, or benefited more than a comparison condition. They should be renamed as prototype signals or withheld from effectiveness claims until validated.

There is no application authentication/authorization dependency in the inspected API routers. In particular, `handle_dialogue_turn()` checks that the session exists and is active but does not compare `request.student_id` with the session’s stored `student_id`; `/events/log` accepts arbitrary event type and payload for a supplied session UUID. [8] [16] This permits corrupted or spoofed diagnostic evidence if these endpoints are reachable outside a protected trusted boundary. The Answer Vault’s method documentation says “authenticated educator review,” but its implementation accepts any `teacher_id` string and returns the entry if the token exists; this audit treats it as a related prototype authorization caveat rather than a misconception-specific control. [21]

The LLM orchestration is a relative strength: its normal dialogue call receives public assignment context and a server-selected hint, uses a pseudonymous provider user value, and defaults to deterministic operation. It is not presently used for candidate generation. [5] [22] If candidate generation is added, raw student identity and complete submissions must remain out of any external-provider request unless institutionally approved and minimized, as issue #42 requires. [1]

## Pedagogical and safety judgment

| Dimension | Judgment | Verified basis | Consequence |
|---|---|---|---|
| Card design | **Promising but ungoverned** | Most cards contain a plausible flawed model, trigger, learner-error example, explanation, and staged hints. [11] [12] | Useful material for educator review; not sufficient evidence for automatic teaching action. |
| Remediation quality | **Mixed** | Rungs begin with inquiry, but several later math/history rungs state the correct transformation, answer, or factual claim. The deterministic default returns the server text unchanged. [5] [11] [12] | Later rungs may be appropriate only after educator-approved disclosure policy; they are not uniformly non-disclosing. |
| Historical/cultural safety | **Needs expert review** | Seed cards make specific interpretive and numerical claims, yet store no sources, edition/page, reviewer, uncertainty, or revision date. [12] | Educators cannot verify scope, contestability, or culturally sensitive framing before use. |
| Diagnostic validity | **Unsafe for labeling** | Hash-derived vectors, top-one retrieval, `>0.01` gate, and reproduced unrelated matches. [2] [5] | False learner profiling and irrelevant hints are credible risks. |
| Context relevance | **Partially protected but functionally incomplete** | Router anchors assignment context; grounded ladder path suppresses taxonomy rather than selecting approved target-KC records. [5] [8] | Avoids some irrelevant hints but fails the desired precise diagnosis workflow. |
| Data integrity | **Insufficient** | No record versions/statuses; broad event APIs; `unmapped` diagnostic KC. [4] [8] [16] | Teacher reports and future candidate evidence can be unreliable. |
| Evaluation | **Not an effectiveness system** | Resolution heuristic and aggregate equality do not link intervention to demonstrated conceptual change. [9] | Do not claim misconception remediation effectiveness. |

## Recommendations: educator-governed lifecycle

The following is a **proposal**, not current implementation. It is designed to satisfy #42 while preserving the product’s useful answer-isolation and assignment-grounding patterns.

### 1. Establish a versioned, reviewable misconception record before improving models — **P0**

Replace “row exists” with a lifecycle state machine: `candidate → validation_failed | under_review → needs_revision | rejected | published → deprecated | retired`. Publication must be an explicit educator action; candidate records must never enter the retrieval index used by students. Create immutable `misconception_versions` and retain a stable `misconception_id` plus version ID. Editing a published card creates a new version, never overwrites historical content. Published assignments should pin the approved version(s) they selected so later card revisions cannot silently alter an active course.

A proposed card should retain the full instructional card: primary and related KCs, domain, learner-language examples, flawed rule, correct conceptual model, trigger conditions, remediation ladder, disclosure classification per rung, severity, and intended learner/grade range. It should also retain required governance information: candidate source type, source citations/excerpts, source/course scope, author, reviewer(s), review decisions, timestamps, review rationale, validation evidence, version, effective dates, retirement reason, and accessibility/equity considerations. Put learner examples in a protected evidence table, not in a broadly readable taxonomy row.

**Acceptance criteria:**

- A database constraint/API contract prevents retrieval unless a specific version is `published` and within its effective interval.
- A candidate has at least one provenance record, target KC, learner-language example or approved synthetic analogue, flawed rule, remediation plan, author, and version before review can begin.
- Publication requires a recorded educator reviewer distinct from the author or a documented single-review exception.
- Editing a published card creates a new version and preserves all historical version and decision records.
- Retired/deprecated versions are excluded from new assignments and diagnostics while remaining auditable for prior events.

### 2. Make diagnosis assignment-bound, KC-bound, calibrated, and abstaining — **P0**

At runtime, require an active **published** assignment and a specific active question/subproblem. Retrieve only misconception versions that the educator explicitly selected for that assignment, or that are published for the assignment’s target KC(s) and approved course scope. Apply the KC filter in SQL before top-k selection. Do not provide a generic taxonomy label in an ungrounded conversation; give a generic Socratic prompt and record no learner diagnostic label.

For mathematics or other structured work, first use a deterministic symbolic/step validator to establish an observable error pattern. For free text, use a trained/validated semantic retrieval system only as candidate generation. Rerank candidates against the learner utterance, task, known answer constraints, and candidate flawed rule. Require a calibrated per-domain/per-KC threshold and a separation margin over the runner-up. Return `unknown`/no label on low confidence. Store confidence, threshold version, candidate version, target KC, assignment version, and a bounded rationale for educator audit; do not present the label to the student as a fixed trait.

**Acceptance criteria:**

- Generic/unbound dialogue cannot emit `matched_misconception_id`.
- The matching SQL/API query filters to published versions and the active assignment’s approved misconception IDs or target KCs.
- The system records an abstention for unrelated, ambiguous, or low-confidence input and does not create a `misconception_flagged` event.
- Every diagnostic event contains the actual target KC, misconception version, decision confidence, threshold/reranker version, and assignment/question context.
- Evaluation fixtures demonstrate target-KC true positives, cross-domain lookalikes, same-domain unrelated utterances, ambiguity, and adversarial answer-extraction attempts.

### 3. Build candidate generation as a privacy-preserving review queue — **P1**

Use two governed inputs: educator-approved instructional sources and recurring, pseudonymized error-pattern aggregates. Candidate generation should consume the minimum approved extract: no raw names, direct identifiers, whole submissions, or complete histories. Before any external model is used, apply institutional policy, retention restrictions, access controls, and provider approval. Prefer deterministic clustering of de-identified features and instructor-curated source excerpts. A model may draft a card only from an approved cluster summary and approved sources, and only into `candidate` state.

Candidates should include a source/evidence bundle, cluster size and period where applicable, representative sanitized utterances, proposed KCs, duplicate-neighbor results, a draft flawed-rule hypothesis, and a draft intervention. Never infer that a rare utterance is a misconception merely because it is unusual. Separate legitimate alternative interpretations, language proficiency variation, disability/access needs, and careless slips from a durable conceptual model.

**Acceptance criteria:**

- Candidate-generation jobs write only `candidate` versions and cannot call the publication method.
- External-provider requests are logged with source approval ID, minimization status, provider policy basis, and no raw student identifiers or complete submissions.
- Candidate evidence distinguishes approved source material from pseudonymized aggregate patterns.
- The review queue supports educator accept, revise, reject, merge-as-duplicate, and request-more-evidence actions.

### 4. Validate instructional quality and false-positive risk before review — **P1**

Run deterministic validation first: JSON/data contract validation; stable ID/version rules; primary/related KC existence; domain and grade-range coherence; required source citation; duplicate and near-duplicate detection; presence of learner-language positives and carefully chosen non-examples; remediation rung order; answer-disclosure linting; and accessibility/style checks. Add model-assisted validation only as a non-authoritative reviewer that returns structured concerns and citations for an educator.

Then evaluate the candidate in a held-out fixture set. Require both an appropriate true-positive rate and a stringent false-positive ceiling for the target KC/domain before human approval. The evaluation must include same-domain sentences that are correct, irrelevant, or alternative but valid, because a nearest-neighbor system always produces a nearest item.

**Acceptance criteria:**

- CI rejects invalid taxonomy data, nonexistent KCs, missing provenance, missing review fields, and invalid state transitions.
- Duplicate review presents nearest published/candidate cards with similarity and an educator merge decision.
- Each published version has test results for positive, negative, cross-KC, cross-domain, and adversarial fixtures.
- A machine-generated concern cannot automatically reject or publish a record; the final decision remains attributable to an educator.

### 5. Measure effectiveness as an intervention outcome, not a count — **P1**

Record the exact approved card version and intervention rung used, but distinguish **detection**, **educator confirmation**, **immediate revision**, **criterion-aligned success**, and **later retention**. Resolve a misconception only when the learner subsequently demonstrates the relevant KC on a new or sufficiently independent attempt under a predeclared rule. Do not count “an attempt existed” as correctness, and never set resolution equal to encounter count.

Educator views should show counts with uncertainty and filtering by course, assignment version, KC, card version, and cohort period. They should expose false-positive adjudications, override reasons, use rate, abstention rate, post-intervention performance, and inequity checks. A high false-positive rate, poor outcome trend, outdated source, or educator complaint should automatically route a published version to review or deprecation—not silently keep it live.

**Acceptance criteria:**

- The data model differentiates detection, confirmation, intervention, outcome, and educator override events.
- “Resolved” requires a specified post-intervention success criterion and cannot be computed from mere participation.
- Teacher dashboards provide a record-level use/effectiveness view and a retirement/review action.
- Automated monitoring flags materially elevated false-positive rates, adverse outcome trends, and expired or contested source evidence for educator review.

### 6. Close authorization and audit-integrity gaps — **P0**

Introduce authenticated principals and role/course authorization for candidate evidence, publication, diagnostic search, event logging, and reports. Bind a dialogue request to the session’s authenticated learner and assignment/question. Eliminate arbitrary client event writes in production or replace them with server-owned event types and validated payload schemas. Preserve append-only event facts, but store diagnostic decisions as structured, immutable records containing the versioned evidence needed for later review.

**Acceptance criteria:**

- A request cannot write dialogue/event data for another learner’s session or arbitrary assignment.
- Only authorized educators for the course can inspect learner examples, approve/revise/publish/retire cards, or access effectiveness views.
- The system retains an immutable audit trail for candidate, validation, review, publication, matching, override, and retirement decisions.

## Recommended first implementation slice

Implement **P0 governance plus runtime containment before candidate generation**. The first slice should add a versioned misconception model with `candidate` and `published` states; author/reviewer/provenance/KC fields; a one-way educator publication action; assignment-level selected misconception-version IDs; and a matching contract that accepts only a published assignment/question and only its published approved cards. Replace the `> 0.01` top-one decision with abstention until a calibrated evaluator exists. Generic dialogue should remain Socratic but unlabelled.

This slice delivers the immediate safety property of #42: no automatically published or out-of-context misconception can shape a tutor turn. It also establishes the identifiers, audit trail, and fixtures needed for later de-identified candidate generation and effectiveness work. Candidate-generation automation should be deliberately deferred until governance, authorization, data minimization, and evaluation baselines are working.

## Test plan for the first slice

Add fixture-driven tests at three levels. Unit tests should validate lifecycle transitions, required review metadata, immutable published versions, retirement behavior, KC referential checks, disclosure linting, and deterministic assignment-version pinning. Retrieval tests should assert exact expected results for known positives and abstention for unrelated text, nonsense, same-domain alternatives, adjacent-KC lookalikes, and no-assignment requests. API tests should prove that draft/retired cards, unauthorized actors, mismatched students, and assignments outside the course cannot generate a diagnostic event.

End-to-end tests should use a published assignment that names specific misconception versions, simulate an observable learner error, verify that a target-KC hint is selected without revealing a prohibited answer, capture an educator confirmation/override, and verify a later criterion-aligned attempt before marking resolution. Add adversarial fixtures that request an answer while mentioning misconception labels, manipulate target KC/assignment IDs, and try to inject fake `misconception_flagged` events. The evaluation suite should report confusion matrices and abstention rates by domain/KC/card version, with a release gate set by educator-approved thresholds.

## References

[1]: https://github.com/darkaengl/fiosra/issues/42 "GitHub issue #42: Misconception Authoring, Validation, and Tutor Effectiveness"
[2]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/seed_pipeline.py "Seed pipeline: deterministic embedding, misconception hydration, and nearest search"
[3]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/reference/agents/misconception_diagnosis_agent.md "Misconception Diagnosis Agent reference specification"
[4]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/migrations/001_initial_schema.sql "Initial PostgreSQL schema including misconceptions table"
[5]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_engine.py "SocraticDialogueEngine dialogue diagnosis and hint selection"
[6]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/distractor_engine.py "DistractorEngine target-KC misconception retrieval"
[7]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/generator.py "AssignmentGenerator scaffolding, persistence, public projection, and publication"
[8]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_router.py "Dialogue message route and misconception event logging"
[9]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/synthesizer.py "Evidence dossier misconception metrics and resolution heuristic"
[10]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/knowledge_components_curriculum.seed.json "Knowledge component curriculum seed data"
[11]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/misconceptions_algebra_geometry.seed.json "Algebra and geometry misconception seed cards"
[12]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/misconceptions_language_history.seed.json "Language and history misconception seed cards"
[13]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/schemas/misconception.schema.json "MisconceptionEntry JSON Schema"
[14]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/knowledge_router.py "Knowledge API misconception search endpoint"
[15]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_graph_service.py "Graph and pgvector misconception search tests"
[16]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/events_router.py "Session and arbitrary event API routes"
[17]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/service.py "Cohort roster diagnostic aggregation"
[18]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/data/schemas/assignment_spec.schema.json "Documented assignment misconception probe and distractor schema"
[19]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_assignment_designer.py "Assignment-designer misconception planning tests"
[20]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/event_store.py "Append-only event store implementation"
[21]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/vault.py "Answer Vault educator retrieval implementation"
[22]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/llm/orchestrator.py "LLM orchestration safety boundary"
