from __future__ import annotations

import pandas as pd

from .validation import ValidationReport


def _lag_for_outcome(frame: pd.DataFrame, lag: int, value_columns: list[str], prefix: str) -> pd.DataFrame:
    selected = frame[["iso3", "year", *value_columns]].copy()
    selected["year"] = selected["year"] + lag
    return selected.rename(columns={column: f"{prefix}{column}_lag{lag}" for column in value_columns})


def build_master(
    atlas: pd.DataFrame,
    acled: pd.DataFrame,
    temperature: pd.DataFrame,
    livestock_group: pd.DataFrame,
    woah: pd.DataFrame,
    rd_annual: pd.DataFrame,
    report: ValidationReport,
) -> pd.DataFrame:
    master = atlas.copy()
    conflict_values = ["annual_events_reported", "annual_events", "months_reported_raw",
                       "zero_months_imputed", "coverage_start_year", "months_reported",
                       "complete_calendar_year", "log2p1_events", "two_year_events",
                       "two_year_log2p1_events"]
    master = master.merge(_lag_for_outcome(acled, 1, conflict_values, "conflict_"),
                          on=["iso3", "year"], how="left", validate="many_to_one")
    temperature_values = ["temperature_anomaly_c", "baseline_sd_c", "standardised_anomaly", "anomaly_2y_mean"]
    master = master.merge(_lag_for_outcome(temperature, 1, temperature_values, "temperature_"),
                          on=["iso3", "year"], how="left", validate="many_to_one")

    livestock_wide = livestock_group.pivot_table(
        index=["iso3", "year"], columns="livestock_group",
        values=["head_count", "livestock_units", "livestock_unit_share"], aggfunc="first"
    )
    livestock_wide.columns = [f"livestock_{measure}_{group}" for measure, group in livestock_wide.columns]
    livestock_wide = livestock_wide.reset_index()
    livestock_values = [column for column in livestock_wide.columns if column not in ["iso3", "year"]]
    master = master.merge(_lag_for_outcome(livestock_wide, 1, livestock_values, ""),
                          on=["iso3", "year"], how="left", validate="many_to_one")

    woah_values = ["total_mgkg_unadjusted", "total_mgkg_adjusted", "reporting_option_export",
                   "growth_promoter_use_export", "growth_promoter_legislation_export"]
    master = master.merge(_lag_for_outcome(woah, 1, woah_values, "animal_amu_"),
                          on=["iso3", "year"], how="left", validate="many_to_one")
    rd_values = ["projects_started", "projects_with_reported_amount", "award_commitment_usd"]
    master = master.merge(rd_annual[["iso3", "year", *rd_values]].rename(
        columns={column: f"rd_{column}" for column in rd_values}),
        on=["iso3", "year"], how="left", validate="many_to_one")
    report.unique_key(master, ["iso3", "year", "endpoint_id"], "Master country-year endpoint")
    return master


def disclosure_safe(master: pd.DataFrame, suppression_n: int) -> pd.DataFrame:
    public = master.copy()
    public["sufficient_atlas_data"] = public["n_tested"].ge(suppression_n)
    sensitive = ["n_tested", "n_resistant", "n_intermediate", "n_susceptible", "n_mic",
                 "resistance_pct", "mic_coverage_pct"]
    public.loc[~public["sufficient_atlas_data"], sensitive] = pd.NA
    return public
