"""
ReconAI - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routers import data, reconcile, reports
from .data_generator import generate_datasets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Generate initial datasets if they don't exist on startup."""
    try:
        from .reconciliation import DATA_DIR as recon_data_dir
        company_path = os.path.join(recon_data_dir, "company_transactions.csv")
        if not os.path.exists(company_path):
            generate_datasets()
    except Exception:
        pass
    yield


app = FastAPI(
    title="ReconAI - Payment Reconciliation API",
    description="Intelligent Payment Reconciliation System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend (allows localhost, Vercel, and any deployed origin)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data.router)
app.include_router(reconcile.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"message": "ReconAI API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
