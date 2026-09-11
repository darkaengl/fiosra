-- ====================================================================
-- Fiosra Migration 008: Student Course Enrollments
-- ====================================================================
-- Adds explicit enrollment tracking so students can browse available
-- courses and self-enroll from the Student Portal.

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id     UUID NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    student_id    VARCHAR(64) NOT NULL,
    enrolled_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (course_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments (student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course  ON enrollments (course_id);
