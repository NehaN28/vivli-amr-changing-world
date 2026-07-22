from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from .phase3 import PRIMARY
from .phase4 import CATEGORICAL, ENDPOINT_LABELS, EXPOSURE, TEMPERATURE, _load_analysis_data


BASE_ADJUSTMENT = "C(year) + C(iso3) + C(gender) + C(age_group) + C(speciality) + C(source)"
LIVESTOCK_SHARE_COLUMNS = {
    "cattle_buffalo_share_10pp": "livestock_livestock_unit_share_cattle_buffalo_lag1",
    "poultry_share_10pp": "livestock_livestock_unit_share_poultry_lag1",
    "swine_share_10pp": "livestock_livestock_unit_share_swine_lag1",
}


def _fit_clustered_logistic(
    frame: pd.DataFrame, formula: str, term: str, analysis: str, endpoint: str,
) -> dict[str, object]:
    result = smf.glm(formula, data=frame, family=sm.families.Binomial()).fit(
        cov_type="cluster",
        cov_kwds={"groups": frame["iso3"], "use_correction": True},
        use_t=True,
        maxiter=100,
        disp=False,
    )
    ci = result.conf_int().loc[term]
    return {
        "analysis": analysis,
        "endpoint_id": endpoint,
        "endpoint": ENDPOINT_LABELS[endpoint],
        "term": term,
        "beta_log_odds": float(result.params[term]),
        "odds_ratio": float(np.exp(result.params[term])),
        "or_ci_low": float(np.exp(ci.iloc[0])),
        "or_ci_high": float(np.exp(ci.iloc[1])),
        "p_value": float(result.pvalues[term]),
        "tested_isolates": int(len(frame)),
        "resistant_isolates": int(frame["resistant"].sum()),
        "countries": int(frame["iso3"].nunique()),
        "country_year_cells": int(frame.groupby(["iso3", "year"]).ngroups),
        "converged": bool(result.converged),
        "few_cluster_warning": bool(frame["iso3"].nunique() < 20),
    }


def _livestock_country_year(processed_dir: Path) -> pd.DataFrame:
    livestock = pd.read_csv(processed_dir / "livestock_country_year_group.csv.gz")
    total = livestock.groupby(["iso3", "year"], as_index=False).agg(
        total_livestock_units=("livestock_units", "sum")
    )
    total["log2_total_livestock_units"] = np.log2(total["total_livestock_units"].clip(lower=1))
    shares = livestock.pivot_table(
        index=["iso3", "year"], columns="livestock_group",
        values="livestock_unit_share", aggfunc="first",
    ).reset_index()
    shares.columns.name = None
    out = total.merge(shares, on=["iso3", "year"], how="left", validate="one_to_one")
    out["year"] += 1
    return out


def one_health_models(processed_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    data, _, _ = _load_analysis_data(processed_dir)
    livestock = _livestock_country_year(processed_dir)
    livestock_cols = ["iso3", "year", "log2_total_livestock_units", "cattle_buffalo", "poultry", "swine"]
    data = data.merge(livestock[livestock_cols], on=["iso3", "year"], how="left", validate="many_to_one")
    data["cattle_buffalo_share_10pp"] = 10 * data["cattle_buffalo"]
    data["poultry_share_10pp"] = 10 * data["poultry"]
    data["swine_share_10pp"] = 10 * data["swine"]

    rows: list[dict[str, object]] = []
    for endpoint in PRIMARY:
        base = data.loc[data["endpoint_id"].eq(endpoint)].copy()
        specifications = [
            ("Lagged temperature anomaly", TEMPERATURE, "Per 1 °C", base),
            ("Lagged total livestock units", "log2_total_livestock_units", "Per doubling", base),
            ("Lagged cattle/buffalo livestock-unit share", "cattle_buffalo_share_10pp", "Per 10 percentage points", base),
            ("Lagged poultry livestock-unit share", "poultry_share_10pp", "Per 10 percentage points", base),
            ("Lagged swine livestock-unit share", "swine_share_10pp", "Per 10 percentage points", base),
        ]
        for label, term, scale, frame in specifications:
            complete = frame.dropna(subset=[term]).copy()
            formula = f"resistant ~ {term} + {EXPOSURE} + {BASE_ADJUSTMENT}"
            row = _fit_clustered_logistic(complete, formula, term, label, endpoint)
            row["effect_scale"] = scale
            row["analysis_family"] = "determinant_main_effect"
            rows.append(row)

        interactions = [
            ("Conflict × temperature", TEMPERATURE, "Conflict doubling × 1 °C"),
            ("Conflict × total livestock units", "log2_total_livestock_units", "Conflict doubling × livestock-unit doubling"),
            ("Conflict × cattle/buffalo share", "cattle_buffalo_share_10pp", "Conflict doubling × 10 percentage points"),
            ("Conflict × poultry share", "poultry_share_10pp", "Conflict doubling × 10 percentage points"),
            ("Conflict × swine share", "swine_share_10pp", "Conflict doubling × 10 percentage points"),
        ]
        for label, moderator, scale in interactions:
            complete = base.dropna(subset=[moderator]).copy()
            complete[f"centered_{moderator}"] = complete[moderator] - complete[moderator].mean()
            centered = f"centered_{moderator}"
            term = f"{EXPOSURE}:{centered}"
            formula = f"resistant ~ {EXPOSURE} * {centered} + {BASE_ADJUSTMENT}"
            row = _fit_clustered_logistic(complete, formula, term, label, endpoint)
            row["effect_scale"] = scale
            row["analysis_family"] = "conflict_effect_modification"
            rows.append(row)

    estimates = pd.DataFrame(rows)
    estimates["fdr_p"] = np.nan
    for family, index in estimates.groupby("analysis_family").groups.items():
        estimates.loc[index, "fdr_p"] = multipletests(
            estimates.loc[index, "p_value"], method="fdr_bh"
        )[1]
    estimates["fdr_significant_005"] = estimates["fdr_p"].lt(0.05)
    coverage = estimates[[
        "analysis_family", "analysis", "endpoint_id", "tested_isolates", "countries",
        "country_year_cells", "few_cluster_warning",
    ]].copy()
    return estimates, coverage


def woah_models(processed_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    data, _, _ = _load_analysis_data(processed_dir)
    totals = pd.read_csv(processed_dir / "woah_country_year.csv.gz")[[
        "iso3", "year", "total_mgkg_adjusted", "total_mgkg_unadjusted",
    ]]
    totals["year"] += 1
    totals["log2p1_total_adjusted_mgkg"] = np.log2(1 + totals["total_mgkg_adjusted"])
    totals["log2p1_total_unadjusted_mgkg"] = np.log2(1 + totals["total_mgkg_unadjusted"])
    classes = pd.read_csv(processed_dir / "woah_class_long.csv.gz")
    classes = classes.loc[classes["antimicrobial_class"].eq("Cephalosporins (all generations)"), [
        "iso3", "year", "estimated_class_mgkg_adjusted",
    ]].rename(columns={"estimated_class_mgkg_adjusted": "cephalosporin_mgkg_adjusted"})
    classes["year"] += 1
    classes["log2p1_cephalosporin_mgkg_adjusted"] = np.log2(1 + classes["cephalosporin_mgkg_adjusted"])
    data = data.merge(totals, on=["iso3", "year"], how="left", validate="many_to_one")
    data = data.merge(classes, on=["iso3", "year"], how="left", validate="many_to_one")

    rows = []
    for endpoint in PRIMARY:
        base = data.loc[data["endpoint_id"].eq(endpoint)].copy()
        specs = [
            ("Adjusted total animal AMU", "log2p1_total_adjusted_mgkg", "Per doubling of 1 + mg/kg"),
            ("Unadjusted total animal AMU sensitivity", "log2p1_total_unadjusted_mgkg", "Per doubling of 1 + mg/kg"),
        ]
        if endpoint in {"ECO_CAZ_R", "KPN_CAZ_R"}:
            specs.append((
                "Aligned animal cephalosporin AMU proxy",
                "log2p1_cephalosporin_mgkg_adjusted",
                "Per doubling of 1 + mg/kg; all cephalosporin generations",
            ))
        for label, term, scale in specs:
            complete = base.dropna(subset=[term]).copy()
            if complete["iso3"].nunique() < 5:
                continue
            formula = f"resistant ~ {term} + {EXPOSURE} + {TEMPERATURE} + {BASE_ADJUSTMENT}"
            row = _fit_clustered_logistic(complete, formula, term, label, endpoint)
            row["effect_scale"] = scale
            row["analysis_family"] = "woah_animal_amu"
            rows.append(row)

            centered = f"centered_{term}"
            complete[centered] = complete[term] - complete[term].mean()
            interaction = f"{EXPOSURE}:{centered}"
            formula_i = f"resistant ~ {EXPOSURE} * {centered} + {TEMPERATURE} + {BASE_ADJUSTMENT}"
            row_i = _fit_clustered_logistic(
                complete, formula_i, interaction, f"Conflict × {label.lower()}", endpoint
            )
            row_i["effect_scale"] = f"Conflict doubling × {scale.lower()}"
            row_i["analysis_family"] = "woah_effect_modification"
            rows.append(row_i)

    estimates = pd.DataFrame(rows)
    estimates["fdr_p"] = np.nan
    for family, index in estimates.groupby("analysis_family").groups.items():
        estimates.loc[index, "fdr_p"] = multipletests(
            estimates.loc[index, "p_value"], method="fdr_bh"
        )[1]
    estimates["fdr_significant_005"] = estimates["fdr_p"].lt(0.05)
    coverage = estimates[[
        "analysis_family", "analysis", "endpoint_id", "tested_isolates", "countries",
        "country_year_cells", "few_cluster_warning",
    ]].copy()
    return estimates, coverage


def rd_alignment(processed_dir: Path, phase4_dir: Path) -> dict[str, pd.DataFrame]:
    projects = pd.read_csv(processed_dir / "rd_projects_clean.csv.gz")
    fractional = pd.read_csv(processed_dir / "rd_fractional_categories.csv.gz")
    window_projects = projects.loc[projects["start_year"].between(2015, 2024)].copy()
    ids = set(window_projects["project_id"])
    frac = fractional.loc[fractional["project_id"].isin(ids)].copy()

    pathogen = frac.loc[frac["dimension"].eq("pathogen")].groupby("category", as_index=False).agg(
        fractional_projects=("fractional_project_count", "sum"),
        fractional_funding_usd=("fractional_amount_usd", "sum"),
    ).rename(columns={"category": "pathogen"})
    specific = ~pathogen["pathogen"].eq("Not pathogen-specific")
    pathogen["share_of_pathogen_specific_funding_pct"] = np.where(
        specific,
        100 * pathogen["fractional_funding_usd"] / pathogen.loc[specific, "fractional_funding_usd"].sum(),
        np.nan,
    )

    standardised = pd.read_csv(phase4_dir / "standardised_amr.csv")
    endpoint_species = {
        "ECO_CAZ_R": "Escherichia coli", "KPN_CAZ_R": "Klebsiella pneumoniae",
        "KPN_MEM_R": "Klebsiella pneumoniae", "ABA_MEM_R": "Acinetobacter baumannii",
    }
    standardised["pathogen"] = standardised["endpoint_id"].map(endpoint_species)
    annual = standardised.groupby(["pathogen", "year"], as_index=False).agg(
        equal_country_standardised_pct=("standardised_resistance_pct", "mean"),
        countries=("iso3", "nunique"),
    )
    burden_rows = []
    for species, group in annual.groupby("pathogen"):
        slope = np.polyfit(group["year"], group["equal_country_standardised_pct"], 1)[0]
        latest = group.loc[group["year"].eq(group["year"].max()), "equal_country_standardised_pct"].iloc[0]
        burden_rows.append({
            "pathogen": species, "latest_standardised_resistance_pct": float(latest),
            "annual_change_pp": float(slope), "amr_years": int(group["year"].nunique()),
        })
    alignment = pathogen.merge(pd.DataFrame(burden_rows), on="pathogen", how="left")
    alignment["funding_rank_specific_pathogens"] = alignment.loc[specific, "fractional_funding_usd"].rank(
        ascending=False, method="min"
    )
    observed = alignment["latest_standardised_resistance_pct"].notna()
    alignment.loc[observed, "resistance_rank_observed_pathogens"] = alignment.loc[
        observed, "latest_standardised_resistance_pct"
    ].rank(ascending=False, method="min")

    sector = frac.loc[frac["dimension"].eq("sector")].groupby("category", as_index=False).agg(
        fractional_projects=("fractional_project_count", "sum"),
        fractional_funding_usd=("fractional_amount_usd", "sum"),
    ).rename(columns={"category": "sector"})
    sector["funding_share_pct"] = 100 * sector["fractional_funding_usd"] / sector["fractional_funding_usd"].sum()

    area = frac.loc[frac["dimension"].eq("research_area")].groupby("category", as_index=False).agg(
        fractional_projects=("fractional_project_count", "sum"),
        fractional_funding_usd=("fractional_amount_usd", "sum"),
    ).rename(columns={"category": "research_area"})
    area["funding_share_pct"] = 100 * area["fractional_funding_usd"] / area["fractional_funding_usd"].sum()

    cross_sector = window_projects.assign(
        sector_count=window_projects["sector"].fillna("Not Specified").str.count(",") + 1,
        one_health_cross_sector=window_projects["sector"].fillna("").str.contains(","),
    ).groupby("one_health_cross_sector", as_index=False).agg(
        projects=("project_id", "nunique"), funding_usd=("amount_usd", "sum")
    )
    cross_sector["funding_share_pct"] = 100 * cross_sector["funding_usd"] / cross_sector["funding_usd"].sum()

    geography = window_projects.groupby(["iso3", "country"], dropna=False, as_index=False).agg(
        recipient_projects=("project_id", "nunique"), recipient_funding_usd=("amount_usd", "sum")
    ).sort_values("recipient_funding_usd", ascending=False)

    return {
        "rd_pathogen_alignment": alignment.sort_values("fractional_funding_usd", ascending=False),
        "rd_sector_portfolio": sector.sort_values("fractional_funding_usd", ascending=False),
        "rd_research_area_portfolio": area.sort_values("fractional_funding_usd", ascending=False),
        "rd_cross_sector_portfolio": cross_sector,
        "rd_recipient_geography": geography,
        "rd_amr_annual_context": annual,
    }


def country_context_profile(processed_dir: Path, phase4_dir: Path) -> pd.DataFrame:
    """Dashboard-oriented component profile; deliberately no composite vulnerability score."""
    standardised = pd.read_csv(phase4_dir / "standardised_amr.csv")
    latest = standardised.loc[standardised["year"].eq(2024)].groupby(
        ["iso3", "country"], as_index=False
    ).agg(
        endpoints_in_2024=("endpoint_id", "nunique"),
        mean_standardised_resistance_pct_2024=("standardised_resistance_pct", "mean"),
        total_tested_isolates_2024=("n_tested", "sum"),
    )
    slopes = []
    for (iso3, country), group in standardised.groupby(["iso3", "country"]):
        annual = group.groupby("year", as_index=False)["standardised_resistance_pct"].mean()
        if len(annual) >= 3:
            slope = float(np.polyfit(annual["year"], annual["standardised_resistance_pct"], 1)[0])
        else:
            slope = np.nan
        slopes.append({
            "iso3": iso3, "country": country, "amr_years": int(len(annual)),
            "mean_amr_change_pp_per_year": slope,
        })
    profile = latest.merge(pd.DataFrame(slopes), on=["iso3", "country"], how="left")

    acled = pd.read_csv(processed_dir / "acled_country_year.csv.gz")
    acled = acled.loc[acled["year"].eq(2023), ["iso3", "annual_events", "log2p1_events"]].rename(columns={
        "annual_events": "conflict_events_2023", "log2p1_events": "conflict_log2p1_2023",
    })
    temperature = pd.read_csv(processed_dir / "temperature_country_year.csv.gz")
    temperature = temperature.loc[temperature["year"].eq(2023), [
        "iso3", "temperature_anomaly_c", "standardised_anomaly",
    ]].rename(columns={
        "temperature_anomaly_c": "temperature_anomaly_c_2023",
        "standardised_anomaly": "temperature_standardised_anomaly_2023",
    })
    livestock = _livestock_country_year(processed_dir)
    livestock = livestock.loc[livestock["year"].eq(2024), [
        "iso3", "total_livestock_units", "cattle_buffalo", "poultry", "swine",
    ]].rename(columns={
        "total_livestock_units": "livestock_units_2023",
        "cattle_buffalo": "cattle_buffalo_lu_share_2023",
        "poultry": "poultry_lu_share_2023", "swine": "swine_lu_share_2023",
    })
    woah = pd.read_csv(processed_dir / "woah_country_year.csv.gz")
    woah = woah.loc[woah["year"].eq(2023), ["iso3", "total_mgkg_adjusted"]].rename(
        columns={"total_mgkg_adjusted": "animal_amu_adjusted_mgkg_2023"}
    )
    projects = pd.read_csv(processed_dir / "rd_projects_clean.csv.gz")
    funding = projects.loc[projects["start_year"].between(2015, 2024)].groupby(
        "iso3", as_index=False, dropna=False
    ).agg(
        recipient_projects_2015_2024=("project_id", "nunique"),
        recipient_funding_usd_2015_2024=("amount_usd", "sum"),
    )
    for context in [acled, temperature, livestock, woah, funding]:
        profile = profile.merge(context, on="iso3", how="left", validate="one_to_one")
    component_columns = [
        "mean_standardised_resistance_pct_2024", "mean_amr_change_pp_per_year",
        "conflict_events_2023", "temperature_anomaly_c_2023", "livestock_units_2023",
        "animal_amu_adjusted_mgkg_2023", "recipient_funding_usd_2015_2024",
    ]
    profile["context_components_available"] = profile[component_columns].notna().sum(axis=1)
    profile["context_components_total"] = len(component_columns)
    profile["composite_score_constructed"] = False
    return profile.sort_values("country")


def run_phase5(processed_dir: Path, phase4_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    one_health, one_health_coverage = one_health_models(processed_dir)
    woah, woah_coverage = woah_models(processed_dir)
    outputs: dict[str, pd.DataFrame] = {
        "one_health_models": one_health,
        "one_health_coverage": one_health_coverage,
        "woah_models": woah,
        "woah_coverage": woah_coverage,
        **rd_alignment(processed_dir, phase4_dir),
        "country_context_profile": country_context_profile(processed_dir, phase4_dir),
    }
    paths = {}
    for name, table in outputs.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        paths[name] = str(path)
    summary = {
        "phase": 5,
        "pipeline_version": "0.5.0",
        "confirmatory_status": "All Phase 5 analyses are secondary or exploratory",
        "one_health_models": int(len(one_health)),
        "woah_models": int(len(woah)),
        "all_models_converged": bool(one_health["converged"].all() and woah["converged"].all()),
        "outputs": paths,
    }
    (output_dir / "phase5_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
