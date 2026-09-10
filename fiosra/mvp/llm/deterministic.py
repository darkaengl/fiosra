from fiosra.mvp.llm.contracts import CompletionRequest, CompletionResult


class DeterministicProvider:
    """Marker provider for observable deterministic fallback operation.

    The orchestration service uses the caller-provided deterministic text as the
    response, so this class is intentionally never asked to synthesize text.
    """

    name = "deterministic"

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        raise RuntimeError(
            "DeterministicProvider does not generate text; pass a deterministic fallback to the orchestrator."
        )
