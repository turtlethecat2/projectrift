"""
Avatar Component
Displays the player avatar icon
"""

import streamlit as st

from app.components.template_loader import load_template


def render_avatar(icon: str = "⚔️") -> None:
    """
    Render the avatar icon

    Args:
        icon: Emoji or text to display in avatar (default: sword emoji)
    """
    html = load_template("avatar.html", icon=icon)
    st.markdown(html, unsafe_allow_html=True)
