import pytest
from src.etl.normaliser import normalize_ticker, normalize_year


# ---------- normalize_ticker: 15+ cases ----------

@pytest.mark.parametrize("raw,expected", [
    ("ABB", "ABB"),
    ("abb", "ABB"),
    ("  ABB  ", "ABB"),
    ("tcs", "TCS"),
    ("HDFCBANK", "HDFCBANK"),
    ("hdfcbank", "HDFCBANK"),
    (" adanienSol ", "ADANIENSOL"),
    ("sbi", "SBI"),
    ("m&m", "M&M"),
    ("l&t", "L&T"),
    ("infy", "INFY"),
    ("Reliance", "RELIANCE"),
    ("ITC", "ITC"),
    ("wipro ", "WIPRO"),
    (" ONGC", "ONGC"),
])
def test_normalize_ticker_valid(raw, expected):
    assert normalize_ticker(raw) == expected


@pytest.mark.parametrize("raw", [
    "A",            # too short (1 char)
    "",              # empty
    "   ",           # whitespace only
    "THISTICKERISTOOLONG",  # too long (>12 chars)
    None,
])
def test_normalize_ticker_invalid(raw):
    with pytest.raises(ValueError):
        normalize_ticker(raw)


# ---------- normalize_year: 20+ cases ----------

@pytest.mark.parametrize("raw,expected", [
    ("Dec 2012", 2012),
    ("Mar 2014", 2014),
    ("Mar-13", 2013),
    ("Mar-9", 2009),
    ("Mar-24", 2024),
    (2024, 2024),
    (2024.0, 2024),
    ("2024", 2024),
    ("FY2023", 2023),
    ("FY 2020", 2020),
    ("Sep 2019", 2019),
    ("Jun-21", 2021),
    ("Dec-99", 1999),
    ("Jan 2001", 2001),
    ("2010", 2010),
    ("Mar 2010", 2010),
    ("Nov-08", 2008),
    ("Apr 2022", 2022),
    ("Mar-00", 2000),
    ("Feb 1998", 1998),
])
def test_normalize_year_valid(raw, expected):
    assert normalize_year(raw) == expected


@pytest.mark.parametrize("raw", [
    "not a year",
    "",
    None,
    "abcd",
    3000,        # implausible year
    "9999",      # will match regex but out of plausible range... see note below
])
def test_normalize_year_invalid(raw):
    # "9999" starts with 19/20? no -> will raise correctly.
    with pytest.raises(ValueError):
        normalize_year(raw)
