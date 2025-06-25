from src.interpret.ner_lime import NERLimeExplainer
from src.interpret.ner_shap import NERShapExplainer

model_path = "ner_model"

sample_text = "skechers ultra walker size 42 price 3500 birr አድራሻ ኮሜርስ ጀርባ"

# LIME explanation
lime_explainer = NERLimeExplainer(model_path)
lime_explainer.explain(sample_text)

# SHAP explanation
shap_explainer = NERShapExplainer(model_path)
shap_explainer.explain(sample_text)
