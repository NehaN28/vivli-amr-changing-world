# Phase 2 data contract

## Keys and terminology

`iso3` is the preferred cross-dataset country key. `country` retains the reviewed canonical display name. Country-year AMR estimates describe ATLAS surveillance isolates and are not national prevalence estimates.

## Core tables

| Table | Unique key | Purpose |
|---|---|---|
| `atlas_endpoint_isolates` | `isolate_id`, `endpoint_id` | Restricted analytical long table with MIC bounds and reported interpretation |
| `atlas_country_year_endpoint` | `iso3`, `year`, `endpoint_id` | Tested and resistant counts, crude resistance, MIC coverage |
| `atlas_composition_strata` | `iso3`, `year`, `endpoint_id`, study and patient/specimen strata | Input for later standardisation |
| `acled_country_month` | `iso3`, `year`, `month_number` | Reconstructed monthly conflict panel with source-row and imputed-zero flags |
| `acled_country_year` | `iso3`, `year` | Annual events and prespecified transforms |
| `temperature_country_year` | `iso3`, `year` | Annual land-temperature anomaly and baseline SD |
| `livestock_country_year_group` | `iso3`, `year`, `livestock_group` | Head counts and livestock-unit sensitivity measure |
| `woah_country_year` | `iso3`, `year` | Animal AMU totals |
| `woah_class_long` | `iso3`, `year`, `antimicrobial_class` | Animal AMU by class |
| `rd_projects_clean` | `project_id` | Deduplicated projects; unavailable amounts stored as missing |
| `rd_fractional_categories` | `project_id`, `dimension`, `category` | Equal fractional allocation across multi-label categories |
| `master_country_year_endpoint` | `iso3`, `year`, `endpoint_id` | AMR outcomes linked to preceding-year conflict and contextual exposures |
| `dashboard_country_year_endpoint` | `iso3`, `year`, `endpoint_id` | Disclosure-safe subset; small ATLAS cells suppressed |

## MIC representation

- Exact `x`: lower bound = upper bound = `x`; censoring = `exact`
- `<=x` or `<x`: upper bound = `x`; lower bound missing; censoring = `left`
- `>=x` or `>x`: lower bound = `x`; upper bound missing; censoring = `right`
- Unparseable non-empty strings are retained in `mic_raw` and reported by validation.

Reported S/I/R interpretation is the primary categorical outcome in Phase 2. Breakpoint re-interpretation is deferred until guideline version and method information are verified.

## Missingness

Absence of an external country-year means missing exposure, not zero. The supplied ACLED extract omits many zero-event months. For each country, the first source year with all 12 months marks the beginning of full January coverage; missing rows in subsequent closed years are reconstructed as zero-event months and flagged by `imputed_zero`. Pre-coverage years and the ongoing incomplete calendar year remain missing. FAOSTAT `M` flags are missing. WOAH absent reporting years are missing. R&D `Amount USD=0` means unavailable or undisclosed.

## Public release boundary

The isolate-level ATLAS table and any derived row-level extract remain restricted. Public tables suppress tested counts and outcome estimates when `n_tested < 30`. Final publication and dashboard release also require confirmation that aggregated derived outputs are permitted under the Vivli data-use agreement.
