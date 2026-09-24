-- ====================================================================
-- Fiosra MVP Assignment Interventions Migration (013_interventions.sql)
-- ====================================================================
-- Allows educators to dispatch AI-generated or educator-refined learning
-- activities/nudges to students based on gaps detected in assignments
-- (both in-progress drafts and submitted work).

CREATE TABLE IF NOT EXISTS assignment_interventions (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES student_sessions(session_id) ON DELETE CASCADE,
    student_id VARCHAR(64) NOT NULL,
    teacher_id VARCHAR(64) NOT NULL DEFAULT 'educator',
    document_id UUID REFERENCES learning_documents(document_id) ON DELETE SET NULL,
    block_id UUID REFERENCES learning_document_blocks(block_id) ON DELETE SET NULL,
    concept_id VARCHAR(96),
    concept_label VARCHAR(160),
    misconception_id VARCHAR(96),
    evidence_quote TEXT NOT NULL,
    activity_type VARCHAR(40) NOT NULL DEFAULT 'socratic_nudge',
    activity_prompt TEXT NOT NULL,
    activity_guidance TEXT,
    student_response TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'dispatched',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_intervention_status CHECK (status IN (
        'draft', 'dispatched', 'viewed', 'responded', 'acknowledged'
    ))
);

CREATE INDEX IF NOT EXISTS idx_interventions_session 
    ON assignment_interventions (session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_interventions_student 
    ON assignment_interventions (student_id, status);

CREATE INDEX IF NOT EXISTS idx_interventions_block 
    ON assignment_interventions (block_id)
    WHERE block_id IS NOT NULL;
