-- ====================================================================
-- Fiosra MVP Long-Form Learning Document Migration
-- ====================================================================
-- One document is bound to one protected learner session. Blocks are stored
-- independently so a long essay can be synchronized incrementally rather than
-- submitted as a single fixed-size canvas field.

CREATE TABLE IF NOT EXISTS learning_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES student_sessions(session_id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES assignments(assignment_id) ON DELETE RESTRICT,
    title VARCHAR(240) NOT NULL DEFAULT 'Untitled reasoning document',
    schema_version INTEGER NOT NULL DEFAULT 1,
    document_revision INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_learning_document_schema_version CHECK (schema_version >= 1),
    CONSTRAINT chk_learning_document_revision_nonnegative CHECK (document_revision >= 0)
);

CREATE TABLE IF NOT EXISTS learning_document_blocks (
    block_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES learning_documents(document_id) ON DELETE CASCADE,
    section_id VARCHAR(64),
    position INTEGER NOT NULL,
    block_type VARCHAR(32) NOT NULL,
    content JSONB NOT NULL,
    plaintext TEXT NOT NULL DEFAULT '',
    author_type VARCHAR(40) NOT NULL DEFAULT 'student',
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_learning_document_block_position UNIQUE (document_id, position),
    CONSTRAINT chk_learning_document_block_type CHECK (
        block_type IN ('heading', 'paragraph', 'blockquote', 'bullet_list', 'ordered_list')
    ),
    CONSTRAINT chk_learning_document_block_author_type CHECK (
        author_type IN ('student', 'student_edited_assistance')
    ),
    CONSTRAINT chk_learning_document_block_revision_positive CHECK (revision >= 1)
);

CREATE INDEX IF NOT EXISTS idx_learning_document_blocks_document_position
    ON learning_document_blocks (document_id, position ASC);

-- Legacy short-form drafts remain immutable source history. When a document is
-- first requested for a session, the application imports them into heading and
-- paragraph blocks; this migration does not alter or delete canvas tables.
