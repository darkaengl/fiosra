# Local Ollama Evaluation Notes

**Reviewed:** 2026-09-10

The current sandbox has no Ollama binary, no running Ollama process, and no NVIDIA GPU detected. It has approximately 7.1 GiB of currently free RAM, 2 GiB swap, and 38 GiB free disk space. This makes a compact CPU-only evaluation feasible, but not an appropriate benchmark for a responsive production student tutor.

LiteLLM’s Ollama provider documentation supports models using the `ollama/<model>` prefix and an Ollama server at `http://localhost:11434`; it recommends `ollama_chat` where higher-quality chat behavior is desired. The LiteLLM configuration used by Fiosra presently uses the documented `ollama/<model>` format. Source: [LiteLLM Ollama provider documentation](https://docs.litellm.ai/docs/providers/ollama).

Ollama’s Linux documentation provides an official installer and runs a local server using `ollama serve`. Source: [Ollama Linux documentation](https://docs.ollama.com/linux).

For a bounded CPU-only smoke test, `qwen2.5:0.5b` is the appropriate first model: Ollama lists it at 398 MB with a 32K context window. The model family has options up to 72B parameters, but models above 1.5B are not appropriate for the available memory and no-GPU environment. Source: [Ollama qwen2.5 library](https://ollama.com/library/qwen2.5).
