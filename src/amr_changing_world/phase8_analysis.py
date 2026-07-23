"""Exploratory longitudinal analyses for the Phase 8 dashboard redesign."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from scipy.stats import t
from statsmodels.stats.multitest import multipletests

from .io import write_json, write_table
from .validation import ValidationReport


MIN_TREND_YEARS = 5
MIN_CHANGEPOINT_YEARS = 8
MIN_PAIRED_CELLS = 40
MIN_PAIRED_COUNTRIES = 10

INDICATORS = {
    "temperature_anomaly_c": ("Temperature anomaly (°C)", "identity"),
    "livestock_units_total": ("Total livestock units", "log1p"),
    "total_mgkg_adjusted": ("Animal antimicrobial use (adjusted mg/kg)", "log1p"),
}


def _weighted_slope(group: pd.DataFrame) -> dict[str, float]:
    """Estimate an isolate-weighted linear trend in resistance percentage."""
    year = group["year"].to_numpy(dtype=float)
    outcome = group["resistance_pct"].to_numpy(dtype=float)
    weights = group["n_tested"].to_numpy(dtype=float)
    if np.ptp(outcome) == 0:
        return {
            "slope_pp_per_year": 0.0,
            "slope_ci_low": 0.0,
            "slope_ci_high": 0.0,
            "slope_p_value": 1.0,
            "weighted_r_squared": np.nan,
        }
    design = sm.add_constant(year - year.min())
    result = sm.WLS(outcome, design, weights=weights).fit()
    critical = t.ppf(0.975, max(len(group) - 2, 1))
    slope = float(result.params[1])
    se = float(result.bse[1])
    return {
        "slope_pp_per_year": slope,
        "slope_ci_low": slope - critical * se,
        "slope_ci_high": slope + critical * se,
        "slope_p_value": float(result.pvalues[1]),
        "weighted_r_squared": float(result.rsquared),
    }


def country_trends(one_health: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (endpoint, iso3, country), group in one_health.groupby(
        ["endpoint_id", "iso3", "country"], dropna=False
    ):
        group = group.sort_values("year")
        if group["year"].nunique() < MIN_TREND_YEARS:
            continue
        estimate = _weighted_slope(group)
        slope = estimate["slope_pp_per_year"]
        if estimate["slope_ci_low"] > 0:
            trajectory = "Increasing"
        elif estimate["slope_ci_high"] < 0:
            trajectory = "Decreasing"
        else:
            trajectory = "No clear linear change"
        rows.append(
            {
                "endpoint_id": endpoint,
                "iso3": iso3,
                "country": country,
                "years_observed": int(group["year"].nunique()),
                "first_year": int(group["year"].min()),
                "last_year": int(group["year"].max()),
                "eligible_tested_isolates": int(group["n_tested"].sum()),
                "trajectory": trajectory,
                **estimate,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["endpoint_id", "country"]).reset_index(drop=True)


def pooled_annual_trends(one_health: pd.DataFrame) -> pd.DataFrame:
    """Produce transparent descriptive annual summaries without pseudo-replication."""
    frame = one_health.copy()
    frame["weighted_resistant"] = frame["resistance_pct"] * frame["n_tested"]
    grouped = frame.groupby(["endpoint_id", "year"], as_index=False).agg(
        countries=("iso3", "nunique"),
        tested_isolates=("n_tested", "sum"),
        weighted_resistant=("weighted_resistant", "sum"),
        median_country_resistance_pct=("resistance_pct", "median"),
        q25_country_resistance_pct=("resistance_pct", lambda x: x.quantile(0.25)),
        q75_country_resistance_pct=("resistance_pct", lambda x: x.quantile(0.75)),
    )
    grouped["isolate_weighted_resistance_pct"] = (
        grouped["weighted_resistant"] / grouped["tested_isolates"]
    )
    return grouped.drop(columns="weighted_resistant")


def _lagged_indicator(frame: pd.DataFrame, indicator: str, lag: int) -> pd.DataFrame:
    exposure = frame[["iso3", "year", indicator]].drop_duplicates(["iso3", "year"])
    exposure["year"] += lag
    return frame.drop(columns=indicator).merge(
        exposure, on=["iso3", "year"], how="left", validate="many_to_one"
    )


def lag_associations(one_health: pd.DataFrame) -> pd.DataFrame:
    """Fit exploratory within-country binomial models for same-year and lagged indicators."""
    rows: list[dict[str, object]] = []
    for endpoint, endpoint_frame in one_health.groupby("endpoint_id"):
        for indicator, (label, transform) in INDICATORS.items():
            for lag in (0, 1, 2):
                frame = _lagged_indicator(endpoint_frame, indicator, lag).dropna(
                    subset=[indicator, "resistance_pct", "n_tested"]
                )
                varying = frame.groupby("iso3")[indicator].nunique()
                keep = varying.index[varying.ge(2)]
                frame = frame.loc[frame["iso3"].isin(keep)].copy()
                countries = frame["iso3"].nunique()
                if len(frame) < MIN_PAIRED_CELLS or countries < MIN_PAIRED_COUNTRIES:
                    continue
                exposure = frame[indicator].astype(float)
                if transform == "log1p":
                    exposure = np.log1p(exposure)
                sd = float(exposure.std())
                if not np.isfinite(sd) or sd == 0:
                    continue
                frame["exposure_z"] = (exposure - exposure.mean()) / sd
                try:
                    design = patsy.dmatrix(
                        "exposure_z + C(year) + C(iso3)", data=frame, return_type="dataframe"
                    )
                    outcome = np.column_stack(
                        [frame["n_resistant"], frame["n_tested"] - frame["n_resistant"]]
                    )
                    result = sm.GLM(
                        outcome,
                        design,
                        family=sm.families.Binomial(),
                    ).fit(
                        cov_type="cluster",
                        cov_kwds={"groups": frame["iso3"], "use_correction": True},
                        use_t=True,
                        maxiter=100,
                        disp=False,
                    )
                except (ValueError, np.linalg.LinAlgError):
                    continue
                ci = result.conf_int().loc["exposure_z"]
                rows.append(
                    {
                        "endpoint_id": endpoint,
                        "indicator": indicator,
                        "indicator_label": label,
                        "exposure_transform": transform,
                        "lag_years": lag,
                        "paired_country_year_cells": int(len(frame)),
                        "countries": int(countries),
                        "tested_isolates": int(frame["n_tested"].sum()),
                        "exposure_original_sd": sd,
                        "odds_ratio_per_sd": float(np.exp(result.params["exposure_z"])),
                        "or_ci_low": float(np.exp(ci.iloc[0])),
                        "or_ci_high": float(np.exp(ci.iloc[1])),
                        "p_value": float(result.pvalues["exposure_z"]),
                        "converged": bool(result.converged),
                    }
                )
    result = pd.DataFrame(rows)
    if not result.empty:
        result["nominal_p_below_005"] = result["p_value"].lt(0.05)
        result["fdr_q_value"] = multipletests(result["p_value"], method="fdr_bh")[1]
        result["fdr_significant_005"] = result["fdr_q_value"].lt(0.05)
    return result


def change_point_candidates(one_health: pd.DataFrame) -> pd.DataFrame:
    """Find the largest descriptive mean shift; this is not a significance test."""
    rows: list[dict[str, object]] = []
    for (endpoint, iso3, country), group in one_health.groupby(
        ["endpoint_id", "iso3", "country"], dropna=False
    ):
        group = group.sort_values("year").reset_index(drop=True)
        if group["year"].nunique() < MIN_CHANGEPOINT_YEARS:
            continue
        candidates: list[dict[str, float]] = []
        for split in range(3, len(group) - 2):
            before = np.average(
                group.loc[: split - 1, "resistance_pct"],
                weights=group.loc[: split - 1, "n_tested"],
            )
            after = np.average(
                group.loc[split:, "resistance_pct"],
                weights=group.loc[split:, "n_tested"],
            )
            candidates.append(
                {
                    "candidate_year": int(group.loc[split, "year"]),
                    "before_pct": float(before),
                    "after_pct": float(after),
                    "absolute_shift_pp": float(after - before),
                }
            )
        best = max(candidates, key=lambda item: abs(item["absolute_shift_pp"]))
        rows.append(
            {
                "endpoint_id": endpoint,
                "iso3": iso3,
                "country": country,
                "years_observed": int(len(group)),
                "first_year": int(group["year"].min()),
                "last_year": int(group["year"].max()),
                **best,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        ["endpoint_id", "absolute_shift_pp"], ascending=[True, False]
    )


def coverage_summary(availability: pd.DataFrame) -> pd.DataFrame:
    components = [
        "has_amr",
        "has_temperature",
        "has_livestock",
        "has_animal_amu",
        "has_rd",
    ]
    rows: list[dict[str, object]] = []
    for component in components:
        frame = availability.loc[availability[component]]
        rows.append(
            {
                "component": component.removeprefix("has_"),
                "country_years_available": int(len(frame)),
                "countries_available": int(frame["iso3"].replace("", np.nan).nunique()),
                "first_year": int(frame["year"].min()) if not frame.empty else pd.NA,
                "last_year": int(frame["year"].max()) if not frame.empty else pd.NA,
            }
        )
    return pd.DataFrame(rows)


def run_phase8_analysis(table_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    one_health = pd.read_parquet(table_dir / "one_health_country_year.parquet")
    availability = pd.read_parquet(table_dir / "data_availability.parquet")
    outputs = {
        "country_trends": country_trends(one_health),
        "pooled_annual_trends": pooled_annual_trends(one_health),
        "lag_associations": lag_associations(one_health),
        "change_point_candidates": change_point_candidates(one_health),
        "coverage_summary": coverage_summary(availability),
    }
    report = ValidationReport()
    report.unique_key(
        outputs["country_trends"], ["endpoint_id", "iso3"], "Phase 8B country trends"
    )
    report.unique_key(
        outputs["pooled_annual_trends"],
        ["endpoint_id", "year"],
        "Phase 8B pooled annual trends",
    )
    report.unique_key(
        outputs["lag_associations"],
        ["endpoint_id", "indicator", "lag_years"],
        "Phase 8B lag associations",
    )
    report.unique_key(
        outputs["change_point_candidates"],
        ["endpoint_id", "iso3"],
        "Phase 8B change-point candidates",
    )
    report.add(
        "Phase 8B: analyses use only disclosure-eligible AMR cells",
        bool(one_health["n_tested"].ge(30).all()),
        {"minimum_n_tested": int(one_health["n_tested"].min())},
    )
    paths = {
        name: str(write_table(frame, output_dir, name)) for name, frame in outputs.items()
    }
    validation_path = output_dir / "phase8_analysis_validation.json"
    write_json(
        {
            "passed": report.passed,
            "checks": report.checks,
            "eligibility_rules": {
                "minimum_trend_years": MIN_TREND_YEARS,
                "minimum_change_point_years": MIN_CHANGEPOINT_YEARS,
                "minimum_paired_cells": MIN_PAIRED_CELLS,
                "minimum_paired_countries": MIN_PAIRED_COUNTRIES,
            },
            "outputs": paths,
        },
        validation_path,
    )
    if not report.passed:
        raise ValueError("Phase 8B analysis validation failed")
    return {"passed": True, "outputs": paths, "checks": report.checks}
