# src/train_ner/tokenize_and_align.py

def tokenize_and_align_labels(tokenizer, texts, tags, label2id, max_len=128):
    tokenized_inputs = tokenizer(
        texts,
        truncation=True,
        is_split_into_words=True,
        padding='max_length',
        max_length=max_len,
        return_offsets_mapping=True
    )

    labels_aligned = []
    for i, label in enumerate(tags):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        aligned = []
        prev_word_id = None
        for word_id in word_ids:
            if word_id is None:
                aligned.append(-100)
            elif word_id != prev_word_id:
                aligned.append(label2id[label[word_id]])
            else:
                aligned.append(-100)  # Skip subword
            prev_word_id = word_id
        labels_aligned.append(aligned)

    tokenized_inputs['labels'] = labels_aligned
    return tokenized_inputs
