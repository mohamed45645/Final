"""Browse, filter, export and delete transactions."""
import streamlit as st

from utils import db, ui

ui.setup("Transactions", "📜")
st.title("📜 Transactions")

df = db.get_transactions()
if df.empty:
    st.info("No transactions yet.")
    st.stop()

with st.expander("🔎 Filters", expanded=True):
    c1, c2, c3 = st.columns(3)
    min_d, max_d = df["date"].min().date(), df["date"].max().date()
    date_range = c1.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    types = c2.multiselect("Type", ["Income", "Expense"], default=["Income", "Expense"])
    cats = c3.multiselect("Category", sorted(df["category"].unique()))
    text = st.text_input("Search in notes")

view = df[df["type"].isin(types)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    view = view[(view["date"].dt.date >= date_range[0]) & (view["date"].dt.date <= date_range[1])]
if cats:
    view = view[view["category"].isin(cats)]
if text:
    view = view[view["note"].str.contains(text, case=False, na=False)]

inc = view.loc[view["type"] == "Income", "amount"].sum()
exp = view.loc[view["type"] == "Expense", "amount"].sum()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows", len(view))
m2.metric("Income", ui.money(inc))
m3.metric("Expenses", ui.money(exp))
m4.metric("Net", ui.money(inc - exp))

EDIT_COLS = ["date", "type", "category", "amount", "note"]
all_cats = sorted(set(db.EXPENSE_CATEGORIES + db.INCOME_CATEGORIES) | set(df["category"]))

table = view.copy()
table["date"] = table["date"].dt.date
table = table.reset_index(drop=True)
table["Delete"] = False
st.caption("✏️ Double-click any cell to edit it, then press **Save changes**. Tick 🗑️ to delete rows.")
edited = st.data_editor(
    table, hide_index=True, use_container_width=True, height=440,
    disabled=["id"],
    column_config={
        "id": None,
        "date": st.column_config.DateColumn("Date"),
        "type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"], required=True),
        "category": st.column_config.SelectboxColumn("Category", options=all_cats, required=True),
        "amount": st.column_config.NumberColumn("Amount", format="%.2f", min_value=0.01, required=True),
        "Delete": st.column_config.CheckboxColumn("🗑️"),
    },
)

changed = (
    table[EDIT_COLS].fillna("").astype(str) != edited[EDIT_COLS].fillna("").astype(str)
).any(axis=1) & ~edited["Delete"]
to_delete = edited.loc[edited["Delete"], "id"].tolist()

col_a, col_b, col_c = st.columns(3)
if col_a.button(f"💾 Save changes ({int(changed.sum())})", type="primary", disabled=not changed.any()):
    rows = edited.loc[changed]
    if (rows["amount"].fillna(0) <= 0).any() or rows["date"].isna().any():
        st.error("Every edited row needs a valid date and an amount greater than zero.")
    else:
        db.update_transactions(
            rows[["id", "date", "type", "category", "amount", "note"]].itertuples(index=False, name=None)
        )
        st.rerun()
if col_b.button(f"🗑️ Delete selected ({len(to_delete)})", disabled=not to_delete):
    db.delete_transactions(to_delete)
    st.rerun()
col_c.download_button("⬇️ Export filtered CSV", view.to_csv(index=False).encode("utf-8"),
                      "transactions.csv", "text/csv")
