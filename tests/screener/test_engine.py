import pandas as pd
from src.screener.engine import apply_filters
from src.analytics.cagr import cagr, FLAG_TURNAROUND, FLAG_ZERO_BASE


def make_fake_df():
    """A tiny 3-row fake dataset so tests don't depend on the real database."""
    return pd.DataFrame([
        {"company_id": "A", "return_on_equity_pct": 20, "debt_to_equity": 0.5,
         "broad_sector": "IT", "interest_coverage": 5, "icr_label": None},
        {"company_id": "B", "return_on_equity_pct": 10, "debt_to_equity": 6.0,
         "broad_sector": "Financials", "interest_coverage": None, "icr_label": "Debt Free"},
        {"company_id": "C", "return_on_equity_pct": 300, "debt_to_equity": 0.2,
         "broad_sector": "IT", "interest_coverage": 1.0, "icr_label": None},
    ])


def test_roe_filter_excludes_implausible_values():
    df = make_fake_df()
    result = apply_filters(df, {"roe_min": 15})
    # A passes (20>15), B fails (10<15), C fails (300 is >200, excluded as implausible)
    assert set(result["company_id"]) == {"A"}


def test_de_filter_skips_financials_sector():
    df = make_fake_df()
    result = apply_filters(df, {"de_max": 1.0})
    # A passes (0.5<1.0). B has D/E=6.0 but is Financials -- should NOT be excluded.
    # C passes (0.2<1.0).
    assert "B" in result["company_id"].tolist()
    assert "A" in result["company_id"].tolist()


def test_icr_debt_free_always_passes():
    df = make_fake_df()
    result = apply_filters(df, {"icr_min": 10})
    # B has icr_label "Debt Free" -- should pass ANY icr_min threshold
    assert "B" in result["company_id"].tolist()


def test_cagr_turnaround_flag():
    value, flag = cagr(-100, 50, 3)
    assert value is None
    assert flag == FLAG_TURNAROUND


def test_cagr_zero_base_flag():
    value, flag = cagr(0, 100, 3)
    assert value is None
    assert flag == FLAG_ZERO_BASE


def test_cagr_normal_case():
    value, flag = cagr(100, 200, 5)
    assert flag is None
    assert value > 0