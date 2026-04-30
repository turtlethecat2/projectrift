"""Avatar component."""

import streamlit as st

from app.components.template_loader import load_template


def render_avatar(icon: str = "⚔️") -> None:
    html = load_template("avatar.html", icon=icon)
    st.markdown(html, unsafe_allow_html=True)
