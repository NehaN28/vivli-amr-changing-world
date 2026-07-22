from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.special import expit
from scipy.stats import norm, t
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

from .phase3 import PRIMARY, escalation_candidates


EXPOSURE = "conflict_log2p1_events_lag1"
TEMPERATURE = "temperature_temperature_anomaly_c_lag1"
CATEGORICAL = ["gender", "age_group", "speciality", "source"]
MAIN_FORMULA = (
    f"resistant ~ {EXPOSURE} + {TEMPERATURE} + C(year) + C(iso3) + "
    "C(gender) + C(age_group) + C(speciality) + C(source)"
)
ENDPOINT_LABELS = {
    "ECO_CAZ_R": "E. coli–ceftazidime",
    "KPN_CAZ_R": "K. pneumoniae–ceftazidime",
    "KPN_MEM_R": "K. pneumoniae–meropenem",
    "ABA_MEM_R": "A. baumannii–meropenem",
}


def holm_adjust(pvalues: pd.Series) -> pd.Series:
    """Holm family-wise-error adjustment, preserving the input index."""
    p = pvalues.astype(float)
    order = np.argsort(p.to_numpy())
    ranked = p.to_numpy()[order]
    adjusted = np.maximum.accumulate((len(p) - np.arange(len(p))) * ranked)
    adjusted = np.minimum(adjusted, 1.0)
    out = np.empty(len(p), dtype=float)
    out[order] = adjusted
    return pd.Series(out, index=p.index)


def _load_analysis_data(processed_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    isolates = pd.read_csv(processed_dir / "restricted" / "atlas_endpoint_isolates.csv.gz")
    cells = pd.read_csv(processed_dir / "restricted" / "phase3_primary_model_cells.csv.gz")
    acled = pd.read_csv(processed_dir / "acled_country_year.csv.gz")
    columns = [
        "endpoint_id", "iso3", "country", "year", "n_tested", "n_resistant",
        EXPOSURE, TEMPERATURE,
    ]
    keep = cells[columns].copy()
    data = isolates.merge(
        keep[["endpoint_id", "iso3", "year", EXPOSURE, TEMPERATURE]],
        on=["endpoint_id", "iso3", "year"], how="inner", validate="many_to_one",
    )
    data = data.loc[data["interpretation"].isin(["S", "I", "R"])].copy()
    data["resistant"] = data["interpretation"].eq("R").astype(int)
    for column in CATEGORICAL:
        data[column] = data[column].fillna("Unknown").astype(str)
    return data, keep, acled


def _wild_cluster_one_step(
    result: object, data: pd.DataFrame, exposure_name: str, replications: int, seed: int,
) -> dict[str, float]:
    """One-step Rademacher wild-cluster interval plus null score-test p value.

    The interval uses cluster score perturbations around the unrestricted MLE.
    The p value uses a nuisance-residualised score under the restricted null.
    """
    x = np.asarray(result.model.exog, dtype=float)
    y = np.asarray(result.model.endog, dtype=float)
    mu = np.asarray(result.fittedvalues, dtype=float)
    names = list(result.model.exog_names)
    j = names.index(exposure_name)
    groups = data["iso3"].astype(str).to_numpy()
    levels = np.unique(groups)
    w = np.clip(mu * (1 - mu), 1e-8, None)
    bread = np.linalg.pinv(x.T @ (w[:, None] * x))
    scores = np.vstack([
        x[groups == g].T @ (y[groups == g] - mu[groups == g]) for g in levels
    ])
    influence = scores @ bread[j, :]
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(replications, len(levels)))
    deltas = signs @ influence
    beta = float(result.params.iloc[j])
    q025, q975 = np.quantile(deltas, [0.025, 0.975])

    restricted_formula = MAIN_FORMULA.replace(f"{exposure_name} + ", "")
    restricted = smf.glm(
        restricted_formula, data=data, family=sm.families.Binomial()
    ).fit(maxiter=100, disp=False)
    z = np.asarray(restricted.model.exog, dtype=float)
    p0 = np.asarray(restricted.fittedvalues, dtype=float)
    w0 = np.clip(p0 * (1 - p0), 1e-8, None)
    raw_exposure = data[exposure_name].to_numpy(dtype=float)
    gamma = np.linalg.pinv(z.T @ (w0[:, None] * z)) @ (z.T @ (w0 * raw_exposure))
    residual_exposure = raw_exposure - z @ gamma
    cluster_score = np.array([
        np.sum(residual_exposure[groups == g] * (y[groups == g] - p0[groups == g]))
        for g in levels
    ])
    denominator = math.sqrt(float(np.sum(cluster_score**2)))
    observed = float(np.sum(cluster_score) / denominator) if denominator else np.nan
    boot = (signs @ cluster_score) / denominator if denominator else np.full(replications, np.nan)
    pvalue = (1 + np.sum(np.abs(boot) >= abs(observed))) / (replications + 1)
    return {
        "wild_bootstrap_reps": replications,
        "wild_bootstrap_p": float(pvalue),
        "wild_bootstrap_beta_ci_low": float(beta - q975),
        "wild_bootstrap_beta_ci_high": float(beta - q025),
        "wild_bootstrap_or_ci_low": float(np.exp(beta - q975)),
        "wild_bootstrap_or_ci_high": float(np.exp(beta - q025)),
    }


def _average_marginal_risk_difference(result: object) -> tuple[float, float, float]:
    x = np.asarray(result.model.exog, dtype=float)
    names = list(result.model.exog_names)
    j = names.index(EXPOSURE)
    beta = np.asarray(result.params, dtype=float)
    x1 = x.copy()
    x1[:, j] += 1.0
    p0 = expit(x @ beta)
    p1 = expit(x1 @ beta)
    difference = float(np.mean(p1 - p0))
    gradient = np.mean(
        p1[:, None] * (1 - p1[:, None]) * x1
        - p0[:, None] * (1 - p0[:, None]) * x,
        axis=0,
    )
    covariance = np.asarray(result.cov_params(), dtype=float)
    standard_error = math.sqrt(max(float(gradient @ covariance @ gradient), 0.0))
    clusters = int(result.model.data.frame["iso3"].nunique())
    critical = t.ppf(0.975, max(clusters - 1, 1))
    return difference, difference - critical * standard_error, difference + critical * standard_error


def _influence_summary(result: object, data: pd.DataFrame) -> dict[str, object]:
    x = np.asarray(result.model.exog, dtype=float)
    y = np.asarray(result.model.endog, dtype=float)
    mu = np.asarray(result.fittedvalues, dtype=float)
    names = list(result.model.exog_names)
    j = names.index(EXPOSURE)
    groups = data["iso3"].astype(str).to_numpy()
    w = np.clip(mu * (1 - mu), 1e-8, None)
    hessian = x.T @ (w[:, None] * x)
    beta = np.asarray(result.params, dtype=float)
    estimates = []
    for group in np.unique(groups):
        select = groups == group
        hg = x[select].T @ (w[select, None] * x[select])
        score = x[select].T @ (y[select] - mu[select])
        deleted = beta - np.linalg.pinv(hessian - hg) @ score
        estimates.append((group, float(deleted[j])))
    most = max(estimates, key=lambda item: abs(item[1] - beta[j]))
    return {
        "most_influential_iso3": most[0],
        "leave_one_cluster_beta": most[1],
        "max_abs_beta_change": abs(most[1] - float(beta[j])),
        "leave_one_cluster_or_min": float(np.exp(min(v for _, v in estimates))),
        "leave_one_cluster_or_max": float(np.exp(max(v for _, v in estimates))),
    }


def fit_confirmatory_models(
    data: pd.DataFrame, replications: int = 9999, seed: int = 20260723,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, diagnostics = [], []
    for index, endpoint in enumerate(PRIMARY):
        frame = data.loc[data["endpoint_id"].eq(endpoint)].copy()
        model = smf.glm(MAIN_FORMULA, data=frame, family=sm.families.Binomial())
        result = model.fit(
            cov_type="cluster", cov_kwds={"groups": frame["iso3"], "use_correction": True},
            use_t=True, maxiter=100, disp=False,
        )
        beta = float(result.params[EXPOSURE])
        se = float(result.bse[EXPOSURE])
        ci = result.conf_int().loc[EXPOSURE]
        risk, risk_low, risk_high = _average_marginal_risk_difference(result)
        wild = _wild_cluster_one_step(result, frame, EXPOSURE, replications, seed + index)
        influence = _influence_summary(result, frame)
        rows.append({
            "endpoint_id": endpoint, "endpoint": ENDPOINT_LABELS[endpoint],
            "tested_isolates": int(len(frame)), "resistant_isolates": int(frame["resistant"].sum()),
            "countries": int(frame["iso3"].nunique()), "country_year_cells": int(frame.groupby(["iso3", "year"]).ngroups),
            "beta_log_odds": beta, "cluster_se": se, "or_per_doubling_1plus_events": float(np.exp(beta)),
            "or_ci_low": float(np.exp(ci.iloc[0])), "or_ci_high": float(np.exp(ci.iloc[1])),
            "cluster_t_p": float(result.pvalues[EXPOSURE]),
            "average_marginal_risk_difference": risk,
            "amrd_ci_low": risk_low, "amrd_ci_high": risk_high,
            **wild,
        })
        diagnostics.append({
            "endpoint_id": endpoint, "converged": bool(result.converged),
            "iterations": int(result.fit_history.get("iteration", -1)),
            "parameters": int(len(result.params)), "clusters": int(frame["iso3"].nunique()),
            "pearson_dispersion": float(result.pearson_chi2 / result.df_resid),
            "minimum_fitted_probability": float(np.min(result.fittedvalues)),
            "maximum_fitted_probability": float(np.max(result.fittedvalues)),
            **influence,
        })
    estimates = pd.DataFrame(rows)
    estimates["holm_p"] = holm_adjust(estimates["cluster_t_p"])
    estimates["confirmatory_holm_significant_005"] = estimates["holm_p"].lt(0.05)
    return estimates, pd.DataFrame(diagnostics)


def _fit_alternative(frame: pd.DataFrame, formula: str, exposure: str) -> dict[str, float]:
    result = smf.glm(formula, data=frame, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": frame["iso3"], "use_correction": True},
        use_t=True, maxiter=100, disp=False,
    )
    ci = result.conf_int().loc[exposure]
    return {
        "beta_log_odds": float(result.params[exposure]),
        "or": float(np.exp(result.params[exposure])),
        "or_ci_low": float(np.exp(ci.iloc[0])), "or_ci_high": float(np.exp(ci.iloc[1])),
        "p_value": float(result.pvalues[exposure]), "tested_isolates": int(len(frame)),
        "countries": int(frame["iso3"].nunique()),
        "country_year_cells": int(frame.groupby(["iso3", "year"]).ngroups),
    }


def sensitivity_models(data: pd.DataFrame, cells: pd.DataFrame, acled: pd.DataFrame) -> pd.DataFrame:
    exposure = acled[["iso3", "year", "log2p1_events"]].copy()
    rows = []
    for endpoint in PRIMARY:
        base = data.loc[data["endpoint_id"].eq(endpoint)].copy()
        specifications: list[tuple[str, pd.DataFrame, str, str]] = [
            ("Unadjusted composition; country/year FE", base,
             f"resistant ~ {EXPOSURE} + C(year) + C(iso3)", EXPOSURE),
            ("Complete-case covariates", base.loc[~base[CATEGORICAL].eq("Unknown").any(axis=1)],
             MAIN_FORMULA, EXPOSURE),
        ]
        country_outcome = base.groupby("iso3")["resistant"].agg(["min", "max"])
        varying_countries = country_outcome.index[country_outcome["min"].lt(country_outcome["max"])]
        specifications.append((
            "Exclude countries without outcome variation",
            base.loc[base["iso3"].isin(varying_countries)], MAIN_FORMULA, EXPOSURE,
        ))
        cell50 = cells.loc[cells["endpoint_id"].eq(endpoint) & cells["n_tested"].ge(50),
                           ["endpoint_id", "iso3", "year"]]
        specifications.append(("Minimum cell n=50", base.merge(cell50, on=["endpoint_id", "iso3", "year"], how="inner"),
                               MAIN_FORMULA, EXPOSURE))
        for lag, label in [(0, "Same-year conflict"), (2, "Two-year lagged conflict")]:
            lagged = exposure.rename(columns={"log2p1_events": f"conflict_lag{lag}"}).copy()
            lagged["year"] += lag
            alt = base.drop(columns=[f"conflict_lag{lag}"], errors="ignore").merge(
                lagged, on=["iso3", "year"], how="left", validate="many_to_one"
            ).dropna(subset=[f"conflict_lag{lag}"])
            formula = MAIN_FORMULA.replace(EXPOSURE, f"conflict_lag{lag}")
            specifications.append((label, alt, formula, f"conflict_lag{lag}"))
        for label, frame, formula, exposure_name in specifications:
            if frame["iso3"].nunique() < 10 or frame.empty:
                continue
            rows.append({"endpoint_id": endpoint, "specification": label,
                         **_fit_alternative(frame, formula, exposure_name)})
    return pd.DataFrame(rows)


def standardised_estimates(
    data: pd.DataFrame, draws: int = 500, seed: int = 20260723,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """VB logistic mixed models with partially pooled country-year intercepts."""
    rng = np.random.default_rng(seed)
    results, diagnostics = [], []
    formula = "resistant ~ C(year) + C(gender) + C(age_group) + C(speciality) + C(source)"
    for endpoint in PRIMARY:
        frame = data.loc[data["endpoint_id"].eq(endpoint)].copy()
        frame["cell_id"] = frame["iso3"] + "_" + frame["year"].astype(str)
        model = BinomialBayesMixedGLM.from_formula(formula, {"cell": "0+C(cell_id)"}, frame)
        fit = model.fit_vb(fit_method="BFGS", minim_opts={"maxiter": 500}, verbose=False)
        # Standardisation distribution is the pooled observed endpoint composition.
        reference = frame.groupby(CATEGORICAL, dropna=False).size().rename("weight").reset_index()
        weights = reference["weight"].to_numpy(dtype=float)
        weights /= weights.sum()
        fixed_draws = rng.normal(fit.fe_mean, fit.fe_sd, size=(draws, len(fit.fe_mean)))
        name_to_position = {name: i for i, name in enumerate(model.vc_names)}
        raw = frame.groupby(["cell_id", "iso3", "country", "year"], as_index=False).agg(
            n_tested=("resistant", "size"), n_resistant=("resistant", "sum")
        )
        for row in raw.itertuples(index=False):
            cell_reference = reference.copy()
            cell_reference["year"] = int(row.year)
            fixed_design = patsy.build_design_matrices(
                [model.data.design_info], cell_reference, return_type="dataframe"
            )[0]
            fixed_x = np.asarray(fixed_design, dtype=float)
            position = name_to_position[f"C(cell_id)[{row.cell_id}]"]
            random_draw = rng.normal(fit.vc_mean[position], fit.vc_sd[position], size=draws)
            linear = fixed_x @ fixed_draws.T + random_draw[None, :]
            predicted = weights @ expit(linear)
            mean = float(weights @ expit(fixed_x @ fit.fe_mean + fit.vc_mean[position]))
            low, high = np.quantile(predicted, [0.025, 0.975])
            results.append({
                "endpoint_id": endpoint, "iso3": row.iso3, "country": row.country, "year": int(row.year),
                "n_tested": int(row.n_tested), "n_resistant": int(row.n_resistant),
                "crude_resistance_pct": 100 * row.n_resistant / row.n_tested,
                "standardised_resistance_pct": 100 * mean,
                "standardised_ci_low": 100 * float(low), "standardised_ci_high": 100 * float(high),
            })
        diagnostics.append({
            "endpoint_id": endpoint, "converged": bool(fit.optim_retvals.get("success", False)),
            "optimizer_message": str(fit.optim_retvals.get("message", "")),
            "country_year_random_effects": len(fit.vc_mean),
            "random_effect_log_sd_mean": float(fit.vcp_mean[0]),
            "random_effect_sd": float(np.exp(fit.vcp_mean[0])),
            "posterior_draws": draws,
        })
    return pd.DataFrame(results), pd.DataFrame(diagnostics)


def standardised_trend_summary(estimates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for (endpoint, year), group in estimates.groupby(["endpoint_id", "year"]):
        rows.append({
            "endpoint_id": endpoint, "year": int(year), "countries": int(group["iso3"].nunique()),
            "tested_isolates": int(group["n_tested"].sum()),
            "pooled_crude_resistance_pct": 100 * group["n_resistant"].sum() / group["n_tested"].sum(),
            "isolate_weighted_standardised_pct": float(np.average(
                group["standardised_resistance_pct"], weights=group["n_tested"]
            )),
            "equal_country_standardised_pct": float(group["standardised_resistance_pct"].mean()),
        })
    estimates = estimates.copy()
    estimates["absolute_adjustment_pp"] = (
        estimates["standardised_resistance_pct"] - estimates["crude_resistance_pct"]
    ).abs()
    calibration_rows = []
    for endpoint, group in estimates.groupby("endpoint_id"):
        calibration_rows.append({
            "endpoint_id": endpoint, "country_year_cells": int(len(group)),
            "mean_absolute_adjustment_pp": float(group["absolute_adjustment_pp"].mean()),
            "median_absolute_adjustment_pp": float(group["absolute_adjustment_pp"].median()),
            "crude_standardised_correlation": float(group["crude_resistance_pct"].corr(
                group["standardised_resistance_pct"]
            )),
        })
    return pd.DataFrame(rows), pd.DataFrame(calibration_rows)


def mic_sensitivity(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Censoring-aware summaries and bounded-substitution MIC trend sensitivities.

    Exact MICs retain their dilution; outer-censored MICs are analysed at the assay
    boundary and, separately, one two-fold dilution beyond that boundary. The two
    estimates explicitly bound the influence of open-ended MIC values.
    """
    frame = data.loc[data["mic_parsed"].eq(True) & data["mic_raw"].notna()].copy()
    boundary = np.where(frame["mic_censoring"].eq("left"), frame["mic_upper"], frame["mic_lower"])
    frame["log2_mic_boundary"] = np.log2(pd.to_numeric(boundary, errors="coerce"))
    frame["log2_mic_outer"] = frame["log2_mic_boundary"]
    frame.loc[frame["mic_censoring"].eq("left"), "log2_mic_outer"] -= 1
    frame.loc[frame["mic_censoring"].eq("right"), "log2_mic_outer"] += 1
    summaries = frame.groupby(["endpoint_id", "iso3", "country", "year"], as_index=False).agg(
        n_mic=("log2_mic_boundary", "count"),
        mean_log2_mic_boundary=("log2_mic_boundary", "mean"),
        mean_log2_mic_outer=("log2_mic_outer", "mean"),
        left_censored=("mic_censoring", lambda x: int(x.eq("left").sum())),
        right_censored=("mic_censoring", lambda x: int(x.eq("right").sum())),
    )
    summaries["censored_pct"] = 100 * (summaries["left_censored"] + summaries["right_censored"]) / summaries["n_mic"]
    model_rows = []
    for endpoint in PRIMARY:
        subset = summaries.loc[summaries["endpoint_id"].eq(endpoint)].copy()
        exposure_cells = data.loc[data["endpoint_id"].eq(endpoint), ["iso3", "year", EXPOSURE, TEMPERATURE]].drop_duplicates()
        subset = subset.merge(exposure_cells, on=["iso3", "year"], how="inner", validate="one_to_one")
        for outcome, label in [("mean_log2_mic_boundary", "Assay-boundary substitution"),
                               ("mean_log2_mic_outer", "One-dilution outer substitution")]:
            formula = f"{outcome} ~ {EXPOSURE} + {TEMPERATURE} + C(year) + C(iso3)"
            fit = smf.wls(formula, data=subset, weights=subset["n_mic"]).fit(
                cov_type="cluster", cov_kwds={"groups": subset["iso3"], "use_correction": True}, use_t=True
            )
            ci = fit.conf_int().loc[EXPOSURE]
            model_rows.append({
                "endpoint_id": endpoint, "specification": label,
                "log2_mic_change_per_exposure_doubling": float(fit.params[EXPOSURE]),
                "ci_low": float(ci.iloc[0]), "ci_high": float(ci.iloc[1]),
                "p_value": float(fit.pvalues[EXPOSURE]), "countries": int(subset["iso3"].nunique()),
                "country_year_cells": int(len(subset)), "mic_records": int(subset["n_mic"].sum()),
            })
    return summaries, pd.DataFrame(model_rows)


def exploratory_event_trajectories(
    processed_dir: Path, acled: pd.DataFrame,
) -> pd.DataFrame:
    master = pd.read_csv(processed_dir / "restricted" / "master_country_year_endpoint.csv.gz")
    _, windows = escalation_candidates(acled, master)
    eligible = windows.loc[windows["minimal_pre_post_eligible"]].copy()
    rows = []
    for event in eligible.itertuples(index=False):
        observations = master.loc[
            master["iso3"].eq(event.iso3)
            & master["endpoint_id"].eq(event.endpoint_id)
            & master["n_tested"].ge(30),
            ["year", "resistance_pct"],
        ].copy()
        observations["relative_year"] = observations["year"] - event.response_index_year
        observations = observations.loc[observations["relative_year"].between(-2, 2)]
        pre = observations.loc[observations["relative_year"].isin([-2, -1]), "resistance_pct"]
        index = observations.loc[observations["relative_year"].eq(0), "resistance_pct"]
        post = observations.loc[observations["relative_year"].isin([1, 2]), "resistance_pct"]
        rows.append({
            "iso3": event.iso3, "country": event.country,
            "endpoint_id": event.endpoint_id, "escalation_year": int(event.escalation_year),
            "response_index_year": int(event.response_index_year),
            "pre_observed_years": int(len(pre)), "post_observed_years": int(len(post)),
            "pre_mean_crude_pct": float(pre.mean()),
            "index_crude_pct": float(index.iloc[0]) if len(index) else np.nan,
            "post_mean_crude_pct": float(post.mean()),
            "index_minus_pre_pp": float(index.iloc[0] - pre.mean()) if len(index) and len(pre) else np.nan,
            "post_minus_pre_pp": float(post.mean() - pre.mean()) if len(post) and len(pre) else np.nan,
        })
    return pd.DataFrame(rows)


def run_phase4(
    processed_dir: Path, output_dir: Path, bootstrap_replications: int = 9999,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data, cells, acled = _load_analysis_data(processed_dir)
    main, diagnostic = fit_confirmatory_models(data, bootstrap_replications)
    sensitivity = sensitivity_models(data, cells, acled)
    standardised, standardisation_diagnostic = standardised_estimates(data)
    trends, calibration = standardised_trend_summary(standardised)
    mic_cells, mic_models = mic_sensitivity(data)
    event_trajectories = exploratory_event_trajectories(processed_dir, acled)
    outputs = {
        "main_conflict_models": main,
        "model_diagnostics": diagnostic,
        "sensitivity_models": sensitivity,
        "standardised_amr": standardised,
        "standardisation_diagnostics": standardisation_diagnostic,
        "standardised_trends": trends,
        "standardisation_calibration": calibration,
        "mic_country_year": mic_cells,
        "mic_models": mic_models,
        "exploratory_event_trajectories": event_trajectories,
    }
    paths = {}
    for name, table in outputs.items():
        path = output_dir / f"{name}.csv"
        table.to_csv(path, index=False)
        paths[name] = str(path)
    summary = {
        "phase": 4, "pipeline_version": "0.4.0", "bootstrap_replications": bootstrap_replications,
        "confirmatory_endpoints": PRIMARY, "all_models_converged": bool(diagnostic["converged"].all()),
        "holm_significant_endpoints": main.loc[main["confirmatory_holm_significant_005"], "endpoint_id"].tolist(),
        "outputs": paths,
    }
    (output_dir / "phase4_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
