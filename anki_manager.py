import os
import json
import genanki
import random
import time
from typing import Dict, List, Set, Tuple, Any, Optional

def get_existing_words_from_deck(deck_path: str) -> Dict[str, List[str]]:
    """
    Extract words from an existing Anki deck.
    
    Args:
        deck_path: Path to the Anki deck (.apkg file)
        
    Returns:
        Dictionary of categorized words from the deck
    """
    # This is a simplified version - in a real implementation, you would use
    # an Anki SQLite parser to extract words from the deck
    
    # For demonstration, let's assume we have a companion JSON file with the words
    json_path = deck_path.replace('.apkg', '.json')
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    # If no companion file, return empty dict
    return {}

def compare_with_existing_decks(
    new_words: Dict[str, List[str]], 
    existing_decks: List[str]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Compare extracted words with existing decks to identify new words.
    
    Args:
        new_words: Dictionary of categorized words extracted from the PDF
        existing_decks: List of paths to existing Anki decks
        
    Returns:
        Tuple of (new_words_dict, existing_words_dict)
    """
    # Initialize new_words_dict and existing_words_dict with same structure as new_words
    new_words_dict = {category: [] for category in new_words}
    existing_words_dict = {category: [] for category in new_words}
    
    # Get all words from existing decks
    all_existing_words = set()
    for deck_path in existing_decks:
        deck_words = get_existing_words_from_deck(deck_path)
        for category, words in deck_words.items():
            all_existing_words.update(words)
    
    # Compare and categorize words
    for category, words in new_words.items():
        for word in words:
            if word in all_existing_words:
                existing_words_dict[category].append(word)
            else:
                new_words_dict[category].append(word)
    
    return new_words_dict, existing_words_dict

def generate_anki_model(language: str) -> genanki.Model:
    """
    Generate an Anki model for the cards.
    
    Args:
        language: The language of the cards
        
    Returns:
        Anki model object
    """
    model_id = random.randrange(1 << 30, 1 << 31)
    
    # Create a model with fields for word, translation, part of speech, and audio
    model = genanki.Model(
        model_id,
        f'{language} Vocabulary',
        fields=[
            {'name': 'Word'},
            {'name': 'Translation'},
            {'name': 'Part of Speech'},
            {'name': 'Example'},
            {'name': 'Audio'}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Word}}<br>{{Part of Speech}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Translation}}<br>{{Example}}<br>{{Audio}}',
            },
        ],
        css='''
        .card {
            font-family: Arial, sans-serif;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
        }
        '''
    )
    
    return model

def create_anki_deck(
    words_dict: Dict[str, List[str]], 
    audio_files: Dict[str, str], 
    deck_name: str, 
    language: str
) -> str:
    """
    Create an Anki deck from the words.
    
    Args:
        words_dict: Dictionary of categorized words
        audio_files: Dictionary mapping words to audio file paths
        deck_name: Name for the new deck
        language: Language of the words
        
    Returns:
        Path to the created Anki deck file
    """
    # Create a unique deck ID
    deck_id = random.randrange(1 << 30, 1 << 31)
    
    # Create the deck
    deck = genanki.Deck(deck_id, deck_name)
    
    # Create the model for cards
    model = generate_anki_model(language)
    
    # Add media files
    media_files = []
    
    # Process each category and add cards
    for category, words in words_dict.items():
        for word in words:
            # Create note fields
            fields = [
                word,                               # Word
                f"[{language} translation]",        # Translation placeholder
                category,                           # Part of Speech
                f"[Example sentence with {word}]",  # Example placeholder
                ""                                  # Audio placeholder
            ]
            
            # Add audio if available
            if word in audio_files:
                audio_path = audio_files[word]
                fields[4] = f"[sound:{os.path.basename(audio_path)}]"
                media_files.append(audio_path)
            
            # Create and add the note
            note = genanki.Note(model=model, fields=fields)
            deck.add_note(note)
    
    # Create a package from the deck
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = f"{deck_name}_{timestamp}.apkg"
    
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)
    
    # Create a companion JSON file with the words (for future reference)
    json_path = output_path.replace('.apkg', '.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(words_dict, f, ensure_ascii=False, indent=2)
    
    return output_path
