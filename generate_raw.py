#!/usr/bin/env python3
"""Generate a messy 1,910-row fictional Singapore condo transactions CSV."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
ROW_COUNT = 1910
DUPLICATE_COUNT = 160
OUT_PATH = Path(__file__).resolve().parent / "condo_transactions_raw.csv"

COLUMNS = [
    "transaction_id",
    "project_name",
    "district",
    "street",
    "block",
    "floor",
    "unit",
    "bedrooms",
    "area",
    "price",
    "sale_date",
    "sale_type",
    "tenure",
]

PROJECTS = [
    ("The Orchid Residences", 19, "Hougang Avenue 2"),
    ("Marina Bay Suites", 1, "Marina Boulevard"),
    ("East Coast Parkview", 15, "Marine Parade Road"),
    ("Holland Village Loft", 10, "Holland Road"),
    ("Bukit Timah Grove", 21, "Upper Bukit Timah Road"),
    ("River Valley Court", 9, "River Valley Road"),
    ("Tanjong Pagar Place", 2, "Tanjong Pagar Road"),
    ("Katong Seaview", 15, "East Coast Road"),
    ("Novena Heights", 11, "Thomson Road"),
    ("Punggol Waterfront", 19, "Punggol Central"),
    ("Clementi Park Residences", 5, "Clementi Avenue 2"),
    ("Queenstown Vista", 3, "Commonwealth Avenue"),
    ("Orchard Heritage", 9, "Orchard Boulevard"),
    ("Serangoon Gardens", 19, "Serangoon Garden Way"),
    ("Bedok Reservoir Views", 16, "Bedok Reservoir Road"),
    ("Pasir Ris Seaview", 18, "Pasir Ris Drive 1"),
    ("Woodlands Cascade", 25, "Woodlands Avenue 2"),
    ("Jurong Lake District", 22, "Yuan Ching Road"),
    ("Bishan Green", 20, "Bishan Street 22"),
    ("Toa Payoh Central", 12, "Lorong 6 Toa Payoh"),
    ("Ang Mo Kio Grove", 20, "Ang Mo Kio Avenue 6"),
    ("Sengkang Riviera", 19, "Sengkang East Avenue"),
    ("Tampines Grande", 18, "Tampines Avenue 1"),
    ("Choa Chu Kang Residences", 23, "Choa Chu Kang Avenue 3"),
    ("Yishun Emerald", 27, "Yishun Avenue 2"),
    ("Sentosa Cove Villas", 4, "Ocean Drive"),
    ("Newton Suites", 11, "Newton Road"),
    ("Balestier Point", 12, "Balestier Road"),
    ("Geylang Quay", 14, "Geylang Road"),
    ("Farrer Park Residences", 8, "Farrer Park Road"),
    ("Little India Lofts", 8, "Serangoon Road"),
    ("Chin Swee Heights", 3, "Chin Swee Road"),
    ("Telok Blangah Ridge", 4, "Telok Blangah Road"),
    ("Alexandra Central", 5, "Alexandra Road"),
    ("Dover Parkview", 5, "Dover Road"),
    ("Buona Vista Court", 5, "North Buona Vista Road"),
    ("Harbourfront Residences", 4, "Harbourfront Avenue"),
    ("Raffles Place Tower", 1, "Raffles Place"),
    ("Shenton Way Suites", 1, "Shenton Way"),
    ("Bugis Junction Residences", 7, "Victoria Street"),
    ("Lavender Street Loft", 7, "Lavender Street"),
    ("Kallang Riverside", 7, "Kallang Avenue"),
    ("MacPherson Park", 13, "MacPherson Road"),
    ("Eunos Ville", 14, "Eunos Road 2"),
    ("Kembangan Court", 14, "Sims Avenue East"),
    ("Siglap Villas", 15, "Siglap Road"),
    ("Opera Estate", 15, "Fidelio Street"),
    ("Upper Thomson Residences", 26, "Upper Thomson Road"),
    ("Springleaf Green", 26, "Springleaf Avenue"),
    ("Sembawang Springs", 27, "Sembawang Road"),
    ("Admiralty Parkview", 25, "Woodlands Drive 16"),
    ("Marsiling Grove", 25, "Marsiling Road"),
    ("Bukit Batok West", 23, "Bukit Batok West Avenue 8"),
    ("Hillview Heights", 23, "Hillview Avenue"),
    ("Beauty World Residences", 21, "Jalan Jurong Kechil"),
    ("Sixth Avenue Suites", 10, "Sixth Avenue"),
    ("Ardmore Park", 10, "Ardmore Park"),
    ("Grange Road Residences", 9, "Grange Road"),
    ("Kim Seng Plaza", 9, "Kim Seng Road"),
    ("Tion Bahru Loft", 3, "Tiong Bahru Road"),
    ("Redhill Peak", 3, "Redhill Close"),
    ("Leng Kee Court", 3, "Leng Kee Road"),
    ("Outram Park Residences", 3, "Outram Road"),
    ("Maxwell Chambers Suites", 1, "Maxwell Road"),
    ("Cecil Street Tower", 1, "Cecil Street"),
    ("Anson Residences", 2, "Anson Road"),
    ("Keppel Bay View", 4, "Keppel Bay Drive"),
    ("West Coast Vale", 5, "West Coast Vale"),
    ("Pasir Panjang Residences", 5, "Pasir Panjang Road"),
    ("One-North Loft", 5, "One-North Crescent"),
    ("Ghim Moh Green", 10, "Ghim Moh Road"),
    ("Farrer Road Court", 10, "Farrer Road"),
    ("Botanic Gardens Residences", 10, "Cluny Park Road"),
    ("Stevens Suites", 10, "Stevens Road"),
    ("Balmoral Heights", 10, "Balmoral Road"),
    ("Nassim Park", 10, "Nassim Road"),
    ("Paterson Residences", 9, "Paterson Road"),
    ("Cuscaden Residences", 9, "Cuscaden Road"),
    ("Scotts Tower", 9, "Scotts Road"),
    ("Irrawaddy Residences", 11, "Irrawaddy Road"),
]

SALE_TYPES = ["Resale", "New Sale", "Sub Sale"]
TENURES = ["99 yrs", "Freehold"]
MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def messy_project_name(rng: random.Random, name: str) -> str:
    mode = rng.randrange(6)
    if mode == 0:
        return name.lower()
    if mode == 1:
        return name.upper()
    if mode == 2:
        return f"  {name}  "
    if mode == 3:
        return name.replace(" ", "  ")
    if mode == 4:
        return name.lower().replace(" ", "  ")
    return name


def messy_district(rng: random.Random, district: int) -> str:
    mode = rng.randrange(5)
    if mode == 0:
        return str(district)
    if mode == 1:
        return f"D{district}"
    if mode == 2:
        return f"D{district:02d}"
    if mode == 3:
        return f"d{district:02d}"
    return f" {district} "


def messy_sale_type(rng: random.Random, sale_type: str) -> str:
    mode = rng.randrange(4)
    if mode == 0:
        return sale_type.lower()
    if mode == 1:
        return sale_type.upper()
    if mode == 2:
        return f" {sale_type} "
    return sale_type


def format_area(rng: random.Random, area_sqft: float) -> str:
    if rng.random() < 0.04:
        return rng.choice(["", " ", "n/a", "-"])
    if rng.random() < 0.45:
        sqm = area_sqft / 10.7639
        unit = rng.choice(["sqm", "sq m", "sq.m", "sq m "])
        return f"{sqm:.1f} {unit}"
    formatted = f"{area_sqft:,.0f}" if rng.random() < 0.5 else f"{area_sqft:.0f}"
    unit = rng.choice(["sqft", "sq ft", "sq.ft"])
    return f"{formatted} {unit}"


def format_price(rng: random.Random, price: int, *, corrupt: str | None) -> str:
    if corrupt == "blank":
        return rng.choice(["", " ", "n/a"])
    if corrupt == "non_numeric":
        return rng.choice(["unknown", "TBC", "$$", "N/A", "price tbd"])
    if corrupt == "ten_x":
        price = price * 10
    elif corrupt == "tenth":
        price = max(1, price // 10)

    mode = rng.randrange(5)
    if mode == 0:
        return str(price)
    if mode == 1:
        return f"${price:,}"
    if mode == 2:
        return f"S$ {price:,}"
    if mode == 3:
        return f"$$ {price:,}"
    return f" {price} "


def format_date(rng: random.Random, d: date) -> str:
    mode = rng.randrange(3)
    if mode == 0:
        return d.isoformat()
    if mode == 1:
        return d.strftime("%d/%m/%Y")
    return f"{d.day:02d} {MONTHS[d.month - 1]} {d.year}"


def format_floor(rng: random.Random, floor: int, unit: str) -> str:
    if rng.random() < 0.35:
        return f"#{floor:02d}-{unit}"
    return str(floor)


def random_sale_date(rng: random.Random) -> date:
    year_weights = {2020: 8, 2021: 10, 2022: 14, 2023: 18, 2024: 22, 2025: 28}
    years = list(year_weights)
    weights = [year_weights[y] for y in years]
    year = rng.choices(years, weights=weights, k=1)[0]
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    if year == 2025:
        end = date(2025, 9, 4)
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def build_clean_row(rng: random.Random, txn_id: str) -> dict[str, object]:
    project, district, street = rng.choice(PROJECTS)
    bedrooms = rng.choice([1, 2, 2, 3, 3, 3, 4])
    area_sqft = {1: 500, 2: 750, 3: 1011, 4: 1350}[bedrooms] + rng.choice(
        [-40, -20, 0, 25, 50, 80]
    )
    area_sqft = max(420, area_sqft)
    base_psf = rng.randint(1100, 2800)
    if district <= 4:
        base_psf += 400
    price = int(area_sqft * base_psf)
    price = int(round(price, -3))
    floor = rng.randint(2, 38)
    unit = f"{rng.randint(1, 20):02d}"
    return {
        "transaction_id": txn_id,
        "project_name": project,
        "district": district,
        "street": street,
        "block": str(rng.randint(1, 88)),
        "floor": floor,
        "unit": unit,
        "bedrooms": bedrooms,
        "area_sqft": area_sqft,
        "price": price,
        "sale_date": random_sale_date(rng),
        "sale_type": rng.choice(SALE_TYPES),
        "tenure": rng.choice(TENURES),
        "corrupt": None,
    }


def mess_up(rng: random.Random, row: dict[str, object]) -> dict[str, str]:
    corrupt = row["corrupt"]
    return {
        "transaction_id": str(row["transaction_id"]),
        "project_name": messy_project_name(rng, str(row["project_name"])),
        "district": messy_district(rng, int(row["district"])),
        "street": str(row["street"]),
        "block": str(row["block"]),
        "floor": format_floor(rng, int(row["floor"]), str(row["unit"])),
        "unit": str(row["unit"]),
        "bedrooms": str(row["bedrooms"]),
        "area": format_area(rng, float(row["area_sqft"])),
        "price": format_price(
            rng, int(row["price"]), corrupt=corrupt if isinstance(corrupt, str) else None
        ),
        "sale_date": format_date(rng, row["sale_date"]),  # type: ignore[arg-type]
        "sale_type": messy_sale_type(rng, str(row["sale_type"])),
        "tenure": str(row["tenure"]),
    }


def generate(rng: random.Random) -> list[dict[str, str]]:
    unique_count = ROW_COUNT - DUPLICATE_COUNT
    clean_rows = [
        build_clean_row(rng, f"TXN-{i:05d}") for i in range(1, unique_count + 1)
    ]

    blank_price_idx = rng.sample(range(unique_count), 25)
    taken = set(blank_price_idx)
    non_numeric_idx = rng.sample(
        [i for i in range(unique_count) if i not in taken], 20
    )
    taken |= set(non_numeric_idx)
    ten_x_idx = rng.sample([i for i in range(unique_count) if i not in taken], 18)
    taken |= set(ten_x_idx)
    tenth_idx = rng.sample([i for i in range(unique_count) if i not in taken], 12)

    for i in blank_price_idx:
        clean_rows[i]["corrupt"] = "blank"
    for i in non_numeric_idx:
        clean_rows[i]["corrupt"] = "non_numeric"
    for i in ten_x_idx:
        clean_rows[i]["corrupt"] = "ten_x"
    for i in tenth_idx:
        clean_rows[i]["corrupt"] = "tenth"

    messy = [mess_up(rng, row) for row in clean_rows]
    dup_sources = rng.choices(messy, k=DUPLICATE_COUNT)
    extra = [dict(row) for row in dup_sources]
    for row in extra[::3]:
        digits = "".join(ch for ch in row["district"] if ch.isdigit()) or "1"
        row["project_name"] = messy_project_name(rng, row["project_name"])
        row["district"] = messy_district(rng, int(digits))

    all_rows = messy + extra
    rng.shuffle(all_rows)
    assert len(all_rows) == ROW_COUNT
    return all_rows


def main() -> None:
    rng = random.Random(SEED)
    rows = generate(rng)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
