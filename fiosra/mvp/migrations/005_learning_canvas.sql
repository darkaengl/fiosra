-- ====================================================================
-- Fiosra MVP Learning Canvas and Session Capability Migration
-- ====================================================================

-- A per-session capability token is stored only as a SHA-256 digest.
-- It protects the student-owned canvas APIs in deployments that have not yet
-- configured institution-level authentication.
ALTER TABLE student_sessions
    ADD COLUMN IF NOT EXISTS access_token_hash VARCHAR(64);

CREATE TABLE IF NOT EXISTS canvas_section_drafts (
    session_id UUID NOT NULL REFERENCES student_sessions(session_id) ON DELETE CASCADE,
    section_id VARCHAR(64) NOT NULL,
    text TEXT NOT NULL DEFAULT '',
    source_references JSONB NOT NULL DEFAULT '[]'::jsonb,
    author_type VARCHAR(32),
    revision INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (session_id, section_id),
    CONSTRAINT chk_canvas_draft_revision_nonnegative CHECK (revision >= 0)
);

CREATE TABLE IF NOT EXISTS canvas_suggestions (
    suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES student_sessions(session_id) ON DELETE CASCADE,
    section_id VARCHAR(64) NOT NULL,
    kind VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    base_revision INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'offered',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    acted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT chk_canvas_suggestion_status CHECK (status IN ('offered', 'accepted', 'dismissed')),
    CONSTRAINT chk_canvas_suggestion_kind CHECK (kind IN ('writing_frame', 'section_question', 'source_reminder')),
    CONSTRAINT chk_canvas_suggestion_revision_nonnegative CHECK (base_revision >= 0)
);

CREATE INDEX IF NOT EXISTS idx_canvas_suggestions_session ON canvas_suggestions (session_id, created_at ASC);
