# Slice 2: Proactive Socratic Probes — Verification Results

**Date:** 2026-09-10  
**Scope:** Approved Slice 2 only: proactive paragraph-bound Socratic questions, response evidence, guarded LiteLLM rephrasing, deterministic fallback, and evaluator visibility.

## Outcome

Slice 2 was validated as a writer-first, server-authoritative workflow. A student can continue composing in the long-form document without an AI panel competing for attention. When a learner saves a substantive paragraph and pauses, the server may offer one compact question about that paragraph. The learner retains the choice to answer, defer, dismiss, or keep writing. A submitted explanation is retained as separate, evaluator-visible evidence and is never inserted into the student essay or presented as an automatic grade.

## Automated release checks

| Check | Result |
|---|---:|
| Ruff linting for backend and tests | Passed |
| Python compilation | Passed |
| Complete backend regression suite | **76 passed** |
| Slice 2 probe lifecycle suite | **3 passed** |
| LiteLLM policy and provider suite | **8 passed** |
| Svelte production build | Passed |
| `git diff --check` | Passed |

The test coverage includes capability ownership, inactive-session rejection, stale revision handling, paragraph eligibility, quiet-period enforcement, duplicate prevention, session budget, cooldown, supersession, response/defer/dismiss transitions, and the evaluator dossier projection. It also covers deterministic fallback when a provider fails, leaks answer-like content, returns non-question text, or introduces vocabulary outside the bounded probe context.

## Live local Ollama journey

The application was launched with the existing local `qwen2.5:0.5b` Ollama model through the LiteLLM adapter, using a five-second probe quiet period for the smoke test. A fresh protected learner session was opened for the published, course-grounded **Canvas source reasoning** assignment.

The student then saved the following independent paragraph in the continuous document:

> The drainage channels suggest deliberate coordination because their alignment across connected homes required shared construction decisions, although the remains do not identify the institution that organized the work.

After the quiet period, the interface displayed a compact **Questions 1** control and a non-modal notification. The editor remained open, editable, and focused as the main working surface. Opening the drawer presented one causal-bridge question. The learner entered a distinct explanation and selected **Save response**. The interface confirmed that the response was stored for educator consideration and was not an automatic grade.

The live local model did produce a candidate with invented context. The new bounded-vocabulary policy rejected that candidate before it could reach the learner. The stored generation metadata confirms `provider: deterministic`, `used_live_provider: false`, and the fallback reason `Provider response introduced vocabulary outside the bounded probe context.` The learner therefore saw the deterministic, answer-blind fallback question:

> What mechanism would need to connect the condition you describe to that outcome?

This validates the intended safety property: local model availability enriches wording only when it stays within the defined boundary; it cannot introduce history, conclusions, source interpretation, or answer material.

## Learner-to-evaluator evidence handoff

The student opened the protected reasoning trace, which recorded the document initialization, document synchronization, question offer, and question response in chronological order. After the student explicitly submitted the session for review, the educator review queue showed a dedicated **Proactive reasoning evidence** panel separate from the rubric evidence.

| Evidence field | Observed result |
|---|---|
| Paragraph context | `Student writing` |
| Server-selected focus | `causal bridge` |
| Learner-visible question | Deterministic question shown above |
| Lifecycle state | `responded` |
| Learner response | Rendered verbatim in the educator evidence panel |
| Grade authority | Retained by the educator; no automated score was changed by the response |

The educator panel clearly communicates that the question and response are evidence for review rather than a grade determination. The existing AutoSCORE recommendation remains visually distinct from this new explanation record.

## Manual acceptance findings

The delivered interaction satisfies the approved writer-first constraints. The question drawer is closed by default, only the small question count appears after evaluation, and saving or answering a question never replaces essay content. The right-side drawer has a clear close control, an explicit text area labelled **Your reasoning**, and the non-punitive **Later** and **Dismiss** options. When a session is submitted, no subsequent document or probe mutation is permitted by the server.

The existing fallback question is intentionally broad and does not paraphrase the learner’s sentence. This is correct for the current safety boundary, but a future evidence-validation slice can introduce richer wording only after it can deterministically verify each term against an assignment-approved evidence bundle. It should not relax the present guardrail for convenience.

## Residual scope

Slice 2 does not provide brainstorming, grammar/reformat edits, evidence-gated drafting, AI grading, role-based educator authorization, or PDF evidence-packet export. Those capabilities remain outside this approved slice and require separate reviewed plans before implementation.

## Migration and browser checks

A disposable PostgreSQL database applied every repository migration in lexical order—`001_initial_schema.sql`, `002_syllabus_chunks.sql`, `004_module_resources.sql`, `005_learning_canvas.sql`, `006_long_form_document.sql`, and `007_proactive_socratic_probes.sql`—with `ON_ERROR_STOP=1`. The final database contained both `socratic_probes` and `socratic_probe_responses`, confirming that the incremental schema is valid from a clean start.

The final browser console inspection reported no console output after completing the learner-to-evaluator journey.
