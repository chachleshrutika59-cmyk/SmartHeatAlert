BEGIN;

ALTER TABLE alerts
    ADD COLUMN IF NOT EXISTS risk_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS location VARCHAR(200),
    ADD COLUMN IF NOT EXISTS condition_key VARCHAR(120);

CREATE INDEX IF NOT EXISTS ix_alerts_user_created_at
    ON alerts (user_id, created_at DESC);

COMMIT;
