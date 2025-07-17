# src/train_ner/prepare_data.py

def read_conll(filepath):
    sentences = []
    labels = []
    with open(filepath, encoding='utf-8') as f:
        tokens = []
        tags = []
        for line in f:
            line = line.strip()
            if not line:
                if tokens:
                    sentences.append(tokens)
                    labels.append(tags)
                    tokens = []
                    tags = []
            else:
                token, tag = line.split()
                tokens.append(token)
                tags.append(tag)
        if tokens:
            sentences.append(tokens)
            labels.append(tags)
    return sentences, labels
