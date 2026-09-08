# Contributing to Fiosra

Thank you for your interest in contributing to Fiosra! Fiosra is a reasoning infrastructure layer designed to make the development of knowledge visible and verifiable.

To maintain architectural integrity, code quality, and verifiable traceability, **all contributions must follow the strict Fork-and-Pull-Request workflow outlined below.**

---

## ⛔ Strict Contribution Policy: No Direct Pushes

> [!CAUTION]
> **Direct pushes to `main` (or any branch in `darkaengl/fiosra`) are strictly disabled and will be rejected.**
> 
> * **Fork Required**: All contributors must fork the repository to their personal GitHub account, create a feature branch within their fork, and open a Pull Request against upstream `darkaengl/fiosra:main`.
> * **Issue Alignment Required**: **Every Pull Request must fall under an existing open issue** (e.g. Epic [#7](https://github.com/darkaengl/fiosra/issues/7), [#8](https://github.com/darkaengl/fiosra/issues/8), [#9](https://github.com/darkaengl/fiosra/issues/9), [#10](https://github.com/darkaengl/fiosra/issues/10) or an approved sub-issue). Pull Requests opened without a linked tracked issue will not be reviewed and will be closed.

---

## 🧭 Architectural Constraints (Non-Negotiables)

When contributing code to Fiosra, you must preserve these four invariant boundaries:

1. **Strict Answer Isolation**:
   - The student-facing conversational tutor in `fiosra/mvp/dialogue/` **must never receive the reference answer or solution** in its context or prompts.
   - Reference answers are encrypted inside the Answer Vault and only accessed by deterministic verifiers.

2. **Deterministic Verification Outranks LLMs**:
   - Text claim rubric matching **must** pass through DeBERTa-v3 Natural Language Inference (NLI) premise-hypothesis entailment.
   - Math/symbolic claims **must** pass through SymPy CAS.
   - Never rely on an LLM's subjective impression to judge correctness.

3. **Anti-Manipulation Hint Ladders**:
   - Allowable hint rungs ($H_d = 0.25$) are calculated strictly by `compute_hint_ceiling()` based on session state and attempt history.
   - Prompts from students pleading for answers or using adversarial jailbreaks must be safely deflected using Socratic probes.

4. **Append-Only Event Store**:
   - All student actions, hint requests, speech-to-thought crystalizations, and claim verifications must emit immutable events to PostgreSQL `session_events`.
   - The AutoSCORE dossier engine strictly derives its report by replaying this log.

---

## 🛠️ Step-by-Step Developer Workflow

### Step 1: Identify or Reference an Existing Issue
Before writing any code, locate the existing open issue in **[`darkaengl/fiosra/issues`](https://github.com/darkaengl/fiosra/issues)** that covers your work. If your proposed work does not fall under an existing issue, open a discussion or issue first to get consensus.

### Step 2: Fork the Repository
1. Click the **Fork** button on GitHub to fork [`darkaengl/fiosra`](https://github.com/darkaengl/fiosra) to your personal account.
2. Clone your personal fork locally:
   ```bash
   git clone https://github.com/<your-github-username>/fiosra.git
   cd fiosra
   ```
3. Set the upstream remote:
   ```bash
   git remote add upstream https://github.com/darkaengl/fiosra.git
   git fetch upstream
   ```

### Step 3: Create a Dedicated Feature Branch
Always create a descriptive feature branch prefixed with the issue number:
```bash
git checkout -b feature/issue-<number>-<short-description>
# Example: git checkout -b feature/issue-7-neo4j-async-driver
```

### Step 4: Develop, Format & Test
1. **Code Standards**:
   - We format and lint Python code using `ruff`:
     ```bash
     make lint
     ```
   - Use explicit type hints (`from typing import List, Optional, Dict, Any`) across all models, services, and routers.
   - All request and response bodies must be typed Pydantic models.
2. **Testing**:
   - Every new service or route must include automated tests in `tests/`:
     ```bash
     make test
     ```
   - All tests must pass cleanly before opening a PR.

### Step 5: Push to Your Fork
Commit your changes with clear, semantic commit messages and push to your fork:
```bash
git push origin feature/issue-<number>-<short-description>
```

### Step 6: Open a Pull Request against Upstream
1. Navigate to [`darkaengl/fiosra/pulls`](https://github.com/darkaengl/fiosra/pulls) and click **New Pull Request**.
2. Select `base: main` and `compare: <your-username>:feature/issue-<number>-<short-description>`.
3. **Fill out the [Pull Request Template](.github/pull_request_template.md) completely**:
   - You **must** specify the linked issue in the header (`Closes #<issue_number>`).
   - Check off all architectural invariants and testing checkboxes.
4. Ensure automated CI checks pass. A maintainer will review your submission.

---

## 🤝 Code of Conduct
All contributors and participants in the Fiosra project are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any violations or concerns to **conduct@fiosra.org**.
