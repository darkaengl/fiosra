# Live LLM Provider Guide

## Purpose

Fiosra can optionally enhance educator-facing scaffold wording and student-facing Socratic hint phrasing with a live language model. It uses LiteLLM as a provider adapter so deployments can change among OpenRouter, OpenAI, Gemini, and Ollama without modifying the FastAPI routes or the Svelte client.

The default configuration is `FIOSRA_LLM_PROVIDER=deterministic`. This is intentional: all learning workflows work without an API key, network access, or local model runtime. Live language models improve phrasing only; they never become an authority for grades, student state, source provenance, assignment publication, or answer access.

## Provider configuration

| Provider value | Required configuration | Example model value | Intended use |
|---|---|---|---|
| `deterministic` | No key or model runtime | `deterministic` | Default for tests, local development, and dependable fallback behavior. |
| `openrouter` | `OPENROUTER_API_KEY` | `openrouter/openrouter/free` or `openrouter/nvidia/nemotron-3.5-lightning:free` | Provider-neutral experimentation and controlled evaluation of OpenRouter models. |
| `openai` | `OPENAI_API_KEY`; optional `OPENAI_API_BASE` | `gpt-4o-mini` | OpenAI or an OpenAI-compatible hosted deployment approved by the institution. |
| `gemini` | `GEMINI_API_KEY` | `gemini/gemini-2.5-flash` | Google AI Studio deployment approved by the institution. |
| `ollama` | A reachable Ollama server | `ollama/llama3.2` | Private/self-hosted deployment with a local or institution-operated model server. |

Copy `.env.example` to `.env` and configure exactly one provider. API keys belong only in secret storage or the server environment; they must never be committed to the repository or sent to the Svelte client.

```dotenv
FIOSRA_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=replace_with_server_secret
OPENROUTER_MODEL=openrouter/openrouter/free
OPENROUTER_TIMEOUT_SECONDS=12
FIOSRA_LLM_FAILURES_BEFORE_COOLDOWN=3
FIOSRA_LLM_COOLDOWN_SECONDS=60
```

## Runtime behavior

Every live completion passes through `fiosra.mvp.llm.LLMOrchestrator`. Before the provider call, Fiosra selects the active assignment, public course context, permitted hint rung, and deterministic fallback. It sends the provider only public, answer-blind context. Student dialogue is eligible for a live rephrase only when its active assignment is course-grounded; it sends the active prompt and the single server-selected hint, never the student identity, full event trace, answer-vault token, reference solution, or educator-only solution material. The live tutor response must remain a concise question or Fiosra returns the deterministic server-selected hint.

The provider receives a pseudonymous hash in the OpenAI-compatible `user` field. Fiosra records only operational metadata in assignment specifications and dialogue event payloads: provider, resolved model, latency, token counts where supplied, whether a live provider was used, and a fallback reason if applicable. It does not persist raw provider prompts or raw responses beyond the approved student-visible wording already captured in the reasoning event.

A live response is rejected if it is blank, over the configured response size, or contains prohibited answer-isolation terms such as `reference solution`, `answer key`, or `vault token`. Provider error, timeout, rate limit, malformed completion, rejected output, or circuit-breaker cooldown all return the deterministic fallback without interrupting a student or educator workflow. The circuit breaker enters cooldown after the configured consecutive failure count.

## Provider selection guidance

Use `openrouter/openrouter/free` for local experimentation only. Free-model availability and rate limits vary, so it is not a production availability guarantee. Validate a named model with Fiosra’s frozen safety and relevance tests before using it as a production default. LiteLLM receives the model string directly, so a named OpenRouter model can be substituted without code changes.

When an institution provides an OpenAI-compatible proxy rather than OpenAI’s public endpoint, set `OPENAI_API_BASE` to the proxy’s versioned base URL. The adapter detects GPT-5 model names and sends the current `max_completion_tokens` parameter with minimal reasoning effort instead of the legacy `max_tokens` field, which those models reject.

Use Ollama for environments where source excerpts or student content must remain inside a private network, provided that the institution operates and governs the model host. Use OpenAI or Gemini only after the organization has approved the selected service, model, retention configuration, and student-data posture.

## Verification

Run the following before enabling a live provider in a shared environment:

```bash
uv run ruff check fiosra tests
uv run pytest tests -q
cd frontend && npm run build
```

The provider tests intentionally mock LiteLLM. They prove that the default path is network-free, model settings resolve for all supported providers, request identity is pseudonymous, live metadata is captured, and provider failures or attempted answer-isolation leaks fall back safely.
