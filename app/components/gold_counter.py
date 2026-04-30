"""Gold counter component."""

import streamlit as st

from app.components.template_loader import load_template


def render_gold_counter(gold: int) -> None:
    formatted_gold = f"{gold:,}"
    html = load_template("gold_counter.html", gold=formatted_gold)
    st.markdown(html, unsafe_allow_html=True)


def render_gold_counter_with_change(gold: int, previous_gold: int) -> None:
    formatted_gold = f"{gold:,}"
    gold_change = gold - previous_gold
    change_html = ""
    if gold_change > 0:
        change_html = f'<span class="gold-change">+{gold_change}</span>'
    html = load_template(
        "gold_counter_with_change.html",
        gold=formatted_gold,
        change_html=change_html,
    )
    st.markdown(html, unsafe_allow_html=True)
