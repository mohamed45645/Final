"""Optional password gate.

Set APP_PASSWORD in `.streamlit/secrets.toml` (or as an environment variable /
Streamlit Cloud secret) to protect the app. If it is not set, the app is open.
"""
from __future__ import annotations

import hmac
import os

import streamlit as st


def _configured_password() -> str | None:
    try:
        value = st.secrets.get("APP_PASSWORD")
    except Exception:  # no secrets file
        value = None
    return value or os.environ.get("APP_PASSWORD")


def require_login() -> None:
    password = _configured_password()
    if not password or st.session_state.get("auth_ok"):
        return
    st.title("🔒 Finance Manager")
    entered = st.text_input("Password", type="password")
    if entered:
        if hmac.compare_digest(entered, password):
            st.session_state["auth_ok"] = True
            st.rerun()
        st.error("Wrong password.")
    st.stop()
