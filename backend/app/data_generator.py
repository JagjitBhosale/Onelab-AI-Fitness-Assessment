"""
ReconAI - Synthetic Data Generator
Generates realistic company transactions and bank settlement datasets
with intentional discrepancies for reconciliation testing.
"""

import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _generate_transaction_id() -> str:
    return f"TXN-{uuid.uuid4().hex[:8].upper()}"


def _generate_settlement_ref() -> str:
    return f"STL-{uuid.uuid4().hex[:8].upper()}"


def _random_amount(min_val: float = 10.0, max_val: float = 5000.0) -> Decimal:
    amount = Decimal(str(round(random.uniform(min_val, max_val), 2)))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86399)
    return start + timedelta(days=random_days, seconds=random_seconds)


TRANSACTION_TYPES = ["payment", "refund", "transfer", "withdrawal", "deposit"]
PAYMENT_STATUSES = ["completed", "pending", "failed", "settled", "reversed"]
MERCHANT_NAMES = [
    "Amazon", "Flipkart", "Swiggy", "Zomato", "Uber", "Ola",
    "PhonePe", "Paytm", "Google Pay", "Netflix", "Spotify",
    "BigBasket", "Myntra", "Jio", "Airtel", "HDFC Bank",
    "ICICI Bank", "SBI", "Axis Bank", "BookMyShow"
]


def generate_datasets(num_transactions: int = 120) -> Tuple[str, str]:
    """
    Generate company transactions and bank settlements with intentional discrepancies.
    Returns paths to the two CSV files.
    """
    _ensure_data_dir()

    random.seed(42)  # Reproducible but realistic

    company_transactions = []
    bank_settlements = []

    base_date = datetime(2026, 10, 1)
    end_date = datetime(2026, 11, 30)

    # --- Generate normal matching transactions ---
    normal_count = num_transactions - 10  # Reserve 10 for discrepancies

    for i in range(normal_count):
        txn_id = _generate_transaction_id()
        settlement_ref = _generate_settlement_ref()
        txn_type = random.choice(TRANSACTION_TYPES[:3])  # payment, refund, transfer
        amount = _random_amount()
        txn_date = _random_date(base_date, end_date - timedelta(days=5))
        settle_days = random.randint(0, 3)
        settle_date = txn_date + timedelta(days=settle_days)
        # Normal transactions settle in the same month
        if settle_date.month != txn_date.month:
            settle_date = txn_date
        merchant = random.choice(MERCHANT_NAMES)
        status = "settled"

        company_txn = {
            "transaction_id": txn_id,
            "transaction_date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(amount),
            "transaction_type": txn_type,
            "payment_status": status,
            "merchant": merchant,
            "settlement_ref": settlement_ref,
            "refund_ref": "",
            "description": f"{txn_type.title()} to {merchant}"
        }

        bank_txn = {
            "settlement_ref": settlement_ref,
            "transaction_id": txn_id,
            "settlement_date": settle_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(amount),
            "transaction_type": txn_type,
            "bank_status": "cleared",
            "bank_reference": f"BNK-{uuid.uuid4().hex[:8].upper()}",
            "description": f"Settlement for {txn_id}"
        }

        company_transactions.append(company_txn)
        bank_settlements.append(bank_txn)

    # --- Discrepancy 1: Next-month settlement ---
    # November transaction that settles in December
    txn_id_timing = _generate_transaction_id()
    stl_ref_timing = _generate_settlement_ref()
    nov_date = datetime(2026, 11, 28, 14, 30, 0)
    dec_date = datetime(2026, 12, 3, 10, 15, 0)
    amount_timing = _random_amount(500, 1500)

    company_transactions.append({
        "transaction_id": txn_id_timing,
        "transaction_date": nov_date.strftime("%Y-%m-%d %H:%M:%S"),
        "amount": str(amount_timing),
        "transaction_type": "payment",
        "payment_status": "completed",
        "merchant": "Amazon",
        "settlement_ref": stl_ref_timing,
        "refund_ref": "",
        "description": "Payment to Amazon - cross-month settlement"
    })

    bank_settlements.append({
        "settlement_ref": stl_ref_timing,
        "transaction_id": txn_id_timing,
        "settlement_date": dec_date.strftime("%Y-%m-%d %H:%M:%S"),
        "amount": str(amount_timing),
        "transaction_type": "payment",
        "bank_status": "cleared",
        "bank_reference": f"BNK-{uuid.uuid4().hex[:8].upper()}",
        "description": f"Settlement for {txn_id_timing} - delayed"
    })

    # --- Discrepancy 2: Rounding differences ---
    # Create 3 transactions with small rounding differences
    for i in range(3):
        txn_id_round = _generate_transaction_id()
        stl_ref_round = _generate_settlement_ref()
        base_amount = _random_amount(100, 3000)
        # Introduce a small rounding difference (1-5 cents)
        rounding_diff = Decimal(str(random.choice(["0.01", "0.02", "0.03", "-0.01", "-0.02"])))
        bank_amount = (base_amount + rounding_diff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        txn_date_r = _random_date(base_date, end_date - timedelta(days=5))
        settle_date_r = txn_date_r + timedelta(days=random.randint(0, 2))
        if settle_date_r.month != txn_date_r.month:
            settle_date_r = txn_date_r

        company_transactions.append({
            "transaction_id": txn_id_round,
            "transaction_date": txn_date_r.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(base_amount),
            "transaction_type": "payment",
            "payment_status": "settled",
            "merchant": random.choice(MERCHANT_NAMES),
            "settlement_ref": stl_ref_round,
            "refund_ref": "",
            "description": f"Payment with rounding difference #{i+1}"
        })

        bank_settlements.append({
            "settlement_ref": stl_ref_round,
            "transaction_id": txn_id_round,
            "settlement_date": settle_date_r.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(bank_amount),
            "transaction_type": "payment",
            "bank_status": "cleared",
            "bank_reference": f"BNK-{uuid.uuid4().hex[:8].upper()}",
            "description": f"Settlement for {txn_id_round}"
        })

    # --- Discrepancy 3: Duplicate entry ---
    # Duplicate a transaction in bank settlements
    if bank_settlements:
        dup_index = random.randint(0, len(bank_settlements) - 5)
        duplicate_entry = bank_settlements[dup_index].copy()
        duplicate_entry["bank_reference"] = f"BNK-{uuid.uuid4().hex[:8].upper()}"
        duplicate_entry["description"] = duplicate_entry["description"] + " (DUPLICATE)"
        bank_settlements.append(duplicate_entry)

    # --- Discrepancy 4: Orphan refund ---
    # A refund in bank records with no matching original transaction
    orphan_refund_id = _generate_transaction_id()
    orphan_stl_ref = _generate_settlement_ref()
    orphan_original_txn = _generate_transaction_id()  # This original doesn't exist
    orphan_amount = _random_amount(50, 500)
    orphan_date = _random_date(base_date, end_date - timedelta(days=5))

    bank_settlements.append({
        "settlement_ref": orphan_stl_ref,
        "transaction_id": orphan_refund_id,
        "settlement_date": orphan_date.strftime("%Y-%m-%d %H:%M:%S"),
        "amount": str(orphan_amount),
        "transaction_type": "refund",
        "bank_status": "cleared",
        "bank_reference": f"BNK-{uuid.uuid4().hex[:8].upper()}",
        "description": f"Refund for original {orphan_original_txn} - orphan"
    })

    # --- Discrepancy 5: Unmatched company transactions (no bank settlement) ---
    for i in range(3):
        txn_id_unmatched = _generate_transaction_id()
        txn_date_u = _random_date(base_date, end_date - timedelta(days=5))

        company_transactions.append({
            "transaction_id": txn_id_unmatched,
            "transaction_date": txn_date_u.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(_random_amount(200, 2000)),
            "transaction_type": random.choice(["payment", "transfer"]),
            "payment_status": "completed",
            "merchant": random.choice(MERCHANT_NAMES),
            "settlement_ref": "",
            "refund_ref": "",
            "description": f"Unmatched transaction #{i+1}"
        })

    # --- Discrepancy 6: Unmatched bank settlements (no company record) ---
    for i in range(2):
        stl_ref_unmatched = _generate_settlement_ref()
        txn_id_bank_only = _generate_transaction_id()
        settle_date_u = _random_date(base_date, end_date - timedelta(days=5))

        bank_settlements.append({
            "settlement_ref": stl_ref_unmatched,
            "transaction_id": txn_id_bank_only,
            "settlement_date": settle_date_u.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": str(_random_amount(100, 1500)),
            "transaction_type": "payment",
            "bank_status": "cleared",
            "bank_reference": f"BNK-{uuid.uuid4().hex[:8].upper()}",
            "description": f"Bank-only settlement #{i+1}"
        })

    # Shuffle to make data more realistic
    random.shuffle(company_transactions)
    random.shuffle(bank_settlements)

    # Write CSV files
    company_path = os.path.join(DATA_DIR, "company_transactions.csv")
    bank_path = os.path.join(DATA_DIR, "bank_settlements.csv")

    company_fields = [
        "transaction_id", "transaction_date", "amount", "transaction_type",
        "payment_status", "merchant", "settlement_ref", "refund_ref", "description"
    ]

    bank_fields = [
        "settlement_ref", "transaction_id", "settlement_date", "amount",
        "transaction_type", "bank_status", "bank_reference", "description"
    ]

    with open(company_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=company_fields)
        writer.writeheader()
        writer.writerows(company_transactions)

    with open(bank_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=bank_fields)
        writer.writeheader()
        writer.writerows(bank_settlements)

    return company_path, bank_path


if __name__ == "__main__":
    c_path, b_path = generate_datasets()
    print(f"Generated company transactions: {c_path}")
    print(f"Generated bank settlements: {b_path}")
