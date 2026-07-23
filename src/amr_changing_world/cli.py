from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline, validate_sources
from .phase3 import run_phase3
from .phase4 import run_phase4
from .phase5 import run_phase5
from .phase8 import run_phase8_tables
from .phase8_analysis import run_phase8_analysis


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="AMR changing-world reproducible data pipeline")
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate required source files and compute hashes")
    validate.add_argument("--raw-dir", required=True, type=Path)
    build = commands.add_parser("build", help="Build all Phase 2 analytical tables")
    build.add_argument("--raw-dir", required=True, type=Path)
    build.add_argument("--output-dir", required=True, type=Path)
    phase3 = commands.add_parser("phase3", help="Build blinded Phase 3 feasibility and model-lock tables")
    phase3.add_argument("--processed-dir", required=True, type=Path)
    phase3.add_argument("--output-dir", required=True, type=Path)
    phase4 = commands.add_parser("phase4", help="Fit locked Phase 4 statistical models")
    phase4.add_argument("--processed-dir", required=True, type=Path)
    phase4.add_argument("--output-dir", required=True, type=Path)
    phase4.add_argument("--bootstrap-replications", type=int, default=9999)
    phase5 = commands.add_parser("phase5", help="Fit Phase 5 One Health and R&D analyses")
    phase5.add_argument("--processed-dir", required=True, type=Path)
    phase5.add_argument("--phase4-dir", required=True, type=Path)
    phase5.add_argument("--output-dir", required=True, type=Path)
    phase8 = commands.add_parser(
        "phase8-tables", help="Build annual disclosure-safe Phase 8 dashboard tables"
    )
    phase8.add_argument("--processed-dir", required=True, type=Path)
    phase8.add_argument("--output-dir", required=True, type=Path)
    phase8b = commands.add_parser(
        "phase8-analysis", help="Run exploratory Phase 8 longitudinal analyses"
    )
    phase8b.add_argument("--table-dir", required=True, type=Path)
    phase8b.add_argument("--output-dir", required=True, type=Path)
    return root


def main() -> None:
    arguments = parser().parse_args()
    if arguments.command == "validate":
        paths, manifest = validate_sources(arguments.raw_dir)
        payload = {"resolved": {key: str(value) for key, value in paths.items()},
                   "manifest": manifest.to_dict(orient="records")}
    elif arguments.command == "build":
        payload = run_pipeline(arguments.raw_dir, arguments.output_dir)
    elif arguments.command == "phase3":
        payload = run_phase3(arguments.processed_dir, arguments.output_dir)
    elif arguments.command == "phase4":
        payload = run_phase4(
            arguments.processed_dir, arguments.output_dir, arguments.bootstrap_replications
        )
    elif arguments.command == "phase5":
        payload = run_phase5(arguments.processed_dir, arguments.phase4_dir, arguments.output_dir)
    elif arguments.command == "phase8-tables":
        payload = run_phase8_tables(arguments.processed_dir, arguments.output_dir)
    else:
        payload = run_phase8_analysis(arguments.table_dir, arguments.output_dir)
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
