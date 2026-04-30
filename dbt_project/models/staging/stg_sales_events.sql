{{ config(materialized='view', tags=['staging','events']) }}

WITH source AS (
    SELECT * FROM {{ source('public', 'raw_events') }}
),

cleaned AS (
    SELECT
        id AS event_id,
        source,
        event_type,
        gold_value,
        xp_value,
        metadata,
        created_at,
        processed_at,
        DATE(created_at) AS event_date,
        EXTRACT(HOUR FROM created_at) AS event_hour,
        EXTRACT(DOW FROM created_at) AS day_of_week,
        metadata->>'prospect_name' AS prospect_name,
        metadata->>'company' AS company_name,
        (metadata->>'call_duration')::INTEGER AS call_duration_seconds
    FROM source
    WHERE created_at >= CURRENT_DATE - INTERVAL '{{ var("raw_events_retention_days", 90) }} days'
)

SELECT * FROM cleaned
