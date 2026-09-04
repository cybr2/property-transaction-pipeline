"""API routes: /projects, /projects/{name}, /estimate, /health."""

from __future__ import annotations

import re
from datetime import date, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.store import Store


def normalize_key(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).casefold()


def _trailing_window(store: Store) -> tuple[str, str] | None:
    end = store.max_sale_date()
    if end is None:
        return None
    months = end.year * 12 + (end.month - 1) - 11
    start = date(months // 12, months % 12 + 1, 1)
    return start.isoformat(), end.isoformat()


def build_router(store: Store) -> APIRouter:
    router = APIRouter()

    @router.get("/projects")
    def list_projects() -> list[dict]:
        return sorted(
            (
                {
                    "project_name": p["project_name"],
                    "district": p["district"],
                    "transaction_count": p["transaction_count"],
                    "median_psf": p["median_psf"],
                }
                for p in store.summary["projects"].values()
            ),
            key=lambda item: item["project_name"],
        )

    @router.get("/projects/{project_name}")
    def project_detail(
        project_name: str,
        year: int | None = Query(default=None, ge=1900, le=2100),
    ) -> dict:
        lookup = {normalize_key(n): n for n in store.summary["projects"]}
        canonical = lookup.get(normalize_key(project_name))
        if canonical is None:
            return JSONResponse(
                status_code=404,
                content={"error": "unknown_project", "project_name": project_name},
            )
        project = store.summary["projects"][canonical]
        result = dict(project)
        if year is not None:
            by_year = project.get("by_year", {}).get(str(year))
            if by_year is None:
                result.update(
                    {"transaction_count": 0, "median_psf": None, "median_price": None}
                )
            else:
                result.update(
                    {
                        "transaction_count": by_year["transaction_count"],
                        "median_psf": by_year["median_psf"],
                        "median_price": by_year["median_price"],
                    }
                )
        return result

    @router.get("/estimate")
    def estimate(
        project: str = Query(...),
        area_sqft: float = Query(..., gt=0),
    ) -> dict:
        lookup = {normalize_key(n): n for n in store.summary["projects"]}
        canonical = lookup.get(normalize_key(project))
        if canonical is None:
            return JSONResponse(
                status_code=404,
                content={"error": "unknown_project", "project_name": project},
            )
        window = _trailing_window(store)
        if window is None:
            return {
                "project": canonical,
                "estimated_price": None,
                "psf_used": None,
                "n_transactions": 0,
            }
        start, end = window
        sales = [
            r
            for r in store.rows_for(canonical)
            if start <= str(r["sale_date"]) <= end
        ]
        if not sales:
            return {
                "project": canonical,
                "estimated_price": None,
                "psf_used": None,
                "n_transactions": 0,
                "window": {"start": start, "end": end},
            }
        psfs = sorted(float(r["psf"]) for r in sales)
        mid = len(psfs) // 2
        median_psf = psfs[mid] if len(psfs) % 2 else (psfs[mid - 1] + psfs[mid]) / 2
        median_psf = round(median_psf, 2)
        return {
            "project": canonical,
            "estimated_price": round(median_psf * area_sqft, 2),
            "psf_used": median_psf,
            "n_transactions": len(sales),
            "window": {"start": start, "end": end},
        }

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return router