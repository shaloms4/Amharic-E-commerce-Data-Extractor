from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt')

def tokenize_amharic(text):
    return word_tokenize(text, preserve_line=True)
