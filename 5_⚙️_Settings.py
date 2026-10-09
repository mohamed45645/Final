"""Backup, demo data and reset."""
import streamlit as st

from utils import db, ui

ui.setup("Settings", "⚙️")
st.title("⚙️ Settings & Data")

df = db.get_transactions()
st.metric("Stored transactions", len(df))

st.subheader("💾 Backup")
st.download_button("⬇️ Download all transactions (CSV)", df.to_csv(index=False).encode("utf-8"),
                   "backup_transactions.csv", "text/csv", disabled=df.empty)
st.caption("Tip: on Streamlit Community Cloud the local database can reset when the app restarts, "
           "so download a backup regularly and re-import it from the *Add Transaction* page.")

st.subheader("✨ Demo data")
if st.button("Load 6 months of demo data"):
    db.seed_demo_data()
    st.success("Demo data loaded.")

st.subheader("⚠️ Danger zone")
sure = st.checkbox("I understand this deletes ALL transactions, budgets and goals")
if st.button("🧨 Reset everything", disabled=not sure):
    db.clear_all()
    st.success("Everything has been deleted.")
