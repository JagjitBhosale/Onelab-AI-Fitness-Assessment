# ReconAI – Intelligent Payment Reconciliation System

A full-stack payment reconciliation application that compares company transaction records against bank settlement records, identifies discrepancies, and generates actionable reconciliation reports.

![Stack](https://img.shields.io/badge/Frontend-React%20+%20Vite%20+%20Tailwind-blue)
![Stack](https://img.shields.io/badge/Backend-Python%20+%20FastAPI-green)
![Stack](https://img.shields.io/badge/Data-Pandas%20+%20Decimal-orange)

## Features

- **Synthetic Data Generation** – Generates 120+ realistic transactions with intentional discrepancies
- **Smart Reconciliation Engine** – Matches by transaction ID, settlement ref, amounts, and dates using Decimal arithmetic
- **Discrepancy Detection** – Identifies: matched, unmatched, timing differences, rounding differences, duplicates, and orphan refunds
- **Interactive Dashboard** – Summary cards, pie/bar charts, filterable discrepancy table
- **Reports** – Reconciliation summary, monthly totals, CSV export, and plain-English explanations
- **Automated Tests** – Full test suite for all discrepancy types

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- pnpm (or npm)

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Datasets are auto-generated on first run.

### 2. Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:5173` in your browser.

### 3. Run Tests

```bash
cd backend
pytest tests/ -v
```

## Project Structure

```
ReconAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # Pydantic data models
│   │   ├── data_generator.py    # Synthetic dataset generator
│   │   ├── reconciliation.py    # Core reconciliation engine
│   │   ├── reports.py           # Report generation & CSV export
│   │   └── routers/
│   │       ├── data.py          # /api/data endpoints
│   │       ├── reconcile.py     # /api/reconcile endpoints
│   │       └── reports.py       # /api/reports endpoints
│   ├── data/                    # Generated CSV files
│   ├── tests/
│   │   ├── test_reconciliation.py
│   │   ├── test_data_generator.py
│   │   ├── test_reports.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SummaryCards.jsx
│   │   │   ├── Charts.jsx
│   │   │   ├── DiscrepancyTable.jsx
│   │   │   └── Reports.jsx
│   │   └── services/api.js
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/data/generate` | Generate/regenerate datasets |
| GET | `/api/data/company` | Get company transactions |
| GET | `/api/data/bank` | Get bank settlements |
| GET | `/api/reconcile` | Run reconciliation (optional `?category=` filter) |
| GET | `/api/reconcile/categories` | List discrepancy categories |
| GET | `/api/reports` | Full reconciliation report |
| GET | `/api/reports/monthly` | Monthly totals |
| GET | `/api/reports/export/csv` | Download discrepancy CSV |

## Intentional Discrepancies

The synthetic data generator creates these four required discrepancy types:

1. **Next-month settlement** – A November transaction that settles in December (classified as `timing_difference`, not unmatched)
2. **Rounding difference** – 3 transactions with 1–3 cent differences between company and bank amounts
3. **Duplicate entry** – One bank settlement duplicated with a different bank reference
4. **Orphan refund** – A refund in bank records whose original transaction doesn't exist

Plus unmatched company transactions and bank-only settlements for complete coverage.

## Design Decisions

- **Decimal arithmetic** – All financial calculations use Python's `Decimal` type to avoid floating-point errors
- **Separation of concerns** – Reconciliation engine is fully independent of the frontend
- **Graceful error handling** – Invalid amounts, missing fields, and empty datasets are handled without crashes
- **Reproducible data** – Uses `random.seed(42)` for consistent test data (re-generateable via UI button)
