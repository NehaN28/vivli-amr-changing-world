from __future__ import annotations

import math
import re
from dataclasses import dataclass


MIC_PATTERN = re.compile(r"^\s*(<=|>=|<|>)?\s*([0-9]+(?:\.[0-9]+)?)\s*$")


@dataclass(frozen=True)
class ParsedMIC:
    raw: str | None
    lower: float | None
    upper: float | None
    censoring: str | None
    parsed: bool


def parse_mic(value: object) -> ParsedMIC:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ParsedMIC(None, None, None, None, True)
    raw = str(value).strip()
    if not raw or raw.casefold() in {"nan", "na", "n/a", "none"}:
        return ParsedMIC(None, None, None, None, True)
    match = MIC_PATTERN.match(raw)
    if not match:
        return ParsedMIC(raw, None, None, "unparsed", False)
    operator, number_text = match.groups()
    number = float(number_text)
    if operator in {"<", "<="}:
        return ParsedMIC(raw, None, number, "left", True)
    if operator in {">", ">="}:
        return ParsedMIC(raw, number, None, "right", True)
    return ParsedMIC(raw, number, number, "exact", True)

