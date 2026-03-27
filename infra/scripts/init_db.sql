CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS instrument_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL,
    instrument_type VARCHAR(50) NOT NULL,
    sample_id VARCHAR(100),
    geom GEOMETRY(Point, 4326),
    data JSONB NOT NULL,
    flagged BOOLEAN DEFAULT FALSE,
    flag_reasons TEXT[],
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instrument_readings_geom ON instrument_readings USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_instrument_readings_type ON instrument_readings(instrument_type);
CREATE INDEX IF NOT EXISTS idx_instrument_readings_upload ON instrument_readings(upload_id);
