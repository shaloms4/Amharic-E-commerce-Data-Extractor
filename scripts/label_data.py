#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import LABELED_DIR, PROCESSED_DIR
from src.labeling.conll import write_conll, write_review
from src.labeling.heuristics import label_tokens

PRICE_RE = re.compile(r"ብር|ዋጋ|birr|Birr|Price|PRICE|ETB", re.IGNORECASE)


def parse_conll_with_meta(path: Path) -> list[dict]:
    if not path.exists():
        return []
    sentences: list[dict] = []
    tokens: list[str] = []
    labels: list[str] = []
    meta: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            if tokens:
                sentences.append(
                    {
                        "channel": meta.get("channel", ""),
                        "message_id": meta.get("message_id", ""),
                        "tokens": tokens,
                        "labels": labels,
                    }
                )
                tokens, labels, meta = [], [], {}
            continue
        if stripped.startswith("#"):
            body = stripped.lstrip("#").strip()
            for part in body.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    meta[k] = v
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        tokens.append(parts[0])
        labels.append(parts[-1])
    if tokens:
        sentences.append(
            {
                "channel": meta.get("channel", ""),
                "message_id": meta.get("message_id", ""),
                "tokens": tokens,
                "labels": labels,
            }
        )
    return sentences


def existing_keys(sentences: list[dict]) -> set[tuple[str, str]]:
    return {
        (str(s.get("channel", "")), str(s.get("message_id", "")))
        for s in sentences
        if s.get("message_id") != ""
    }


def select_messages(
    df: pd.DataFrame,
    n: int,
    seed: int,
    *,
    exclude: set[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    work = df.copy()
    work["cleaned_text"] = work["cleaned_text"].fillna("")
    work["tokens"] = work["tokens"].fillna("")
    work["message_id"] = work["message_id"].astype(str)
    work["channel"] = work["channel"].astype(str)
    work = work[work["token_count"].fillna(0).astype(int).between(8, 70)]
    work = work[work["cleaned_text"].str.contains(PRICE_RE)]
    work = work[work["tokens"].str.len() > 0]
    work = work.drop_duplicates(subset=["cleaned_text"])

    if exclude:
        mask = work.apply(
            lambda r: (r["channel"], r["message_id"]) not in exclude, axis=1
        )
        work = work[mask]

    channels = work["channel"].unique().tolist()
    if not channels:
        raise RuntimeError("No candidate messages found for labeling.")

    per = max(1, n // len(channels))
    parts: list[pd.DataFrame] = []
    for ch in channels:
        subset = work[work["channel"] == ch]
        take = min(per, len(subset))
        if take:
            parts.append(subset.sample(n=take, random_state=seed))

    sampled = pd.concat(parts, ignore_index=True) if parts else work.head(0)
    if len(sampled) < n:
        remaining = work[~work.index.isin(sampled.index)]
        remaining = remaining[~remaining["cleaned_text"].isin(set(sampled["cleaned_text"]))]
        need = n - len(sampled)
        if need > 0 and len(remaining) > 0:
            extra = remaining.sample(n=min(need, len(remaining)), random_state=seed + 1)
            sampled = pd.concat([sampled, extra], ignore_index=True)

    if len(sampled) > n:
        sampled = sampled.sample(n=n, random_state=seed).reset_index(drop=True)
    else:
        sampled = sampled.reset_index(drop=True)

    if len(sampled) < n:
        print(f"Warning: only found {len(sampled)} candidates (requested {n}).")
    return sampled


def rows_to_labeled(sampled: pd.DataFrame) -> tuple[list[tuple], list[dict], list[str]]:
    sentences_conll: list[tuple[list[str], list[str]]] = []
    review_rows: list[dict] = []
    meta: list[str] = []
    for _, row in sampled.iterrows():
        tokens = str(row["tokens"]).split()
        labels = label_tokens(tokens)
        sentences_conll.append((tokens, labels))
        meta.append(f"channel={row['channel']} message_id={row['message_id']}")
        review_rows.append(
            {
                "channel": row["channel"],
                "message_id": row["message_id"],
                "cleaned_text": row["cleaned_text"],
                "tokens": tokens,
                "labels": labels,
            }
        )
    return sentences_conll, review_rows, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft CoNLL labels for Amharic NER")
    parser.add_argument("--input", type=Path, default=PROCESSED_DIR / "messages.csv")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--out", type=Path, default=LABELED_DIR / "amharic_ner.conll")
    parser.add_argument("--review", type=Path, default=LABELED_DIR / "amharic_ner_REVIEW.txt")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    existing = parse_conll_with_meta(args.out) if args.append else []
    exclude = existing_keys(existing) if args.append else set()

    sampled = select_messages(df, args.n, args.seed, exclude=exclude)
    new_conll, new_review, new_meta = rows_to_labeled(sampled)

    if args.append and existing:
        all_conll = [(s["tokens"], s["labels"]) for s in existing] + new_conll
        all_meta = [
            f"channel={s['channel']} message_id={s['message_id']}" for s in existing
        ] + new_meta
        text_lookup = {
            (str(r.channel), str(r.message_id)): r.cleaned_text for r in df.itertuples()
        }
        all_review = []
        for s in existing:
            key = (str(s["channel"]), str(s["message_id"]))
            all_review.append(
                {
                    "channel": s["channel"],
                    "message_id": s["message_id"],
                    "cleaned_text": text_lookup.get(key, ""),
                    "tokens": s["tokens"],
                    "labels": s["labels"],
                }
            )
        all_review.extend(new_review)
        print(f"Appending {len(new_conll)} to existing {len(existing)}")
    else:
        all_conll, all_review, all_meta = new_conll, new_review, new_meta

    conll_path = write_conll(all_conll, args.out, meta_lines=all_meta)
    review_path = write_review(all_review, args.review)

    counts: Counter[str] = Counter()
    for _, labels in all_conll:
        counts.update(labels)

    channel_counts: Counter[str] = Counter()
    for m in all_meta:
        for part in m.split():
            if part.startswith("channel="):
                channel_counts[part.split("=", 1)[1]] += 1

    print(f"Total labeled messages: {len(all_conll)}")
    print(f"  CoNLL:  {conll_path}")
    print(f"  Review: {review_path}")
    print("Tag counts:", dict(counts))
    print("Channels:", dict(channel_counts))


if __name__ == "__main__":
    main()
