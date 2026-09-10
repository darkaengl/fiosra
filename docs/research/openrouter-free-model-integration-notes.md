# OpenRouter Free-Model Integration Research Notes

**Reviewed:** 2026-09-10

OpenRouter’s [free-model collection](https://openrouter.ai/collections/free-models) states that `openrouter/free` automatically routes a request to an available free model based on request requirements. The collection describes zero-priced inference but does not guarantee future capacity or availability. Its September 2026 ranking lists models such as NVIDIA Nemotron 3 Ultra, NVIDIA Nemotron 3.5 Lightning, NVIDIA Nemotron 3 Super, Thinking Machines Inkling, and Liquid LFM2.5-2.6B as free options. It specifically notes that some providers may retain prompts and outputs for training or improvement.

OpenRouter’s [API overview](https://openrouter.ai/docs/api-reference/overview) documents an OpenAI-compatible `POST https://openrouter.ai/api/v1/chat/completions` API using an `Authorization: Bearer <OPENROUTER_API_KEY>` header and a `model` name with organization prefix. The API supports non-streaming and SSE streaming completions, normalized response fields, structured JSON or JSON-schema output, model fallback routing, and optional application attribution headers. Non-streaming responses expose usage and optional cost data.

Product implication: Fiosra should use OpenRouter only as an optional, server-side provider for non-authoritative language generation such as scope clarification, draft hint wording, and dialogue phrasing. The Answer Vault, event store, student-session state, publication checks, rubric thresholds, and evidence/grade decisions must remain deterministic and server-authoritative. A free router/model requires timeout, rate-limit, invalid-output, and availability fallbacks because zero-cost availability is not guaranteed. Student prompts and source text should not be sent to providers that retain data for training unless the institution has obtained appropriate consent and the provider’s data policy is approved.

Sources:

1. [OpenRouter Free Models](https://openrouter.ai/collections/free-models)
2. [OpenRouter API Overview](https://openrouter.ai/docs/api-reference/overview)
