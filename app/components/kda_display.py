"""
KDA Display Component
Shows call/meeting statistics in a KDA-style format
"""

import streamlit as st


def render_kda_display(
    calls_made: int,
    calls_connected: int,
    meetings_booked: int
) -> None:
    """
    Render KDA-style statistics display

    Args:
        calls_made: Total calls made (dials)
        calls_connected: Total calls connected
        meetings_booked: Total meetings booked
    """
    # Calculate connect rate
    connect_rate = (calls_connected / calls_made * 100) if calls_made > 0 else 0

    st.markdown(
        f"""
        <div class="kda-container">
            <div class="kda-stat">
                <span class="kda-label">Calls</span>
                <span class="kda-value">{calls_made}</span>
            </div>
            <div class="kda-stat">
                <span class="kda-label">Connects</span>
                <span class="kda-value kda-value-success">{calls_connected}</span>
            </div>
            <div class="kda-stat">
                <span class="kda-label">Meetings</span>
                <span class="kda-value kda-value-gold">{meetings_booked}</span>
            </div>
            <div class="kda-stat">
                <span class="kda-label">Rate</span>
                <span class="kda-value">{connect_rate:.1f}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_event_counts(stats: dict) -> None:
    """
    Render detailed event counts

    Args:
        stats: Dictionary with event statistics
    """
    calls_made = stats.get('calls_made', 0)
    calls_connected = stats.get('calls_connected', 0)
    meetings_booked = stats.get('meetings_booked', 0)
    events_today = stats.get('events_today', 0)

    st.markdown(
        f"""
        <div class="events-container">
            <div class="event-stat">
                <span class="event-icon">📞</span>
                <span class="event-count">{calls_made}</span>
                <span class="event-label">Dials</span>
            </div>
            <div class="event-stat">
                <span class="event-icon">✅</span>
                <span class="event-count">{calls_connected}</span>
                <span class="event-label">Connected</span>
            </div>
            <div class="event-stat">
                <span class="event-icon">📅</span>
                <span class="event-count">{meetings_booked}</span>
                <span class="event-label">Meetings</span>
            </div>
            <div class="event-stat">
                <span class="event-icon">⚡</span>
                <span class="event-count">{events_today}</span>
                <span class="event-label">Today</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
