# Fiosra MVP — Work Planning & Dependency Map
> **Purpose**: This document tracks all pending implementation work, groups tasks by layer, and makes dependency chains explicit so developers can pick up work sequentially without blockers.
>
> **Status Key**: `✅ Done` · `🔧 Partial` · `⬜ Not Started` · `🔒 Blocked` (cannot begin until dependency is done)

> [!IMPORTANT]
> **MVP Domain Scope Decision**: The end-to-end MVP will be built and validated using **Language & History** as the first subject domain. Humanities subjects use structured text claims that can be verified using the NLI text-claim verifier — no symbolic math infrastructure is required.
> 
> **Algebra/Geometry is deferred** to a later phase (post-MVP), once the full pedagogical loop is working end-to-end. The SymPy CAS math verifier will be integrated then. Existing seed data (`misconceptions_algebra_geometry.seed.json`) is preserved as a future reference.

---

## 📦 What Already Exists

| File / Directory | Status | Notes |
|:---|:---|:---|
| `docker-compose.yml` | ✅ Done | PostgreSQL 16 (pgvector) + Neo4j 5 containers defined |
| `.env.example` | ✅ Done | All environment variables including Neo4j credentials |
| `requirements.txt` | ✅ Done | FastAPI, SQLAlchemy, asyncpg, pgvector, neo4j, sympy |
| `Makefile` | ✅ Done | `make dev`, `make test`, `make db-up`, `make lint` |
| `.gitignore` | ✅ Done | Python, Node, OS, IDE excludes |
| `README.md` (root) | ✅ Done | Quickstart, directory map, architectural tenets |
| `CONTRIBUTING.md` | ✅ Done | Invariants, branching, testing, PR, Code of Conduct link |
| `CODE_OF_CONDUCT.md` | ✅ Done | Contributor Covenant v2.1 |
| `.github/pull_request_template.md` | ✅ Done | Architectural invariant checklist |
| `.github/ISSUE_TEMPLATE/` | ✅ Done | Bug report + feature request templates |
| `fiosra/README.md` | ✅ Done | Full canonical MVP architecture + UX decisions + Flag resolutions |
| `fiosra/reference/` | ✅ Done | Long-term research vision + 6 full agent research specs |
| `fiosra/__init__.py` | ✅ Done | Package init |
| `fiosra/mvp/__init__.py` | ✅ Done | Package init |
| `fiosra/mvp/config.py` | 🔧 Partial | Missing `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` settings |
| `fiosra/mvp/database.py` | ✅ Done | Async SQLAlchemy engine + session factory |
| `fiosra/mvp/migrations/001_initial_schema.sql` | 🔧 Partial | Needs Course/Module tables; `kc_prerequisites` table is now Neo4j's responsibility |
| `fiosra/mvp/assignment_designer/schemas.py` | ✅ Done | Pydantic models: `QuestionSpec`, `HintRung`, `ScaffoldingStep` |
| `fiosra/mvp/assignment_designer/distractor_engine.py` | 🔧 Partial | Stub implemented; real LLM call pending |
| `fiosra/mvp/assignment_designer/generator.py` | 🔧 Partial | Stub implemented; real LLM prompt pipeline pending |
| `fiosra/mvp/assignment_designer/__init__.py` | ✅ Done | Package init |
| `fiosra/knowledge/seeds/misconceptions_algebra_geometry.seed.json` | ⏸️ Deferred | Algebra seed preserved for post-MVP math phase. Not used in current build. |
| `fiosra/knowledge/seeds/misconceptions_language_history.seed.json` | ⬜ Not Started | **New: MVP domain seed file** — language & history misconceptions with 4-rung hints |
| `ui/ux/frontend/README.md` | ✅ Done | Design tokens, screen inventory, UX invariants |

---

## 🏗️ Phase 0: Infrastructure & Configuration Fixes
> **Dependency**: Must be completed before any other backend work can run.

### 0.1 — Update `config.py` with Neo4j Settings
**Depends on**: Nothing  
**Blocks**: Phase 1 (Neo4j client), Phase 3 (Knowledge Layer)

```
File: fiosra/mvp/config.py
- Add: NEO4J_URI: str = "bolt://localhost:7687"
- Add: NEO4J_USER: str = "neo4j"
- Add: NEO4J_PASSWORD: str = "fiosra_neo4j_password"
```

### 0.2 — Fix PostgreSQL Migration: Remove KC Hierarchy Tables, Add Course/Module Tables
**Depends on**: Nothing  
**Blocks**: Phase 4 (Event Store), Phase 6 (Course Layer)

The current `001_initial_schema.sql` still defines `knowledge_components` and `kc_prerequisites` relational tables — these are now Neo4j's responsibility. Additionally, the schema is missing `courses` and `modules` tables required by the UX decision on Flag 5.

```sql
-- Remove (now owned by Neo4j):
--   knowledge_components table
--   kc_prerequisites table

-- Add:
CREATE TABLE IF NOT EXISTS courses (
    course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    domain VARCHAR(64),
    created_by VARCHAR(64) NOT NULL,
    syllabus_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modules (
    module_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    learning_objectives JSONB,
    position INT NOT NULL DEFAULT 1
);

-- Add module_id FK to assignments:
ALTER TABLE assignments ADD COLUMN module_id UUID REFERENCES modules(module_id);
```

### 0.3 — Create Neo4j Client & Connection Manager
**Depends on**: 0.1  
**Blocks**: Phase 3 (Knowledge Layer), Phase 5 (Policy Engine uses KC lookup)

```
New file: fiosra/mvp/neo4j_client.py
- Singleton Neo4j driver using neo4j.AsyncGraphDatabase
- async get_session() context manager
- health_check() verifying bolt connectivity
```

### 0.4 — Verify Docker Containers Boot & Both Databases Are Reachable
**Depends on**: 0.1, 0.2, 0.3  
**Blocks**: Everything

```bash
make db-up
# Verify:
# - psql -U postgres -d fiosra_db -c "\dt" shows all expected tables
# - curl http://localhost:7474 returns Neo4j browser
# - python3 -c "from fiosra.mvp.database import engine" (no errors)
# - python3 -c "from fiosra.mvp.neo4j_client import driver" (no errors)
```

---

## 🌐 Phase 1: Neo4j Graph Schema & Seed Data
> **Dependency**: Phase 0 must be complete.

### 1.1 — Define Neo4j Constraints & Indexes
**Depends on**: 0.3, 0.4  
**Blocks**: 1.2, 1.3

```cypher
-- To run once on fresh database:
CREATE CONSTRAINT kc_id_unique IF NOT EXISTS FOR (kc:KnowledgeConcept) REQUIRE kc.kc_id IS UNIQUE;
CREATE CONSTRAINT misc_id_unique IF NOT EXISTS FOR (m:Misconception) REQUIRE m.misconception_id IS UNIQUE;
CREATE INDEX kc_domain_index IF NOT EXISTS FOR (kc:KnowledgeConcept) ON (kc.domain);
CREATE INDEX misc_domain_index IF NOT EXISTS FOR (m:Misconception) ON (m.domain);
```

```
New file: fiosra/mvp/migrations/002_neo4j_constraints.cypher
```

### 1.2 — Write Neo4j Seed Script: KnowledgeConcept Nodes
**Depends on**: 1.1  
**Blocks**: 1.3, Phase 3 (Knowledge Layer)

```
New file: fiosra/scripts/seed_neo4j_graph.py
- Load Language & History KnowledgeConcept nodes (kc_id, name, domain, blooms_level)
- Create REQUIRES relationships for prerequisite DAG
- Cross-reference knowledge_component.schema.json for structure
```

Minimum viable seed data — **Language domain**:
```
KC_LANG_READING_COMPREHENSION
    └── KC_LANG_ARGUMENT_IDENTIFICATION
            └── KC_LANG_EVIDENCE_EVALUATION
                    └── KC_LANG_CLAIM_CONSTRUCTION
                            └── KC_LANG_STRUCTURED_ESSAY
```

Minimum viable seed data — **History domain**:
```
KC_HIST_TIMELINE_SEQUENCING
    └── KC_HIST_CAUSE_AND_EFFECT
            └── KC_HIST_PRIMARY_SOURCE_ANALYSIS
                    └── KC_HIST_PERSPECTIVE_AND_BIAS
                            └── KC_HIST_HISTORICAL_ARGUMENT
```

> [!NOTE]
> Algebra/Geometry KCs (`KC_ALG_*`) are **not seeded in the MVP build**. They will be added in the post-MVP math expansion phase.

### 1.3 — Create MVP Misconception Seed File: Language & History
**Depends on**: Nothing (can be done in parallel with 1.1)  
**Blocks**: 1.4, Phase 3 (Knowledge Layer - vector service)

```
New file: fiosra/knowledge/seeds/misconceptions_language_history.seed.json
```

Required misconception coverage (minimum viable set — ~20 entries):

**Language domain:**
- Confusing the author's argument with factual truth
- Treating an anecdote as representative evidence
- Mistaking correlation in a quoted source for causation
- Paraphrasing a source without evaluating its reliability
- Conflating opinion and evidence in a written claim

**History domain:**
- Attributing a single cause to a complex historical event
- Applying present-day values to judge past actors (anachronism)
- Accepting a primary source as objective fact without considering author bias
- Confusing a historical claim with a moral judgement
- Treating sequence of events (A then B) as causation (A caused B)

Each entry must include: `misconception_id`, `domain`, `knowledge_component`, `label`, `description`, `flawed_rule`, `remediation_hints` (4 rungs: metacognitive, conceptual, procedural, worked analogy).

### 1.3b — Load Misconception Nodes into Neo4j
**Depends on**: 1.2, 1.3  
**Blocks**: Phase 3 (Knowledge Layer - vector service)

```
Extends: fiosra/scripts/seed_neo4j_graph.py
- Source: fiosra/knowledge/seeds/misconceptions_language_history.seed.json
- For each misconception: CREATE (:Misconception {misconception_id, name, flawed_rule, remediation_hint, domain})
- For each misconception.knowledge_component: MATCH KC → CREATE [:ASSOCIATED_WITH] edge to Misconception
```

### 1.4 — Write pgvector Seed Script: Misconception Embeddings
**Depends on**: 0.4 (PostgreSQL running), 1.3 (Misconception seed data defined)  
**Blocks**: Phase 3 (vector service)

```
New file: fiosra/scripts/seed_pgvector_embeddings.py
- For each misconception from seed JSON:
  - Concatenate name + flawed_rule + remediation_hint into embedding input text
  - Call OpenAI text-embedding-ada-002 (or local alternative)
  - INSERT into misconceptions table with VECTOR(1536) embedding
```

---

## ⚙️ Phase 2: Central Application Bootstrap
> **Dependency**: Phase 0 complete.

### 2.1 — Reshape Agent Topology in `app.py` (3-Agent Model)
**Depends on**: 0.1  
**Blocks**: Phase 5, 6, 7 (all agent components)

The current stub in `fiosra/mvp/app.py` still references 6 microservice routers. It must be reshaped to reflect the **3-functional-agent** topology decided in Flag 6:

```
New file: fiosra/mvp/app.py
- Lifespan: async context manager booting both DB connections
- 3 router groups mounted:
    /dialogue  → Socratic Dialogue Agent router
    /integrity → Policy Engine / Integrity Agent router
    /evidence  → Evidence Dossier router
- Supporting routers mounted:
    /knowledge → Knowledge Layer (internal graph service)
    /events    → Event Store (internal flight recorder)
    /courses   → Course/Module context layer
    /assignments → Assignment Designer
    /health    → Health probe (PostgreSQL + Neo4j connectivity)
```

### 2.2 — Create Central `fiosra/scripts/` Directory for CLI Tools
**Depends on**: 0.1  
**Blocks**: 1.2, 1.3, 1.4

```
fiosra/scripts/
├── __init__.py
├── seed_neo4j_graph.py        (Phase 1.2 + 1.3)
└── seed_pgvector_embeddings.py (Phase 1.4)
```

---

## 🗂️ Phase 3: Knowledge Layer (Neo4j + pgvector)
> **Dependency**: Phase 0 + Phase 1 must be complete. This component is used by the Assignment Designer and Policy Engine — must come before both.

### 3.1 — `knowledge_layer/models.py`
**Depends on**: 0.2 (PostgreSQL schema with misconceptions table)  
**Blocks**: 3.3

```
SQLAlchemy model for `misconceptions` table
(misconception_id, kc_id, name, flawed_rule, remediation_hint, embedding)
```

### 3.2 — `knowledge_layer/graph_service.py`
**Depends on**: 0.3 (Neo4j client), 1.2, 1.3  
**Blocks**: Phase 5, Phase 6

```python
# Key methods:
get_prerequisites(kc_id: str) -> List[str]              # REQUIRES* traversal
get_learning_frontier(mastered_kc_ids: List[str])        # Unlock detection
get_associated_misconceptions(kc_id: str)                # ASSOCIATED_WITH traversal
```

### 3.3 — `knowledge_layer/vector_service.py`
**Depends on**: 3.1, 1.4 (embeddings seeded)  
**Blocks**: Phase 5 (Policy Engine uses misconception lookup)

```python
# Key method:
find_closest_misconception(student_text: str, kc_id: str, top_k: int = 3) -> List[Misconception]
# Step 1: pgvector cosine similarity on student_text embedding
# Step 2: Neo4j confirmation that matched misconception is ASSOCIATED_WITH target KC
```

### 3.4 — `knowledge_layer/router.py`
**Depends on**: 3.2, 3.3  
**Blocks**: Nothing externally (internal service)

```
GET /knowledge/prerequisites/{kc_id}
GET /knowledge/misconceptions/{kc_id}
GET /knowledge/frontier         (POST body: mastered_kc_ids)
```

---

## 📡 Phase 4: Event Store (Append-Only Flight Recorder)
> **Dependency**: Phase 0.2 (PostgreSQL schema with `student_sessions` and `session_events` tables). Parallel to Phase 3.

### 4.1 — `event_store/models.py`
**Depends on**: 0.2  
**Blocks**: 4.2

```python
# SQLAlchemy models:
class StudentSession(Base):    # Maps to student_sessions table
class SessionEvent(Base):      # Maps to session_events (append-only JSONB)
```

### 4.2 — `event_store/event_service.py`
**Depends on**: 4.1  
**Blocks**: 4.3, Phase 5, Phase 7

```python
# Key methods:
create_session(student_id, assignment_id, question_id) -> UUID
log_event(session_id, event_type, payload: dict) -> None   # < 2ms target
get_timeline(session_id) -> List[SessionEvent]             # Chronological replay
complete_session(session_id) -> None
```

**Event types to support** (typed enum):
```
session_started · attempt_submitted · attempt_evaluated · hint_requested
hint_delivered · self_correction · concept_shift · session_completed
```

### 4.3 — `event_store/router.py`
**Depends on**: 4.2  
**Blocks**: Nothing externally

```
POST /events/session/start
POST /events/log
GET  /events/session/{session_id}/timeline
POST /events/session/{session_id}/complete
```

---

## 🔐 Phase 5: Integrity Agent (Policy Engine + Answer Vault + Verifiers)
> **Dependency**: Phase 3 (Knowledge Layer for misconception lookup), Phase 4 (Event Store for logging evaluated attempts). This is the core guardrail — must come before the Dialogue Agent.

> [!IMPORTANT]
> **MVP Verifier Scope**: For the Language & History MVP, only `verify_humanities_claim` (NLI text-claim check) is implemented.
> `verify_math_equivalence` (SymPy CAS) is **deferred to the post-MVP math phase** and exists only as a placeholder stub that returns `NOT_APPLICABLE`.

### 5.1 — `policy_engine/answer_vault.py`
**Depends on**: Phase 0 only  
**Blocks**: 5.4, Phase 6

```python
# In-memory secured Answer Vault (no student-read routes exist)
class AnswerVault:
    _store: Dict[str, dict] = {}    # question_id -> {solution, rubric_criteria}
    def register(question_id, reference_claims, rubric) -> None
    def get_claims(question_id) -> dict           # Internal only, never exposed to dialogue agent
    def verify_registered(question_id) -> bool
```

For Language & History, `reference_claims` is a list of required rubric claim statements (not a numeric solution):
```json
{
  "required_claims": [
    "The student identifies at least one primary source as evidence.",
    "The student distinguishes between the author's argument and factual record.",
    "The student connects their claim to a specific historical period."
  ]
}
```

### 5.2 — `policy_engine/verifiers.py`
**Depends on**: Phase 0 only  
**Blocks**: 5.4

```python
class PluggableVerifier:

    # ✅ MVP — Language & History: Active
    @staticmethod
    def verify_humanities_claim(student_text: str, required_claim: str) -> VerificationResult:
        """
        NLI-based rubric claim check.
        Determines whether student_text (premise) entails required_claim (hypothesis).
        MVP implementation: structured LLM call with JSON schema output.
        Returns: {status: 'MET' | 'PARTIALLY_MET' | 'MISSING', confidence, evidence_quote}
        """

    # ⏸️ Deferred to Post-MVP Math Phase
    @staticmethod
    def verify_math_equivalence(student_expr: str, target_expr: str) -> VerificationResult:
        """
        Placeholder stub. SymPy CAS integration deferred until math domain is introduced.
        Returns: {status: 'NOT_APPLICABLE', verdict: 'math_verifier_deferred'}
        """
        return VerificationResult(status="NOT_APPLICABLE", verdict="math_verifier_deferred")
```

### 5.3 — `policy_engine/hint_ceiling.py`
**Depends on**: Phase 0 only  
**Blocks**: 5.4

```python
compute_hint_ceiling(attempt_count: int, prior_mastery: float,
                     teacher_override: bool = False) -> int
# Returns 0-4; Level 4 locked unless teacher_override=True
# Never inspects student prompt text — prevents jailbreak attacks
# Works identically for language, history, and math domains
```

### 5.4 — `policy_engine/router.py`
**Depends on**: 5.1, 5.2, 5.3, Phase 3 (misconception lookup), Phase 4 (event logging)  
**Blocks**: Phase 6 (Assignment Designer registers to vault), Phase 7 (Dialogue Agent calls verify)

```
POST /integrity/verify          → Run NLI claim verifier, log attempt_evaluated event, return verdict + hint_level
POST /integrity/vault/register  → Register reference claims + rubric (educator only, called by Assignment Designer)
GET  /integrity/hint-ceiling    → Compute current hint ceiling for session
```

---

## 📝 Phase 6: Assignment Designer & Pedagogical Scope De-Ambiguator Co-Pilot
> **Dependency**: Phase 3 (Knowledge Layer for KCs + misconceptions), Phase 5 (Answer Vault to register solutions). Can start partial implementation after Phase 3.

### 6.0 — `assignment_designer/deambiguator.py`
**Status**: ⬜ Not Started  
**Depends on**: 3.2 (Neo4j KC & misconception traversal)

```python
# Multi-dimensional ambiguity evaluation pipeline ($f_{\text{de-ambiguate}}$):
# 1. Evaluate temporal/epoch boundary clarity
# 2. Check Neo4j KC DAG reachability & prerequisite completeness
# 3. Detect causal mechanism ambiguity & moral hand-waving susceptibility
# 4. Validate primary source anchor presence for DeBERTa NLI verifier
# 5. Compute Ambiguity Index (A_i) & generate 3-question Socratic educator interview
evaluate_prompt_ambiguity(raw_prompt: str, course_id: str) -> AmbiguityDiagnosis
generate_clarification_interview(diagnosis: AmbiguityDiagnosis) -> List[ClarificationQuestion]
```

### 6.1 — `assignment_designer/schemas.py`
**Status**: ✅ Done — `QuestionSpec`, `HintRung`, `ScaffoldingStep` models complete. (Need to add `AmbiguityDiagnosis`, `ClarificationQuestion`, `ScopeClarificationRequest`).

### 6.2 — `assignment_designer/distractor_engine.py`
**Status**: 🔧 Partial — stub exists  
**Depends on**: 3.2 (Neo4j misconception traversal)

```python
# Replace stub: query Neo4j ASSOCIATED_WITH edges for real misconception-seeded distractors
generate_distractors(kc_id: str, domain: str) -> List[DistractorOption]
```

### 6.3 — `assignment_designer/generator.py`
**Status**: 🔧 Partial — hardcoded stub  
**Depends on**: 3.2, 6.0, 6.2

```python
# Replace hardcoded stub with:
# 1. Query Knowledge Layer for prerequisite KCs + top-3 misconceptions
# 2. Build structured LLM prompt (structured JSON output schema)
# 3. Apply teacher clarifications (epoch, selected traps, primary source anchor)
# 4. Generate 4-rung answer-blind Socratic hint ladder (Hd step: 0.25)
# 5. Formulate verifiable NLI rubric rules (Premise ➔ Hypothesis ≥ 0.85)
# 6. Register reference_solution in Answer Vault
draft_question(req: QuestionDraftRequest) -> QuestionSpec
scaffold_from_clarifications(req: ScopeClarificationRequest) -> AssignmentScaffoldingSpec
```

### 6.4 — `assignment_designer/router.py`
**Status**: ⬜ Not Started  
**Depends on**: 6.0, 6.2, 6.3, 5.1 (Answer Vault registration)

```
POST /assignments/analyze-scope       → Ingest raw syllabus/prompt, return Ambiguity Index + 3-question interview
POST /assignments/clarify-and-scaffold→ Ingest teacher interview responses, auto-populate 4-rung ladder & NLI rules
POST /assignments/draft               → Generate QuestionSpec + register solution in vault
GET  /assignments/{id}                → Fetch published assignment spec
POST /assignments/{id}/publish        → Publish to module and student canvases
```

---

## 💬 Phase 7: Dialogue Agent (Socratic Tutor)
> **Dependency**: Phase 4 (Event Store for logging hint events), Phase 5 (receives verification verdict + hint ceiling). Most student-facing logic lives here.

### 7.1 — `socratic_tutor/prompts.py`
**Status**: ⬜ Not Started  
**Depends on**: Phase 0 only

```python
SOCRATIC_SYSTEM_PROMPT = """..."""   # Non-negotiable negative constraints
# Includes: ABSOLUTE_RULES (never reveal answer), MAX_HINT_LEVEL injection, JSON schema enforcement
# Hint type templates: metacognitive, conceptual, procedural, worked_analogy
```

### 7.2 — `socratic_tutor/agent.py`
**Status**: ⬜ Not Started  
**Depends on**: 7.1, Phase 4, Phase 5

```python
class SocraticAgent:
    async def respond(
        session_id, question_spec, student_input, verifier_verdict, hint_level
    ) -> SocraticResponse:
    # 1. Build context-injected prompt (no reference solution in context)
    # 2. Call LLM with structured JSON schema output
    # 3. Parse {thoughts_of_tutorbot, response_text}
    # 4. Log hint_delivered event to Event Store
    # 5. Return response to student
```

### 7.3 — `socratic_tutor/router.py`
**Status**: ⬜ Not Started  
**Depends on**: 7.2

```
POST /dialogue/message          → Main student interaction endpoint (answer-blind Socratic probe)
GET  /dialogue/session/{id}     → Retrieve dialogue history for session
POST /dialogue/step/verify      → Evaluate single section milestone claim via NLI; unlock next step
POST /dialogue/weave-synthesis  → Weave discrete verified sections into cohesive continuous essay
POST /dialogue/speech-to-thought→ Transcribe student verbal explanation & crystallize into draft premises
```

---

## 📊 Phase 8: Evidence Agent (Reasoning Trace + Dossier)
> **Dependency**: Phase 4 (Event Store — replays chronological timeline). Can be developed independently alongside Phase 7.

### 8.1 — `evidence_dossier/extractor.py`
**Status**: ⬜ Not Started  
**Depends on**: 4.2 (Event Store timeline replay)

```python
# AutoSCORE Stage 1 (f_extract):
extract_reasoning_trace(session_id: UUID) -> ReasoningTrace
# - Replay session_events in chronological order
# - Identify: initial_exploration, diagnostic_friction, concept_shifts, self_corrections
# - Calculate: autonomy_score, hint_dependency_ratio, dwell_times
# - Capture verbatim student quote citations per rubric criterion
```

### 8.2 — `evidence_dossier/scoring.py`
**Status**: ⬜ Not Started  
**Depends on**: 8.1

```python
# AutoSCORE Stage 2 (f_score):
pre_score_against_rubric(trace: ReasoningTrace, rubric_criteria: List[dict]) -> ScoredDossier
# - Match evidence quotes against rubric criteria (no LLM grading)
# - Produce suggested_grade with cited evidence
```

### 8.3 — `evidence_dossier/router.py`
**Status**: ⬜ Not Started  
**Depends on**: 8.1, 8.2

```
GET  /evidence/dossier/{session_id}       → Synthesized 1-page educator review card
POST /evidence/dossier/{session_id}/finalise-grade  → 1-click educator grade approval
GET  /evidence/trace/{session_id}         → Reasoning Trace nodes for student review UI
```

---

## 🏫 Phase 9: Course & Module Context Layer (Simulated LMS)
> **Dependency**: Phase 0.2 (courses + modules tables added to PostgreSQL schema). Can be developed in parallel with Phases 3–5.

### 9.1 — `courses/models.py`
**Depends on**: 0.2  
**Blocks**: 9.2

```python
class Course(Base): ...
class Module(Base): ...
```

### 9.2 — `courses/router.py`
**Depends on**: 9.1

```
POST /courses                      → Create course (educator)
GET  /courses/{id}                 → Get course with modules
POST /courses/{id}/modules         → Add module
GET  /courses/{id}/modules/{mid}   → Get module with assignments
```

---

## 🧪 Phase 10: Test Suite
> **Dependency**: Phases 3–8 must have at least core implementations. Tests may be written incrementally alongside each phase.

| Test File | Tests | Depends On |
|:---|:---|:---|
| `tests/test_verifiers.py` | SymPy math equivalence (true/false/syntax error) | Phase 5.2 |
| `tests/test_hint_ceiling.py` | Ceiling progression, anti-manipulation (no prompt injection) | Phase 5.3 |
| `tests/test_graph_service.py` | Neo4j prerequisite traversal, frontier detection | Phase 3.2 |
| `tests/test_event_store.py` | Event append speed (< 2ms), chronological ordering | Phase 4.2 |
| `tests/test_dialogue_guardrails.py` | Adversarial prompt test: student demands answer | Phase 7.2 |
| `tests/test_e2e_flow.py` | Full loop: draft assignment → session → dialogue → dossier | Phases 3–8 |

---

## 🖥️ Phase 11: Frontend (Next.js 14)
> **Dependency**: Backend API must be stable (Phases 5–9). Start in parallel only if working from mocked API responses.

### 11.1 — Student Learning Workspace
- **Active Work Canvas** (KaTeX math input / rich text / step-by-step).
- **Contextual AI Panel** (emerges on request, recedes after response).
- **Focus Mode** toggle (zero environmental noise).
- Calls: `POST /dialogue/message`, `POST /integrity/verify`, `POST /events/log`.

### 11.2 — Reasoning Trace Visualization
- **"A Path Made Visible"** interactive node graph:
  $\text{Exploration} \to \text{Friction} \to \text{Concept Shift} \to \text{Self-Correction} \to \text{Finalisation}$
- Node click reveals progressive quote disclosure.
- **Re-Engage** and **Finalise** actions.
- Calls: `GET /evidence/trace/{session_id}`.

### 11.3 — Educator Studio (Assignment Design)
- Sequential canvas: Purpose → Objectives → Task → Rubric → AI Policy Boundaries.
- Calls: `POST /assignments/draft`, `POST /assignments/{id}/publish`.

### 11.4 — Educator Observability & Dossier Review
- **Signal Triage Queue** (not a dashboard full of charts).
- 1-page synthesized evidence dossier with cited quotes.
- **1-click grade confirmation**.
- Calls: `GET /evidence/dossier/{session_id}`, `POST /evidence/dossier/{session_id}/finalise-grade`.

---

## 🗺️ Full Dependency Graph

```
Phase 0: Infrastructure Fixes & Config
    └── 0.1 config.py Neo4j settings
    └── 0.2 PostgreSQL schema (courses, modules, remove KC tables)
    └── 0.3 neo4j_client.py
    └── 0.4 Verify both DBs boot
         │
         ├── Phase 1: Neo4j Schema + Seed Data
         │     ├── 1.1 Neo4j constraints & indexes
         │     ├── 1.2 KC nodes + REQUIRES edges
         │     ├── 1.3 Misconception nodes + ASSOCIATED_WITH edges
         │     └── 1.4 pgvector misconception embeddings
         │
         ├── Phase 2: Application Bootstrap
         │     ├── 2.1 Reshape app.py (3-agent topology)
         │     └── 2.2 Create scripts/ directory
         │
         ├── Phase 3: Knowledge Layer ← needs Phase 1 + 0.3
         │     ├── 3.1 models.py (PostgreSQL misconception model)
         │     ├── 3.2 graph_service.py (Neo4j Cypher queries)
         │     ├── 3.3 vector_service.py (pgvector cosine search)
         │     └── 3.4 router.py
         │
         ├── Phase 4: Event Store ← needs 0.2 only (parallel to Phase 3)
         │     ├── 4.1 models.py
         │     ├── 4.2 event_service.py
         │     └── 4.3 router.py
         │
         ├── Phase 5: Integrity Agent ← needs Phase 3 + Phase 4
         │     ├── 5.1 answer_vault.py
         │     ├── 5.2 verifiers.py (SymPy CAS)
         │     ├── 5.3 hint_ceiling.py
         │     └── 5.4 router.py
         │
         ├── Phase 6: Assignment Designer ← needs Phase 3 + Phase 5
         │     ├── 6.1 schemas.py ✅ Done
         │     ├── 6.2 distractor_engine.py 🔧 Fix Neo4j integration
         │     ├── 6.3 generator.py 🔧 Replace stub with real LLM pipeline
         │     └── 6.4 router.py ⬜ Missing
         │
         ├── Phase 7: Dialogue Agent ← needs Phase 4 + Phase 5
         │     ├── 7.1 prompts.py
         │     ├── 7.2 agent.py
         │     └── 7.3 router.py
         │
         ├── Phase 8: Evidence Agent ← needs Phase 4
         │     ├── 8.1 extractor.py (AutoSCORE light)
         │     ├── 8.2 scoring.py (Rubric pre-scoring)
         │     └── 8.3 router.py
         │
         ├── Phase 9: Course & Module Layer ← needs 0.2 (parallel to 3–5)
         │     ├── 9.1 courses/models.py
         │     └── 9.2 courses/router.py
         │
         ├── Phase 10: Test Suite ← needs Phases 3–8
         │     └── test_verifiers, test_graph, test_events, test_e2e
         │
         └── Phase 11: Frontend ← needs Phases 5–9
               ├── 11.1 Student Workspace
               ├── 11.2 Reasoning Trace Visualization
               ├── 11.3 Educator Studio
               └── 11.4 Observability + Dossier Review
```

---

## 🚦 Recommended Parallel Work Tracks

If you have multiple contributors available, these tracks can be pursued concurrently after Phase 0 is complete:

| Track A (Core Backend) | Track B (Knowledge Data) | Track C (Frontend Foundation) |
|:---|:---|:---|
| Phase 3: Knowledge Layer | Phase 1: Neo4j seed scripts | Phase 11.1: Student Workspace (mock API) |
| Phase 4: Event Store | Phase 1.4: pgvector embeddings | Phase 11.3: Educator Studio (mock API) |
| Phase 5: Integrity Agent | | |
| Phase 6: Assignment Designer | | |

> [!CAUTION]
> Do **not** begin Phase 7 (Dialogue Agent) or Phase 11 (Frontend live API calls) until Phase 5 (Integrity Agent / Answer Vault) is complete and verified. Connecting student-facing surfaces to an unguarded backend risks answer leakage.
