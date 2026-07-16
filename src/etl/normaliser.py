"""
normaliser.py
-------------
Two small, well-tested functions that clean up the two messiest
fields in the raw data: company ticker (company_id) and year.

Keep these simple and bulletproof -- everything else in the ETL
pipeline depends on them being correct.
"""
import re


def normalize_ticker(raw) -> str:
    """
    Clean a company_id / ticker value.
    - strips whitespace
    - uppercases
    - checks length is between 2 and 12 characters (DQ-08)
    Raises ValueError if the result is empty or out of range.
    """
    if raw is None:
        raise ValueError("Ticker is None")
    s = str(raw).strip().upper()
    if not s:
        raise ValueError("Ticker is empty after stripping")
    if not (2 <= len(s) <= 12):
        raise ValueError(f"Ticker length out of range (2-12): '{s}'")
    return s


def normalize_year(raw) -> int:
    """
    Convert messy year labels into a single 4-digit integer year.
    Handles formats seen in the raw files:
        "Dec 2012"  -> 2012
        "Mar 2014"  -> 2014
        "Mar-13"    -> 2013
        "Mar-9"     -> 2009
        2024        -> 2024
        "2024"      -> 2024
    Raises ValueError if no year can be extracted (DQ-07).
    """
    if raw is None:
        raise ValueError("Year is None")

    # Already a plain int/float like 2024 or 2024.0
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        year = int(raw)
        if 1990 <= year <= 2100:
            return year
        raise ValueError(f"Year out of plausible range: {raw}")

    s = str(raw).strip()

    # Case 1: contains a 4-digit year anywhere, e.g. "Dec 2012", "2024"
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        return int(m.group(0))

    # Case 2: "Mar-13" / "Mar-9" style short year at the end
    m = re.search(r"-(\d{1,2})$", s)
    if m:
        two_digit = int(m.group(1))
        # 00-79 -> 2000s, 80-99 -> 1900s (standard pivot-year convention)
        year = 2000 + two_digit if two_digit < 80 else 1900 + two_digit
        return year

    raise ValueError(f"Unparseable year value: '{raw}'")
