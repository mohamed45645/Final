"""SQLite data layer for the Personal Finance Manager."""
from __future__ import annotations

import random
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finance.db"

EXPENSE_CATEGORIES = [
    "🛒 Groceries", "🏠 Rent & Bills", "🚗 Transport", "🍽️ Dining Out",
    "🎬 Entertainment", "🏥 Health", "📚 Education", "👕 Shopping",
    "✈️ Travel", "💡 Utilities", "🎁 Gifts & Charity", "📦 Other",
]
INCOME_CATEGORIES = [
    "💼 Salary", "💻 Freelance", "📈 Investments", "🎁 Gifts", "🏷️ Other Income",
]


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('Income','Expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                note TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL CHECK (monthly_limit > 0)
            );
            CREATE TABLE IF NOT EXISTS recurring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('Income','Expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 28),
                active INTEGER NOT NULL DEFAULT 1,
                last_applied TEXT
            );
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target REAL NOT NULL CHECK (target > 0),
                saved REAL NOT NULL DEFAULT 0,
                deadline TEXT
            );
            """
        )


# ----------------------------------------------------------------- transactions
def add_transaction(d: date, t_type: str, category: str, amount: float, note: str = "") -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO transactions (date, type, category, amount, note) VALUES (?,?,?,?,?)",
            (d.isoformat(), t_type, category, float(amount), note.strip()),
        )


def get_transactions() -> pd.DataFrame:
    with connect() as c:
        df = pd.read_sql_query(
            "SELECT id, date, type, category, amount, note FROM transactions "
            "ORDER BY date DESC, id DESC",
            c,
        )
    df["date"] = pd.to_datetime(df["date"])
    return df


def delete_transactions(ids) -> int:
    ids = [(int(i),) for i in ids]
    with connect() as c:
        c.executemany("DELETE FROM transactions WHERE id = ?", ids)
    return len(ids)


def update_transactions(rows) -> int:
    """rows: iterable of (id, date, type, category, amount, note)."""
    data = [(d.isoformat() if hasattr(d, "isoformat") else str(d)[:10], t, c, float(a), n or "", int(i))
            for i, d, t, c, a, n in rows]
    with connect() as c:
        c.executemany(
            "UPDATE transactions SET date=?, type=?, category=?, amount=?, note=? WHERE id=?", data
        )
    return len(data)


def import_transactions(df: pd.DataFrame) -> int:
    """Import rows with columns: date, type, category, amount, note(optional)."""
    df = df.rename(columns=lambda x: str(x).strip().lower())
    missing = {"date", "type", "category", "amount"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["type"] = df["type"].astype(str).str.strip().str.capitalize()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "note" not in df.columns:
        df["note"] = ""
    df["note"] = df["note"].fillna("").astype(str)
    df = df.dropna(subset=["date", "amount", "category"])
    df = df[df["type"].isin(["Income", "Expense"]) & (df["amount"] > 0)]
    rows = [
        (r.date.date().isoformat(), r.type, str(r.category), float(r.amount), r.note)
        for r in df.itertuples()
    ]
    with connect() as c:
        c.executemany(
            "INSERT INTO transactions (date, type, category, amount, note) VALUES (?,?,?,?,?)",
            rows,
        )
    return len(rows)


# --------------------------------------------------------------------- budgets
def set_budget(category: str, limit: float) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, float(limit)),
        )


def get_budgets() -> pd.DataFrame:
    with connect() as c:
        return pd.read_sql_query("SELECT category, monthly_limit FROM budgets", c)


def delete_budget(category: str) -> None:
    with connect() as c:
        c.execute("DELETE FROM budgets WHERE category = ?", (category,))


# ----------------------------------------------------------------------- goals
def add_goal(name: str, target: float, deadline: date | None) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO goals (name, target, saved, deadline) VALUES (?,?,0,?)",
            (name.strip(), float(target), deadline.isoformat() if deadline else None),
        )


def get_goals() -> pd.DataFrame:
    with connect() as c:
        return pd.read_sql_query("SELECT id, name, target, saved, deadline FROM goals", c)


def add_to_goal(goal_id: int, amount: float) -> None:
    with connect() as c:
        c.execute("UPDATE goals SET saved = saved + ? WHERE id = ?", (float(amount), int(goal_id)))


def delete_goal(goal_id: int) -> None:
    with connect() as c:
        c.execute("DELETE FROM goals WHERE id = ?", (int(goal_id),))


# ------------------------------------------------------------------- recurring
def add_recurring(name: str, t_type: str, category: str, amount: float, day: int) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO recurring (name, type, category, amount, day) VALUES (?,?,?,?,?)",
            (name.strip(), t_type, category, float(amount), int(day)),
        )


def get_recurring() -> pd.DataFrame:
    with connect() as c:
        return pd.read_sql_query(
            "SELECT id, name, type, category, amount, day, active, last_applied FROM recurring", c
        )


def set_recurring_active(rec_id: int, active: bool) -> None:
    with connect() as c:
        c.execute("UPDATE recurring SET active=? WHERE id=?", (int(active), int(rec_id)))


def delete_recurring(rec_id: int) -> None:
    with connect() as c:
        c.execute("DELETE FROM recurring WHERE id = ?", (int(rec_id),))


def apply_recurring(today: date | None = None) -> int:
    """Create this month's transaction for every active recurring item that is due."""
    today = today or date.today()
    month_key = today.strftime("%Y-%m")
    created = 0
    with connect() as c:
        due = c.execute(
            "SELECT id, name, type, category, amount, day FROM recurring "
            "WHERE active = 1 AND day <= ? AND (last_applied IS NULL OR last_applied <> ?)",
            (today.day, month_key),
        ).fetchall()
        for rid, name, t, cat, amt, day in due:
            c.execute(
                "INSERT INTO transactions (date, type, category, amount, note) VALUES (?,?,?,?,?)",
                (date(today.year, today.month, day).isoformat(), t, cat, amt, f"🔁 {name}"),
            )
            c.execute("UPDATE recurring SET last_applied=? WHERE id=?", (month_key, rid))
            created += 1
    return created


# ------------------------------------------------------------------- utilities
def clear_all() -> None:
    with connect() as c:
        c.executescript("DELETE FROM transactions; DELETE FROM budgets; DELETE FROM goals; DELETE FROM recurring;")


def seed_demo_data(days: int = 180) -> None:
    """Fill the database with ~6 months of realistic demo data."""
    rnd = random.Random(42)
    today = date.today()
    rows = []

    def add(d, t, cat, lo, hi, note=""):
        rows.append((d.isoformat(), t, cat, round(rnd.uniform(lo, hi), 2), note))

    for i in range(days, -1, -1):
        d = today - timedelta(days=i)
        if d.day == 1:
            add(d, "Income", "💼 Salary", 14500, 15500, "Monthly salary")
        if d.day == 15 and rnd.random() < 0.6:
            add(d, "Income", "💻 Freelance", 1500, 4500, "Side project")
        if d.day == 20 and rnd.random() < 0.3:
            add(d, "Income", "📈 Investments", 200, 900, "Dividends")
        if d.day == 3:
            add(d, "Expense", "🏠 Rent & Bills", 4800, 5000, "Rent")
        if d.day == 10:
            add(d, "Expense", "💡 Utilities", 350, 700, "Electricity & internet")
        if rnd.random() < 0.35:
            add(d, "Expense", "🛒 Groceries", 150, 550, "Supermarket")
        if rnd.random() < 0.55:
            add(d, "Expense", "🚗 Transport", 30, 140, "Fuel / ride")
        if rnd.random() < 0.28:
            add(d, "Expense", "🍽️ Dining Out", 90, 420, "Restaurant")
        if rnd.random() < 0.12:
            add(d, "Expense", "🎬 Entertainment", 100, 450, "Cinema / games")
        if rnd.random() < 0.08:
            add(d, "Expense", "👕 Shopping", 250, 1200, "Clothes")
        if rnd.random() < 0.04:
            add(d, "Expense", "🏥 Health", 150, 900, "Pharmacy / clinic")
        if rnd.random() < 0.03:
            add(d, "Expense", "📚 Education", 200, 1200, "Course / books")
        if rnd.random() < 0.012:
            add(d, "Expense", "✈️ Travel", 2500, 6000, "Trip")

    with connect() as c:
        c.executemany(
            "INSERT INTO transactions (date, type, category, amount, note) VALUES (?,?,?,?,?)",
            rows,
        )
        if c.execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)",
                [("🛒 Groceries", 3500), ("🍽️ Dining Out", 1500), ("🚗 Transport", 1200),
                 ("🎬 Entertainment", 800), ("👕 Shopping", 1500)],
            )
        if c.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO goals (name, target, saved, deadline) VALUES (?,?,?,?)",
                [("Emergency fund", 30000, 12500, (today + timedelta(days=240)).isoformat()),
                 ("New laptop", 25000, 9000, (today + timedelta(days=120)).isoformat()),
                 ("Summer trip", 40000, 6000, (today + timedelta(days=300)).isoformat())],
            )
