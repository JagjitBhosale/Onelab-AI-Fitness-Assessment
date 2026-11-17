"""Tests for reports module."""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import reconciliation as recon_module
from app.reconciliation import reconcile
from app.reports import generate_report, generate_monthly_totals, export_discrepancies_csv

COMPANY_FIELDS = [
    "transaction_id", "transaction_date", "amount", "transaction_type",
    "payment_status", "merchant", "settlement_ref", "refund_ref", "description",
]
BANK_FIELDS = [
    "settlement_ref", "transaction_id", "settlement_date", "amount",
    "transaction_type", "bank_status", "bank_reference", "description",
]


@pytest.fixture(autouse=True)
def _use_tmp_data_dir(tmp_path, monkeypatch):
    data_dir = str(tmp_path / "data")
    os.makedirs(data_dir, exist_ok=True)
    monkeypatch.setattr(recon_module, "DATA_DIR", data_dir)
    # Also patch reports module's import path
    from app import reports as reports_mod
    monkeypatch.setattr(reports_mod, "load_company_transactions", recon_module.load_company_transactions)
    monkeypatch.setattr(reports_mod, "load_bank_settlements", recon_module.load_bank_settlements)
    return data_dir


def _write_csvs(data_dir, company_rows, bank_rows):
    with open(os.path.join(data_dir, "company_transactions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COMPANY_FIELDS)
        w.writeheader()
        w.writerows(company_rows)
    with open(os.path.join(data_dir, "bank_settlements.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BANK_FIELDS)
        w.writeheader()
        w.writerows(bank_rows)


def test_generate_report(_use_tmp_data_dir):
    _write_csvs(
        _use_tmp_data_dir,
        [dict(transaction_id="TXN-1", transaction_date="2026-11-10 12:00:00",
              amount="100.00", transaction_type="payment", payment_status="settled",
              merchant="X", settlement_ref="STL-1", refund_ref="", description="t")],
        [dict(settlement_ref="STL-1", transaction_id="TXN-1",
              settlement_date="2026-11-11 12:00:00", amount="100.00",
              transaction_type="payment", bank_status="cleared",
              bank_reference="BNK-1", description="s")],
    )
    result = reconcile()
    report = generate_report(result)
    assert "Reconciliation completed" in report.explanation
    assert report.summary.matched_count == 1


def test_monthly_totals(_use_tmp_data_dir):
    _write_csvs(
        _use_tmp_data_dir,
        [dict(transaction_id="TXN-1", transaction_date="2026-10-15 12:00:00",
              amount="200.00", transaction_type="payment", payment_status="settled",
              merchant="X", settlement_ref="STL-1", refund_ref="", description="t"),
         dict(transaction_id="TXN-2", transaction_date="2026-11-15 12:00:00",
              amount="300.00", transaction_type="payment", payment_status="settled",
              merchant="X", settlement_ref="STL-2", refund_ref="", description="t")],
        [dict(settlement_ref="STL-1", transaction_id="TXN-1",
              settlement_date="2026-10-16 12:00:00", amount="200.00",
              transaction_type="payment", bank_status="cleared",
              bank_reference="BNK-1", description="s")],
    )
    totals = generate_monthly_totals()
    assert len(totals) >= 1
    months = [t.month for t in totals]
    assert "2026-10" in months


def test_export_csv(_use_tmp_data_dir):
    _write_csvs(
        _use_tmp_data_dir,
        [dict(transaction_id="TXN-1", transaction_date="2026-11-10 12:00:00",
              amount="100.00", transaction_type="payment", payment_status="settled",
              merchant="X", settlement_ref="", refund_ref="", description="unmatched")],
        [],
    )
    result = reconcile()
    csv_str = export_discrepancies_csv(result.discrepancies)
    assert "TXN-1" in csv_str
    assert "unmatched_company" in csv_str
