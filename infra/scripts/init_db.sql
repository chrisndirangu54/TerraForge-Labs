CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS instrument_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL,
    project_id UUID,
    source VARCHAR(100) NOT NULL DEFAULT 'unknown',
    parser_version VARCHAR(100) NOT NULL DEFAULT 'unknown@0.0.0',
    crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:4326',
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
CREATE INDEX IF NOT EXISTS idx_instrument_readings_project ON instrument_readings(project_id);
CREATE INDEX IF NOT EXISTS idx_instrument_readings_source ON instrument_readings(source);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL DEFAULT 'generic',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payload JSONB,
    result JSONB,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    project_id UUID,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_events_job_id ON job_events(job_id);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'geologist',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_memberships (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'geologist',
    PRIMARY KEY (project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects(slug);

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    artifact_type VARCHAR(100) NOT NULL,
    storage_key TEXT NOT NULL,
    content_type VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream',
    size_bytes BIGINT NOT NULL DEFAULT 0,
    checksum VARCHAR(64),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_storage_key ON artifacts(storage_key);

CREATE TABLE IF NOT EXISTS stac_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection VARCHAR(100) NOT NULL DEFAULT 'terraforge-rasters',
    item_id VARCHAR(100) NOT NULL UNIQUE,
    bbox DOUBLE PRECISION[4],
    geometry JSONB,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    assets JSONB NOT NULL DEFAULT '{}'::jsonb,
    artifact_id UUID REFERENCES artifacts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stac_items_collection ON stac_items(collection);
CREATE INDEX IF NOT EXISTS idx_stac_items_item_id ON stac_items(item_id);
