{{ config(materialized='table', tags=['marts','dimensions']) }}

WITH lifetime_stats AS (
    SELECT
        SUM(gold_value) AS lifetime_gold,
        SUM(xp_value) AS lifetime_xp,
        COUNT(*) AS lifetime_events,
        SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS lifetime_calls_made,
        SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS lifetime_calls_connected,
        SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS lifetime_meetings_booked,
        SUM(CASE WHEN event_type = 'meeting_attended' THEN 1 ELSE 0 END) AS lifetime_meetings_attended,
        SUM(CASE WHEN event_type = 'email_sent' THEN 1 ELSE 0 END) AS lifetime_emails_sent,
        MIN(created_at) AS first_activity,
        MAX(created_at) AS last_activity,
        COUNT(DISTINCT DATE(created_at)) AS days_active
    FROM {{ ref('stg_sales_events') }}
),

current_level AS (
    SELECT
        FLOOR(lifetime_xp / {{ var('xp_per_level', 1000) }}::NUMERIC) + 1 AS level,
        MOD(lifetime_xp, {{ var('xp_per_level', 1000) }}) AS xp_in_current_level,
        {{ var('xp_per_level', 1000) }} - MOD(lifetime_xp, {{ var('xp_per_level', 1000) }}) AS xp_to_next_level
    FROM lifetime_stats
),

weekly_stats AS (
    SELECT
        SUM(CASE
            WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE) AND event_type = 'meeting_booked'
            THEN 1 ELSE 0 END) AS weekly_meetings_booked
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
        ws.weekly_meetings_booked
    FROM weekly_stats ws
),

performance_metrics AS (
    SELECT
        ROUND(
            CASE WHEN lifetime_calls_made > 0
                THEN (lifetime_calls_connected::NUMERIC / lifetime_calls_made::NUMERIC) * 100
                ELSE 0 END,
            2
        ) AS lifetime_connect_rate_pct,
        ROUND(
            CASE WHEN lifetime_calls_connected > 0
                THEN (lifetime_meetings_booked::NUMERIC / lifetime_calls_connected::NUMERIC) * 100
                ELSE 0 END,
            2
        ) AS lifetime_booking_rate_pct,
        ROUND(
            CASE WHEN days_active > 0
                THEN lifetime_events::NUMERIC / days_active::NUMERIC
                ELSE 0 END,
            2
        ) AS avg_events_per_day
    FROM lifetime_stats
)

SELECT
    ls.*,
    cl.level AS current_level,
    cl.xp_in_current_level,
    cl.xp_to_next_level,
    cr.rank AS current_rank,
    cr.weekly_meetings_booked,
    pm.lifetime_connect_rate_pct,
    pm.lifetime_booking_rate_pct,
    pm.avg_events_per_day,
    CURRENT_TIMESTAMP AS last_calculated
FROM lifetime_stats ls
CROSS JOIN current_level cl
CROSS JOIN current_rank cr
CROSS JOIN performance_metrics pm
