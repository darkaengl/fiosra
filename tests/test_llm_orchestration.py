from types import SimpleNamespace

import pytest

from fiosra.mvp.config import settings
from fiosra.mvp.llm.contracts import CompletionRequest, CompletionResult, LLMProviderError
from fiosra.mvp.llm.litellm_provider import LiteLLMProvider
from fiosra.mvp.llm.orchestrator import llm_orchestrator


@pytest.fixture(autouse=True)
def reset_llm_state(monkeypatch):
    """Keep provider selection and circuit-breaker state isolated per test."""
    original = {
        "FIOSRA_LLM_PROVIDER": settings.FIOSRA_LLM_PROVIDER,
        "FIOSRA_LLM_FAILURES_BEFORE_COOLDOWN": settings.FIOSRA_LLM_FAILURES_BEFORE_COOLDOWN,
        "FIOSRA_LLM_COOLDOWN_SECONDS": settings.FIOSRA_LLM_COOLDOWN_SECONDS,
    }
    llm_orchestrator.reset_for_testing()
    yield
    for name, value in original.items():
        monkeypatch.setattr(settings, name, value)
    llm_orchestrator.reset_for_testing()


@pytest.mark.asyncio
async def test_deterministic_provider_is_default_and_never_attempts_network(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "deterministic")

    result = await llm_orchestrator.enhance(
        purpose="socratic_hint_rephrase",
        system_prompt="system",
        user_prompt="public assignment context",
        deterministic_fallback="Name the observation that supports your claim.",
        pseudonymous_seed="course-module-rung",
        max_characters=420,
        max_tokens=100,
    )

    assert result.content == "Name the observation that supports your claim."
    assert result.metadata.provider == "deterministic"
    assert result.metadata.used_live_provider is False
    assert result.metadata.fallback_reason is None


@pytest.mark.asyncio
async def test_live_provider_receives_pseudonymous_request_and_returns_audited_output(monkeypatch):
    captured: list[CompletionRequest] = []

    class FakeProvider:
        async def complete(self, request: CompletionRequest) -> CompletionResult:
            captured.append(request)
            return CompletionResult(
                content="Which detail in the source supports your inference?",
                provider="openrouter",
                model="openrouter/openrouter/free",
                latency_ms=74,
                prompt_tokens=90,
                completion_tokens=12,
                total_tokens=102,
            )

    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(LiteLLMProvider, "from_settings", classmethod(lambda cls: FakeProvider()))

    result = await llm_orchestrator.enhance(
        purpose="socratic_hint_rephrase",
        system_prompt="Use only the supplied public assignment context.",
        user_prompt="Public context: drainage channels. Selected hint: inspect the evidence.",
        deterministic_fallback="Inspect the evidence.",
        pseudonymous_seed="student-session-id-must-not-leave-plaintext",
        max_characters=420,
        max_tokens=100,
    )

    assert result.content == "Which detail in the source supports your inference?"
    assert result.metadata.used_live_provider is True
    assert result.metadata.provider == "openrouter"
    assert result.metadata.total_tokens == 102
    assert captured[0].metadata["user"].startswith("fiosra-")
    assert "student-session-id" not in captured[0].metadata["user"]


@pytest.mark.asyncio
async def test_provider_error_and_answer_leak_both_fall_back_deterministically(monkeypatch):
    class FailingProvider:
        async def complete(self, request: CompletionRequest) -> CompletionResult:
            raise LLMProviderError("provider rate limit")

    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "FIOSRA_LLM_FAILURES_BEFORE_COOLDOWN", 1)
    monkeypatch.setattr(LiteLLMProvider, "from_settings", classmethod(lambda cls: FailingProvider()))

    first_result = await llm_orchestrator.enhance(
        purpose="assignment_scaffold_prompt",
        system_prompt="system",
        user_prompt="public prompt",
        deterministic_fallback="Use the supplied source.",
        pseudonymous_seed="assignment-id",
        max_characters=1600,
        max_tokens=240,
    )
    second_result = await llm_orchestrator.enhance(
        purpose="assignment_scaffold_prompt",
        system_prompt="system",
        user_prompt="public prompt",
        deterministic_fallback="Use the supplied source.",
        pseudonymous_seed="assignment-id",
        max_characters=1600,
        max_tokens=240,
    )

    assert first_result.content == "Use the supplied source."
    assert first_result.metadata.fallback_reason == "provider rate limit"
    assert second_result.metadata.fallback_reason == "provider_cooldown"

    class LeakingProvider:
        async def complete(self, request: CompletionRequest) -> CompletionResult:
            return CompletionResult(
                content="The reference solution is to assert the hidden answer.",
                provider="openrouter",
                model="openrouter/openrouter/free",
                latency_ms=10,
            )

    llm_orchestrator.reset_for_testing()
    monkeypatch.setattr(LiteLLMProvider, "from_settings", classmethod(lambda cls: LeakingProvider()))
    leak_result = await llm_orchestrator.enhance(
        purpose="socratic_hint_rephrase",
        system_prompt="system",
        user_prompt="public prompt",
        deterministic_fallback="Return to the source evidence.",
        pseudonymous_seed="assignment-id",
        max_characters=420,
        max_tokens=100,
    )

    assert leak_result.content == "Return to the source evidence."
    assert "prohibited answer-isolation" in leak_result.metadata.fallback_reason


@pytest.mark.asyncio
async def test_missing_live_provider_credential_keeps_authoring_available(monkeypatch):
    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", None)

    result = await llm_orchestrator.enhance(
        purpose="assignment_scaffold_prompt",
        system_prompt="system",
        user_prompt="public prompt",
        deterministic_fallback="Use the selected course source.",
        pseudonymous_seed="assignment-id",
        max_characters=1600,
        max_tokens=240,
    )

    assert result.content == "Use the selected course source."
    assert result.metadata.used_live_provider is False
    assert "No API key is configured" in result.metadata.fallback_reason


def test_litellm_provider_configuration_supports_named_provider_switches(monkeypatch):
    configurations = [
        ("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "openrouter/openrouter/free"),
        ("openai", "OPENAI_API_KEY", "OPENAI_MODEL", "gpt-4o-mini"),
        ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL", "gemini/gemini-2.5-flash"),
    ]
    for provider, key_field, model_field, model in configurations:
        monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", provider)
        monkeypatch.setattr(settings, key_field, "test-key")
        monkeypatch.setattr(settings, model_field, model)
        configured = LiteLLMProvider.from_settings()
        assert configured.provider_name == provider
        assert configured.model == model

    monkeypatch.setattr(settings, "FIOSRA_LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_MODEL", "ollama/llama3.2")
    configured = LiteLLMProvider.from_settings()
    assert configured.provider_name == "ollama"
    assert configured.api_base == "http://localhost:11434"


@pytest.mark.asyncio
async def test_litellm_adapter_uses_async_completion_with_normalized_configuration(monkeypatch):
    import litellm

    captured: dict = {}

    async def fake_acompletion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=" A bounded Socratic prompt. "))],
            model="openrouter/openrouter/free",
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=7, total_tokens=12),
        )

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    provider = LiteLLMProvider(
        provider_name="openrouter",
        model="openrouter/openrouter/free",
        api_key="test-key",
        api_base="https://openrouter.ai/api/v1",
    )
    result = await provider.complete(
        CompletionRequest(
            system_prompt="System boundary",
            user_prompt="Public source context",
            purpose="socratic_hint_rephrase",
            max_tokens=100,
            metadata={"user": "fiosra-opaque"},
        )
    )

    assert result.content == "A bounded Socratic prompt."
    assert result.total_tokens == 12
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["api_key"] == "test-key"
    assert captured["user"] == "fiosra-opaque"
    assert captured["num_retries"] == 0
