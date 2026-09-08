# Contributing to Fiosra

Thank you for contributing to Fiosra! This guide outlines our architectural constraints, coding standards, and developer workflows.

---

## 🧭 Architectural Constraints (Non-Negotiables)

When contributing code to Fiosra, you must preserve these four invariant boundaries:

1. **Strict Answer Isolation**:
   - The conversational tutor in `fiosra/mvp/socratic_tutor/` **must never receive the answer** in its context or prompts.
   - All evaluation is performed deterministically by `fiosra/mvp/policy_engine/`.

2. **Deterministic Verification**:
   - Math and algebra equivalence **must** pass through SymPy CAS in `fiosra/mvp/policy_engine/verifiers.py`.
   - Never rely on an LLM to judge mathematical correctness when symbolic equality can be checked.

3. **Anti-Manipulation Hint Ladders**:
   - The allowable hint level is calculated by `compute_hint_ceiling()` based on session state and attempt count.
   - Prompts from students pleading for answers or using jailbreak templates must be safely rejected.

4. **Append-Only Event Store**:
   - All student actions must emit immutable events to `session_events` via `fiosra/mvp/event_store/`.
   - The dossier engine (`evidence_dossier`) strictly derives its report by replaying this log.

---

## 🛠️ Development Workflow

### 1. Branching
- Create descriptive feature branches from `main`:
  ```bash
  git checkout -b feature/component-name-feature-description
  ```

### 2. Code Standards
- We format and lint Python code using `ruff`:
  ```bash
  make lint
  ```
- Use type hints (`from typing import List, Optional, Dict, Any`) across all models, services, and endpoints.
- All request and response bodies must be typed Pydantic models.

### 3. Testing Requirements
- Every new endpoint or service function must include test coverage in `fiosra/tests/`:
  ```bash
  make test
  ```
- All tests must pass before submitting a Pull Request.

---

## 📦 Adding a New Subsystem or Migration
1. If modifying database tables, create a new SQL file in `fiosra/mvp/migrations/` (e.g., `002_add_feature_x.sql`).
2. If adding a new FastAPI route, define it in the relevant component's `router.py` and register it in `fiosra/mvp/app.py`.

---

## 🔀 Submitting a Pull Request
1. Push your feature branch to your fork or origin.
2. Open a Pull Request against `main`.
3. Fill out the [Pull Request Template](.github/pull_request_template.md), ensuring you check off all relevant **Architectural Invariants**.
4. Verify that CI / automated tests pass.

---

## 🤝 Code of Conduct
All contributors and participants in the Fiosra project are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any violations or concerns to **conduct@fiosra.org**.

