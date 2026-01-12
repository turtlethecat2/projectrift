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

weekly_stats AS (
    SELECT
        -- Weekly meetings for rank calculation (week starts Monday)
        SUM(CASE
            WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE)
            AND event_type = 'meeting_booked'
            THEN 1
            ELSE 0
        END) AS weekly_meetings_booked

    FROM {{ ref('stg_sales_events') }}
),

current_rank AS (
    SELECT
        CASE
            WHEN ws.weekly_meetings_booked >= 9 THEN 'Challenger'
            WHEN ws.weekly_meetings_booked = 8 THEN 'Grandmaster'
            WHEN ws.weekly_meetings_booked = 7 THEN 'Master'
            WHEN ws.weekly_meetings_booked = 6 THEN 'Diamond'
            WHEN ws.weekly_meetings_booked = 5 THEN 'Emerald'
            WHEN ws.weekly_meetings_booked = 4 THEN 'Platinum'
            WHEN ws.weekly_meetings_booked = 3 THEN 'Gold'
            WHEN ws.weekly_meetings_booked = 2 THEN 'Silver'
            WHEN ws.weekly_meetings_booked = 1 THEN 'Bronze'
            ELSE 'Iron'
        END AS rank,

        -- Calculate meetings needed for next rank
        CASE
            WHEN ws.weekly_meetings_booked >= 9 THEN 0
            ELSE (
                CASE
                    WHEN ws.weekly_meetings_booked < 1 THEN 1 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 2 THEN 2 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 3 THEN 3 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 4 THEN 4 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 5 THEN 5 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 6 THEN 6 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 7 THEN 7 - ws.weekly_meetings_booked
                    WHEN ws.weekly_meetings_booked < 8 THEN 8 - ws.weekly_meetings_booked
                    ELSE 9 - ws.weekly_meetings_booked
                END
            )
        END AS meetings_to_next_rank,

        ws.weekly_meetings_booked

    FROM weekly_stats ws
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
    cr.meetings_to_next_rank,
    cr.weekly_meetings_booked,
    pm.lifetime_connect_rate_pct,
    pm.lifetime_booking_rate_pct,
    pm.avg_events_per_day,
    CURRENT_TIMESTAMP AS last_calculated

FROM lifetime_stats ls
CROSS JOIN current_level cl
CROSS JOIN current_rank cr
CROSS JOIN performance_metrics pm
