"""
Gold Counter Component
Displays total gold earned with League of Legends styling
"""

import streamlit as st


def render_gold_counter(gold: int) -> None:
    """
    Render the gold counter with LoL styling

    Args:
        gold: Total gold amount
    """
    # Format gold with comma separators
    formatted_gold = f"{gold:,}"

    # Render gold counter with custom HTML for styling
    st.markdown(
        f"""
        <div class="gold-counter">
            <span class="gold-icon">💰</span>
            <span class="gold-value">{formatted_gold}</span>
            <span class="gold-label">G</span>
        </div>
        """,
        unsafe_allow_html=True
    )


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

    st.markdown(
        f"""
        <div class="gold-counter">
            <span class="gold-icon">💰</span>
            <span class="gold-value">{formatted_gold}</span>
            <span class="gold-label">G</span>
            {change_html}
        </div>
        """,
        unsafe_allow_html=True
    )
