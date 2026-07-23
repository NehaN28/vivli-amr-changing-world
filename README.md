# Human AMR trends in a changing world

Reproducible data pipeline, statistical workflow and interactive platform developed for the Vivli AMR Data Challenge 2026. The project examines longitudinal changes in human antimicrobial resistance in relation to political violence, One Health determinants and global AMR R&D investment.

**Project team:** Dr. Neha Nityadarshini (Team Lead) and Dr. Jaya Biswas (Team Member).

## Scientific scope

The confirmatory outcome family is frozen in the Phase 1 protocol:

1. *Escherichia coli* ceftazidime resistance
2. *Klebsiella pneumoniae* ceftazidime resistance
3. *K. pneumoniae* meropenem resistance
4. *Acinetobacter baumannii* meropenem resistance

The primary outcome years are 2019–2024. The primary exposure is the preceding year's `log2(1 + ACLED political-violence events)`. No conflict–AMR result was examined when selecting endpoints.

## Data governance

The ATLAS/Vivli isolate-level file is restricted and must never be committed. Raw and interim data directories are ignored by Git. Public dashboard outputs must be aggregated, disclosure checked, and suppress cells with fewer than 30 tested isolates.

## Expected raw files

Place these files in a local raw-data directory, or point the command to the directory containing them:

- `atlas_vivli_2004_2024.csv`
- `number_of_political_violence_events_by_country-month-year_as-of-17Jul2026.xlsx`
- `Environment_Temperature_change_E_All_Data_(Normalized).csv`
- `Livestock_FAOSTAT_data_en_7-22-2026(2).csv`
- `WOAH_consolidated_AMU_2014_2024.xlsx`
- `ALL PROJECTS WITHOUT FILTER.xlsx`

The WOAH consolidated workbook is itself generated from the three original WOAH exports; the original consolidation script is retained outside this Phase 2 repository and will be incorporated before public release if redistribution terms permit.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
amr-pipeline validate --raw-dir /path/to/raw
amr-pipeline build --raw-dir /path/to/raw --output-dir data/processed
amr-pipeline phase3 --processed-dir data/processed --output-dir outputs/phase3_audit
amr-pipeline phase4 --processed-dir data/processed --output-dir outputs/phase4_analysis
amr-pipeline phase5 --processed-dir data/processed --phase4-dir outputs/phase4_analysis --output-dir outputs/phase5_analysis
streamlit run app.py
python -m pytest -q
```

For an exact reproduction of release `v0.7.0`, install `requirements-lock.txt`
instead of `requirements.txt`, then install the project with
`pip install -e . --no-deps`.

The build writes Parquet tables when `pyarrow` is installed. It falls back to compressed CSV for constrained environments. A machine-readable validation report and SHA-256 source manifest are written with every run.

## Pipeline outputs

- ATLAS endpoint-level isolate table with parsed MIC censoring bounds
- Country–year endpoint counts and crude resistance proportions
- ATLAS composition strata for later standardisation
- ACLED reconstructed country-month panel and annual lagged exposures, with zero-event months imputed only after coverage begins
- FAOSTAT annual temperature anomalies
- FAOSTAT livestock head counts, species groups and transparent livestock-unit estimates
- WOAH country-year and antimicrobial-class tables
- Deduplicated AMR R&D projects and fractional category allocations
- Linked country-year-endpoint master table
- Disclosure-safe dashboard table with cells below `n=30` suppressed

## Reproducibility principles

- Raw files are immutable inputs.
- Country harmonisation uses a reviewed, versioned crosswalk.
- Every table has a declared unique key and validation checks.
- Missing exposure values are never converted to zero.
- MIC inequalities are retained as censoring information.
- R&D zero amounts are treated as unavailable, not as zero investment.
- Recipient-institution geography is interpreted as research-capacity location, not beneficiary geography.
- Dashboard values are derived from the same pipeline used for manuscript tables.

See `docs/phase2_data_contract.md` for table definitions and `config/project.yml` for frozen analysis decisions.

See `config/phase3_lock.yml` and `docs/phase3_run_report.md` for the final model-sample rules and Phase 4 analysis lock. No conflict–AMR association was examined during Phase 3.

Phase 4 fits the four locked isolate-level logistic fixed-effects models, uses country-clustered inference and a 9,999-replication wild-cluster sensitivity, applies the prespecified Holm correction, derives partially pooled standardised country-year estimates, and runs lag, threshold, complete-case and MIC-censoring sensitivities.

Phase 5 fits secondary One Health determinant and conflict-effect-modification models, performs limited-coverage WOAH animal-AMU analyses, applies family-specific false-discovery-rate correction, describes 2015–2024 R&D portfolio alignment, and exports a component-based country context profile without a composite vulnerability score. See `docs/phase5_run_report.md`.

## Interactive dashboard

The public Streamlit application provides seven connected pages:

1. Start Here
2. Global AMR Explorer
3. Conflict and AMR
4. One Health Trend Studio
5. R&D Investment Alignment
6. Country Profile
7. Methods and Data Quality

The redesigned application explains the research context before presenting results, supports coverage-first selection across 17 clinically selected endpoints, compares up to five countries over time, and retains complete geographic context in maps. Confirmatory, exploratory and descriptive evidence are explicitly separated.

The application loads only files in `data/dashboard/`. These are aggregated, disclosure-checked outputs suitable for the public interface. Standardised estimates are limited to the four locked primary endpoints. The dashboard never loads raw or isolate-level ATLAS data and does not refit statistical models when filters change.

Run locally with `streamlit run app.py`. See `docs/phase6_run_report.md` for the page-level data contract and verification record.

## Public release and deployment

Release `v0.8.0` is the redesigned dashboard candidate for GitHub and
Streamlit Community Cloud. The publication gate, deployment procedure,
rollback steps and post-deployment checks are documented in `DEPLOYMENT.md`.
Permission to redistribute the packaged disclosure-safe derived tables was
confirmed by the project lead on 23 July 2026.

The public repository must be named `vivli-amr-changing-world`. After the
repository URL and permanent dashboard URL exist, add them to `CITATION.cff`
and the deployment record before creating the final public GitHub release.

See `CHANGELOG.md` for release history and `docs/phase7_run_report.md` for the
Phase 7 reproducibility record.
