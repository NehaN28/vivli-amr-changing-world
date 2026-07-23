from pathlib import Path

import pandas as pd

from amr_changing_world.phase8 import (
    _availability,
    _endpoint_coverage,
    _one_health_trends,
    _rd_annual_portfolio,
)


def test_endpoint_coverage_applies_public_threshold():
    atlas = pd.DataFrame(
        {
            "endpoint_id": ["ECO_CAZ_R", "ECO_CAZ_R"],
            "iso3": ["AAA", "BBB"],
            "country": ["A", "B"],
            "year": [2020, 2020],
            "n_tested": [29, 30],
        }
    )
    coverage = _endpoint_coverage(atlas, 30).set_index("endpoint_id")
    assert coverage.loc["ECO_CAZ_R", "eligible_tested_isolates"] == 30
    assert coverage.loc["ECO_CAZ_R", "eligible_countries"] == 1


def test_one_health_trends_never_exports_small_amr_cells():
    atlas = pd.DataFrame(
        {
            "iso3": ["AAA", "AAA"],
            "country": ["A", "A"],
            "year": [2020, 2021],
            "endpoint_id": ["ECO_CAZ_R", "ECO_CAZ_R"],
            "species": ["Escherichia coli", "Escherichia coli"],
            "drug": ["Ceftazidime", "Ceftazidime"],
            "analysis_tier": ["Primary", "Primary"],
            "n_tested": [29, 30],
            "n_resistant": [10, 12],
            "n_intermediate": [0, 0],
            "n_susceptible": [19, 18],
            "n_mic": [29, 30],
            "resistance_pct": [34.5, 40.0],
            "mic_coverage_pct": [100.0, 100.0],
        }
    )
    temperature = pd.DataFrame(
        {
            "iso3": ["AAA"],
            "year": [2021],
            "temperature_anomaly_c": [1.0],
            "standardised_anomaly": [2.0],
            "anomaly_2y_mean": [0.8],
        }
    )
    livestock = pd.DataFrame(
        {
            "iso3": ["AAA"],
            "country": ["A"],
            "year": [2021],
            "livestock_group": ["Swine"],
            "head_count": [100],
            "livestock_units": [30],
            "livestock_unit_share": [1.0],
        }
    )
    woah = pd.DataFrame(
        {
            "iso3": ["AAA"],
            "year": [2021],
            "total_mgkg_unadjusted": [10.0],
            "total_mgkg_adjusted": [9.0],
            "reporting_option_export": ["Option 1"],
            "growth_promoter_use_export": ["No"],
            "growth_promoter_legislation_export": ["Yes"],
        }
    )
    result = _one_health_trends(atlas, temperature, livestock, woah, 30)
    assert result["year"].tolist() == [2021]
    assert result["n_tested"].min() >= 30


def test_rd_annual_portfolio_preserves_start_year():
    projects = pd.DataFrame(
        {
            "project_id": [1],
            "start_year": [2020],
            "iso3": ["AAA"],
            "country": ["A"],
            "amount_status": ["reported_positive"],
            "amount_usd": [100.0],
        }
    )
    fractional = pd.DataFrame(
        {
            "project_id": [1],
            "dimension": ["sector"],
            "category": ["Human"],
            "fraction": [1.0],
            "fractional_project_count": [1.0],
            "fractional_amount_usd": [100.0],
        }
    )
    portfolio, geography = _rd_annual_portfolio(projects, fractional)
    assert portfolio.loc[0, "year"] == 2020
    assert portfolio.loc[0, "reported_commitment_usd"] == 100
    assert geography.loc[0, "reported_commitment_usd"] == 100
    assert geography.loc[0, "projects_started"] == 1


def test_availability_retains_full_component_union():
    atlas = pd.DataFrame(
        {
            "iso3": ["AAA"],
            "country": ["A"],
            "year": [2020],
            "endpoint_id": ["ECO_CAZ_R"],
            "n_tested": [30],
        }
    )
    temperature = pd.DataFrame({"iso3": ["BBB"], "country": ["B"], "year": [2020]})
    livestock = pd.DataFrame({"iso3": ["CCC"], "country": ["C"], "year": [2020]})
    woah = pd.DataFrame({"iso3": ["DDD"], "country": ["D"], "year": [2020]})
    rd = pd.DataFrame({"iso3": ["EEE"], "country": ["E"], "year": [2020]})
    result = _availability(atlas, temperature, livestock, woah, rd, 30)
    assert set(result["iso3"]) == {"AAA", "BBB", "CCC", "DDD", "EEE"}
    assert result.loc[result["iso3"].eq("AAA"), "has_amr"].iloc[0]
