"""Tests for app.cleaning — dedupe, title case, district, price, area/sqft,
psf exclusions, dates, sale_type, in spec order."""

from __future__ import annotations

import pytest

from app.cleaning import (
    PSF_MAX,
    PSF_MIN,
    SQM_TO_SQFT,
    clean_district,
    clean_project_name,
    clean_rows,
    clean_sale_type,
    parse_area,
    parse_price,
    parse_sale_date,
)


def row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "transaction_id": "TXN-00001",
        "project_name": "The Orchid Residences",
        "district": "D19",
        "price": "1450000",
        "area": "1000 sqft",
        "sale_date": "2025-01-15",
        "sale_type": "Resale",
        "tenure": "99 yrs",
    }
    base.update(overrides)
    return base


class TestDedupe:
    def test_keeps_first_occurrence(self) -> None:
        rows = [
            row(transaction_id="TXN-1", price="1000000"),
            row(transaction_id="TXN-1", price="999999999"),
            row(transaction_id="TXN-2", price="2000000"),
        ]
        result = clean_rows(rows)
        assert result.duplicates == 1
        assert len(result.rows) == 2
        prices = {r["transaction_id"]: r["price"] for r in result.rows}
        assert prices["TXN-1"] == 1000000


class TestProjectName:
    def test_title_case(self) -> None:
        assert clean_project_name("the orchid residences") == "The Orchid Residences"

    def test_trims_surrounding_whitespace(self) -> None:
        assert clean_project_name("  Marina Bay Suites  ") == "Marina Bay Suites"

    def test_collapses_internal_whitespace(self) -> None:
        assert clean_project_name("Bishan  Green") == "Bishan Green"
        assert clean_project_name("Choa  Chu  Kang  Residences") == "Choa Chu Kang Residences"


class TestDistrict:
    def test_plain_number(self) -> None:
        assert clean_district("5") == "D05"

    def test_d_prefix(self) -> None:
        assert clean_district("D19") == "D19"

    def test_d_with_zero_padded(self) -> None:
        assert clean_district("D09") == "D09"

    def test_lowercase_and_padded(self) -> None:
        assert clean_district("d23") == "D23"

    def test_surrounding_spaces(self) -> None:
        assert clean_district(" 25 ") == "D25"


class TestPrice:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1450000", 1450000),
            ("$1,450,000", 1450000),
            ("S$ 1,450,000", 1450000),
            ("$$ 1,450,000", 1450000),
            (" 1000000 ", 1000000),
        ],
    )
    def test_parses_whole_dollars(self, raw: str, expected: int) -> None:
        assert parse_price(raw) == expected

    @pytest.mark.parametrize("raw", ["", " ", "n/a", "unknown", "TBC", "$$", "N/A", "price tbd", "1.5M"])
    def test_rejects_junk(self, raw: str) -> None:
        assert parse_price(raw) is None


class TestArea:
    def test_sqft_direct(self) -> None:
        assert parse_area("1330 sqft") == 1330

    def test_sq_ft_with_commas(self) -> None:
        assert parse_area("1,036 sq ft") == 1036

    def test_sqm_conversion(self) -> None:
        assert parse_area("92.1 sqm") == pytest.approx(92.1 * SQM_TO_SQFT)

    def test_sq_m_variants(self) -> None:
        assert parse_area("48.8 sq m") == pytest.approx(48.8 * SQM_TO_SQFT)
        assert parse_area("98.6 sq.m") == pytest.approx(98.6 * SQM_TO_SQFT)
        assert parse_area("96.2 sq m ") == pytest.approx(96.2 * SQM_TO_SQFT)

    def test_sqft_abbreviated(self) -> None:
        assert parse_area("710 sq.ft") == 710

    @pytest.mark.parametrize("raw", ["", " ", "n/a", "-"])
    def test_blank_or_missing(self, raw: str) -> None:
        assert parse_area(raw) is None


class TestSaleDate:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("2025-09-04", "2025-09-04"),
            ("19/04/2025", "2025-04-19"),
            ("08 Aug 2020", "2020-08-08"),
            ("21 Dec 2020", "2020-12-21"),
        ],
    )
    def test_all_formats(self, raw: str, expected: str) -> None:
        assert parse_sale_date(raw) == expected


class TestSaleType:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Resale", "Resale"),
            ("RESALE", "Resale"),
            ("new sale", "New Sale"),
            (" NEW SALE ", "New Sale"),
            ("Sub Sale", "Sub Sale"),
            ("SUB SALE", "Sub Sale"),
        ],
    )
    def test_title_case(self, raw: str, expected: str) -> None:
        assert clean_sale_type(raw) == expected


class TestExclusions:
    def test_invalid_price(self) -> None:
        result = clean_rows([row(price="unknown")])
        assert result.excluded == {"invalid_price": 1}
        assert result.rows == []

    def test_missing_area(self) -> None:
        result = clean_rows([row(area="n/a")])
        assert result.excluded == {"missing_area": 1}
        assert result.rows == []

    def test_psf_below_band(self) -> None:
        result = clean_rows([row(price="100000", area="1000 sqft")])
        assert result.excluded == {"outlier_psf": 1}

    def test_psf_above_band(self) -> None:
        result = clean_rows([row(price="6100000", area="1000 sqft")])
        assert result.excluded == {"outlier_psf": 1}

    def test_psf_at_band_edges_inclusive(self) -> None:
        assert PSF_MIN < PSF_MAX
        low = clean_rows([row(price=str(int(PSF_MIN * 1000)), area="1000 sqft")])
        high = clean_rows([row(price=str(int(PSF_MAX * 1000)), area="1000 sqft")])
        assert low.rows and low.excluded == {}
        assert high.rows and high.excluded == {}

    def test_priority_price_before_area(self) -> None:
        # price junk and area blank: only one reason, price wins
        result = clean_rows([row(price="TBC", area="n/a")])
        assert result.excluded == {"invalid_price": 1}

    def test_priority_area_before_psf(self) -> None:
        # area blank and psf out of band: only one reason, area wins
        result = clean_rows([row(price="6000000", area="n/a")])
        assert result.excluded == {"missing_area": 1}

    def test_valid_row_is_normalized(self) -> None:
        result = clean_rows(
            [
                row(
                    transaction_id="TXN-00042",
                    project_name="  the orchid residences  ",
                    district=" 5 ",
                    price="S$ 1,450,000",
                    area="92.1 sqm",
                    sale_date="19/04/2025",
                    sale_type="NEW SALE",
                )
            ]
        )
        assert len(result.rows) == 1
        clean = result.rows[0]
        assert clean["project_name"] == "The Orchid Residences"
        assert clean["district"] == "D05"
        assert clean["price"] == 1450000
        assert clean["area_sqft"] == pytest.approx(92.1 * SQM_TO_SQFT, abs=0.01)
        assert clean["psf"] == pytest.approx(1450000 / (92.1 * SQM_TO_SQFT), abs=0.01)
        assert clean["sale_date"] == "2025-04-19"
        assert clean["sale_type"] == "New Sale"
        assert clean["tenure"] == "99 yrs"
        assert result.excluded == {}