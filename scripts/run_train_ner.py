import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.train_ner.train import train_ner_model

if __name__ == "__main__":
    conll_path = "./data/labeled_data.conll"

    model_name = "rasyosef/bert-tiny-amharic"  # Or try "Davlan/bert-base-amharic"
    labels = ["O", "B-Product", "I-Product", "B-PRICE", "I-PRICE", "B-LOC", "I-LOC"]

    train_ner_model(conll_path, model_name, labels)
