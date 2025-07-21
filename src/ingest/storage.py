from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR

RAW_COLUMNS = [
    "channel",
    "message_id",
    "date",
    "views",
    "forwards",
    "has_photo",
    "has_document",
    "media_type",
    "raw_text",
]

PROCESSED_COLUMNS = [
    "channel",
    "message_id",
    "date",
    "views",
    "forwards",
    "has_photo",
    "has_document",
    "media_type",
    "cleaned_text",
    "tokens",
    "token_count",
]


def ensure_data_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def save_raw_jsonl(records: Iterable[dict[str, Any]], path: Path | None = None) -> Path:
    ensure_data_dirs()
    out = path or (RAW_DIR / "messages.jsonl")
    count = 0
    with out.open("w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    if count == 0:
        out.write_text("", encoding="utf-8")
    return out


def save_metadata_csv(records: list[dict[str, Any]], path: Path | None = None) -> Path:
    ensure_data_dirs()
    out = path or (RAW_DIR / "messages_metadata.csv")
    meta_cols = [c for c in RAW_COLUMNS if c != "raw_text"]
    rows = [{k: r.get(k) for k in meta_cols} for r in records]
    pd.DataFrame(rows, columns=meta_cols).to_csv(out, index=False)
    return out


def save_content_csv(records: list[dict[str, Any]], path: Path | None = None) -> Path:
    ensure_data_dirs()
    out = path or (RAW_DIR / "messages_content.csv")
    rows = [
        {
            "channel": r.get("channel"),
            "message_id": r.get("message_id"),
            "raw_text": r.get("raw_text", ""),
        }
        for r in records
    ]
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def save_processed(records: list[dict[str, Any]], path: Path | None = None) -> Path:
    ensure_data_dirs()
    out = path or (PROCESSED_DIR / "messages.csv")
    df = pd.DataFrame(records)
    for col in PROCESSED_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[PROCESSED_COLUMNS]
    df.to_csv(out, index=False)
    return out
