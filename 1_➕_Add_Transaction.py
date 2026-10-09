"""Add a single transaction or import many from CSV."""
from datetime import date

import pandas as pd
import streamlit as st

from utils import db, ui

ui.setup("Add Transaction", "➕")
st.title("➕ Add Transaction")

tab_single, tab_import = st.tabs(["✍️ Single entry", "📥 Import from CSV"])

with tab_single:
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    cats = db.EXPENSE_CATEGORIES if t_type == "Expense" else db.INCOME_CATEGORIES
    with st.form("add_tx", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d = c1.date_input("Date", value=date.today())
        category = c2.selectbox("Category", cats)
        amount = c1.number_input("Amount", min_value=0.0, step=10.0, format="%.2f")
        note = c2.text_input("Note (optional)")
        submitted = st.form_submit_button("💾 Save transaction", type="primary")
    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            db.add_transaction(d, t_type, category, amount, note)
            st.success(f"Saved {t_type.lower()}: {ui.money(amount)} · {category}")

    st.subheader("Latest entries")
    latest = db.get_transactions().head(5)
    if latest.empty:
        st.caption("Nothing here yet.")
    else:
        latest["date"] = latest["date"].dt.date
        st.dataframe(latest.drop(columns="id"), hide_index=True, use_container_width=True)

with tab_import:
    st.markdown(
        "Upload a CSV with the columns **date, type, category, amount, note** "
        "(`type` is `Income` or `Expense`; `note` is optional)."
    )
    template = pd.DataFrame(
        [{"date": date.today().isoformat(), "type": "Expense", "category": "🛒 Groceries",
          "amount": 250.0, "note": "Example"}]
    )
    st.download_button("⬇️ Download CSV template", template.to_csv(index=False).encode("utf-8"),
                       "template.csv", "text/csv")
    file = st.file_uploader("Choose a CSV file", type="csv")
    if file is not None:
        try:
            data = pd.read_csv(file)
            st.dataframe(data.head(20), hide_index=True, use_container_width=True)
            st.caption(f"{len(data)} rows detected")
            if st.button("📥 Import these rows", type="primary"):
                n = db.import_transactions(data)
                st.success(f"Imported {n} valid transactions.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not import: {e}")
