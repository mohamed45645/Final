import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import analysis, db  # noqa: E402


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


def test_add_and_read_transaction():
    db.add_transaction(date(2026, 1, 5), "Expense", "🛒 Groceries", 120.5, "milk")
    df = db.get_transactions()
    assert len(df) == 1 and df.loc[0, "amount"] == 120.5


def test_update_and_delete():
    db.add_transaction(date(2026, 1, 5), "Expense", "🛒 Groceries", 10, "")
    tid = int(db.get_transactions().loc[0, "id"])
    db.update_transactions([(tid, date(2026, 1, 6), "Income", "💼 Salary", 99, "fix")])
    row = db.get_transactions().loc[0]
    assert row["type"] == "Income" and row["amount"] == 99
    db.delete_transactions([tid])
    assert db.get_transactions().empty


def test_summarize():
    db.add_transaction(date(2026, 1, 1), "Income", "💼 Salary", 1000)
    db.add_transaction(date(2026, 1, 2), "Expense", "🛒 Groceries", 250)
    s = analysis.summarize(db.get_transactions())
    assert s["net"] == 750 and s["savings_rate"] == 75


def test_import_validation():
    good = pd.DataFrame([{"Date": "2026-02-01", "Type": "expense", "Category": "x", "Amount": 5}])
    bad = pd.DataFrame([{"date": "2026-02-01"}])
    assert db.import_transactions(good) == 1
    with pytest.raises(ValueError):
        db.import_transactions(bad)


def test_budget_status_current_month():
    today = date.today()
    db.add_transaction(today, "Expense", "🛒 Groceries", 80)
    db.set_budget("🛒 Groceries", 100)
    st = analysis.budget_status(db.get_transactions(), db.get_budgets())
    assert round(st.loc[0, "pct"]) == 80


def test_recurring_applied_once_per_month():
    db.add_recurring("Rent", "Expense", "🏠 Rent & Bills", 1000, 1)
    assert db.apply_recurring(date(2026, 3, 10)) == 1
    assert db.apply_recurring(date(2026, 3, 20)) == 0   # same month: no duplicate
    assert db.apply_recurring(date(2026, 4, 2)) == 1    # next month
    assert len(db.get_transactions()) == 2


def test_seed_and_clear():
    db.seed_demo_data()
    assert len(db.get_transactions()) > 100
    db.clear_all()
    assert db.get_transactions().empty and db.get_goals().empty
