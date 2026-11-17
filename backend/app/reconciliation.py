"""
ReconAI - Reconciliation Engine
Core matching and discrepancy detection logic using Decimal arithmetic.
"""

import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, List, Optional, Tuple

from .models import (
    DiscrepancyCategory,
    DiscrepancyRecord,
    ReconciliationResult,
    ReconciliationSummary,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Threshold for rounding differences (in absolute value)
ROUNDING_THRESHOLD = Decimal("0.10")
# Threshold for timing differences (in days)
TIMING_THRESHOLD_DAYS = 45


def _safe_decimal(value: str) -> Decimal:
    """Safely parse a string to Decimal, returning 0 for invalid values."""
    try:
        if value is None or str(value).strip() == "":
            return Decimal("0.00")
        return Decimal(str(value).strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def _safe_parse_date(date_str: str) -> Optional[datetime]:
    """Safely parse date string in multiple formats."""
    if not date_str or str(date_str).strip() == "":
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def load_company_transactions() -> List[Dict]:
    """Load company transactions from CSV."""
    path = os.path.join(DATA_DIR, "company_transactions.csv")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def load_bank_settlements() -> List[Dict]:
    """Load bank settlements from CSV."""
    path = os.path.join(DATA_DIR, "bank_settlements.csv")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def _detect_duplicates(records: List[Dict], id_field: str) -> Dict[str, int]:
    """Detect duplicate transaction IDs and return counts."""
    id_counts = Counter(r.get(id_field, "") for r in records if r.get(id_field, ""))
    return {tid: count for tid, count in id_counts.items() if count > 1}


def _is_cross_month(date1: Optional[datetime], date2: Optional[datetime]) -> bool:
    """Check if two dates are in different months."""
    if date1 is None or date2 is None:
        return False
    return (date1.year, date1.month) != (date2.year, date2.month)


def reconcile() -> ReconciliationResult:
    """
    Main reconciliation logic.
    Matches company transactions against bank settlements and classifies discrepancies.
    """
    company_txns = load_company_transactions()
    bank_stls = load_bank_settlements()

    # Build lookup indices
    # Company: index by transaction_id
    company_by_txn_id = {}
    for txn in company_txns:
        tid = txn.get("transaction_id", "").strip()
        if tid:
            if tid not in company_by_txn_id:
                company_by_txn_id[tid] = []
            company_by_txn_id[tid].append(txn)

    # Company: also index by settlement_ref
    company_by_stl_ref = {}
    for txn in company_txns:
        sref = txn.get("settlement_ref", "").strip()
        if sref:
            if sref not in company_by_stl_ref:
                company_by_stl_ref[sref] = []
            company_by_stl_ref[sref].append(txn)

    # Bank: index by transaction_id
    bank_by_txn_id = defaultdict(list)
    for stl in bank_stls:
        tid = stl.get("transaction_id", "").strip()
        if tid:
            bank_by_txn_id[tid].append(stl)

    # Bank: also index by settlement_ref
    bank_by_stl_ref = defaultdict(list)
    for stl in bank_stls:
        sref = stl.get("settlement_ref", "").strip()
        if sref:
            bank_by_stl_ref[sref].append(stl)

    # Detect duplicates
    bank_duplicates = _detect_duplicates(bank_stls, "transaction_id")
    company_duplicates = _detect_duplicates(company_txns, "transaction_id")

    discrepancies: List[DiscrepancyRecord] = []
    matched_records: List[DiscrepancyRecord] = []
    matched_company_ids = set()
    matched_bank_indices = set()

    # --- Phase 1: Match company transactions to bank settlements ---
    for txn in company_txns:
        txn_id = txn.get("transaction_id", "").strip()
        stl_ref = txn.get("settlement_ref", "").strip()
        company_amount = _safe_decimal(txn.get("amount", "0"))
        txn_date = _safe_parse_date(txn.get("transaction_date", ""))

        # Try to find matching bank record by transaction_id first, then settlement_ref
        bank_matches = bank_by_txn_id.get(txn_id, [])
        if not bank_matches and stl_ref:
            bank_matches = bank_by_stl_ref.get(stl_ref, [])

        if not bank_matches:
            # No match found - unmatched company transaction
            discrepancies.append(DiscrepancyRecord(
                transaction_id=txn_id,
                company_amount=str(company_amount),
                bank_amount=None,
                transaction_date=txn.get("transaction_date", ""),
                settlement_date=None,
                difference=str(company_amount),
                category=DiscrepancyCategory.UNMATCHED_COMPANY,
                explanation=f"Company transaction {txn_id} has no matching bank settlement."
            ))
            continue

        # Check for duplicates in bank records
        if txn_id in bank_duplicates:
            # Mark duplicates - first occurrence is the real one, rest are duplicates
            first_match = bank_matches[0]
            bank_amount = _safe_decimal(first_match.get("amount", "0"))
            settle_date = _safe_parse_date(first_match.get("settlement_date", ""))
            diff = (company_amount - bank_amount).copy_abs()

            for dup_match in bank_matches[1:]:
                dup_amount = _safe_decimal(dup_match.get("amount", "0"))
                bank_idx = bank_stls.index(dup_match)
                matched_bank_indices.add(bank_idx)
                discrepancies.append(DiscrepancyRecord(
                    transaction_id=txn_id,
                    company_amount=str(company_amount),
                    bank_amount=str(dup_amount),
                    transaction_date=txn.get("transaction_date", ""),
                    settlement_date=dup_match.get("settlement_date", ""),
                    difference=str(dup_amount),
                    category=DiscrepancyCategory.DUPLICATE_ENTRY,
                    explanation=f"Duplicate bank settlement found for transaction {txn_id}. "
                               f"Bank ref: {dup_match.get('bank_reference', 'N/A')}."
                ))

            # Process the first (legitimate) match
            bank_match = first_match
        else:
            bank_match = bank_matches[0]

        bank_amount = _safe_decimal(bank_match.get("amount", "0"))
        settle_date = _safe_parse_date(bank_match.get("settlement_date", ""))
        diff = (company_amount - bank_amount).copy_abs()

        bank_idx = bank_stls.index(bank_match)
        matched_company_ids.add(txn_id)
        matched_bank_indices.add(bank_idx)

        # Check for timing difference (cross-month settlement)
        if _is_cross_month(txn_date, settle_date):
            discrepancies.append(DiscrepancyRecord(
                transaction_id=txn_id,
                company_amount=str(company_amount),
                bank_amount=str(bank_amount),
                transaction_date=txn.get("transaction_date", ""),
                settlement_date=bank_match.get("settlement_date", ""),
                difference=str(diff),
                category=DiscrepancyCategory.TIMING_DIFFERENCE,
                explanation=f"Transaction {txn_id} dated {txn.get('transaction_date', '')} "
                           f"settled on {bank_match.get('settlement_date', '')} (cross-month). "
                           f"This is a legitimate timing difference, not a missing transaction."
            ))
            continue

        # Check for rounding difference
        if Decimal("0.00") < diff <= ROUNDING_THRESHOLD:
            discrepancies.append(DiscrepancyRecord(
                transaction_id=txn_id,
                company_amount=str(company_amount),
                bank_amount=str(bank_amount),
                transaction_date=txn.get("transaction_date", ""),
                settlement_date=bank_match.get("settlement_date", ""),
                difference=str(diff),
                category=DiscrepancyCategory.ROUNDING_DIFFERENCE,
                explanation=f"Small rounding difference of {diff} detected for {txn_id}. "
                           f"Company: {company_amount}, Bank: {bank_amount}."
            ))
            continue

        # Exact match
        if diff == Decimal("0.00"):
            matched_records.append(DiscrepancyRecord(
                transaction_id=txn_id,
                company_amount=str(company_amount),
                bank_amount=str(bank_amount),
                transaction_date=txn.get("transaction_date", ""),
                settlement_date=bank_match.get("settlement_date", ""),
                difference="0.00",
                category=DiscrepancyCategory.MATCHED,
                explanation="Transaction fully matched."
            ))
        else:
            # Amount mismatch beyond rounding
            discrepancies.append(DiscrepancyRecord(
                transaction_id=txn_id,
                company_amount=str(company_amount),
                bank_amount=str(bank_amount),
                transaction_date=txn.get("transaction_date", ""),
                settlement_date=bank_match.get("settlement_date", ""),
                difference=str(diff),
                category=DiscrepancyCategory.UNMATCHED_COMPANY,
                explanation=f"Amount mismatch for {txn_id}. "
                           f"Company: {company_amount}, Bank: {bank_amount}, Diff: {diff}."
            ))

    # --- Phase 2: Find unmatched bank settlements ---
    for idx, stl in enumerate(bank_stls):
        if idx in matched_bank_indices:
            continue

        stl_txn_id = stl.get("transaction_id", "").strip()
        stl_ref = stl.get("settlement_ref", "").strip()
        bank_amount = _safe_decimal(stl.get("amount", "0"))
        txn_type = stl.get("transaction_type", "").strip().lower()
        description = stl.get("description", "").lower()

        # Check if this is an orphan refund
        is_refund = txn_type == "refund"
        has_orphan_marker = "orphan" in description
        # Check if the original transaction for this refund exists
        original_exists = stl_txn_id in company_by_txn_id

        if is_refund and (has_orphan_marker or not original_exists):
            discrepancies.append(DiscrepancyRecord(
                transaction_id=stl_txn_id,
                company_amount=None,
                bank_amount=str(bank_amount),
                transaction_date=None,
                settlement_date=stl.get("settlement_date", ""),
                difference=str(bank_amount),
                category=DiscrepancyCategory.ORPHAN_REFUND,
                explanation=f"Orphan refund {stl_txn_id} found in bank records with no matching "
                           f"original transaction in company records. Amount: {bank_amount}."
            ))
        else:
            discrepancies.append(DiscrepancyRecord(
                transaction_id=stl_txn_id or stl_ref,
                company_amount=None,
                bank_amount=str(bank_amount),
                transaction_date=None,
                settlement_date=stl.get("settlement_date", ""),
                difference=str(bank_amount),
                category=DiscrepancyCategory.UNMATCHED_BANK,
                explanation=f"Bank settlement {stl_ref} (txn: {stl_txn_id}) has no matching "
                           f"company transaction."
            ))

    # --- Build summary ---
    total_company_amount = sum((_safe_decimal(t.get("amount", "0")) for t in company_txns), Decimal("0.00"))
    total_bank_amount = sum((_safe_decimal(s.get("amount", "0")) for s in bank_stls), Decimal("0.00"))
    total_diff = (total_company_amount - total_bank_amount).copy_abs()

    # Count categories
    category_counts = Counter(d.category for d in discrepancies)
    matched_count = len(matched_records)

    # Total distinct financial events to reconcile
    unmatched_bank_count = category_counts.get(DiscrepancyCategory.UNMATCHED_BANK, 0)
    orphan_refund_count = category_counts.get(DiscrepancyCategory.ORPHAN_REFUND, 0)
    duplicate_count = category_counts.get(DiscrepancyCategory.DUPLICATE_ENTRY, 0)
    timing_count = category_counts.get(DiscrepancyCategory.TIMING_DIFFERENCE, 0)
    rounding_count = category_counts.get(DiscrepancyCategory.ROUNDING_DIFFERENCE, 0)

    # Reconciled records include exact matches and legitimate timing differences
    reconciled_count = matched_count + timing_count
    total_records = len(company_txns) + unmatched_bank_count + orphan_refund_count + duplicate_count
    success_rate = min(100.0, round((reconciled_count / max(total_records, 1)) * 100, 2))

    summary = ReconciliationSummary(
        total_company_transactions=len(company_txns),
        total_bank_settlements=len(bank_stls),
        matched_count=matched_count,
        unmatched_company_count=category_counts.get(DiscrepancyCategory.UNMATCHED_COMPANY, 0),
        unmatched_bank_count=category_counts.get(DiscrepancyCategory.UNMATCHED_BANK, 0),
        timing_difference_count=category_counts.get(DiscrepancyCategory.TIMING_DIFFERENCE, 0),
        rounding_difference_count=category_counts.get(DiscrepancyCategory.ROUNDING_DIFFERENCE, 0),
        duplicate_count=category_counts.get(DiscrepancyCategory.DUPLICATE_ENTRY, 0),
        orphan_refund_count=category_counts.get(DiscrepancyCategory.ORPHAN_REFUND, 0),
        total_company_amount=str(total_company_amount),
        total_bank_amount=str(total_bank_amount),
        total_amount_difference=str(total_diff),
        reconciliation_success_rate=success_rate,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return ReconciliationResult(
        summary=summary,
        discrepancies=discrepancies,
        matched_records=matched_records
    )
