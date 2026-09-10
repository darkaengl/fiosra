# Audit: Server-Authoritative Agentic Learning Workflow

**Issue:** [#41 — Server-Authoritative Learning Workflow Orchestration][1]  
**Repository state audited:** `feat/end-to-end-learning-workflow`, commit `59036e5d6fc97b42a9a23aa80736d5c6009bae8e`  
**Author:** Manus AI  
**Audit date:** 2026-09-10  
**Scope:** LiteLLM adapter/orchestrator; student dialogue engine and router; assignment generation and public projections; runtime configuration; session/event storage; and the event/evidence routes that affect authority boundaries. This is a design audit only. No production code, settings, database data, or GitHub records were changed.

## Executive conclusion

Fiosra already has a **narrow, answer-blind live-model enhancement path** and several useful server-side controls. The only direct `litellm.acompletion` call is behind `LiteLLMProvider.complete`; `LLMOrchestrator.enhance` provides deterministic fallback, output-size checks, a provider circuit breaker, and prompt-free generation metadata. Student dialogue derives the hint rung from persisted events rather than the client’s `current_rung`, and published assignments have a public projection that removes `vault_token`. These are meaningful foundations. [2] [3] [4] [5] [6] [7]

The implementation does **not yet satisfy issue #41’s server-authoritative workflow acceptance criteria**. There is no typed workflow-state object, action-proposal schema, action allow-list, per-session rate limit, idempotency mechanism, invocation audit event, or dedicated learning-workflow orchestrator. More importantly, current routes permit unvalidated event appends and do not bind a dialogue request’s `student_id` or `question_id` to the authoritative session. A client can therefore write arbitrary event types/payloads through `/events/log`, and a dialogue request can change `student_sessions.current_question_id` because `EventStore.log_event` always updates it. These are authority-boundary defects, not merely missing refinements. [5] [6] [8]

> **Recommended decision:** introduce one server-owned `LearningWorkflowOrchestrator` before adding further agent roles or model capabilities. In its first slice, retain the current pedagogical behavior—deterministic misconception lookup and hint selection, with an optional constrained live Socratic rephrase—but make every state source, proposal, validation decision, rate-limit decision, and fallback explicit and auditable.

The proposed system is “agentic” only in the bounded sense required by the issue: roles may make **schema-validated proposals** from answer-blind context. The orchestrator alone validates, chooses, persists, and emits the action. It must be unable to invoke any action that authors a student response, changes a grade, publishes an assignment, accesses an Answer Vault record, or changes curriculum state.

## Method and evidence standard

This review traced direct imports and invocations, read the source and associated tests, inspected initial database DDL, reviewed issue #41, and ran the isolated LLM test module plus focused Ruff linting. `uv run pytest tests/test_llm_orchestration.py -q` completed successfully (**8 passed**), and `uv run ruff check` for the examined LLM, dialogue, event, and assignment modules completed successfully. The LLM tests use mocked LiteLLM calls; they do **not** establish behavior of a live provider, concurrent dialogue turns, authentication, database authorization, or event tamper resistance.

Facts in this report are marked **Verified** and cite the exact current file/function. Architecture, contracts, limits, and rollout are marked **Proposal**. A proposal is not a claim that the repository currently implements it.

## Current-state map

| Surface | Verified implementation | What it establishes | What it does not establish |
|---|---|---|---|
| LiteLLM boundary | `LiteLLMProvider.complete()` is the sole repository location calling `litellm.acompletion`; it constructs a two-message call with a timeout, zero provider retries, configured model/key/base URL, and an opaque `user` value. | Provider switching is server configuration driven; raw model invocation is centralized in the adapter. | A typed model-output protocol, provider-independent JSON schema mode, per-session quota, request idempotency, or an import/architecture rule preventing future routes from calling the adapter. [2] |
| LLM orchestration | `LLMOrchestrator.enhance()` selects deterministic fallback for disabled/ungrounded/cooldown/error cases; normalizes text; checks length and several answer/format patterns; tracks a process-local consecutive-failure cooldown. | A usable deterministic fallback already exists for the two current live purposes. | A learning-workflow state machine, structured role proposals, output validation beyond text heuristics, action validation, per-session limits, or durable multi-instance circuit-breaker state. [3] |
| Dialogue | `SocraticDialogueEngine.generate_response()` deterministically detects adversarial prompts, computes a rung, queries nearest misconceptions, selects a hint, and optionally asks the LLM only to rephrase a server-selected hint. The model prompt does not include `student_input`. | A conservative, answer-blind phrasing path is already present; ungrounded dialogue disables live generation. | A dedicated diagnosis/action role contract; canonical active canvas section; concurrency-safe rung advancement; a guarantee that a generated question contains no novel leading content; or broad semantic answer-leak detection. [4] |
| Dialogue routing | `handle_dialogue_turn()` gets a session, rejects non-active sessions, resolves an attached assignment from the session, ignores client `current_rung`, gets the current rung from events, and logs input/result events. | Session status and assigned context are partly server derived. | Session-to-student ownership checks, server-owned question/section identity, idempotency, rate limiting, transactional action selection, or an invocation audit record. [5] |
| Assignments and sources | `AssignmentGenerator._load_grounding_sources()` caps five excerpts at 280 characters. `get_public_assignment()` removes `vault_token` before validating `PublicQuestionSpec`; `publish_assignment()` checks a module assignment has course grounding. | A useful answer-blind public assignment/context projection and a source excerpt limit already exist. | A published-only check when creating a student session; assignment revision/snapshot in a student session; an active-section model; source-excerpt IDs as an enforced response constraint; or route authentication. [7] [9] |
| Answer vault | `AnswerVault.lock_solution()` keeps a plaintext Python object keyed by a hash-derived opaque token. Public assignment projection excludes the token and dialogue does not import the vault. | The ordinary public projection and dialogue call path do not expose the token/reference solution. | Cryptographic encryption at rest, process isolation, authenticated educator authorization, durable storage, or a hard capability boundary between all server code and the vault. [10] |
| Events | `EventStore.log_event()` inserts JSONB then updates `student_sessions.last_activity_at` and `current_question_id` in the same SQL statement. The generic `/events/log` endpoint accepts arbitrary `event_type`, JSON payload, `student_id`, `question_id`, and optional assignment ID. | Append/replay behavior exists; `get_current_hint_rung()` reads server-stored prior events. | Typed event payloads, an event-type allow-list, actor/session/assignment binding, internal-only workflow events, idempotent writes, or write-once database privileges. [6] [8] [11] |

### Current execution path

The current student path is narrowly layered but still route-led:

1. `POST /dialogue/message` receives student text and client-supplied identifiers in `DialogueMessageRequest`. [5]
2. `handle_dialogue_turn()` reads `student_sessions`; when an assignment is attached, it replaces the client prompt/domain with the public assignment’s values. It then logs `student_prompt_submitted`. [5]
3. It derives the stored maximum hint rung by reading previous event JSON, then calls `SocraticDialogueEngine.generate_response()`. [5] [6]
4. The engine performs deterministic adversarial detection, optional nearest-misconception lookup, deterministic hint selection, then calls `llm_orchestrator.enhance()` for `socratic_hint_rephrase`. [4]
5. `LLMOrchestrator` calls `LiteLLMProvider` only if the configured provider is non-deterministic and the assignment is course-grounded. Otherwise it returns the supplied deterministic response. [3]
6. The router appends a dialogue event and an optional `misconception_flagged` event. [5]

This is a good baseline for a **single constrained rephrase**, but it is not an orchestrated workflow because the request handler and dialogue engine collectively resolve state, choose behavior, call the model, validate output, and log results without a single typed contract or authoritative action boundary.

## Verified strengths

### Answer-blind context has meaningful, but incomplete, separation

**Verified.** The current dialogue engine imports the LLM orchestrator and misconception search, not `answer_vault`. It passes the active question prompt and a selected hint to `enhance()`; it does not pass the student’s text to the live rephrase call. `LLMOrchestrator` documents that callers must resolve answer-blind context before calling it. Public assignment retrieval removes `vault_token`, and `PublicQuestionSpec` has no `vault_token` or `reference_solution` field. [3] [4] [7]

This is pedagogically sound because the live model is currently limited to wording an already selected nudge. It reduces direct solution extraction and preserves a deterministic path when the model is unavailable. It should remain the core shape of the first slice.

**Verified qualification.** `AnswerVault` is an in-memory dictionary that stores the reference solution as plaintext. Its opaque token uses SHA-256 but the solution itself is neither encrypted nor isolated in a separate process or service; `unlock_solution_for_educator()` accepts any nonempty caller-provided teacher identifier without an authentication check. The audit can verify **application-level token projection**, not the “cryptographically isolated” or authenticated-educator properties claimed in its docstring. [10]

### Provider selection and ordinary reliability fallback are already configuration-driven

**Verified.** `Settings` exposes `FIOSRA_LLM_PROVIDER`, provider model/key/base settings, a timeout, and failure/cooldown settings. `LiteLLMProvider.from_settings()` maps `openrouter`, `openai`, `gemini`, and `ollama` to those settings; `LLMOrchestrator.enhance()` falls back deterministically for a deterministic provider, disabled live use, cooldown, adapter exceptions, timeout, empty output, and rejected output. [2] [3] [12]

**Verified.** The isolated unit tests cover default no-network operation, pseudonymous provider metadata, rejected answer-key-style output, missing credentials, ungrounded live-provider suppression, named provider configuration, and the GPT-5 token parameter branch. [13]

This aligns with issue #41’s requirement that provider selection and fallback remain configuration-only through LiteLLM. The new workflow should reuse—not duplicate—this adapter boundary, while adding a structured response mode and workflow-specific budgets at the orchestrator layer.

### Hint persistence is server-derived in the ordinary route

**Verified.** `DialogueMessageRequest.current_rung` is explicitly described as ignored, and `handle_dialogue_turn()` obtains the stored rung using `event_store.get_current_hint_rung()` before calling the engine. The engine caps requested progress at rung 3 and does not advance an adversarial prompt. Tests exercise the monotonic normal sequence and adversarial no-advance behavior. [4] [5] [6] [14]

This supports productive struggle: a student cannot simply submit a larger `current_rung` to receive a deeper hint. The proposed workflow must preserve this control while correcting its scope and concurrency weaknesses.

### Assignment context is more structured than free-form conversation

**Verified.** Assignment scaffolding persists target KCs, a five-entry hint ladder where level 4 is locked, rubric criteria, grounding mode, and public grounding sources. A source loader returns no more than five excerpts truncated to 280 characters. Module assignment publication fails if it lacks course grounding, and public retrieval strips the vault token. [7]

That is a practical minimum for an answer-blind context packet. The proposed state model should consume the `PublicQuestionSpec` projection rather than the raw assignment JSON, and should carry only selected public excerpts and IDs.

## Authority, safety, and pedagogy gaps

The following are **verified code-level gaps**. They are listed in priority order because the first three can compromise the premise that the server is authoritative even without a live LLM.

| Priority | Verified finding | Consequence | Exact current boundary |
|---|---|---|---|
| P0 | `/events/log` accepts arbitrary event type/payload and caller-supplied session/student/question/assignment fields, then invokes the generic append method without ownership, type, or payload validation. | Any caller able to reach the route can poison the learning record, impersonate a student, create fake hint/misconception events, or influence aggregate evidence. It also invalidates the trustworthiness of event-derived rate limits and hint state. | `events_router.log_session_event()` and `EventStore.log_event()` [6] [8] |
| P0 | `DialogueMessageRequest.student_id` is not compared with `session_info["student_id"]`. The router passes the request value to both event writes. | Dialogue history can be attributed to a different student. A future state/action audit based on these fields would be unreliable. | `handle_dialogue_turn()` [5] |
| P0 | The dialogue route accepts client `question_id`; `EventStore.log_event()` always sets `student_sessions.current_question_id = :question_id`. There is no equality check against the server session value. | A caller can alter the authoritative active question, which is the current proxy for canvas position. This directly conflicts with an authoritative active-section requirement. | `handle_dialogue_turn()` and `EventStore.log_event()` [5] [6] |
| P0 | The event-derived rung query includes `hint_delivered`, `tutor_turn_completed`, and `adversarial_probe_defended`, reading an unconstrained JSON `hint_rung`. | Together with the open event endpoint, a forged event can change observed hint state. It also aggregates across the entire session rather than explicitly scoping to a section/question. | `EventStore.get_current_hint_rung()` [6] |
| P1 | No session-scoped idempotency key, event uniqueness constraint, turn record, or database locking/compare-and-swap exists around “read rung → generate → append action.” | Retries can produce duplicate student prompts/actions. Concurrent hint requests can observe the same rung and each produce an action. A future model call could be paid twice and produce divergent messages. | `handle_dialogue_turn()`, `get_current_hint_rung()`, `log_event()` [5] [6] [11] |
| P1 | There is no request or model-call rate limiter. The only throttling-like control is a process-local provider failure circuit breaker. | A single session can request unlimited turns/hints and repeated paid completions. Process-local state is inconsistent across workers and is not a pedagogical pacing control. | `LLMOrchestrator._failure_count/_cooldown_until` and settings [3] [12] |
| P1 | There is no typed workflow state, role proposal, action enum, action-policy matrix, or invocation audit event. Current response and event payloads are ad hoc dictionaries. | There is no stable interface on which to validate an agent’s authority, prove an allow-list, or evolve roles without route-level logic. | `SocraticDialogueEngine.generate_response()`, `DialogueMessageResponse`, `EventStore.log_event()` [4] [5] [6] |
| P1 | The model output check is text-pattern based. For Socratic rephrasing it mostly requires nonempty text, a character ceiling, absence of several “answer-key” phrases, and a final `?`. | A question can still contain invented facts, an overly leading answer, a rubric judgment, or harmful content while passing. Pattern checks are a useful backstop, not semantic proof of non-disclosure. | `LLMOrchestrator._clean_candidate()` [3] |
| P1 | A session can be created with any assignment UUID without verifying that the assignment exists or is published. Dialogue resolves an attached assignment regardless of its `status`. | A learner can be attached to a draft/unavailable context, which weakens curriculum and teacher-authority guarantees. | `EventStore.create_session()` and `handle_dialogue_turn()` [5] [6] |
| P2 | Active section is not modeled. The only persistent positional field is `current_question_id`; the client controls it through current event logging. | The issue’s required active-canvas-section state cannot be represented or enforced, and per-section hint/rate analysis cannot be reliable. | DDL `student_sessions`, event store [6] [11] |
| P2 | The generic dialogue fallback uses a fixed ladder and no requested `question_prompt` can be trusted without an authoritative assignment. | The response remains usable, but pedagogical relevance and source anchoring degrade for unassigned sessions. It is appropriate that live rephrasing is disabled, but the system should not present it as a grounded agentic workflow. | `SocraticDialogueEngine.generate_hint_ladder()` and `generate_response()` [4] |
| P2 | Evidence synthesis defines `solved_correctly` largely as “has an attempt and no adversarial count,” then produces a suggested grade. | This is outside the new workflow’s execution path, but it can overstate learning and should not consume new agent decisions as truth. Final grading is route-accessible without authentication in current code. | `EvidenceDossierSynthesizer.synthesize_dossier()` and `finalise_student_grade()` [15] [16] |

### Pedagogical assessment

The existing learning design has strong intentions: answer-blind hints, a graduated ladder, a misconception taxonomy, source-grounded assignments, and deterministic fallback all support **guided inquiry rather than cognitive offloading**. The level-4 locked bottom-out entry is particularly appropriate as a visible boundary, although current dialogue caps at 3. [4] [7]

Its main pedagogical risk is not only technical misuse. The engine advances a rung whenever `hint_requested` is true, without using verified attempt quality, section state, time for reflection, or a transparent retry rule. Conversely, nearest-misconception matching considers a similarity threshold of `> 0.01`; this is very permissive, even though course-grounded assignments subsequently require the matched KC to be among the target KCs. A wrong diagnosis can anchor a student to an irrelevant misconception and produce false confidence. [4]

The minimal workflow should therefore make diagnosis **advisory and reversible**. It should not label a learner with a misconception as fact. It should only select a relevant, low-stakes Socratic action from the public hint ladder. A diagnosis must be identified as an approximate match, carry confidence and source/KC evidence, expire when new student text arrives, and never drive grades, publication, progression, or permanent learner profile updates.

## Proposed minimal target architecture

### Design constraints

**Proposal.** Keep the first implementation deliberately small:

1. Preserve assignment authoring as a separate workflow. The new orchestrator governs **student learning turns only**. `AssignmentGenerator.generate_scaffolding_plan()` may remain an educator-facing caller of `LLMOrchestrator`, provided it retains its own answer-isolation and publication controls. [7]
2. Make the new orchestrator the **only student-workflow caller** of `LLMOrchestrator.enhance()`. `SocraticDialogueEngine` becomes deterministic policy/selection logic or is folded into the orchestrator. The LiteLLM adapter remains the only component that calls LiteLLM.
3. Treat all request identifiers and client state as claims, not authority. Resolve actor identity from authentication and session/assignment/section from the server.
4. Limit agent roles to deterministic assembly, deterministic diagnosis, and optional constrained phrasing. No role may mutate state, call a database write method, select a provider, select a model, call a route, grade, publish, unlock a vault, or access a reference solution.
5. Store the accepted action and operational audit in the same successful commit as the resulting learning event. Do not persist raw prompts, rejected model output, chain-of-thought, or a reference solution.

### Component boundary

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Router as Dialogue router
    participant W as LearningWorkflowOrchestrator
    participant ES as Event/session repository
    participant A as Public assignment repository
    participant D as Deterministic diagnosis
    participant L as LLMOrchestrator / LiteLLM

    Student->>Router: turn_id + student text + optional hint request
    Router->>W: authenticated actor + validated input
    W->>ES: reserve idempotency key; read authoritative session
    W->>A: fetch published PublicQuestionSpec only
    W->>ES: read bounded current-section events
    W->>W: assemble frozen answer-blind WorkflowState
    W->>D: deterministic diagnosis proposal
    W->>W: policy validates proposal and selects allow-listed action
    alt constrained phrasing is eligible and budget permits
        W->>L: public bounded packet + selected canonical prompt
        L-->>W: schema-shaped SocraticProposal
        W->>W: validate schema, action, provenance, wording
    else unavailable/rejected/rate-limited
        W->>W: use canonical deterministic fallback
    end
    W->>ES: atomically commit action + prompt-free invocation audit
    W-->>Router: cached/committed student-safe response
    Router-->>Student: action text, rung, limited metadata
```

The router should perform transport validation and authentication only. The workflow orchestrator should be the **single owner** of state resolution, action selection, live-eligibility selection, output validation, fallback, and persistence. This removes the present split between `dialogue_router.handle_dialogue_turn()` and `SocraticDialogueEngine.generate_response()`. [4] [5]

### Required typed state

**Proposal.** Add `fiosra/mvp/learning_workflow/contracts.py` with strict Pydantic v2 models and frozen resolved state. The state is constructed server-side and is never accepted wholesale from a client.

```python
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class CanvasSectionState(StrEnum):
    ACTIVE = "active"
    COMPLETE = "complete"

class PublicExcerpt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    chunk_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    kc_id: str | None = Field(default=None, max_length=128)
    text: str = Field(min_length=1, max_length=320)

class RecentStudentText(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: int = Field(gt=0)
    section_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=1200)

class HintPolicyState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    current_rung: int = Field(ge=0, le=3)
    permitted_rung: int = Field(ge=0, le=3)
    hint_requested: bool
    locked_rungs: tuple[int, ...] = (4,)

class LearningWorkflowState(BaseModel):
    """Answer-blind, server-resolved input to bounded learning roles."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: str = "1"
    workflow_id: UUID
    turn_id: UUID
    state_version: int = Field(ge=0)
    session_id: UUID
    actor_student_id: str = Field(min_length=1, max_length=64)
    assignment_id: UUID
    assignment_revision: str = Field(min_length=1, max_length=128)
    active_canvas_section: str = Field(min_length=1, max_length=64)
    section_state: CanvasSectionState
    assignment_prompt: str = Field(min_length=3, max_length=4000)
    hint_policy: HintPolicyState
    public_source_excerpts: tuple[PublicExcerpt, ...] = Field(max_length=5)
    target_kcs: tuple[str, ...] = Field(min_length=1, max_length=16)
    recent_student_authored_text: tuple[RecentStudentText, ...] = Field(max_length=3)
```

The issue’s required fields are explicit: assignment, `active_canvas_section`, permitted hint rung, public excerpts, target KCs, and recent student-authored text. Add the request/turn/state versions because they are necessary to make an authoritative state actionable under retry and concurrency.

**State sources.** `assignment_id`, assignment prompt, KCs, ladder, and excerpts must come from a **published** `PublicQuestionSpec`, not request JSON. `active_canvas_section` must come from a server-owned session field and match an assignment-declared section. In the first slice, use the existing `current_question_id` only after removing client control over it; add an explicit `active_section_id` before multi-section canvas work. `recent_student_authored_text` must be limited to the current section’s authenticated, accepted `student_prompt_submitted` events, ordered by `event_id`, with a count and character cap. The model does not need the entire event stream.

The state deliberately excludes all of the following: `vault_token`, `reference_solution`, private assignment JSON, rubric answer keys, grade/suggested grade, educator comments, full event history, other students’ data, plain student identifier in an external prompt, provider API key, and unapproved source content. The provider sees only an opaque per-session pseudonym as today. [3] [7]

### Roles, allow-listed actions, and proposal contract

**Proposal.** The roles should be small, deterministic where possible, and independent of database writes.

| Role | Implementation in first slice | Input | Permitted proposal | Live model eligible? | Prohibited capability |
|---|---|---|---|---|---|
| `context_assembler` | Deterministic repository/service function | Authenticated turn and server repositories | `no_op` plus a successful state-resolution marker | No | Picking a section, source, rung, or provider from client input; any write except reserved turn bookkeeping owned by orchestrator |
| `misconception_diagnoser` | Existing pgvector lookup plus KC/threshold policy | Bounded recent text, target KCs, domain | `flag_misconception` or `no_op` | No | Declaring correctness, changing a grade, advancing a rung, or producing student-facing prose |
| `action_policy` | Deterministic orchestrator method, not a model role | State and validated diagnosis | `ask_socratic_question`, `deliver_selected_hint`, `integrity_redirect` | No | Any action not in the enum; section progression; grading; publication; answer access |
| `socratic_phraser` | Optional constrained rephrase through existing LLM boundary | Canonical selected text and a minimal public packet | `ask_socratic_question` only | Yes, course-grounded only | Selecting hint rung/action, citing unselected facts, writing a student answer, or updating state |

The three roles required by the issue are thus present, but only the phrasing role needs a model. “Agentic” selection remains bounded because the deterministic policy has final selection authority.

```python
class WorkflowRole(StrEnum):
    CONTEXT_ASSEMBLER = "context_assembler"
    MISCONCEPTION_DIAGNOSER = "misconception_diagnoser"
    SOCRATIC_PHRASER = "socratic_phraser"

class LearningAction(StrEnum):
    NO_OP = "no_op"
    FLAG_MISCONCEPTION = "flag_misconception"
    ASK_SOCRATIC_QUESTION = "ask_socratic_question"
    DELIVER_SELECTED_HINT = "deliver_selected_hint"
    INTEGRITY_REDIRECT = "integrity_redirect"

class RationaleCode(StrEnum):
    ADVERSARIAL_REQUEST = "adversarial_request"
    HINT_EXPLICITLY_REQUESTED = "hint_explicitly_requested"
    HINT_CEILING_REACHED = "hint_ceiling_reached"
    TARGET_KC_MATCH = "target_kc_match"
    NO_RELIABLE_DIAGNOSIS = "no_reliable_diagnosis"
    LIVE_REPHRASE_ELIGIBLE = "live_rephrase_eligible"

class ActionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1"
    role: WorkflowRole
    action: LearningAction
    rationale_codes: tuple[RationaleCode, ...] = Field(max_length=4)
    misconception_id: str | None = Field(default=None, max_length=64)
    kc_id: str | None = Field(default=None, max_length=128)
    requested_rung: int | None = Field(default=None, ge=0, le=3)
    source_chunk_ids: tuple[str, ...] = Field(default=(), max_length=2)
    student_visible_text: str | None = Field(default=None, max_length=420)
```

The contract must use `extra="forbid"`, enum values, maximum lengths, and a version. A proposal is **not a command**. It contains no field such as `next_section`, `grade`, `publish`, `vault_token`, `tool_name`, `SQL`, `url`, `model`, `provider`, or arbitrary parameters. The server produces the authoritative `SelectedAction` after it validates the proposal against `LearningWorkflowState`.

The role/action matrix must be enforced in code, not merely prompted:

| Role | Accepted actions | Required fields | Rejection examples |
|---|---|---|---|
| Context assembler | `no_op` | no student text, no source IDs | any UI/action request, unknown field, source selected by client |
| Misconception diagnoser | `flag_misconception`, `no_op` | known `misconception_id`, matching `kc_id`, current target KC, confidence above configured threshold | `deliver_selected_hint`, target-KC mismatch, unknown diagnosis ID |
| Action policy | `ask_socratic_question`, `deliver_selected_hint`, `integrity_redirect` | canonical text and valid rung where applicable | rung above permitted, locked rung, unsupported action, section change |
| Socratic phraser | `ask_socratic_question` | exactly one bounded question | hint action, unknown source ID, non-question, multi-part answer, any state field |

### Validation order

**Proposal.** Validation should be a fail-closed sequence. The server must perform it before any state-changing event and again after any optional live rephrase.

1. **Authenticate and bind identity.** Do not accept `student_id` as authority from a JSON body. Resolve it from the authenticated principal. Verify `student_sessions.student_id == principal.subject`. A route authentication mechanism is not present in the current application, so this is a prerequisite for real authority, not a cosmetic field check. [5] [8] [16]
2. **Validate the transport request.** Accept only `turn_id`, bounded `student_input`, `hint_requested`, and perhaps a UI `expected_state_version`. Do not accept assignment ID, question ID, domain, rung, prompt, actor ID, model/provider, or section ID as mutable learner inputs.
3. **Reserve idempotency and serialize the session turn.** Scope uniqueness to `(session_id, turn_id)`, record a request-content hash, and return the completed stored response for a repeat with the same hash. Return `409` for a reused key with a different hash and `409/202` for a distinct turn while another turn for that session is processing. Do not charge another live call.
4. **Resolve and validate server state.** Require session status `active`, a matching published assignment, an active server section, target KCs, and a valid public ladder. Reject missing/invalid context rather than falling back to client prompt for an “authoritative” workflow.
5. **Classify integrity and compute policy deterministically.** Handle adversarial extraction with `integrity_redirect` before sending any model request. Calculate current/permitted rung from typed, current-section events or a materialized server-state field. A request can progress at most one rung and never past the configured ceiling/locked ladder entries.
6. **Validate diagnosis.** The selected `misconception_id` must come from the deterministic query result, meet a conservative configuration threshold, match one of `target_kcs`, and be associated with the active section. When confidence is insufficient, use `no_op`; do not invent a remediation label.
7. **Validate the proposed action against the allow-list.** Check the role/action matrix, action-specific fields, rung, source IDs, canonical fallback, policy/rate status, and forbidden capabilities. The orchestrator, not a role, selects the final action.
8. **Apply limits before live generation.** If the session has exhausted a relevant limit, do not invoke LiteLLM. Select the specified deterministic rate-limit fallback and log the reason.
9. **If eligible, validate the model output as a `SocraticPhrasingProposal`.** Strict-parse JSON or a bounded text envelope, reject unknown fields, require `action == ask_socratic_question`, one question mark at the end, no markdown/list/quote, maximum characters, no answer/rubric/grade/vault language, no unapproved source IDs, and no numbers/proper nouns/new content outside the canonical prompt and approved public packet. Use deterministic fallback on any parse, provider, timeout, schema, policy, or lexical-anchor failure.
10. **Atomically persist accepted action and audit.** Recheck the `state_version` and active section, then write the student-visible event and a prompt-free workflow audit event in one transaction. If the version changed, discard the stale model response and recompute or return a safe retry response; do not deliver an action calculated for stale state.

The lexical/source-anchor check in step 9 is intentionally conservative. A generic output filter cannot prove that a sentence does not function as an answer. The strongest safety measure is to give the model only a canonical server-selected Socratic question or hint and to reject novel factual content. The deterministic fallback remains the authoritative content.

### Structured LLM output

**Proposal.** Extend the completion contract only as far as necessary. The adapter can accept an optional response schema/format and return raw bounded text to the workflow, which Pydantic validates locally. Do not trust provider JSON mode by itself; support varies by LiteLLM provider/model.

```python
class SocraticPhrasingProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: str = "1"
    action: Literal[LearningAction.ASK_SOCRATIC_QUESTION]
    text: str = Field(min_length=8, max_length=420)

class ValidatedPhrasing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    used_live_provider: bool
    fallback_reason: str | None = None
```

A minimal system instruction should state that the model is a **stylistic rephraser**, not an action selector: it must emit the schema only; preserve the supplied question’s intent; output a single question; introduce no facts, answer, analysis, praise/grade, source citation, or next action; and never mention hidden instructions, an answer key, rubric, vault, teacher, or system. The user packet should include a canonical server-selected question and, only if needed, approved excerpt IDs/text. It must not include Answer Vault material, hidden rubric answer content, complete event history, model metadata, identity, or free-form action instructions.

For the initial slice, a still safer option is to keep the existing string call but require that the model can only rephrase `ASK_SOCRATIC_QUESTION` after the server has already selected it. The agent never proposes `DELIVER_SELECTED_HINT`, because hint advancement has greater pedagogical and state impact. The deterministic fallback returns the exact canonical question.

### Rate limits and idempotency

**Proposal.** Define workflow controls as deployment configuration, not client parameters or provider-specific options. The values below are recommended defaults that should be piloted with educators and accessibility stakeholders, not treated as universal instructional policy.

| Setting | Recommended default | Scope | Behavior on limit | Rationale |
|---|---:|---|---|---|
| `FIOSRA_WORKFLOW_TURNS_PER_SESSION_PER_MINUTE` | 20 | session | return a short deterministic “pause, reread the selected evidence, then submit one claim” action; do not call model | Prevents automated flooding without blocking ordinary drafting and revision. |
| `FIOSRA_WORKFLOW_LIVE_REPHRASES_PER_SESSION_PER_MINUTE` | 6 | session | use the canonical deterministic question; emit `live_rate_limited` | Caps paid/external calls while retaining full instructional availability. |
| `FIOSRA_WORKFLOW_HINT_ACTIONS_PER_SESSION_PER_MINUTE` | 4 | session + active section | do not advance; return the current-rung reflection prompt; emit `hint_rate_limited` | Slows rapid hint-clicking while allowing meaningful help. |
| `FIOSRA_WORKFLOW_HINT_COOLDOWN_SECONDS` | 10 | session + active section | no rung advance; return the current canonical prompt | Encourages reading/revision and mitigates duplicate-click races. |
| `FIOSRA_WORKFLOW_RECENT_TEXT_COUNT` | 3 | turn packet | truncate deterministically | Minimizes data exposure and prompt injection surface. |
| `FIOSRA_WORKFLOW_RECENT_TEXT_MAX_CHARS` | 1,200 | event/turn packet | truncate before role input | Bounds context and provider exposure. |
| `FIOSRA_WORKFLOW_DIAGNOSIS_MIN_SIMILARITY` | educator-validated, initially materially above `0.01` | diagnosis | `no_op` when below threshold | Avoids presenting weak vector proximity as a learner misconception. |

Rate records must be durable and queryable across application instances—either typed event counts constrained to current section/window or a small `workflow_turns` table. The current class-level circuit breaker is retained for provider health, but it is neither a user/session rate limit nor a durable distributed control. [3]

A minimal idempotency table should retain `session_id`, `turn_id`, `actor_id`, `request_hash`, `state_version`, status (`processing`, `completed`, `failed_safe`), selected action, serialized student-safe response, event IDs, timestamps, and expiry. Create a unique constraint on `(session_id, turn_id)`. A duplicate with the same hash returns the cached response and must not append a second action/audit event. A duplicate with a different hash is rejected. No raw student text need be copied into the table; retain a cryptographic hash and refer to the accepted student-input event.

### Event design and audit record

**Proposal.** Remove public generic event logging from the student-facing API. Keep an internal repository method but expose only typed server-owned commands, or restrict specific client telemetry to a separate validated allow-list that cannot emit workflow, grade, hint, verifier, or state events.

Add typed events such as:

| Event type | Writer | Required payload (illustrative, prompt-free where operational) | Forbidden payload |
|---|---|---|---|
| `student_prompt_submitted` | Workflow orchestrator | `turn_id`, `section_id`, authenticated actor binding, accepted text (existing learning trace need) | client-supplied actor/session/assignment authority fields |
| `learning_action_delivered` | Workflow orchestrator | `turn_id`, `section_id`, `action`, `rung`, `source_chunk_ids`, `misconception_id?`, approved student-visible text | raw LLM response, prompt, chain-of-thought, answer material |
| `workflow_invocation_audited` | Workflow orchestrator | `workflow_id`, `turn_id`, `state_version`, role names/outcomes, selected action, validation outcome, provider/model/token/latency metadata, `used_live_provider`, controlled fallback reason, policy version, rate-limit result, idempotent replay flag | system/user prompts, student text duplication, rejected model output, secret keys, vault tokens/reference solution |
| `misconception_flagged` | Workflow orchestrator | `turn_id`, `section_id`, diagnosed code, target KC, confidence band | permanent mastery/grade outcome |
| `workflow_action_rejected` | Workflow orchestrator | `turn_id`, action/validation code, safe fallback action | raw malicious request/model content |

The existing `GenerationMetadata` has a strong base—provider, model, live-use flag, latency, token counts, and fallback reason are already prompt-free. Convert fallback reason from an arbitrary truncated exception string into a controlled enum such as `provider_unavailable`, `provider_timeout`, `provider_cooldown`, `output_parse_failed`, `output_schema_failed`, `output_policy_rejected`, `requires_course_grounding`, `live_rate_limited`, `hint_rate_limited`, `stale_state`, or `deterministic_provider`. [3]

For atomicity, persist `learning_action_delivered` and `workflow_invocation_audited` in the same transaction as the completed idempotency row. The input event can be committed during initial turn reservation; then the final audit references its event ID. If a model call fails, complete the same turn with a deterministic action and audit rather than leaving an opaque processing record. A durable recovery job may convert expired processing leases into the deterministic fallback, but it must never replay a live completion automatically.

### Configuration and provider policy

**Proposal.** Preserve the present environment-driven LiteLLM selection exactly in spirit:

- `FIOSRA_LLM_PROVIDER` and per-provider model/key/base URL remain the only provider selection mechanism.
- No student request, assignment field, agent proposal, or route may select a provider, model, base URL, retry count, tool, or fallback provider.
- `LLMOrchestrator` remains the only code that creates `LiteLLMProvider` for the student workflow.
- The workflow chooses whether a live rephrase is eligible; it never selects a vendor. Existing course-grounded gating should remain.
- Provider error, timeout, malformed JSON, schema error, policy rejection, cooldown, disabled configuration, rate limit, stale state, and missing ground context all deliver a deterministic canonical next action.

Keep `num_retries=0` in the adapter so that deterministic workflow fallback remains visible and auditable rather than hidden by vendor retries. Current timeout and generic circuit-breaker behavior are appropriate starting points, though production deployment should provide a durable shared breaker if running multiple processes. [2] [3] [12]

## First implementation slice

**Proposal: P0 first slice — “authoritative constrained Socratic turn.”** Do not add autonomous section progression, new external tools, grading actions, or multi-agent planning. Build only the server boundary required to make one dialogue turn safe and auditable.

1. Add `learning_workflow/contracts.py` with `LearningWorkflowState`, role/action enums, proposal/response/event payload models, `extra="forbid"`, versions, and explicit field limits.
2. Add a `LearningWorkflowOrchestrator.handle_turn()` service. Move state resolution, adversarial redirect, rung calculation, diagnosis acceptance, canonical action selection, optional live rephrase, and fallbacks into it. Make the dialogue router a thin transport/auth adapter.
3. Constrain the current engine to deterministic helpers. Remove direct calls to `llm_orchestrator.enhance()` from `SocraticDialogueEngine`; student calls originate only in the new workflow orchestrator. Continue to allow the separately scoped assignment generator’s educator authoring call.
4. Harden authority before relying on events: delete or make `/events/log` internal-only; authenticate requests; derive actor/session assignment/question/section only from server state; verify a session is bound to a published assignment at creation; and reject a draft/unassigned session from the authoritative route.
5. Add a durable `(session_id, turn_id)` idempotency record and current-section authoritative state/version. Ensure a client cannot change `current_question_id` through an event payload. Use a transaction and version check to avoid stale model results.
6. Introduce the three per-session limits and controlled fallback enums. The live phrasing budget is independent of normal deterministic dialogue availability.
7. Emit `learning_action_delivered` and `workflow_invocation_audited`, and add tests for action validation, rejection, duplicate replay, request/actor mismatch, event forgery denial, concurrent/stale turn handling, limits, output-schema rejection, every fallback, no-vault packet, and prompt-free audit fields.

This slice meets the issue’s architectural intent without expanding model authority. It also repairs the current risks that would otherwise make “server-authoritative” a misleading label.

## Acceptance criteria and test matrix

**Proposal.** The following tests should be green before enabling a live provider for student turns.

| Requirement | Acceptance test |
|---|---|
| Typed state | A unit test builds state only from a session, published `PublicQuestionSpec`, and current-section events; request-supplied assignment/prompt/rung/section values cannot appear in it. Validation rejects unknown fields, extra excerpts, locked rungs, and private fields. |
| Answer isolation | Assert serialized model packet/audit payload lacks `vault_token`, `reference_solution`, raw private spec, grade, rubric answer content, educator comments, and full history. Include a canary vault string and assert it is absent. |
| Single student model caller | Static/import test asserts student dialogue modules do not import `LiteLLMProvider` or call `llm_orchestrator.enhance`; integration test spies one orchestrator invocation only when eligible. Educator assignment authoring is tested separately. |
| Allow-listed actions | Parametrized role/action matrix rejects unsupported actions, undeclared fields, provider/model/tool fields, section change, grade/publish/answer actions, invalid source IDs, and rung escalation. The fallback response is deterministic. |
| Authoritative actor/section | A request with a different student ID, question/section, or assignment claim cannot alter the session; unauthenticated/unauthorized requests are rejected. An event client cannot append workflow, grade, or hint events. |
| Published-context gate | Session creation rejects nonexistent/draft assignment IDs. Authoritative workflow rejects a session without a valid active published assignment rather than using client prompt context. |
| Idempotency | The same `(session_id, turn_id, body hash)` returns byte-equivalent cached response and yields exactly one input/action/audit sequence. Same key with changed body is `409`; overlapping distinct turns cannot both commit a state transition. |
| Rate limits | Limits are measured per session and section across two app instances/test repositories; a limit causes no LiteLLM call, no rung advancement, a recorded controlled reason, and a usable deterministic response. |
| Schema/output validation | Invalid JSON, unknown fields, non-question text, multiple questions, excessive length, answer-key/rubric/vault language, invented numerals/entities, unapproved sources, and action mismatch all fall back deterministically and log `output_policy_rejected`/specific controlled code. |
| Fallback coverage | Deterministic provider, no credential, timeout, adapter error, provider cooldown, missing grounding, live budget exhaustion, diagnosis miss, invalid state, stale state, and model rejection each produce one usable action/audit outcome. |
| Audit properties | Audit event includes workflow/turn/state/action/validation/provider metadata/fallback/rate/idempotency values, while containing no prompt, raw rejected model output, secret, or vault material. Verify event ordering and linkage. |
| Pedagogical quality | Educator-reviewed fixtures show current-rung-only help, no bottom-out answer, target-KC relevance, conservative diagnosis abstention, predictable hint progression, and a clear recovery response after an adversarial prompt or rate limit. |

## Deferred work and explicit non-goals

The first slice should **not** implement model-selected tools, multi-step autonomous plans, student-work authoring, automatic section unlocking, content publication, grade changes, rubric verdicts, Answer Vault retrieval, browser/network tools, or background retry agents. Those capabilities need separate threat models, authorization design, pedagogical evaluation, and stronger persistence boundaries.

An explicit active-section model and durable encrypted/authorized Answer Vault are important follow-ups. They are not prerequisites for extracting the current rephrase logic into an orchestrator only if the first slice rejects unassigned/unpublished contexts and treats `current_question_id` as a server-controlled compatibility field. They become prerequisites before enabling the documented multi-section canvas/progression behavior.

## Final assessment

The codebase has the beginnings of a safe hybrid approach: deterministic learning policy first, optional LiteLLM wording second, and deterministic fallback always. The correct next move is not to broaden prompting or add free-form agents. It is to formalize the existing intended boundary into one **server-authoritative workflow service** and to close the open event/session authority gaps.

A successful implementation of the first slice will make the server—not the client, event payload, or model—the only component that can select a permitted learning action. It will preserve the strongest current pedagogical feature: every learner gets a useful bounded next step even when a model fails, is rate-limited, is unsafe, or is not allowed to run.

## References

[1]: https://github.com/darkaengl/fiosra/issues/41 "GitHub issue #41: Server-Authoritative Learning Workflow Orchestration"
[2]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/llm/litellm_provider.py "LiteLLM provider adapter"
[3]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/llm/orchestrator.py "LLM orchestrator and guarded generation"
[4]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_engine.py "Socratic dialogue engine"
[5]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/dialogue_router.py "Dialogue router"
[6]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/event_store.py "Append-only event store"
[7]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/generator.py "Assignment generator and public assignment projection"
[8]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/events_router.py "Event router"
[9]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/schemas.py "Assignment and public-question schemas"
[10]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/assignment_designer/vault.py "In-memory Answer Vault"
[11]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/migrations/001_initial_schema.sql "Initial PostgreSQL schema migration"
[12]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/config.py "Application settings including LiteLLM configuration"
[13]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_llm_orchestration.py "LLM orchestration tests"
[14]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/tests/test_hint_ceiling.py "Hint ceiling tests"
[15]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/synthesizer.py "Evidence dossier synthesizer"
[16]: https://github.com/darkaengl/fiosra/blob/59036e5d6fc97b42a9a23aa80736d5c6009bae8e/fiosra/mvp/evidence_dossier/router.py "Evidence dossier router and grade finalisation"
