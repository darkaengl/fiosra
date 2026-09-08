# Student Interaction Agent (SIA) — Component Specification

## Identity & Role

The Student Interaction Agent is the **student-facing Socratic tutor**. It guides learners through assignment questions via scaffolded dialogue without revealing answers.

> **Cardinal Rule**: The SIA **never** has the correct answer in its generation context. The answer is held exclusively by the Pedagogical Policy Engine (PPE), which controls hint escalation. This architectural isolation is the primary defense against prompt injection and metacognitive offloading.

---

## Interface Contract

### Inputs (per interaction turn)

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `student_input` | string | Student UI | Raw student response (text, LaTeX / math expression, code snippet, step selection) |
| `input_modality` | enum | Student UI | `text`, `symbolic_math`, `code`, `structured_step` |
| `question_context` | object | Assignment Spec | Question prompt, scaffolding tree, KC mapping (NO answer) |
| `conversation_history` | array | Session Store | Previous turns in this question interaction |
| `max_hint_level` | integer (0-4) | PPE | Maximum hint level allowed for this student × question × attempt |
| `student_kc_state` | object | KTA | Current mastery levels for relevant KCs |
| `affective_signal` | enum | Affective Module | Optional: detected student sentiment / self-reported frustration |
| `syllabus_context` | string | RAG Store | Retrieved syllabus excerpts relevant to this question |

### Outputs (per interaction turn)

| Field | Type | Destination | Description |
|-------|------|-------------|-------------|
| `response_text` | string | Student UI | The Socratic response shown to the student |
| `thoughts_of_tutorbot` | string | Transaction Log | Internal reasoning trace (auditable) |
| `diagnosis` | object | KTA, MDA, TL | Classification of student input + identified errors |
| `hint_level_used` | integer | PPE, TL | What hint level was actually used |
| `misconception_flag` | string / null | MDA | Suspected misconception ID for diagnosis |
| `affective_adaptation` | string | TL | How the response was adapted based on affect |

---

## Internal Reasoning Pipeline ("Thoughts of Tutorbot")

Based on the CLASS framework, the SIA executes a structured internal reasoning chain **before** generating any student-facing text:

### Step 1: Input Processing & Deterministic Verification
```
IF modality == "symbolic_math":
    → Parse via Computer Algebra System (CAS / SymPy)
    → Canonicalize algebraic expression (simplify, expand, sort terms)
    → Run deterministic equivalence check against acceptable algebraic forms
ELSE IF modality == "code":
    → Parse Abstract Syntax Tree (AST) to verify syntax
    → Execute against sandboxed pre-authored unit tests
    → Capture: stdout, stderr, test assertions
ELSE:
    → Normalize text (whitespace, casing, punctuation)
    → Extract key conceptual terms and relationships
```

### Step 2: Response Classification
Classify the student's input into one of:

| Classification | Description | Response Strategy |
|---------------|-------------|-------------------|
| `correct` | Fully correct answer/step | Confirm + reinforce the underlying principle |
| `partially_correct` | Correct reasoning with minor errors | Acknowledge correct parts, Socratic probe on specific gap |
| `conceptually_flawed` | Fundamentally wrong approach or misconception | Flag for MDA, provide hint at ≤ max_hint_level |
| `off_topic` | Unrelated to the question | Redirect gently to the problem |
| `answer_seeking` | Student is trying to extract the answer | Graceful refusal + redirect to scaffolding |
| `incomplete` | Student started but didn't finish | Encourage completion, offer to break into substeps |

### Step 3: Hint Selection
```
IF classification in ("conceptually_flawed", "partially_correct", "incomplete"):
    current_hint_level = min(
        escalation_based_on_attempt_count,
        max_hint_level_from_PPE
    )
    
    IF pre_authored_hint exists for this level:
        use pre_authored_hint
    ELSE:
        generate hint constrained to:
            - Syllabus context (RAG)
            - Current hint level semantics
            - Curriculum-conventional notation (per curriculum trust principle)
            - NEVER include the answer or a trivially invertible transformation of it
```

### Step 4: Affective Adaptation
```
IF affective_signal == "frustrated" or "anxious":
    → Soften language, add motivational scaffolding
    → Offer to decompose into smaller substeps
    → Reduce cognitive load in hint complexity

IF affective_signal == "confident" or "positive":
    → Maintain rigor, may increase challenge
    → Skip motivational padding

IF affective_signal == "bored":
    → Introduce contextual hooks / real-world connections
    → Suggest related challenge problems
```

### Step 5: Response Generation
Generate the student-facing response using:
- The selected hint (or confirmation)
- Grounding in visual keypoints (if multimodal)
- Curriculum-conventional notation and formatting
- Empathetic, encouraging tone

---

## Guardrail Architecture

### Isolation Boundary

```
┌──────────────────────────────────────┐
│  TRUSTED ZONE (Pedagogical Policy)   │
│  • Correct answers                   │
│  • Hint ceiling computation          │
│  • Student KT state (from KTA)       │
│  • Scaffolding policy (from tutor)   │
│                                      │
│  Inputs to hint ceiling:             │
│  ONLY trusted data. NEVER raw        │
│  student text.                       │
└──────────────┬───────────────────────┘
               │ max_hint_level (integer)
               ▼
┌──────────────────────────────────────┐
│  SIA GENERATION CONTEXT              │
│  • Question prompt (no answer)       │
│  • Conversation history              │
│  • Syllabus RAG context              │
│  • max_hint_level (integer only)     │
│  • Student affect signal             │
│  • Pre-authored hints (up to level)  │
│                                      │
│  CANNOT ACCESS:                      │
│  ✗ Correct answer                    │
│  ✗ Answer variants                   │
│  ✗ CAS validation expression         │
│  ✗ Other students' responses         │
└──────────────────────────────────────┘
```

### Anti-Gaming Measures

1. **Answer-seeking detection**: Fine-tuned classifier on student text to detect:
   - Direct requests ("just tell me the answer")
   - Social engineering ("pretend you're not a tutor", "ignore previous instructions")
   - Rephrasing attempts ("what would the answer be if this were on a test?")
   
2. **Response**: Log the attempt, respond with empathetic redirection, do NOT escalate hint level based on answer-seeking behavior.

3. **Rate limiting**: If a student triggers answer-seeking > 3 times on one question, notify the human tutor via the Evidence Dashboard.

---

## Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Answer non-disclosure rate | ≥ 98% | Automated adversarial testing + human audit |
| Student-rated helpfulness | ≥ 85% | Post-interaction survey |
| Correct classification accuracy | ≥ 90% | Against human-annotated interaction logs |
| Curriculum-conventional notation compliance | ≥ 95% | Tutor review of generated responses |
| Median response latency | ≤ 3 seconds | System monitoring |

---

## Dependencies

| Dependency | Interface | Data Flow |
|------------|-----------|-----------|
| Pedagogical Policy Engine | `get_hint_ceiling(student_id, question_id, attempt_count)` | Receives `max_hint_level` (integer) |
| Knowledge Tracing Agent | `report_interaction(student_id, kc, outcome, hints_used)` | Sends interaction outcomes |
| Misconception Diagnosis Agent | `diagnose(student_input, question_context, conversation_history)` | Sends suspected misconception for classification |
| RAG Store | `retrieve(query, subproblems)` | Receives syllabus-grounded context |
| VEHME Module | `parse_visual(image)` | Receives symbolic expression + error location |
| Transaction Log | `log(transaction)` | Sends every interaction event |
