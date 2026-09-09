-- ====================================================================
-- Fiosra MVP Migration 004: Module Resource Ingestion & Metadata
-- ====================================================================

ALTER TABLE syllabus_chunks 
ADD COLUMN IF NOT EXISTS resource_type VARCHAR(32) DEFAULT 'document',
ADD COLUMN IF NOT EXISTS source_url TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_syllabus_chunks_course_module 
ON syllabus_chunks (course_id, module_id);
