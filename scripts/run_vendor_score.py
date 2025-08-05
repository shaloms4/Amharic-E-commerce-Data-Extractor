#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ner_infer import (
    extract_entities,
    load_ner_model,
    parse_price_values,
    predict_labels,
)
from src.analytics.vendor_score import SCORE_WEIGHTS, build_vendor_scorecard
from src.config import PROCESSED_DIR, ROOT_DIR


def resolve_model_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    selected = (ROOT_DIR / "models" / "SELECTED_MODEL.txt").read_text(encoding="utf-8").strip()
    candidate = ROOT_DIR / "models" / selected / "best"
    if candidate.exists():
        return candidate
    alt = ROOT_DIR / "models" / selected
    if (alt / "config.json").exists():
        return alt
    raise FileNotFoundError(f"Could not find model for '{selected}' under models/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vendor lending scorecard from NER + metadata")
    parser.add_argument("--input", type=Path, default=PROCESSED_DIR / "messages.csv")
    parser.add_argument("--model-dir", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT_DIR / "reports" / "vendor_scorecard",
    )
    parser.add_argument("--max-length", type=int, default=256)
    args = parser.parse_args()

    model_dir = resolve_model_dir(args.model_dir)
    print(f"Model: {model_dir}")

    df = pd.read_csv(args.input)
    df["cleaned_text"] = df["cleaned_text"].fillna("")
    df["tokens"] = df["tokens"].fillna("")
    df = df[df["tokens"].str.len() > 0].copy()
    if args.limit is not None:
        df = df.head(args.limit).copy()
    print(f"Scoring {len(df)} posts across {df['channel'].nunique()} vendors")

    tokenizer, model, device = load_ner_model(model_dir)
    print(f"Device: {device}")

    entity_rows = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="NER"):
        tokens = str(row["tokens"]).split()
        labels = predict_labels(tokens, tokenizer, model, device, max_length=args.max_length)
        entities = extract_entities(tokens, labels)
        prices = parse_price_values(entities)
        entity_rows.append(
            {
                "channel": row["channel"],
                "message_id": row["message_id"],
                "date": row["date"],
                "views": row["views"],
                "cleaned_text": row["cleaned_text"],
                "entities": entities,
                "prices": prices,
                "labels": " ".join(labels),
            }
        )

    ner_df = pd.DataFrame(entity_rows)
    scorecard = build_vendor_scorecard(ner_df)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ner_path = args.out_dir / "post_ner_extractions.jsonl"
    with ner_path.open("w", encoding="utf-8") as f:
        for rec in entity_rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    score_path = args.out_dir / "vendor_scorecard.csv"
    scorecard.to_csv(score_path, index=False)

    meta = {
        "model_dir": str(model_dir),
        "n_posts": len(ner_df),
        "vendors": int(ner_df["channel"].nunique()),
        "score_weights": SCORE_WEIGHTS,
        "scorecard_path": str(score_path),
        "extractions_path": str(ner_path),
    }
    (args.out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("\n=== Vendor lending scorecard ===")
    print(scorecard.to_string(index=False))
    print(f"\nWrote {score_path}")
    print(f"Wrote {ner_path}")
    print("Weights:", SCORE_WEIGHTS)


if __name__ == "__main__":
    main()
