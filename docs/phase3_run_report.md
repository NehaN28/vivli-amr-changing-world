# Phase 3 descriptive feasibility and final model lock

Lock date: 23 July 2026  
Pipeline version: 0.3.0  
Protocol version: 1.0

## Safeguard

No conflict–AMR association was examined while defining the final endpoint roles, eligible countries, model sample, escalation rule or One Health analysis scope.

## Critical ACLED correction

The supplied country-month extract omits many zero-event months in later calendar years. The pipeline now identifies the first source year containing all 12 months for each country as the beginning of full January coverage. Missing rows in later closed years are reconstructed as zero-event months. Pre-coverage months and the ongoing incomplete year are never filled.

This reconstruction imputes 6,232 zero-event months in the complete ACLED panel and is consistent with ACLED's official country/time-period coverage table: https://acleddata.com/methodology/countrytime-period-coverage

## Locked primary sample

| Endpoint | Countries | Country-year cells | Tested isolate records | Resistant records |
|---|---:|---:|---:|---:|
| ABA_MEM_R | 28 | 131 | 11,564 | 9,008 |
| ECO_CAZ_R | 45 | 222 | 28,968 | 6,628 |
| KPN_CAZ_R | 46 | 228 | 29,015 | 12,927 |
| KPN_MEM_R | 46 | 228 | 29,015 | 6,009 |

The final sample contains 809 country-year-endpoint cells, 98,562 endpoint-level isolate records and 69,547 unique isolates. K. pneumoniae isolates contribute separately to the ceftazidime and meropenem endpoints.

Country-endpoint inclusion requires:

1. At least 30 tested isolates in a country-year cell.
2. Available preceding-year ACLED exposure.
3. At least three eligible outcome years during 2019–2024.
4. Within-country variation in lagged log2(1 + annual events).

The primary design is an endpoint-specific unbalanced panel with country and calendar-year fixed effects.

## Secondary endpoints

Seven outcomes pass the prespecified numeric model rules and remain secondary: ECO_MEM_R, PAE_MEM_R, SAU_OXA_R, ECO_CIP_R, KPN_CIP_R, ECO_GEN_R and KPN_GEN_R. KPN_COL_R passes numeric rules but remains exploratory because colistin phenotype validity requires additional caution. ECO_COL_R, EFA_VAN_R, SPN_ERY_R, HIN_AMP_R and GAS_ERY_R are descriptive or dashboard-only.

## Composition and external variables

- Missing or unavailable age, sex, specialty and specimen categories are uncommon (<2.4% each).
- Specimen composition has a median consecutive-year total-variation distance of 0.242; specialty has a median of 0.175. Isolate-level adjustment is therefore retained.
- Lagged temperature and livestock-system data cover 100% of locked primary cells.
- Lagged adjusted WOAH animal AMU covers only 18.3%–23.0% of cells and 6–14 countries depending on endpoint. It remains a secondary restricted-sample analysis.
- R&D recipient commitments remain a separate policy-alignment analysis and are not included as confounders.

## Escalation analysis

A candidate escalation requires a year-on-year increase of at least one unit in log2(1 + events), at least 20 additional events, and an annual count at or above the country's 75th percentile during 2018–2023. Fourteen candidate rows occur in primary-ATLAS countries. Only 17 country-endpoint windows across Ivory Coast, Greece, Poland, Spain and Ukraine contain an index cell plus at least one pre- and one post-index cell. The event-study analysis is therefore exploratory.

## Phase 4 lock

- Four separate isolate-level logistic fixed-effects models for the confirmatory endpoints.
- Primary exposure: preceding-year log2(1 + ACLED political-violence events).
- Covariates: age group, sex, specimen source, specialty and lagged annual temperature anomaly.
- Country-clustered inference with a wild-cluster bootstrap sensitivity analysis.
- Holm correction across four primary conflict coefficients.
- Same-year and two-year lag models are sensitivity analyses.
- Public dashboard cells below 30 isolates remain suppressed.
