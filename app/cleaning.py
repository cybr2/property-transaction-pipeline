"""Pure parse/normalize/exclude functions for the messy transactions CSV.

Each cleaning rule follows the spec (docs/specs/2026-09-05-...) in order:
dedupe on transaction_id (first wins), title-case project_name, district
normalization, price parse, area parse, psf band, date normalize, sale_type
casing. Excluded rows carry exactly one reason applied in order
price -> area -> psf.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime

SQM_TO_SQFT = 10.7639
PSF_MIN = 500.0
PSF_MAX = 6000.0

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y")

OUTPUT_COLUMNS = [
    "transaction_id",
    "project_name",
    "district",
    "price",
    "area_sqft",
    "psf",
    "sale_date",
    "sale_type",
    "tenure",
]

_AREA_RE = re.compile(
    r"^\s*(?P<number>[\d][\d,]*\.?\d*)\s*"
    r"(?P<unit>sq\s*\.?\s*(?:ft|m)\.?)?\s*$",
    re.IGNORECASE,
)


@dataclass
class CleaningResult:
    rows: list[dict[str, object]] = field(default_factory=list)
    excluded: dict[str, int] = field(default_factory=dict)
    duplicates: int = 0
    skipped_dates: int = 0


def clean_project_name(raw: object) -> str:
    collapsed = re.sub(r"\s+", " ", str(raw or "").strip())
    return collapsed.title()


def clean_district(raw: object) -> str:
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if not digits:
        return str(raw or "").strip()
    return f"D{int(digits):02d}"


def parse_price(raw: object) -> int | None:
    s = str(raw or "").strip().upper()
    s = s.replace(",", "").replace(" ", "").replace("\u00a0", "")
    if not s:
        return None
    for prefix in ("S$", "$$", "$"):
        if s.startswith(prefix):
            s = s[len(prefix) :]
            break
    if not s or not s.isdigit():
        return None
    return int(s)


def parse_area(raw: object) -> float | None:
    s = str(raw or "").strip()
    if not s:
        return None
    m = _AREA_RE.match(s)
    if not m:
        return None
    number = m.group("number").replace(",", "")
    unit = (m.group("unit") or "").lower()
    try:
        value = float(number)
    except ValueError:
        return None
    if "m" in unit:
        return value * SQM_TO_SQFT
    return value


def parse_sale_date(raw: object) -> str | None:
    s = str(raw or "").strip()
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def clean_sale_type(raw: object) -> str:
    return str(raw or "").strip().title()


def normalize_row(row: dict[str, object]) -> tuple[dict[str, object] | None, str | None]:
    """Apply rules in spec order. Returns (clean_row, exclude_reason)."""
    price = parse_price(row.get("price"))
    if price is None:
        return None, "invalid_price"

    area_sqft = parse_area(row.get("area"))
    if area_sqft is None:
        return None, "missing_area"

    psf = price / area_sqft
    if psf < PSF_MIN or psf > PSF_MAX:
        return None, "outlier_psf"

    sale_date = parse_sale_date(row.get("sale_date"))
    if sale_date is None:
        # Not an official exclude reason; generator never emits these.
        return None, None

    return {
        "transaction_id": str(row.get("transaction_id", "")).strip(),
        "project_name": clean_project_name(row.get("project_name")),
        "district": clean_district(row.get("district")),
        "price": price,
        "area_sqft": round(area_sqft, 2),
        "psf": round(psf, 2),
        "sale_date": sale_date,
        "sale_type": clean_sale_type(row.get("sale_type")),
        "tenure": str(row.get("tenure", "")).strip(),
    }, None


def clean_rows(rows: list[dict[str, object]]) -> CleaningResult:
    result = CleaningResult()
    seen: set[str] = set()
    for raw in rows:
        txn_id = str(raw.get("transaction_id", "")).strip()
        if txn_id in seen:
            result.duplicates += 1
            continue
        seen.add(txn_id)

        clean, reason = normalize_row(raw)
        if reason == "invalid_price":
            result.excluded["invalid_price"] = result.excluded.get("invalid_price", 0) + 1
            continue
        if reason == "missing_area":
            result.excluded["missing_area"] = result.excluded.get("missing_area", 0) + 1
            continue
        if reason == "outlier_psf":
            result.excluded["outlier_psf"] = result.excluded.get("outlier_psf", 0) + 1
            continue
        if clean is None:
            result.skipped_dates += 1
            continue
        result.rows.append(clean)
    return result


def read_raw_csv(path: str | object) -> list[dict[str, object]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))  # type: ignore[arg-type]


def write_clean_csv(rows: list[dict[str, object]], path: str | object) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)  # type: ignore[arg-type]