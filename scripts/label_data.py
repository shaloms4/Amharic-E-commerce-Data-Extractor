import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import csv
from src.tokenizer import tokenize_amharic

INPUT_CSV = "data/messages.csv"
OUTPUT_CONLL = "data/labeled_data.conll"

def label_tokens(tokens):
    print("\nTokens:")
    print(" | ".join(tokens))
    print("\nEnter labels for each token separated by spaces:")
    print("Available labels: B-Product, I-Product, B-LOC, I-LOC, B-PRICE, I-PRICE, O")
    labels = input("> ").strip().split()
    if len(labels) != len(tokens):
        print(f"Error: Number of labels ({len(labels)}) does not match number of tokens ({len(tokens)}). Try again.")
        return None
    return labels

def main():
    mode = "a" if os.path.exists(OUTPUT_CONLL) else "w"
    with open(INPUT_CSV, encoding="utf-8") as csvfile, \
         open(OUTPUT_CONLL, mode, encoding="utf-8") as outfile:

        reader = csv.DictReader(csvfile)
        labeled_count = 0

        for row in reader:
            message = row.get("cleaned_text") or row.get("text")
            if not message or message.strip() == "":
                continue

            tokens = tokenize_amharic(message)
            print("\n--- Message to label ---")
            print(message)

            labels = label_tokens(tokens)
            if labels is None:
                print("Skipping this message. Try again with a different one.")
                continue

            for token, label in zip(tokens, labels):
                outfile.write(f"{token}\t{label}\n")
            outfile.write("\n")  # blank line between messages

            labeled_count += 1
            print(f"Labeled messages so far: {labeled_count}")

            if labeled_count >= 50:
                print("Reached labeling limit of 50 messages. Exiting.")
                break

if __name__ == "__main__":
    main()
