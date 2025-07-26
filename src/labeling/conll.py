from __future__ import annotations

from pathlib import Path


def write_conll(
    sentences: list[tuple[list[str], list[str]]],
    path: Path,
    *,
    meta_lines: list[str] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for idx, (tokens, labels) in enumerate(sentences):
        if len(tokens) != len(labels):
            raise ValueError(f"Token/label length mismatch at sentence {idx}")
        if meta_lines is not None:
            chunks.append(f"# {meta_lines[idx]}")
        for tok, lab in zip(tokens, labels):
            safe = tok.replace(" ", "_")
            chunks.append(f"{safe} {lab}")
        chunks.append("")
    path.write_text("\n".join(chunks), encoding="utf-8")
    return path


def write_review(sentences: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = [
        "EthioMart — draft labels for correction",
        "Edit data/labeled/amharic_ner.conll (token TAG per line).",
        "Tags: B-Product I-Product B-LOC I-LOC B-PRICE I-PRICE O",
        "=" * 72,
        "",
    ]
    for i, sent in enumerate(sentences, start=1):
        parts.append(
            f"[{i}] {sent['channel']} msg_id={sent['message_id']} "
            f"tokens={len(sent['tokens'])}"
        )
        parts.append(sent.get("cleaned_text", "")[:500])
        parts.append("-" * 40)
        for tok, lab in zip(sent["tokens"], sent["labels"]):
            mark = " " if lab == "O" else "*"
            parts.append(f"  {mark} {tok}\t{lab}")
        parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def read_conll(path: Path) -> list[tuple[list[str], list[str]]]:
    tokens: list[str] = []
    labels: list[str] = []
    sentences: list[tuple[list[str], list[str]]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            if tokens:
                sentences.append((tokens, labels))
                tokens, labels = [], []
            continue
        if line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        tokens.append(parts[0])
        labels.append(parts[-1])
    if tokens:
        sentences.append((tokens, labels))
    return sentences
