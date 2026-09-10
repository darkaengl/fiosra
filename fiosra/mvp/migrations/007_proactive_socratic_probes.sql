-- ====================================================================
-- Fiosra MVP Proactive Socratic Probe Migration
-- ====================================================================
-- Questions are bound to an already-saved learner block and revision. They are
-- evidence for human evaluation, never an automated grade or answer source.

CREATE TABLE IF NOT EXISTS socratic_probes (
    probe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES student_sessions(session_id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES learning_documents(document_id) ON DELETE CASCADE,
    block_id UUID NOT NULL REFERENCES learning_document_blocks(block_id) ON DELETE CASCADE,
    source_block_revision INTEGER NOT NULL,
    claim_fingerprint CHAR(64) NOT NULL,
    focus_type VARCHAR(40) NOT NULL,
    question TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'offered',
    generation_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    offered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deferred_until TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    superseded_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_socratic_probe_block_revision UNIQUE (block_id, source_block_revision),
    CONSTRAINT chk_socratic_probe_focus CHECK (focus_type IN (
        'direct_observation', 'warrant', 'causal_bridge', 'alternative_explanation', 'qualification'
    )),
    CONSTRAINT chk_socratic_probe_status CHECK (status IN (
        'offered', 'deferred', 'responded', 'dismissed', 'superseded', 'expired'
    )),
    CONSTRAINT chk_socratic_probe_question_length CHECK (char_length(question) BETWEEN 1 AND 260),
    CONSTRAINT chk_socratic_probe_revision_positive CHECK (source_block_revision >= 1)
);

-- A paragraph can have one unresolved question at a time. The service marks a
-- prior question superseded before a material revision becomes eligible again.
CREATE UNIQUE INDEX IF NOT EXISTS uq_socratic_probe_pending_per_block
    ON socratic_probes (block_id)
    WHERE status IN ('offered', 'deferred');

CREATE INDEX IF NOT EXISTS idx_socratic_probes_session_offered
    ON socratic_probes (session_id, offered_at DESC);

CREATE INDEX IF NOT EXISTS idx_socratic_probes_document_block
    ON socratic_probes (document_id, block_id, source_block_revision DESC);

CREATE TABLE IF NOT EXISTS socratic_probe_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    probe_id UUID NOT NULL UNIQUE REFERENCES socratic_probes(probe_id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    response_revision INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_socratic_probe_response_length CHECK (char_length(response_text) BETWEEN 10 AND 6000),
    CONSTRAINT chk_socratic_probe_response_revision_positive CHECK (response_revision >= 1)
);

-- Raw learner prose remains in protected document/probe tables. Generic
-- session_events contain only lifecycle IDs, state transitions, and prompt-free
-- provider metadata so telemetry never becomes a duplicate essay transcript.
