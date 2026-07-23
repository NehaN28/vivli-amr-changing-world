import pandas as pd
import pytest

from amr_changing_world.phase8_analysis import (
    change_point_candidates,
    country_trends,
    coverage_summary,
    pooled_annual_trends,
)


def _series(values):
    return pd.DataFrame(
        {
            "endpoint_id": ["ECO_CAZ_R"] * len(values),
            "iso3": ["AAA"] * len(values),
            "country": ["A"] * len(values),
            "year": list(range(2010, 2010 + len(values))),
            "n_tested": [100] * len(values),
            "n_resistant": values,
            "resistance_pct": values,
        }
    )


def test_country_trends_requires_five_years_and_classifies_increase():
    assert country_trends(_series([10, 11, 12, 13])).empty
    result = country_trends(_series([10, 15, 20, 25, 30]))
    assert result.loc[0, "trajectory"] == "Increasing"
    assert result.loc[0, "slope_pp_per_year"] == pytest.approx(5)


def test_pooled_annual_trends_uses_isolate_weights():
    frame = pd.concat(
        [
            _series([10]).assign(iso3="AAA", country="A", n_tested=100),
            _series([30]).assign(iso3="BBB", country="B", n_tested=300),
        ],
        ignore_index=True,
    )
    result = pooled_annual_trends(frame)
    assert result.loc[0, "isolate_weighted_resistance_pct"] == 25
    assert result.loc[0, "countries"] == 2


def test_change_point_requires_eight_years():
    assert change_point_candidates(_series([10] * 7)).empty
    result = change_point_candidates(_series([10, 10, 10, 10, 40, 40, 40, 40]))
    assert result.loc[0, "candidate_year"] == 2014
    assert result.loc[0, "absolute_shift_pp"] == 30


def test_coverage_summary_reports_component_ranges():
    frame = pd.DataFrame(
        {
            "iso3": ["AAA", "BBB"],
            "year": [2020, 2021],
            "has_amr": [True, False],
            "has_temperature": [True, True],
            "has_livestock": [False, True],
            "has_animal_amu": [False, False],
            "has_rd": [True, False],
        }
    )
    result = coverage_summary(frame).set_index("component")
    assert result.loc["temperature", "country_years_available"] == 2
    assert result.loc["amr", "countries_available"] == 1
