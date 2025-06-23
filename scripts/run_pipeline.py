import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from src.config import CHANNELS
from src.fetcher import fetch_channel_messages
from src.cleaner import clean_amharic
from src.tokenizer import tokenize_amharic
from src.storage import save_csv



async def main():
    all_cleaned = []

    for channel in CHANNELS:
        print(f"Fetching from {channel}...")
        messages = await fetch_channel_messages(channel)

        for msg in messages:
            if not msg['text']:
                continue
            clean_text = clean_amharic(msg['text'])
            tokens = tokenize_amharic(clean_text)

            structured = {
                **msg,
                "cleaned_text": clean_text,
                "tokens": tokens
            }

            all_cleaned.append(structured)

    save_csv(all_cleaned)


if __name__ == "__main__":
    asyncio.run(main())
