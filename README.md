# 💰 Personal Finance Manager

A multi-page **Streamlit** app to track income & expenses, set monthly budgets, reach savings goals and get smart insights — all stored locally in SQLite.

## ✨ Features
- **Dashboard** – KPI cards, income vs expense, category donut, cumulative net, budget alerts
- **Add Transaction** – single entry form + bulk CSV import (with template)
- **Transactions** – filters, search, multi-delete, CSV export
- **Budgets & Goals** – per-category monthly limits with progress bars, savings goals with "save per month" hints
- **Reports** – key insights, month-end forecast, weekday chart, category × month heatmap, Excel report
- **Recurring** – salary, rent, subscriptions added automatically every month
- **Edit in place** – fix any transaction directly in the table
- **Settings** – backup, demo data, reset
- **Optional password** – set `APP_PASSWORD` (see `.streamlit/secrets.toml.example`)
- Multi-currency label (EGP, USD, EUR, SAR, AED, GBP)

## 🚀 Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Click **Load demo data** on the home page to explore with 6 months of sample data.

## ☁️ Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repository
2. Go to https://share.streamlit.io → **New app**
3. Select the repo, branch `main`, main file `app.py` → **Deploy**

> Note: Community Cloud storage is ephemeral — the SQLite file may reset on restart. Use **Settings → Download backup** regularly.

## 🧪 Tests & Docker
```bash
pip install -r requirements-dev.txt && pytest -q      # unit tests (also run by GitHub Actions)
docker build -t finance-manager . && docker run -p 8501:8501 finance-manager
```

## 🗂️ Structure
```
app.py                 # Dashboard
pages/                 # Add, Transactions, Budgets & Goals, Reports, Recurring, Settings
utils/auth.py          # optional password gate
tests/                 # pytest suite
.github/workflows/     # CI
utils/db.py            # SQLite layer
utils/analysis.py      # KPIs, budgets, forecast
utils/charts.py        # Plotly charts
utils/ui.py            # Styling & shared UI
.streamlit/config.toml # Theme
```
