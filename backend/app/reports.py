"""
ReconAI - Reports Module
Report generation, CSV export, and monthly totals.
"""

import csv
import io
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from .models import (
    DiscrepancyCategory,
    DiscrepancyRecord,
    MonthlyTotal,
    ReconciliationResult,
    ReportResponse,
)
from .reconciliation import (
    _safe_decimal,
    _safe_parse_date,
    load_bank_settlements,
    load_company_transactions,
)


def generate_monthly_totals() -> List[MonthlyTotal]:
    """Calculate monthly reconciliation totals."""
    company_txns = load_company_transactions()
    bank_stls = load_bank_settlements()

    # Aggregate by month
    company_monthly = defaultdict(lambda: {"total": Decimal("0.00"), "count": 0})
    bank_monthly = defaultdict(lambda: {"total": Decimal("0.00"), "count": 0})

    for txn in company_txns:
        date = _safe_parse_date(txn.get("transaction_date", ""))
        if date:
            month_key = date.strftime("%Y-%m")
            company_monthly[month_key]["total"] += _safe_decimal(txn.get("amount", "0"))
            company_monthly[month_key]["count"] += 1

    for stl in bank_stls:
        date = _safe_parse_date(stl.get("settlement_date", ""))
        if date:
            month_key = date.strftime("%Y-%m")
            bank_monthly[month_key]["total"] += _safe_decimal(stl.get("amount", "0"))
            bank_monthly[month_key]["count"] += 1

    all_months = sorted(set(list(company_monthly.keys()) + list(bank_monthly.keys())))

    monthly_totals = []
    for month in all_months:
        c_total = company_monthly[month]["total"]
        b_total = bank_monthly[month]["total"]
        diff = (c_total - b_total).copy_abs()
        c_count = company_monthly[month]["count"]
        b_count = bank_monthly[month]["count"]

        monthly_totals.append(MonthlyTotal(
            month=month,
            company_total=str(c_total),
            bank_total=str(b_total),
            difference=str(diff),
            matched_count=min(c_count, b_count),
            unmatched_count=abs(c_count - b_count)
        ))

    return monthly_totals


def generate_report(result: ReconciliationResult) -> ReportResponse:
    """Generate a full reconciliation report with explanation."""
    monthly_totals = generate_monthly_totals()

    # Build explanation
    s = result.summary
    explanations = []
    explanations.append(
        f"Reconciliation completed at {s.generated_at}. "
        f"Processed {s.total_company_transactions} company transactions and "
        f"{s.total_bank_settlements} bank settlements."
    )

    if s.matched_count > 0:
        explanations.append(
            f"✅ {s.matched_count} transactions matched perfectly between company and bank records."
        )

    if s.timing_difference_count > 0:
        explanations.append(
            f"⏱️ {s.timing_difference_count} transaction(s) have timing differences "
            f"(cross-month settlements). These are legitimate settlements that occurred "
            f"in a different month than the transaction date."
        )

    if s.rounding_difference_count > 0:
        explanations.append(
            f"🔢 {s.rounding_difference_count} transaction(s) have small rounding differences "
            f"(< $0.10). These may be due to currency conversion or bank processing."
        )

    if s.duplicate_count > 0:
        explanations.append(
            f"⚠️ {s.duplicate_count} duplicate entry/entries detected in bank settlements. "
            f"These should be investigated and corrected."
        )

    if s.orphan_refund_count > 0:
        explanations.append(
            f"🔍 {s.orphan_refund_count} orphan refund(s) found in bank records with no "
            f"corresponding original transaction. These require investigation."
        )

    if s.unmatched_company_count > 0:
        explanations.append(
            f"❌ {s.unmatched_company_count} company transaction(s) have no matching bank settlement."
        )

    if s.unmatched_bank_count > 0:
        explanations.append(
            f"❌ {s.unmatched_bank_count} bank settlement(s) have no matching company transaction."
        )

    total_diff = _safe_decimal(s.total_amount_difference)
    if total_diff > Decimal("0.00"):
        explanations.append(
            f"\n💰 Total amount difference: ${s.total_amount_difference}. "
            f"Company total: ${s.total_company_amount}, Bank total: ${s.total_bank_amount}."
        )

    explanations.append(
        f"\n📊 Reconciliation success rate: {s.reconciliation_success_rate}%"
    )

    return ReportResponse(
        summary=s,
        monthly_totals=monthly_totals,
        explanation="\n\n".join(explanations)
    )


def export_discrepancies_csv(discrepancies: List[DiscrepancyRecord]) -> str:
    """Export discrepancies to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Transaction ID", "Company Amount", "Bank Amount",
        "Transaction Date", "Settlement Date", "Difference",
        "Category", "Explanation"
    ])

    for d in discrepancies:
        writer.writerow([
            d.transaction_id,
            d.company_amount or "N/A",
            d.bank_amount or "N/A",
            d.transaction_date or "N/A",
            d.settlement_date or "N/A",
            d.difference,
            d.category.value,
            d.explanation
        ])

    return output.getvalue()
