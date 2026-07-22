# Phase 2 pipeline run report

> Phase 3 amendment (23 July 2026): the supplied ACLED extract omits many zero-event month rows. The pipeline now reconstructs absent zero-event months after each country's full-coverage start. The earlier partial-year interpretation and its reported 716-cell overlap are superseded by `docs/phase3_run_report.md`.

Run date: 23 July 2026  
Pipeline version: 0.2.0  
Protocol version: 1.0

## Outcome

The complete data pipeline ran successfully on all six analytical sources. All declared schema, key, country-mapping, MIC-parsing, unit, duplication and disclosure checks passed.

## ATLAS analytical outputs

- 1,072,897 endpoint-level isolate records across 17 prespecified outcomes
- 11,847 country-year-endpoint rows
- 82 countries with at least one selected pathogen-drug observation
- No duplicate isolate IDs
- No unparsed non-empty MIC values among selected endpoint records
- All inequality-coded MICs retained using left- or right-censoring bounds

### Frozen primary outcomes, 2019–2024

| Endpoint | Countries | Country-years | Tested | Resistant | Cells with n ≥ 30 |
|---|---:|---:|---:|---:|---:|
| *A. baumannii*–meropenem | 64 | 329 | 16,849 | 11,657 | 174 |
| *E. coli*–ceftazidime | 64 | 342 | 37,791 | 7,829 | 281 |
| *K. pneumoniae*–ceftazidime | 64 | 342 | 36,743 | 15,271 | 287 |
| *K. pneumoniae*–meropenem | 64 | 342 | 36,743 | 6,565 | 287 |

## Linked primary analysis table

- 1,355 primary endpoint country-year rows in 2019–2024
- 1,029 rows meet the `n ≥ 30` threshold
- 906 rows have a complete preceding-year ACLED exposure
- 716 rows have both `n ≥ 30` and a complete preceding-year ACLED exposure
- 1,355 rows have preceding-year annual temperature anomaly data
- 441 rows have preceding-year adjusted WOAH animal AMU data

## Data-quality decisions implemented

1. FAOSTAT reports both `China` and `China, mainland`. The former is an aggregate and is excluded; the mainland series maps to CHN. This prevents double-counting.
2. ACLED country coverage begins in different years. Partial country-years are retained for audit but cannot contribute an annual exposure. Only records with all 12 months populate `annual_events` and `log2p1_events`.
3. Six ACLED non-country labels, including oceans, are excluded.
4. FAOSTAT `M` livestock records remain missing, and `1000 An` values are converted to individual head counts.
5. Bees remain outside animal head-count and livestock-unit totals.
6. Exactly 16 excess R&D project rows are flagged and removed: 15 identical project-detail pairs and one same-external-project pair with a title variation.
7. The 124 R&D projects with `Amount USD = 0` are retained for project counts but have monetary amount set to missing.
8. Dashboard outputs suppress ATLAS outcome values for 4,301 cells with fewer than 30 tested isolates.

## Phase 3 implications

The prespecified pathogen-outcome family remains feasible. However, ACLED exposure coverage is not globally uniform from 2018. Phase 3 must formally describe complete country-year coverage, identify the final model sample, and determine whether the primary model should use a common later period or a country-specific unbalanced panel with explicit coverage requirements. This decision must be made before any conflict–AMR association is examined.
