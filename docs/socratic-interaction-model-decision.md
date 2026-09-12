# Unified Socratic Interaction Model Decision

**Status:** Accepted
**Date:** 2026-09-12
**Scope:** Student writing experience, Socratic Enquirer, probe lifecycle, and AutoSCORE evidence collection

## Decision

Fiosra will use **one student-facing Socratic interaction model: the student-initiated Socratic Enquirer**. The former proactive-background-probe workflow will **not** remain a second visible question system.

Background analysis remains useful, but only as a quiet **opportunity detector**. It may identify a sentence or section where support could be valuable, but it must never interrupt the student, open a panel, create a required response, or imply that a learner must defend a claim before continuing their work. The Socratic Enquirer is the sole interface through which a learner elects to explore an idea, request help, or add an agent-proposed writing structure.

> **Core principle:** Fiosra helps learners complete a rigorous assignment through voluntary, contextual dialogue. It does not turn drafting into a sequence of compulsory claim-defense checkpoints.

## Why this model

The existing hybrid model presents two overlapping concepts of assistance. The earlier lifecycle automatically persists paragraph-bound questions after a quiet period. The newer Enquirer lets a learner select a sentence or start a general inquiry, choose a mode, use a slash command, and accept optional canvas actions. Both can appear to assess the same prose, but they have different triggers, terminology, persistence behavior, and expectations.

Keeping both systems visible would make the writing experience harder to predict. A student could see a highlighted sentence, a pending probe count, an evidence prompt, and an independent Socratic chat around the same passage. This undermines the intended writer-first experience and makes the completion path feel evaluative rather than supportive.

The Enquirer is the better primary interaction because it preserves agency, keeps support connected to the learner's immediate purpose, and can evolve from sentence-level questioning into planning, source use, outlining, counterargument, and revision support. Background signals should support that interface rather than compete with it.

## Target behavior

| Concern | Unified behavior | Explicitly excluded behavior |
|---|---|---|
| **While the learner writes** | Local, low-cost signals may subtly mark passages that could benefit from inquiry. The learner can ignore them and continue writing. | No automatic chat opening, modal, side panel, required response, or blocking state. |
| **Opening assistance** | The learner clicks the Socratic Enquirer, selects a highlighted passage, or invokes a slash command. | The system does not force the learner to answer a question before drafting or submitting. |
| **Analysis unit** | The agent works on the selected sentence, passage, heading, source, assignment task, or current writing goal. | The interface does not label every sentence as a compulsory “claim” requiring validation. |
| **LLM invocation** | The backend calls an LLM on learner action for a scoped inquiry, source task, outline request, or revision request. | No LLM call is made automatically for every changed paragraph merely to generate a question. |
| **Agent response** | The Enquirer offers one concise response and, when useful, optional actions such as opening a source, drafting an outline, or inserting a neutral writing frame. | The agent does not write a final answer, silently alter the document, expose the answer vault, or assign a grade. |
| **Teacher evidence** | The system records learner-selected support, accepted assistance, source use, revisions, and the final submission as review evidence. | An ignored or dismissed background signal is not a negative score or an evidence deficit. |

## Operating model

## Emergent Socratic canvas

The current fixed canvas template—**Working claim**, **Source observations**, **Reasoning**, **Alternative explanation**, and **Revision reflection**—is retired. It presupposes a single argumentative workflow before the learner has understood the task, chosen a line of inquiry, or established what form of response is useful. It also duplicates an instructional structure that the published assignment, public rubric, and Socratic Enquirer can provide more appropriately when needed.

The learner's document begins as an intentionally open, minimal canvas. It has no default analytical headings, no placeholder claims, and no pre-created “source observation” sections. The only empty-state affordance is a short invitation to either begin writing or ask the Enquirer for help starting. The published assignment remains available in the Assignment & Materials view; it is not copied into the document as a fixed outline.

> **The published assignment is immutable teacher-authored context. The student canvas is an emergent, learner-owned working document. The helper may propose or apply student-approved edits to the canvas, but it never alters the published assignment.**

### How structure emerges

The Socratic Enquirer and its Canvas Scribe Helper form one coordinated assistance system. The Enquirer first understands the learner's immediate intent. The helper then prepares a bounded, editable canvas operation only when the learner chooses a concrete action.

| Learner situation | Enquirer behavior | Optional helper proposal | Result only after learner acceptance |
|---|---|---|---|
| **Blank canvas** | Asks what part of the task the learner wants to begin with, or offers a concise task/source orientation. | Create a short, task-specific starting plan. | Two or three relevant headings with neutral writing prompts, or one starting paragraph frame. |
| **Learner has a provisional idea** | Helps clarify scope, evidence need, or an alternative interpretation. | Add an evidence question, a comparison point, or a counterargument section. | A new section or note placed at the learner's chosen location. |
| **Learner needs source help** | Helps locate an appropriate assigned source and distinguish observation from inference. | Insert a source note or a citation-ready evidence placeholder. | A clearly attributed source note; never a fabricated quotation or completed analysis. |
| **Learner needs organization** | Reviews the current document and the public task to identify the smallest useful next structure. | Reorder or create headings, split a paragraph, or add a revision checklist. | A reversible document edit with assistance attribution. |
| **Learner is revising** | Uses the public rubric to identify one self-directed next step. | Create a private revision note or a missing-evidence placeholder. | A learner-editable revision aid, not an automated judgment. |

The model must retrieve the relevant assignment task, public rubric, selected source excerpts, current document state, and concept graph context **only for the active request**. It must not indiscriminately send every course material or the complete learner document to an LLM. Source retrieval should be narrow and explainable: the helper receives the specific source or concept context used to justify a proposed canvas operation.

### Minimal interaction design

The target is closer to a Notion editing flow than a dashboard or command center. The canvas remains dominant. The Enquirer is a compact, collapsible contextual conversation rather than a permanently populated right-hand tool catalog.

There must be **one visible path to tools at a time**:

1. A learner opens the compact Enquirer from its single launcher, from a selected passage, or by typing `/` in the Enquirer input.
2. Slash command discovery appears only after the learner types `/`; it is not rendered as a permanent list of sample prompts.
3. Agent actions appear only beneath the response that makes them relevant.
4. The interface removes duplicate fixed quick-action buttons, duplicate sample-prompt cards, and a separate command palette that exposes the same actions.

The result should normally show a short conversation, one useful response, and at most one to three action chips. A long transcript is scrollable and collapsed by default. The editor must retain most of the available width while the Enquirer is open.

### Assistant and helper operation contract

The existing helper must be redesigned from a provider of hard-coded scaffolds into a **validated canvas-operation planner**. It may propose the following operations:

| Operation | Permitted output | Prohibited output |
|---|---|---|
| `create_outline` | Task-specific headings and neutral prompts derived from the active assignment and the learner request. | Default historical headings, a solution outline, or invented facts. |
| `insert_writing_frame` | An empty evidence/reasoning/revision frame that the learner completes. | Finished learner prose, thesis statements, or unverified citations. |
| `insert_source_note` | A sourced observation with attribution and a prompt to explain significance. | A quotation that is not in an approved source or a conclusion about the source. |
| `split_or_reorder_blocks` | A reversible structural change to existing learner-authored blocks. | Deleting learner content without confirmation. |
| `add_revision_note` | A private, editable note tied to one public-rubric criterion. | A score, grade, mastery conclusion, or hidden evaluation rule. |

Every operation returns structured blocks or a block-patch proposal that passes the same ProseMirror and document-revision validation as manual edits. The client presents the proposal with a plain-language summary, and applies it only after the learner accepts. Assisted content is attributed as `student_edited_assistance` once the learner retains or edits it.

### 1. Quiet background opportunity detection

The editor may continue to segment prose and identify broad rhetorical patterns such as a causal statement, unsupported conclusion, source mention, or unresolved task requirement. This work should be deterministic and client-side where feasible. It is a visual affordance and a routing signal, not a judgment.

The editor should use neutral labels such as **Explore this idea**, **Check your evidence**, or **Develop this connection**. It should not present an automatic card as an open probe, an unmet requirement, or a measure of understanding.

### 2. Student-initiated Socratic Enquirer

The Enquirer becomes the only conversation surface. It supports three entry points:

| Entry point | Example learner intent | Agent role |
|---|---|---|
| **Selected writing** | “Help me test this explanation.” | Ask a scoped Socratic question or identify a productive next revision. |
| **Assignment-level inquiry** | “What does the prompt require?” | Clarify task, scope, deliverable, and visible rubric without solving the task. |
| **Command or action** | `/hint`, `/brainstorm`, `/structure`, `/counter`, or `/why` | Provide bounded, answer-blind help and offer optional next actions. |

Each Enquirer turn must be grounded in the published assignment contract and, where relevant, its approved source pack. The agent may recommend an action, but a learner must deliberately trigger any insertion into the canvas.

### 3. Completion-oriented assistance

The assistance system should orient the learner toward the next productive step in completing the assignment. Its default sequence is: understand the task, locate or interpret useful material, form a provisional line of reasoning, organize the response, revise against the public rubric, and submit.

Socratic challenge remains available when a student asks to test an idea. It is one mode of help, not the mandatory path through the assignment.

### 4. Teacher-facing AutoSCORE evidence dossier

AutoSCORE remains a **teacher-facing evidence organizer**, not a live student interrogation engine and not an autonomous grader. It aligns observed work with the published rubric and prepares a reviewable dossier.

The dossier can show the teacher the student’s final work, source engagements, document revisions, learner-initiated Enquirer conversations, learner-accepted canvas support, and rubric-organized evidence. It must clearly distinguish recorded evidence from an inference and from an educator's final judgment.

## Precise implementation boundary

### Retire as a student-facing workflow

The following parts of the earlier proactive-probe lifecycle should be removed from the live student experience:

1. Automatic calls to `POST /learning-documents/sessions/{session_id}/probes/evaluate` after every document quiet period.
2. Pending-probe counts, automatic probe notices, and a separate tutor/probe response panel in `StudentWorkspace.svelte`.
3. Student-facing actions framed as response, defer, or dismiss requirements for a persisted probe.
4. The implication that a sentence needs an evidence response before the student can progress.
5. Automatic LLM classification requests for every edited paragraph when the only result is a question the learner did not request.

### Preserve temporarily for compatibility and auditability

Existing `socratic_probes` and `socratic_probe_responses` records should remain readable in teacher traces. Existing API routes can remain operational during a migration period, but they should not be called by the current student UI. New product development must not depend on them.

A later cleanup can formally deprecate the legacy endpoints after existing sessions are archived or migrated. No historic learner data should be deleted merely to simplify the new interaction model.

### Build around the Enquirer

The live implementation should consolidate around the following contract:

1. **`epistemic-classify` becomes optional analysis.** It returns lightweight, neutral opportunity metadata for a selected passage or an explicitly requested document scan. Its result is not an assignment requirement.
2. **`sentence-inquire` becomes the first scoped assistance turn.** It receives a learner-selected passage, the published task, the relevant source context, and an explicit mode or intent.
3. **`dialectical-turn` becomes the multi-turn assistance endpoint.** It returns a concise answer-blind response and zero or more learner-triggerable actions.
4. **`HelperCanvasAction` remains proposal-only.** The client presents each action and applies it only after a learner click. Inserted text must retain assistance attribution.
5. **Events become the evidence layer.** Persist events only for student-initiated inquiries, selected mode/command, source-opening activity, accepted or edited assistance, document revisions, and submission. Opportunity detection itself does not create evaluative evidence.

## Required code changes

### Implementation status — 2026-09-12

The first consolidation increment is implemented. New learner documents start as blank canvases rather than receiving the former fixed headings. The student workspace no longer schedules `probes/evaluate` after each save, and the editor no longer sends every changed paragraph to an LLM for classification. The Enquirer now presents assistance only after a learner action, while accepted helper proposals are applied only through an explicit action chip and are attributed as `student_edited_assistance`. Enquirer calls require a valid live model result. An unavailable, malformed, or unsafe model response produces a retryable availability error; Fiosra does not replace it with canned tutoring.

The legacy persisted-probe API remains intact for historical-session compatibility and teacher evidence retrieval, but it is not called by the active student workspace. The next increment should normalize the event and dossier projection around accepted actions and learner-authored revisions before formally deprecating those legacy routes.

| Area | Change | Outcome |
|---|---|---|
| `frontend/src/routes/StudentWorkspace.svelte` | Remove automatic probe evaluation timers and the pending-probe panel from the normal workspace. Retain only a compatibility reader for legacy sessions if needed. | One visible assistance system. |
| `frontend/src/lib/LongFormDocumentEditor.svelte` | Keep the Enquirer drawer, selected-passage entry, slash palette, and optional actions. Change automatic paragraph classification to local opportunity highlighting or make server classification explicitly requested. | Fast, non-interruptive writing flow. |
| `fiosra/mvp/socratic_probe_service.py` | Separate the student-initiated Enquirer methods from the legacy persisted-probe lifecycle. Stop treating automatic analysis as a probe-generation obligation. | Clear service ownership and safer performance profile. |
| `fiosra/mvp/socratic_probe_router.py` | Mark evaluate/list/respond/defer/dismiss routes as legacy-compatible. Establish clear request and response names for Enquirer analysis and turns. | Unambiguous API boundary. |
| `fiosra/mvp/event_store.py` and evidence dossier services | Add or normalize event types for student-initiated inquiry, action offered, action accepted, source opened, and assistance-edited text. | Teacher evidence follows actual learner choices. |
| `fiosra/mvp/evidence_dossier/` | Group the dossier by public rubric criterion and present evidence with confidence/provenance labels. Do not calculate an automatic final grade. | Transparent human review. |
| Tests | Replace automatic-probe UI expectations with Enquirer opt-in and event-trace coverage. Preserve migration tests for existing probe records. | Product behavior and legacy integrity both remain verified. |

## Data and safety rules

The unified model must preserve the existing answer-isolation and learner-agency boundaries.

| Rule | Requirement |
|---|---|
| **No answer substitution** | The agent may explain a process, pose a question, suggest an outline, or point to an assigned source. It may not produce the student’s final response. |
| **No silent writing** | Every canvas insertion requires a learner action. The system records whether the learner retained, modified, or removed assisted text. |
| **No automatic grading** | AutoSCORE may organize criterion-level evidence. Only the educator determines a grade or evaluative conclusion. |
| **No penalty for non-use** | Ignoring a highlight, declining an action, or closing the Enquirer creates no negative inference. |
| **Assignment grounding** | All student help is bounded by the published task, source pack, public rubric, and safe private plan. The answer vault is never sent to the model. |
| **Data minimization** | Background detection remains local where possible. Requests to the model contain only the selected or necessary passage and approved assignment context. |

## Acceptance criteria

The model is resolved when all of the following are true:

1. A student can draft uninterrupted without receiving an automatic question, pending-probe obligation, or required evidence response.
2. The Socratic Enquirer is the only visible conversational assistance surface.
3. A student can request task clarification, source help, planning, counterargument, or revision support from any relevant writing context.
4. Canvas actions require an explicit learner click and preserve assistance attribution.
5. Every published assignment remains available without any interaction with the Enquirer.
6. The teacher can review learner-selected assistance and work history against the public rubric without seeing an automatic grade.
7. Existing persisted probe records remain viewable for historical sessions until a deliberate deprecation migration is completed.

## Recommended delivery sequence

First, remove the automatic probe calls and surface from the student workspace while retaining legacy read support. Second, harden the Enquirer’s scoped commands and action confirmation. Third, normalize the event schema and teacher dossier around learner-selected evidence. Fourth, archive and deprecate the old persisted-probe interaction routes only after production records have a safe retention path.

## Code references

The decision is based on the current implementation of the legacy probe lifecycle, the student workspace orchestration, and the new Enquirer/editor interaction model.

[1]: https://github.com/darkaengl/fiosra/blob/feature/canvas/fiosra/mvp/socratic_probe_service.py "Current Socratic probe service"
[2]: https://github.com/darkaengl/fiosra/blob/feature/canvas/fiosra/mvp/socratic_probe_router.py "Current Socratic probe API router"
[3]: https://github.com/darkaengl/fiosra/blob/feature/canvas/frontend/src/routes/StudentWorkspace.svelte "Current student workspace"
[4]: https://github.com/darkaengl/fiosra/blob/feature/canvas/frontend/src/lib/LongFormDocumentEditor.svelte "Current long-form document editor"
[5]: https://github.com/darkaengl/fiosra/blob/feature/canvas/fiosra/mvp/evidence_dossier/synthesizer.py "Current AutoSCORE evidence dossier synthesizer"
