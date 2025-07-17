import shap
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

class NERShapExplainer:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.model.eval()

    def explain(self, text):
        tokens = self.tokenizer(text, return_tensors="pt", truncation=True)
        input_ids = tokens['input_ids']

        def f(x):
            with torch.no_grad():
                outputs = self.model(torch.tensor(x, dtype=torch.long))
                return outputs.logits.detach().numpy()

        explainer = shap.Explainer(f, self.tokenizer)
        shap_values = explainer([text])
        shap.plots.text(shap_values[0])
