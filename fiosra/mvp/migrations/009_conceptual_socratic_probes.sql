-- Records the approved curriculum concept that a voluntary Socratic question explores.
-- A match is a retrieval aid, never a judgement of learner correctness or mastery.
ALTER TABLE socratic_probes
    ADD COLUMN IF NOT EXISTS concept_id VARCHAR(96),
    ADD COLUMN IF NOT EXISTS concept_label VARCHAR(160);

CREATE INDEX IF NOT EXISTS idx_socratic_probes_concept
    ON socratic_probes (concept_id);
