"""Pure-pandas helpers: period filtering, KPIs, budgets and forecasts."""
from __future__ import annotations

import calendar
from datetime import date

import pandas as pd

PERIODS = ["This month", "Last month", "Last 3 months", "Last 6 months", "This year", "All time"]


def period_range(label: str, df: pd.DataFrame):
    today = pd.Timestamp(date.today())
    first = today.replace(day=1)
    if label == "This month":
        return first, today
    if label == "Last month":
        end = first - pd.Timedelta(days=1)
        return end.replace(day=1), end
    if label == "Last 3 months":
        return first - pd.DateOffset(months=2), today
    if label == "Last 6 months":
        return first - pd.DateOffset(months=5), today
    if label == "This year":
        return today.replace(month=1, day=1), today
    return (df["date"].min(), df["date"].max()) if not df.empty else (today, today)


def filter_period(df: pd.DataFrame, label: str) -> pd.DataFrame:
    start, end = period_range(label, df)
    return df[(df["date"] >= start) & (df["date"] <= end)]


def summarize(df: pd.DataFrame) -> dict:
    income = float(df.loc[df["type"] == "Income", "amount"].sum())
    expense = float(df.loc[df["type"] == "Expense", "amount"].sum())
    net = income - expense
    rate = (net / income * 100) if income > 0 else 0.0
    return {"income": income, "expense": expense, "net": net, "savings_rate": rate}


def pct_change(current: float, previous: float):
    if previous == 0:
        return None
    return (current - previous) / previous * 100


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Month", "Income", "Expense", "Net", "Savings rate %"])
    d = df.copy()
    d["Month"] = d["date"].dt.to_period("M").astype(str)
    pivot = d.pivot_table(index="Month", columns="type", values="amount", aggfunc="sum", fill_value=0)
    for col in ("Income", "Expense"):
        if col not in pivot:
            pivot[col] = 0.0
    pivot["Net"] = pivot["Income"] - pivot["Expense"]
    pivot["Savings rate %"] = (pivot["Net"] / pivot["Income"].where(pivot["Income"] > 0) * 100).fillna(0)
    return pivot[["Income", "Expense", "Net", "Savings rate %"]].reset_index()


def budget_status(df: pd.DataFrame, budgets: pd.DataFrame) -> pd.DataFrame:
    """Spending vs. monthly budget for the current month."""
    cols = ["category", "monthly_limit", "spent", "pct", "remaining"]
    if budgets.empty:
        return pd.DataFrame(columns=cols)
    month = filter_period(df, "This month")
    spent = (
        month[month["type"] == "Expense"].groupby("category")["amount"].sum().rename("spent")
    )
    out = budgets.merge(spent, how="left", left_on="category", right_index=True)
    out["spent"] = out["spent"].fillna(0.0)
    out["pct"] = out["spent"] / out["monthly_limit"] * 100
    out["remaining"] = out["monthly_limit"] - out["spent"]
    return out[cols].sort_values("pct", ascending=False).reset_index(drop=True)


def month_end_forecast(df: pd.DataFrame) -> dict:
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month = filter_period(df, "This month")
    spent = float(month.loc[month["type"] == "Expense", "amount"].sum())
    projected = spent / today.day * days_in_month if today.day else spent
    return {"spent": spent, "projected": projected, "day": today.day, "days_in_month": days_in_month}
