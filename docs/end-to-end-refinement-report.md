# Fiosra End-to-End Product Refinement Report

## Executive summary

Fiosra already had the right foundational architecture for a reasoning-centered learning product: **FastAPI** for the API layer, **PostgreSQL 16 with pgvector** for durable course and evidence data, **Neo4j 5** for prerequisite knowledge components, and a **Svelte 5/Vite** client for educator and student workspaces. The work completed in this iteration preserves that stack and turns the main pedagogical loop into a connected product workflow rather than a collection of largely independent screens and endpoints.

The completed path is now: an educator grounds a course, designs and publishes an answer-isolated assignment, a student starts a durable reasoning session, the Socratic engine records every turn and controls the hint ladder server-side, the student submits the immutable trace, and an educator receives a dossier in a review queue before finalizing the outcome. The client calls the same API contracts that are exercised by the automated regression suite.

## Architecture retained

| Layer | Ground-truth technology | Role in the finished flow |
|---|---|---|
| Web client | Svelte 5 and Vite | Educator design, student reasoning, trace review, and final educator decision screens. |
| API | Python FastAPI | Course, assignment, dialogue, session-event, evidence, and graph endpoints. |
| Durable store | PostgreSQL 16 and pgvector | Courses, modules, resources, assignments, sessions, immutable events, and semantic curriculum chunks. |
| Knowledge graph | Neo4j 5 | Knowledge-component prerequisite DAG and curriculum grounding. |
| Assessment controls | Answer Vault and deterministic verifiers | Keeps reference solutions out of public assignment payloads while generating evidence for educator review. |

## Principal refinements completed

| Product area | Original operational gap | Implemented refinement | Result |
|---|---|---|---|
| **Assignment safety** | The persisted assignment specification contained an internal vault token, and there was no explicit public projection. | Added student-safe assignment retrieval and listing projections that remove `vault_token`; added a regression test ensuring neither the token nor a reference solution appears in public data. | Student canvas retrieves a publishable task without answer material. |
| **Hint integrity** | The client submitted its own hint rung, allowing the browser to influence the scaffolding state. | The dialogue route derives the rung from the append-only event stream, ignores the legacy client value, records each tutor turn, and prevents adversarial messages from obtaining advanced context. | Hint progression is server authoritative and auditable. |
| **Student submission** | Student sessions had no explicit handoff to the educator workflow. | Added an idempotent session submission endpoint, a `submitted` session state, submission event, and a trace screen action. | A student can deliberately send an evidence packet for review without self-grading. |
| **Educator sovereignty** | Evidence was viewable but was not organized into a live queue linked to a student submission lifecycle. | Added an educator review queue, dossier retrieval, grade-finalization endpoint, event logging, and completed-session sealing. | Only the educator workspace performs the final grade decision. |
| **Client workflow** | The student workspace, trace, designer, and review screens used local mock data or lacked a full live handoff. | Rebuilt the four core Svelte routes around live FastAPI calls and hash-route parameters; added reusable session and response utilities. | The main workflow is navigable from a published assignment through final review. |
| **Course continuity** | Published assignments were not easily launchable into the student flow. | Added a student-canvas launch action to published assignment rows in curriculum modules. | The curriculum UI is now a usable entry point into the student experience. |
| **Operational resilience** | Curriculum resource ingestion failed completely when Neo4j was briefly unavailable. | Changed the ingestion path to catch Neo4j connectivity errors and use the existing deterministic KC fallback for resource persistence. | Course materials remain ingestible during a graph-service transient outage. |
| **Portable validation** | A PDF test depended on an absolute path on a former developer machine. | Added a repository-owned PDF fixture and updated the regression test to consume it. | The suite runs from a clean checkout. |
| **Deployment correctness** | Compose mounted a host path over the frontend bundle produced in the image. | Removed the conflicting runtime bind mount; the Docker image now serves the Vite production bundle it builds. | Container deployment no longer depends on an undeclared local asset directory. |
| **Security hygiene** | CORS allowed every origin while enabling credentials. | Replaced wildcard CORS with configurable development origins. | Browser cross-origin access is restricted to explicit origins. |

## User journey now supported

### Educator journey

An educator can create a course and module, ingest source material, and use the Assignment Scaffold Designer to assess prompt ambiguity. The designer gathers alignment inputs where needed, displays the generated knowledge components, a five-rung bounded hint ladder, and rubric criteria, then saves or publishes the assignment. Publishing exposes a public student specification, but not the reference answer or Answer Vault token.

### Student journey

The student opens the published assignment through the curriculum module or a direct student link. The Svelte workspace creates or restores a durable session tied to a local student identity, shows the course sources, and submits each reasoning attempt to the Socratic API. The backend appends the student turn, calculates the permitted hint level, returns a student-safe response, and appends the tutor event. The student can inspect the chronologically reconstructed trace and submit it for educator review.

### Educator review journey

A submitted session appears in the AutoSCORE review queue. Selecting it loads the evidence dossier, including citations to learner turns, rubric evaluation, autonomy indicators, hint dependency, and misconception signals. The educator enters or accepts a grade, leaves formative feedback, and finalizes the decision. Finalization appends a grade event and seals the session as completed.

## Verification

The local validation environment ran PostgreSQL 16 with pgvector and Neo4j 5, then applied the repository migrations and seed pipeline. The graph seed contained 19 knowledge components, 21 prerequisite edges, and 25 misconception records. The complete backend regression suite passed with **56 tests**, including the end-to-end pedagogical lifecycle, answer-isolation projection, submission immutability, course grounding, graph traversal, resource ingestion, dialogue guardrails, evidence dossier generation, and educator finalization.

The final quality command also passed Ruff, built the production Svelte bundle, and completed a whitespace diff check. Browser smoke testing opened the FastAPI-served production bundle at the course portfolio and assignment designer routes. The designer was populated interactively; it returned a live scope diagnosis and rendered the generated scaffold, target knowledge components, locked bottom-out hint, and rubric criteria.

## Recommended next product increment

The repository’s current identity fields are still simple identifiers supplied by the client rather than a full authentication and authorization system. A production rollout should add the project’s selected identity provider, role-bound access control, and server-derived teacher/student identity before exposing educator-only routes outside a controlled deployment. This is intentionally identified as the next increment rather than approximated with insecure client headers. The functional workflow and answer-isolated public projection delivered here remain compatible with that change.
