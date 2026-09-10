# Live LLM Provider Verification

## Default-provider browser check

The built Fiosra application was launched with `FIOSRA_LLM_PROVIDER=deterministic`. The educator Assignment Scaffold Designer loaded normally, accepted a title and a course-grounded inquiry prompt, and remained fully usable without a provider credential or a network model call. This confirms that LiteLLM is an optional enhancement rather than a startup or authoring dependency.

The remaining browser action generates the scaffold and verifies that the educator-facing provenance line reports deterministic generation when no external provider is enabled.

## Deterministic scaffold result

The educator triggered scope analysis and scaffold generation with no live provider configured. The application returned the existing answer-isolated scaffold successfully, displayed the explicit **Deterministic wording** provenance line, and did not require a credential, model response, or outbound provider call. The preview continued to show the locked bottom-out rung and source-grounding publication warning, confirming that the optional LLM layer did not weaken the existing authoring controls.
