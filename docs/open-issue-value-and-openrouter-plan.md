# Open-Issue Triage and OpenRouter LLM Integration Plan

**Prepared:** 2026-09-10  
**Repository:** `darkaengl/fiosra`  
**Scope:** Current open GitHub issues and a safe OpenRouter free-model integration path

## Executive assessment

The immediate product opportunity is **not** to make Fiosra an unconstrained chatbot. The product’s value is its course-grounded reasoning workflow, answer isolation, bounded scaffolding, append-only evidence, and educator final authority. A language model should improve the quality and variety of wording inside those boundaries, while the application retains deterministic control over assignment publication, hint progression, evidence records, and grades.

Two currently open feature issues—dynamic student source loading and assignment authoring/module binding—are already delivered by [PR #38](https://github.com/darkaengl/fiosra/pull/38). Their acceptance paths were exercised locally from educator course setup through source grounding, publication, student workspace, submission, and course-filtered review. They should be linked to the pull request and closed on merge rather than rebuilt.

## Open-issue prioritization

| Priority | Issue | Current status and immediate value | Recommendation |
|---|---|---|---|
| P0 | [#31 Live LLM Provider Orchestration](https://github.com/darkaengl/fiosra/issues/31) | This is the smallest remaining capability that makes the co-pilot feel genuinely adaptive. It enables controlled draft language for scope clarification and Socratic dialogue while retaining deterministic fallbacks. | Implement next, with OpenRouter as an optional provider and the current deterministic behavior as the default and fallback. |
| P0 | [#35 Assignment Authoring & Module Binding](https://github.com/darkaengl/fiosra/issues/35) | Already implemented on PR #38: authoring persists a module-bound assignment, student-safe projection is verified, and the assignment renders on the module card. | Do not duplicate. Add `Closes #35` to the pull request description before merge. |
| P0 | [#36 Dynamic Course Reading Corpus](https://github.com/darkaengl/fiosra/issues/36) | Already implemented on PR #38: the student canvas receives the selected course/module’s real grounded source and provenance. | Do not duplicate. Add `Closes #36` to the pull request description before merge. |
| P1 | [#30 Speech-to-Thought](https://github.com/darkaengl/fiosra/issues/30) | High pedagogical differentiation: students can externalize early reasoning before formalizing it. It is especially useful after the core tutor wording becomes adaptive. | Build a browser speech-recognition first release after #31. Make transcription opt-in, visibly editable before submission, and preserve the resulting text—not raw audio—as the default evidence artifact. |
| P2 | [#32 Real-Time Dialogue Streaming](https://github.com/darkaengl/fiosra/issues/32) | Streaming improves perceived responsiveness when a live provider has noticeable latency. With the deterministic current tutor, its user value is limited and it introduces disconnect/event-finalization complexity. | Implement after #31, using SSE rather than WebSockets for one-direction tutor output. Commit a completed turn only after stream completion; never stream an unchecked answer. |
| Umbrella | [#28 Epic 8](https://github.com/darkaengl/fiosra/issues/28) | Its frontend-wiring acceptance criterion is substantially advanced by PR #38, while #30–#32 remain the active dependencies. | Keep as the tracking issue; update its checklist after #35 and #36 close. |

## Why OpenRouter is feasible

OpenRouter is a practical fit for this codebase because it exposes an OpenAI-compatible chat-completions API at `https://openrouter.ai/api/v1/chat/completions`. The FastAPI backend already depends on `httpx`, so an asynchronous integration does not require a new HTTP-client dependency. Requests authenticate with a server-side bearer token and support structured JSON responses, routing/fallback options, and server-sent event streaming.[^openrouter-api]

The free collection exposes both named `:free` models and the `openrouter/free` router. The latter automatically selects an available free model for a request, which makes it useful for development and demos. It is not a reliable production capacity commitment: OpenRouter states that free models have low limits, typically **50 requests per day total** before the account has purchased at least $10 in credits, and free-model availability is not guaranteed.[^openrouter-faq] Therefore, the free router should be an optional, rate-limited enhancement—not the sole dependency for student-facing work.

## Recommended integration boundary

| Application concern | LLM role | Must remain server-authoritative |
|---|---|---|
| Scope de-ambiguation | Propose clearer follow-up wording and candidate assumptions from the educator-provided prompt and approved source excerpts. | Whether the prompt is ambiguous, what the educator accepts, and the assignment’s final scope. |
| Assignment scaffolding | Draft alternative answer-blind question wording, Socratic ladders, and rubric language in a schema-validated response. | Publication readiness, source provenance, rubric thresholds, answer vault storage, and the teacher’s final edit/publish action. |
| Student dialogue | Rephrase the *already selected* bounded hint into a concise, contextual Socratic question. | Adversarial detection, active hint rung, assignment/course context, event logging, and all answer-isolation rules. |
| Review and grading | None in the first release. | Evidence extraction, scoring evidence, grade recommendation presentation, and educator finalization. |

The existing `SocraticDialogueEngine` should continue to choose the server-authoritative rung and assignment context before any provider is called. The provider receives only a concise, public prompt containing the selected hint, the public assignment prompt, a short source excerpt, and formatting constraints. It never receives an Answer Vault token, reference solution, educator-only rubric key, student identifier, or full historic trace.

## Proposed technical design

Add an `fiosra.mvp.llm` package containing a small provider protocol, an OpenRouter implementation, a deterministic implementation, and an orchestrator. The provider surface should offer one schema-validated completion method rather than letting UI routes make raw calls. Configuration should add `FIOSRA_LLM_PROVIDER=deterministic|openrouter`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_TIMEOUT_SECONDS`, and a conservative per-session request budget. The default must remain `deterministic`, so development, test, and deployment continue to work without a key.

When enabled, the OpenRouter provider should call the OpenAI-compatible API with a fixed model value such as `openrouter/free` for non-production exploration, an explicit timeout, a stable pseudonymous `user` value, and a strict response schema where model support permits it. The orchestrator should reject empty, overlong, malformed, or out-of-scope output; apply an answer-leak guard before returning text; and fall back to the current deterministic response on a timeout, 429, 5xx, schema failure, or guardrail failure. It should record the selected model, latency, token counts, and fallback reason without logging raw prompts or student content.

The first model evaluation should compare `openrouter/free` with two currently listed named free text models, such as `nvidia/nemotron-3.5-lightning:free` and `liquid/lfm-2.5-2.6b:free`, using a frozen Fiosra evaluation set. The final production setting should be selected on contextual relevance, safe JSON compliance, response latency, and guardrail-failure rate—not ranking position alone, because the free-model list changes over time.[^openrouter-free]

## Privacy, reliability, and release safeguards

OpenRouter states that it does not log prompts and completions by default, but it routes requests to third-party model providers and provider retention/training policies vary. Its FAQ notes that a privacy setting can exclude providers whose policies are not confirmed, while some free-model pages explicitly say they may use inputs and outputs for training.[^openrouter-faq] Fiosra should therefore use institution-controlled provider privacy settings, never enable prompt logging for a production tenant by default, pseudonymize user identifiers, and prohibit transmitting student names, raw recordings, or Answer Vault content. Course-material licensing and institutional student-data approval must be established before any live classroom rollout.

Reliability should be designed for failure rather than assumed from free availability. The deterministic system already creates bounded, course-grounded hints and must remain the response path if OpenRouter is unavailable. The UI should identify model-assisted wording only in educator-facing diagnostics, never label the tutor as reliable merely because a model responded. A circuit breaker should pause the provider after repeated provider failures and allow only deterministic responses until the cooldown ends.

## Recommended implementation order

Implement #31 as a narrow, test-first provider boundary. Start with **educator-side scope clarification and scaffold phrasing**, because the educator reviews the result before publication. Add the student-turn rephrasing only after adversarial, context-leakage, source-grounding, and deterministic-fallback tests pass. Then implement #30’s editable speech-to-thought capture, followed by #32’s SSE transport once the live provider’s latency justifies streaming. This order delivers visible quality while preserving Fiosra’s distinctive trust model.

## Sources

[^openrouter-api]: [OpenRouter API Overview](https://openrouter.ai/docs/api-reference/overview), retrieved 2026-09-10.
[^openrouter-faq]: [OpenRouter FAQ](https://openrouter.ai/docs/faq), retrieved 2026-09-10.
[^openrouter-free]: [OpenRouter Free Models collection](https://openrouter.ai/collections/free-models), retrieved 2026-09-10.
