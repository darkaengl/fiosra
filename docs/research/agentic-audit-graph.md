# Neo4j Graph Usefulness and Architecture Audit

**Issue:** [#43 — Knowledge Graph Utility, Data Model, and Educator UX Audit][1]  
**Audited revision:** `59036e5d6fc97b42a9a23aa80736d5c6009bae8e` on `feat/end-to-end-learning-workflow`  
**Audit date:** 2026-09-10  
**Author:** Manus AI  
**Scope:** Neo4j client; graph service and router; seed data and migrations; current Svelte Knowledge Graph, Curriculum/Modules, and Cohort screens; graph-adjacent product flows; and graph tests.  
**Change policy:** This audit ran read-only inspection and local tests. It did **not** change production code, settings, database data, seed data, or GitHub records.

## Executive conclusion

**Verdict: Neo4j is technically functional but is not yet justified as an MVP operational dependency.** The repository has a small, valid, live prerequisite graph with useful basic traversal primitives. However, the only production workflow that calls it is syllabus chunk tagging, and the default course-domain casing causes that workflow to bypass the live graph and use a stale hard-coded fallback. The actual student dialogue, misconception diagnosis, assignment distractors, curriculum sequencing, cohort diagnosis, and frontend graph screen do not use graph traversal to make a product decision.

The current Neo4j database is therefore best described as an **unconsumed curriculum reference DAG**, rather than a live decision system. It could earn its cost through one narrow teacher-facing prerequisite-coverage decision: show an educator when a selected module target KC has prerequisites that no earlier course module covers, and take the educator directly to the affected module and KC. That slice requires explicit teacher-confirmed course-module-to-KC mappings, source-of-truth reconciliation, and an outage-safe read model. It should be implemented before any graph visualization work.

If that vertical slice is not prioritized, the smallest safe simplification is to treat the committed KC JSON as the authoritative curriculum catalog, materialize its `REQUIRES` edges in PostgreSQL, serve prerequisite and frontier queries with recursive SQL or a precomputed closure, and remove the Neo4j container, client, graph-only API surface, and display-only graph screen. At the present graph size—**19 KCs and 21 edges**—Neo4j does not provide demonstrated product value that a relational projection cannot provide.

> **Interpretation rule used in this report:** “Verified” means observed in the audited source, tests, or read-only live inspection. “Proposal” means a recommended future change, not a claim about current behavior.

## Audit method and observed state

The audit inspected the complete Neo4j execution path and its callers. It also read the current source used to produce the Svelte UI and confirmed that the served frontend bundle contains the same hard-coded Knowledge Graph strings. Read-only Neo4j inspection found a reachable database with **19 `KnowledgeComponent` nodes**, **21 `REQUIRES` relationships**, no isolated KCs, and no live `Misconception` nodes. The committed curriculum seed has the same 19 KCs and 21 prerequisite declarations; it has 13 history KCs, 6 language KCs, and 4 roots. These observations support that the current instance was seeded from the current curriculum catalog, but do not establish an automatic reconciliation process.

| Check | Result | Classification | Evidence |
|---|---:|---|---|
| Focused test run | `11 passed in 1.29s` | Verified | `tests/test_graph_service.py` and `tests/test_database_foundation.py` [13] [14] |
| Neo4j health query | Reachable during audit | Verified | `Neo4jClient.health_check()` [3] |
| Live graph nodes / relationships | 19 / 21 | Verified | Read-only `MATCH` counts; committed seed agrees [5] |
| Live node labels | `KnowledgeComponent` only | Verified | Read-only label count |
| Live relationship types | `REQUIRES` only | Verified | Read-only relationship-type count |
| Live isolated KCs | 0 | Verified | Read-only `MATCH (k) WHERE NOT (k)--()` query |
| Current graph UI data | 7 hard-coded nodes / 6 hard-coded edges | Verified | `KnowledgeGraph.svelte` [15] |
| Frontend calls to `/knowledge` | 0 | Verified | Source-wide frontend call-site inspection; the graph screen has no `fetch` |

The focused test result proves the test assumptions under the current local environment. It does **not** prove outage handling, curriculum-to-module mapping integrity, student mastery validity, or that graph queries affect a real educator or learner decision.

## Actual architecture and node/relationship model

### Runtime topology and ownership

`Neo4jClient` is an async singleton around Neo4j’s Bolt driver. It lazily creates a driver for the current running event loop, exposes scoped sessions, catches connection-related exceptions in `health_check()`, and closes the pool only in the FastAPI lifespan shutdown hook. The application has Neo4j settings with local defaults and Docker Compose provisions a Neo4j 5 service, but application startup neither initializes graph schema nor seeds curriculum data. The manual `make seed` command runs the dual-database seed pipeline. [3] [21] [20] [4]

The committed file `fiosra/knowledge/seeds/knowledge_components_curriculum.seed.json` is the practical catalog source used by `seed_neo4j_curriculum()`. The seed pipeline invokes `GraphService.seed_curriculum()`, which creates constraints and an index, merges KC nodes, then merges edges. It is an **upsert**, not a reconciliation: it never deletes a removed KC or obsolete `REQUIRES` edge, and it returns the lengths of the input lists rather than counts confirmed from Neo4j. [4] [2] [5]

PostgreSQL retains loose `kc_id` strings in `syllabus_chunks` and `misconceptions`. These are not foreign keys to Neo4j, and there is no course-module-to-KC mapping table or student-KC-mastery table. The initial migration explicitly says KCs live in Neo4j, but its comment names `:KnowledgeConcept`, whereas the implementation creates `:KnowledgeComponent`; that mismatch is documentation-level but illustrates the absence of an enforced cross-store contract. [6] [7]

| Data concern | Current authoritative location | Materialized / referenced locations | Integrity status |
|---|---|---|---|
| KC catalog and direct prerequisite declarations | `knowledge_components_curriculum.seed.json` | Neo4j after manual seed; static frontend copy is separate | No version, reconciliation, or startup validation |
| KC node identity | Neo4j `KnowledgeComponent.kc_id` after hydration | `syllabus_chunks.kc_id`, `misconceptions.kc_id`, JSON assignment specs | Neo4j uniqueness only; PostgreSQL references are unconstrained |
| Misconception catalog | Two JSON seed files, then PostgreSQL `misconceptions` | Tutor and distractor queries use PostgreSQL | No Neo4j `Misconception` node is seeded |
| Course and module order | PostgreSQL `courses` / `modules` | Modules UI and service | Position-based only; no KC mapping |
| Student struggle indicators | PostgreSQL event payloads | Cohort roster response | KC values can be arbitrary or `"unmapped"`; no graph validation |
| Student mastery | None | Client-supplied IDs only to `/knowledge/frontier` | No durable or verified source |

### Implemented graph schema

The implementation creates unique constraints on `KnowledgeComponent.kc_id` and `Misconception.misconception_id`, plus a range index on `KnowledgeComponent.domain`. Read-only live inspection confirmed that those constraints and the domain index are online. The `Misconception` constraint is presently unused because the live graph has no such nodes. [2]

| Element | Actual shape | Required / enforced fields | Observed live state | Notes |
|---|---|---|---|---|
| KC node | `(:KnowledgeComponent)` | Only `kc_id` uniqueness is enforced | 19 nodes | Seed sets `kc_id`, `label`, `domain`, `bloom_level`, `description`, and `estimated_difficulty` |
| Prerequisite edge | `(target)-[:REQUIRES]->(prereq)` | No relationship property or endpoint constraint | 21 edges | Direction means “target requires prerequisite,” which `get_prerequisites()` traverses upstream |
| Misconception node | `(:Misconception)` | `misconception_id` uniqueness is configured | 0 nodes | Neither seed pipeline nor service creates them |
| KC–misconception edge | None | None | 0 edges | Misconception-to-KC association exists only as PostgreSQL `kc_id` text |
| Course/module node or edge | None | None | 0 graph entities | Course sequencing remains PostgreSQL position order |
| Learner/mastery node or edge | None | None | 0 graph entities | Frontier trusts the caller’s ID list |

The relationship direction is internally consistent. `seed_curriculum()` emits `(target)-[:REQUIRES]->(prereq)`, `get_prerequisites()` searches that direction transitively, and `get_kc_details()` searches the inverse direction for direct dependents. The graph has no edge type that expresses misconception inhibition, evidence coverage, module ownership, demonstrated mastery, or pedagogical status. [2]

### Seed quality and pedagogical model

The curriculum seed is a small DAG that combines French Revolution content KCs with transferable historical-reasoning skills and a language/argumentation sequence. Several KCs have multiple prerequisites, such as `KC_HIST_ESTATES_GENERAL`, `KC_HIST_TENNIS_COURT_OATH`, `KC_HIST_DECL_RIGHTS_MAN`, `KC_HIST_HISTORICAL_ARGUMENT`, `KC_LANG_STRUCTURED_ESSAY`, and `KC_LANG_RHETORICAL_ANALYSIS`. This is a reasonable starter structure for expressing dependency rather than mere chronological order. The seed has no missing declared prerequisite IDs and no isolated KCs in the inspected live graph. [5]

Its instructional metadata is insufficiently governed for high-stakes sequencing. `bloom_level` is an undocumented integer rather than a named taxonomy/version; `estimated_difficulty` is a free numeric value with no calibration, evidence, learner-population definition, or update process; and the catalog mixes domain-general disciplinary practices with course-specific historical events without specifying granularity rules. The frontier orders KCs by these values, so they influence output despite having no stated validation basis. [2] [5]

The misconception data are richer as instructional prose than the live graph model. They include example errors, corrections, levels of remediation hints, severity, frequency percentile, source, a primary `knowledge_component`, and related KCs. However, they are loaded into PostgreSQL with deterministic vector embeddings; their related-KC arrays are discarded and no Neo4j nodes or relationships result. Of the **25** misconception records, 20 primary KC references point to the 19-KC history/language graph and 5 algebra/geometry primary references have no seeded Neo4j KC. Among current graph KCs, **16 of 19** have at least one primary misconception seed; `KC_HIST_TIMELINE_SEQUENCING`, `KC_LANG_READING_COMPREHENSION`, and `KC_LANG_RHETORICAL_ANALYSIS` have none. [4] [5] [23] [24]

This seed collection has good examples of reasoning-oriented feedback, such as distinguishing evidence from inference and avoiding single-cause explanations. It is not yet a validated pedagogical taxonomy because source labels are broad, provenance is not operationalized, relationships are not materialized, and outcomes are not measured. The system should not present its `frequency_percentile`, difficulty, or graph ordering as learner-validated intelligence.

## What graph operations actually do

`GraphService` exposes five operations: schema initialization, seed upsert, transitive prerequisite lookup, learning-frontier lookup, acyclicity check, KC details, and domain-filtered KC list. The API exposes integrity, KC details, prerequisites, frontier, and a misconception-search endpoint. The latter is named under `/knowledge` but executes PostgreSQL pgvector search rather than Neo4j graph search. [2] [12] [4]

| Operation | Current result | Actual caller / consumer | Decision impact today |
|---|---|---|---|
| `get_prerequisites(kc_id, depth)` | Distinct transitive prerequisite IDs, default depth 10 | API and tests | No frontend consumer; no module, tutor, or cohort action uses it |
| `get_learning_frontier(mastered_kc_ids, domain)` | Unmastered KCs whose **direct** prerequisite IDs are all supplied by caller | API and tests | No mastery store and no frontend caller; not a product decision |
| `get_kc_details(kc_id)` | KC attributes with direct prerequisites and dependents | API and tests | No frontend caller |
| `check_acyclicity()` | Tests cycles no longer than 20 edges | Seed pipeline, API, tests | Protects manual seed only; no reconciliation or course mapping check |
| `list_all_kcs(domain)` | KC label and description list | Syllabus `match_kc_for_text()` | Sole live graph use, but default domain casing bypasses graph |
| `search_nearest_misconceptions()` | PostgreSQL cosine similarity result | Dialogue, API, tests | Does affect tutoring, but it is **not** Neo4j-based |

### The only live graph-dependent workflow: syllabus tagging

`SyllabusParser.match_kc_for_text()` asks Neo4j for all KCs in the course domain, then scores each KC by the count of its label words longer than three characters that occur in the chunk. It saves at most one winning `kc_id` to the PostgreSQL syllabus chunk. Assignment generation later treats those stored strings as possible target KCs in its prompt, rubrics, and distractor lookup. This is the one indirect path by which the graph catalog can alter an assignment’s target KC. [8] [9]

That integration is materially unreliable in its normal path. `CourseCreate.domain` defaults to `"History"` and stored course domains preserve the submitted casing. The graph seed uses lowercase `"history"`; `list_all_kcs()` filters with exact equality. Read-only verification returned 13 KCs for `domain="history"` but **0** for `domain="History"`. Thus default course ingestion falls back instead of reading the live catalog. [25] [2] [8]

The fallback list is not a safe local replica. It is history-only, contains only six items, and includes obsolete/non-catalog IDs including `KC_HIST_TENNIS_COURT`, `KC_HIST_BASTILLE`, and `KC_HIST_CALONNE`. A simulated Neo4j outage with text mentioning the Tennis Court Oath produced `KC_HIST_TENNIS_COURT`; read-only verification confirmed that this ID is absent from the committed current KC seed. The failure path can therefore persist an invalid graph reference in PostgreSQL and then carry it into assignment target metadata. [8] [5]

The matching algorithm is also a lexical label overlap, not semantic classification or educator confirmation. It lacks a score threshold beyond one matching word, a confidence value, multiple KC coverage, an explanation of why a KC was selected, and a check that the selected ID exists in the current catalog. It can be useful as a suggestion generator, but it is not safe as an authoritative instructional mapping.

## Product decision audit

### Verified current decision paths

The graph does **not** presently control the core learning workflow described in product documentation. The dialogue engine diagnoses misconceptions through PostgreSQL vector search. The distractor engine reads PostgreSQL `misconceptions`. The dialogue router logs a matched misconception as `kc_id: "unmapped"`, so cohort reporting cannot reliably connect a real tutor diagnosis to the prerequisite graph. [10] [11] [9]

Modules are locked purely by their list position. `CourseService.add_module()` marks position greater than one as locked, and `get_modules_for_course()` locks every module after the first based on result order. Neither function queries a KC nor checks a prerequisite. The cohort roster computes autonomy and struggle from PostgreSQL events and returns strings supplied in event payloads. It performs no graph lookup, no prerequisite-gap computation, and no assignment-to-module-to-KC navigation. [11]

| Product decision | Is Neo4j consulted? | What actually determines it | Assessment |
|---|---:|---|---|
| Whether a student gets a tutoring response or which hint rung | No | Server-side hint-event state, public assignment ladder, and PostgreSQL misconception vector search | Graph has no effect |
| Which misconception becomes a tutor prompt | No | PostgreSQL pgvector similarity, subject to assignment target filtering | Graph has no effect |
| Which distractor traps are proposed | No | PostgreSQL `misconceptions.kc_id` query | Graph has no effect |
| Whether a module is locked | No | PostgreSQL module position / ordered index | Graph has no effect |
| Which students are struggling | No | Hint/misconception event aggregates and thresholds | Graph has no effect |
| Which KC tags a syllabus chunk | Nominally yes | Exact-case graph list plus lexical label overlap; normally falls back for default `History` | Weak and unsafe indirect effect |
| What the graph screen shows | No | Static Svelte arrays and static text | Graph has no effect |

### Three decisions Neo4j could support, but does not yet support

The following are **proposals**, not descriptions of current behavior. Each is pedagogically explainable because it makes a visible curriculum or intervention decision from explicit relationships.

| Proposed decision | Necessary data not present today | Minimum graph query / explanation | User action and safety boundary |
|---|---|---|---|
| **Prerequisite coverage before publishing a module** | Educator-confirmed module-to-KC targets and prior-module scope | For each target, find transitive `REQUIRES` prerequisites that lack an earlier mapped module | Educator may revise mapping, reorder modules, or explicitly waive with reason; never auto-lock or rewrite curriculum |
| **Readiness recommendation for an identified learner** | Evidence-backed KC mastery state with timestamps and confidence | Return only frontier KCs and name satisfied / missing prerequisites | Teacher or learner sees a recommendation and evidence; it must not be an automated placement, grade, or denial of access |
| **Cohort prerequisite-gap intervention** | Tutor diagnosis must record actual KC, and course assignments must map to KCs | Aggregate flagged KCs, traverse their prerequisites, then find source/module artifacts | Teacher sees a ranked, explainable group pattern and can open the source/module; dispatch remains a reviewed action |

These three queries would make the existing DAG observable in a teacher or learner decision. They would still need a fallback projection because the value is in the curriculum rule, not in Neo4j availability.

## Frontend audit

### Knowledge Graph screen

The `KnowledgeGraph.svelte` screen is wholly static. It declares seven node objects and six edge objects in source, draws them into an SVG, uses no network request, does not bind `activeFilter` to rendered nodes or edges, and has no node click handler despite the inspector instruction to “Click a node to inspect.” “Export Graph (JSON)” and “Sync to Neo4j” are buttons without handlers. The current `course_id` query parameter is also not read by this route. [15] [26]

The static screen is not a faithful visualization of the live graph. It declares identifiers such as `KC_HIST_FISCAL_CRISIS`, `KC_HIST_ESTATE_SYSTEM`, `KC_HIST_SOCIAL_CONTRACT`, `KC_HIST_CONSTITUTIONAL`, `KC_HIST_TERROR`, and `KC_HIST_NAPOLEON`, which are not in the current seed. Only `KC_HIST_POPULAR_SOV` overlaps the current catalog. It says “7 Nodes • 6 Edges • HIST-201,” “14 KCs Active,” “14 Misc. Traps,” “3 Modules,” and “Fall 2026”; these are fixed display text, not calculated state. The served bundle is built from the current source output directory and contains the same graph text. [15] [26] [27]

The SVG also does not label arrows with `REQUIRES` or explain their direction. Its edge directions should not be interpreted as a visualization of the backend’s `(target)-[:REQUIRES]->(prereq)` semantics. This violates the issue’s explainability goal and risks a teacher reading a visual decoration as an accurate curriculum map.

### Modules and cohort screens

`Modules.svelte` fetches courses, a course, syllabus resources, and roster data. It neither fetches `/knowledge` nor uses KC metadata. Its empty state says the workspace is active in “PostgreSQL and Neo4j,” but the associated course workflow does not create or synchronize a course graph. The roster view displays `struggling_kcs` from the PostgreSQL cohort response. Its “Dispatch Targeted Socratic Micro-Scaffold” action is wired to an `alert()`. [16] [18]

`CohortDiagnostics.svelte` has hard-coded KPIs, a hard-coded KC heatmap, static student names and scores, and buttons with no action. It makes a “Real-time” diagnostic claim without a fetch, event subscription, or graph query. It is separate from the Modules screen’s live course roster and cannot be used to validate graph-driven diagnostics. [17]

The global header has a fixed “14 KCs Grounded” status chip and does not call the graph health or count endpoints. This can falsely indicate a healthy, grounded graph during an outage or when graph data does not match the selected course. [19]

Finally, the Vite development proxy lists `/courses`, `/events`, `/dialogue`, `/evidence`, `/assignments`, and `/healthz`, but not `/knowledge`. A new development-mode graph fetch using the intended relative backend route would require proxy configuration in addition to frontend implementation. [27]

## Failure degradation and engineering safety

### Current failure behavior

`Neo4jClient.health_check()` safely returns `False` for several connection failures, and FastAPI’s `/healthz` returns application status without checking Neo4j. This is a positive separation: an outage need not make the basic health endpoint fail. The course ingestion path catches expected Neo4j lookup failures and continues through a fallback list. [3] [21] [8]

That behavior is incomplete and unsafe at the application boundary. The `/knowledge` routes call graph methods without translating Neo4j failures into a truthful service-unavailable response or a canonical fallback response. An unavailable database therefore becomes an unhandled request failure. Docker Compose also makes app startup depend on a healthy Neo4j container, so the application cannot start under that declared stack when Neo4j is unavailable, even though most core product paths do not require the graph. [12] [20]

| Scenario | Current behavior | Safe? | Required outcome |
|---|---|---:|---|
| Neo4j unavailable during `/healthz` | Returns `200` application status | Yes, narrowly | Keep; optionally expose dependency state separately |
| Neo4j unavailable during syllabus ingestion | Logs warning; uses stale six-item fallback; persists candidate ID | No | Use versioned canonical catalog projection or leave suggestion unconfirmed; persist only validated IDs |
| Neo4j unavailable during `/knowledge/*` | Exception is not handled in router | No | Return explicit dependency-degraded response or canonical read-model result, with no false health claim |
| Neo4j unavailable before Compose app start | `depends_on: condition: service_healthy` prevents startup | No, for optional dependency | Make graph optional for core app start, or explicitly declare it a required service and remove fallback claims |
| Missing or empty graph | `check_acyclicity()` can return `True`; frontier can return empty | No | Distinguish empty/unseeded/degraded from a validated graph |
| Neo4j shutdown | `main.lifespan()` closes driver pool | Yes | Keep |

### Integrity and operational risks

`check_acyclicity()` searches only closed `REQUIRES` paths of length 1 through 20. It can miss a cycle whose shortest loop has more than 20 edges. It also returns `True` when no record is obtained, and it does not check orphan KCs, invalid node properties, stale edges, course/module mappings, or non-graph references. `seed_curriculum()` invokes this check only after writing data; it does not pre-validate input or roll back its Neo4j writes on failure. [2] [4]

The `depth` value in `get_prerequisites()` is interpolated into Cypher. The public router bounds it from 1 to 20, so the exposed API path is constrained, but service-level validation should not rely on every future caller using that router. [2] [12]

The client holds driver and loop at class scope. It recreates the driver when it observes a new running loop but does not close the previous driver at that moment. That is not a demonstrated outage, but it is a lifecycle risk for multi-loop test or worker environments. The present shutdown hook only closes the final referenced driver. [3] [21]

## Test coverage assessment

The current graph tests have useful happy-path coverage: acyclicity, a multi-hop traversal, history frontier outcomes, an average-latency assertion, and API endpoint responses. The database-foundation tests cover settings shape, singleton identity, and that `health_check()` returns a boolean if offline. The focused run passed in the audit environment. [13] [14]

They do not establish the issue’s acceptance criteria. Several tests require the seeded graph to exist and use shared live databases; none seeds an isolated graph fixture or validates the current JSON catalog against the actual graph. There is no simulated outage test for `get_prerequisites`, `get_learning_frontier`, `/knowledge/*`, or syllabus ingestion. There is no test for case-normalized domain filtering, stale fallback IDs, current graph UI/API parity, graph source reconciliation, orphan detection, cycles longer than 20, invalid PostgreSQL `kc_id` references, course/module mapping, or a teacher-visible product decision.

The `<15 ms` latency assertion is also environment-sensitive. It does not define a dataset size, driver connection state, percentile, CI condition, or outcome relevance. Keep performance measurement only after the graph has an end-user decision path and establish a deterministic benchmark fixture.

## Recommendations

### Priority 0 — stop presenting a display-only graph as live

**Proposal:** Remove, hide, or clearly label the current Graph route, static Cohort Diagnostics screen, and fixed “14 KCs Grounded” indicator as preview data until they derive state from an implemented read model. Do not add visual filters, export, or “sync” buttons ahead of a decision workflow.

**Rationale:** Current display values are inaccurate relative to the live graph, several controls are inert, and no frontend calls graph APIs. A static curriculum illustration has a higher risk of misleading educators than of helping them. [15] [17] [19]

**Acceptance criteria:**

1. A displayed graph count, edge, status, and selected-course label must be computed from a defined API or explicitly marked as demo content.
2. Every displayed edge must state `REQUIRES` and its direction in teacher language.
3. A displayed graph insight must link to a real KC detail and affected course artifact, or the Graph route must be absent from main navigation.
4. A graph service outage must never show a green/live status chip.

### Priority 0 — repair source-of-truth and outage safety before using graph output

**Proposal:** Keep the committed KC JSON as a versioned canonical curriculum artifact initially. Build a validated in-process or PostgreSQL read projection from it for fallback reads; normalize domains at the boundary; replace the stale hard-coded ingestion list; reject or flag any persisted KC ID not in the catalog; and make `/knowledge` distinguish unavailable, unseeded, and healthy states.

**Rationale:** The present default `History`/`history` mismatch bypasses Neo4j. The fallback can write obsolete IDs, and relational references are not constrained. A curriculum decision cannot be trusted while its identifiers drift under an outage. [25] [8] [6] [7]

**Acceptance criteria:**

1. `History` and `history` resolve to the same catalog domain under an explicit normalization rule.
2. Every fallback-generated `kc_id` exists in the same versioned curriculum catalog used for normal reads.
3. Syllabus tagging returns a confidence and “suggested/unconfirmed” state; it does not silently claim an authoritative mapping from one token overlap.
4. An unavailable, empty, and unseeded graph return distinct API states and do not produce a false integrity success.
5. Production startup can serve core authoring and student paths if the optional graph store is unavailable.

### Priority 1 — implement one decision slice: prerequisite coverage before module publication

**Proposal:** Add teacher-confirmed module-to-KC targets and a publish-time prerequisite-coverage check. For every KC targeted by a module, traverse its prerequisites and identify prerequisites not covered by any earlier module. Return the target, missing prerequisite, relationship explanation, and direct links to modules/resources that could be adjusted.

**Rationale:** This is the smallest graph query that can alter a legitimate educator decision without pretending to know student mastery. It makes dependencies visible at the moment course sequencing is authored. It also has a clear fallback: use a canonical prerequisite closure projection. The current `modules.position` lock alone provides no conceptual justification. [11] [2]

**Acceptance criteria:**

1. A course-module-to-KC mapping is persisted with educator confirmation and catalog version, rather than inferred only from keyword matching.
2. The API reports missing transitive prerequisites with an explainable KC path and maps each finding to the current module and prior modules.
3. The teacher can resolve, reorder, remap, or document a waiver; the application does not silently auto-change curriculum or block access without review.
4. The same coverage result is available from a tested PostgreSQL/canonical projection during Neo4j outage.
5. An integration test proves that a mapped advanced KC produces a coverage warning until its prerequisites are mapped to earlier modules.

### Priority 1 — make misconception and cohort diagnosis traceable, not merely labeled

**Proposal:** When PostgreSQL similarity identifies a misconception, resolve and persist its actual validated primary KC instead of `"unmapped"`. Then aggregate verified tutor/event records by KC and prerequisite dependency. Do not fabricate historical coverage or static student scores.

**Rationale:** The current tutor and distractor flows use PostgreSQL, which is acceptable, but their `kc_id` values are not reconciled to the graph. The cohort UI cannot presently distinguish a real concept pattern from a string in a payload. [10] [11] [18]

**Acceptance criteria:**

1. A `misconception_flagged` event contains a validated KC ID and catalog version when a match is used.
2. Cohort diagnostics show only recorded data, clearly separate sample data, or show an empty state.
3. An educator can navigate from a KC concentration to the relevant assignments, modules, sources, and individual traces.
4. No intervention dispatch is automatic; the interface provides a reviewable teacher action and records its rationale.

### Priority 2 — make graph lifecycle and integrity real

**Proposal:** Introduce an explicit graph/catalog version and reconciliation job that validates seed input before mutation, creates or deletes nodes/edges to match the catalog, verifies all referenced relational IDs, detects cycles without a fixed length cap, checks isolation, and produces a machine-readable integrity report. Validate query depth within the service before constructing Cypher.

**Rationale:** Manual upserts leave stale data and cannot prove schema-to-catalog equivalence. Acyclicity alone is insufficient to support instructional sequencing. [4] [2]

**Acceptance criteria:**

1. A reproducible read-only integrity command reports node/edge count, catalog version, orphan KCs, missing prerequisite targets, stale nodes/edges, invalid relational IDs, and cycle status.
2. Seed validation fails before writes when a prerequisite target is absent or metadata is invalid.
3. Cycle detection has no arbitrary path-length blind spot.
4. The graph service validates `depth` independently of FastAPI bounds.
5. Integration tests cover a healthy graph, a Neo4j outage, stale/missing IDs, an orphan, and a cycle.

### Decision gate: retain or simplify Neo4j

**Proposal:** Retain Neo4j only if the Priority 1 prerequisite-coverage slice is delivered with the stated outage fallback and demonstrated educator use. The operational cost is then paid by a query that a recursive relational projection may still replicate; continue to retain Neo4j only if planned graph scale, relationship richness, or traversal complexity exceeds the PostgreSQL alternative in measured production usage.

Otherwise, simplify. Materialize `knowledge_components` and `kc_prerequisites` in PostgreSQL from the canonical JSON, add a validated foreign-key-like catalog contract for stored IDs, implement recursive prerequisite/coverage queries there, and delete the Neo4j container, dependencies, client, seed branch, graph-only endpoints, and display-only UI. This gives the MVP a single durable operational store for course, learner, assignment, and curriculum decisions.

## Recommended first implementation slice

The recommended first slice is **“Prerequisite Coverage Before Module Publication.”** It deliberately avoids automated mastery claims. A teacher chooses or confirms KCs for each module. When publishing or reviewing a module, the backend identifies every direct and transitive prerequisite absent from earlier modules. The UI says, for example, “This module targets *Declaration of the Rights of Man*, which requires *Tennis Court Oath* and *Popular Sovereignty*. Neither is covered by an earlier module,” and links to those modules and KCs. The teacher may remap, reorder, add material, or document a waiver.

The implementation should first run against a canonical catalog projection and must return the same explanation when Neo4j is unreachable. Neo4j may serve the traversal implementation after parity is established, but the user experience must not depend on it. This slice provides an observable, pedagogically cautious decision and creates the mapping data needed for later learner-readiness and cohort analyses.

## References

[1]: https://github.com/darkaengl/fiosra/issues/43 "Issue #43: Knowledge Graph Utility, Data Model, and Educator UX Audit"
[2]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/graph_service.py "GraphService: Neo4j curriculum graph queries and schema setup"
[3]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/neo4j_client.py "Neo4jClient: asynchronous driver lifecycle and health check"
[4]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/seed_pipeline.py "Dual-database seed pipeline and PostgreSQL misconception search"
[5]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/knowledge_components_curriculum.seed.json "Knowledge component curriculum seed catalog"
[6]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/migrations/001_initial_schema.sql "Initial PostgreSQL course, misconception, assignment, and event schema"
[7]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/migrations/002_syllabus_chunks.sql "PostgreSQL syllabus chunks schema with nullable kc_id"
[8]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/ingestion.py "SyllabusParser graph lookup, fallback, lexical KC matching, and persistence"
[9]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/generator.py "AssignmentGenerator source KC use and target-KC construction"
[10]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_router.py "Dialogue event logging and unmapped misconception KC payload"
[11]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/service.py "CourseService module sequencing and cohort roster aggregation"
[12]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/knowledge_router.py "Knowledge Layer API routes"
[13]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_graph_service.py "Graph service, traversal, frontier, latency, and API tests"
[14]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_database_foundation.py "Neo4j configuration, singleton, health, and migration tests"
[15]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/KnowledgeGraph.svelte "Static Knowledge Graph Svelte route"
[16]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/Modules.svelte "Modules route and cohort roster integration"
[17]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/routes/CohortDiagnostics.svelte "Static Cohort Diagnostics Svelte route"
[18]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/lib/CohortRoster.svelte "Cohort roster component"
[19]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/lib/AppHeader.svelte "Application header and fixed graph status chip"
[20]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/docker-compose.yml "Docker Compose Neo4j provisioning and application dependency"
[21]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/main.py "FastAPI lifespan and health endpoint"
[22]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_engine.py "Dialogue engine PostgreSQL misconception search path"
[23]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/misconceptions_language_history.seed.json "Language and history misconception seed catalog"
[24]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/knowledge/seeds/misconceptions_algebra_geometry.seed.json "Algebra and geometry misconception seed catalog"
[25]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/courses/schemas.py "Course input and response schemas including domain default"
[26]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/src/App.svelte "Svelte route registration"
[27]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/frontend/vite.config.js "Vite build output and development proxy configuration"
