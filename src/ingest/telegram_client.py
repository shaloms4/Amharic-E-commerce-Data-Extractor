from __future__ import annotations

from telethon import TelegramClient

from src.config import SESSION_NAME, SESSIONS_DIR, TELEGRAM_PHONE, require_telegram_credentials


def build_client() -> TelegramClient:
    api_id, api_hash = require_telegram_credentials()
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_path = SESSIONS_DIR / SESSION_NAME
    return TelegramClient(str(session_path), api_id, api_hash)


async def connect_client(client: TelegramClient) -> TelegramClient:
    if TELEGRAM_PHONE:
        await client.start(phone=TELEGRAM_PHONE)
    else:
        await client.start()
    return client
