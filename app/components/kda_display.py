"""
KDA Display Component
Shows call/meeting statistics in a KDA-style format
"""

import streamlit as st

from app.components.template_loader import load_template


def render_kda_display(
    calls_made: int, calls_connected: int, meetings_booked: int
) -> None:
    """
    Render KDA-style statistics display

    Args:
        calls_made: Total calls made (dials)
        calls_connected: Total calls connected
        meetings_booked: Total meetings booked
    """
    connect_rate = (calls_connected / calls_made * 100) if calls_made > 0 else 0

    html = load_template(
        "kda_display.html",
        calls_made=calls_made,
        calls_connected=calls_connected,
        meetings_booked=meetings_booked,
        connect_rate=f"{connect_rate:.1f}%",
    )
    st.markdown(html, unsafe_allow_html=True)


def render_event_counts(stats: dict) -> None:
    """
    Render detailed event counts

    Args:
        stats: Dictionary with event statistics
    """
    html = load_template(
        "event_counts.html",
        calls_made=stats.get("calls_made", 0),
        calls_connected=stats.get("calls_connected", 0),
        meetings_booked=stats.get("meetings_booked", 0),
        events_today=stats.get("events_today", 0),
    )
    st.markdown(html, unsafe_allow_html=True)
