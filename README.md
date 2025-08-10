# EthioMart — Amharic E-commerce NER

Extract **Product**, **Price**, and **Location** entities from Ethiopian Telegram
e-commerce channels, then turn vendor activity into a simple **lending score**.

## Pipeline

1. **Ingest** — scrape public channels with Telethon (text + metadata; no media downloads)
2. **Label** — CoNLL BIO tags (`B-/I-Product`, `B-/I-LOC`, `B-/I-PRICE`, `O`)
3. **Train** — fine-tune `xlm-roberta-base` on Colab
4. **Score** — run NER on posts and rank vendors

## Project layout

```text
data/
  raw/                 # scrape outputs (jsonl / csv)
  processed/           # cleaned text + tokens
  labeled/             # CoNLL labels
models/
  xlm-roberta-ner/     # fine-tuned checkpoint (gitignored)
notebooks/             # Colab training notebook
reports/
  vendor_scorecard/    # lending scores + NER extractions
scripts/               # CLI entrypoints
src/
  ingest/              # scrape, clean, tokenize, store
  labeling/            # draft CoNLL labels
  analytics/           # NER inference + scorecard
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu   # local inference
```

Create `.env` (see `.env.example`):

```env
api_id=YOUR_API_ID
api_hash=YOUR_API_HASH
TELEGRAM_PHONE=+2519XXXXXXXX   # optional, helps first login
```

## Usage

### 1. Scrape channels

Default channels: `ZemenExpress`, `ethio_brand_collection`, `Leyueqa`, `MerttEka`, `AwasMart`, `qnashcom` (300 messages each).

```bash
python scripts/run_pipeline.py
python scripts/run_pipeline.py --limit 100 --channels ZemenExpress Leyueqa
```

Writes:

| Path | Contents |
|------|----------|
| `data/raw/messages.jsonl` | Full records |
| `data/raw/messages_metadata.csv` | Metadata only |
| `data/raw/messages_content.csv` | Message text |
| `data/processed/messages.csv` | Cleaned text + tokens |

### 2. Label data (CoNLL)

```bash
python scripts/label_data.py --n 50 --seed 42
python scripts/label_data.py --n 50 --seed 43 --append
```

Edit `data/labeled/amharic_ner.conll` using `amharic_ner_REVIEW.txt` as a guide.

### 3. Train NER (Colab)

1. Open `notebooks/train_xlmr_roberta_base.ipynb` in Google Colab
2. Runtime → GPU
3. Upload `data/labeled/amharic_ner.conll`
4. Run all cells; download the model zip

Place the checkpoint at:

```text
models/xlm-roberta-ner/best/
models/xlm-roberta-ner/metrics.json
```

Ensure `models/SELECTED_MODEL.txt` contains `xlm-roberta-ner`.

**Validation metrics (this run):** micro-F1 **0.744**, precision **0.703**, recall **0.790**.

### 4. Vendor lending scorecard

```bash
python scripts/run_vendor_score.py
python scripts/run_vendor_score.py --limit 100   # quick test
```

Outputs under `reports/vendor_scorecard/`:

- `vendor_scorecard.csv` — per-vendor metrics + `lending_score`
- `post_ner_extractions.jsonl` — entities and prices per post

**Lending score**:

| Signal | Weight |
|--------|-------:|
| Posting frequency | 25% |
| Average views | 30% |
| Top-post views | 15% |
| Average extracted price | 20% |
| Share of posts with a price | 10% |

## Stack

- **Ingest:** Telethon, pandas, clean-text  
- **NER:** Hugging Face Transformers (`xlm-roberta-base`)  
- **Scorecard:** pandas  
