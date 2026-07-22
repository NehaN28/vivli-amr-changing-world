from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import config_path


class CountryCrosswalk:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path("country_crosswalk.csv")
        table = pd.read_csv(self.path, dtype=str).fillna("")
        if table["alias"].duplicated().any():
            duplicates = table.loc[table["alias"].duplicated(False), "alias"].tolist()
            raise ValueError(f"Duplicate country aliases: {duplicates[:5]}")
        self.table = table
        self._mapping = table.set_index("alias").to_dict(orient="index")

    @staticmethod
    def normalize(value: object) -> str:
        return " ".join(str(value).strip().casefold().split())

    def map_series(self, values: pd.Series, source: str) -> pd.DataFrame:
        keys = values.map(self.normalize)
        source_keys = (source.casefold() + "::" + keys).tolist()
        rows = []
        for generic, specific in zip(keys, source_keys):
            row = self._mapping.get(specific) or self._mapping.get(generic)
            rows.append(row or {"country": "", "iso3": "", "m49": "", "status": "unmapped"})
        result = pd.DataFrame(rows, index=values.index)
        result["source_country"] = values.astype("string")
        return result[["source_country", "country", "iso3", "m49", "status"]]


def attach_country_keys(frame: pd.DataFrame, column: str, source: str) -> pd.DataFrame:
    mapped = CountryCrosswalk().map_series(frame[column], source)
    result = frame.copy()
    for field in ["country", "iso3", "m49", "status"]:
        result[f"country_{field}" if field == "status" else field] = mapped[field].values
    return result

