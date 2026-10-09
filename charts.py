"""Plotly chart builders."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

INCOME_COLOR = "#00b894"
EXPENSE_COLOR = "#e17055"
ACCENT = "#6c5ce7"


def _tidy(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def income_vs_expense(df: pd.DataFrame) -> go.Figure:
    d = df.copy()
    d["Month"] = d["date"].dt.to_period("M").astype(str)
    g = d.groupby(["Month", "type"], as_index=False)["amount"].sum()
    fig = px.bar(
        g, x="Month", y="amount", color="type", barmode="group",
        color_discrete_map={"Income": INCOME_COLOR, "Expense": EXPENSE_COLOR},
        title="Income vs Expense by month",
    )
    fig.update_layout(yaxis_title=None, xaxis_title=None, legend_title=None)
    return _tidy(fig)


def expense_donut(df: pd.DataFrame) -> go.Figure:
    g = df[df["type"] == "Expense"].groupby("category", as_index=False)["amount"].sum()
    fig = px.pie(g, names="category", values="amount", hole=0.55, title="Where the money goes")
    fig.update_traces(textposition="inside", textinfo="percent")
    fig.update_layout(legend=dict(font=dict(size=11)))
    return _tidy(fig)


def top_categories(df: pd.DataFrame, n: int = 8) -> go.Figure:
    g = (
        df[df["type"] == "Expense"].groupby("category", as_index=False)["amount"].sum()
        .sort_values("amount", ascending=True).tail(n)
    )
    fig = px.bar(g, x="amount", y="category", orientation="h", title=f"Top {n} expense categories")
    fig.update_traces(marker_color=EXPENSE_COLOR)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _tidy(fig)


def balance_curve(df: pd.DataFrame) -> go.Figure:
    d = df.copy()
    d["signed"] = d["amount"].where(d["type"] == "Income", -d["amount"])
    daily = d.groupby("date", as_index=False)["signed"].sum().sort_values("date")
    daily["Cumulative net"] = daily["signed"].cumsum()
    fig = px.area(daily, x="date", y="Cumulative net", title="Cumulative net (income − expenses)")
    fig.update_traces(line_color=ACCENT, fillcolor="rgba(108,92,231,0.18)")
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _tidy(fig)


def weekday_spending(df: pd.DataFrame) -> go.Figure:
    d = df[df["type"] == "Expense"].copy()
    d["weekday"] = d["date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    g = d.groupby("weekday", as_index=False)["amount"].sum()
    fig = px.bar(g, x="weekday", y="amount", title="Spending by weekday",
                 category_orders={"weekday": order})
    fig.update_traces(marker_color=ACCENT)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _tidy(fig)


def category_month_heatmap(df: pd.DataFrame) -> go.Figure:
    d = df[df["type"] == "Expense"].copy()
    d["Month"] = d["date"].dt.to_period("M").astype(str)
    pivot = d.pivot_table(index="category", columns="Month", values="amount",
                          aggfunc="sum", fill_value=0)
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="Purples",
                    title="Expense heatmap · category × month")
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    return _tidy(fig, height=420)


def budget_bars(status: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=status["category"], y=status["monthly_limit"], name="Budget",
                marker_color="rgba(108,92,231,0.35)")
    fig.add_bar(x=status["category"], y=status["spent"], name="Spent", marker_color=EXPENSE_COLOR)
    fig.update_layout(barmode="overlay", title="Budget vs actual (this month)")
    return _tidy(fig)
