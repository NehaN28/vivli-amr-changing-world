"""Build disclosure-safe longitudinal tables for the Phase 8 dashboard redesign."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import config_path, load_yaml
from .io import write_json, write_table
from .validation import ValidationReport


def _read_table(directory: Path, name: str) -> pd.DataFrame:
    parquet = directory / f"{name}.parquet"
    csv = directory / f"{name}.csv"
    if parquet.exists():
        return pd.read_parquet(parquet)
    if csv.exists():
        return pd.read_csv(csv)
    raise FileNotFoundError(f"Missing processed table: {name}")


def _endpoint_coverage(atlas: pd.DataFrame, suppression_n: int) -> pd.DataFrame:
    eligible = atlas.loc[atlas["n_tested"].ge(suppression_n)].copy()
    matrix = pd.DataFrame(load_yaml(config_path("pathogen_drug_matrix.yml"))["endpoints"])
    rows: list[dict[str, object]] = []
    for endpoint in matrix.itertuples(index=False):
        all_rows = atlas.loc[atlas["endpoint_id"].eq(endpoint.id)]
        public_rows = eligible.loc[eligible["endpoint_id"].eq(endpoint.id)]
        rows.append(
            {
                "endpoint_id": endpoint.id,
                "species": endpoint.species,
                "drug": endpoint.drug,
                "analysis_tier": endpoint.tier,
                "who_group": endpoint.who_group,
                "phenotype": endpoint.phenotype,
                "all_tested_isolates": int(all_rows["n_tested"].sum()),
                "eligible_tested_isolates": int(public_rows["n_tested"].sum()),
                "eligible_country_year_cells": int(len(public_rows)),
                "eligible_countries": int(public_rows["iso3"].nunique()),
                "eligible_years": int(public_rows["year"].nunique()),
                "first_eligible_year": (
                    int(public_rows["year"].min()) if not public_rows.empty else pd.NA
                ),
                "last_eligible_year": (
                    int(public_rows["year"].max()) if not public_rows.empty else pd.NA
                ),
                "inclusion_reason": (
                    f"{endpoint.tier} clinically selected phenotype; public country-year "
                    f"cells require at least {suppression_n} tested isolates."
                ),
            }
        )
    return pd.DataFrame(rows)


def _livestock_wide(livestock: pd.DataFrame) -> pd.DataFrame:
    index = ["iso3", "country", "year"]
    totals = livestock.groupby(index, as_index=False).agg(
        livestock_units_total=("livestock_units", "sum"),
        livestock_head_count_total=("head_count", "sum"),
        livestock_groups_reported=("livestock_group", "nunique"),
    )
    units = livestock.pivot_table(
        index=index, columns="livestock_group", values="livestock_units", aggfunc="first"
    )
    shares = livestock.pivot_table(
        index=index, columns="livestock_group", values="livestock_unit_share", aggfunc="first"
    )
    units.columns = [f"livestock_units_{str(value).lower().replace(' ', '_')}" for value in units]
    shares.columns = [f"livestock_share_{str(value).lower().replace(' ', '_')}" for value in shares]
    return totals.merge(units.reset_index(), on=index, how="left").merge(
        shares.reset_index(), on=index, how="left"
    )


def _one_health_trends(
    atlas: pd.DataFrame,
    temperature: pd.DataFrame,
    livestock: pd.DataFrame,
    woah: pd.DataFrame,
    suppression_n: int,
) -> pd.DataFrame:
    amr = atlas.loc[atlas["n_tested"].ge(suppression_n)].copy()
    amr["sufficient_atlas_data"] = True
    temperature_columns = [
        "iso3",
        "year",
        "temperature_anomaly_c",
        "standardised_anomaly",
        "anomaly_2y_mean",
    ]
    livestock_country_year = _livestock_wide(livestock)
    woah_columns = [
        "iso3",
        "year",
        "total_mgkg_unadjusted",
        "total_mgkg_adjusted",
        "reporting_option_export",
        "growth_promoter_use_export",
        "growth_promoter_legislation_export",
    ]
    result = amr.merge(
        temperature[temperature_columns],
        on=["iso3", "year"],
        how="left",
        validate="many_to_one",
    )
    result = result.merge(
        livestock_country_year.drop(columns="country"),
        on=["iso3", "year"],
        how="left",
        validate="many_to_one",
    )
    result = result.merge(
        woah[woah_columns],
        on=["iso3", "year"],
        how="left",
        validate="many_to_one",
    )
    return result.sort_values(["endpoint_id", "iso3", "year"]).reset_index(drop=True)


def _rd_annual_portfolio(
    projects: pd.DataFrame, fractional: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    project_fields = projects[
        ["project_id", "start_year", "iso3", "country", "amount_status"]
    ].rename(columns={"start_year": "year"})
    annual = fractional.merge(project_fields, on="project_id", how="left", validate="many_to_one")
    annual["year"] = pd.to_numeric(annual["year"], errors="coerce").astype("Int64")
    portfolio = annual.groupby(
        ["year", "dimension", "category"], dropna=False, as_index=False
    ).agg(
        fractional_projects=("fractional_project_count", "sum"),
        projects_with_reported_amount=("fractional_amount_usd", "count"),
        reported_commitment_usd=("fractional_amount_usd", "sum"),
    )
    portfolio.loc[
        portfolio["projects_with_reported_amount"].eq(0), "reported_commitment_usd"
    ] = pd.NA
    geography = projects.groupby(
        ["iso3", "country", "start_year"], dropna=False, as_index=False
    ).agg(
        projects_started=("project_id", "size"),
        projects_with_reported_amount=("amount_usd", "count"),
        reported_commitment_usd=("amount_usd", "sum"),
    ).rename(columns={"start_year": "year"})
    geography.loc[
        geography["projects_with_reported_amount"].eq(0), "reported_commitment_usd"
    ] = pd.NA
    return portfolio, geography


def _availability(
    atlas: pd.DataFrame,
    temperature: pd.DataFrame,
    livestock: pd.DataFrame,
    woah: pd.DataFrame,
    rd: pd.DataFrame,
    suppression_n: int,
) -> pd.DataFrame:
    keys = pd.concat(
        [
            atlas[["iso3", "country", "year"]],
            temperature[["iso3", "country", "year"]],
            livestock[["iso3", "country", "year"]],
            woah[["iso3", "country", "year"]],
            rd[["iso3", "country", "year"]],
        ],
        ignore_index=True,
    ).dropna(subset=["iso3", "year"])
    keys = keys.sort_values(["iso3", "year"]).drop_duplicates(["iso3", "year"])
    atlas_public = (
        atlas.loc[atlas["n_tested"].ge(suppression_n)]
        .groupby(["iso3", "year"], as_index=False)
        .agg(amr_endpoints_available=("endpoint_id", "nunique"))
    )
    result = keys.merge(atlas_public, on=["iso3", "year"], how="left")
    result["has_amr"] = result["amr_endpoints_available"].fillna(0).gt(0)
    for label, frame in [
        ("temperature", temperature),
        ("livestock", livestock),
        ("animal_amu", woah),
        ("rd", rd),
    ]:
        present = frame[["iso3", "year"]].drop_duplicates().assign(**{f"has_{label}": True})
        result = result.merge(present, on=["iso3", "year"], how="left", validate="one_to_one")
        result[f"has_{label}"] = result[f"has_{label}"].eq(True)
    return result.reset_index(drop=True)


def run_phase8_tables(processed_dir: Path, output_dir: Path) -> dict[str, object]:
    """Build the annual public tables used by the Phase 8 dashboard."""

    output_dir.mkdir(parents=True, exist_ok=True)
    report = ValidationReport()
    suppression_n = int(
        load_yaml(config_path("project.yml"))["thresholds"]["public_suppression_n"]
    )
    atlas = _read_table(processed_dir, "atlas_country_year_endpoint")
    temperature = _read_table(processed_dir, "temperature_country_year")
    livestock = _read_table(processed_dir, "livestock_country_year_group")
    woah = _read_table(processed_dir, "woah_country_year")
    projects = _read_table(processed_dir, "rd_projects_clean")
    fractional = _read_table(processed_dir, "rd_fractional_categories")
    rd_country_year = _read_table(processed_dir, "rd_country_year_commitments")

    coverage = _endpoint_coverage(atlas, suppression_n)
    one_health = _one_health_trends(atlas, temperature, livestock, woah, suppression_n)
    rd_portfolio, rd_geography = _rd_annual_portfolio(projects, fractional)
    availability = _availability(
        atlas, temperature, livestock, woah, rd_country_year, suppression_n
    )

    report.unique_key(coverage, ["endpoint_id"], "Phase 8 endpoint coverage")
    report.unique_key(
        one_health, ["iso3", "year", "endpoint_id"], "Phase 8 One Health trends"
    )
    report.unique_key(
        rd_portfolio, ["year", "dimension", "category"], "Phase 8 R&D portfolio"
    )
    report.unique_key(
        rd_geography, ["iso3", "year"], "Phase 8 R&D geography"
    )
    report.unique_key(availability, ["iso3", "year"], "Phase 8 availability")
    report.add(
        "Phase 8: all public AMR cells meet suppression threshold",
        bool(one_health["n_tested"].ge(suppression_n).all()),
        {
            "threshold": suppression_n,
            "minimum": int(one_health["n_tested"].min()),
        },
    )

    outputs = {
        "endpoint_coverage": str(write_table(coverage, output_dir, "endpoint_coverage")),
        "one_health_country_year": str(
            write_table(one_health, output_dir, "one_health_country_year")
        ),
        "rd_annual_portfolio": str(
            write_table(rd_portfolio, output_dir, "rd_annual_portfolio")
        ),
        "rd_country_year": str(write_table(rd_geography, output_dir, "rd_country_year")),
        "data_availability": str(
            write_table(availability, output_dir, "data_availability")
        ),
    }
    report_path = output_dir / "phase8_table_validation.json"
    write_json({"passed": report.passed, "checks": report.checks, "outputs": outputs}, report_path)
    outputs["validation_report"] = str(report_path)
    if not report.passed:
        raise ValueError("Phase 8 table validation failed")
    return {"passed": True, "outputs": outputs, "checks": report.checks}
