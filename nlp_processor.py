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

def normalize_adjectives(adjectives: Set[str], language: str) -> List[str]:
    """
    Normalize adjectives by combining gender forms.
    For example, in Spanish: ['bueno', 'buena'] becomes ['bueno/buena']
    
    Args:
        adjectives: Set of adjective forms
        language: Language of the adjectives
        
    Returns:
        List of normalized adjectives
    """
    # Convert to lowercase for matching
    adj_list = [adj.lower() for adj in adjectives]
    
    # Skip if no adjectives
    if not adj_list:
        return []
    
    # Gender suffixes by language
    gender_suffixes = {
        "Spanish": [('o', 'a'), ('os', 'as')],
        "French": [('', 'e'), ('s', 'es')],
        "Italian": [('o', 'a'), ('i', 'e')],
        "Portuguese": [('o', 'a'), ('os', 'as')],
        # Add other languages as needed
    }
    
    # If language not supported, return original list
    if language not in gender_suffixes:
        return sorted(adj_list)
    
    # Group adjectives by potential gender pairs
    matched_pairs = set()
    normalized_adjs = []
    
    for adj in sorted(adj_list):
        # Skip if already processed
        if adj in matched_pairs:
            continue
        
        # Check for gender pairs
        found_match = False
        for male_suffix, female_suffix in gender_suffixes[language]:
            if adj.endswith(male_suffix) and len(adj) > len(male_suffix):
                # Create the potential female form
                stem = adj[:-len(male_suffix)] if male_suffix else adj
                female_form = stem + female_suffix
                
                # Check if the female form exists in our adjective list
                if female_form in adj_list:
                    matched_pairs.add(adj)
                    matched_pairs.add(female_form)
                    normalized_adjs.append(f"{adj}/{female_form}")
                    found_match = True
                    break
                
            elif adj.endswith(female_suffix) and len(adj) > len(female_suffix):
                # Create the potential male form
                stem = adj[:-len(female_suffix)]
                male_form = stem + male_suffix
                
                # Check if the male form exists in our adjective list
                if male_form in adj_list:
                    # Already handled when we encountered the male form
                    matched_pairs.add(adj)
                    matched_pairs.add(male_form)
                    found_match = True
                    break
        
        # If no gender match found, add as-is
        if not found_match:
            normalized_adjs.append(adj)
    
    return sorted(normalized_adjs)


def categorize_words(
    text: str, 
    language: str, 
    min_length: int = 3, 
    include_proper_nouns: bool = False,
    word_types: Dict[str, bool] = None,
    existing_words: Set[str] = None
) -> Dict[str, List[str]]:
    # Initialize default values for optional parameters
    if word_types is None:
        word_types = {
            "nouns": True,
            "verbs": True,
            "adjectives": True,
            "adverbs": True,
            "proper_nouns": include_proper_nouns,
            "numbers": False,
            "other": False
        }
    
    if existing_words is None:
        existing_words = set()
    """
    Categorize words in the text by their part of speech using spaCy.
    
    Args:
        text: The text to process
        language: The language of the text
        min_length: Minimum word length to include
        include_proper_nouns: Whether to include proper nouns
        word_types: Dictionary mapping word types to boolean values indicating inclusion
        existing_words: Set of existing words to check against (for de-duplication)
        
    Returns:
        Dictionary mapping categories to lists of words
    """
    # Load language model
    nlp = load_language_model(language)
    
    # Process the text
    doc = nlp(text)
    
    # Initialize categories
    categories = defaultdict(set)
    
    # Default word types (include all)
    if word_types is None:
        word_types = {
            "nouns": True,
            "verbs": True,
            "adjectives": True,
            "adverbs": True,
            "proper_nouns": include_proper_nouns,
            "numbers": False,
            "other": False
        }
    
    # Map category names to POS tags
    category_to_pos = {
        "nouns": ["NOUN"],
        "verbs": ["VERB"],
        "adjectives": ["ADJ"],
        "adverbs": ["ADV"],
        "proper_nouns": ["PROPN"],
        "numbers": ["NUM"],
        "other": ["ADP", "CONJ", "DET", "PRON", "INTJ", "PART", "SYM", "X"]
    }
    
    # Create a set of allowed POS tags based on selected word types
    allowed_pos = set()
    for category, include in word_types.items():
        if include and category in category_to_pos:
            allowed_pos.update(category_to_pos[category])
    
    # If proper_nouns is explicitly set in word_types, override include_proper_nouns
    if "proper_nouns" in word_types:
        include_proper_nouns = word_types["proper_nouns"]
    
    # Initialize a set for words that have already been added (to prevent duplicates)
    already_added = set()
    if existing_words is not None:
        # Add existing words to already_added (case insensitive)
        already_added.update([w.lower() for w in existing_words])
    
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
        
        # Skip words with POS tags not in the allowed set
        if token.pos_ not in allowed_pos:
            continue
        
        # Skip if this word (or variant) already exists in the already_added set
        if word.lower() in already_added:
            continue
        
        # Add word to the already_added set to prevent future duplicates
        already_added.add(word.lower())
        
        # Add word to its category
        category = POS_TO_CATEGORY.get(token.pos_, "Other")
        categories[category].add(word)
    
    # Normalize adjectives (combine gender forms)
    result_dict = {}
    
    for category, words in categories.items():
        if category == "Adjectives" and language in ["Spanish", "French", "Italian", "Portuguese"]:
            result_dict[category] = normalize_adjectives(words, language)
        else:
            result_dict[category] = sorted(list(words))
    
    return result_dict

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
