{{
    config(
        materialized='table',
        tags=['marts', 'dimensions', 'user']
    )
}}

/*
    User statistics dimension table
    Contains lifetime aggregates and current status
*/

WITH lifetime_stats AS (
    SELECT
        -- Lifetime aggregates
        SUM(gold_value) AS lifetime_gold,
        SUM(xp_value) AS lifetime_xp,
        COUNT(*) AS lifetime_events,

        -- Activity breakdown
        SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS lifetime_calls_made,
        SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS lifetime_calls_connected,
        SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS lifetime_meetings_booked,
        SUM(CASE WHEN event_type = 'meeting_attended' THEN 1 ELSE 0 END) AS lifetime_meetings_attended,
        SUM(CASE WHEN event_type = 'email_sent' THEN 1 ELSE 0 END) AS lifetime_emails_sent,

        -- Timestamps
        MIN(created_at) AS first_activity,
        MAX(created_at) AS last_activity,

        -- Days active
        COUNT(DISTINCT DATE(created_at)) AS days_active

    FROM {{ ref('stg_sales_events') }}
),

current_level AS (
    SELECT
        -- Calculate current level from lifetime XP
        FLOOR(lifetime_xp / {{ var('xp_per_level', 1000) }}::NUMERIC) + 1 AS level,
        MOD(lifetime_xp, {{ var('xp_per_level', 1000) }}) AS xp_in_current_level,
        {{ var('xp_per_level', 1000) }} - MOD(lifetime_xp, {{ var('xp_per_level', 1000) }}) AS xp_to_next_level

    FROM lifetime_stats
),

current_rank AS (
    SELECT
        CASE
            WHEN lifetime_gold >= {{ var('rank_thresholds').challenger }} THEN 'Challenger'
            WHEN lifetime_gold >= {{ var('rank_thresholds').diamond }} THEN 'Diamond'
            WHEN lifetime_gold >= {{ var('rank_thresholds').platinum }} THEN 'Platinum'
            WHEN lifetime_gold >= {{ var('rank_thresholds').gold }} THEN 'Gold'
            WHEN lifetime_gold >= {{ var('rank_thresholds').silver }} THEN 'Silver'
            WHEN lifetime_gold >= {{ var('rank_thresholds').bronze }} THEN 'Bronze'
            ELSE 'Iron'
        END AS rank,

        -- Calculate gold needed for next rank
        CASE
            WHEN lifetime_gold < {{ var('rank_thresholds').bronze }} THEN {{ var('rank_thresholds').bronze }} - lifetime_gold
            WHEN lifetime_gold < {{ var('rank_thresholds').silver }} THEN {{ var('rank_thresholds').silver }} - lifetime_gold
            WHEN lifetime_gold < {{ var('rank_thresholds').gold }} THEN {{ var('rank_thresholds').gold }} - lifetime_gold
            WHEN lifetime_gold < {{ var('rank_thresholds').platinum }} THEN {{ var('rank_thresholds').platinum }} - lifetime_gold
            WHEN lifetime_gold < {{ var('rank_thresholds').diamond }} THEN {{ var('rank_thresholds').diamond }} - lifetime_gold
            WHEN lifetime_gold < {{ var('rank_thresholds').challenger }} THEN {{ var('rank_thresholds').challenger }} - lifetime_gold
            ELSE 0
        END AS gold_to_next_rank

    FROM lifetime_stats
),

performance_metrics AS (
    SELECT
        -- Calculate performance rates
        ROUND(
            CASE
                WHEN lifetime_calls_made > 0
                THEN (lifetime_calls_connected::NUMERIC / lifetime_calls_made::NUMERIC) * 100
                ELSE 0
            END,
            2
        ) AS lifetime_connect_rate_pct,

        ROUND(
            CASE
                WHEN lifetime_calls_connected > 0
                THEN (lifetime_meetings_booked::NUMERIC / lifetime_calls_connected::NUMERIC) * 100
                ELSE 0
            END,
            2
        ) AS lifetime_booking_rate_pct,

        ROUND(
            CASE
                WHEN days_active > 0
                THEN lifetime_events::NUMERIC / days_active::NUMERIC
                ELSE 0
            END,
            2
        ) AS avg_events_per_day

    FROM lifetime_stats
)

-- Combine all CTEs
SELECT
    ls.*,
    cl.level AS current_level,
    cl.xp_in_current_level,
    cl.xp_to_next_level,
    cr.rank AS current_rank,
    cr.gold_to_next_rank,
    pm.lifetime_connect_rate_pct,
    pm.lifetime_booking_rate_pct,
    pm.avg_events_per_day,
    CURRENT_TIMESTAMP AS last_calculated

FROM lifetime_stats ls
CROSS JOIN current_level cl
CROSS JOIN current_rank cr
CROSS JOIN performance_metrics pm
