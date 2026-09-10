# Student Evidence Packet PDF Plan

**Author:** Manus AI  
**Status:** Proposed for approval; no implementation changes are authorized by this plan  
**Scope:** A post-submission PDF that preserves the learner’s completed canvas sections and makes the submitted work readable in the educator evaluation workflow  
**Dependency:** The planned role-bound workflow orchestration in Issue #41 must establish educator authorization before an educator-only PDF download route is enabled.

## Decision

Fiosra should create a **server-generated evidence packet PDF** when a learner submits a completed assignment for review. The packet will preserve the submitted state of the student-owned reasoning canvas and present it in an evaluator-friendly sequence: assignment context, student-authored sections, attached approved sources, assistance attribution, and the non-authoritative process trace. It will not contain Answer Vault data, a reference answer, hidden educator prompt material, autonomous AI prose, a generated grade, or unapproved source content.

> **The PDF is a frozen submission artifact, not an essay generator.** It shows what the learner wrote and what assistance was offered or applied. It does not synthesize an answer on the learner’s behalf.

The service will render the PDF from a canonical server-side snapshot using Typst. The visual document template is versioned with the application and compiled in the backend runtime. PostgreSQL stores the immutable structured snapshot and integrity digest, not raw model-generated prose or a mutable PDF blob.

## User journey

| Moment | Learner experience | Educator experience | System behavior |
|---|---|---|---|
| **Before submission** | Learner writes and revises within the protected canvas. | No packet exists. | Canvas drafts and sources retain their current revision semantics. |
| **Submit for review** | Learner sees that the trace and evidence packet are frozen for evaluation. | The submitted session appears in the review queue. | The server atomically seals the submission state, records the submission event, and writes a canonical packet snapshot with a SHA-256 digest. |
| **Download packet** | The learner can download their own completed packet from the trace page, using their session capability. | An authorized educator can download the evaluator copy from AutoSCORE review. | The service generates the PDF from the immutable snapshot and returns it as an attachment. |
| **Educator finalization** | The original packet remains unchanged. | The educator’s grade and feedback remain a separate, timestamped evaluation record. | A later grade does not overwrite student work or retroactively alter the frozen submission packet. |

## Packet content model

The packet should be readable as a professional evidence dossier rather than a raw event export. It should use simple typography, accessible headings, page numbers, and a clear separation between learner-authored reasoning and optional assistance.

| Packet section | Source of truth | Included | Explicitly excluded |
|---|---|---|---|
| **Cover and submission metadata** | Published assignment plus submitted session snapshot | Assignment title, course/module context where available, submitted timestamp, packet ID, integrity digest, and learner identifier following existing policy. | Session capability, access-token digest, internal database identifiers beyond packet/session reference, provider API keys. |
| **Assignment brief** | Public assignment projection | Public prompt, target knowledge components, and approved-source titles. | Answer Vault, reference solution, hidden prompt, scoring key, private instructor annotations. |
| **Learner reasoning sections** | Frozen `canvas_section_drafts` snapshot | Ordered section label, student-saved text, revision number, and attribution label. | Automatically completed or model-composed sections. |
| **Evidence references** | Frozen source-reference snapshot plus public grounding source projection | Source title, learner-selected quotation, and learner-supplied rationale. | Unselected source text and claims that a source supports an unstated conclusion. |
| **Assistance disclosure** | Frozen support-card and dialogue events | Offered/accepted/dismissed support, active section, and clear learner-edit attribution. | Full provider prompt, chain-of-thought, internal model logs, or an implication that an offered card is learner-written. |
| **Reasoning process summary** | Existing evidence dossier, adjusted to consume the snapshot | Trace counts, explicit hint use, integrity-boundary events, and evaluator-facing factual chronology. | A final grade, a claim that the learner achieved mastery, or fabricated time/engagement metrics. |
| **Educator assessment page** | Blank template fields plus packet metadata | Space for evaluator observations and reference to the separate finalization workflow. | Automatic grade or automated high-stakes assessment decision. |

## Architecture

### 1. Immutable structured snapshot

Add migration `006_evidence_packets.sql` with a `submission_evidence_packets` table. It will contain a packet UUID, session ID, assignment ID, packet-schema version, JSONB snapshot, SHA-256 content digest, status, creator timestamp, and optional PDF render metadata. The table has a unique session ID to enforce one canonical submission snapshot per session.

At submission, one server-side transaction will lock the active session, load its current canvas revisions and permitted assistance events, construct the snapshot from public assignment context, calculate the digest, append the submission event, and transition the session to `submitted`. A repeated submission request will return the existing packet identifier rather than creating a second snapshot. Post-submission canvas writes remain blocked by the existing lifecycle controls.

The packet service must query only public assignment data, learner canvas drafts, learner-selected source references, and allow-listed trace events. It must never query `assignment_answer_vault`, `reference_solution`, `vault_token`, hidden rubric content, model API configuration, or raw provider prompts.

### 2. PDF rendering service

Introduce `fiosra/mvp/evidence_dossier/pdf_packet_service.py` and a versioned Typst template at `fiosra/mvp/evidence_dossier/templates/student_evidence_packet.typ`. The Python service will serialize the already-sanitized snapshot into a temporary JSON file, invoke the pinned Typst compiler with a strict process timeout, and stream the compiled result back to the caller. It will delete temporary source and output files in all success and failure paths.

The production Docker image will install a pinned Typst release or validated Debian package during the runtime build. The exact version will be documented and covered by a container build smoke test. The service will not call a hosted LLM or external document API to generate the PDF.

A deterministic fallback will remain available if a render fails: the submission snapshot is still stored and the evaluator UI displays a clear **PDF temporarily unavailable; retry download** state. The service does not discard the packet, modify student work, or retry indefinitely. A request may safely retry compilation from the same immutable snapshot.

### 3. Authorized delivery endpoints

The recommended access model is deliberately split by audience.

| Endpoint | Audience | Required authorization | Response |
|---|---|---|---|
| `GET /evidence/packets/{packet_id}/student.pdf` | The submitting learner | The existing `X-Fiosra-Session-Token` capability and a packet/session match. | `application/pdf` attachment. |
| `GET /evidence/packets/{packet_id}/review.pdf` | The assigned educator/reviewer | Role-bound educator authentication and course/assignment authorization delivered by Issue #41. | `application/pdf` attachment. |
| `GET /evidence/packets/{packet_id}` | Learner or authorized evaluator | Same audience-specific authorization. | Packet metadata, digest, schema version, render availability, and download affordance. |

The current repository does not yet have institutional user authentication or educator role-based access control. Therefore, the `review.pdf` endpoint must not be released as a public UUID URL. Implementation will first add the learner-protected delivery route and packet rendering foundation. The educator download button will be enabled only in the Issue #41 implementation slice that establishes a real reviewer principal and course entitlement. Until then, the existing educator workspace can show packet availability and integrity metadata without exposing an unprotected document download.

### 4. UI placement

The student trace page will retain its current submit action. On a successful response, it will display an unobtrusive **Download my evidence packet (PDF)** secondary action. Download uses `fetch` with the session-capability header and a browser Blob URL, so the capability is not placed into an address bar or document link.

The educator review view will show the packet identifier, digest prefix, snapshot status, and—after role-bound educator authorization exists—a **Download submitted evidence packet** action in the evidence packet header. The existing canvas authorship record remains visible in the interactive review; the PDF makes the same distinction in a durable evaluation artifact.

## Implementation sequence

| Step | Deliverable | Required validation gate |
|---:|---|---|
| 1 | A typed, versioned submission-packet schema and migration with unique packet/session binding. | Migration applies cleanly to a fresh database and a pre-existing local database. Packet JSON schema forbids unknown fields and sensitive answer-vault names. |
| 2 | Server-side snapshot construction integrated with idempotent session submission. | Tests prove one packet per session, identical re-submission results, snapshot immutability, and no packet for a draft or unauthorized session. |
| 3 | Sanitized Typst data adapter and packet template. | Typst strict compilation succeeds for a multi-section, multi-source packet. PDF text extraction shows expected headings and learner text; visual review checks page flow and readable source references. |
| 4 | Learner-protected metadata and PDF download endpoint. | Tests reject missing, wrong, and cross-session capabilities. Browser test downloads a valid PDF after submission without placing a token in the URL. |
| 5 | Student trace download action and packet status display. | Browser flow verifies save → submit → PDF download. A failed render yields a retryable, non-destructive state. |
| 6 | Educator reviewer download action after Issue #41 delivers course-scoped role authorization. | Cross-course and non-educator authorization tests fail with `403`; assigned educator can view/download only their evaluation packet. |
| 7 | Developer guide, API reference, migration guide, deployment Typst dependency, and retention documentation. | Full test suite, frontend production build, Docker build, API contract checks, document compilation, PDF verifier, and representative visual review all pass. |

## Acceptance criteria

| Category | Acceptance criterion |
|---|---|
| **Submission integrity** | Submission produces exactly one immutable packet snapshot associated with the submitted session. Repeated requests are idempotent and return the same packet metadata. |
| **Student work fidelity** | The PDF contains every persisted canvas section in assignment order, with the exact submitted text, revision value, attached source references, and author label. |
| **Attribution** | The PDF visibly distinguishes direct learner revisions, optional support offered, learner-edited assistance, and dismissed support. Offered assistance is never represented as learner-authored prose. |
| **Answer isolation** | Automated tests and source review demonstrate that vault tokens, reference solutions, answer keys, rubric answers, raw LLM prompts, and provider configuration cannot enter the snapshot, Typst input, PDF, or response headers. |
| **Evidence fidelity** | A quoted source reference in the PDF is constrained to the assignment-approved public excerpt and retains the learner rationale without new claims. |
| **Evaluation usability** | The document has an assignment brief, clear section hierarchy, evidence citations, trace context, an integrity identifier, page numbers, and sufficient blank/structured space for human evaluator notes. |
| **Authorization** | Student download requires the correct session capability. Educator download requires course-scoped educator authorization; it is not published until Issue #41 supplies that control. |
| **Failure behavior** | A Typst compiler failure does not change the submission, erase the snapshot, or expose a partial document. The user receives a bounded retryable failure and reviewers can inspect packet availability. |
| **Deployment** | The Docker runtime includes a pinned Typst compiler version and health checks remain healthy. The implementation does not add a dependency on an external generation service. |
| **Verification** | Backend tests, Svelte production build, Docker build, a real locally generated PDF, deterministic PDF verification, and browser download tests pass. |

## Explicit exclusions

This plan does not provide PDF editing after submission, a model-written executive summary, autonomous essay weaving, automated grading, a public/shareable packet URL, digital signatures, long-term object-storage archival, or student-to-student sharing. Those require data retention, authorization, audit, and institutional policy decisions beyond this product slice.

## Approval request

Approve this plan to authorize the **first protected PDF delivery slice**: immutable snapshot creation on submission, a server-rendered Typst evidence packet, learner-capability-protected PDF download from the trace page, comprehensive testing, and documentation. Educator document download will remain disabled until the preceding Issue #41 authorization foundation is implemented and validated.

## References

[1]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/evidence_dossier/synthesizer.py "Existing evidence dossier synthesis service"
[2]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/events_router.py "Protected session submission endpoint"
[3]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/learning_canvas_service.py "Student-owned canvas persistence and source validation"
[4]: https://github.com/darkaengl/fiosra/blob/main/fiosra/mvp/migrations/005_learning_canvas.sql "Learning canvas session capability migration"
[5]: https://github.com/darkaengl/fiosra/blob/main/docs/developer-guide/06-learning-canvas-and-assistance.md "Writer-first learning canvas developer guide"
