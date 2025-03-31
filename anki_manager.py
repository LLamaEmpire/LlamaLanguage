import os
import json
import genanki
import random
import time
from typing import Dict, List, Set, Tuple, Any, Optional
from deck_storage import save_deck_to_storage, get_words_from_all_stored_decks
from utils import get_existing_words

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
        existing_decks: List of paths to existing Anki decks (can include format "name (path)")
        
    Returns:
        Tuple of (new_words_dict, existing_words_dict)
    """
    # Initialize new_words_dict and existing_words_dict with same structure as new_words
    new_words_dict = {category: [] for category in new_words}
    existing_words_dict = {category: [] for category in new_words}
    
    # First get words from stored decks
    all_existing_words = get_words_from_all_stored_decks()
    
    # Then add words from specified existing decks
    for deck_path in existing_decks:
        # Handle the case where the deck path is in the format "name (path)"
        if " (" in deck_path and deck_path.endswith(")"):
            # Extract the actual path from the format "name (path)"
            deck_path = deck_path.split(" (", 1)[1].rstrip(")")
        
        try:
            deck_words = get_existing_words_from_deck(deck_path)
            for category, words in deck_words.items():
                all_existing_words.update(words)
        except Exception as e:
            print(f"Error processing deck {deck_path}: {str(e)}")
            # Continue with other decks even if one fails
            continue
    
    # Convert all existing words to lowercase for case-insensitive comparison
    all_existing_words_lower = {word.lower() for word in all_existing_words}
    
    # Keep track of words we've seen in this processing session to avoid duplicates
    already_processed = set()
    
    # Compare and categorize words
    for category, words in new_words.items():
        for word in words:
            # Skip if we've already processed this word in another category
            word_lower = word.lower()
            if word_lower in already_processed:
                continue
            
            # Mark as processed
            already_processed.add(word_lower)
            
            # Check if word exists in existing decks
            if word_lower in all_existing_words_lower:
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
    language: str,
    store_deck: bool = True
) -> str:
    """
    Create an Anki deck from the words.
    
    Args:
        words_dict: Dictionary of categorized words
        audio_files: Dictionary mapping words to audio file paths
        deck_name: Name for the new deck
        language: Language of the words
        store_deck: Whether to save this deck to permanent storage
        
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
    
    # Store the deck in permanent storage if requested
    if store_deck:
        stored_path = save_deck_to_storage(output_path, deck_name)
        print(f"Deck saved to permanent storage: {stored_path}")
    
    return output_path
