from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


PRIMARY = ["ECO_CAZ_R", "KPN_CAZ_R", "KPN_MEM_R", "ABA_MEM_R"]
SECONDARY_MODEL = ["ECO_MEM_R", "PAE_MEM_R", "SAU_OXA_R", "ECO_CIP_R",
                   "KPN_CIP_R", "ECO_GEN_R", "KPN_GEN_R"]
EXPLORATORY_MODEL = ["KPN_COL_R"]
DESCRIPTIVE_ONLY = ["ECO_COL_R", "EFA_VAN_R", "SPN_ERY_R", "HIN_AMP_R", "GAS_ERY_R"]


def _write(frame: pd.DataFrame, output_dir: Path, name: str) -> Path:
    path = output_dir / f"{name}.csv"
    frame.to_csv(path, index=False)
    return path


def endpoint_feasibility(master: pd.DataFrame) -> pd.DataFrame:
    frame = master.loc[master["year"].between(2019, 2024)].copy()
    frame["base_cell"] = frame["n_tested"].ge(30) & frame["conflict_log2p1_events_lag1"].notna()
    rows: list[dict[str, object]] = []
    for endpoint, group in frame.groupby("endpoint_id"):
        base = group.loc[group["base_cell"]]
        country = base.groupby(["iso3", "country"], as_index=False).agg(
            eligible_years=("year", "nunique"),
            exposure_min=("conflict_log2p1_events_lag1", "min"),
            exposure_max=("conflict_log2p1_events_lag1", "max"),
        )
        n_three = country["eligible_years"].ge(3)
        n_vary = n_three & country["exposure_max"].gt(country["exposure_min"])
        if endpoint in PRIMARY:
            decision = "Confirmatory"
        elif endpoint in SECONDARY_MODEL:
            decision = "Secondary model"
        elif endpoint in EXPLORATORY_MODEL:
            decision = "Exploratory model"
        else:
            decision = "Descriptive only"
        rows.append({
            "endpoint_id": endpoint,
            "species": group["species"].iloc[0],
            "drug": group["drug"].iloc[0],
            "phase1_tier": group["analysis_tier"].iloc[0],
            "phase3_decision": decision,
            "tested_isolates": int(group["n_tested"].sum()),
            "resistant_isolates": int(group["n_resistant"].sum()),
            "represented_countries": int(group["iso3"].nunique()),
            "cells_n30": int(group["n_tested"].ge(30).sum()),
            "cells_n30_with_lagged_conflict": int(base.shape[0]),
            "countries_with_3_eligible_years": int(n_three.sum()),
            "countries_with_3_years_and_exposure_variation": int(n_vary.sum()),
            "calendar_years": int(group["year"].nunique()),
            "passes_numeric_model_rules": bool(
                group["n_tested"].sum() >= 5000 and group["n_resistant"].sum() >= 200
                and group["n_tested"].ge(30).sum() >= 100 and n_vary.sum() >= 20
                and group["year"].nunique() >= 5
            ),
        })
    return pd.DataFrame(rows).sort_values(["phase3_decision", "endpoint_id"])


def primary_model_lock(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    primary = master.loc[master["endpoint_id"].isin(PRIMARY) & master["year"].between(2019, 2024)].copy()
    primary["cell_n30"] = primary["n_tested"].ge(30)
    primary["lagged_conflict_available"] = primary["conflict_log2p1_events_lag1"].notna()
    primary["base_eligible"] = primary["cell_n30"] & primary["lagged_conflict_available"]
    country = primary.loc[primary["base_eligible"]].groupby(
        ["endpoint_id", "iso3", "country"], as_index=False
    ).agg(
        eligible_years=("year", "nunique"),
        first_eligible_year=("year", "min"),
        last_eligible_year=("year", "max"),
        eligible_cells=("year", "size"),
        tested_isolates=("n_tested", "sum"),
        conflict_events_min=("conflict_annual_events_lag1", "min"),
        conflict_events_max=("conflict_annual_events_lag1", "max"),
        conflict_log2p1_min=("conflict_log2p1_events_lag1", "min"),
        conflict_log2p1_max=("conflict_log2p1_events_lag1", "max"),
    )
    country["has_3_eligible_years"] = country["eligible_years"].ge(3)
    country["has_exposure_variation"] = country["conflict_log2p1_max"].gt(country["conflict_log2p1_min"])
    country["included_primary_model"] = country["has_3_eligible_years"] & country["has_exposure_variation"]
    keys = country.loc[country["included_primary_model"], ["endpoint_id", "iso3"]]
    final = primary.merge(keys.assign(_include=True), on=["endpoint_id", "iso3"], how="left")
    include = final["_include"].eq(True)
    final = final.loc[final["base_eligible"] & include].drop(columns="_include")
    summary = final.groupby("endpoint_id", as_index=False).agg(
        countries=("iso3", "nunique"), eligible_country_year_cells=("year", "size"),
        tested_isolates=("n_tested", "sum"), resistant_isolates=("n_resistant", "sum"),
        first_year=("year", "min"), last_year=("year", "max"),
    )
    return final, country.sort_values(["endpoint_id", "country"]), summary


def year_coverage(master: pd.DataFrame, final: pd.DataFrame) -> pd.DataFrame:
    primary = master.loc[master["endpoint_id"].isin(PRIMARY) & master["year"].between(2019, 2024)].copy()
    base = primary.groupby(["endpoint_id", "year"], as_index=False).agg(
        observed_cells=("iso3", "size"), cells_n30=("n_tested", lambda x: int(x.ge(30).sum())),
        tested_isolates=("n_tested", "sum"),
        cells_with_lagged_conflict=("conflict_log2p1_events_lag1", lambda x: int(x.notna().sum())),
    )
    locked = final.groupby(["endpoint_id", "year"], as_index=False).agg(
        final_countries=("iso3", "nunique"), final_cells=("iso3", "size"),
        final_tested_isolates=("n_tested", "sum"),
    )
    return base.merge(locked, on=["endpoint_id", "year"], how="left").fillna(0)


def external_overlap(final: pd.DataFrame) -> pd.DataFrame:
    livestock_cols = [c for c in final if c.startswith("livestock_livestock_units_")]
    indicators = {
        "Lagged annual temperature anomaly": final["temperature_temperature_anomaly_c_lag1"].notna(),
        "Lagged livestock-system data": final[livestock_cols].notna().any(axis=1),
        "Lagged adjusted animal AMU": final["animal_amu_total_mgkg_adjusted_lag1"].notna(),
        "Same-year R&D recipient commitments": final["rd_award_commitment_usd"].notna(),
    }
    rows = []
    for endpoint, group in final.groupby("endpoint_id"):
        for label, mask in indicators.items():
            selected = mask.loc[group.index]
            rows.append({
                "endpoint_id": endpoint, "external_variable": label,
                "eligible_cells": int(len(group)), "covered_cells": int(selected.sum()),
                "coverage_pct": float(100 * selected.mean()),
                "covered_countries": int(group.loc[selected, "iso3"].nunique()),
                "covered_tested_isolates": int(group.loc[selected, "n_tested"].sum()),
            })
    return pd.DataFrame(rows)


def missingness_audit(master: pd.DataFrame, acled: pd.DataFrame) -> pd.DataFrame:
    atlas = master.loc[master["endpoint_id"].isin(PRIMARY) & master["year"].between(2019, 2024),
                       ["endpoint_id", "iso3", "country", "year", "n_tested"]]
    grids = []
    for endpoint, group in atlas.groupby("endpoint_id"):
        countries = group[["iso3", "country"]].drop_duplicates()
        grid = pd.DataFrame(product(countries["iso3"], range(2019, 2025)), columns=["iso3", "year"])
        grid = grid.merge(countries, on="iso3", how="left")
        grid["endpoint_id"] = endpoint
        grids.append(grid)
    grid = pd.concat(grids, ignore_index=True).merge(
        atlas, on=["endpoint_id", "iso3", "country", "year"], how="left", validate="one_to_one"
    )
    lag = acled[["iso3", "year", "annual_events", "log2p1_events"]].copy()
    lag["year"] += 1
    grid = grid.merge(lag, on=["iso3", "year"], how="left", validate="many_to_one")
    grid["outcome_status"] = np.select(
        [grid["n_tested"].isna(), grid["n_tested"].lt(30)],
        ["No endpoint row", "Observed, n < 30"], default="Usable, n >= 30"
    )
    grid["within_country_rank"] = grid.groupby("iso3")["log2p1_events"].rank(pct=True, method="average")
    grid["conflict_intensity_group"] = pd.cut(
        grid["within_country_rank"], bins=[0, .25, .5, .75, 1], include_lowest=True,
        labels=["Lowest within-country", "Lower-middle", "Upper-middle", "Highest within-country"]
    )
    out = grid.dropna(subset=["conflict_intensity_group"]).groupby(
        ["endpoint_id", "conflict_intensity_group", "outcome_status"], observed=True
    ).size().rename("cells").reset_index()
    out["group_total"] = out.groupby(["endpoint_id", "conflict_intensity_group"], observed=True)["cells"].transform("sum")
    out["cell_pct"] = 100 * out["cells"] / out["group_total"]
    return out


def composition_audit(strata: pd.DataFrame, final: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = final[["endpoint_id", "iso3", "year"]].drop_duplicates()
    selected = strata.merge(keys, on=["endpoint_id", "iso3", "year"], how="inner")
    unknown_defs = {
        "gender": {"Unknown"}, "age_group": {"Unknown"},
        "speciality": {"None Given"}, "source": {"None Given", "Unknown"},
    }
    missing_rows = []
    for variable, unknown_values in unknown_defs.items():
        by_value = selected.groupby(variable, dropna=False)["n_tested"].sum()
        unavailable = int(sum(by_value.get(value, 0) for value in unknown_values) +
                          by_value.loc[by_value.index.isna()].sum())
        total = int(by_value.sum())
        missing_rows.append({"variable": variable, "unavailable_isolate_records": unavailable,
                             "total_isolate_records": total,
                             "unavailable_pct": 100 * unavailable / total if total else np.nan})
    shifts = []
    for variable in ["gender", "age_group", "speciality", "source"]:
        agg = selected.groupby(["endpoint_id", "iso3", "year", variable], dropna=False)["n_tested"].sum().reset_index()
        agg["proportion"] = agg["n_tested"] / agg.groupby(["endpoint_id", "iso3", "year"])["n_tested"].transform("sum")
        for (endpoint, iso3), group in agg.groupby(["endpoint_id", "iso3"]):
            years = sorted(group["year"].unique())
            for left, right in zip(years, years[1:]):
                if right - left != 1:
                    continue
                p = group.loc[group["year"].eq(left)].set_index(variable)["proportion"]
                q = group.loc[group["year"].eq(right)].set_index(variable)["proportion"]
                categories = p.index.union(q.index)
                tvd = .5 * (p.reindex(categories, fill_value=0) - q.reindex(categories, fill_value=0)).abs().sum()
                shifts.append({"variable": variable, "endpoint_id": endpoint, "iso3": iso3,
                               "year_from": left, "year_to": right, "total_variation_distance": float(tvd)})
    shift = pd.DataFrame(shifts)
    summary = shift.groupby("variable", as_index=False).agg(
        consecutive_pairs=("total_variation_distance", "size"),
        median_tvd=("total_variation_distance", "median"),
        p90_tvd=("total_variation_distance", lambda x: x.quantile(.90)),
        pairs_tvd_over_025=("total_variation_distance", lambda x: int(x.gt(.25).sum())),
    )
    return pd.DataFrame(missing_rows), summary


def escalation_candidates(acled: pd.DataFrame, master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    exposure = acled.loc[acled["year"].between(2018, 2023)].copy().sort_values(["iso3", "year"])
    exposure["previous_events"] = exposure.groupby("iso3")["annual_events"].shift(1)
    exposure["log2p1_change"] = exposure["log2p1_events"] - exposure.groupby("iso3")["log2p1_events"].shift(1)
    exposure["absolute_increase"] = exposure["annual_events"] - exposure["previous_events"]
    exposure["country_p75_2018_2023"] = exposure.groupby("iso3")["annual_events"].transform(lambda x: x.quantile(.75))
    exposure["meets_escalation_rule"] = (
        exposure["log2p1_change"].ge(1) & exposure["absolute_increase"].ge(20)
        & exposure["annual_events"].ge(exposure["country_p75_2018_2023"])
    )
    atlas_countries = set(master.loc[master["endpoint_id"].isin(PRIMARY) & master["year"].between(2019, 2024), "iso3"])
    candidates = exposure.loc[exposure["meets_escalation_rule"] & exposure["iso3"].isin(atlas_countries),
                              ["iso3", "country", "year", "previous_events", "annual_events",
                               "absolute_increase", "log2p1_change", "country_p75_2018_2023"]].copy()
    candidates = candidates.rename(columns={"year": "escalation_year"})
    candidates["response_index_year"] = candidates["escalation_year"] + 1
    candidates["first_qualifying_event_for_country"] = ~candidates.duplicated("iso3")

    observed = master.loc[master["endpoint_id"].isin(PRIMARY) & master["year"].between(2019, 2024) &
                          master["n_tested"].ge(30), ["iso3", "endpoint_id", "year"]]
    windows = []
    for event in candidates.itertuples(index=False):
        for endpoint in PRIMARY:
            years = set(observed.loc[(observed["iso3"].eq(event.iso3)) &
                                     (observed["endpoint_id"].eq(endpoint)), "year"])
            rel = {k: int(event.response_index_year + k in years) for k in [-2, -1, 0, 1, 2]}
            windows.append({
                "iso3": event.iso3, "country": event.country, "escalation_year": event.escalation_year,
                "response_index_year": event.response_index_year, "endpoint_id": endpoint,
                "n_pre_cells": rel[-2] + rel[-1], "index_cell": rel[0],
                "n_post_cells": rel[1] + rel[2], "five_year_cells": sum(rel.values()),
                "minimal_pre_post_eligible": bool((rel[-2] + rel[-1]) >= 1 and rel[0] == 1 and
                                                  (rel[1] + rel[2]) >= 1),
            })
    return candidates.sort_values(["escalation_year", "country"]), pd.DataFrame(windows)


def run_phase3(processed_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(processed_dir / "restricted" / "master_country_year_endpoint.csv.gz")
    strata = pd.read_csv(processed_dir / "restricted" / "atlas_composition_strata.csv.gz")
    isolates = pd.read_csv(processed_dir / "restricted" / "atlas_endpoint_isolates.csv.gz")
    acled = pd.read_csv(processed_dir / "acled_country_year.csv.gz")

    endpoint = endpoint_feasibility(master)
    final, country, model_summary = primary_model_lock(master)
    year = year_coverage(master, final)
    external = external_overlap(final)
    missingness = missingness_audit(master, acled)
    composition_missing, composition_shift = composition_audit(strata, final)
    escalations, event_windows = escalation_candidates(acled, master)

    final_keys = final[["endpoint_id", "iso3", "year"]].drop_duplicates()
    final_isolates = isolates.merge(final_keys, on=["endpoint_id", "iso3", "year"], how="inner")
    totals = {
        "primary_endpoint_cells_before_lock": int(master.loc[master["endpoint_id"].isin(PRIMARY) &
                                                                  master["year"].between(2019, 2024)].shape[0]),
        "primary_endpoint_cells_n30": int(master.loc[master["endpoint_id"].isin(PRIMARY) &
                                                       master["year"].between(2019, 2024), "n_tested"].ge(30).sum()),
        "final_primary_endpoint_cells": int(len(final)),
        "final_endpoint_isolate_records": int(len(final_isolates)),
        "final_unique_isolates": int(final_isolates["isolate_id"].nunique()),
        "event_candidates_in_atlas": int(len(escalations)),
        "event_country_endpoint_windows_minimal_pre_post": int(event_windows["minimal_pre_post_eligible"].sum()),
    }
    outputs = {
        "endpoint_feasibility": _write(endpoint, output_dir, "01_endpoint_feasibility"),
        "primary_model_summary": _write(model_summary, output_dir, "02_primary_model_summary"),
        "primary_year_coverage": _write(year, output_dir, "03_primary_year_coverage"),
        "primary_country_eligibility": _write(country, output_dir, "04_primary_country_eligibility"),
        "external_overlap": _write(external, output_dir, "05_external_overlap"),
        "missingness_by_conflict_intensity": _write(missingness, output_dir, "06_missingness_by_conflict_intensity"),
        "composition_missingness": _write(composition_missing, output_dir, "07_composition_missingness"),
        "composition_shift": _write(composition_shift, output_dir, "08_composition_shift"),
        "escalation_candidates": _write(escalations, output_dir, "09_escalation_candidates"),
        "event_study_windows": _write(event_windows, output_dir, "10_event_study_windows"),
    }
    final.to_csv(processed_dir / "restricted" / "phase3_primary_model_cells.csv.gz", index=False, compression="gzip")
    payload = {"totals": totals, "outputs": {k: str(v) for k, v in outputs.items()}}
    (output_dir / "phase3_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
