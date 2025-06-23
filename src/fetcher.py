import os
from src.telegram_client import client

async def fetch_channel_messages(channel, limit=10):
    await client.start()
    entity = await client.get_entity(channel)
    messages = await client.get_messages(entity, limit=limit)
    
    results = []
    for msg in messages:
        if msg.message:
            media_path = None
            if msg.media:
                media_path = f"images/{channel.strip('@')}_{msg.id}.jpg"
                await msg.download_media(file=media_path)

            results.append({
                "channel": channel,
                "timestamp": str(msg.date),
                "text": msg.message,
                "media_path": media_path,
                "sender_id": msg.sender_id
            })
    return results
