from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
    r"|[\w\u1200-\u137F\u1380-\u139F\u2D80-\u2DDF\uAB00-\uAB2F]+"
    r"|[።፣፤፥፦፧፨]|[./:%+\-ብር$€£]+",
    flags=re.UNICODE,
)


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return _TOKEN_PATTERN.findall(text)
