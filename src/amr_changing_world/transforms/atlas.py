from __future__ import annotations

import gzip
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import config_path, load_yaml
from ..countries import attach_country_keys
from ..mic import MIC_PATTERN
from ..validation import ValidationReport


DEMOGRAPHIC_COLUMNS = [
    "Isolate Id", "Study", "Species", "Country", "Gender", "Age Group",
    "Speciality", "Source", "Year",
]


def _parse_mic_series(series: pd.Series) -> pd.DataFrame:
    raw = series.astype("string").str.strip()
    raw = raw.mask(raw.str.casefold().isin(["", "nan", "na", "n/a", "none"]))
    extracted = raw.str.extract(MIC_PATTERN.pattern)
    operator = extracted[0]
    number = pd.to_numeric(extracted[1], errors="coerce")
    parsed = raw.isna() | number.notna()
    censoring = pd.Series(pd.NA, index=series.index, dtype="string")
    censoring = censoring.mask(raw.notna() & operator.isna() & number.notna(), "exact")
    censoring = censoring.mask(operator.isin(["<", "<="]), "left")
    censoring = censoring.mask(operator.isin([">", ">="]), "right")
    censoring = censoring.mask(raw.notna() & ~parsed, "unparsed")
    lower = number.mask(operator.isin(["<", "<="]))
    upper = number.mask(operator.isin([">", ">="]))
    return pd.DataFrame(
        {"mic_raw": raw, "mic_lower": lower, "mic_upper": upper,
         "mic_censoring": censoring, "mic_parsed": parsed}, index=series.index
    )


def _normalise_interpretation(series: pd.Series) -> pd.Series:
    mapping = {"susceptible": "S", "intermediate": "I", "resistant": "R"}
    return series.astype("string").str.strip().str.casefold().map(mapping).astype("string")


def process_atlas(
    path: Path,
    output_dir: Path,
    report: ValidationReport,
    chunksize: int = 100_000,
) -> dict[str, pd.DataFrame | Path]:
    matrix = load_yaml(config_path("pathogen_drug_matrix.yml"))["endpoints"]
    drugs = sorted({item["drug"] for item in matrix})
    required = DEMOGRAPHIC_COLUMNS + [value for d in drugs for value in (d, f"{d}_I")]
    header = pd.read_csv(path, nrows=0)
    report.require_columns(header, required, "ATLAS")

    output_dir.mkdir(parents=True, exist_ok=True)
    isolate_path = output_dir / "atlas_endpoint_isolates.csv.gz"
    isolate_temp_path = output_dir / "atlas_endpoint_isolates.csv"
    if isolate_path.exists():
        isolate_path.unlink()
    if isolate_temp_path.exists():
        isolate_temp_path.unlink()

    summary_parts: list[pd.DataFrame] = []
    strata_parts: list[pd.DataFrame] = []
    unparsed_mic: dict[str, int] = {}
    unmapped_countries: set[str] = set()
    isolate_duplicate_count = 0
    seen_isolates: set[str] = set()
    first_write = True

    with isolate_temp_path.open("w", encoding="utf-8", newline="") as isolate_handle:
        for chunk in pd.read_csv(path, usecols=required, chunksize=chunksize, low_memory=False):
            ids = chunk["Isolate Id"].astype("string")
            isolate_duplicate_count += int(ids.isin(seen_isolates).sum())
            isolate_duplicate_count += int(ids.duplicated().sum())
            seen_isolates.update(ids.dropna().tolist())
            chunk = attach_country_keys(chunk, "Country", "atlas")
            unmapped_countries.update(
                chunk.loc[chunk["iso3"].eq(""), "Country"].dropna().astype(str).unique()
            )

            for endpoint in matrix:
                species = endpoint["species"]
                drug = endpoint["drug"]
                selected = chunk.loc[chunk["Species"].eq(species)].copy()
                if selected.empty:
                    continue
                interpretation = _normalise_interpretation(selected[f"{drug}_I"])
                mic = _parse_mic_series(selected[drug])
                keep = interpretation.notna() | mic["mic_raw"].notna()
                if not keep.any():
                    continue
                selected = selected.loc[keep].copy()
                interpretation = interpretation.loc[keep]
                mic = mic.loc[keep]
                selected["endpoint_id"] = endpoint["id"]
                selected["drug"] = drug
                selected["analysis_tier"] = endpoint["tier"]
                selected["interpretation"] = interpretation
                selected["resistant"] = interpretation.eq("R").astype("Int8")
                for column in mic.columns:
                    selected[column] = mic[column]
                bad_count = int((~selected["mic_parsed"] & selected["mic_raw"].notna()).sum())
                unparsed_mic[endpoint["id"]] = unparsed_mic.get(endpoint["id"], 0) + bad_count

                long_columns = [
                    "Isolate Id", "Study", "Country", "country", "iso3", "Year",
                    "Species", "endpoint_id", "drug", "analysis_tier", "Gender",
                    "Age Group", "Speciality", "Source", "interpretation", "resistant",
                    "mic_raw", "mic_lower", "mic_upper", "mic_censoring", "mic_parsed",
                ]
                long = selected[long_columns].rename(columns={
                    "Isolate Id": "isolate_id", "Study": "study", "Country": "country_raw",
                    "Year": "year", "Species": "species", "Gender": "gender",
                    "Age Group": "age_group", "Speciality": "speciality", "Source": "source",
                })
                long.to_csv(isolate_handle, index=False, header=first_write)
                first_write = False

                tested = long.loc[long["interpretation"].isin(["S", "I", "R"])].copy()
                if tested.empty:
                    continue
                tested["n_resistant"] = tested["interpretation"].eq("R").astype(int)
                tested["n_intermediate"] = tested["interpretation"].eq("I").astype(int)
                tested["n_susceptible"] = tested["interpretation"].eq("S").astype(int)
                tested["n_mic"] = tested["mic_raw"].notna().astype(int)
                group_cols = ["iso3", "country", "year", "endpoint_id", "species", "drug", "analysis_tier"]
                summary_parts.append(tested.groupby(group_cols, dropna=False).agg(
                    n_tested=("interpretation", "size"), n_resistant=("n_resistant", "sum"),
                    n_intermediate=("n_intermediate", "sum"), n_susceptible=("n_susceptible", "sum"),
                    n_mic=("n_mic", "sum"),
                ).reset_index())

                strata_columns = ["study", "gender", "age_group", "speciality", "source"]
                for column in strata_columns:
                    tested[column] = tested[column].fillna("Unknown")
                strata_group = group_cols + strata_columns
                strata_parts.append(tested.groupby(strata_group, dropna=False).agg(
                    n_tested=("interpretation", "size"), n_resistant=("n_resistant", "sum")
                ).reset_index())

    with isolate_temp_path.open("rb") as source, gzip.open(isolate_path, "wb") as destination:
        shutil.copyfileobj(source, destination, length=1024 * 1024)
    isolate_temp_path.unlink()

    summary = pd.concat(summary_parts, ignore_index=True)
    summary_group = ["iso3", "country", "year", "endpoint_id", "species", "drug", "analysis_tier"]
    summary = summary.groupby(summary_group, as_index=False).agg(
        n_tested=("n_tested", "sum"), n_resistant=("n_resistant", "sum"),
        n_intermediate=("n_intermediate", "sum"), n_susceptible=("n_susceptible", "sum"),
        n_mic=("n_mic", "sum"),
    )
    summary["resistance_pct"] = 100 * summary["n_resistant"] / summary["n_tested"]
    summary["mic_coverage_pct"] = 100 * summary["n_mic"] / summary["n_tested"]

    strata = pd.concat(strata_parts, ignore_index=True)
    strata_group = summary_group + ["study", "gender", "age_group", "speciality", "source"]
    strata = strata.groupby(strata_group, as_index=False)[["n_tested", "n_resistant"]].sum()

    report.add("ATLAS: duplicate isolate IDs", isolate_duplicate_count == 0, isolate_duplicate_count)
    report.add("ATLAS: country mapping", not unmapped_countries, sorted(unmapped_countries))
    report.add("ATLAS: MIC parse", sum(unparsed_mic.values()) == 0, unparsed_mic)
    report.unique_key(summary, ["iso3", "year", "endpoint_id"], "ATLAS country-year endpoint")
    report.unique_key(
        strata,
        ["iso3", "year", "endpoint_id", "study", "gender", "age_group", "speciality", "source"],
        "ATLAS composition strata",
    )
    return {"isolates_path": isolate_path, "summary": summary, "strata": strata}
