from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

PRICE_NUM = re.compile(r"[\d,]+(?:\.\d+)?")


def load_ner_model(model_dir: Path, device: str | None = None):
    model_dir = Path(model_dir)
    if not model_dir.exists():
        raise FileNotFoundError(f"Model not found: {model_dir}")
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForTokenClassification.from_pretrained(str(model_dir))
    model.to(device)
    model.eval()
    return tokenizer, model, device


def align_word_predictions(
    word_ids: list[int | None],
    pred_ids: list[int],
    id2label: dict[int, str],
) -> list[str]:
    labels: list[str] = []
    previous = None
    for word_id, pred in zip(word_ids, pred_ids):
        if word_id is None:
            continue
        if word_id != previous:
            labels.append(id2label[int(pred)])
            previous = word_id
    return labels


@torch.inference_mode()
def predict_labels(
    tokens: list[str],
    tokenizer,
    model,
    device: str,
    *,
    max_length: int = 256,
) -> list[str]:
    if not tokens:
        return []
    encoded = tokenizer(
        tokens,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    word_ids = encoded.word_ids(batch_index=0)
    encoded = {k: v.to(device) for k, v in encoded.items()}
    logits = model(**encoded).logits[0]
    pred_ids = logits.argmax(dim=-1).tolist()
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    if id2label and not isinstance(next(iter(model.config.id2label.keys())), int):
        id2label = {int(k): v for k, v in model.config.id2label.items()}
    labels = align_word_predictions(word_ids, pred_ids, id2label)
    if len(labels) < len(tokens):
        labels.extend(["O"] * (len(tokens) - len(labels)))
    return labels[: len(tokens)]


def extract_entities(tokens: list[str], labels: list[str]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    cur_type: str | None = None
    cur_toks: list[str] = []

    def flush() -> None:
        nonlocal cur_type, cur_toks
        if cur_type and cur_toks:
            text = " ".join(cur_toks)
            entities.append({"type": cur_type, "text": text, "tokens": list(cur_toks)})
        cur_type, cur_toks = None, []

    for tok, lab in zip(tokens, labels):
        if lab.startswith("B-"):
            flush()
            cur_type = lab[2:]
            cur_toks = [tok]
        elif lab.startswith("I-") and cur_type and lab[2:] == cur_type:
            cur_toks.append(tok)
        else:
            flush()
    flush()
    return entities


def parse_price_values(entities: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for ent in entities:
        if ent["type"] != "PRICE":
            continue
        for match in PRICE_NUM.findall(ent["text"].replace(" ", "")):
            try:
                values.append(float(match.replace(",", "")))
            except ValueError:
                continue
    return values
