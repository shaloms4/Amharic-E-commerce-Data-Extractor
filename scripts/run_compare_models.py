from src.train_ner.train import train_ner_model
import os

MODELS = {
    "bert-tiny-amharic": "rasyosef/bert-tiny-amharic",
    "xlm-roberta": "xlm-roberta-base",
    "mbert": "bert-base-multilingual-cased",
    "distil-mbert": "distilbert-base-multilingual-cased"
}

LABELS = ["O", "B-Product", "I-Product", "B-PRICE", "I-PRICE", "B-LOC", "I-LOC"]
CONLL_PATH = "labeled_data"

for name, model_id in MODELS.items():
    print(f"\n🔧 Training: {name}")
    output_path = f"models/{name}"
    os.makedirs(output_path, exist_ok=True)

    train_ner_model(
        conll_file=CONLL_PATH,
        model_name=model_id,
        label_list=LABELS,
        output_dir=output_path
    )

    print(f"Saved: {output_path}")
