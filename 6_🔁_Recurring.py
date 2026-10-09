"""Recurring income & bills (salary, rent, subscriptions...)."""
import streamlit as st

from utils import db, ui

ui.setup("Recurring", "🔁")
st.title("🔁 Recurring Transactions")
st.caption("Added automatically once per month, on the day you choose (1–28).")

t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
cats = db.EXPENSE_CATEGORIES if t_type == "Expense" else db.INCOME_CATEGORIES
with st.form("rec_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    name = c1.text_input("Name (e.g. Netflix, Rent, Salary)")
    category = c2.selectbox("Category", cats)
    amount = c1.number_input("Amount", min_value=0.0, step=10.0, format="%.2f")
    day = c2.number_input("Day of month", min_value=1, max_value=28, value=1, step=1)
    ok = st.form_submit_button("➕ Add recurring item", type="primary")
if ok:
    if name.strip() and amount > 0:
        db.add_recurring(name, t_type, category, amount, int(day))
        st.rerun()
    else:
        st.error("Enter a name and an amount greater than zero.")

items = db.get_recurring()
if items.empty:
    st.info("Nothing scheduled yet.")
for r in items.itertuples():
    with st.container(border=True):
        a, b, c = st.columns([5, 2, 1])
        sign = "🟢" if r.type == "Income" else "🔴"
        a.markdown(f"{sign} **{r.name}** · {r.category} · {ui.money(r.amount)} · day {r.day}")
        if r.last_applied:
            a.caption(f"Last applied: {r.last_applied}")
        active = b.toggle("Active", value=bool(r.active), key=f"act_{r.id}")
        if active != bool(r.active):
            db.set_recurring_active(r.id, active)
            st.rerun()
        if c.button("Delete", key=f"rdel_{r.id}"):
            db.delete_recurring(r.id)
            st.rerun()
