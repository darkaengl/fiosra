"""Contracts for the per-student concept mastery overlay on the course concept graph.

See docs/knowledge-graph-mastery-plan.md for the design this implements. Mastery is a
deterministic, event-derived cache over the course-scoped Neo4j Concept graph
(fiosra.mvp.concepts) — never a second source of truth, never LLM-inferred.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CriterionOutcome = Literal["met", "partially_met", "not_met"]
# "emergent" is never assigned by the deterministic scorer - it marks a
# student-introduced concept extracted (best-effort, LLM-assisted) from their own
# work, not one of the teacher's tracked course concepts. See EmergentConceptNode.
MasteryState = Literal["unassessed", "weak", "developing", "strong", "emergent"]


class CriterionGradeInput(BaseModel):
    """One rubric criterion's educator-assigned outcome for a finalized session."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(min_length=1, max_length=96)
    outcome: CriterionOutcome


class ConceptMasteryNode(BaseModel):
    """A course concept-graph node annotated with one student's mastery state."""

    concept_id: str
    label: str
    definition: str
    concept_type: str
    level: str
    state: MasteryState = "unassessed"
    score: float = 0.0
    evidence_count: int = 0
    last_evidence_at: str | None = None


class EmergentConceptNode(BaseModel):
    """A concept the student mentioned that is not part of the teacher's course graph.

    Extracted best-effort by an LLM pass over the student's own submitted text at
    grading time (see ConceptMasteryService._extract_emergent_concepts). Never
    written into the shared Neo4j course graph - scoped to one student, stored in
    Postgres, and surfaced only in that student's own overlay.
    """

    concept_id: str  # synthetic id, e.g. "EMERGENT_<uuid>" - not a real Concept.concept_id
    label: str
    definition: str = ""
    concept_type: str = "emergent"
    level: str = "emergent"
    state: MasteryState = "emergent"
    related_concept_id: str | None = None


class StudentConceptMasteryResponse(BaseModel):
    course_id: str
    student_id: str
    nodes: list[ConceptMasteryNode] = Field(default_factory=list)
    emergent_nodes: list[EmergentConceptNode] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class ConceptMasteryDistribution(BaseModel):
    """Cohort-wide state counts for one concept, for the educator heatmap view."""

    concept_id: str
    label: str
    definition: str
    concept_type: str
    level: str
    strong: int = 0
    developing: int = 0
    weak: int = 0
    unassessed: int = 0
    assessed_student_count: int = 0
    cohort_size: int = 0


class CohortConceptMasteryResponse(BaseModel):
    course_id: str
    cohort_size: int = 0
    nodes: list[ConceptMasteryDistribution] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class MasteryRebuildResponse(BaseModel):
    course_id: str
    sessions_replayed: int
    rows_written: int
