# Phase 8B exploratory longitudinal analysis

Date: 2026-07-23  
Branch: `phase8-redesign`

## Scope

Phase 8B adds exploratory longitudinal outputs without changing the four locked
confirmatory conflict models. All analyses use only disclosure-eligible ATLAS
country-year-endpoint cells (`n_tested >= 30`).

## Prespecified eligibility rules

- Country trend: at least 5 observed years.
- Descriptive change-point candidate: at least 8 observed years, with at least
  3 observations on each side of the candidate split.
- One Health lag model: at least 40 paired country-year cells across at least
  10 countries, with within-country exposure variation.
- Lags: same year, 1 year and 2 years.
- Multiplicity: Benjamini-Hochberg false-discovery-rate adjustment across the
  complete One Health lag-model family.

## Outputs

| Output | Records | Purpose |
|---|---:|---|
| `country_trends` | 687 | Isolate-weighted country-specific linear AMR trends |
| `pooled_annual_trends` | 249 | Annual isolate-weighted and country-distribution summaries |
| `lag_associations` | 144 | Exploratory fixed-effect One Health models |
| `change_point_candidates` | 399 | Largest descriptive shifts for sufficiently long series |
| `coverage_summary` | 5 | Coverage boundaries for each linked data component |

## Main descriptive findings

- Of 687 eligible country-endpoint trajectories, 82 were classified as
  increasing, 94 as decreasing and 511 as showing no clear linear change.
- Fourteen of 144 One Health lag models had nominal `p < 0.05`; one remained
  below a 5% false-discovery-rate threshold.
- The FDR-retained estimate was a positive 2-year-lag association between
  adjusted animal AMU and *E. coli* meropenem resistance. It was based on 107
  paired cells across 15 countries and had a large, imprecise effect estimate.
  It is hypothesis-generating and is not suitable as a causal or headline
  conclusion.
- AMR data were available for 813 country-years across 70 countries.
  Temperature had much broader coverage, while animal AMU was the most limited
  linked series (376 country-years across 57 countries).

## Interpretation contract

- Country slopes describe sampled ATLAS isolates and are not population
  prevalence estimates.
- “No clear linear change” means the slope confidence interval included zero;
  it does not prove absence of change.
- Change-point candidates are navigation aids for visual review, not formal
  change-point tests.
- One Health models compare within-country changes while controlling for
  country and calendar year. Residual confounding, surveillance-composition
  changes, ecological bias and non-representative sampling remain possible.
- Nominal associations must not be highlighted without the FDR result,
  coverage and uncertainty.
- R&D trends remain descriptive. Recipient-country funding is not interpreted
  as local burden-directed investment or as an AMR determinant.

## Validation

- 30 automated tests passed.
- All output keys were unique.
- Minimum exported AMR cell size was 30.
- The full analysis completed without runtime or statistical-library warnings.
