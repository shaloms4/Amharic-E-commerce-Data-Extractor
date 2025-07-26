from __future__ import annotations

import re

PRICE_TRIGGER = re.compile(r"^(ዋጋ|ዋጋ፦|ዋጋ፡|price|Price|PRICE)$")
PRICE_UNIT = re.compile(r"^(ብር|birr|Birr|ETB)$", re.IGNORECASE)
NUMBER = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$|^\d+(?:\.\d+)?$")
PHONE = re.compile(r"^\d{9,13}$")
LATIN_WORD = re.compile(r"^[A-Za-z][A-Za-z0-9+\-/%]*$")

LOC_LEXICON = {
    "አዲስ",
    "አበባ",
    "አዲስአበባ",
    "ቦሌ",
    "መገናኛ",
    "መርካቶ",
    "ፒያሳ",
    "ካዛንቺስ",
    "ሳሪስ",
    "ላፍቶ",
    "ሜክሲኮ",
    "CMC",
    "መሰረት",
    "ደፋር",
    "ሞል",
    "ሞሉ",
    "ፎቅ",
    "ቢሮ",
    "ሀዋሳ",
    "ባህርዳር",
    "ጎንደር",
    "መቀሌ",
    "ጅማ",
    "ድሬዳዋ",
    "አዳማ",
    "ኮሜርስ",
    "ፕላዛ",
    "Plaza",
    "plaza",
    "Mall",
    "mall",
}

PRODUCT_STOP = {
    "ዋጋ",
    "ዋጋ፦",
    "ዋጋ፡",
    "ብር",
    "ውስን",
    "ፍሬ",
    "ነው",
    "ያለው",
    "አድራሻ",
    "በTelegram",
    "ለማዘዝ",
    "ይጠቀሙ",
    "ለተጨማሪ",
    "ማብራሪያ",
    "የቴሌግራም",
    "ገፃችን",
    "እና",
    "ወይም",
    "ከ",
    "ለ",
    "በ",
    "የ",
    "ጋር",
    "ላይ",
    "ውስጥ",
    "ነው።",
    "..",
    ".",
    ":",
    "/",
    "Usage",
    "Features",
    "Volume",
    "Scent",
    "Designed",
    "for",
    "and",
    "the",
    "with",
}

ADDRESS_STOP = {
    "ለማዘዝ",
    "ይጠቀሙ",
    "በTelegram",
    "Telegram",
    "ለተጨማሪ",
    "ማብራሪያ",
    "የቴሌግራም",
    "ገፃችን",
    "ይደውሉ",
    "ይጻፉ",
}


def _bio_span(labels: list[str], start: int, end: int, entity: str) -> None:
    if start >= end or start < 0 or end > len(labels):
        return
    if any(labels[i] != "O" for i in range(start, end)):
        return
    labels[start] = f"B-{entity}"
    for i in range(start + 1, end):
        labels[i] = f"I-{entity}"


def label_tokens(tokens: list[str]) -> list[str]:
    n = len(tokens)
    labels = ["O"] * n
    if n == 0:
        return labels

    i = 0
    while i < n:
        tok = tokens[i]
        if PRICE_TRIGGER.match(tok) and i + 1 < n and NUMBER.match(tokens[i + 1]):
            j = i + 1
            end = j + 1
            if end < n and PRICE_UNIT.match(tokens[end]):
                end += 1
            _bio_span(labels, j, end, "PRICE")
            i = end
            continue
        if NUMBER.match(tok):
            if PHONE.match(tok.replace(",", "")):
                i += 1
                continue
            end = i + 1
            if end < n and PRICE_UNIT.match(tokens[end]):
                end += 1
                _bio_span(labels, i, end, "PRICE")
                i = end
                continue
            if i > 0 and PRICE_TRIGGER.match(tokens[i - 1]):
                _bio_span(labels, i, i + 1, "PRICE")
        i += 1

    for i, tok in enumerate(tokens):
        glued = tok.startswith("አድራሻ-") or tok.startswith("አድራሻ፡") or tok.startswith("አድራሻ:")
        if tok != "አድራሻ" and not glued:
            continue
        start = i if glued else i + 1
        while start < n and tokens[start] in {"-", ":", "፡", "–"}:
            start += 1
        j = max(start, i + 1)
        while j < n:
            t = tokens[j]
            if t in ADDRESS_STOP or PHONE.match(t.replace(",", "")) or PRICE_TRIGGER.match(t):
                break
            if t in {"or", "call", "Call"}:
                break
            if labels[j] != "O":
                break
            j += 1
        if j > start:
            _bio_span(labels, start, j, "LOC")

    for i, tok in enumerate(tokens):
        if labels[i] != "O":
            continue
        base = tok.strip("_")
        if base in LOC_LEXICON or tok in LOC_LEXICON:
            j = i + 1
            while j < n and labels[j] == "O":
                b = tokens[j].strip("_")
                if b in LOC_LEXICON or tokens[j] in LOC_LEXICON or "_" in tokens[j]:
                    j += 1
                else:
                    break
            _bio_span(labels, i, max(j, i + 1), "LOC")

    price_idx = next((k for k, t in enumerate(tokens) if PRICE_TRIGGER.match(t) or t == "ብር"), n)
    for k, t in enumerate(tokens):
        if PRICE_TRIGGER.match(t):
            price_idx = k
            break

    start = 0
    while start < price_idx and (tokens[start] in {".", "..", "..."} or tokens[start] in PRODUCT_STOP):
        start += 1

    end = start
    while end < price_idx:
        tok = tokens[end]
        if tok in PRODUCT_STOP and end > start:
            if LATIN_WORD.match(tok) and end + 1 < price_idx and LATIN_WORD.match(tokens[end + 1]):
                end += 1
                continue
            break
        if PHONE.match(tok.replace(",", "")):
            break
        if tok == "አድራሻ" or tok.startswith("አድራሻ-"):
            break
        end += 1

    while end > start and tokens[end - 1] in PRODUCT_STOP | {".", "..", ":", "-", "/"}:
        end -= 1

    if end - start >= 2:
        _bio_span(labels, start, end, "Product")
    elif end - start == 1 and (LATIN_WORD.match(tokens[start]) or len(tokens[start]) >= 3):
        _bio_span(labels, start, end, "Product")

    return labels
