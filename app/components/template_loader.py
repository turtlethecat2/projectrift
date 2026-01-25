"""
Template Loader
Helper to load HTML templates from the templates folder
"""

from pathlib import Path

import streamlit as st


# Cache templates to avoid reading files repeatedly
@st.cache_resource
def _load_template_file(template_name: str) -> str:
    """Load a template file from disk (cached)"""
    template_path = Path(__file__).parent.parent / "templates" / template_name
    if template_path.exists():
        with open(template_path, "r") as f:
            return f.read()
    raise FileNotFoundError(f"Template not found: {template_name}")


def load_template(template_name: str, **kwargs) -> str:
    """
    Load an HTML template and fill in placeholders

    Args:
        template_name: Name of template file (e.g., "gold_counter.html")
        **kwargs: Values to substitute for {placeholders} in template

    Returns:
        HTML string with placeholders filled in

    Example:
        html = load_template("gold_counter.html", gold="1,234")
    """
    template = _load_template_file(template_name)
    return template.format(**kwargs)
