import nltk
import re
from typing import Dict, List, Set, Tuple
import spacy
import spacy.cli
from collections import defaultdict

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

# Mapping of language names to spaCy model names
LANGUAGE_TO_MODEL = {
    "French": "fr_core_news_sm",
    "Spanish": "es_core_news_sm",
    "German": "de_core_news_sm",
    "Italian": "it_core_news_sm",
    "Japanese": "ja_core_news_sm",
    "Chinese": "zh_core_web_sm",
    "Russian": "ru_core_news_sm",
    "English": "en_core_web_sm"  # Default fallback
}

# Mapping of POS tags to categories
POS_TO_CATEGORY = {
    "NOUN": "Nouns",
    "PROPN": "Proper Nouns",
    "VERB": "Verbs",
    "ADJ": "Adjectives",
    "ADV": "Adverbs",
    "ADP": "Prepositions",
    "CONJ": "Conjunctions",
    "DET": "Determiners",
    "NUM": "Numbers",
    "PRON": "Pronouns",
    "INTJ": "Interjections",
    "PART": "Particles",
    "SYM": "Symbols",
    "X": "Other"
}

def load_language_model(language: str):
    """
    Load the appropriate spaCy language model.
    
    Args:
        language: The language name
        
    Returns:
        Loaded spaCy language model
    """
    model_name = LANGUAGE_TO_MODEL.get(language, "en_core_web_sm")
    
    try:
        # Try to load the model
        nlp = spacy.load(model_name)
        return nlp
    except OSError:
        # If model not found, download it
        spacy.cli.download(model_name)
        return spacy.load(model_name)

def categorize_words(
    text: str, 
    language: str, 
    min_length: int = 3, 
    include_proper_nouns: bool = False
) -> Dict[str, List[str]]:
    """
    Categorize words in the text by their part of speech using spaCy.
    
    Args:
        text: The text to process
        language: The language of the text
        min_length: Minimum word length to include
        include_proper_nouns: Whether to include proper nouns
        
    Returns:
        Dictionary mapping categories to lists of words
    """
    # Load language model
    nlp = load_language_model(language)
    
    # Process the text
    doc = nlp(text)
    
    # Initialize categories
    categories = defaultdict(set)
    
    # Process words
    for token in doc:
        # Skip punctuation and stop words
        if token.is_punct or token.is_stop or token.is_space:
            continue
        
        # Skip short words
        if len(token.text) < min_length:
            continue
        
        # Normalize word (lowercase unless it's a proper noun)
        word = token.text if token.pos_ == "PROPN" else token.text.lower()
        
        # Skip proper nouns if not included
        if token.pos_ == "PROPN" and not include_proper_nouns:
            continue
        
        # Add word to its category
        category = POS_TO_CATEGORY.get(token.pos_, "Other")
        categories[category].add(word)
    
    # Convert sets to sorted lists
    return {category: sorted(list(words)) for category, words in categories.items() if words}

def extract_lemmas(text: str, language: str) -> List[str]:
    """
    Extract lemmas (dictionary forms) of words in the text.
    
    Args:
        text: The text to process
        language: The language of the text
        
    Returns:
        List of lemmas
    """
    nlp = load_language_model(language)
    doc = nlp(text)
    
    # Extract lemmas, filtering out stop words and punctuation
    lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    
    return lemmas

def get_important_words(text: str, language: str, top_n: int = 100) -> List[str]:
    """
    Extract the most important words from the text using frequency.
    
    Args:
        text: The text to process
        language: The language of the text
        top_n: Number of top words to return
        
    Returns:
        List of the most important words
    """
    nlp = load_language_model(language)
    doc = nlp(text)
    
    # Count word frequencies (excluding stop words and punctuation)
    word_freq = defaultdict(int)
    for token in doc:
        if not token.is_stop and not token.is_punct and len(token.text) > 2:
            word_freq[token.lemma_] += 1
    
    # Sort words by frequency
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    return [word for word, freq in top_words]
