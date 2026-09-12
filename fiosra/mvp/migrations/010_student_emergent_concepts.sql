-- ====================================================================
-- Fiosra Migration 010: Student Emergent Concepts ("green nodes")
-- ====================================================================
-- Concepts a student mentions in their own work that are NOT part of the
-- teacher-governed course concept graph (fiosra.mvp.concepts, Neo4j). Kept
-- entirely separate from that canonical graph - these are student-scoped
-- and best-effort LLM-extracted, never written into the shared course
-- topology every student and the teacher see. Surfaced only as extra
-- nodes/edges in that one student's mastery overlay (concept_mastery
-- service), colored differently (green) from tracked course concepts.

CREATE TABLE IF NOT EXISTS student_emergent_concepts (
    emergent_id        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id         VARCHAR(64)  NOT NULL,
    course_id          UUID         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    session_id         UUID         REFERENCES student_sessions(session_id) ON DELETE SET NULL,
    label              VARCHAR(200) NOT NULL,
    context_snippet    TEXT,
    related_concept_id VARCHAR(96),  -- Neo4j Concept.concept_id this was raised alongside (cross-db; not FK'd)
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, course_id, label)
);

CREATE INDEX IF NOT EXISTS idx_student_emergent_concepts_course  ON student_emergent_concepts (course_id);
CREATE INDEX IF NOT EXISTS idx_student_emergent_concepts_student ON student_emergent_concepts (student_id, course_id);
