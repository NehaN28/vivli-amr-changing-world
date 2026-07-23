# Changelog

All notable changes to this project are documented here.

## [0.8.0] - 2026-07-23

### Added

- Longitudinal AMR-One Health tables, annual R&D views and country trajectory summaries.
- Coverage-first exploration across 17 clinically selected organism-drug endpoints.
- Multi-country annual trend comparisons and disclosure-safe exploratory lag results.
- Explanatory landing page with Vivli AMR Data Challenge 2026 context and project-team biographies.
- Full-context world maps with explicit no-data geography and markers for small geographies.

### Changed

- Reorganised the dashboard into seven self-explanatory pages.
- Improved responsive layouts, labels, legends, metric cards and empty-data states.
- Credited Dr. Neha Nityadarshini as Team Lead and Dr. Jaya Biswas as Team Member.

### Scientific status

- The four prespecified confirmatory endpoints and models remain unchanged.
- New longitudinal analyses are explicitly labelled exploratory or descriptive.
- Public AMR cells continue to suppress results based on fewer than 30 tested isolates.

## [0.7.1] - 2026-07-23

### Fixed

- Install the local `src/`-layout package when Streamlit Community Cloud
  processes `requirements.txt`, resolving the production
  `ModuleNotFoundError`.
- Added a release regression test for the cloud installation contract.

### Scientific status

- No data, endpoint, exposure, model, estimate or interpretation changed.

## [0.7.0] - 2026-07-23

### Added

- Deployment guide with explicit data-governance publication gate and rollback procedure.
- Automated release validator for version consistency, required public assets, restricted-file exclusions and small-cell suppression.
- Clean-install and Streamlit application smoke-test coverage.
- Reproducibility lock file and Phase 7 verification report.

### Changed

- Unified the package, configuration and citation version at `0.7.0`.
- Declared Streamlit and Plotly in package metadata, not only `requirements.txt`.
- Hardened continuous integration with read-only permissions and a job timeout.
- Configured production Streamlit runs without file watching.

### Scientific status

- No endpoint, exposure, eligibility, model or interpretation decision changed.
- All Phase 4 and Phase 5 results remain unchanged.
- Public data remain aggregated and cells with fewer than 30 tested isolates remain suppressed.

## [0.6.0] - 2026-07-23

- Added the six-page Streamlit dashboard and disclosure-safe public data bundle.

## [0.5.0] - 2026-07-23

- Added One Health and R&D alignment analyses.

## [0.4.0] - 2026-07-23

- Added locked confirmatory statistical analyses and standardised AMR estimates.

## [0.3.0] - 2026-07-23

- Locked the feasible model sample and escalation-event design.

## [0.2.0] - 2026-07-23

- Added the reproducible ingestion, validation and linkage pipeline.
