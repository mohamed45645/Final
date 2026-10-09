"""Monthly category budgets and savings goals."""
from datetime import date, timedelta

import streamlit as st

from utils import analysis, charts, db, ui

ui.setup("Budgets & Goals", "🎯")
st.title("🎯 Budgets & Goals")

tab_budget, tab_goals = st.tabs(["🚦 Monthly budgets", "🏆 Savings goals"])

with tab_budget:
    with st.form("budget_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        cat = c1.selectbox("Category", db.EXPENSE_CATEGORIES)
        limit = c2.number_input("Monthly limit", min_value=0.0, step=100.0, format="%.2f")
        c3.write("")
        c3.write("")
        ok = c3.form_submit_button("Save", type="primary")
    if ok:
        if limit > 0:
            db.set_budget(cat, limit)
            st.rerun()
        else:
            st.error("Limit must be greater than zero.")

    status = analysis.budget_status(db.get_transactions(), db.get_budgets())
    if status.empty:
        st.info("No budgets yet. Create your first one above.")
    else:
        st.plotly_chart(charts.budget_bars(status), use_container_width=True)
        for row in status.itertuples():
            c1, c2 = st.columns([6, 1])
            icon = "🟢" if row.pct < 80 else ("🟠" if row.pct < 100 else "🔴")
            c1.markdown(f"{icon} **{row.category}** — {ui.money(row.spent)} / {ui.money(row.monthly_limit)}")
            c1.progress(min(row.pct / 100, 1.0))
            if c2.button("Remove", key=f"rm_{row.category}"):
                db.delete_budget(row.category)
                st.rerun()

with tab_goals:
    with st.form("goal_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Goal name")
        target = c2.number_input("Target amount", min_value=0.0, step=500.0, format="%.2f")
        deadline = c3.date_input("Deadline", value=date.today() + timedelta(days=180))
        add = st.form_submit_button("➕ Create goal", type="primary")
    if add:
        if name.strip() and target > 0:
            db.add_goal(name, target, deadline)
            st.rerun()
        else:
            st.error("Please enter a name and a target greater than zero.")

    goals = db.get_goals()
    if goals.empty:
        st.info("No goals yet.")
    for g in goals.itertuples():
        pct = min(g.saved / g.target, 1.0)
        with st.container(border=True):
            top, btn = st.columns([5, 1])
            top.markdown(f"### {'✅' if pct >= 1 else '🎯'} {g.name}")
            if btn.button("Delete", key=f"gdel_{g.id}"):
                db.delete_goal(g.id)
                st.rerun()
            st.progress(pct, text=f"{ui.money(g.saved)} of {ui.money(g.target)} ({pct*100:.0f}%)")
            if g.deadline:
                days_left = (date.fromisoformat(g.deadline) - date.today()).days
                remaining = max(g.target - g.saved, 0)
                if remaining > 0 and days_left > 0:
                    per_month = remaining / max(days_left / 30, 1)
                    st.caption(f"⏳ {days_left} days left · save about **{ui.money(per_month)}/month** to make it")
                elif remaining > 0:
                    st.caption("⏳ Deadline passed")
            a, b = st.columns([3, 1])
            amt = a.number_input("Add savings", min_value=0.0, step=100.0, key=f"amt_{g.id}",
                                 label_visibility="collapsed")
            if b.button("Add", key=f"add_{g.id}", disabled=amt <= 0):
                db.add_to_goal(g.id, amt)
                st.rerun()
