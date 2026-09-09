-- ====================================================================
-- Fiosra MVP Migration 002: Syllabus Corpus Chunks (pgvector)
-- ====================================================================

CREATE TABLE IF NOT EXISTS syllabus_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    module_id UUID REFERENCES modules(module_id) ON DELETE SET NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    kc_id VARCHAR(64),
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_syllabus_chunks_vector ON syllabus_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_syllabus_chunks_course ON syllabus_chunks (course_id);
