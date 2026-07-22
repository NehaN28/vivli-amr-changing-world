# Deployment guide

## Publication gates

Do not make the repository or dashboard public until all gates are satisfied:

1. Confirm in writing that the applicable Vivli data-use agreement permits
   redistribution of the packaged aggregated derived tables.
2. Confirm that no raw, isolate-level, participant-level or potentially
   disclosive Vivli data are tracked by Git.
3. Run `python scripts/validate_release.py` and `python -m pytest -q` from a
   clean installation.
4. Review the dashboard wording, source acknowledgements and citation metadata.
5. Replace the pending repository and dashboard fields in the deployment record
   after their permanent URLs exist.

## GitHub publication

Create a public repository named `vivli-amr-changing-world`, then push the
frozen release commit and annotated tag:

```bash
git remote add origin https://github.com/<account>/vivli-amr-changing-world.git
git push -u origin main
git push origin v0.7.0
```

On GitHub, verify that the `tests` workflow passes. Create a release from tag
`v0.7.0`, attach the clean repository archive and use the corresponding section
of `CHANGELOG.md` as the release notes.

## Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with the GitHub account that owns or
   can access the repository.
2. Create an app from the `main` branch.
3. Set the entry point to `app.py`.
4. Select Python 3.12.
5. Do not add secrets. The app requires none.
6. Deploy only the commit carrying tag `v0.7.0`.

The application reads only `data/dashboard/`. It must never be configured with
a raw-data path, Vivli credential or private data mount.

## Post-deployment verification

Open the permanent URL in a private browser window and verify:

- all six pages load;
- crude and standardised Global AMR views render;
- country and endpoint filters work;
- downloads contain aggregated records only;
- cells below 30 isolates are not visible;
- no stack trace, filesystem path or secret appears;
- the deployed commit matches tag `v0.7.0`.

Record the repository URL, dashboard URL, deployed commit and verification date
in `docs/deployment_record.md`. Add the repository URL to `CITATION.cff`, commit
that metadata-only update, and issue the final public release.

## Rollback

If a disclosure, rendering or data-integrity problem is found, pause or delete
the Streamlit deployment immediately. Make the GitHub repository private if
the problem concerns redistributed data. Correct the issue on a new branch,
rerun all release checks and deploy a new tagged patch release. Never rewrite
the existing public tag.
