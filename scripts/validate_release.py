#!/usr/bin/env python3
"""Validate public-release metadata, packaging and disclosure boundaries."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DASHBOARD_FILES = {
    "acled_country_year.csv.gz",
    "amr_country_year.csv.gz",
    "country_context.csv.gz",
    "event_trajectories.csv.gz",
    "main_conflict_models.csv.gz",
    "one_health_models.csv.gz",
    "rd_geography.csv.gz",
    "rd_pathogen.csv.gz",
    "rd_research_area.csv.gz",
    "rd_sector.csv.gz",
    "standardised_amr.csv.gz",
    "woah_models.csv.gz",
}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
    "OpenAI token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
}


def _tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file()]
    return [Path(p.decode()) for p in result.stdout.split(b"\0") if p]


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate() -> list[str]:
    errors: list[str] = []
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    project = yaml.safe_load((ROOT / "config/project.yml").read_text())

    init_text = (ROOT / "src/amr_changing_world/__init__.py").read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    versions = {
        "pyproject": str(pyproject["project"]["version"]),
        "package": match.group(1) if match else "missing",
        "configuration": str(project["project"]["pipeline_version"]),
        "citation": str(citation["version"]),
    }
    if len(set(versions.values())) != 1:
        _fail(errors, f"Release versions differ: {versions}")

    actual_dashboard = {p.name for p in (ROOT / "data/dashboard").glob("*.csv.gz")}
    missing = REQUIRED_DASHBOARD_FILES - actual_dashboard
    if missing:
        _fail(errors, f"Dashboard bundle is missing: {sorted(missing)}")

    checksum_path = ROOT / "data/dashboard/SHA256SUMS"
    expected_checksums = {}
    for line in checksum_path.read_text().splitlines():
        digest, filename = line.split(maxsplit=1)
        expected_checksums[filename.strip()] = digest
    if set(expected_checksums) != REQUIRED_DASHBOARD_FILES:
        _fail(errors, "Dashboard checksum manifest does not match the required public bundle")
    for filename, expected in expected_checksums.items():
        actual = hashlib.sha256((ROOT / "data/dashboard" / filename).read_bytes()).hexdigest()
        if actual != expected:
            _fail(errors, f"Dashboard checksum differs for {filename}")

    tracked = _tracked_files()
    forbidden = [
        str(p)
        for p in tracked
        if (
            (p.parts[:2] in (("data", "raw"), ("data", "interim")) and p.name != ".gitkeep")
            or p.name in {".env", "secrets.toml"}
            or "isolate_level" in p.name.lower()
        )
    ]
    if forbidden:
        _fail(errors, f"Restricted or secret files are tracked: {forbidden}")

    for relative in tracked:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                _fail(errors, f"Possible {label} in {relative}")

    amr = pd.read_csv(ROOT / "data/dashboard/amr_country_year.csv.gz")
    visible = amr[amr["sufficient_atlas_data"]]
    hidden = amr[~amr["sufficient_atlas_data"]]
    if not visible["n_tested"].ge(30).all():
        _fail(errors, "A visible AMR cell has fewer than 30 tested isolates")
    protected = ["n_tested", "n_resistant", "resistance_pct"]
    if not hidden[protected].isna().all().all():
        _fail(errors, "A suppressed AMR cell retains a protected value")

    standardised = pd.read_csv(ROOT / "data/dashboard/standardised_amr.csv.gz")
    if not standardised["n_tested"].ge(30).all():
        _fail(errors, "A standardised AMR cell has fewer than 30 tested isolates")
    if not standardised["standardised_resistance_pct"].between(0, 100).all():
        _fail(errors, "A standardised AMR estimate is outside 0–100%")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Release validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
