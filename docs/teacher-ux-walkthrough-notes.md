# Educator UI Walkthrough Notes

## Course portfolio and creation workflow

The educator portfolio makes the course-management entry point visible and the course-creation modal is understandable. The modal collects title, domain, instructor, and optional syllabus context in one focused surface.

Observed opportunities include the discrepancy between the portfolio metrics and the current data context. The page labels course count as “Live Synced” and reports cohort, sessions, and review totals that do not appear tied to the newly created course. The course title field combines code and title, which complicates consistent naming, sorting, and later integration with an SIS or LMS. The modal also tells an educator that the workspace will be initialized in PostgreSQL and Neo4j without explaining what the system will infer, validate, or create. It does not preview duplicate-course handling, draft state, privacy/access options, term dates, roster source, or success next steps.

These observations are provisional and will be combined with the curriculum, assignment-authoring, tutor, and review walkthroughs in the final report.

## Course creation outcome

The local educator course was created successfully and appeared at the start of the portfolio. The active-workspace total and domain-filter total updated from 34 to 35. The immediate result is therefore technically clear through the reordered card list, but the interaction provides no explicit success message, no confirmation of the generated course identifier, and no direct post-create decision such as “add first module,” “ingest syllabus,” or “invite students.”

The result also exposed a trust issue. The live course total changed, while the “Total Enrolled Cohort,” “Live Socratic Sessions,” and “AutoSCORE Review Queue” cards remained fixed at 86, 14, and 4. For a teacher, the mixed presence of live and illustrative data makes it unclear whether the dashboard can be relied upon for classroom decisions. The refinement should distinguish actual metrics from empty-state examples and scope any metric to the selected course or term.

## Curriculum workspace and module setup

The new course opens to a clean empty state with clear calls to action for the first module and a co-pilot assignment. The module dialog is also compact and easily understood for a simple linear unit: title, scope, and comma-separated objectives.

However, the course breadcrumb displays `HIST-002`, not the course code supplied by the teacher. The workspace simultaneously says “3 enrolled students” even though no roster was entered. That is a severe data-provenance problem in a teacher-facing product. More broadly, the user interface calls the relationship model a “Prerequisite DAG” and promises that modules unlock concepts in Neo4j, but the module form has no way to select prerequisite modules or knowledge components, show a sequence, visualize dependencies, or validate cycles. The current form can create a flat sequence only. Comma-separated objectives are acceptable for a prototype, but should become individual editable objective chips with suggested knowledge-component mapping, competency level, and observable evidence.

## Module creation outcome

The module was created successfully and the curriculum screen immediately displayed its title, scope, position, objectives, resource count, and assignment empty state. This confirms the workflow reaches a usable module surface without a page reload.

The main weakness is that the UI still reports only a generic “Active • Position 1” rather than showing intended learning time, release criteria, student visibility, prerequisite connections, assignment readiness, or grounding coverage. A teacher designing a sequence needs a distinct setup-completion state. The best next action is visually present, but two simultaneous resource calls to action create duplication. The individual module should instead expose a guided checklist: objectives mapped, at least one source attached, first task drafted, teacher preview completed, then publish.

## Source grounding outcome

Pasting an excerpt worked and the material was returned to the module card as a primary source with a “Grounded” label. The direct presentation of stored source text is a good basis for a teacher to audit what students can cite.

The ingest experience currently describes implementation details—“1536-dim pgvector” and Neo4j grounding—rather than teacher outcomes. It does not preview extracted chunks, citation metadata, copyright or license fields, reading-level information, source provenance, or the inferred knowledge-component link. A “Grounded” badge without a visible KC mapping, confidence score, or manual override is not sufficiently explainable. The visible single-character delete action is also risky for instructional materials: it needs an explicit confirmation, undo window, and source-impact warning explaining which assignments and student citations would be affected.

## Assignment analysis outcome

The Assignment Scaffold Designer preserves the selected course and module context. It asks the teacher to analyze the prompt before scaffold generation, which is pedagogically defensible and gives a teacher an opportunity to specify scope, expected evidence, and common misconceptions.

The content of the analysis was materially wrong for the assignment. The teacher’s Mohenjo-daro task was classified against pre-revolutionary France, Marie Antoinette, and Necker’s Compte Rendu. This indicates a stale or hard-coded default alignment dataset rather than analysis grounded in the selected module and attached source. A teacher cannot safely proceed when the system’s first instructional recommendation is demonstrably unrelated to their course. The refinement is critical: use source-aware retrieval limited to selected course/module resources, surface a “why this recommendation” citation, label any generic fallback, and provide an easy “start fresh” control. Scaffold generation must be disabled when detected recommendations have no source-to-course match.

## Scaffold generation outcome

Even after the teacher replaced all three inappropriate alignment values, the generated clarified task, knowledge components, hint ladder, and rubric remained about the French fiscal crisis. The only changed text was the pasted evidence-anchor phrase inserted into an otherwise French-specific template. The displayed output is polished enough that a busy teacher might miss the mismatch and publish a flawed task. This is the most serious observed experience defect because it converts an internal relevance failure into harmful student-facing content.

The generator needs to be changed from a domain-specific template with variable substitution to a course-aware generation pipeline. The preview needs an explicit validation panel before Save or Publish, including source resource citations, module and KC match checks, a semantic contradiction warning, and a teacher-controlled regenerate/edit action at the level of each task, hint, and rubric item. Until every output is traceable to the course corpus, the publish action should be blocked rather than merely allowing the teacher to spot a mismatch manually.

## Published assignment entry point

The seeded course curriculum makes the published assignment status and student-canvas launch link visible on the module. This is a strong use of the module as the handoff point between course design and student experience.

The evidence dependency is not enforced in the teacher-facing readiness state. The module reports zero grounded sources while the published Fiscal Crisis Essay sends a student into a source-based reasoning space. The product should show an explicit readiness policy—such as “publishable with no source corpus” only if the task is intentionally source-free—and should identify any required resource that a student will actually see. The assignment card also needs due date, estimated duration, attempt policy, student release state, and a teacher preview action before publication.

## Student tutor handoff outcome

Selecting the published Fiscal Crisis Essay from the curriculum opened the student shell but immediately showed “Workspace unavailable: The requested assignment could not be loaded.” This is a blocker, not merely a usability concern: the teacher-facing module displays a published assignment and a student-canvas link that resolves to an assignment identifier with no corresponding public assignment record. The student cannot begin a reasoning session.

The browser showed no client-side console error, and the server returned an HTTP 404 for the linked assignment. This is consistent with the teacher module presenting assignment data that is not available through the student-safe assignment endpoint. The product needs one canonical assignment projection and integration contract. Before a module can show “published” or render a student link, an API check must confirm a public student spec is present, answer-isolated, and launchable. The UI should then offer a pre-publish student-preview test that uses the same endpoint and session initialization that students use.

Separate static-code review confirms a further trust risk: the student home route is currently populated with fixed Julian/HIST-201 sample data rather than the selected course and student’s session data. Cohort and grade-review interfaces should likewise make current course scope and data provenance explicit rather than mixing live and example content.

## Educator review queue outcome

The AutoSCORE review route has a well-structured empty-state layout and correctly communicates the intended educator role: evidence supports a decision rather than replacing it. However, the page simultaneously claims that nothing is awaiting review and displays “The educator review queue could not be loaded.” Refresh produced the same result. The interface must never combine an error with a factual empty-state assertion, because a teacher cannot know whether no work exists or the system has failed.

The refinement is to distinguish reliable empty, loading, partial, and failed states. On a failed fetch, hide the zero count and empty queue claim, explain whether existing cached data may be stale, present a diagnostic request ID for support, and offer retry. More fundamentally, the review queue should have a course selector and visible filters for assignment, submission time, learner, status, and rubric risk so that a teacher can manage real classroom volume.
