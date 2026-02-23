"""Frontend Streamlit application for Criterion code review interface.

This module provides a web UI for viewing system health status and
triggering manual code analysis on GitLab merge requests.
"""

import os

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Criterion",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Criterion")
st.caption("GitLab MR Code Review Intelligence")

# System status
st.subheader("System Status")
try:
    response = httpx.get(f"{BACKEND_URL}/health", timeout=5)
    health = response.json()

    if health["status"] == "healthy":
        st.success("● All systems operational")
    else:
        st.warning("● System degraded")

    col1, col2, col3 = st.columns(3)
    col1.metric("Database", health["checks"]["database"])
    col2.metric("Redis", health["checks"]["redis"])
    col3.metric("Workers", health["checks"]["celery_workers"])

except Exception as e:
    st.error(f"Cannot reach backend: {e}")

st.divider()
st.subheader("Recent Analyses")
st.info("No analyses yet. Trigger one below or open a GitLab MR.")

st.divider()
st.subheader("Trigger Manual Analysis")
mr_url = st.text_input(
    "GitLab MR URL",
    placeholder="https://gitlab.com/org/repo/-/merge_requests/42"
)
if st.button("Analyze MR", type="primary"):
    if mr_url:
        st.info("Analysis queued — this feature coming in Phase 2")
    else:
        st.error("Please enter an MR URL")