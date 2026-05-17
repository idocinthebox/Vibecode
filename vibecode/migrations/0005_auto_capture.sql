ALTER TABLE success_patterns ADD COLUMN confidence REAL NOT NULL DEFAULT 1.0;
ALTER TABLE success_patterns ADD COLUMN occurrence_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE success_patterns ADD COLUMN last_seen_at TEXT;
ALTER TABLE success_patterns ADD COLUMN agent_source TEXT;
ALTER TABLE success_patterns ADD COLUMN review_state TEXT NOT NULL DEFAULT 'confirmed';

ALTER TABLE failure_patterns ADD COLUMN confidence REAL NOT NULL DEFAULT 1.0;
ALTER TABLE failure_patterns ADD COLUMN occurrence_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE failure_patterns ADD COLUMN last_seen_at TEXT;
ALTER TABLE failure_patterns ADD COLUMN agent_source TEXT;
ALTER TABLE failure_patterns ADD COLUMN review_state TEXT NOT NULL DEFAULT 'confirmed';

CREATE INDEX IF NOT EXISTS idx_success_review ON success_patterns(review_state);
CREATE INDEX IF NOT EXISTS idx_failure_review ON failure_patterns(review_state);
CREATE INDEX IF NOT EXISTS idx_failure_confidence ON failure_patterns(confidence DESC, last_seen_at DESC);
