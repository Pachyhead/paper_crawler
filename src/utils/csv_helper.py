from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def save_titles_to_csv(
    records: Iterable[str | dict],
    output_path: str | Path,
) -> Path:
    """
    Save extracted titles to CSV with pandas default index + title column.

    Supported record shapes:
    - "Paper title"
    - {"title": "Paper title"}
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for record in records:
        title = _extract_title(record)
        if not title:
            continue
        rows.append({"title": title})

    frame = pd.DataFrame(rows, columns=["title"])
    frame.to_csv(output, index=True, encoding="utf-8")

    return output


def _extract_title(record: str | dict) -> str:
    if isinstance(record, str):
        return record.strip()

    if isinstance(record, dict):
        value = record.get("title")
        if value is None:
            return ""
        return str(value).strip()

    return ""
