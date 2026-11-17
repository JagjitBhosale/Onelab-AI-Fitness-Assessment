"""Tests for the FastAPI application endpoints."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from app import reconciliation as recon_module
from app import data_generator as gen_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    data_dir = str(tmp_path / "data")
    os.makedirs(data_dir, exist_ok=True)
    monkeypatch.setattr(recon_module, "DATA_DIR", data_dir)
    monkeypatch.setattr(gen_module, "DATA_DIR", data_dir)
    from app import reports as reports_mod
    monkeypatch.setattr(reports_mod, "load_company_transactions", recon_module.load_company_transactions)
    monkeypatch.setattr(reports_mod, "load_bank_settlements", recon_module.load_bank_settlements)
    # Generate data into the temp dir
    gen_module.generate_datasets()
    # Import app AFTER patching
    from app.main import app
    return TestClient(app)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ReconAI" in r.json()["message"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_generate_data(client):
    r = client.post("/api/data/generate")
    assert r.status_code == 200
    assert r.json()["company_transactions_count"] >= 100


def test_reconcile(client):
    r = client.get("/api/reconcile")
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "discrepancies" in data


def test_reconcile_filter(client):
    r = client.get("/api/reconcile?category=matched")
    assert r.status_code == 200


def test_reports(client):
    r = client.get("/api/reports")
    assert r.status_code == 200
    assert "explanation" in r.json()


def test_monthly(client):
    r = client.get("/api/reports/monthly")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_export_csv(client):
    r = client.get("/api/reports/export/csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
