-- TrialScope database initialization
-- Runs once when the postgres container first starts.
-- Creates the raw ingestion schema and the warehouse schema.

-- ── Schemas ──────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS raw;        -- landing zone for extracted data
CREATE SCHEMA IF NOT EXISTS staging;   -- dbt staging models
CREATE SCHEMA IF NOT EXISTS marts;     -- dbt mart models (analytics-ready)
CREATE SCHEMA IF NOT EXISTS ml;        -- ML feature store and predictions

-- ── Raw tables ───────────────────────────────────────────────────
-- Stores one row per trial as raw JSONB — no transformation yet.
-- dbt reads from this table in staging models.
CREATE TABLE IF NOT EXISTS raw.clinical_trials (
    nct_id          TEXT PRIMARY KEY,
    condition_query TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_json        JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_trials_fetched
    ON raw.clinical_trials (fetched_at DESC);

-- Stores raw FAERS adverse event batches
CREATE TABLE IF NOT EXISTS raw.faers_events (
    id              BIGSERIAL PRIMARY KEY,
    drug_query      TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    batch_json      JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_faers_drug
    ON raw.faers_events (drug_query);

-- Stores raw PubMed abstract metadata
CREATE TABLE IF NOT EXISTS raw.pubmed_abstracts (
    pmid            TEXT PRIMARY KEY,
    condition_query TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_json        JSONB NOT NULL
);

-- ── ML schema ────────────────────────────────────────────────────
-- Feature vectors computed from warehouse data (populated by research notebooks)
CREATE TABLE IF NOT EXISTS ml.trial_features (
    nct_id                  TEXT PRIMARY KEY,
    computed_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Structured features
    phase_numeric           SMALLINT,   -- 1, 2, 3, 4
    enrollment_count        INTEGER,
    sponsor_class           TEXT,       -- INDUSTRY, NIH, OTHER
    study_duration_days     INTEGER,
    num_conditions          SMALLINT,
    num_interventions       SMALLINT,
    num_locations           SMALLINT,
    num_countries           SMALLINT,
    has_results             BOOLEAN,

    -- NLP-derived features (populated after NLP pipeline runs)
    eligibility_word_count  INTEGER,
    num_inclusion_criteria  SMALLINT,
    num_exclusion_criteria  SMALLINT,
    biomarker_count         SMALLINT,
    eligibility_embedding   FLOAT8[],  -- BioBERT embedding vector

    -- Target variable
    outcome_label           TEXT        -- 'completed', 'terminated', 'withdrawn', 'ongoing'
);

-- Stores model predictions with explanations
CREATE TABLE IF NOT EXISTS ml.trial_predictions (
    nct_id              TEXT PRIMARY KEY,
    predicted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mlflow_run_id       TEXT,
    completion_prob     FLOAT4,         -- probability of completing
    termination_prob    FLOAT4,
    top_features        JSONB,          -- SHAP values for top 10 features
    model_version       TEXT
);

-- ── Utility function ─────────────────────────────────────────────
-- Called by the loader script to upsert raw trial JSON
CREATE OR REPLACE FUNCTION raw.upsert_trial(
    p_nct_id          TEXT,
    p_condition_query TEXT,
    p_raw_json        JSONB
) RETURNS VOID AS $$
BEGIN
    INSERT INTO raw.clinical_trials (nct_id, condition_query, raw_json)
    VALUES (p_nct_id, p_condition_query, p_raw_json)
    ON CONFLICT (nct_id) DO UPDATE
        SET raw_json        = EXCLUDED.raw_json,
            condition_query = EXCLUDED.condition_query,
            updated_at      = NOW();
END;
$$ LANGUAGE plpgsql;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO trialscope;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ml TO trialscope;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw TO trialscope;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ml TO trialscope;
