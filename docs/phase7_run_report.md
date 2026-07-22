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

## Publication status

- Vivli redistribution permission was confirmed by the project lead on 23 July 2026.
- The public repository is available at
  `https://github.com/NehaN28/vivli-amr-changing-world`.
- The public tracked tree is byte-for-byte identical to the verified local
  `v0.7.0` release tree (`66fa4179c5dac2a5388eed046f6818e0b5f0e71b`).
- The public release-content commit is
  `4bc425569b5ed895af54e4761bc33e2f84accb4e`.
- Streamlit Community Cloud deployment and the final public tag/release remain
  pending external hosting actions.

## Remaining external steps

1. Deploy `app.py` from `main` on Streamlit Community Cloud.
2. Run the private-browser post-deployment checklist.
3. Record the permanent dashboard URL.
4. Create the final `v0.7.0` tag and GitHub release after the deployment record
   contains the permanent URL.
