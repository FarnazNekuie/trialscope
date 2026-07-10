{{ config(materialized='table', indexes=[{'columns': ['nct_id'], 'unique': True}]) }}

WITH trials AS (SELECT * FROM {{ ref('stg_trials') }}),
predictions AS (SELECT * FROM {{ source('ml', 'trial_predictions') }}),
location_counts AS (
    SELECT nct_id,
        jsonb_array_length(COALESCE(locations_json, '[]'::jsonb)) AS num_locations,
        COUNT(DISTINCT loc->>'country') AS num_countries
    FROM trials, jsonb_array_elements(COALESCE(locations_json, '[]'::jsonb)) AS loc
    GROUP BY nct_id, locations_json
),
intervention_counts AS (
    SELECT nct_id, jsonb_array_length(interventions_json) AS num_interventions
    FROM trials WHERE interventions_json IS NOT NULL
)
SELECT
    t.nct_id, t.brief_title, t.official_title, t.acronym,
    t.overall_status, t.outcome_label, t.why_stopped,
    t.start_date, t.primary_completion_date, t.completion_date,
    t.first_submit_date, t.has_results, t.study_duration_days,
    t.study_type, t.phase_raw, t.phase_numeric,
    t.enrollment_count, t.enrollment_type,
    t.lead_sponsor_name, t.lead_sponsor_class,
    t.healthy_volunteers, t.sex, t.minimum_age, t.maximum_age,
    t.eligibility_criteria_text,
    jsonb_array_length(COALESCE(t.conditions_json, '[]'::jsonb)) AS num_conditions,
    COALESCE(ic.num_interventions, 0) AS num_interventions,
    COALESCE(lc.num_locations, 0) AS num_locations,
    COALESCE(lc.num_countries, 0) AS num_countries,
    p.completion_prob, p.termination_prob,
    p.top_features AS shap_features, p.model_version, p.predicted_at,
    t.fetched_at, t.updated_at
FROM trials t
LEFT JOIN location_counts lc ON lc.nct_id = t.nct_id
LEFT JOIN intervention_counts ic ON ic.nct_id = t.nct_id
LEFT JOIN predictions p ON p.nct_id = t.nct_id
