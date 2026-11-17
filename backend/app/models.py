"""
ReconAI - Pydantic Models
Data models for the reconciliation system.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DiscrepancyCategory(str, Enum):
    MATCHED = "matched"
    UNMATCHED_COMPANY = "unmatched_company"
    UNMATCHED_BANK = "unmatched_bank"
    TIMING_DIFFERENCE = "timing_difference"
    ROUNDING_DIFFERENCE = "rounding_difference"
    DUPLICATE_ENTRY = "duplicate_entry"
    ORPHAN_REFUND = "orphan_refund"


class CompanyTransaction(BaseModel):
    transaction_id: str
    transaction_date: str
    amount: str
    transaction_type: str
    payment_status: str
    merchant: str = ""
    settlement_ref: str = ""
    refund_ref: str = ""
    description: str = ""


class BankSettlement(BaseModel):
    settlement_ref: str
    transaction_id: str
    settlement_date: str
    amount: str
    transaction_type: str
    bank_status: str
    bank_reference: str = ""
    description: str = ""


class DiscrepancyRecord(BaseModel):
    transaction_id: str
    company_amount: Optional[str] = None
    bank_amount: Optional[str] = None
    transaction_date: Optional[str] = None
    settlement_date: Optional[str] = None
    difference: str = "0.00"
    category: DiscrepancyCategory
    explanation: str


class ReconciliationSummary(BaseModel):
    total_company_transactions: int
    total_bank_settlements: int
    matched_count: int
    unmatched_company_count: int
    unmatched_bank_count: int
    timing_difference_count: int
    rounding_difference_count: int
    duplicate_count: int
    orphan_refund_count: int
    total_company_amount: str
    total_bank_amount: str
    total_amount_difference: str
    reconciliation_success_rate: float
    generated_at: str


class ReconciliationResult(BaseModel):
    summary: ReconciliationSummary
    discrepancies: List[DiscrepancyRecord]
    matched_records: List[DiscrepancyRecord]


class MonthlyTotal(BaseModel):
    month: str
    company_total: str
    bank_total: str
    difference: str
    matched_count: int
    unmatched_count: int


class ReportResponse(BaseModel):
    summary: ReconciliationSummary
    monthly_totals: List[MonthlyTotal]
    explanation: str
