"""Reports router."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from ..reconciliation import reconcile
from ..reports import generate_report, generate_monthly_totals, export_discrepancies_csv

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def get_report():
    """Get full reconciliation report."""
    try:
        result = reconcile()
        report = generate_report(result)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly")
def get_monthly_totals():
    """Get monthly reconciliation totals."""
    try:
        return [m.model_dump() for m in generate_monthly_totals()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/csv")
def export_csv():
    """Export discrepancies as CSV file download."""
    try:
        result = reconcile()
        csv_content = export_discrepancies_csv(result.discrepancies)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=discrepancy_report.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
