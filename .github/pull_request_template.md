## 🔗 Linked Issue (Mandatory)

> [!IMPORTANT]
> **Every Pull Request must correspond to an existing open issue in `darkaengl/fiosra` (e.g. Epic #7, #8, #9, #10).**
> Pull Requests opened without an associated issue will be closed automatically.

Closes # <!-- Specify issue number here, e.g., #7 -->

---

## 📝 Description

Briefly describe the purpose of this Pull Request, what was changed, and how it addresses the linked issue.

---

## 🛡️ Contribution & Workflow Verification

Before proceeding, please verify that you adhered to the [Contributing Guidelines](CONTRIBUTING.md):

- [ ] **No Direct Push**: This PR is submitted from a feature branch on a **forked repository** (not directly pushed to upstream `darkaengl/fiosra`).
- [ ] **Tracked Issue Alignment**: This PR directly addresses an existing, open issue in `darkaengl/fiosra` specified above.

---

## 🏷️ Type of Change

- [ ] 🚀 New feature / Epic milestone deliverable
- [ ] 🐛 Bug fix (non-breaking fix for an existing issue)
- [ ] 🛠️ Refactoring / Code quality (no functional change)
- [ ] 📚 Documentation update / Specification
- [ ] ⚙️ Infrastructure / Database migration / CI

---

## 📦 Component(s) Affected

- [ ] `database / migrations` (PostgreSQL schema, courses, modules)
- [ ] `knowledge_graph` (Neo4j client, Cypher DAG, prerequisite traversal)
- [ ] `seed_data` (Language & History misconceptions, 4-rung hint ladders)
- [ ] `event_store` (Append-only session event engine, PostgreSQL logger)
- [ ] `dialogue_engine` (Answer-isolated Socratic tutor, prompt guardrails)
- [ ] `verifiers` (DeBERTa-v3 NLI text claim verifier, SymPy CAS)
- [ ] `evidence_dossier` (AutoSCORE Light synthesizer, Packet Z)
- [ ] `ui-ux / frontend` (Interactive semantic HTML/CSS screens)

---

## 🧭 Architectural Invariants Checklist

Fiosra enforces four strict non-negotiable architectural boundaries. Please verify that this PR respects all of them:

- [ ] **Strict Answer Isolation**: Student-facing prompts (`dialogue_engine`) **never** receive the reference answer or solution.
- [ ] **Deterministic Verification**: Correctness claims are verified by deterministic logic engines (DeBERTa NLI premise-hypothesis entailment or SymPy CAS), never subjective LLM guesswork.
- [ ] **Non-Manipulable Hint Ladder**: Hint progression ($H_d = 0.25$) is mathematically governed by `compute_hint_ceiling()` and cannot be bypassed via student prompt injection.
- [ ] **Append-Only Event Store**: Key student actions, speech-to-thought crystalizations, and claim verifications emit immutable events to PostgreSQL `session_events`.

---

## 🧪 Testing Performed

- [ ] Automated tests added or updated in `tests/`
- [ ] Ran `make test` (all tests passing)
- [ ] Ran `make lint` (no ruff linting or formatting errors)

### Test Commands Executed:
```bash
# Example test run:
pytest tests/ -v
```

---

## 📋 General Checklist

- [ ] My code adheres to the project's [Code of Conduct](CODE_OF_CONDUCT.md).
- [ ] I have read and followed the [Contributing Guidelines](CONTRIBUTING.md).
- [ ] Complex or non-obvious code paths are clearly documented with docstrings and comments.
- [ ] Any required schema migration or config updates are included.
