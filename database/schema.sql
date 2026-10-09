CREATE TABLE IF NOT EXISTS generation_jobs (
    job_id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    model TEXT NOT NULL,
    model_file TEXT NOT NULL,
    ratio TEXT NOT NULL CHECK (ratio IN ('1:1', '4:3', '16:9', '9:16')),
    count INTEGER NOT NULL CHECK (count BETWEEN 1 AND 4),
    cfg_scale REAL NOT NULL CHECK (cfg_scale BETWEEN 1 AND 20),
    base_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    message TEXT NOT NULL,
    images TEXT NOT NULL DEFAULT '[]',
    model_path TEXT,
    engine TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_generation_jobs_status_created
    ON generation_jobs (status, created_at);