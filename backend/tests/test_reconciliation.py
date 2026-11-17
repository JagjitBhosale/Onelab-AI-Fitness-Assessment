"""
Tests for the reconciliation engine.
Covers: exact matches, next-month settlements, rounding differences,
duplicate records, orphan refunds, and missing settlements.
"""

import csv
import os
import sys
import tempfile
import shutil
from decimal import Decimal

import pytest

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import DiscrepancyCategory
from app import reconciliation as recon_module
from app.reconciliation import reconcile, _safe_decimal, _safe_parse_date, _is_cross_month


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    """Redirect DATA_DIR to a temp folder for every test."""
    data_dir = str(tmp_path / "data")
    os.makedirs(data_dir, exist_ok=True)
    monkeypatch.setattr(recon_module, "DATA_DIR", data_dir)
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


def _company_row(txn_id="TXN-001", date="2026-11-10 12:00:00", amount="100.00",
                 txn_type="payment", status="settled", merchant="TestCo",
                 stl_ref="STL-001", refund_ref="", desc="test"):
    return dict(transaction_id=txn_id, transaction_date=date, amount=amount,
                transaction_type=txn_type, payment_status=status, merchant=merchant,
                settlement_ref=stl_ref, refund_ref=refund_ref, description=desc)


def _bank_row(stl_ref="STL-001", txn_id="TXN-001", date="2026-11-11 12:00:00",
              amount="100.00", txn_type="payment", status="cleared",
              bank_ref="BNK-001", desc="settlement"):
    return dict(settlement_ref=stl_ref, transaction_id=txn_id, settlement_date=date,
                amount=amount, transaction_type=txn_type, bank_status=status,
                bank_reference=bank_ref, description=desc)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExactMatch:
    def test_single_exact_match(self, _use_tmp_data_dir):
        _write_csvs(_use_tmp_data_dir,
                     [_company_row()],
                     [_bank_row()])
        result = reconcile()
        assert result.summary.matched_count == 1
        assert len(result.discrepancies) == 0

    def test_multiple_exact_matches(self, _use_tmp_data_dir):
        rows_c, rows_b = [], []
        for i in range(5):
            rows_c.append(_company_row(txn_id=f"TXN-{i}", stl_ref=f"STL-{i}", amount="250.00"))
            rows_b.append(_bank_row(stl_ref=f"STL-{i}", txn_id=f"TXN-{i}", amount="250.00"))
        _write_csvs(_use_tmp_data_dir, rows_c, rows_b)
        result = reconcile()
        assert result.summary.matched_count == 5
        assert len(result.discrepancies) == 0


class TestNextMonthSettlement:
    def test_cross_month_detected(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(date="2026-11-28 14:00:00", amount="1000.00")],
            [_bank_row(date="2026-12-03 10:00:00", amount="1000.00")],
        )
        result = reconcile()
        timing = [d for d in result.discrepancies
                  if d.category == DiscrepancyCategory.TIMING_DIFFERENCE]
        assert len(timing) == 1
        assert "cross-month" in timing[0].explanation.lower()
        # It should NOT be classified as unmatched
        unmatched = [d for d in result.discrepancies
                     if d.category == DiscrepancyCategory.UNMATCHED_COMPANY]
        assert len(unmatched) == 0


class TestRoundingDifference:
    def test_small_rounding_detected(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(amount="500.00")],
            [_bank_row(amount="500.03")],
        )
        result = reconcile()
        rounding = [d for d in result.discrepancies
                    if d.category == DiscrepancyCategory.ROUNDING_DIFFERENCE]
        assert len(rounding) == 1
        assert rounding[0].difference == "0.03"

    def test_large_difference_not_rounding(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(amount="500.00")],
            [_bank_row(amount="510.00")],
        )
        result = reconcile()
        rounding = [d for d in result.discrepancies
                    if d.category == DiscrepancyCategory.ROUNDING_DIFFERENCE]
        assert len(rounding) == 0


class TestDuplicateRecords:
    def test_duplicate_bank_entry(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row()],
            [_bank_row(), _bank_row(bank_ref="BNK-DUP")],
        )
        result = reconcile()
        duplicates = [d for d in result.discrepancies
                      if d.category == DiscrepancyCategory.DUPLICATE_ENTRY]
        assert len(duplicates) >= 1


class TestOrphanRefund:
    def test_orphan_refund_detected(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [],  # no company transactions
            [_bank_row(txn_id="TXN-ORPHAN", txn_type="refund",
                       desc="Refund for original TXN-MISSING - orphan")],
        )
        result = reconcile()
        orphans = [d for d in result.discrepancies
                   if d.category == DiscrepancyCategory.ORPHAN_REFUND]
        assert len(orphans) == 1
        assert "orphan" in orphans[0].explanation.lower()


class TestMissingSettlement:
    def test_company_txn_no_bank(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(txn_id="TXN-MISS", stl_ref="STL-MISS")],
            [],
        )
        result = reconcile()
        unmatched = [d for d in result.discrepancies
                     if d.category == DiscrepancyCategory.UNMATCHED_COMPANY]
        assert len(unmatched) == 1

    def test_bank_stl_no_company(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [],
            [_bank_row(txn_id="TXN-BANKONLY")],
        )
        result = reconcile()
        unmatched = [d for d in result.discrepancies
                     if d.category == DiscrepancyCategory.UNMATCHED_BANK]
        assert len(unmatched) == 1


class TestEdgeCases:
    def test_empty_datasets(self, _use_tmp_data_dir):
        _write_csvs(_use_tmp_data_dir, [], [])
        result = reconcile()
        assert result.summary.matched_count == 0
        assert result.summary.total_company_transactions == 0

    def test_invalid_amounts(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(amount="invalid")],
            [_bank_row(amount="")],
        )
        result = reconcile()
        # Should handle gracefully without crashing
        assert result.summary.total_company_transactions == 1

    def test_missing_dates(self, _use_tmp_data_dir):
        _write_csvs(
            _use_tmp_data_dir,
            [_company_row(date="")],
            [_bank_row(date="")],
        )
        result = reconcile()
        assert result.summary.total_company_transactions == 1


class TestSafeDecimal:
    def test_normal(self):
        assert _safe_decimal("123.45") == Decimal("123.45")

    def test_empty(self):
        assert _safe_decimal("") == Decimal("0.00")

    def test_none(self):
        assert _safe_decimal(None) == Decimal("0.00")

    def test_invalid(self):
        assert _safe_decimal("abc") == Decimal("0.00")


class TestSafeParseDate:
    def test_standard_format(self):
        d = _safe_parse_date("2026-11-10 12:00:00")
        assert d is not None
        assert d.year == 2026

    def test_empty(self):
        assert _safe_parse_date("") is None

    def test_none(self):
        assert _safe_parse_date(None) is None


class TestCrossMonth:
    def test_same_month(self):
        from datetime import datetime
        d1 = datetime(2026, 11, 1)
        d2 = datetime(2026, 11, 30)
        assert _is_cross_month(d1, d2) is False

    def test_different_month(self):
        from datetime import datetime
        d1 = datetime(2026, 11, 28)
        d2 = datetime(2026, 12, 3)
        assert _is_cross_month(d1, d2) is True
