from transformers import pipeline
from lime.lime_text import LimeTextExplainer
import numpy as np

class NERLimeExplainer:
    def __init__(self, model_path):
        self.ner_pipeline = pipeline("ner", model=model_path, tokenizer=model_path, aggregation_strategy="simple")
        self.explainer = LimeTextExplainer(class_names=["O", "Product", "PRICE", "LOC"])

    def predict_proba(self, texts):
        """Convert LIME text input to simplified label probabilities."""
        outputs = []
        for text in texts:
            ner_result = self.ner_pipeline(text)
            probs = [0.0] * len(self.explainer.class_names)
            for ent in ner_result:
                if ent['entity_group'] in self.explainer.class_names:
                    probs[self.explainer.class_names.index(ent['entity_group'])] += ent['score']
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
            outputs.append(probs)
        return np.array(outputs)

    def explain(self, text):
        exp = self.explainer.explain_instance(text, self.predict_proba, num_features=10)
        exp.show_in_notebook(text=True)
