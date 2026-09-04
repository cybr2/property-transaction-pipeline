"""Aggregations for summary.json — project stats, district medians, top-5 2025.

All medians use statistics.median (even counts average the two middle values)
and are rounded to 2 decimals, including by-year figures.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.median(values), 2)


def _sale_year(sale_date: str) -> str:
    return sale_date[:4]


def build_project_stats(rows: list[dict[str, object]]) -> dict[str, dict]:
    """Return {project_name: {project_name, district, transaction_count,
    median_psf, median_price, by_year}}."""
    by_project: dict[str, list[dict[str, object]]] = defaultdict(list)
    district_of: dict[str, str] = {}
    for row in rows:
        name = str(row["project_name"])
        by_project[name].append(row)
        district_of.setdefault(name, str(row["district"]))

    projects: dict[str, dict] = {}
    for name, sales in by_project.items():
        psfs = [float(s["psf"]) for s in sales]
        prices = [float(s["price"]) for s in sales]
        by_year: dict[str, dict] = {}
        for year in sorted({_sale_year(str(s["sale_date"])) for s in sales}):
            year_sales = [s for s in sales if _sale_year(str(s["sale_date"])) == year]
            by_year[year] = {
                "transaction_count": len(year_sales),
                "median_psf": median([float(s["psf"]) for s in year_sales]),
                "median_price": median([float(s["price"]) for s in year_sales]),
            }
        projects[name] = {
            "project_name": name,
            "district": district_of[name],
            "transaction_count": len(sales),
            "median_psf": median(psfs),
            "median_price": median(prices),
            "by_year": by_year,
        }
    return projects


def build_district_stats(rows: list[dict[str, object]]) -> dict[str, dict]:
    """Return {district: {transaction_count, median_psf, median_price}}."""
    by_district: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_district[str(row["district"])].append(row)

    districts: dict[str, dict] = {}
    for district, sales in by_district.items():
        districts[district] = {
            "transaction_count": len(sales),
            "median_psf": median([float(s["psf"]) for s in sales]),
            "median_price": median([float(s["price"]) for s in sales]),
        }
    return districts


def build_top5_2025(projects: dict[str, dict]) -> list[dict]:
    """Highest-first list of the 5 projects by their 2025 by-year median psf.

    Projects with no 2025 sales are skipped.
    """
    ranked = []
    for name, project in projects.items():
        year_2025 = project.get("by_year", {}).get("2025")
        if year_2025 is None:
            continue
        ranked.append(
            {
                "project_name": name,
                "district": project["district"],
                "median_psf": year_2025["median_psf"],
                "transaction_count": year_2025["transaction_count"],
            }
        )
    ranked.sort(key=lambda item: item["median_psf"], reverse=True)
    return ranked[:5]


def build_summary(
    rows: list[dict[str, object]],
    *,
    source_count: int,
    excluded: dict[str, int],
    duplicates: int,
) -> dict:
    """Assemble the full summary.json document."""
    projects = build_project_stats(rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_rows": source_count,
        "cleaned_rows": len(rows),
        "duplicates_dropped": duplicates,
        "excluded": excluded,
        "districts": build_district_stats(rows),
        "top5_projects_by_median_psf_2025": build_top5_2025(projects),
        "projects": projects,
    }