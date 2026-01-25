"""
XP Bar Component
Displays experience progress with animated bar
"""

from pathlib import Path

import streamlit as st

from app.components.template_loader import load_template


def render_xp_bar(current_xp: int, xp_to_next_level: int, current_level: int) -> None:
    """
    Render the XP progress bar with LoL styling

    Args:
        current_xp: Current XP in this level
        xp_to_next_level: XP needed for next level
        current_level: Current player level
    """
    total_xp_for_level = 1000  # Each level requires 1000 XP
    percentage = (current_xp / total_xp_for_level) * 100

    html = load_template(
        "xp_bar.html",
        percentage=f"{percentage:.0f}",
        next_level=current_level + 1,
        current_xp=current_xp,
        total_xp=total_xp_for_level,
    )
    st.markdown(html, unsafe_allow_html=True)


def render_level_badge(level: int) -> None:
    """
    Render the level badge

    Args:
        level: Current player level
    """
    html = load_template("level_badge.html", level=level)
    st.markdown(html, unsafe_allow_html=True)


def render_rank_badge(rank: str) -> None:
    """
    Render the rank badge with image and text

    Args:
        rank: Current rank (Iron, Bronze, Silver, Gold, Platinum, Emerald, Diamond, Master, Grandmaster, Challenger)
    """
    rank_image_path = (
        Path(__file__).parent.parent
        / "assets"
        / "images"
        / "ranks"
        / f"{rank.lower()}.png"
    )

    if rank_image_path.exists():
        st.image(str(rank_image_path), width=100)
        html = load_template("rank_badge.html", rank=rank)
        st.markdown(html, unsafe_allow_html=True)
    else:
        html = load_template("rank_badge_placeholder.html", rank=rank)
        st.markdown(html, unsafe_allow_html=True)
