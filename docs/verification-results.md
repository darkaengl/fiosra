# Validation Results

## Automated checks

On 2026-09-10, the repository passed the full backend suite with **56 passing tests**. The validation command also completed `ruff check fiosra tests`, the Svelte production build, and `git diff --check` successfully.

## Local integrated services

A local PostgreSQL 16 instance with pgvector and a local Neo4j 5 instance were initialized from the repository migrations and seed pipeline. The seed pipeline completed with 19 knowledge components, 21 prerequisite edges, and 25 misconception records. This environment was used for the backend test suite.

## Browser smoke test

The built FastAPI-served Svelte application was opened at `/ui/#/courses` and `/ui/#/designer`. The course portfolio rendered the live course list and navigation, while the redesigned Assignment Scaffold Designer rendered its live input form, module selector, scope-analysis action, and protected-preview state without layout or runtime errors.

The designer form was also populated through the browser automation interface, confirming that the editable title and prompt fields are bound and usable in the production bundle.

Live scope analysis returned a specificity assessment and the subsequent scaffold generation rendered the clarified task, target knowledge components, five-rung bounded hint ladder, locked bottom-out rung, and rubric criteria. This confirms the educator design flow is connected to the FastAPI endpoints rather than using static placeholders.

## Workflow contracts verified by regression tests

The suite now asserts that the public assignment projection does not disclose the Answer Vault token or reference solution, and that a session submitted for educator review rejects subsequent student dialogue writes. The existing end-to-end suite additionally exercises drafting, publishing, dialogue, evidence synthesis, and educator finalization.
