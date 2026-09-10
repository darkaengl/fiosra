# Writer-First Student Canvas Redesign Plan

**Author:** Manus AI  
**Status:** Proposed for approval; no implementation changes authorized by this plan  
**Scope:** The student-facing reasoning canvas in `frontend/src/routes/StudentWorkspace.svelte`  
**Related backlog:** Issue #40 is complete. This plan is a focused UX refinement that preserves its server-authoritative canvas and answer-isolation controls.

## Decision

Fiosra should make the **student’s active section editor the visual and interactional centre of the workspace**. The Socratic guide must become an on-demand utility rather than a parallel chat product. A learner should be able to draft uninterrupted in a large editor, invoke bounded assistance with `/` commands or `@` source references, and open an optional right-hand assistance drawer only when they choose.

> **Design rule:** AI may help a learner plan, inspect, locate, or question their own work. It may not take focus by default, write directly into the learner’s draft, generate a completed response, or expose a reference answer.

The change is a front-end-first refinement. It will reuse the existing FastAPI canvas and dialogue endpoints, session capability, revision checks, assignment-bound source set, provider boundary, deterministic fallback, and assistance-provenance events. It will not introduce autonomous writing, a new model provider, or a free-form “write this for me” tool.

## Current-state basis

The current canvas already separates learner section drafts from optional support cards and preserves source references, learner edits, and assistance events. It also supplies assignment-scoped public source excerpts and sends the active section identifier with tutor requests. However, the visual layout gives persistent space to a left assignment rail, a right source rail, a horizontal section stepper, a support-card area, and a full Socratic chat transcript beneath the editor. At typical laptop widths, the editor becomes one of several competing panels rather than the primary working surface. [1] [2]

The repository’s student-experience specification already establishes the intended principle that AI should not dominate the screen and that the active reasoning canvas should be the dominant surface. This plan implements that principle without adopting its unimplemented automatic unlocking or synthetic score claims. [3]

## Experience model

| Surface | Default state | Learner purpose | AI and safety behavior |
|---|---|---|---|
| **Focused section editor** | Open and visually dominant | Write, revise, attach an approved source, and save a student-owned section. | No assistant text appears in the editor without a learner-triggered edit-and-save action. |
| **Compact assignment bar** | Visible above the editor | Provide the assignment title, current section, draft status, and a concise progress indicator. | Full prompt and hint information are available through a disclosure, not permanently occupying a side rail. |
| **Section navigator** | Compact vertical rail on desktop; horizontal scrollable control on small screens | Move deliberately between the five saved/review-required sections. | It reports persisted state only. It does not auto-complete, auto-advance, or grade a section. |
| **Contextual editor command menu** | Closed until `/` or a dedicated toolbar control | Request a permitted writing frame, a Socratic question, or a source reminder for the active section. | The menu maps only to allow-listed existing support types. It contains no answer, thesis, rewrite, or essay-completion command. |
| **`@` source reference picker** | Closed until `@` or “Sources” control | Search and insert a non-answer-bearing source reference marker linked to an approved assignment source. | Only assignment-approved sources can be selected. The server remains the authoritative validation point when the draft is saved. |
| **AI utility drawer** | Collapsed by default; opened explicitly from the editor toolbar or command result | Show the latest Socratic question, support card, hint status, and a concise recent-assistance history. | Drawer content is section-scoped, source-aware where relevant, attributable, dismissible, and never writes to the draft merely by rendering. |
| **Reasoning trace** | Separate route | Review the complete sequence before submitting. | It preserves student text, optional assistance, integrity redirects, and revision history as distinct record types. |

## Proposed layout and interaction details

### 1. Establish a writing-first desktop layout

The desktop workspace will use a narrow section navigator at the left, a broad central editor, and a closed-by-default utility drawer at the right. The editor column will take the majority of available width and will have a generous writing height. The permanent course-source rail and persistent transcript will be removed from the default layout.

The top assignment bar will show the active assignment name, the current section label, saved state, and a subtle “View brief” control. Opening “View brief” will reveal the full assignment prompt, target knowledge components, and hint-policy explanation in a temporary popover or drawer. This preserves learning context without reducing the writing area.

The active section will present its purpose and completion guidance in a compact, dismissible line directly above the editor. It will not render a large instruction card after a learner starts drafting. The current revision status and source-reference chips will remain visible immediately below the editor.

### 2. Replace the permanent chat panel with editor-native commands

Typing `/` after whitespace, or pressing an accessible “Assist” toolbar button, will open a command menu anchored to the editor. The first release will expose only bounded actions that map directly to the existing server contract.

| Command | Existing safe action | Result location | Explicit learner decision |
|---|---|---|---|
| `/question` | Request `section_question` | AI utility drawer | The learner reads, dismisses, or uses it as a prompt for their own writing. |
| `/frame` | Request `writing_frame` | AI utility drawer | The learner may load it into an editable review state, alter it, and save their own version. |
| `/source` | Request `source_reminder` | AI utility drawer | The learner decides whether to select a cited source reference. |
| `/hint` | Send an explicit bounded hint request | AI utility drawer | The server controls rung progression; no answer is exposed. |
| `/show brief` | Open assignment brief | Temporary overlay | No backend mutation. |

The command list will intentionally omit `/write`, `/answer`, `/thesis`, `/complete`, `/rewrite paragraph`, and similar verbs that imply authorship substitution. The help text will state that the tools ask, structure, or surface evidence; they do not complete assessed work.

### 3. Add approved-source `@` references without turning the editor into a citation generator

When a learner types `@`, the editor will display a short list of approved assignment sources filtered by source title and excerpt text. Selecting a source will create a visible reference chip or inline marker in the editor and attach the source to the active section’s local draft state. It will not copy an entire source excerpt or fabricate a citation.

The learner will be able to open a compact source preview beneath the editor, select an optional bounded quote, and write their own rationale. Save continues to use the existing server validation: a source must belong to the published assignment, and any selected quotation must occur in that approved excerpt. This keeps source provenance structured and prevents the UI from treating copied text as evidence attribution.

### 4. Make the AI drawer deliberately peripheral

The AI utility drawer will remain closed after page load and after ordinary typing. It opens only after the learner presses the toolbar’s **Assist** control, invokes a command, clicks a small “Latest guidance” affordance, or uses a keyboard shortcut. It can be closed with Escape and will never reopen itself merely because a model response arrives.

The drawer will identify each entry as one of **Socratic question**, **Writing frame**, **Source reminder**, **Requested hint**, or **Integrity boundary**. It will show the active section and, when appropriate, the server-reported support rung. The latest card will offer only existing explicit actions: **Use as editable frame**, **Dismiss**, or **Return to writing**. The text is not inserted, saved, or treated as student-authored unless the learner consciously edits and saves it.

A slim “Guidance available” indicator can appear at the editor edge after a requested response is ready. It must not interrupt cursor focus, move text, or expand the drawer.

### 5. Use a progressively disclosed responsive layout

On tablets, the section navigator becomes a compact top strip and the source picker is opened from the editor toolbar. On phones, the AI drawer becomes a bottom sheet. The writing editor remains the first and largest interactive element after the assignment bar. The command menu must remain keyboard accessible and screen-reader labelled at every breakpoint.

## Architecture and data-contract implications

The first release does **not** require a new LLM endpoint. `/question`, `/frame`, `/source`, and `/hint` reuse the existing request paths and their controls. The UI will continue to include the session capability header and active section ID when calling canvas or dialogue APIs. LiteLLM remains hidden behind the server orchestrator boundary; the browser will not select a provider or model. [1] [2]

The only anticipated contract extension is optional and local to the browser: a `draftEditorSelection` model to track command-menu state, the active inline-source marker, and a source quote pending inclusion. It is not authoritative. The existing `CanvasSourceReference` remains the persisted source structure. Persisted section text will remain student-owned, revisioned, and protected from stale writes. [2]

The temporary AI drawer history will be reconstructed from existing dialogue and canvas-suggestion events. No free-form client event type will be introduced. The existing support-card lifecycle remains authoritative: an offered card is a server record; applying it requires an intentional learner save; dismissal is a separate server record. [2]

## Implementation sequence

| Step | Deliverable | Validation before proceeding to the next step |
|---:|---|---|
| 1 | A desktop and mobile Svelte layout refactor that promotes the active editor and replaces permanent rails with compact navigation plus closed panels. | Production build, keyboard navigation check, and a screenshot review at desktop and mobile widths confirm that the editor is the dominant surface. |
| 2 | Editor toolbar, `/` command menu, and accessible command filtering wired only to safe existing actions. | Unit-level command mapping tests confirm there is no route to answer generation, direct draft mutation, provider selection, or unrestricted chat. |
| 3 | `@` approved-source picker, inline marker/chip representation, quote preview, and existing structured source-reference save path. | API regression tests confirm unapproved chunks and quotation text outside approved excerpts still fail. Browser testing confirms choosing a source does not paste or invent source content. |
| 4 | Collapsible AI drawer that presents existing support cards, dialogue turns, requested hints, and integrity messages as peripheral context. | Browser testing confirms the drawer is closed initially, does not steal focus, does not open automatically, and cannot save or mutate draft text without the learner’s explicit action. |
| 5 | Trace and educator-review wording refinements so UI labels describe assistance accurately after the new interaction model. | Full frontend build, backend regression suite, and the protected learner-to-educator browser journey pass. |

## Acceptance criteria

| Category | Acceptance criterion |
|---|---|
| **Writing primacy** | At a standard desktop width, the active editor is visually larger than every AI and source control combined. The initial viewport shows no expanded chat transcript or AI card. |
| **Non-clutter** | Assignment detail, source browsing, and AI history are progressively disclosed. The learner can write and save without navigating a persistent three-column dashboard. |
| **Safe invocation** | `/` and the toolbar reveal only allow-listed, instructional tools. No command offers a completed answer, thesis, paragraph, rubric judgment, grade, or provider/model choice. |
| **Source provenance** | `@` offers only approved assignment sources. Saving preserves the existing structured source-reference validation and rejects unsupported quotations. |
| **Student authorship** | A writing frame remains outside the saved draft until the learner explicitly invokes it, changes or confirms text, and saves. Assistance remains separately attributed in trace and educator review. |
| **AI periphery** | The AI drawer is closed by default, does not open on typing or response arrival, can be dismissed with Escape, and returns keyboard focus to the editor. |
| **Answer isolation** | The integrity boundary continues to intercept answer-extraction requests before the provider path. Student-facing AI continues to receive no Answer Vault material. |
| **Provider resilience** | With `FIOSRA_LLM_PROVIDER=deterministic` or a provider failure, every command still yields a usable deterministic question, writing frame, source reminder, or policy response. |
| **Accessibility** | Command menu, source picker, and drawer are usable by keyboard, expose meaningful labels and focus states, and behave coherently at desktop, tablet, and mobile breakpoints. |
| **Regression safety** | Existing session-capability, revision-conflict, source-validation, post-submission write-block, trace, and full course-to-review tests remain green. |

## Explicit exclusions

This plan will not add an autonomous essay agent, automatic draft completion, automatic section progression, model-selected sources, hidden rewriting, text streaming directly into the editor, generated grades, or a new public model API. It will not claim that a learner has mastered a concept merely because they invoked a tool or saved a draft.

## Approval request

Approve this plan to authorize the following bounded implementation: a writer-first Svelte canvas, command-driven safe assistance, approved-source `@` references, a collapsed AI utility drawer, and full browser/API regression validation. The implementation will preserve the existing FastAPI, PostgreSQL, Svelte, LiteLLM, Ollama, and event-trace architecture.

## References

[1]: https://github.com/darkaengl/fiosra/blob/feat/end-to-end-learning-workflow/frontend/src/routes/StudentWorkspace.svelte "Current StudentWorkspace implementation"
[2]: https://github.com/darkaengl/fiosra/blob/feat/end-to-end-learning-workflow/fiosra/mvp/learning_canvas_service.py "Learning canvas persistence and assistance lifecycle"
[3]: https://github.com/darkaengl/fiosra/blob/feat/end-to-end-learning-workflow/ui-ux/student-experience/README.md "Fiosra student experience specification"
