from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..validation import ValidationReport


def process_woah(path: Path, report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    country_year = pd.read_excel(path, sheet_name="Country_Year")
    class_long = pd.read_excel(path, sheet_name="Class_Long")
    participation = pd.read_excel(path, sheet_name="Participation")
    report.require_columns(country_year, ["year", "iso3", "country_harmonized",
                                           "total_mgkg_unadjusted", "total_mgkg_adjusted"], "WOAH country-year")
    report.require_columns(class_long, ["year", "iso3", "antimicrobial_class",
                                        "class_mgkg_unadjusted", "estimated_class_mgkg_adjusted"], "WOAH class")
    country_year = country_year.rename(columns={"country_harmonized": "country"})
    class_long = class_long.rename(columns={"country_harmonized": "country"})
    participation = participation.rename(columns={"country_harmonized": "country"})
    report.add("WOAH: mapped country-year ISO3", country_year["iso3"].notna().all(),
               int(country_year["iso3"].isna().sum()))
    report.unique_key(country_year, ["iso3", "year"], "WOAH country-year")
    report.unique_key(class_long, ["iso3", "year", "antimicrobial_class"], "WOAH class")
    report.unique_key(participation, ["iso3"], "WOAH participation")
    return country_year, class_long, participation

