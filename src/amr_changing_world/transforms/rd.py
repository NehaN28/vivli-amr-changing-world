from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import config_path, load_yaml
from ..countries import attach_country_keys
from ..validation import ValidationReport


def _normalise_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _split_labels(value: object) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return ["Not specified"]
    labels = [item.strip() for item in re.split(r"[,;\n]+", str(value)) if item.strip()]
    return sorted(set(labels)) or ["Not specified"]


def _fractional_rows(projects: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in projects.itertuples(index=False):
        dimensions = {
            "sector": _split_labels(row.sector),
            "research_area": _split_labels(row.research_area),
            "infectious_agent": _split_labels(row.individual_infectious_agent),
        }
        for dimension, labels in dimensions.items():
            weight = 1.0 / len(labels)
            for label in labels:
                rows.append({
                    "project_id": row.project_id, "dimension": dimension, "category": label,
                    "fraction": weight, "fractional_project_count": weight,
                    "fractional_amount_usd": row.amount_usd * weight if pd.notna(row.amount_usd) else np.nan,
                })
        for pathogen in row.pathogen_tags:
            weight = 1.0 / len(row.pathogen_tags)
            rows.append({
                "project_id": row.project_id, "dimension": "pathogen", "category": pathogen,
                "fraction": weight, "fractional_project_count": weight,
                "fractional_amount_usd": row.amount_usd * weight if pd.notna(row.amount_usd) else np.nan,
            })
    return pd.DataFrame(rows)


def process_rd(path: Path, report: ValidationReport) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(path, sheet_name="data")
    required = [
        "Id", "Funder Name", "Institution Name", "Institution Country", "External Project No",
        "Title", "Abstract", "Start Year", "End Year", "Amount USD", "Sector", "Research Area",
        "Individual Infectious Agent", "Categories",
    ]
    report.require_columns(raw, required, "AMR R&D")
    frame = raw.copy()
    frame["amount_original_usd"] = pd.to_numeric(frame["Amount USD"], errors="coerce")
    frame["amount_status"] = np.where(
        frame["amount_original_usd"].eq(0), "unavailable_or_undisclosed",
        np.where(frame["amount_original_usd"].isna(), "missing", "reported_positive")
    )
    frame["amount_usd"] = frame["amount_original_usd"].mask(frame["amount_original_usd"].eq(0))

    exact_fields = ["Title", "Funder Name", "Institution Name", "Start Year", "End Year", "Amount USD"]
    exact_key = frame[exact_fields].astype("string").fillna("<NA>").agg("|".join, axis=1)
    external_no = frame["External Project No"].astype("string").str.strip()
    external_fields = ["Funder Name", "Institution Name", "Start Year", "End Year", "Amount USD"]
    external_tail = frame[external_fields].astype("string").fillna("<NA>").agg("|".join, axis=1)
    external_key = external_no + "|" + external_tail
    external_key = external_key.mask(external_no.isna() | external_no.eq(""))

    frame["duplicate_key"] = "unique|" + frame["Id"].astype(str)
    exact_duplicate = exact_key.duplicated(keep=False)
    frame.loc[exact_duplicate, "duplicate_key"] = "exact|" + exact_key[exact_duplicate]
    external_duplicate = external_key.notna() & external_key.duplicated(keep=False) & ~exact_duplicate
    frame.loc[external_duplicate, "duplicate_key"] = "external|" + external_key[external_duplicate]
    frame["duplicate_group_size"] = frame.groupby("duplicate_key")["Id"].transform("size")
    frame["duplicate_of_project_id"] = frame.groupby("duplicate_key")["Id"].transform("min")
    frame["is_duplicate_excess"] = frame["Id"].ne(frame["duplicate_of_project_id"])
    duplicate_audit = frame.loc[frame["duplicate_group_size"].gt(1), [
        "Id", "duplicate_of_project_id", "duplicate_group_size", "is_duplicate_excess",
        "Title", "Funder Name", "Institution Name", "External Project No", "Amount USD"
    ]].copy()

    clean = frame.loc[~frame["is_duplicate_excess"]].copy()
    clean = attach_country_keys(clean, "Institution Country", "rd")
    keyword_map = load_yaml(config_path("rd_keyword_map.yml"))["pathogens"]
    text = clean[["Title", "Abstract", "Individual Infectious Agent", "Categories"]].fillna("").agg(" ".join, axis=1).str.casefold()
    pathogen_tags = []
    for value in text:
        matches = [pathogen for pathogen, words in keyword_map.items()
                   if any(word.casefold() in value for word in words)]
        pathogen_tags.append(matches or ["Not pathogen-specific"])
    clean["pathogen_tags"] = pathogen_tags
    clean = clean.rename(columns={
        "Id": "project_id", "Title": "title", "Abstract": "abstract",
        "Funder Name": "funder_name", "Institution Name": "institution_name",
        "Institution Country": "institution_country_raw", "External Project No": "external_project_no",
        "Start Year": "start_year", "End Year": "end_year", "Sector": "sector",
        "Research Area": "research_area", "Individual Infectious Agent": "individual_infectious_agent",
        "Categories": "categories",
    })
    keep = [
        "project_id", "title", "abstract", "funder_name", "institution_name",
        "institution_country_raw", "country", "iso3", "external_project_no", "start_year", "end_year",
        "amount_original_usd", "amount_usd", "amount_status", "sector", "research_area",
        "individual_infectious_agent", "categories", "pathogen_tags",
    ]
    clean = clean[keep].sort_values("project_id").reset_index(drop=True)
    fractional = _fractional_rows(clean)
    annual = clean.groupby(["iso3", "country", "start_year"], dropna=False, as_index=False).agg(
        projects_started=("project_id", "size"),
        projects_with_reported_amount=("amount_usd", "count"),
        award_commitment_usd=("amount_usd", "sum"),
    ).rename(columns={"start_year": "year"})
    annual.loc[annual["projects_with_reported_amount"].eq(0), "award_commitment_usd"] = np.nan
    report.add("R&D: unique raw project IDs", not raw["Id"].duplicated().any(), int(raw["Id"].duplicated().sum()))
    report.add("R&D: duplicate excess rows flagged", True, int(frame["is_duplicate_excess"].sum()))
    report.add("R&D: zero amounts treated as missing", not clean["amount_usd"].eq(0).any(),
               int((clean["amount_status"] == "unavailable_or_undisclosed").sum()))
    report.unique_key(clean, ["project_id"], "R&D clean projects")
    report.unique_key(fractional, ["project_id", "dimension", "category"], "R&D fractional categories")
    report.unique_key(annual, ["iso3", "year"], "R&D recipient country-year commitments")
    return clean, fractional, duplicate_audit, annual
