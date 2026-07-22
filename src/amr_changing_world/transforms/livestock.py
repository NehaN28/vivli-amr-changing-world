from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import config_path, load_yaml
from ..countries import attach_country_keys
from ..validation import ValidationReport


def process_livestock(path: Path, report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(path, low_memory=False)
    required = ["Area", "Item", "Year", "Unit", "Value", "Flag", "Flag Description"]
    report.require_columns(raw, required, "FAOSTAT livestock")
    frame = raw[required].copy()
    frame = attach_country_keys(frame, "Area", "livestock")
    frame = frame.loc[frame["country_status"].isin(["current", "territory"]) & frame["iso3"].ne("")]
    frame["value_reported"] = pd.to_numeric(frame["Value"], errors="coerce")
    frame.loc[frame["Flag"].eq("M"), "value_reported"] = pd.NA
    multipliers = {"An": 1.0, "1000 An": 1000.0, "No": 1.0}
    frame["unit_multiplier"] = frame["Unit"].map(multipliers)
    report.add("Livestock: recognised units", frame["unit_multiplier"].notna().all(),
               sorted(frame.loc[frame["unit_multiplier"].isna(), "Unit"].dropna().unique()))
    frame["head_count"] = frame["value_reported"] * frame["unit_multiplier"]
    frame.loc[frame["Item"].eq("Bees"), "head_count"] = pd.NA

    config = load_yaml(config_path("livestock_groups.yml"))
    item_to_group: dict[str, str] = {}
    group_weight: dict[str, float] = {}
    for group, details in config["groups"].items():
        group_weight[group] = float(details["livestock_unit_weight"])
        for item in details["items"]:
            item_to_group[item] = group
    frame["livestock_group"] = frame["Item"].map(item_to_group)
    unknown = sorted(frame.loc[~frame["Item"].isin(config.get("excluded_items", [])) &
                               frame["livestock_group"].isna(), "Item"].unique())
    report.add("Livestock: all analytical items grouped", not unknown, unknown)
    frame["livestock_unit_weight"] = frame["livestock_group"].map(group_weight)
    frame["livestock_units"] = frame["head_count"] * frame["livestock_unit_weight"]

    detail = frame.rename(columns={"Area": "country_raw", "Item": "item", "Year": "year",
                                         "Unit": "unit", "Flag": "flag", "Flag Description": "flag_description"})
    detail = detail[["iso3", "country", "country_raw", "year", "item", "livestock_group",
                     "unit", "value_reported", "head_count", "livestock_unit_weight",
                     "livestock_units", "flag", "flag_description"]]
    report.unique_key(detail, ["iso3", "year", "item"], "Livestock item country-year")

    grouped = detail.loc[detail["livestock_group"].notna()].groupby(
        ["iso3", "country", "year", "livestock_group"], as_index=False
    ).agg(head_count=("head_count", "sum"), livestock_units=("livestock_units", "sum"),
          n_items_reported=("head_count", "count"))
    totals = grouped.groupby(["iso3", "year"])["livestock_units"].transform("sum")
    grouped["livestock_unit_share"] = grouped["livestock_units"] / totals
    report.unique_key(grouped, ["iso3", "year", "livestock_group"], "Livestock group country-year")
    return detail, grouped

