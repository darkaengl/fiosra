-- ====================================================================
-- Fiosra Migration 009: Per-Student Concept Mastery Overlay
-- ====================================================================
-- Materialized, fully-recomputable overlay on top of the course-scoped
-- Neo4j Concept graph (fiosra.mvp.concepts). Topology (nodes/edges) lives
-- in Neo4j; this table holds only the deterministic, event-derived
-- mastery state per (student, course, concept). It is a cache, not a
-- second source of truth: it can be rebuilt at any time by replaying
-- grade_finalised_by_educator events (see concept_mastery/service.py).

CREATE TABLE IF NOT EXISTS concept_mastery (
    student_id       VARCHAR(64)  NOT NULL,
    course_id        UUID         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    concept_id       VARCHAR(96)  NOT NULL,  -- Neo4j Concept.concept_id (cross-db; not FK'd)
    state            VARCHAR(16)  NOT NULL DEFAULT 'unassessed',  -- unassessed | weak | developing | strong
    score            NUMERIC(4,3) NOT NULL DEFAULT 0,             -- 0.000-1.000 running weighted average
    evidence_count   INT          NOT NULL DEFAULT 0,
    last_evidence_at TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (student_id, course_id, concept_id)
);

CREATE INDEX IF NOT EXISTS idx_concept_mastery_course  ON concept_mastery (course_id);
CREATE INDEX IF NOT EXISTS idx_concept_mastery_student ON concept_mastery (student_id, course_id);
