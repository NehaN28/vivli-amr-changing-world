from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import config_path, load_yaml
from .io import sha256_file, write_json, write_table
from .linkage import build_master, disclosure_safe
from .transforms.acled import process_acled
from .transforms.atlas import process_atlas
from .transforms.livestock import process_livestock
from .transforms.rd import process_rd
from .transforms.temperature import process_temperature
from .transforms.woah import process_woah
from .validation import ValidationReport


def resolve_inputs(raw_dir: Path) -> dict[str, Path]:
    manifest = load_yaml(config_path("data_manifest.yml"))
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for source, details in manifest.items():
        path = raw_dir / details["filename"]
        if path.exists():
            resolved[source] = path
        else:
            missing.append(details["filename"])
    if missing:
        raise FileNotFoundError(f"Missing source files in {raw_dir}: {missing}")
    return resolved


def validate_sources(raw_dir: Path) -> tuple[dict[str, Path], pd.DataFrame]:
    paths = resolve_inputs(raw_dir)
    rows = []
    for source, path in paths.items():
        rows.append({
            "source": source, "filename": path.name, "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return paths, pd.DataFrame(rows)


def run_pipeline(raw_dir: Path, output_dir: Path) -> dict[str, object]:
    paths, source_manifest = validate_sources(raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = ValidationReport()
    produced: dict[str, str] = {}
    produced["source_manifest"] = str(write_table(source_manifest, output_dir, "source_manifest"))

    atlas_result = process_atlas(paths["atlas"], output_dir / "restricted", report)
    atlas_summary = atlas_result["summary"]
    atlas_strata = atlas_result["strata"]
    produced["atlas_endpoint_isolates"] = str(atlas_result["isolates_path"])
    produced["atlas_country_year_endpoint"] = str(write_table(atlas_summary, output_dir, "atlas_country_year_endpoint"))
    produced["atlas_composition_strata"] = str(write_table(atlas_strata, output_dir / "restricted", "atlas_composition_strata"))

    acled_month, acled_year = process_acled(paths["acled"], report)
    produced["acled_country_month"] = str(write_table(acled_month, output_dir, "acled_country_month"))
    produced["acled_country_year"] = str(write_table(acled_year, output_dir, "acled_country_year"))
    temperature = process_temperature(paths["temperature"], report)
    produced["temperature_country_year"] = str(write_table(temperature, output_dir, "temperature_country_year"))
    livestock_detail, livestock_group = process_livestock(paths["livestock"], report)
    produced["livestock_item_country_year"] = str(write_table(livestock_detail, output_dir, "livestock_item_country_year"))
    produced["livestock_country_year_group"] = str(write_table(livestock_group, output_dir, "livestock_country_year_group"))
    woah_country, woah_class, woah_participation = process_woah(paths["woah"], report)
    produced["woah_country_year"] = str(write_table(woah_country, output_dir, "woah_country_year"))
    produced["woah_class_long"] = str(write_table(woah_class, output_dir, "woah_class_long"))
    produced["woah_participation"] = str(write_table(woah_participation, output_dir, "woah_participation"))
    rd_clean, rd_fractional, rd_duplicates, rd_annual = process_rd(paths["rd"], report)
    produced["rd_projects_clean"] = str(write_table(rd_clean, output_dir, "rd_projects_clean"))
    produced["rd_fractional_categories"] = str(write_table(rd_fractional, output_dir, "rd_fractional_categories"))
    produced["rd_duplicate_audit"] = str(write_table(rd_duplicates, output_dir, "rd_duplicate_audit"))
    produced["rd_country_year_commitments"] = str(write_table(rd_annual, output_dir, "rd_country_year_commitments"))

    master = build_master(atlas_summary, acled_year, temperature, livestock_group, woah_country, rd_annual, report)
    produced["master_country_year_endpoint"] = str(write_table(master, output_dir / "restricted", "master_country_year_endpoint"))
    project = load_yaml(config_path("project.yml"))
    public = disclosure_safe(master, int(project["thresholds"]["public_suppression_n"]))
    produced["dashboard_country_year_endpoint"] = str(write_table(public, output_dir / "dashboard", "dashboard_country_year_endpoint"))

    report_path = output_dir / "validation_report.json"
    write_json({"passed": report.passed, "checks": report.checks, "outputs": produced}, report_path)
    produced["validation_report"] = str(report_path)
    if not report.passed:
        failed = [item for item in report.checks if not item["passed"]]
        raise ValueError(f"Pipeline validation failed: {failed}")
    return {"passed": True, "outputs": produced, "checks": report.checks}

