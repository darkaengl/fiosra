# Fiosra: Long-Term Reference & Research Architecture

This directory contains the **long-term research specifications, master theoretical frameworks, and full multi-agent designs** for Fiosra. 

These documents describe the full-scale vision beyond the initial 3–4 week lean MVP implementation.

---

## Contents

### 1. Master Architecture Vision
- **[`README_MASTER_VISION.md`](README_MASTER_VISION.md)**: The comprehensive architectural specification, covering:
  - Theoretical foundations and cognitive design principles
  - Poincaré hyperbolic ball embeddings ($\mathbb{D}^{32}$) for curriculum DAGs
  - Event-driven streaming architecture (Kafka, TimescaleDB, Neo4j)
  - Full multi-agent orchestration lifecycle

### 2. Full Research Agent Specifications (`agents/`)
Detailed functional contracts and prompt architectures for the 6 core research agents:
- **[`agents/orchestrator.md`](agents/orchestrator.md)**: Session lifecycle, finite state machine, and answer-isolation guardrails.
- **[`agents/assignment_design_agent.md`](agents/assignment_design_agent.md)**: Syllabus grounding, Graph-Structured Rubrics (GSR), and misconception-seeded distractors.
- **[`agents/student_interaction_agent.md`](agents/student_interaction_agent.md)**: Socratic dialogue management and "Thoughts of Tutorbot" diagnostic state.
- **[`agents/knowledge_tracing_agent.md`](agents/knowledge_tracing_agent.md)**: L-HAKT hyperbolic knowledge tracing and Riemannian optimization.
- **[`agents/misconception_diagnosis_agent.md`](agents/misconception_diagnosis_agent.md)**: Generate $\to$ Retrieve $\to$ Rerank diagnostic pipeline with vector search.
- **[`agents/evidence_scoring_agent.md`](agents/evidence_scoring_agent.md)**: AutoSCORE two-stage extraction $\to$ rubric alignment and structured evidence packets ($Z$).

---

> [!TIP]
> For the active, lean 3–4 week build specifications, refer to the primary project [MVP Architecture](../README.md) and [`fiosra/mvp/`](../mvp/).
