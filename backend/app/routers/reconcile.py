"""Reconciliation router."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from ..reconciliation import reconcile
from ..models import DiscrepancyCategory

router = APIRouter(prefix="/api/reconcile", tags=["reconciliation"])


@router.get("")
def run_reconciliation(
    category: Optional[str] = Query(None, description="Filter by discrepancy category"),
):
    """Run reconciliation and return results, with optional category filter."""
    try:
        result = reconcile()

        if category:
            try:
                cat = DiscrepancyCategory(category)
                result.discrepancies = [
                    d for d in result.discrepancies if d.category == cat
                ]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {category}. Valid: {[c.value for c in DiscrepancyCategory]}"
                )

        return result.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
def get_categories():
    """Get all discrepancy categories."""
    return [{"value": c.value, "label": c.value.replace("_", " ").title()} for c in DiscrepancyCategory]
