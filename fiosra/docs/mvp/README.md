# Fiosra MVP: Modular Component Architecture

> **Fiosra** is a reasoning infrastructure layer for education.
> 
> It helps educators design environments where thinking can be developed and gives students the space and support to demonstrate that thinking, while creating a student-owned record of learning over time.

---

## 1. Overview & Directory Structure

This `mvp/` directory contains the modular architecture, functional contracts, and implementation blueprints for the **Fiosra Minimum Viable Product (MVP)**.

The system is partitioned into six decoupled, self-contained components designed to run on a single unified PostgreSQL database and FastAPI backend:

```
fiosra/mvp/
├── README.md                     # Master architecture overview (this file)
│
├── assignment_designer/          # Component 1: Educator Studio & Syllabus RAG
│   └── README.md                 # Question drafting, hint authoring, misconception traps
│
├── policy_engine/                # Component 2: Pedagogical Policy & Multi-Domain Verifier
│   └── README.md                 # Answer vault, hint ceilings, SymPy / AST / NLI verifiers
│
├── socratic_tutor/               # Component 3: Socratic Interaction Agent
│   └── README.md                 # Answer-blind dialogue, 4-rung hint ladder, Thoughts of Tutorbot
│
├── knowledge_layer/              # Component 4: Curriculum DAG & Misconception Store
│   └── README.md                 # Relational prerequisite DAG, NetworkX cache, pgvector taxonomy
│
├── event_store/                  # Component 5: JSON Event Store & Session Manager
│   └── README.md                 # Append-only jsonb transaction log, GIN indexes, session state
│
└── evidence_dossier/             # Component 6: Evidence & Scoring Dossier Engine
    └── README.md                 # AutoSCORE light, timeline synthesis, 1-click teacher review
```

---

## 2. End-to-End Component Interaction Map

```mermaid
flowchart TB
    subgraph UI [Frontend Next.js]
        T_UI["Educator Studio Author and Review"]
        S_UI["Student Workspace Socratic Learning"]
    end

    subgraph CoreServices [FastAPI Application Services]
        AD["1. Assignment Designer RAG and Distractor Engine"]
        PE["2. Policy Engine and Verifier Answer Vault and Checkers"]
        ST["3. Socratic Tutor Answer-Blind Guidance"]
        KL["4. Knowledge Layer Curriculum DAG and Misconceptions"]
        ES["5. JSON Event Store Append-Only Engine"]
        ED["6. Evidence Dossier Engine AutoSCORE Light"]
    end

    subgraph Data [PostgreSQL 16]
        DB["Unified Database Tables jsonb Logs pgvector"]
    end

    %% Educator Flow
    T_UI -->|1. Request Draft| AD
    AD <-->|Query Prereqs| KL
    AD <-->|Verify Solutions| PE
    AD -->|Save Assignment Spec| DB

    %% Student Learning Flow
    S_UI <-->|2. Interactive Problem Solving| ST
    ST <-->|Request Hint Ceiling| PE
    S_UI -->|Submit Step| PE
    PE <-->|Match Common Traps| KL
    PE -->|Emit Action Result| ST
    PE -->|Log Micro-Step| ES
    ST -->|Log Dialogue Turn| ES
    ES -->|Append jsonb Row| DB

    %% Evidence & Review Flow
    S_UI -->|3. Submit Assignment| ED
    ED -->|Replay Events| ES
    ED -->|Compile Packet Z| DB
    T_UI <-->|4. Review Evidence Dossier| ED
```

---

## 3. The 6 MVP Components at a Glance

| Component | Primary Function | Primary Technology | Spec Link |
|:---|:---|:---|:---|
| **1. Assignment Designer** | Co-pilots assignment creation with teachers across STEM and Humanities. Seeds questions with diagnostic misconception traps. | LLM (Claude 3.5 Sonnet) + Syllabus RAG | [assignment_designer/README.md](assignment_designer/README.md) |
| **2. Policy Engine & Verifier** | Holds reference answers in isolation. Computes allowable hint rungs. Dispatches verification to SymPy (math), Test Runner (code), or NLI (humanities). | Python + SymPy + PyTest + NLI Semantic Match | [policy_engine/README.md](policy_engine/README.md) |
| **3. Socratic Tutor** | Interacts directly with students. Probes misconceptions and delivers graduated hints without ever seeing or giving the final answer. | LLM Prompt with strict answer-isolation guardrails | [socratic_tutor/README.md](socratic_tutor/README.md) |
| **4. Knowledge Layer** | Represents learning objectives, curriculum prerequisite trees, and cataloged student misconceptions. | PostgreSQL Relational DAG + NetworkX in-memory + `pgvector` | [knowledge_layer/README.md](knowledge_layer/README.md) |
| **5. JSON Event Store** | Records every keystroke, student attempt, hint delivered, and dwell time in an immutable chronological flight recorder. | PostgreSQL `jsonb` + GIN Indexing | [event_store/README.md](event_store/README.md) |
| **6. Evidence Dossier** | Replays transaction events to synthesize the AutoSCORE Evidence Packet ($Z$), highlighting self-corrections and rubric fulfillment. | Python Extraction Pipeline + Next.js Review UI | [evidence_dossier/README.md](evidence_dossier/README.md) |

---

## 4. Multi-Domain Support (STEM & Humanities)

Unlike math-only systems, the Fiosra MVP architecture is domain-pluggable:

1. **Mathematics & Science**:
   - Verification Engine: **SymPy (Computer Algebra System)**.
   - Evidence Check: Algebraic equivalence ($E_{\text{student}} - E_{\text{target}} == 0$).
2. **Computer Science & Coding**:
   - Verification Engine: **Sandboxed Python AST & Test Runner**.
   - Evidence Check: Test assertions, syntax validity, edge cases.
3. **History, Business & Language Arts**:
   - Verification Engine: **AutoSCORE Semantic Claim Matcher**.
   - Evidence Check: Natural Language Inference (NLI) verifying that the student's text contains required claims, textual citations, and causal explanations.

---

## 5. Development Getting Started

1. **Database Setup**: Ensure PostgreSQL 16 is running with `pgvector` enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. **Environment Configuration**:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/fiosra_db
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. **Explore Individual Component Specs**:
   - Review each component folder for detailed API contracts, class definitions, and step-by-step algorithms.
