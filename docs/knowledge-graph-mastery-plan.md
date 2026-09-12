# Course Concept Graph → Student Mastery Overlay: Design Plan

Status: draft, grounded in code at commit `fd18bea` (branch `feat/fix-student-page`).
Author: brainstormed with Claude, written up 2026-09-12.

## 0. What already exists (don't rebuild this)

The repo already has most of the "course knowledge graph" half of this feature, just not
wired to student mastery yet.

- **`fiosra/mvp/concepts/`** (Neo4j, course-scoped) is the real course concept graph:
  `Course -[:HAS_CONCEPT]-> Concept`, with two *deliberately separate* edge types —
  `CONTAINS` (hierarchy: course_theme → strand → topic → subtopic → atomic_concept) and
  `PREREQUISITE_OF` (dependency ordering). This is exactly the split described in the
  brainstorm (derivative → chain rule → sigmoid → ... as a *prerequisite* DAG, not a
  strict parent/child tree). Cycle validation runs both in-proposal
  (`_validate_proposal`) and at DB write (`_validate_relation`). AI proposes via
  `generate_proposal`, teacher approves via `approve_proposal` — keep this pattern.
  `Module -[:INTRODUCES|DEVELOPS|ASSESSES]-> Concept` already links curriculum modules
  to concepts, and `SourceChunk -[:EVIDENCES]-> Concept` already links ingested source
  material to concepts.
- **`EvaluationCriterionMap.concept_ids`** (`assignment_designer/schemas.py:112`) already
  tags a rubric criterion to concept ids, populated in `generator.py:384` from
  `target_kcs`. This is teacher/agent-only (`AutoScoreEvaluationPlan`, never sent to the
  student), matching invariant #1 (Strict Answer Isolation).
- **`PublicQuestionSpec.target_kcs`** (excluded from the student-facing projection)
  already threads concept ids through the dialogue engine and Socratic probes
  (`dialogue_engine.py:88`, `socratic_probe_service.py:911-935` — the latter already
  queries `Concept {concept_id: kid}` and walks `PREREQUISITE_OF` for tutoring context).

**Decision needed and made here: the course-scoped `Concept`/`PREREQUISITE_OF` graph in
`concepts/` is the canonical knowledge graph for this feature.** There is a second,
older, domain-wide graph — `graph_service.py`'s `KnowledgeComponent`/`REQUIRES` nodes
(seeded by `seed_pipeline`/`seed_hi4083_curriculum.py`, exposed at `/knowledge`,
including an existing `get_learning_frontier(mastered_kc_ids)` that already does
frontier-style mastery traversal). It is **not** course-scoped and is a different node
label from `Concept`, so `KnowledgeComponent.kc_id` and `Concept.concept_id` are two
incompatible id spaces even though both get called "kc_id" in different files. Building
mastery on both would silently attach data to the wrong graph half the time. Treat
`graph_service.py`/`/knowledge` as legacy scaffolding: keep it running (misconceptions
still FK to it via `misconceptions.kc_id`), but do not extend it — new work targets
`Concept` only. Reconciling or retiring `KnowledgeComponent` is a separate cleanup, out
of scope here.

## 1. The actual gap: grading is holistic, not per-criterion

This is the one finding that changes the shape of the plan. `POST
/evidence/dossier/{session_id}/finalise-grade` (`evidence_dossier/router.py:112-134`)
takes `FinaliseGradeRequest{approved_grade: str, teacher_id, teacher_override,
feedback_comments}` — a single holistic grade. There is no per-rubric-criterion outcome
anywhere in `session_events`. `EvaluationCriterionMap.concept_ids` tells you *which*
concepts a criterion probes, but nothing today records whether the student actually met
that criterion. **You cannot compute a mastery score without first capturing a
per-criterion outcome at grading time.** Everything below is designed around adding
that, additively, without touching the holistic grade path.

## 2. Data model

Keep Neo4j for topology only (nodes + edges, teacher-governed, slow-changing) and
Postgres for mastery (a quantitative, event-derived, fast-changing materialized view).
Don't create `Student` nodes in Neo4j or duplicate identity across both databases —
mastery rows key on `(student_id, course_id, concept_id)` and join against Neo4j
topology at read time.

Per invariant #4 (append-only event store; state derives purely from replaying
`session_events`), `concept_mastery` is a **cache**, not a second source of truth: it's
fully recomputable by replaying `grade_finalised_by_educator` events, never hand-edited.

```sql
-- migrations/009_concept_mastery.sql
CREATE TABLE IF NOT EXISTS concept_mastery (
    student_id            VARCHAR(64)  NOT NULL,
    course_id             UUID         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    concept_id            VARCHAR(96)  NOT NULL,  -- Neo4j Concept.concept_id (cross-db, not FK'd)
    state                 VARCHAR(16)  NOT NULL DEFAULT 'unassessed', -- unassessed|weak|developing|strong
    score                 NUMERIC(4,3) NOT NULL DEFAULT 0,            -- 0.000-1.000 deterministic composite
    evidence_count        INT          NOT NULL DEFAULT 0,
    last_evidence_at      TIMESTAMPTZ,
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (student_id, course_id, concept_id)
);
CREATE INDEX idx_concept_mastery_course  ON concept_mastery (course_id);
CREATE INDEX idx_concept_mastery_student ON concept_mastery (student_id, course_id);
```

Scoring is **conservative / direct-evidence-only for v1**: a concept is only ever
`weak`/`developing`/`strong` if a rubric criterion tagged with that concept id was
actually graded. Everything else stays `unassessed` (rendered dim-grey, distinct from
"assessed and weak" which is a different, more actionable signal for the educator).
Inferential propagation (backprop strong ⇒ infer chain-rule probably-fine) is a **v2**
idea — it needs a real confidence model (Bayesian Knowledge Tracing-style) and the MVP's
own stated ethos is deterministic-over-inferred (invariant #2). Don't ship a guess
dressed up as a measurement.

`outcome → score`: `met` = 1.0, `partially_met` = 0.5, `not_met` = 0.0. `score` is a
running weighted average over `evidence_count`; `state` buckets from the current score
once `evidence_count > 0`: `< 0.4` weak, `0.4–0.75` developing, `> 0.75` strong.

## 3. Grading path extension (additive)

`FinaliseGradeRequest` gains an optional field:

```python
class CriterionGradeInput(BaseModel):
    criterion_id: str
    outcome: Literal["met", "partially_met", "not_met"]

class FinaliseGradeRequest(BaseModel):
    approved_grade: str
    teacher_id: str = "teacher_sovereign_01"
    teacher_override: bool = False
    feedback_comments: str = ""
    criterion_grades: list[CriterionGradeInput] = []   # NEW, optional — old callers unaffected
```

`finalise_student_grade` logs `criterion_grades` into the *existing*
`grade_finalised_by_educator` event payload (no new event type — keeps the replay model
simple) and then calls `concept_mastery_service.recompute_for_session(session_id)`,
which:

1. Loads the assignment's `evaluation_plan.public_rubric_map` (via
   `assignment_generator.get_authoring_assignment`) to resolve `criterion_id →
   concept_ids`.
2. Resolves `course_id` via the existing `assignments a JOIN modules m ON
   a.module_id = m.module_id` join pattern used elsewhere
   (`courses/service.py:401`, `courses/ingestion.py:413`).
3. For each graded criterion, for each tagged concept id, upserts one
   `concept_mastery` row (running average, as above).

Educators can still finalize a grade with `criterion_grades: []` (today's behavior) —
mastery simply doesn't move for that session. This makes the feature opt-in per
assignment/educator rather than a breaking change to the grading contract.

A `rebuild_course(course_id)` admin path replays every session's latest
`grade_finalised_by_educator` event for that course from scratch — the concrete
expression of "derives purely from replaying session_events," and the fix if scoring
logic changes later or a concept gets re-tagged.

## 4. API surface

New router, mounted under the existing concept-graph prefix
(`/courses/{course_id}/concept-graph/mastery`) rather than a new top-level path, since
it's a view over the same graph:

- `GET .../mastery/students/{student_id}` — merges Neo4j topology
  (`concept_graph_service.get_course_graph`) with that student's `concept_mastery` rows;
  concepts with no row come back `state: "unassessed"`. This is the payload the "light
  up / dim" visualization renders directly — nodes carry their own state, edges are
  unchanged from the base graph.
- `GET .../mastery/cohort` — same shape, but each node carries a distribution
  (`{strong: 12, developing: 5, weak: 2, unassessed: 3}`) across enrolled students
  instead of one state. This is the real replacement for the known-gap "static fake
  cohort heatmap."
- `POST .../mastery/rebuild` — recompute-all, teacher/admin only.

## 5. Frontend (not built in this pass)

`frontend/src/routes/KnowledgeGraph.svelte` is currently orphaned (per the known-gaps
audit — dropped after a nav merge). Revive and repurpose it rather than starting a third
graph component: render the `concept-graph` topology (hierarchical layout keyed off
`level`, e.g. dagre/elkjs), add a student picker that calls the `mastery/students/{id}`
endpoint and recolors nodes by `state` (strong = lit/saturated, developing = medium,
weak = dim-warm, unassessed = greyed-out), and a cohort toggle that renders the
distribution instead. This is a separate, sizeable Svelte task — flagged as the next
step, not attempted here.

## 6. Extensions to revisit once v1 ships

- Misconception nodes (`(Misconception)-[:CONFOUNDS]->(Concept)`) so a dim node carries
  *why*, not just *that* — ties into the already-tracked
  `misconceptions_triggered`/`autonomy_rating` field-name bug in
  `evidence_dossier/synthesizer.py` vs `router.py`, worth fixing alongside this.
- Gap-path recommendation: walk `PREREQUISITE_OF` backward from a weak leaf to find the
  root cause instead of showing a wall of dim nodes.
- Cross-course concept reuse via pgvector dedup, so mastery carries forward across
  courses instead of starting cold.
- Temporal replay of a student's graph over the term (invariant #4 makes this nearly
  free once v1 exists — it's the same recompute, run against a truncated event window).

## 7. Sequencing

1. Migration `009_concept_mastery.sql`.
2. `FinaliseGradeRequest.criterion_grades` (additive) + `concept_mastery` package
   (`schemas.py`, `service.py`, `router.py`) + wire into `main.py`.
3. Frontend: revive `KnowledgeGraph.svelte` with the mastery overlay.
4. Cohort view replacing the fake heatmap.
5. v2: misconception nodes, inferential propagation, gap-path recommendation,
   cross-course reuse.

## 8. Flag before shipping

Every educator router, `concepts/` included, has zero auth today (known gap, re-audited
2026-09-11). The mastery endpoints expose individual students' per-concept performance —
more sensitive than most existing educator data. Don't let this be the router that ships
first without at least a minimal auth check; the broader fix can land after, but this
one shouldn't widen the unauthenticated surface on student-identifiable data.
