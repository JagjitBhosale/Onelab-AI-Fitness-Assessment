"""Tests for data generator."""
import os
import sys
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.data_generator import generate_datasets, DATA_DIR


def test_generate_datasets(tmp_path, monkeypatch):
    import app.data_generator as gen_mod
    monkeypatch.setattr(gen_mod, "DATA_DIR", str(tmp_path))
    c_path, b_path = generate_datasets(120)
    assert os.path.exists(c_path)
    assert os.path.exists(b_path)

    with open(c_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 100

    with open(b_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        assert len(rows) >= 100
