# Phase 6 dashboard development report

## Release

- Repository version: `v0.6.0`
- Application: Streamlit multipage dashboard
- Pages: six
- Statistical models refitted in application: none

## Public data contract

The application reads only aggregated files from `data/dashboard/`. The primary AMR explorer suppresses all country-year pathogen-drug cells with fewer than 30 tested isolates. Standardised estimates are restricted to the four confirmatory endpoints and to the Phase 3 locked country-year sample. Raw ATLAS, isolate-level derivatives and restricted composition strata are neither packaged nor loaded.

## Pages

1. **Global AMR**: crude estimates for all supported endpoint combinations and standardised estimates for primary endpoints, global map, country trends, uncertainty and filtered downloads.
2. **Conflict and AMR**: aligned country timelines, preceding-year conflict exposure, confirmatory model estimates, multiplicity-corrected interpretation and exploratory escalation trajectories.
3. **One Health**: temperature, livestock composition, animal-AMU availability and secondary model estimates with FDR correction.
4. **R&D Alignment**: sector, research-area, pathogen-attention and recipient-institution geography views.
5. **Country Profile**: 2024 AMR coverage and trajectories with component-wise 2023 context. No composite vulnerability score.
6. **Methods and Data Quality**: definitions, eligibility, modelling, safeguards, limitations and aggregated downloads.

## Verification

- All automated tests pass, including dashboard disclosure tests.
- Every page was executed through Streamlit's application-testing runtime with no exceptions.
- Default and alternate widget states were exercised for crude and standardised AMR views, country selection and evidence-family selection.
- Responsive CSS collapses Streamlit columns at narrow widths, reduces page padding and uses fluid heading sizes. Charts use container-width rendering.
- Public data bundle inspected for restricted filenames and isolate-level tables: none present.
- Python syntax compilation completed successfully.

## Interpretation safeguards

- Country estimates are described as clinical-isolate surveillance estimates, not population prevalence.
- Temporal association is explicitly separated from causal inference.
- Non-significant results are not described as evidence of no effect.
- WOAH analyses are labelled underpowered because of limited country coverage.
- Livestock units are not labelled as density.
- R&D geography is described as recipient research-capacity location, not beneficiary geography.
- No composite vulnerability ranking is displayed.
