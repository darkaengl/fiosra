# Educator Experience Refinement Plan

**Author:** Manus AI  
**Assessment mode:** Hands-on teacher walkthrough of the local Fiosra UI  
**Scope:** Course setup, curriculum sequencing, source grounding, assignment authoring, student launch, and educator review

## Executive conclusion

Fiosra presents a distinctive and promising teacher proposition: an educator designs a reasoning task, grounds it in course material, exposes only a bounded Socratic scaffold to students, and later reviews a trace of their thinking. The interface already communicates that proposition clearly in several places. Course and module creation are approachable, the assignment designer makes answer isolation understandable, and the review screen correctly positions the educator as the final decision-maker.

However, the educator experience cannot yet be trusted for a real class. During a live walk-through, a Mohenjo-daro assignment generated French Revolution content even after the educator supplied corrected context. A module then displayed a published assignment whose student-canvas link could not load the assignment. The review queue simultaneously showed an empty state and a server failure. These are **release-blocking workflow integrity defects**, not surface-level usability concerns. The product should prioritize making the displayed pedagogical data true, traceable, and launchable before adding further dashboard features. [1] [2]

> **Primary design principle:** In a teacher-facing reasoning product, every instructional recommendation, status badge, count, and student launch link must be traceable to the selected course, module, source corpus, and server-side record.

## Walkthrough performed

The assessment created a local History course called **HIST-275: Cities, Evidence, and Historical Argument**, added a first module focused on reading urban infrastructure as evidence, and pasted a short Mohenjo-daro drainage excerpt as a primary source. The flow then used the module’s assignment entry point to design a source-grounded historical argument. The educator intentionally did not publish the generated draft because its preview was demonstrably unrelated to the course. The walkthrough next opened an existing published assignment and attempted the student-canvas and review-queue handoffs. [1]

| Journey stage | What worked | What prevented confident classroom use |
|---|---|---|
| Course creation | A compact modal captured title, domain, instructor, and syllabus context. The new course appeared immediately. | Course code was inferred as `HIST-002` rather than preserved; dashboard totals mixed a live course count with unrelated cohort, session, and review numbers. |
| Curriculum setup | Empty state, first-module action, and basic module details were clear. | The UI promises a prerequisite graph without allowing prerequisite, KC, sequence, release, or readiness configuration. |
| Source grounding | A pasted source returned to the module and was visibly labeled as grounded. | The educator sees no evidence of which chunks or KCs were inferred, no confidence signal, no override, and a destructive one-click delete control. |
| Assignment design | The form preserves course/module context and requires a scope check before generating a scaffold. | The system recommends and generates a French fiscal-crisis task for a Mohenjo-daro assignment; the generated KCs, hints, and rubric are not course-aware. |
| Student handoff | Published task cards expose a student-canvas entry point. | The linked student workspace failed to load the advertised assignment, so the student cannot begin. |
| Educator review | The layout and teacher-final-authority framing are strong. | The route returned a failure while displaying a zero-item empty state, creating an ambiguous and untrustworthy result. |

## Priority 0 — Restore pedagogical and workflow integrity

### 1. Replace the French-specific scaffold template with contextual task generation

The scaffold generator currently builds a French fiscal-crisis task, target KCs, hints, rubric rules, subproblems, and reference-solution defaults regardless of the selected course. The current request values can be interpolated into that template, but they do not change its subject matter. This behavior directly caused the Mohenjo-daro assignment to return references to royal debt, Marie Antoinette, the Estates-General, and French KCs. [2]

The replacement should derive the task from the selected **course ID, module ID, source resources, learning objectives, selected KCs, and teacher prompt**. Retrieval must be constrained to that module’s corpus before any generation occurs. Each generated task, hint, rubric criterion, and misconception should retain source-resource IDs and KC IDs as provenance. If no adequate source or KC exists, Fiosra should clearly offer a generic draft mode rather than imply that a grounded recommendation is authoritative.

| Acceptance criterion | Required behavior |
|---|---|
| Course relevance | A generated task cites only sources and KCs assigned to the selected course/module, unless the teacher explicitly opts into generic mode. |
| Explainability | The preview identifies the source excerpts, objectives, and KCs used for every instructional recommendation. |
| Contradiction prevention | Publishing is blocked when the module, source corpus, and generated KCs have no validated relationship. |
| Teacher control | The teacher can regenerate or directly edit the clarified prompt, individual hint rungs, and rubric criteria before drafting. |
| Regression safety | Add a Mohenjo-daro test that rejects any generated reference to the French fiscal-crisis vocabulary or French-only KCs. |

### 2. Establish one canonical published-assignment contract

A teacher must not be able to see a “published” status or a student-canvas link unless that exact assignment can be loaded through the student-safe assignment endpoint and can create a session. The walk-through found a published card that linked to a workspace error. That defect means the module projection and student-assignment projection are not reliably representing the same durable record. [1]

The assignment lifecycle should be explicit: **draft → validation pending → ready to publish → published → archived**. The server should own every transition. The module card should render the current status from the same public projection consumed by the student page. A pre-publish validation request should validate schema completeness, Answer Vault isolation, module binding, resource readiness, public retrieval, and a simulated student-session initialization.

| Acceptance criterion | Required behavior |
|---|---|
| Single source of truth | Module cards, educator preview, student workspace, and review queue refer to a shared assignment ID and status. |
| Launchability | A published assignment returns HTTP 200 via the public projection and a session can be opened for a permitted student. |
| Safe preview | “Preview as student” invokes the same data endpoint and session creation pathway as a student launch. |
| Actionable failure | If publication validation fails, explain the missing record or dependency in the designer; do not render a launch link. |
| Regression safety | Browser integration test: create, validate, publish, open student canvas, submit, and confirm review-queue visibility. |

### 3. Fix review-queue request typing and error-state truthfulness

The review queue returned an HTTP 500 for a filtered course request. The server output identifies an async PostgreSQL ambiguous parameter-type error in the optional course ID condition. The visible UI then showed both an empty queue and a fetch failure. [1]

The API query should use an explicit type-safe parameter expression, and the front end must distinguish a confirmed zero-result response from a failed request. A failure should not report “Awaiting review 0” or “Nothing is waiting for review.” Instead, it should show a retry action, non-sensitive diagnostic ID, and a message that the result could not be determined.

## Priority 1 — Make the course-design experience teacher-legible

### 4. Separate course identity, course setup, and operational metrics

The course-creation modal combines a code and title in one field, then the curriculum breadcrumb displays an inferred code that is not the code supplied by the teacher. The dashboard also mixes an updated active-course count with fixed cohort, session, and review metrics. This makes it impossible to tell which figures are live, which are course-scoped, and which are illustrative. [1]

The creation workflow should ask for separate **course code**, **course title**, **term**, **lead instructor**, **section/roster source**, and **student visibility** fields. The confirmation should show the durable course ID and guide the teacher toward the next required setup step. Analytics cards should be bound to a selected course and term, include a visible refresh timestamp, and use an explicit “example data” treatment wherever data has not yet been connected.

### 5. Turn the module form into a sequencing and readiness workspace

The existing module form successfully captures title, scope, and comma-separated objectives, but it cannot create the prerequisite structure promised by the “Prerequisite DAG” label. The system should make a module’s pedagogical dependencies tangible rather than ask teachers to infer them from position alone.

The revised form should use editable objective chips and provide suggestions for KCs and Bloom’s level. It should let teachers choose prerequisite modules and KCs, display a cycle-safe visual sequence, and define release rules. The module page should display a setup checklist: objectives mapped, resources grounded, assignment draft ready, student preview verified, and release configured. That checklist creates a useful stopping rule before publication.

### 6. Make source grounding auditable and safe to edit

“Grounded” is meaningful only if the teacher can see what grounding means. After ingesting a source, the interface should show bibliographic or attribution metadata, text chunks, mapped KCs, confidence, and the ability to approve, adjust, or reject a mapping. The copy should describe instructional benefit—such as “students can cite this in their argument”—rather than foregrounding embedding dimensions and database technology.

Deleting a grounded source should be a two-stage action. The confirmation must list affected assignments, published tasks, and student citations. It should offer a short undo window where possible and preserve historical evidence for already submitted work.

## Priority 2 — Improve authoring clarity and student experience continuity

### 7. Redesign the scope interview around teacher intent

The scope-analysis interaction is valuable, but it needs to begin with the teacher’s intent rather than a presumed content template. The questions should be phrased in instructional terms: **What should students be able to claim? What evidence are they required to use? Which incomplete or misleading inference should the scaffold help them confront? What historical or conceptual boundary matters?** The defaults must come from the selected module or be marked as generic suggestions.

The preview should be editable in place and display a short “coverage panel” that relates the task to objectives, sources, KCs, and assessment criteria. The educator should be able to compare a student-safe prompt with an educator-only reference model without exposing the latter in the student route.

### 8. Replace static learner screens with route-aware, student-specific data

The student-home code currently includes a fixed learner name, course, progress, task, mastery pattern, and date. That approach can be useful for a design prototype but breaks trust when it appears adjacent to live course routing. The home, timeline, canvas, and trace should all consume the authenticated student identity and selected course. [3]

A student needs a reliable task list, a plain-language explanation of why an assignment is available or locked, the assigned sources, autosave visibility, session recovery, and a clear trace-submission confirmation. The tutor should keep its bounded hint behavior, but each rung should tell learners what type of support it offers and should never imply they are being graded automatically.

### 9. Prepare the review queue for actual teacher workload

Once data loading is reliable, the review queue should support assignment, learner, submission-time, state, and risk filters. The default order should make instructional triage clear: submissions with high misconception signals, low autonomy, or upcoming deadlines first. A teacher should be able to save feedback, return work for revision without finalizing, and compare a current trace with prior submissions while preserving the append-only record.

## Recommended implementation order

The first increment should solve the data-contract defects before modifying the visual design. Correct content and truthful state are the prerequisite for teacher confidence.

| Sequence | Scope | Outcome |
|---|---|---|
| 1 | Repair scaffold generator and scope defaults | Generated prompts, hints, KCs, rubrics, and distractors are relevant to the selected module or visibly generic. |
| 2 | Repair assignment lifecycle/projections | Published module cards and student links refer to a verified, student-safe durable assignment record. |
| 3 | Repair review query and front-end request-state model | Educators get either a trustworthy queue or an explicit recoverable error state. |
| 4 | Add end-to-end browser coverage | The core author → publish → student → submit → review journey is mechanically protected from regression. |
| 5 | Redesign setup, grounding, and readiness guidance | Educators gain transparent, course-aware tools for curriculum sequence and source governance. |
| 6 | Replace static learner and dashboard data | All visible counts, learner details, and progress indicators communicate their provenance and scope. |

## Suggested end-to-end acceptance scenario

An educator creates a course with an explicit code and term, creates a module, maps objectives to KCs, attaches a source, and verifies the source-to-KC mapping. The educator then writes a prompt and receives only source-cited, module-aligned task suggestions. Before publishing, Fiosra runs a student-safe preview and validates that the public assignment can load and open a session. A student launches the same task, submits reasoning and a trace, and the educator sees a reliable review-queue entry. The educator can offer feedback, request revision, or finalize an outcome. At every point, the UI distinguishes current live data from examples or unavailable data.

## Assessment limitation

This assessment used a local development database and intentionally did not publish the obviously incorrect Mohenjo-daro scaffold. The student and review paths were tested from their visible UI entry points but could not be exercised to completion because the linked assignment failed to load and the filtered review endpoint failed. These failures are themselves central findings, and the recommended browser acceptance scenario should be implemented before any private or public pilot.

## References

[1]: teacher-ux-walkthrough-notes.md "Local educator UI walkthrough observations"
[2]: https://github.com/darkaengl/fiosra/pull/38/files "Fiosra PR #38 source changes and validation"
[3]: https://github.com/darkaengl/fiosra/blob/main/frontend/src/routes/StudentHome.svelte "StudentHome Svelte route"
