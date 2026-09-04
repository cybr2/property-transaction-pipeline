"""API tests using FastAPI TestClient against the real clean dataset."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "clean_transactions.csv"

client = TestClient(create_app(clean_csv=CSV))


class TestHealth:
    def test_health(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestListProjects:
    def test_shape_and_sorted(self) -> None:
        resp = client.get("/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        names = [p["project_name"] for p in data]
        assert names == sorted(names)
        for p in data:
            assert set(p) == {"project_name", "district", "transaction_count", "median_psf"}
            assert p["median_psf"] is not None


class TestProjectDetail:
    def test_known_project(self) -> None:
        resp = client.get("/projects/the orchid residences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_name"] == "The Orchid Residences"
        assert data["district"] == "D19"
        assert data["transaction_count"] > 0
        assert "by_year" in data

    def test_lookup_is_casefolded_and_trimmed(self) -> None:
        resp = client.get("/projects/  THE ORCHID RESIDENCES  ")
        assert resp.status_code == 200
        assert resp.json()["project_name"] == "The Orchid Residences"

    def test_year_filter_overrides_three_fields(self) -> None:
        base = client.get("/projects/The Orchid Residences").json()
        resp = client.get("/projects/The Orchid Residences?year=2025")
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_count"] == base["by_year"]["2025"]["transaction_count"]
        assert data["median_psf"] == base["by_year"]["2025"]["median_psf"]
        assert data["median_price"] == base["by_year"]["2025"]["median_price"]
        assert data["district"] == base["district"]

    def test_unknown_project_404(self) -> None:
        resp = client.get("/projects/No Such Place")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "unknown_project"
        assert body["project_name"] == "No Such Place"


class TestEstimate:
    def test_known_project(self) -> None:
        resp = client.get("/estimate", params={"project": "Marina Bay Suites", "area_sqft": 1000})
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"] == "Marina Bay Suites"
        assert data["psf_used"] is not None
        assert data["n_transactions"] > 0
        assert data["estimated_price"] == round(data["psf_used"] * 1000, 2)
        assert "window" in data

    def test_unknown_project_404(self) -> None:
        resp = client.get("/estimate", params={"project": "Nope", "area_sqft": 1000})
        assert resp.status_code == 404

    def test_nonpositive_area_rejected(self) -> None:
        resp = client.get("/estimate", params={"project": "Marina Bay Suites", "area_sqft": 0})
        assert resp.status_code == 422