from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationReport:
    checks: list[dict[str, object]] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: object) -> None:
        self.checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def require_columns(self, frame: pd.DataFrame, columns: list[str], table: str) -> None:
        missing = sorted(set(columns) - set(frame.columns))
        self.add(f"{table}: required columns", not missing, {"missing": missing})
        if missing:
            raise ValueError(f"{table} missing required columns: {missing}")

    def unique_key(self, frame: pd.DataFrame, columns: list[str], table: str) -> None:
        count = int(frame.duplicated(columns).sum())
        self.add(f"{table}: unique key", count == 0, {"key": columns, "duplicates": count})
        if count:
            raise ValueError(f"{table} has {count} duplicate keys for {columns}")

    @property
    def passed(self) -> bool:
        return all(item["passed"] for item in self.checks)

