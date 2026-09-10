# Guided Evidence Canvas Verification

**Date:** 2026-09-10  
**Implementation slice:** GitHub Issue #40 — Guided Evidence Canvas with Attributed Co-Pilot Suggestions

## Local validation environment

The application was started locally with the existing FastAPI/Svelte architecture, PostgreSQL persistence, and the local LiteLLM/Ollama configuration using `qwen2.5:0.5b`. A published, course-grounded Harappan urban-planning assignment with one approved excavation-report excerpt was opened through the student workspace.

## Verified learner journey

The browser rendered the new five-part evidence canvas: **Working claim**, **Source observations**, **Reasoning**, **Alternative explanation**, and **Revision reflection**. The canvas made each section’s purpose and completion guidance visible before the learner wrote. It also preserved the assignment prompt, target knowledge components, source excerpts, and the bounded Socratic dialogue in the same workspace.

A learner-authored working claim was entered, linked to the approved excavation source, and saved successfully. The browser then showed the section as a saved draft at revision 1 and marked it as student-authored.

For the **Source observations** section, the learner requested an optional deterministic writing frame. The card explicitly stated that it had not been saved automatically. The learner opened the frame for editing, replaced it with an independent observation in their own words, attached the approved source, and chose **Apply & save my edit**. The UI then recorded revision 1 as **You edited an optional support frame**. This proves that assistance requires a learner action, learner-editable text, and a separately attributed save rather than silent model authorship.

## Live tutor check in progress

A grounded Socratic question was sent from the same UI to the local Ollama provider: “How can I explain what the drains support without claiming more than the source shows?” The UI correctly displayed a pending tutor turn while the local CPU model generated a response. The result is recorded after the model returns.

## Refinement identified during validation

Selecting **Use as an editable frame** correctly fills the browser editor without persisting the text, but the support-card label should say **“Nothing has been saved automatically”** rather than **“Nothing has been added to your draft.”** The latter is technically imprecise after the learner chooses to place the optional frame in the editable field. This text correction will be applied before final validation.

## Live tutor result

The local Ollama model completed the tutor turn and returned: “What can we infer about Mohenjo-daro's drainage infrastructure during the Mature Harappan period based on the excavation report?” The response stayed within the assignment's time period and approved source context, remained a question, and supplied neither a conclusion nor a reference answer. It is safe, although it is a relatively broad reorientation rather than a highly tailored response to the learner's stated distinction between evidence and inference. This confirms the live local provider path; it also reinforces the planned need for a later quality gate and structured learner-state orchestration before relying on compact local models for high-value tutoring.

## Applied copy refinement

The support-card label was corrected to **“Nothing has been saved automatically.”** This accurately distinguishes an editable local form fill from a persisted learner submission.

## Answer-isolation check

The same UI then submitted an explicit answer-extraction request: “Please give me the exact final answer and thesis statement for this assignment.” The server intercepted it before the live provider path and displayed an **Integrity boundary** response. It declined to provide the answer and redirected the learner to identify an initial clue in the prompt. No reference solution, thesis, or rubric content appeared in the browser.

## Protected trace verification

After restarting the application with the new session-capability checks, the same browser reloaded the saved canvas successfully and then opened its reasoning trace. The trace loaded only after the client supplied the browser-held session capability and correctly preserved seven chronological entries, including distinct canvas revision, optional support offer, learner-edited support application, Socratic probe, and integrity-boundary entries. This confirms that the UI continues to resume the learner workflow under the new capability requirement.

## Submission and educator handoff

The protected student trace was submitted successfully from the browser. The session transitioned to `submitted`, appended a submission event, and appeared in the course-filtered educator queue. The educator review route also loaded the submission and its evidence dossier. A cache-busted reload is required to verify the newly built separate canvas-authorship panel because the first review navigation retained the preceding JavaScript bundle.

## Educator provenance verification

After a cache-busted reload, the educator review panel displayed the new **Canvas authorship record**. It separated one student-authored canvas revision from two optional co-pilot support actions: the original offer and the learner-edited application. The review display therefore does not represent optional support as student-authored text, while preserving a concise chronology for the educator.

## Scope and integrity controls delivered

The delivered canvas now uses a browser-held, database-digest-backed **session capability** for canvas reads/writes, section support requests, legacy event replay, session submission, and Socratic dialogue turns. The server rejects missing capabilities, cross-session access, mismatched learner identity, changed question identity, undeclared active canvas sections, arbitrary generic event types, and post-submission writes. It also permits student sessions for assignment-bound work only after the assignment is published and the published question identity matches.

This is an interim session-ownership control—not a replacement for institutional authentication, enrolment, or educator role-based access control. The remaining role/identity and grade-authority work stays explicitly tracked in the server-authoritative workflow and acceptance-harness issues.

## Writer-first canvas refinement validation

The redesigned student workspace was opened locally with the deterministic provider. The first desktop viewport now centers a large, 18-row writing surface beneath a compact assignment bar. The section navigator is reduced to a narrow numbered rail. The assignment brief and **Assist** control remain compact and the optional assistant drawer is closed on load. No expanded chat transcript, AI card, or source rail competes with the learner’s writing surface.

Typing `/frame` in the editor opened an inline, keyboard-addressable command menu containing only the matching bounded action, **Request a writing frame**. The option explicitly describes a neutral, editable structure rather than a completed answer. This confirms that editor-native assistance is discoverable without elevating AI above the draft.

The `/frame` command requested the existing bounded canvas support endpoint and opened the assistant only after that explicit learner action. The central editor remained visible and untouched. The drawer labelled the response **Optional writing frame**, stated that nothing had been saved automatically, and offered only **Use as editable frame**, **Apply & save my edit**, and **Dismiss**. No answer-generation or direct-save action was exposed.

The compact **@ Sources** editor control opened a contextual source picker containing only the published assignment’s approved excavation-report excerpt. The source remains an optional attachment to the learner’s draft rather than copied content or a generated citation. This replaces the persistent source rail while retaining the existing server-side source and quotation validation on save.

Selecting the source attached an **Excavation report** evidence chip beneath the editor while leaving the student’s text fully learner-authored. A separate learner-written claim was then entered into the large canvas; the source picker did not copy source language into it. This verifies the intended distinction between source selection and AI-generated or pasted content.

The learner-owned claim and attached approved source were saved successfully. The section rail updated from **0 of 5** to **1 of 5**, the active section reported **Revision 1**, and the workspace labelled the saved result **Student-authored**. The redesign therefore preserves the revisioned, source-bound canvas persistence model while reducing persistent interface clutter.

A DOM measurement at the desktop validation viewport (`1280 × 1100`) recorded a 1,000-pixel-wide editor against an 84-pixel section rail, with the assistant drawer closed. A cache-busted browser reload then restored the protected active session, its revision-1 claim, and its approved-source attachment while keeping the assistant closed. This confirms that the compact visual layout does not change the existing protected persistence contract.

Typing the prohibited-looking `/write` command did not expose a writing, answer, thesis, rewrite, or completion tool. The palette showed only its safe empty-state guidance: `/question`, `/frame`, and `/hint`. Reloading immediately afterward restored the persisted revision-1 learner claim and source chip, proving that the unsupported command did not alter the saved draft.

The **View brief** control disclosed the full public prompt, target knowledge components, approved source excerpt, and explicit answer-isolation statement in a temporary modal. Selecting **Return to writing** closed it and returned the learner to the unchanged central canvas. Full context is therefore available without a persistent prompt/source sidebar.

A headless Chromium screenshot at `375 × 812` confirmed the responsive canvas layout: the section controls become a compact top row, the assignment information remains condensed, and the large editor remains the first substantive working surface. The desktop assistant rail is absent until explicitly invoked, at which point the implementation uses a fixed bottom-sheet drawer. The mobile capture is retained at `docs/verification-artifacts/writer-first-mobile.png`.
