"""Load HTML templates from app/templates."""

from pathlib import Path

import streamlit as st


@st.cache_resource
def _load_template_file(template_name: str) -> str:
    template_path = Path(__file__).parent.parent / "templates" / template_name
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Template not found: {template_name}")


def load_template(template_name: str, **kwargs) -> str:
    template = _load_template_file(template_name)
    return template.format(**kwargs)
