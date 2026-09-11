from dataclasses import dataclass, field
from typing import Protocol


class LLMProviderError(RuntimeError):
    """Raised when a configured live language-model provider cannot complete safely."""


@dataclass(frozen=True)
class CompletionRequest:
    """Answer-blind request passed to a language-model provider."""

    system_prompt: str
    user_prompt: str
    purpose: str
    max_tokens: int
    temperature: float = 0.2
    metadata: dict[str, str] = field(default_factory=dict)
    response_format: dict[str, object] | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class CompletionResult:
    """Normalized provider result without raw prompt persistence."""

    content: str
    provider: str
    model: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class LLMProvider(Protocol):
    """Minimal asynchronous provider interface used by Fiosra orchestration."""

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        """Return a single bounded text completion or raise LLMProviderError."""
