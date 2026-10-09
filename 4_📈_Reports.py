"""Insights, trends, forecasts and Excel report export."""
import io

import pandas as pd
import streamlit as st

from utils import analysis, charts, db, ui

ui.setup("Reports", "📈")
st.title("📈 Reports & Insights")

df_all = db.get_transactions()
if df_all.empty:
    st.info("Add some transactions to see reports.")
    st.stop()

period = st.radio("Period", analysis.PERIODS, index=3, horizontal=True, label_visibility="collapsed")
df = analysis.filter_period(df_all, period)
if df.empty:
    st.warning("No data in this period.")
    st.stop()

exp = df[df["type"] == "Expense"]

st.subheader("💡 Key insights")
c1, c2, c3, c4 = st.columns(4)
if not exp.empty:
    top = exp.groupby("category")["amount"].sum().sort_values(ascending=False)
    days = max((df["date"].max() - df["date"].min()).days + 1, 1)
    biggest = exp.loc[exp["amount"].idxmax()]
    c1.metric("Top category", top.index[0], ui.money(top.iloc[0]))
    c2.metric("Avg daily spend", ui.money(exp["amount"].sum() / days))
    c3.metric("Biggest expense", ui.money(biggest["amount"]), biggest["category"])
c4.metric("Transactions", len(df))

fc = analysis.month_end_forecast(df_all)
st.info(
    f"🔮 **Month-end forecast:** you've spent {ui.money(fc['spent'])} in {fc['day']} days; "
    f"at this pace you'll reach about **{ui.money(fc['projected'])}** by day {fc['days_in_month']}."
)

left, right = st.columns(2)
left.plotly_chart(charts.weekday_spending(df), use_container_width=True)
right.plotly_chart(charts.top_categories(df, 10), use_container_width=True)
st.plotly_chart(charts.category_month_heatmap(df), use_container_width=True)

st.subheader("🗓️ Monthly summary")
monthly = analysis.monthly_table(df)
st.dataframe(
    monthly, hide_index=True, use_container_width=True,
    column_config={
        "Income": st.column_config.NumberColumn(format="%.2f"),
        "Expense": st.column_config.NumberColumn(format="%.2f"),
        "Net": st.column_config.NumberColumn(format="%.2f"),
        "Savings rate %": st.column_config.NumberColumn(format="%.1f%%"),
    },
)

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    out = df.copy()
    out["date"] = out["date"].dt.date
    out.to_excel(writer, sheet_name="Transactions", index=False)
    monthly.to_excel(writer, sheet_name="Monthly summary", index=False)
    if not exp.empty:
        exp.groupby("category", as_index=False)["amount"].sum().sort_values(
            "amount", ascending=False
        ).to_excel(writer, sheet_name="By category", index=False)
st.download_button(
    "⬇️ Download Excel report", buffer.getvalue(), "finance_report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary",
)
