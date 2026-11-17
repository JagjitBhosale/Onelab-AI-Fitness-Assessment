"""Data management router - generate/regenerate datasets."""
from fastapi import APIRouter, HTTPException
from ..data_generator import generate_datasets
from ..reconciliation import load_company_transactions, load_bank_settlements

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/generate")
def generate_data():
    """Generate or regenerate synthetic datasets."""
    try:
        company_path, bank_path = generate_datasets()
        company = load_company_transactions()
        bank = load_bank_settlements()
        return {
            "message": "Datasets generated successfully",
            "company_transactions_count": len(company),
            "bank_settlements_count": len(bank),
            "company_path": company_path,
            "bank_path": bank_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company")
def get_company_transactions():
    """Get all company transactions."""
    return load_company_transactions()


@router.get("/bank")
def get_bank_settlements():
    """Get all bank settlements."""
    return load_bank_settlements()
