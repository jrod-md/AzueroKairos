"""Minimal Streamlit dashboard scaffold for Azuero Kairós."""

from __future__ import annotations

import streamlit as st

from azuero_kairos.confidence_engine import DECISION_STATES


st.set_page_config(page_title="Azuero Kairós", layout="wide")

st.title("Azuero Kairós")
st.caption("Copernicus-based satellite confidence decision layer for Azuero, Panama.")

st.subheader("Decision States")
st.write(", ".join(f"`{state}`" for state in DECISION_STATES))

st.info(
    "This scaffold does not detect contamination or declare water safe. "
    "Official dashboard outputs will be generated during the hackathon window."
)
