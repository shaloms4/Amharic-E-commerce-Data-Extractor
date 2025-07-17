import csv
import os

def save_csv(data, filepath="data/messages.csv"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if not data:
        return

    fieldnames = list(data[0].keys())

    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for row in data:
            writer.writerow(row)
