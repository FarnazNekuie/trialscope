{{ config(materialized='incremental', unique_key='nct_id', on_schema_change='append_new_columns') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'clinical_trials') }}
    {% if is_incremental() %}
        WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

extracted AS (
    SELECT
        nct_id, fetched_at, updated_at, condition_query,

        raw_json->'protocolSection'->'identificationModule'->>'briefTitle' AS brief_title,
        raw_json->'protocolSection'->'identificationModule'->>'officialTitle' AS official_title,
        raw_json->'protocolSection'->'identificationModule'->>'acronym' AS acronym,

        raw_json->'protocolSection'->'statusModule'->>'overallStatus' AS overall_status,
        (NULLIF(regexp_replace(raw_json->'protocolSection'->'statusModule'->'startDateStruct'->>'date', '^(\d{4}-\d{2})$', '\1-01'), ''))::DATE AS start_date,
        (NULLIF(regexp_replace(raw_json->'protocolSection'->'statusModule'->'primaryCompletionDateStruct'->>'date', '^(\d{4}-\d{2})$', '\1-01'), ''))::DATE AS primary_completion_date,
        (NULLIF(regexp_replace(raw_json->'protocolSection'->'statusModule'->'completionDateStruct'->>'date', '^(\d{4}-\d{2})$', '\1-01'), ''))::DATE AS completion_date,
        (NULLIF(regexp_replace(raw_json->'protocolSection'->'statusModule'->>'studyFirstSubmitDate', '^(\d{4}-\d{2})$', '\1-01'), ''))::DATE AS first_submit_date,
        raw_json->'protocolSection'->'statusModule'->>'whyStopped' AS why_stopped,

        raw_json->'protocolSection'->'designModule'->>'studyType' AS study_type,
        raw_json->'protocolSection'->'designModule'->'phases'->0 AS phase_raw,
        CASE raw_json->'protocolSection'->'designModule'->'phases'->0
            WHEN '"PHASE1"' THEN 1 WHEN '"PHASE2"' THEN 2
            WHEN '"PHASE3"' THEN 3 WHEN '"PHASE4"' THEN 4
            WHEN '"EARLY_PHASE1"' THEN 1 ELSE NULL
        END AS phase_numeric,

        (raw_json->'protocolSection'->'designModule'->'enrollmentInfo'->>'count')::INT AS enrollment_count,
        raw_json->'protocolSection'->'designModule'->'enrollmentInfo'->>'type' AS enrollment_type,

        raw_json->'protocolSection'->'sponsorCollaboratorsModule'->'leadSponsor'->>'name' AS lead_sponsor_name,
        raw_json->'protocolSection'->'sponsorCollaboratorsModule'->'leadSponsor'->>'class' AS lead_sponsor_class,

        raw_json->'protocolSection'->'eligibilityModule'->>'eligibilityCriteria' AS eligibility_criteria_text,
        raw_json->'protocolSection'->'eligibilityModule'->>'healthyVolunteers' AS healthy_volunteers,
        raw_json->'protocolSection'->'eligibilityModule'->>'sex' AS sex,
        raw_json->'protocolSection'->'eligibilityModule'->>'minimumAge' AS minimum_age,
        raw_json->'protocolSection'->'eligibilityModule'->>'maximumAge' AS maximum_age,

        raw_json->'protocolSection'->'conditionsModule'->'conditions' AS conditions_json,
        raw_json->'protocolSection'->'armsInterventionsModule'->'interventions' AS interventions_json,
        raw_json->'protocolSection'->'contactsLocationsModule'->'locations' AS locations_json,

        (raw_json->'protocolSection'->'resultsSection') IS NOT NULL AS has_results

    FROM source
)

SELECT *,
    CASE
        WHEN overall_status = 'COMPLETED' THEN 'completed'
        WHEN overall_status IN ('TERMINATED','WITHDRAWN') THEN 'terminated'
        WHEN overall_status IN ('RECRUITING','ACTIVE_NOT_RECRUITING','ENROLLING_BY_INVITATION','NOT_YET_RECRUITING') THEN 'ongoing'
        ELSE 'other'
    END AS outcome_label,
    CASE WHEN completion_date IS NOT NULL AND start_date IS NOT NULL
        THEN (completion_date - start_date)::INT ELSE NULL
    END AS study_duration_days
FROM extracted
