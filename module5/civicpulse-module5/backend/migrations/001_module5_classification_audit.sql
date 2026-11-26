-- Module 5: audit trail for officer corrections of AI classifications.
-- Idempotent. The only schema change Module 5 makes; Module 1 tables are untouched.
-- If the project uses Alembic, wrap this in a revision (op.execute) instead.

CREATE TABLE IF NOT EXISTS classification_corrections (
    id               UUID PRIMARY KEY,
    complaint_id     UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    officer_id       UUID REFERENCES users(id),
    old_issue_type   TEXT,
    new_issue_type   TEXT NOT NULL,
    reason           TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_classification_corrections_complaint
    ON classification_corrections (complaint_id, created_at);

-- Indexes that keep the officer table and map fast (safe to skip if Module 1 already has them).
CREATE INDEX IF NOT EXISTS idx_complaints_priority  ON complaints (priority_band, priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_status    ON complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_created   ON complaints (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_location  ON complaints USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_status_history_complaint ON status_history (complaint_id, created_at);
CREATE INDEX IF NOT EXISTS idx_reports_complaint    ON reports (complaint_id, created_at);
