"""
Gold Counter Component
Displays total gold earned with League of Legends styling
"""

import streamlit as st

from app.components.template_loader import load_template


def render_gold_counter(gold: int) -> None:
    """
    Render the gold counter with LoL styling

    Args:
        gold: Total gold amount
    """
    formatted_gold = f"{gold:,}"
    html = load_template("gold_counter.html", gold=formatted_gold)
    st.markdown(html, unsafe_allow_html=True)


def render_gold_counter_with_change(gold: int, previous_gold: int) -> None:
    """
    Render gold counter with change indicator

    Args:
        gold: Current gold amount
        previous_gold: Previous gold amount
    """
    formatted_gold = f"{gold:,}"
    gold_change = gold - previous_gold

    change_html = ""
    if gold_change > 0:
        change_html = f'<span class="gold-change">+{gold_change}</span>'

    html = load_template(
        "gold_counter_with_change.html", gold=formatted_gold, change_html=change_html
    )
    st.markdown(html, unsafe_allow_html=True)
