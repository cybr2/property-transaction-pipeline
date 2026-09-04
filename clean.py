#!/usr/bin/env python3
"""CLI: read the raw CSV, write clean_transactions.csv + summary.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.cleaning import clean_rows, read_raw_csv, write_clean_csv
from app.summary import build_summary

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw",
        default=ROOT / "condo_transactions_raw.csv",
        help="input messy CSV (default: repo raw file)",
    )
    parser.add_argument(
        "--clean",
        default=ROOT / "clean_transactions.csv",
        help="output clean CSV (default: repo root)",
    )
    parser.add_argument(
        "--summary",
        default=ROOT / "summary.json",
        help="output summary JSON (default: repo root)",
    )
    args = parser.parse_args()

    raw_rows = read_raw_csv(args.raw)
    result = clean_rows(raw_rows)
    write_clean_csv(result.rows, args.clean)
    summary = build_summary(
        result.rows,
        source_count=len(raw_rows),
        excluded=result.excluded,
        duplicates=result.duplicates,
    )
    with open(args.summary, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"source_rows={len(raw_rows)} cleaned={len(result.rows)} "
          f"duplicates={result.duplicates} excluded={result.excluded}")
    print(f"wrote {args.clean}")
    print(f"wrote {args.summary}")


if __name__ == "__main__":
    main()