# Fiosra MVP Architecture & UX/UI Specification
### Canonical Synthesis of Technical Infrastructure & Product Experience Blueprint (Phases 1–7)

> **Fiosra** is a structured learning environment that makes the development of knowledge visible.
> It sits between existing institutional LMS infrastructure and the student's active inquiry, capturing an authentic, auditable **Reasoning Trace** of thinking over time without reducing learners to surveillance data.

---

## 🧭 Executive Summary & Core Philosophy

### 1. What Fiosra Is vs. What It Is Not

| What Fiosra IS | What Fiosra IS NOT |
|:---|:---|
| **A Reasoning Infrastructure Layer** providing an environment for inquiry, struggle, and evidence. | **An LMS Replacement** (it connects to and grounds within course materials; it does not replace Moodle/Canvas). |
| **A Structured Workspace** balancing freedom to think with a clear path forward (*Structured Freedom*). | **An AI Chatbot / Answer Machine** (AI is an ambient capability, not the interface itself). |
| **An Evidence Synthesis Engine** capturing meaningful developmental milestones. | **A Surveillance / Keystroke Logging Tool** (activity $\neq$ evidence; time spent $\neq$ effort). |
| **A Human-in-the-Loop Evaluator** surfacing signals that invite educator context. | **An Automated Grading Engine** (AI never silently assumes authority over final student evaluation). |
| **Quiet, Purposeful Interface** using progressive disclosure to maintain focus. | **Gamified Education / Analytics Theatre** (no streaks, points, confetti, badges, or walls of charts). |

### 2. Core Metaphor: Knowledge in Motion
Fiosra draws from the Irish verb for active pursuit and inquiry into knowledge. Knowledge is not static or stored; it is investigated, developed, and transformed. The design avoids clichéd academic motifs (books, brains, graduation caps, neural nets, chatbots) in favor of **The Emergent Path**—a visual metaphor of trajectories, convergence, and progressive inquiry.

---

## 🎨 Prescribed Brand & Design Language System (Phase 5)

Fiosra's aesthetic is **Quietly Futuristic**: restrained, spacious, dimensional, and calm.

### 1. Color System: Deep Mineral + Electric Horizon

The product lives primarily in a calm, warm-neutral environment. Color communicates **state, focus, and meaning—never decoration**.

| Token Name | Hex Code | Role in Interface |
|:---|:---|:---|
| **Bone** | `#F6F5F1` | **Primary Light Background**: Warm neutral avoiding the sterile, clinical feel of pure white. |
| **Obsidian** | `#111315` | **Primary Dark Surface / Text**: High-authority text and dominant dark-mode background. |
| **Graphite** | `#23272B` | **Secondary Dark Surface**: Elevated dark containers and modals. |
| **Cloud** | `#E9E8E3` | **Secondary Light Surface**: Subtle card backgrounds and surface separations. |
| **Slate** | `#6D7378` | **Secondary Metadata**: Supporting labels, captions, and structural borders. |
| **Horizon Blue** | `#4F6BFF` | **Primary Accent**: Active states, forward motion, focus, and primary actions. |
| **Aurora** | `#7B61FF` | **Secondary Accent**: Intelligence states, generative moments, and subtle transitions. |
| **Signal Green** | `#5FAF7A` | **Progress Accent**: Muted, mature indicator of genuine completion (not celebratory confetti). |
| **Amber** | `#D89A3A` | **Attention Accent**: Meaningful signals requiring review or educator context. |
| **Deep Red** | `#B74C4C` | **Error Accent**: Strictly reserved for destructive actions and system failures. **Banned from student educational feedback.** |

> [!IMPORTANT]
> **No Red for Educational Feedback**: Incorrect student attempts must never trigger red warning banners. Errors are normal developmental steps—they trigger neutral or amber Socratic inquiry prompts.

### 2. Signature Gradient
Used sparingly for brand moments, onboarding, and intelligence states:
$$\text{Horizon Blue } (\#\text{4F6BFF}) \longrightarrow \text{Aurora } (\#\text{7B61FF})$$
*Rule:* If the gradient disappeared tomorrow, the interface must still look distinctly like Fiosra.

### 3. Typography Hierarchy
- **Display / Brand**: *Instrument Sans* (or contemporary characterful grotesk).
- **Interface & Workspace**: *Inter* or *Geist* (neutral, highly legible sans-serif with tabular numerical support).
- **Tone**: Calm, direct, confident, and human. **No motivational microcopy, artificial enthusiasm, or exclamation marks.**

### 4. Spatial Scale & Geometry
- **Consistent Grid Scale**: `4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px`.
- **Corner Radii**: Small (`6px`), Standard (`10px`), Large (`16px`), Feature (`24px`).
- **Surface Restraint**: Depth is created through typography and whitespace, **not shadow proliferation or "cards-inside-cards" syndrome**.

### 5. Motion & Progressive Emergence
- **Durations**: Micro feedback (`100–150ms`), Component transitions (`150–220ms`), Panel transitions (`200–300ms`).
- **Signature Behavior**: *Progressive Emergence*—information unfolds as the user moves deeper:
  $$\text{Level 1 (What matters now)} \longrightarrow \text{Level 2 (What explains it)} \longrightarrow \text{Level 3 (Supporting evidence)} \longrightarrow \text{Level 4 (Full depth)}$$

---

## ✅ Architectural & UX Decision Log (Conflicts Resolved)

All 7 flagged conflicts between the initial candidate technical architecture (`mvp_architecture.pdf`) and the canonical Product Blueprint (Phases 1–7) have been **decided and resolved**:

| # | Conflict Area | Original Technical Blueprint | Canonical Product Blueprint | Decision |
|:--|:---|:---|:---|:---|
| 1 | **AI Workspace Surface** | Split-screen persistent chat panel | Contextual, embedded pop-in that recedes | ✅ ADOPT |
| 2 | **Reasoning Trace** | Raw flight-recorder event replay | *"A Path Made Visible"* node graph | ✅ ADOPT |
| 3 | **Observability View** | Analytics dashboard (charts/graphs) | Attention-signal triage queue | ✅ ADOPT |
| 4 | **Feedback Tone** | Gamified percentages & red alerts | Quiet, earned progress & amber cues | ✅ ADOPT |
| 5 | **Assignment Grounding** | Isolated standalone question JSON | Grounded in Course/Module simulated LMS | ✅ ADOPT |
| 6 | **Agent Topology** | 6 independently deployed services | 3 functional roles in 1 application | ✅ ADOPT |
| 7 | **Knowledge Infrastructure** | pgvector + flat NetworkX Python DAG | Relational SQL queries only | ⚡ CUSTOM |

> [!IMPORTANT]
> **Decision for Flag 7 (Custom)**: We reject **both** the original flat `NetworkX` in-memory Python DAG *and* the canonical blueprint's simplification to plain SQL. The chosen architecture is a **hybrid graph + vector model**:
> - **Neo4j**: Owns concept-level hierarchy — `KnowledgeConcept` nodes, `REQUIRES` prerequisite edges, and `ASSOCIATED_WITH` edges to misconceptions.
> - **pgvector** (PostgreSQL): Owns semantic misconception embeddings — cosine similarity lookup diagnosing the *type* of error from free-text student input.
> - **Why not flat relational?** Concept hierarchies are inherently recursive. SQL recursive CTEs become brittle at depth. Neo4j Cypher is purpose-built for ancestor traversal, frontier detection, and bidirectional concept-misconception association queries.

### 🚩 Flag 1: AI Workspace Surface — Floating Contextual Guidance vs. Split-Screen Chat
- **Current Technical Model**: The frontend often defaults to a two-pane layout with a permanent chat interface occupying 50% of the screen.
- **Canonical UX Requirement (Phase 3.13)**: The AI **must never permanently dominate the screen**. The student is in a workspace, not a chat session.
- **Prescribed UX**: The dominant surface is the **Active Work Canvas**. The Dialogue Agent appears contextually when summoned or triggered, offers Socratic guidance, and smoothly recedes to the background upon resumption of active work.

### 🚩 Flag 2: Reasoning Trace — "A Path Made Visible" vs. Raw Event Log Replay
- **Current Technical Model**: Focuses on chronological event streams (`session_events` table) and JSON transaction logs.
- **Canonical UX Requirement (Phase 5.40)**: The Reasoning Trace is **not** an activity log, git commit trail, or transcript. It is a structured visual artifact: *A Path Made Visible*.
- **Prescribed UX**: An interactive node-based path showing developmental moments:
  $$\text{Beginning} \longrightarrow \text{Exploration} \longrightarrow \text{Concept Shift} \longrightarrow \text{Development} \longrightarrow \text{Revision} \longrightarrow \text{Finalisation}$$
  Clicking a node progressively discloses quotes and evidence without exposing raw database payloads.

### 🚩 Flag 3: Educator Observability — Signal Triage vs. Wall-of-Charts Analytics
- **Current Technical Model**: Visualizes dwell time distributions, hint dependency ratios, and statistical bar charts.
- **Canonical UX Requirement (Phase 2.25 & 3.16)**: **Observability $\neq$ Analytics.** Analytics asks *"What happened?"* Observability asks *"What deserves my attention right now?"*
- **Prescribed UX**: A prioritized signal triage list following `Signal -> Context -> Interpretation -> Action`. Avoid walls of charts, percentages, and red/yellow/green grids.

### 🚩 Flag 4: Tone & Feedback — Quiet Reinforcement vs. Gamification
- **Current Technical Model**: Generic test scoring percentages, completion points, and potential red error banners.
- **Canonical UX Requirement (Phase 5.37 & 5.48)**: No badges, streaks, confetti, or artificial celebrations. Red is strictly prohibited for educational mistakes.
- **Prescribed UX**: Progress is shown as quiet stage continuity ($\circ\text{───}\circ\text{───}\bullet\text{───}\circ$). Language is respectful and adult (*"You've completed the first stage."*, *"Your work is ready for review."*).

### 🚩 Flag 5: Course Context — Grounded Course Modules vs. Isolated Questions
- **Current Technical Model**: Assignments exist as isolated question JSON objects without educational context.
- **Canonical UX Requirement (Phase 1.8 & 2.3)**: Assignments must exist inside a **Course / Module Workspace** with syllabus context, lecture grounding, and learning objectives.
- **Prescribed UX**: The MVP simulates an internal lightweight LMS (Course $\to$ Module $\to$ Assignment) so students and educators always see what academic goal the work serves.

### 🚩 Flag 6: Intelligence Architecture — 3 Functional Roles vs. 6 Microservices
- **Current Technical Model**: Proposes 6 independently deployed services (Assignment Designer, Policy Engine, Socratic Tutor, Knowledge Layer, Event Store, Evidence Dossier).
- **Canonical Execution Model (Part 2, Phase 6.30.2 & 6.30.6)**: Modularity is desirable; **distributed complexity is fatal** for a rapid build.
- **Prescribed Architecture**: **One single integrated application** with a shared core, implementing **three functional agent roles**:
  1. `Dialogue Agent`: Student inquiry & Socratic scaffolding (answer-blind).
  2. `Integrity / Policy Agent`: Boundary enforcement, SymPy CAS verification, and hint ceiling calculation.
  3. `Evidence Agent`: Translates meaningful interaction events into the student-reviewed Reasoning Trace.

### ⚡ Flag 7 (Custom Decision): Knowledge Infrastructure — Neo4j Graph + pgvector Hybrid

**Adopted Architecture**: Neo4j (concept hierarchy & misconception graph) + PostgreSQL pgvector (semantic misconception matching).

```
  Neo4j Graph Database                           PostgreSQL 16 (pgvector)
  ─────────────────────────────────────────      ────────────────────────────────────────────
  Node: KnowledgeConcept                         Table: misconceptions
    kc_id, name, domain, blooms_level              misconception_id, kc_id, name,
                                                   flawed_rule, remediation_hint,
  Relationship: (:KC)-[:REQUIRES]->(:KC)           embedding VECTOR(1536)
    Encodes prerequisite DAG edges
                                                 Index: ivfflat (embedding vector_cosine_ops)
  Relationship: (:KC)-[:ASSOCIATED_WITH]->(:Misconception)
    Binds misconception nodes to concept nodes
```

**What each store owns:**

| Concern | Technology | Rationale |
|:---|:---|:---|
| Concept hierarchy & prerequisite DAG | **Neo4j** | Cypher ancestor queries resolve full prerequisite chains at any depth. SQL CTEs become brittle and verbose. |
| Learning frontier detection | **Neo4j** | `WHERE NOT (kc)<-[:MASTERED_BY]-(student)` pattern queries identify available next concepts naturally. |
| Misconception-to-concept binding | **Neo4j** | `[:ASSOCIATED_WITH]` edges allow traversal in both directions between concepts and error patterns. |
| Semantic misconception diagnosis | **pgvector** | Cosine similarity `<=>` on student free-text embeddings identifies the cognitive error type from input. |
| Sessions, events, assignments, rubrics | **PostgreSQL** | Standard relational tables for transactional structured data. |

**Key Cypher Queries:**
```cypher
-- Get all prerequisite concepts for a given KC (any depth)
MATCH p=(kc:KnowledgeConcept {kc_id: $kc_id})-[:REQUIRES*]->(prereq)
RETURN prereq.kc_id, prereq.name, length(p) AS depth ORDER BY depth;

-- Get misconceptions associated with a knowledge concept
MATCH (kc:KnowledgeConcept {kc_id: $kc_id})-[:ASSOCIATED_WITH]->(m:Misconception)
RETURN m.misconception_id, m.name, m.flawed_rule, m.remediation_hint;

-- Detect next unlocked concepts given a set of mastered KC IDs
MATCH (kc:KnowledgeConcept)
WHERE ALL(prereq IN [(kc)-[:REQUIRES]->(p) | p.kc_id] WHERE prereq IN $mastered_kc_ids)
AND NOT kc.kc_id IN $mastered_kc_ids
RETURN kc.kc_id, kc.name;
```

---

## 🖥️ Component-by-Component UX/UI Specifications

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FIOSRA PRODUCT SURFACES                                        │
├────────────────────────────────────────┬─────────────────────────────────────────────────────────┤
│ EDUCATOR EXPERIENCE                    │ STUDENT EXPERIENCE                                      │
├────────────────────────────────────────┼─────────────────────────────────────────────────────────┤
│ 1. Workspace & Module Grounding        │ 1. Student Home & Current Work Orientation              │
│ 2. Assignment Design Studio            │ 2. Learning Workspace (Context / Active Work / AI)       │
│ 3. Observability & Signal Triage       │ 3. Focus Mode Canvas (Zero Environmental Noise)         │
│ 4. Progressive Evidence Review Dossier │ 4. Reasoning Trace Review & Re-Engagement Surface       │
│ 5. One-Click Human Evaluation          │ 5. Deliberate Finalisation & Submission Screen          │
└────────────────────────────────────────┴─────────────────────────────────────────────────────────┘
```

### Component 1: Course Workspace & Module Grounding (Simulated LMS)
- **Role**: Establishes academic context, syllabus materials, and learning objectives.
- **Educator UX**: Lightweight setup. Selects module, pastes/uploads syllabus grounding context, and defines target competencies.
- **Student UX**: Clear orientation screen answering:
  - *What am I working on?*
  - *Why does it matter to my course?*
  - *What should I do next?*

### Component 2: Assignment Designer & Pedagogical Scope De-Ambiguator (Educator Studio)
- **Role**: Authoring rubric-aligned, misconception-aware tasks from raw syllabi or unstructured prompts.
- **Surface**: Focused design canvas with integrated **AI Pedagogical De-Ambiguator Co-Pilot Modal**, not a tedious administrative form.
- **UX Flow**:
  1. **Raw Syllabus Ingestion**: Educator enters topic, uploads syllabus snippet, or types an open-ended assignment prompt.
  2. **Automated Ambiguity Diagnosis ($A_i$)**: The system evaluates temporal bounds, Neo4j KC path reachability, causal clarity, and primary source grounding. If $A_i > 30\%$, the Co-Pilot modal triggers.
  3. **3-Question Alignment Interview**:
     - *Temporal & Causal Focus*: Selects epoch and mechanism from Neo4j concepts (e.g. Fiscal Insolvency 1787–1789).
     - *Expected Misconception Traps*: Toggles active cognitive trap monitors (e.g. `MISC_TAILLE_EQUALITY`, `MISC_MORAL_VERSUS_INST`).
     - *Primary Source Grounding*: Binds curated source text (e.g. Arthur Young excerpt) for DeBERTa-v3 NLI premise-hypothesis verification.
  4. **Auto-Populate Scaffolding**: Automatically constructs the 4-rung Socratic hint ladder ($H_d = 0.25$) and machine-verifiable NLI rubric rules ($\ge 0.85$).
  5. **3-Agent Simulator Sandbox**: Teacher dry-runs simulated student inputs against Dialogue, Integrity, and Evidence agents.
  6. **Automated Vault Registration & Publish**: Locks target solutions into the encrypted Answer Vault and publishes to student reasoning canvases.

### Component 3: Student Learning Workspace & Contextual Dialogue
- **Role**: The primary environment where thinking, struggle, and discovery occur.
- **Layout (Vertical Three-Tier Structure)**:
  ```
  ┌───────────────────────────────────────────────────────────────────────┐
  │ 1. CONTEXT / ORIENTATION (Course / Objective / Target Milestone)     │
  ├───────────────────────────────────────────────────────────────────────┤
  │                                                                       │
  │ 2. ACTIVE WORK CANVAS (Dominant central space)                        │
  │    - Mathematical symbolic entry / Rich text drafting / Steps         │
  │                                                                       │
  │    ┌───────────────────────────────────────────────┐                  │
  │    │ CONTEXTUAL AI ASSISTANT (Horizon Blue accent) │ (Emerges when    │
  │    │ Socratic prompt / hint ladder Level 0–3       │  needed, then    │
  │    └───────────────────────────────────────────────┘  recedes)        │
  │                                                                       │
  ├───────────────────────────────────────────────────────────────────────┤
  │ 3. STATUS & REINFORCEMENT (○───○───●───○ Progress / Focus Toggle)     │
  └───────────────────────────────────────────────────────────────────────┘
  ```
- **Focus Mode**: One-click toggle that hides all navigation and secondary metadata, leaving only the work surface and an optional calm timer.
- **Dialogue Interaction**: Socratic, warm, and non-judgmental. If an expression is algebraically incorrect, the tutor invites self-correction (*"Check what happened to the negative sign when distributing across parentheses."*).

### Component 4: Integrity & Policy Guardrails (Answer Vault + CAS Verifier)
- **Role**: Enforcing strict answer isolation and objective mathematical verification.
- **UX Manifestation**:
  - **Invisible Guardrail**: The student-facing model never possesses the reference answer.
  - **SymPy Verifier**: Instant symbolic equivalence check ($8x - 12 \equiv 4(2x - 3)$) running behind the scenes.
  - **Hint Ceiling**: Locks bottom-out hints (Level 4) by default; advances scaffolding based on attempt counts rather than student prompt demands.

### Component 4b: Knowledge Layer (Neo4j + pgvector)
- **Role**: Providing the concept-level cognitive map and semantic misconception taxonomy for curriculum-grounded question generation and precise error diagnosis.
- **Neo4j (Graph Model)**:
  - `KnowledgeConcept` nodes with `kc_id`, `name`, `domain`, `blooms_level`.
  - `REQUIRES` edges encoding prerequisite dependencies between concepts.
  - `ASSOCIATED_WITH` edges linking each concept to its known misconception nodes.
  - Enables ancestor traversal, frontier detection, and bidirectional concept-error lookups via Cypher.
- **pgvector (Semantic Search)**:
  - Misconception records stored in PostgreSQL with 1536-dimensional embedding vectors.
  - Cosine similarity `<=>` lookup identifies the closest matching cognitive error from student free-text input.
- **How they work together at runtime**:
  1. Student submits an incorrect expression.
  2. `pgvector` semantic search returns top-3 closest misconceptions by embedding distance.
  3. Neo4j confirms which misconception is `ASSOCIATED_WITH` the target `KnowledgeConcept` for this question.
  4. `remediation_hint` from the confirmed misconception node informs the calibrated Socratic prompt.
- **UX Manifestation**: Entirely invisible to the student. Misconception diagnosis improves the *precision and relevance* of Socratic hints—the student only experiences a more accurate and contextually appropriate prompt.

### Component 5: The Reasoning Trace (Student Reflection & Review Surface)
- **Role**: The core proof artifact of authentic student thinking.
- **UX Surface**: Dedicated review stage before final submission.
- **Visual Presentation**: An interactive journey path (*The Emergent Path*):
  - **Node 1: Initial Exploration** (First hypothesis, scratch steps).
  - **Node 2: Diagnostic Friction** (Identified misconception or calculation hurdle).
  - **Node 3: Concept Shift / Scaffolding** (Socratic hint reflection).
  - **Node 4: Self-Correction & Verification** (Student re-engages and solves).
  - **Node 5: Final Formulation** (Completed reasoning).
- **Agency Rules**:
  - Students **cannot** delete or falsify historical nodes.
  - Students **can** review their trace, click **Re-Engage** to improve their work, or proceed to **Finalise**.

### Component 6: Educator Observability & Evidence Dossier
- **Role**: Providing actionable visibility without forcing educators into surveillance monitoring.
- **Observability Triage Surface**:
  - Surfaces **Attention Signals** (e.g., *"3 students struggling with sign distribution in Question 2"*).
  - Allows clicking into **Context** and recommending proportionate action (e.g., cohort clarification vs. individual message).
- **Review Surface (AutoSCORE Light Dossier)**:
  - 1-page synthesized evaluation card.
  - Shows student's final submission side-by-side with their **Reasoning Trace**.
  - Highlights verified student quote citations for each rubric criterion.
  - **1-Click Grade Approval**: Educator reviews the evidence and confirms or modifies the suggested grade in under 60 seconds.

---

## 🏛️ End-to-End Experience Map & State Model

```
EDUCATOR JOURNEY                                  STUDENT JOURNEY
      │                                                 │
  [ Prepare ]                                       [ Orient ]
Create Course & Module                            Enter Student Home
      │                                                 │
   [ Ground ]                                       [ Begin ]
Add Syllabus Context                              Open Assignment Workspace
      │                                                 │
   [ Design ]                                      [ Explore ]
Draft Assignment & Rubrics                        Attempt Milestone / Step
      │                                                 │
   [ Publish ] ──────────────────────────────────►  [ Develop ]
                                                  Receive Contextual Socratic Hint
                                                        │
   [ Observe ] ◄────────────────────────────────  [ Re-Engage ]
Signal Triage (Attention Queue)                   Apply Self-Correction
      │                                                 │
   [ Intervene ] ────────────────────────────────►  [ Reflect ]
Optional Cohort / 1-on-1 Guidance                 Review Reasoning Trace
      │                                                 │
   [ Evaluate ] ◄────────────────────────────────  [ Finalise ]
Review Evidence Dossier & 1-Click Confirm         Submit Final Work + Immutable Trace
```

---

## 🚀 Technical Build Strategy for Hackathon Execution (Part 2)

Based on **Part 2: Execution Blueprint (Phases 6 & 7)**:

### 1. Build Team Roles & Authority
- **Product Authority & Orchestration**: Deepanand *(Owns scope, blueprint adherence, and UX priorities)*.
- **Technical Authority**: Prince *(Owns technical architecture, code decisions, and canonical build acceptance)*.
- **Build Execution Authority**: Sibin *(Owns Manus AI build orchestration and prompt sequencing)*.
- **Core Implementation**: Prince, Sibin, Arjun *(Canonical build cell)*.
- **Technical Reinforcement**: Amit *(Debugging, integration, and code review)*.
- **Product Validation & QA**: Moras, Deepu *(Test cases, scenario verification, and UX consistency)*.

### 2. The 3 Demo-Invalidating Tests
Every stage of the build must satisfy these three gates before the demo recording:
1. **Faculty Trust**: *Can an educator reasonably trust a transcript-grounded Reasoning Trace without reading raw logs?*
2. **Gaming Resistance**: *Can the system's evidence model be trivially tricked into fabricating fake development?*
3. **Attribution Accuracy**: *Does the evidence accurately cite verbatim student quotes without making unsupported claims about thinking?*

### 3. Vertical Build Slices (Scope Control)
- **Tier 1 (Non-Negotiable Core)**: Course context $\to$ Assignment $\to$ Student Workspace $\to$ Socratic Dialogue $\to$ Evidence Capture $\to$ Reasoning Trace $\to$ Educator Dossier.
- **Tier 2 (If Stable)**: Seeded longitudinal progress over multiple assignments.
- **Tier 3 (Remove First)**: Multi-tenant institutional administration, complex gradebooks, and custom analytics charts.
