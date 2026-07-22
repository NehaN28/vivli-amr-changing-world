from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def write_table(frame: pd.DataFrame, output_dir: Path, stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / f"{stem}.parquet"
    try:
        frame.to_parquet(parquet_path, index=False)
        return parquet_path
    except (ImportError, ModuleNotFoundError):
        csv_path = output_dir / f"{stem}.csv.gz"
        frame.to_csv(csv_path, index=False, compression="gzip")
        return csv_path


def write_json(value: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def dataframe_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")

