"""In-memory dataset loaded once at app startup from the clean CSV."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.summary import build_summary


@dataclass
class Store:
    rows: list[dict[str, object]] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @classmethod
    def from_csv(cls, path: str) -> "Store":
        from app.cleaning import read_raw_csv

        rows = read_raw_csv(path)
        summary = build_summary(rows, source_count=len(rows), excluded={}, duplicates=0)
        return cls(rows=rows, summary=summary)

    def rows_for(self, project_name: str) -> list[dict[str, object]]:
        return [r for r in self.rows if str(r["project_name"]) == project_name]

    def max_sale_date(self) -> date | None:
        dates = [str(r["sale_date"]) for r in self.rows if r.get("sale_date")]
        if not dates:
            return None
        return date.fromisoformat(max(dates))