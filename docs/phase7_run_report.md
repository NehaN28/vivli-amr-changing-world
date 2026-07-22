# Phase 7 reproducibility and deployment report

## Release status

- Prepared repository version: `v0.7.0`
- Verification date: 23 July 2026
- Scientific definitions changed: none
- Statistical results changed: none
- Public repository name: `vivli-amr-changing-world`

## Reproducibility work completed

- Package, configuration and citation versions synchronised at `0.7.0`.
- Streamlit and Plotly added to package metadata.
- Exact Python 3.12 verification environment recorded in `requirements-lock.txt`.
- Fresh temporary virtual environment created from the lock file.
- Project installed into that environment as an editable package without dependency resolution.
- Dependency consistency check passed.
- Continuous integration hardened with read-only permissions, timeout and release validation.
- SHA-256 checksums recorded for every packaged dashboard data table.

## Verification results

- Automated tests: 21 passed.
- Release validation: passed.
- Python dependency check: passed.
- Python syntax compilation: passed.
- Streamlit entry point: passed.
- Six individual dashboard pages: passed without exceptions.
- Visible AMR cells below 30 tested isolates: none.
- Protected values retained in suppressed AMR cells: none.
- Raw, interim, isolate-level, credential or Streamlit-secret files tracked: none detected.

## Publication boundary

The repository has no configured Git remote, and no authenticated GitHub
connection is available in the working environment. Therefore, no GitHub push,
public tag, GitHub release or Streamlit Community Cloud deployment was made.

Public redistribution also remains gated on written confirmation that the
applicable Vivli data-use agreement permits redistribution of the packaged
aggregated derived tables. Technical disclosure checking does not replace that
contractual review.

## Remaining external steps

1. Confirm permission to redistribute the derived aggregate tables.
2. Connect the intended GitHub account and create `vivli-amr-changing-world`.
3. Push the frozen commit and tag `v0.7.0`.
4. Confirm the GitHub Actions workflow passes.
5. Deploy `app.py` from the tagged commit on Streamlit Community Cloud.
6. Run the private-browser post-deployment checklist.
7. Record permanent URLs and update `CITATION.cff`.
