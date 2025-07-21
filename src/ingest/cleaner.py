from __future__ import annotations

import re
import unicodedata

from cleantext import clean

_ETHIOPIC_OR_WORD = re.compile(
    r"[^\w\s\u1200-\u137F\u1380-\u139F\u2D80-\u2DDF"
    r"\uAB00-\uAB2F።፣፤፥፦፧፨./:%+\-ብር$€£,]",
    flags=re.UNICODE,
)
_URL = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_MENTION = re.compile(r"@[A-Za-z0-9_]+")
_MULTI_SPACE = re.compile(r"\s+")
_REPEAT_CHAR = re.compile(r"(.)\1{3,}", flags=re.DOTALL)


def normalize_amharic(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = _URL.sub(" ", text)
    text = _MENTION.sub(" ", text)
    text = clean(
        text,
        fix_unicode=True,
        to_ascii=False,
        lower=False,
        no_line_breaks=False,
        no_urls=True,
        no_emails=True,
        no_phone_numbers=False,
        no_numbers=False,
        no_digits=False,
        no_currency_symbols=False,
        no_punct=False,
        no_emoji=True,
        replace_with_url=" ",
        replace_with_email=" ",
        lang="en",
    )
    text = _ETHIOPIC_OR_WORD.sub(" ", text)
    text = _REPEAT_CHAR.sub(r"\1\1", text)
    text = _MULTI_SPACE.sub(" ", text).strip()
    return text
