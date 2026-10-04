"""
test_rules.py
-------------
Day 41: 14 unit tests -- one per DQ rule. Each test crafts a minimal
DataFrame that violates exactly that rule and verifies the correct
rule_id and severity are returned by the validator.
"""
import pandas as pd
import pytest
from src.etl.validator import (
    dq01_company_pk_uniqueness, dq02_annual_pk_uniqueness,
    dq03_fk_integrity, dq04_bs_balance, dq05_opm_crosscheck,
    dq06_positive_sales, dq09_net_cash_check, dq10_nonneg_fixed_assets,
    dq11_tax_rate_range, dq12_dividend_payout_cap,
    dq14_eps_sign_consistency, dq16_coverage_check,
)


def test_dq01_duplicate_company_id():
    df = pd.DataFrame({"id": ["TCS", "TCS"]})
    v = dq01_company_pk_uniqueness(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-01"
    assert v[0]["severity"] == "CRITICAL"


def test_dq01_unique_passes():
    df = pd.DataFrame({"id": ["TCS", "INFY"]})
    assert dq01_company_pk_uniqueness(df) == []


def test_dq02_duplicate_year():
    df = pd.DataFrame({"company_id": ["TCS", "TCS"], "year": [2024, 2024]})
    v = dq02_annual_pk_uniqueness(df, "profitandloss")
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-02"
    assert v[0]["severity"] == "CRITICAL"


def test_dq03_orphan_fk():
    df = pd.DataFrame({"company_id": ["UNKNOWN"], "year": [2024]})
    v = dq03_fk_integrity(df, "profitandloss", {"TCS", "INFY"})
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-03"
    assert v[0]["severity"] == "CRITICAL"


def test_dq04_bs_imbalance():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024],
                        "total_assets": [1000.0], "total_liabilities": [500.0]})
    v = dq04_bs_balance(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-04"
    assert v[0]["severity"] == "WARNING"


def test_dq04_balanced_passes():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024],
                        "total_assets": [1000.0], "total_liabilities": [1000.0]})
    assert dq04_bs_balance(df) == []


def test_dq05_opm_mismatch():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024],
                        "sales": [100.0], "operating_profit": [20.0], "opm_percentage": [30.0]})
    v = dq05_opm_crosscheck(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-05"


def test_dq06_negative_sales():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024], "sales": [-100.0]})
    v = dq06_positive_sales(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-06"


def test_dq09_net_cash_mismatch():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024],
                        "operating_activity": [100.0], "investing_activity": [50.0],
                        "financing_activity": [30.0], "net_cash_flow": [500.0]})
    v = dq09_net_cash_check(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-09"


def test_dq10_negative_fixed_assets():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024], "fixed_assets": [-100.0]})
    v = dq10_nonneg_fixed_assets(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-10"


def test_dq11_tax_rate_out_of_range():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024], "tax_percentage": [80.0]})
    v = dq11_tax_rate_range(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-11"


def test_dq12_dividend_payout_too_high():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024], "dividend_payout": [250.0]})
    v = dq12_dividend_payout_cap(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-12"


def test_dq14_eps_sign_mismatch():
    df = pd.DataFrame({"company_id": ["TCS"], "year": [2024],
                        "net_profit": [100.0], "eps": [-5.0]})
    v = dq14_eps_sign_consistency(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-14"


def test_dq16_thin_coverage():
    df = pd.DataFrame({
        "company_id": ["JIOFIN"] * 2,
        "year": [2023, 2024]
    })
    v = dq16_coverage_check(df)
    assert len(v) > 0
    assert v[0]["rule_id"] == "DQ-16"