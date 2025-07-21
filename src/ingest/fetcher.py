from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from telethon import TelegramClient
from telethon.tl.custom.message import Message
from tqdm.asyncio import tqdm as atqdm


def _media_flags(message: Message) -> tuple[bool, bool, str | None]:
    has_photo = message.photo is not None
    has_document = message.document is not None
    media_type = None
    if has_photo:
        media_type = "photo"
    elif has_document:
        mime = getattr(message.document, "mime_type", None) or "document"
        media_type = mime
    elif message.media is not None:
        media_type = type(message.media).__name__
    return has_photo, has_document, media_type


def message_to_record(channel: str, message: Message) -> dict[str, Any] | None:
    text = (message.message or "").strip()
    has_photo, has_document, media_type = _media_flags(message)
    if not text and not has_photo and not has_document:
        return None

    date = message.date
    if isinstance(date, datetime):
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        date_str = date.isoformat()
    else:
        date_str = None

    return {
        "channel": channel.lstrip("@"),
        "message_id": message.id,
        "date": date_str,
        "views": message.views,
        "forwards": message.forwards,
        "has_photo": has_photo,
        "has_document": has_document,
        "media_type": media_type,
        "raw_text": text,
        "media_downloaded": False,
    }


async def fetch_channel_messages(
    client: TelegramClient,
    channel: str,
    limit: int = 300,
) -> list[dict[str, Any]]:
    entity = channel if channel.startswith("@") else f"@{channel}"
    records: list[dict[str, Any]] = []
    async for message in atqdm(
        client.iter_messages(entity, limit=limit),
        total=limit,
        desc=entity,
        leave=True,
    ):
        row = message_to_record(channel, message)
        if row is not None:
            records.append(row)
    return records


async def fetch_all_channels(
    client: TelegramClient,
    channels: list[str],
    limit_per_channel: int = 300,
) -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for channel in channels:
        try:
            rows = await fetch_channel_messages(client, channel, limit=limit_per_channel)
            all_rows.extend(rows)
            print(f"[ok] {channel}: {len(rows)} messages")
        except Exception as exc:  # noqa: BLE001
            msg = f"[error] {channel}: {exc}"
            print(msg)
            errors.append(msg)
    if errors:
        print(f"Finished with {len(errors)} channel error(s).")
    return all_rows
