{{
    config(
        materialized='view',
        tags=['staging', 'events']
    )
}}

/*
    Staging model for sales events
    Cleans and standardizes raw_events data for downstream consumption
*/

WITH source AS (
    SELECT * FROM {{ source('public', 'raw_events') }}
),

cleaned AS (
    SELECT
        -- Primary key
        id AS event_id,

        -- Event attributes
        source,
        event_type,
        gold_value,
        xp_value,
        metadata,

        -- Timestamps
        created_at,
        processed_at,

        -- Derived fields
        DATE(created_at) AS event_date,
        EXTRACT(HOUR FROM created_at) AS event_hour,
        EXTRACT(DOW FROM created_at) AS day_of_week,  -- 0 = Sunday, 6 = Saturday

        -- Additional metadata extractions
        metadata->>'prospect_name' AS prospect_name,
        metadata->>'company' AS company_name,
        (metadata->>'call_duration')::INTEGER AS call_duration_seconds

    FROM source

    -- Only include events from the last 90 days (configurable via var)
    WHERE created_at >= CURRENT_DATE - INTERVAL '{{ var("raw_events_retention_days", 90) }} days'
)

SELECT * FROM cleaned
