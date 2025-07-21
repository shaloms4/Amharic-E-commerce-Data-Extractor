#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DEFAULT_CHANNELS, MESSAGES_PER_CHANNEL
from src.ingest.cleaner import normalize_amharic
from src.ingest.fetcher import fetch_all_channels
from src.ingest.storage import (
    save_content_csv,
    save_metadata_csv,
    save_processed,
    save_raw_jsonl,
)
from src.ingest.telegram_client import build_client, connect_client
from src.ingest.tokenizer import tokenize


def preprocess_records(raw_records: list[dict]) -> list[dict]:
    processed = []
    for row in raw_records:
        cleaned = normalize_amharic(row.get("raw_text") or "")
        tokens = tokenize(cleaned)
        processed.append(
            {
                "channel": row.get("channel"),
                "message_id": row.get("message_id"),
                "date": row.get("date"),
                "views": row.get("views"),
                "forwards": row.get("forwards"),
                "has_photo": row.get("has_photo"),
                "has_document": row.get("has_document"),
                "media_type": row.get("media_type"),
                "cleaned_text": cleaned,
                "tokens": " ".join(tokens),
                "token_count": len(tokens),
            }
        )
    return processed


async def run(channels: list[str], limit: int) -> None:
    client = build_client()
    await connect_client(client)
    try:
        print(f"Scraping {len(channels)} channels × {limit} messages (metadata only)...")
        raw = await fetch_all_channels(client, channels, limit_per_channel=limit)
    finally:
        await client.disconnect()

    if not raw:
        print("No messages scraped. Check channel usernames and Telegram login.")
        return

    jsonl_path = save_raw_jsonl(raw)
    meta_path = save_metadata_csv(raw)
    content_path = save_content_csv(raw)
    processed = preprocess_records(raw)
    processed_path = save_processed(processed)

    print("Wrote:")
    print(f"  raw JSONL:     {jsonl_path}")
    print(f"  metadata CSV:  {meta_path}")
    print(f"  content CSV:   {content_path}")
    print(f"  processed CSV: {processed_path}")
    print(f"Total messages: {len(raw)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EthioMart Telegram ingest pipeline")
    parser.add_argument("--channels", nargs="+", default=DEFAULT_CHANNELS)
    parser.add_argument("--limit", type=int, default=MESSAGES_PER_CHANNEL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    channels = [c.lstrip("@") for c in args.channels]
    asyncio.run(run(channels, args.limit))


if __name__ == "__main__":
    main()
