"""
XP Bar Component
Displays experience progress with animated bar
"""

import streamlit as st
from pathlib import Path


def render_xp_bar(
    current_xp: int,
    xp_to_next_level: int,
    current_level: int
) -> None:
    """
    Render the XP progress bar with LoL styling

    Args:
        current_xp: Current XP in this level
        xp_to_next_level: XP needed for next level
        current_level: Current player level
    """
    # Calculate percentage
    total_xp_for_level = 1000  # Each level requires 1000 XP
    percentage = (current_xp / total_xp_for_level) * 100

    # Render XP bar
    st.markdown(
        f"""
        <div class="xp-container">
            <div class="xp-bar-background">
                <div class="xp-bar-fill" style="width: {percentage}%"></div>
            </div>
            <div class="xp-text">
                {percentage:.0f}% to Level {current_level + 1}
                ({current_xp}/{total_xp_for_level} XP)
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_level_badge(level: int) -> None:
    """
    Render the level badge

    Args:
        level: Current player level
    """
    st.markdown(
        f"""
        <div class="level-badge">
            <span class="level-text">Lvl {level}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_rank_badge(rank: str) -> None:
    """
    Render the rank badge with image

    Args:
        rank: Current rank (Iron, Bronze, Silver, Gold, Platinum, Emerald, Diamond, Master, Grandmaster, Challenger)
    """
    rank_image_path = Path(__file__).parent.parent / "assets" / "images" / "ranks" / f"{rank.lower()}.png"

    if rank_image_path.exists():
        # Display rank image
        st.image(str(rank_image_path), width=100)
    else:
        # Fallback placeholder when image not found
        st.markdown(
            f"""
            <div class="rank-badge-placeholder">
                <div style="width: 100px; height: 100px; border: 2px dashed #c8aa6e;
                     display: flex; align-items: center; justify-content: center;
                     background: rgba(200, 170, 110, 0.1); border-radius: 8px;">
                    <span style="color: #c8aa6e; font-size: 12px;">{rank}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
