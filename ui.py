"""Shared UI helpers: page setup, CSS, KPI cards, formatting."""
from __future__ import annotations

import streamlit as st

from utils import auth, db

CURRENCIES = ["EGP", "USD", "EUR", "SAR", "AED", "GBP"]

CSS = """
<style>
  .block-container {padding-top: 2rem; padding-bottom: 3rem;}
  h1 {font-weight: 800; letter-spacing: -0.5px;}
  .kpi {
    border-radius: 18px; padding: 18px 20px; color: #fff;
    box-shadow: 0 6px 18px rgba(60, 40, 140, .18);
  }
  .kpi .label {font-size: .82rem; opacity: .85; text-transform: uppercase; letter-spacing: .6px;}
  .kpi .value {font-size: 1.7rem; font-weight: 800; margin-top: 4px;}
  .kpi .delta {font-size: .8rem; margin-top: 2px; opacity: .95;}
  .kpi.income  {background: linear-gradient(135deg, #00b894, #00cec9);}
  .kpi.expense {background: linear-gradient(135deg, #e17055, #d63031);}
  .kpi.net     {background: linear-gradient(135deg, #6c5ce7, #a29bfe);}
  .kpi.rate    {background: linear-gradient(135deg, #0984e3, #74b9ff);}
  .pill {display:inline-block; padding: 2px 10px; border-radius: 99px; font-size: .75rem;
         background: rgba(108,92,231,.12); color: #6c5ce7; font-weight: 600;}
  div[data-testid="stSidebar"] {border-right: 1px solid rgba(108,92,231,.15);}
</style>
"""


def setup(title: str, icon: str) -> None:
    """Must be the first Streamlit call on every page."""
    st.set_page_config(page_title=f"{title} · Finance Manager", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    auth.require_login()
    db.init_db()
    if "recurring_checked" not in st.session_state:
        n = db.apply_recurring()
        st.session_state["recurring_checked"] = True
        if n:
            st.toast(f"🔁 {n} recurring transaction(s) added for this month")
    st.session_state.setdefault("currency", "EGP")
    with st.sidebar:
        st.markdown("## 💰 Finance Manager")
        st.session_state["currency"] = st.selectbox(
            "Currency", CURRENCIES, index=CURRENCIES.index(st.session_state["currency"])
        )
        st.divider()
        st.caption("Built with Streamlit · Plotly · SQLite")


def currency() -> str:
    return st.session_state.get("currency", "EGP")


def money(value: float) -> str:
    return f"{value:,.2f} {currency()}"


def kpi(label: str, value: str, tone: str, delta: str | None = None) -> None:
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    st.markdown(
        f'<div class="kpi {tone}"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>{delta_html}</div>',
        unsafe_allow_html=True,
    )


def delta_text(change: float | None, good_when_up: bool = True) -> str | None:
    if change is None:
        return None
    arrow = "▲" if change >= 0 else "▼"
    return f"{arrow} {abs(change):.1f}% vs last month"
