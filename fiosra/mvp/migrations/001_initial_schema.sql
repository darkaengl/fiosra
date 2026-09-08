-- ====================================================================
-- Fiosra MVP Initial Schema Migration
-- ====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Knowledge Components (Curriculum Tree)
CREATE TABLE IF NOT EXISTS knowledge_components (
    kc_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(64) NOT NULL,
    description TEXT,
    parent_id VARCHAR(64) REFERENCES knowledge_components(kc_id)
);

-- 3. Prerequisite Directed Edges (DAG)
CREATE TABLE IF NOT EXISTS kc_prerequisites (
    kc_id VARCHAR(64) REFERENCES knowledge_components(kc_id),
    prerequisite_id VARCHAR(64) REFERENCES knowledge_components(kc_id),
    PRIMARY KEY (kc_id, prerequisite_id)
);

-- 4. Misconception Taxonomy with Vector Search
CREATE TABLE IF NOT EXISTS misconceptions (
    misconception_id VARCHAR(64) PRIMARY KEY,
    kc_id VARCHAR(64) REFERENCES knowledge_components(kc_id),
    domain VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    flawed_rule TEXT NOT NULL,
    remediation_hint TEXT NOT NULL,
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_misconceptions_vector ON misconceptions 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- 5. Assignments & Specifications
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    created_by VARCHAR(64) NOT NULL,
    spec JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Student Sessions
CREATE TABLE IF NOT EXISTS student_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(64) NOT NULL,
    assignment_id UUID REFERENCES assignments(assignment_id),
    current_question_id VARCHAR(32) NOT NULL,
    status VARCHAR(32) DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 7. Append-Only JSON Event Store (Flight Recorder)
CREATE TABLE IF NOT EXISTS session_events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES student_sessions(session_id),
    student_id VARCHAR(64) NOT NULL,
    assignment_id UUID,
    question_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_events_payload ON session_events USING gin (payload);
CREATE INDEX IF NOT EXISTS idx_session_events_chronological ON session_events (session_id, created_at ASC);
