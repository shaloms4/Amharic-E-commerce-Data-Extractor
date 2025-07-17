import os
from src.analytics.vendor_score import analyze_vendor
import json

DATA_DIR = "data/processed_posts"
OUTPUT_FILE = "data/vendor_scores.json"

results = []

for file in os.listdir(DATA_DIR):
    if file.endswith(".json"):
        file_path = os.path.join(DATA_DIR, file)
        result = analyze_vendor(file_path)
        results.append(result)
        print(f"✅ Analyzed: {file} → Score: {result['lending_score']}")

# Save all scores
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n📊 Saved final scores to:", OUTPUT_FILE)
