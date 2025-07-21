from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LABELED_DIR = DATA_DIR / "labeled"
SESSIONS_DIR = ROOT_DIR / "sessions"

API_ID = os.getenv("TELEGRAM_API_ID") or os.getenv("api_id")
API_HASH = os.getenv("TELEGRAM_API_HASH") or os.getenv("api_hash")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE") or os.getenv("phone")
SESSION_NAME = os.getenv("TELEGRAM_SESSION", "ethiomart")

DEFAULT_CHANNELS: list[str] = [
    "ZemenExpress",
    "ethio_brand_collection",
    "Leyueqa",
    "MerttEka",
    "AwasMart",
    "qnashcom",
]

MESSAGES_PER_CHANNEL = int(os.getenv("MESSAGES_PER_CHANNEL", "300"))


def require_telegram_credentials() -> tuple[int, str]:
    if not API_ID or not API_HASH:
        raise RuntimeError(
            "Missing Telegram credentials. Set api_id and api_hash (or "
            "TELEGRAM_API_ID / TELEGRAM_API_HASH) in .env"
        )
    try:
        api_id = int(str(API_ID).strip())
    except ValueError as exc:
        raise RuntimeError("api_id must be an integer") from exc
    return api_id, str(API_HASH).strip()
