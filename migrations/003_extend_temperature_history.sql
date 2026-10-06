BEGIN;

ALTER TABLE temperature_records
    ADD COLUMN IF NOT EXISTS risk_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS risk_level VARCHAR(50);

CREATE INDEX IF NOT EXISTS ix_temperature_records_user_recorded_at
    ON temperature_records (user_id, recorded_at DESC);

COMMIT;
