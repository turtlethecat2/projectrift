{{
    config(
        materialized='table',
        tags=['marts', 'daily', 'performance']
    )
}}

/*
    Daily performance fact table
    Aggregates sales activity by day with rankings and metrics
*/

WITH daily_events AS (
    SELECT
        event_date,

        -- Event counts
        COUNT(*) AS total_events,
        SUM(gold_value) AS total_gold,
        SUM(xp_value) AS total_xp,

        -- Activity breakdown
        SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
        SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
        SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked,
        SUM(CASE WHEN event_type = 'meeting_attended' THEN 1 ELSE 0 END) AS meetings_attended,
        SUM(CASE WHEN event_type = 'email_sent' THEN 1 ELSE 0 END) AS emails_sent,

        -- Time-based metrics
        MIN(created_at) AS first_event_time,
        MAX(created_at) AS last_event_time

    FROM {{ ref('stg_sales_events') }}
    GROUP BY 1
),

cumulative_stats AS (
    SELECT
        event_date,
        total_events,
        total_gold,
        total_xp,
        calls_made,
        calls_connected,
        meetings_booked,
        meetings_attended,
        emails_sent,
        first_event_time,
        last_event_time,

        -- Cumulative totals (running sum)
        SUM(total_xp) OVER (
            ORDER BY event_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_xp,

        SUM(total_gold) OVER (
            ORDER BY event_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_gold

    FROM daily_events
),

ranked AS (
    SELECT
        *,

        -- Calculate level from cumulative XP
        FLOOR(cumulative_xp / {{ var('xp_per_level', 1000) }}::NUMERIC) + 1 AS current_level,

        -- Calculate rank based on daily gold
        CASE
            WHEN total_gold >= {{ var('rank_thresholds').challenger }} THEN 'Challenger'
            WHEN total_gold >= {{ var('rank_thresholds').diamond }} THEN 'Diamond'
            WHEN total_gold >= {{ var('rank_thresholds').platinum }} THEN 'Platinum'
            WHEN total_gold >= {{ var('rank_thresholds').gold }} THEN 'Gold'
            WHEN total_gold >= {{ var('rank_thresholds').silver }} THEN 'Silver'
            WHEN total_gold >= {{ var('rank_thresholds').bronze }} THEN 'Bronze'
            ELSE 'Iron'
        END AS daily_rank,

        -- Calculate connect rate percentage
        ROUND(
            CASE
                WHEN calls_made > 0
                THEN (calls_connected::NUMERIC / calls_made::NUMERIC) * 100
                ELSE 0
            END,
            2
        ) AS connect_rate_pct,

        -- Calculate meeting booking rate
        ROUND(
            CASE
                WHEN calls_connected > 0
                THEN (meetings_booked::NUMERIC / calls_connected::NUMERIC) * 100
                ELSE 0
            END,
            2
        ) AS booking_rate_pct

    FROM cumulative_stats
)

SELECT * FROM ranked
ORDER BY event_date DESC
