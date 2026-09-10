# Live LLM Provider Verification

## Default-provider browser check

The built Fiosra application was launched with `FIOSRA_LLM_PROVIDER=deterministic`. The educator Assignment Scaffold Designer loaded normally, accepted a title and a course-grounded inquiry prompt, and remained fully usable without a provider credential or a network model call. This confirms that LiteLLM is an optional enhancement rather than a startup or authoring dependency.

The remaining browser action generates the scaffold and verifies that the educator-facing provenance line reports deterministic generation when no external provider is enabled.

## Deterministic scaffold result

The educator triggered scope analysis and scaffold generation with no live provider configured. The application returned the existing answer-isolated scaffold successfully, displayed the explicit **Deterministic wording** provenance line, and did not require a credential, model response, or outbound provider call. The preview continued to show the locked bottom-out rung and source-grounding publication warning, confirming that the optional LLM layer did not weaken the existing authoring controls.

## Local Ollama smoke test

Ollama was installed locally and the compact CPU-capable `qwen2.5:0.5b` model was downloaded. A real FastAPI `clarify-and-scaffold` request passed through LiteLLM to `ollama/qwen2.5:0.5b`, proving that the configured provider, local base URL, async adapter, and returned provider metadata work end to end. On the 9.5 GiB, CPU-only sandbox, the response took 5.8–11.5 seconds, which is suitable for development validation but not a basis for a production latency commitment.

The initial authoring response was declarative and answer-like despite the instructions. The artifact was deleted immediately. Fiosra now requires model-generated scaffold text to be an imperative student task, rejects worked-answer formatting, and returns the deterministic scaffold whenever the output does not pass those rules. The same live request then returned `provider: deterministic` with the safe fallback reason `Provider response did not preserve student-task imperative form.`

A second test created a course-grounded student session while deliberately submitting conflicting prompt and domain values from the client. The server used the session’s authoritative assignment context, then accepted a real Ollama Socratic response: “What can Mohenjo-daro's drainage infrastructure tell us about urban planning during the Mature Harappan period?” The response carried `provider: ollama`, `model: ollama/qwen2.5:0.5b`, `used_live_provider: true`, and a 1.3-second measured provider response time. Live rephrasing is now restricted to course-grounded assignments and must end as a concise question; ungrounded sessions remain deterministic.

## OpenAI-compatible provider smoke test

The configured OpenAI-compatible sandbox endpoint was also tested through Fiosra and LiteLLM using the currently available `gpt-5-nano` model. The first attempt exposed a provider-normalization issue: GPT-5 rejects the legacy `max_tokens` parameter. The adapter now detects GPT-5 model names and supplies `max_completion_tokens` with minimal reasoning effort; a regression test verifies that mapping.

The corrected end-to-end, course-grounded tutor request returned a live model response: “What provisional claim would you state, and which observation most directly supports it, while identifying what remains uncertain?” Fiosra returned `provider: openai`, `model: gpt-5-nano`, `used_live_provider: true`, 1.9-second measured latency, and 191 prompt / 39 completion tokens. The request deliberately supplied conflicting client prompt and domain values; the response remained based on the server-authoritative assignment context. No credential values, raw provider requests, or test response artifacts were retained.
