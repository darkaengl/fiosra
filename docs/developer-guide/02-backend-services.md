# Chapter 2: Backend Services & Storage Architecture

The Fiosra backend is built on **Python 3.11+ / 3.14** and **FastAPI**, backed by **PostgreSQL 16 with `pgvector`** for relational and vector search, and **Neo4j 5** for pedagogical dependency graphs.

---

## 🏛️ Backend Architecture Overview

```mermaid
graph TD
    Client["Svelte 5 Web Client (/ui/#/)"] -->|REST / JSON| Gateway["FastAPI Gateway (main.py)"]
    
    subgraph CoreRouters["API Router Layer"]
        Gateway --> R_LMS["/courses (LMS & Portfolio)"]
        Gateway --> R_Assign["/assignment (Designer & Vault)"]
        Gateway --> R_Dial["/api/v1/dialogue (Socratic Tutor)"]
        Gateway --> R_Graph["/api/v1/knowledge (Neo4j / DAG)"]
        Gateway --> R_Event["/api/v1/events (Event Store)"]
        Gateway --> R_Evid["/api/v1/evidence (AutoSCORE)"]
    end

    subgraph ServiceEngines["Reasoning Engine Layer"]
        R_LMS --> S_Course["CourseService & Ingestion"]
        R_Assign --> S_Assign["AssignmentGenerator & Vault"]
        R_Dial --> S_Dial["SocraticDialogueEngine"]
        R_Graph --> S_Graph["GraphService (NetworkX / Cypher)"]
        R_Event --> S_Event["EventStoreFlightRecorder"]
        R_Evid --> S_Evid["DossierSynthesizer"]
    end

    subgraph StorageLayer["Data & Persistence Layer"]
        S_Course --> PG[(PostgreSQL 16 Relational)]
        S_Course --> PGV[(pgvector Embeddings)]
        S_Event --> PG
        S_Graph --> Neo[(Neo4j 5 Graph DB)]
        S_Assign --> Vault[(Isolated Answer Vault)]
    end
```

---

## 🏗️ Directory Layout (`fiosra/mvp/`)

```
fiosra/mvp/
├── main.py                     # FastAPI application factory, lifespan, CORS, and static mount
├── config.py                   # Pydantic BaseSettings loading .env configuration
├── database.py                 # Async SQLAlchemy engine and session factory
├── neo4j_client.py             # Async Neo4j driver connection pool & lifecycle management
├── graph_service.py            # KC DAG traversal with NetworkX fallback
├── dialogue_engine.py          # Answer-blind Socratic tutor conversation manager
├── dialogue_router.py          # /api/v1/dialogue endpoints
├── event_store.py              # Flight recorder append-only event engine
├── events_router.py            # /api/v1/events endpoints
├── learning_document_service.py # Protected long-form document persistence
├── learning_document_router.py  # /learning-documents document endpoints
├── socratic_probe_service.py    # Canonical-block proactive probe lifecycle
├── socratic_probe_router.py     # Capability-protected probe endpoints
├── llm/                         # LiteLLM adapter, policy orchestration, deterministic fallback
├── seed_pipeline.py            # Seed script populating Neo4j KCs and PostgreSQL initial records
│
├── courses/                    # LMS Curriculum & Portfolio Service
│   ├── models.py               # SQLAlchemy ORM models (Course, Module, Resource, SyllabusChunk)
│   ├── schemas.py              # Pydantic v2 schemas for CRUD & cohort rosters
│   ├── service.py              # Course business logic & syllabus processing
│   ├── ingestion.py            # Syllabus PDF/Text chunking & pgvector embedding pipeline
│   └── router.py               # /courses endpoints
│
├── assignment_designer/        # Assignment Authoring & Answer Vault
│   ├── generator.py            # Syllabus RAG assignment generation
│   ├── distractor_engine.py    # Misconception-grounded multiple-choice distractor generator
│   ├── deambiguator.py         # Prompt clarity & edge-case resolver
│   ├── vault.py                # Answer Vault (isolated reference solutions)
│   ├── schemas.py              # Pydantic models for prompts & rubrics
│   └── router.py               # /assignment endpoints
│
├── evidence_dossier/           # AutoSCORE Synthesis Engine
│   ├── synthesizer.py          # Trajectory analyzer calculating Autonomy Index & Rubric points
│   └── router.py               # /evidence endpoints
│
├── verifiers/                  # Formal & Symbolic Verification
│   └── text_claim.py           # Claim assertion validator & SymPy CAS interface
│
└── migrations/                 # DDL & Schema Migration SQL Scripts
├── 001_initial_schema.sql  # Core event store & assignment tables
├── 002_syllabus_chunks.sql # pgvector extension & vector tables
├── 004_module_resources.sql# Grounded syllabus resources table
├── 005_learning_canvas.sql # Legacy canvas drafts and session capability tables
├── 006_long_form_document.sql # Long-form block persistence tables
└── 007_proactive_socratic_probes.sql # Paragraph-bound question and response tables
```

---

## ⚙️ Core Application Infrastructure

### 1. Configuration (`config.py`)
Application settings are validated via `pydantic-settings`. Default environment variables:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `str` | `"Fiosra MVP"` | Application name |
| `DATABASE_URL` | `str` | `postgresql+asyncpg://fiosra:fiosra@localhost:5432/fiosra_db` | Async PostgreSQL connection string |
| `NEO4J_URI` | `str` | `bolt://localhost:7687` | Neo4j Bolt protocol URI |
| `NEO4J_USER` | `str` | `"neo4j"` | Neo4j username |
| `NEO4J_PASSWORD` | `str` | `"fiosra_neo4j"` | Neo4j password |
| `OPENAI_API_KEY` | `SecretStr`| `""` | Key for embeddings and the optional OpenAI-compatible LiteLLM provider |
| `FIOSRA_LLM_PROVIDER` | `str` | `"deterministic"` | `deterministic`, `ollama`, `openrouter`, `openai`, or `gemini`; controls optional constrained rephrasing only |
| `OLLAMA_MODEL` | `str` | provider-specific | Local model name used through LiteLLM when `FIOSRA_LLM_PROVIDER=ollama` |
| `FIOSRA_PROBE_QUIET_SECONDS` | `int` | `5` | Minimum stable period after document sync before a canonical-block probe can be evaluated |
| `FIOSRA_PROBE_SESSION_BUDGET` | `int` | `6` | Maximum automatic questions persisted for one learner session |

### 2. Async Database Session (`database.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. Proactive Socratic probe lifecycle

`SocraticProbeService` is deliberately a **server-authoritative micro-workflow**, not an autonomous essay-writing agent. The browser invokes evaluation only after a successful document synchronization and five-second quiet period. The service re-reads the canonical block, verifies the capability-bound active session and public assignment, selects one allow-listed focus deterministically, and observes per-block/session limits. It stores the question and all learner dispositions in PostgreSQL, while the append-only event stream stores only IDs, focus, and prompt-free generation metadata.

Only a bounded question rephrase may use `llm_orchestrator`. The provider sees reduced public context and may not select a focus, see a complete essay, access the Answer Vault, mutate a document, or decide a grade. The policy layer requires exactly one question and rejects answer language, conclusions, source inventions, and out-of-context vocabulary. A deterministic question is the final fallback.

---

## 🔄 Syllabus Ingestion & Grounding Pipeline

The diagram below details how teacher-provided course syllabi and PDFs are ingested, vectorized, and attached to modules:

```mermaid
flowchart LR
    PDF["Syllabus PDF / Text"] --> Parse["Text Extraction & Cleaning"]
    Parse --> Chunk["Sliding Window Chunker (500 tokens)"]
    Chunk --> Embed["OpenAI text-embedding-3-small"]
    Embed --> VectorDB[("pgvector (syllabus_chunks table)")]
    
    subgraph QueryTime["Runtime Grounding"]
        StudentPrompt["Student Query"] --> QueryEmbed["Compute Embedding"]
        QueryEmbed --> CosineSearch["Cosine Similarity Search (IVFFlat)"]
        VectorDB --> CosineSearch
        CosineSearch --> TopK["Top-3 Grounded Excerpts"]
        TopK --> SocraticPrompt["Socratic Tutor Prompt Context"]
    end
```

---

## 🗄️ Relational & Vector Entity-Relationship (ER) Schema

```mermaid
erDiagram
    COURSES ||--o{ COURSE_MODULES : contains
    COURSES ||--o{ SYLLABUS_CHUNKS : owns
    COURSE_MODULES ||--o{ MODULE_RESOURCES : attaches
    COURSE_MODULES ||--o{ ASSIGNMENTS : contains
    ASSIGNMENTS ||--o{ STUDENT_SESSIONS : scaffolds
    STUDENT_SESSIONS ||--o{ STUDENT_EVENTS : logs
    STUDENT_SESSIONS ||--o| EVIDENCE_DOSSIERS : synthesizes

    COURSES {
        uuid id PK
        string code
        string title
        text description
        string domain
        string instructor
        timestamp created_at
    }

    COURSE_MODULES {
        uuid id PK
        uuid course_id FK
        string title
        text description
        int position
        timestamp created_at
    }

    MODULE_RESOURCES {
        uuid id PK
        uuid module_id FK
        string title
        string resource_type
        text source_url
        text grounding_notes
        timestamp created_at
    }

    SYLLABUS_CHUNKS {
        uuid id PK
        uuid course_id FK
        int chunk_index
        text content
        vector embedding
        jsonb metadata
    }

    STUDENT_EVENTS {
        uuid id PK
        uuid session_id
        string student_id
        string event_type
        jsonb payload
        timestamp created_at
    }
```

---

## 🧩 Deep Dive: Modular Reasoning Engines

### Component 1: Course & Curriculum Engine (`fiosra/mvp/courses/`)
- Manages institutional course workspaces (e.g. `HIST-201`, `PHIL-102`).
- Handles unit and prerequisite module sequencing (`ModuleModel`).
- Ingests syllabi: chunks text into semantic segments and calculates OpenAI embeddings (`vector(1536)`).
- Manages Grounded Syllabus Resources attached to individual units (`ResourceModel`), maintaining URLs, PDF references, and primary source citations.

### Component 2: Assignment Designer & Answer Vault (`fiosra/mvp/assignment_designer/`)
- **Syllabus RAG**: Ingests course syllabus context to draft Socratic assignments.
- **Deambiguator**: Flags vague assignment prompts that lack clear evaluation criteria.
- **Answer Vault (`vault.py`)**:
  - Reference solutions, formal proofs, and correct numeric answers are stored separately from assignments.
  - When an assignment is queried via student APIs, the Answer Vault field is **omitted** from Pydantic serialization.

### Component 3: Socratic Dialogue Engine (`dialogue_engine.py`)
- Manages real-time conversational reasoning sessions with students.
- Enforces the **Socratic Dialogue Protocol**:
  1. *Acknowledge & Validate*: Restates the student's premise without confirming accuracy.
  2. *Dialectical Questioning*: Asks counter-questions targeting unstated assumptions.
  3. *Hint Gating*: Queries the student's prior attempt record and only delivers hints if permitted by the ceiling policy.
  4. *Grounded Source Attribution*: Pins excerpts from course readings into the reasoning canvas.

### Component 4: Knowledge Graph Service (`graph_service.py`)
- Tracks atomic **Knowledge Components (KCs)**:
  - Example: `KC_FISCAL_CRISIS_1786`, `KC_ESTATE_TAX_EXEMPTION`.
- Tracks **Student Misconceptions (MCs)**:
  - Example: `MC_NOBLE_TAX_EXEMPTION_ABSOLUTE`.
- Executes prerequisite topological traversals to calculate missing prerequisite KCs for struggling students.

### Component 5: Append-Only Event Store (`event_store.py`)
- Captures all interaction telemetry as typed immutable events in the `student_events` table:
  - `EVENT_SESSION_START`
  - `EVENT_STUDENT_ATTEMPT`
  - `EVENT_SOCRATIC_FEEDBACK`
  - `EVENT_HINT_REQUESTED`
  - `EVENT_MISCONCEPTION_TRIGGERED`
  - `EVENT_FINAL_SUBMISSION`
- Event payloads adhere to strict JSON schemas (`fiosra/data/schemas/transaction_log.schema.json`).

### Component 6: AutoSCORE Evidence Dossier (`evidence_dossier/synthesizer.py`)
- Computes the student's **Autonomy Index** ($A \in [0, 100]\%$):
  $$A = 100 - (\alpha \cdot H_{\text{used}} + \beta \cdot M_{\text{resolved}} + \gamma \cdot R_{\text{interventions}})$$
- Compiles the full trajectory into an **Evidence Dossier** with verifiable quotes, timeline timestamps, and rubric alignment for teacher approval.
