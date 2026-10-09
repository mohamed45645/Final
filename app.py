"""💰 Personal Finance Manager — Dashboard (home page)."""
import streamlit as st

from utils import analysis, charts, db, ui

ui.setup("Dashboard", "💰")

st.title("💰 Personal Finance Manager")
st.caption("Track income & expenses, stay inside your budgets, and reach your savings goals.")

df_all = db.get_transactions()

if df_all.empty:
    st.info("👋 Welcome! No transactions yet. Add your first one from the sidebar, "
            "or load demo data to explore the app.")
    if st.button("✨ Load demo data", type="primary"):
        db.seed_demo_data()
        st.rerun()
    st.stop()

period = st.radio("Period", analysis.PERIODS, horizontal=True, label_visibility="collapsed")
df = analysis.filter_period(df_all, period)

if df.empty:
    st.warning("No transactions in this period.")
    st.stop()

cur = analysis.summarize(df)
inc_delta = exp_delta = None
if period == "This month":
    prev = analysis.summarize(analysis.filter_period(df_all, "Last month"))
    inc_delta = ui.delta_text(analysis.pct_change(cur["income"], prev["income"]))
    exp_delta = ui.delta_text(analysis.pct_change(cur["expense"], prev["expense"]))

c1, c2, c3, c4 = st.columns(4)
with c1:
    ui.kpi("Income", ui.money(cur["income"]), "income", inc_delta)
with c2:
    ui.kpi("Expenses", ui.money(cur["expense"]), "expense", exp_delta)
with c3:
    ui.kpi("Net savings", ui.money(cur["net"]), "net")
with c4:
    ui.kpi("Savings rate", f"{cur['savings_rate']:.1f}%", "rate")

st.write("")

left, right = st.columns([3, 2])
left.plotly_chart(charts.income_vs_expense(df), use_container_width=True)
right.plotly_chart(charts.expense_donut(df), use_container_width=True)

left, right = st.columns([3, 2])
left.plotly_chart(charts.balance_curve(df), use_container_width=True)
right.plotly_chart(charts.top_categories(df), use_container_width=True)

st.subheader("🚦 Budget alerts (this month)")
status = analysis.budget_status(df_all, db.get_budgets())
if status.empty:
    st.caption("No budgets yet — set some on the **Budgets & Goals** page.")
else:
    alerts = status[status["pct"] >= 80]
    if alerts.empty:
        st.success("All budgets are healthy. Keep it up! 🎉")
    for row in alerts.itertuples():
        msg = f"**{row.category}** — {row.pct:.0f}% used ({ui.money(row.spent)} of {ui.money(row.monthly_limit)})"
        (st.error if row.pct >= 100 else st.warning)(msg)

st.subheader("🕒 Recent transactions")
recent = df_all.head(8).copy()
recent["date"] = recent["date"].dt.date
st.dataframe(
    recent[["date", "type", "category", "amount", "note"]],
    hide_index=True, use_container_width=True,
    column_config={"amount": st.column_config.NumberColumn(format="%.2f")},
)
