from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..countries import attach_country_keys
from ..validation import ValidationReport


MONTH_MAP = {name: number for number, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1
)}


def process_acled(path: Path, report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(path, sheet_name="Sheet1")
    required = ["COUNTRY", "MONTH", "YEAR", "EVENTS"]
    report.require_columns(raw, required, "ACLED")
    frame = raw[required].rename(columns={
        "COUNTRY": "country_raw", "MONTH": "month", "YEAR": "year", "EVENTS": "events"
    })
    frame["month_number"] = frame["month"].map(MONTH_MAP)
    frame = attach_country_keys(frame, "country_raw", "acled")
    excluded = frame.loc[~frame["country_status"].isin(["current", "territory"]), "country_raw"].unique()
    frame = frame.loc[frame["country_status"].isin(["current", "territory"])].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["events"] = pd.to_numeric(frame["events"], errors="raise").astype(int)
    report.add("ACLED: valid months", frame["month_number"].notna().all(),
               sorted(frame.loc[frame["month_number"].isna(), "month"].dropna().unique()))
    report.add("ACLED: nonnegative events", bool(frame["events"].ge(0).all()),
               int(frame["events"].lt(0).sum()))
    report.add("ACLED: excluded non-country labels", True, sorted(map(str, excluded)))
    report.unique_key(frame, ["iso3", "year", "month_number"], "ACLED country-month")

    # The supplied country-month extract contains explicit zeroes in early years,
    # but omits many zero-event months in later years.  A missing row is therefore
    # not automatically a missing-coverage month.  The first observed 12-month
    # year is used as a reproducible, source-internal marker that January coverage
    # has begun.  Thereafter, absent months in closed calendar years are true zeroes.
    raw_annual = frame.groupby(["iso3", "country", "year"], as_index=False).agg(
        annual_events_reported=("events", "sum"), months_reported_raw=("month_number", "nunique")
    )
    coverage_start = (
        raw_annual.loc[raw_annual["months_reported_raw"].eq(12)]
        .groupby(["iso3", "country"], as_index=False)["year"].min()
        .rename(columns={"year": "coverage_start_year"})
    )
    last_closed_year = int(frame["year"].max()) - 1
    panels: list[pd.DataFrame] = []
    for row in coverage_start.itertuples(index=False):
        years = range(int(row.coverage_start_year), last_closed_year + 1)
        panels.append(pd.DataFrame({"iso3": row.iso3, "country": row.country, "year": years,
                                    "coverage_start_year": int(row.coverage_start_year)}))
    annual = (pd.concat(panels, ignore_index=True) if panels else
              pd.DataFrame(columns=["iso3", "country", "year", "coverage_start_year"]))
    annual = annual.merge(raw_annual, on=["iso3", "country", "year"], how="left", validate="one_to_one")
    annual["annual_events_reported"] = annual["annual_events_reported"].fillna(0).astype(int)
    annual["months_reported_raw"] = annual["months_reported_raw"].fillna(0).astype(int)
    annual["zero_months_imputed"] = 12 - annual["months_reported_raw"]
    annual["months_reported"] = 12
    annual["complete_calendar_year"] = True
    annual["annual_events"] = annual["annual_events_reported"].astype(float)
    annual["log2p1_events"] = np.log2(1 + annual["annual_events"])
    annual = annual.sort_values(["iso3", "year"])
    previous_year = annual.groupby("iso3")["year"].shift(1)
    rolling_sum = annual.groupby("iso3")["annual_events"].transform(
        lambda values: values.rolling(2, min_periods=2).sum())
    annual["two_year_events"] = rolling_sum.where(annual["year"].sub(previous_year).eq(1))
    annual["two_year_log2p1_events"] = np.log2(1 + annual["two_year_events"])
    report.add("ACLED: coverage start inferred from a 12-month source year",
               bool(len(coverage_start) > 0), int(len(coverage_start)))
    report.add("ACLED: zero-event months imputed only after coverage start",
               bool(annual["zero_months_imputed"].between(0, 12).all()),
               int(annual["zero_months_imputed"].sum()))
    report.unique_key(annual, ["iso3", "year"], "ACLED country-year")
    month_grid = annual[["iso3", "country", "year", "coverage_start_year"]].merge(
        pd.DataFrame({"month_number": range(1, 13)}), how="cross"
    )
    observed = frame[["iso3", "year", "month_number", "events"]].rename(
        columns={"events": "events_reported"})
    month_grid = month_grid.merge(observed, on=["iso3", "year", "month_number"], how="left",
                                  validate="one_to_one")
    month_grid["source_month_present"] = month_grid["events_reported"].notna()
    month_grid["imputed_zero"] = month_grid["events_reported"].isna()
    month_grid["events"] = month_grid["events_reported"].fillna(0).astype(int)
    month_names = {number: name for name, number in MONTH_MAP.items()}
    month_grid["month"] = month_grid["month_number"].map(month_names)
    report.unique_key(month_grid, ["iso3", "year", "month_number"], "ACLED reconstructed country-month")
    return month_grid.sort_values(["iso3", "year", "month_number"]), annual.sort_values(["iso3", "year"])
