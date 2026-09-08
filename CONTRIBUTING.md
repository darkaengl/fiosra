# Contributing to Fiosra

Thank you for your interest in contributing to Fiosra! Fiosra is a reasoning infrastructure layer designed to make the development of knowledge visible and verifiable.

To maintain architectural integrity, prevent massive unreviewable PRs, and ensure verifiable traceability, **all contributions follow a strict Fork-and-Pull-Request workflow governed by an Epic ➔ Sub-Issue ➔ PR hierarchy.**

---

## ⛔ Strict Contribution Policy: No Direct Pushes

> [!CAUTION]
> **Direct pushes to `main` (or any branch in `darkaengl/fiosra`) are strictly disabled and will be rejected.**
> 
> * **Fork Required**: All contributors must fork the repository to their personal GitHub account, create a feature branch in their fork, and open a Pull Request against upstream `darkaengl/fiosra:main`.
> * **Issue Alignment Required**: Every Pull Request must correspond to a **scoped sub-issue** that rolls up into an open **Epic** (e.g. Epic [#7](https://github.com/darkaengl/fiosra/issues/7), [#8](https://github.com/darkaengl/fiosra/issues/8), [#9](https://github.com/darkaengl/fiosra/issues/9), [#10](https://github.com/darkaengl/fiosra/issues/10)). Pull Requests opened without a linked tracked issue will not be reviewed and will be closed.

---

## 🏛️ The Fiosra Issue & PR Hierarchy

To keep pull requests atomic, focused, and fast to review (under 300 lines of code), we use a two-tier issue hierarchy:

```
┌────────────────────────────────────────────────────────┐
│  PARENT EPIC (e.g. #7: Dual-Database Foundation)       │  <-- High-level milestone & architectural goal
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│  SUB-ISSUE (e.g. #11) │       │  SUB-ISSUE (e.g. #12) │   <-- Scoped, claimable task (< 300 LOC)
│  "Async Neo4j Client" │       │  "Postgres Migration" │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│  PULL REQUEST (PR)    │       │  PULL REQUEST (PR)    │   <-- Atomic PR in fork targeting upstream
│  Closes #11 (Ref #7)  │       │  Closes #12 (Ref #7)  │
└───────────────────────┘       └───────────────────────┘
```

1. **Epics (Milestones)**: High-level architectural tracks created by maintainers that define end-to-end deliverables with an overarching checklist.
2. **Sub-Issues (Actionable Units)**: Bite-sized tasks addressing a single component, file, or feature within an Epic. If a sub-issue does not exist for an unchecked item on an Epic, **you can create one before starting work**.
3. **Pull Requests (Atomic Delivery)**: Code changes that close a specific sub-issue and reference the parent Epic.

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

### Step 1: Find or Create a Scoped Sub-Issue
1. Review the open **[Milestone Epics](https://github.com/darkaengl/fiosra/issues)** ([#7](https://github.com/darkaengl/fiosra/issues/7), [#8](https://github.com/darkaengl/fiosra/issues/8), [#9](https://github.com/darkaengl/fiosra/issues/9), [#10](https://github.com/darkaengl/fiosra/issues/10)).
2. Choose an unchecked subtask from an Epic.
3. Check if a sub-issue already exists:
   - If **yes**, comment on the sub-issue: *"I'd like to work on this!"*
   - If **no**, create a new sub-issue linking back to the parent Epic:
     - **Title**: `[Subtask of #<epic_number>] <Concise feature description>`
     - **Body**: Describe the exact scope, component, and link to the parent Epic (`Part of Epic #<epic_number>`).

### Step 2: Fork the Repository
1. Click **Fork** on [`darkaengl/fiosra`](https://github.com/darkaengl/fiosra) to create a copy in your personal GitHub account.
2. Clone your personal fork locally:
   ```bash
   git clone https://github.com/<your-github-username>/fiosra.git
   cd fiosra
   ```
3. Set upstream remote to stay synchronized:
   ```bash
   git remote add upstream https://github.com/darkaengl/fiosra.git
   git fetch upstream
   ```

### Step 3: Create a Dedicated Feature Branch
Create a feature branch named after your specific sub-issue:
```bash
git checkout -b feature/issue-<subissue_number>-<short-description>
# Example: git checkout -b feature/issue-11-neo4j-async-client
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
git push origin feature/issue-<subissue_number>-<short-description>
```

### Step 6: Open a Pull Request against Upstream
1. Navigate to [`darkaengl/fiosra/pulls`](https://github.com/darkaengl/fiosra/pulls) and click **New Pull Request**.
2. Select `base: main` and `compare: <your-username>:feature/issue-<subissue_number>-<short-description>`.
3. **Fill out the [Pull Request Template](.github/pull_request_template.md) completely**:
   - Specify the linked sub-issue: `Closes #<subissue_number>`
   - Specify the parent Epic: `Part of Epic #<epic_number>`
   - Check off all architectural invariants and verification checkboxes.
4. Ensure automated CI checks pass. A maintainer will review and merge your PR.

---

## 🤝 Code of Conduct
All contributors and participants in the Fiosra project are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any violations or concerns to **conduct@fiosra.org**.
