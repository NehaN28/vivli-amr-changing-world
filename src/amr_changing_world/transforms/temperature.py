from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..countries import attach_country_keys
from ..validation import ValidationReport


def process_temperature(path: Path, report: ValidationReport) -> pd.DataFrame:
    raw = pd.read_csv(path, low_memory=False)
    required = ["Area", "Months", "Element", "Year", "Unit", "Value", "Flag"]
    report.require_columns(raw, required, "FAOSTAT temperature")
    frame = raw.loc[raw["Months"].eq("Meteorological year"), required].copy()
    frame = attach_country_keys(frame, "Area", "temperature")
    frame = frame.loc[frame["country_status"].isin(["current", "territory"]) & frame["iso3"].ne("")]
    frame["Value"] = pd.to_numeric(frame["Value"], errors="coerce")
    wide = frame.pivot_table(
        index=["iso3", "country", "Year"], columns="Element", values="Value", aggfunc="first"
    ).reset_index().rename(columns={
        "Year": "year", "Temperature change": "temperature_anomaly_c",
        "Standard Deviation": "baseline_sd_c",
    })
    wide.columns.name = None
    wide["standardised_anomaly"] = wide["temperature_anomaly_c"] / wide["baseline_sd_c"]
    wide = wide.sort_values(["iso3", "year"])
    wide["anomaly_2y_mean"] = wide.groupby("iso3")["temperature_anomaly_c"].transform(
        lambda values: values.rolling(2, min_periods=2).mean()
    )
    report.unique_key(wide, ["iso3", "year"], "FAOSTAT temperature country-year")
    return wide

