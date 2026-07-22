# Phase 4 statistical analysis

Analysis date: 23 July 2026  
Pipeline version: 0.4.0  
Protocol version: 1.0

## Confirmatory conclusion

None of the four prespecified preceding-year conflict coefficients was statistically significant after Holm correction. Odds ratios per doubling of `1 + annual ACLED political-violence events` were 0.974 for *E. coli* ceftazidime resistance, 0.964 for *K. pneumoniae* ceftazidime resistance, 1.052 for *K. pneumoniae* meropenem resistance and 1.043 for *A. baumannii* meropenem resistance. All confidence intervals crossed 1.

The interpretation is no detectable association in the locked ATLAS sample, not evidence that the true effect is exactly zero.

## Model

- Isolate-level logistic regression, resistant versus susceptible/intermediate.
- Country and calendar-year fixed effects.
- Age group, sex, specimen source, clinical specialty and lagged annual temperature anomaly.
- Country-clustered t inference.
- Holm adjustment across the four confirmatory coefficients.
- 9,999-replication Rademacher wild-cluster score sensitivity.
- Average marginal risk difference for a one-unit increase in the exposure, equivalent to a doubling of `1 + events`.

## Robustness

Complete-case, minimum cell size 50, no-composition-adjustment, same-year, two-year-lag and outcome-variation sensitivities did not alter the confirmatory conclusion. MIC boundary-substitution sensitivities were also non-significant. The prespecified event study remains exploratory because Phase 3 found only 17 minimally usable country-endpoint windows.

The 17 escalation windows were exported as descriptive crude pre/index/post trajectories. Changes were heterogeneous across outcomes and countries. No pooled hypothesis test was fitted because only five countries contributed and pre/post coverage was irregular.

## Standardisation

Country-year estimates use variational-Bayes logistic mixed models with partially pooled country-year intercepts and adjustment to the pooled endpoint-specific age, sex, specimen and specialty distribution. These describe resistance among ATLAS surveillance isolates and are not national prevalence estimates.

## Diagnostics

All four confirmatory and standardisation models converged. Pearson dispersion was close to 1. Leave-one-country influence estimates did not reverse the conclusion. Ireland and New Zealand had no meropenem-resistant *K. pneumoniae* observations in the locked records; excluding these countries left the primary coefficient unchanged to three decimals.

## Governance

All result tables must remain in reporting, including null findings. Raw and isolate-level Vivli data are excluded from public repository packages. Dashboard release files must retain suppression for cells with fewer than 30 isolates.
