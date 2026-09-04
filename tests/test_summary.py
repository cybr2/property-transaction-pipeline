"""Tests for app.summary aggregations and rounding."""

from __future__ import annotations

import pytest

from app.summary import (
    build_district_stats,
    build_project_stats,
    build_summary,
    build_top5_2025,
    median,
)


def row(name: str, district: str, psf: float, price: int, date: str) -> dict[str, object]:
    return {
        "transaction_id": f"TXN-{name}-{date}",
        "project_name": name,
        "district": district,
        "price": price,
        "area_sqft": price / psf,
        "psf": psf,
        "sale_date": date,
        "sale_type": "Resale",
        "tenure": "99 yrs",
    }


class TestMedian:
    def test_odd_count(self) -> None:
        assert median([1, 2, 3]) == 2.0

    def test_even_count_averages_middle(self) -> None:
        assert median([1, 2, 3, 4]) == 2.5

    def test_rounds_to_two_decimals(self) -> None:
        assert median([1.234, 1.239]) == 1.24

    def test_empty_is_none(self) -> None:
        assert median([]) is None


class TestProjectStats:
    def test_full_history_and_by_year(self) -> None:
        projects = build_project_stats(
            [
                row("A", "D01", 1000, 1_000_000, "2024-01-01"),
                row("A", "D01", 2000, 2_000_000, "2025-01-01"),
                row("A", "D01", 3000, 3_000_000, "2025-06-01"),
            ]
        )
        a = projects["A"]
        assert a["district"] == "D01"
        assert a["transaction_count"] == 3
        assert a["median_psf"] == 2000.0
        assert a["median_price"] == 2_000_000.0
        assert a["by_year"]["2024"] == {
            "transaction_count": 1,
            "median_psf": 1000.0,
            "median_price": 1_000_000.0,
        }
        assert a["by_year"]["2025"]["transaction_count"] == 2
        assert a["by_year"]["2025"]["median_psf"] == 2500.0
        assert a["by_year"]["2025"]["median_price"] == 2_500_000.0


class TestDistrictStats:
    def test_groups_by_district(self) -> None:
        districts = build_district_stats(
            [
                row("A", "D01", 1000, 1_000_000, "2025-01-01"),
                row("B", "D01", 3000, 3_000_000, "2025-01-02"),
                row("C", "D19", 2000, 2_000_000, "2025-01-03"),
            ]
        )
        assert districts["D01"]["transaction_count"] == 2
        assert districts["D01"]["median_psf"] == 2000.0
        assert districts["D19"]["transaction_count"] == 1


class TestTop5:
    def test_highest_first_skips_no_2025_sales(self) -> None:
        projects = build_project_stats(
            [
                row("Low", "D01", 1000, 1_000_000, "2025-01-01"),
                row("High", "D01", 5000, 5_000_000, "2025-01-02"),
                row("Mid", "D01", 2500, 2_500_000, "2025-01-03"),
                row("Old", "D01", 9000, 9_000_000, "2024-01-01"),
                row("A", "D01", 3000, 3_000_000, "2025-01-04"),
                row("B", "D01", 2000, 2_000_000, "2025-01-05"),
                row("C", "D01", 1500, 1_500_000, "2025-01-06"),
            ]
        )
        top = build_top5_2025(projects)
        names = [t["project_name"] for t in top]
        assert names == ["High", "A", "Mid", "B", "C"]
        assert "Old" not in names
        assert len(top) == 5

    def test_fewer_than_five(self) -> None:
        projects = build_project_stats(
            [row("Only", "D01", 1200, 1_200_000, "2025-01-01")]
        )
        top = build_top5_2025(projects)
        assert len(top) == 1
        assert top[0]["project_name"] == "Only"


class TestBuildSummary:
    def test_structure(self) -> None:
        rows = [row("A", "D01", 1000, 1_000_000, "2025-01-01")]
        summary = build_summary(rows, source_count=5, excluded={"invalid_price": 2}, duplicates=1)
        assert summary["source_rows"] == 5
        assert summary["cleaned_rows"] == 1
        assert summary["duplicates_dropped"] == 1
        assert summary["excluded"] == {"invalid_price": 2}
        assert set(summary) >= {"generated_at", "districts", "top5_projects_by_median_psf_2025", "projects"}
        assert "A" in summary["projects"]
        assert "D01" in summary["districts"]