## Description

Briefly describe the purpose of this Pull Request and the problem it solves.

Closes #(issue)

---

## Type of Change

- [ ] 🚀 New feature (non-breaking change adding functionality)
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] 🛠️ Refactoring / Code cleanup (no behavioral changes)
- [ ] 📚 Documentation update
- [ ] ⚙️ Infrastructure / CI / Dependencies

---

## Component(s) Affected

- [ ] `assignment_designer` (Component 1: Question generation & distractor traps)
- [ ] `policy_engine` (Component 2: Answer Vault, SymPy CAS verifiers, hint ceiling)
- [ ] `socratic_tutor` (Component 3: Conversational Socratic guide)
- [ ] `knowledge_layer` (Component 4: NetworkX curriculum DAG & pgvector)
- [ ] `event_store` (Component 5: Append-only session flight recorder)
- [ ] `evidence_dossier` (Component 6: AutoSCORE light synthesis)
- [ ] `frontend` (Next.js web applications)
- [ ] `infra / database` (Docker, PostgreSQL migrations)

---

## 🧭 Architectural Invariants Checklist

Before submitting, please verify that this PR upholds Fiosra's core architectural tenets:

- [ ] **Strict Answer Isolation**: Student-facing prompts (`socratic_tutor`) **never** receive the reference answer or solution.
- [ ] **Deterministic Verification**: Math/symbolic claims are checked by SymPy CAS or unit tests, not probabilistic LLM predictions.
- [ ] **Non-Manipulable Hint Ladder**: Hint rungs cannot be accelerated through adversarial student prompt injection.
- [ ] **Immutable Event Logging**: Key learner actions emit structured JSON events to `session_events`.

---

## 🧪 Testing Performed

- [ ] Unit tests added / updated in `fiosra/tests/`
- [ ] Ran `make test` (all tests passing)
- [ ] Ran `make lint` (no ruff linting errors)

### Test Commands / Verification Steps:
```bash
# Example command run:
pytest fiosra/tests/ -v
```

---

## Checklist

- [ ] My code follows the project's [Code of Conduct](CODE_OF_CONDUCT.md).
- [ ] I have read the [Contributing Guidelines](CONTRIBUTING.md).
- [ ] I have commented complex or non-obvious logic.
- [ ] I have updated relevant documentation where necessary.
