# src/train_ner/train.py

from transformers import (
    AutoTokenizer, AutoModelForTokenClassification,
    Trainer, TrainingArguments, DataCollatorForTokenClassification
)
from datasets import Dataset
from sklearn.model_selection import train_test_split
from src.train_ner.prepare_data import read_conll
from src.train_ner.tokenize_and_align import tokenize_and_align_labels

def train_ner_model(conll_file, model_name, label_list, output_dir='ner_model'):
    label2id = {label: i for i, label in enumerate(label_list)}
    id2label = {i: label for label, i in label2id.items()}

    texts, tags = read_conll(conll_file)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id
    )

    X_train, X_val, y_train, y_val = train_test_split(texts, tags, test_size=0.2)

    train_data = tokenize_and_align_labels(tokenizer, X_train, y_train, label2id)
    val_data = tokenize_and_align_labels(tokenizer, X_val, y_val, label2id)

    train_dataset = Dataset.from_dict(train_data)
    val_dataset = Dataset.from_dict(val_data)

    training_args = TrainingArguments(
    output_dir="./ner_model",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    logging_dir="./logs",
    logging_steps=10,
    save_steps=10_000,
    save_total_limit=2,
    # Remove this line if your transformers version doesn't support it:
    # evaluation_strategy="steps",
)


    data_collator = DataCollatorForTokenClassification(tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
