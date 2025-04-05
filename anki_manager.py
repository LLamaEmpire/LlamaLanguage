import os
import json
import genanki
import random
import time
from typing import Dict, List, Set, Tuple, Any, Optional
from deck_storage import save_deck_to_storage, get_words_from_all_stored_decks, is_valid_json_file, extract_words_from_apkg
from utils import get_existing_words

def get_existing_words_from_deck(deck_path: str) -> Dict[str, List[str]]:
    """
    Extract words from an existing Anki deck.
    
    Args:
        deck_path: Path to the Anki deck (.apkg file) or JSON file
        
    Returns:
        Dictionary of categorized words from the deck
    """
    from deck_storage import is_valid_json_file, extract_words_from_apkg
    
    print(f"DEBUG: get_existing_words_from_deck called with path: {deck_path}")
    
    # For files without extension (which are already JSON)
    if '.' not in deck_path:
        json_path = deck_path
        print(f"DEBUG: No extension found, using as JSON path: {json_path}")
    else:
        # For .apkg files, check the companion JSON file
        json_path = deck_path.replace('.apkg', '.json')
        print(f"DEBUG: Extension found, converted to JSON path: {json_path}")
    
    # Check if the JSON file exists and is a valid JSON file
    file_exists = os.path.exists(json_path)
    is_valid = is_valid_json_file(json_path) if file_exists else False
    print(f"DEBUG: JSON file exists: {file_exists}, is valid JSON: {is_valid}")
    
    # First try to load from the JSON companion file
    if file_exists and is_valid:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                words_dict = json.load(f)
                print(f"DEBUG: Successfully loaded words from JSON file: {len(words_dict)} categories")
                return words_dict
        except UnicodeDecodeError:
            # Try with different encodings if utf-8 fails
            try:
                with open(json_path, 'r', encoding='latin-1') as f:
                    words_dict = json.load(f)
                    print(f"DEBUG: Successfully loaded words from JSON file with latin-1 encoding: {len(words_dict)} categories")
                    return words_dict
            except Exception as e:
                print(f"Error reading words from {json_path} with latin-1 encoding: {str(e)}")
                # Continue to try direct extraction
        except Exception as e:
            print(f"Error reading words from {json_path}: {str(e)}")
            # Continue to try direct extraction
    
    # If JSON file doesn't exist or is invalid, try direct extraction from .apkg
    if deck_path.endswith('.apkg') and os.path.exists(deck_path):
        try:
            print(f"DEBUG: Attempting direct extraction from .apkg file: {deck_path}")
            words_dict = extract_words_from_apkg(deck_path)
            
            # Save the extracted words to a JSON file for future use
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(words_dict, f, ensure_ascii=False, indent=2)
                print(f"DEBUG: Saved extracted words to JSON file: {json_path}")
            except Exception as e:
                print(f"Warning: Could not save extracted words to JSON: {str(e)}")
            
            return words_dict
        except Exception as e:
            print(f"Error extracting words directly from {deck_path}: {str(e)}")
    
    # If all extraction methods fail, return empty dictionary with the expected structure
    print(f"DEBUG: All extraction methods failed, returning empty dictionary")
    return {
        "nouns": [],
        "verbs": [],
        "adjectives": [],
        "adverbs": [],
        "other": []
    }

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
                # Process words considering both simple words and normalized adjective format (word/wordFeminine)
                for word in words:
                    if '/' in word:
                        # Split and add both forms
                        parts = word.split('/')
                        all_existing_words.update(parts)
                    else:
                        all_existing_words.add(word)
        except Exception as e:
            print(f"Error processing deck {deck_path}: {str(e)}")
            # Continue with other decks even if one fails
            continue
    
    # Convert all existing words to lowercase for case-insensitive comparison
    all_existing_words_lower = {word.lower() for word in all_existing_words}
    
    # Keep track of words we've seen in this processing session to avoid duplicates across categories
    already_processed = set()
    
    # Compare and categorize words
    for category, words in new_words.items():
        for word in words:
            # Parse the word, considering normalized adjective format
            if '/' in word:
                # Check both parts of combined adjectives
                word_parts = word.split('/')
                # If any part exists in existing words, consider the whole word as existing
                is_existing = any(part.lower() in all_existing_words_lower for part in word_parts)
            else:
                word_lower = word.lower()
                # Check if word already exists in any deck
                is_existing = word_lower in all_existing_words_lower
                
                # Skip duplicates across categories, but still keep track of all words
                if word_lower in already_processed:
                    # Even if we skip adding it to dictionaries, we want to continue with other words
                    continue
            
            # Mark as processed to prevent duplicates across categories
            already_processed.add(word.lower())
            
            # Categorize the word
            if is_existing:
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
    store_deck: bool = True,
    existing_deck_path: Optional[str] = None,
    merge_existing: bool = False
) -> str:
    """
    Create an Anki deck from the words.
    
    Args:
        words_dict: Dictionary of categorized words
        audio_files: Dictionary mapping words to audio file paths
        deck_name: Name for the new deck
        language: Language of the words
        store_deck: Whether to save this deck to permanent storage
        existing_deck_path: Path to an existing deck to merge with
        merge_existing: Whether to merge with an existing deck
        
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
    
    # Check if we're merging with an existing deck
    merged_words_dict = {category: [] for category in words_dict.keys()}
    
    if merge_existing and existing_deck_path:
        # Load words from the existing deck
        existing_words = get_existing_words_from_deck(existing_deck_path)
        
        # Merge with the new words
        for category in words_dict.keys():
            # Add existing words from this category
            if category in existing_words:
                merged_words_dict[category].extend(existing_words[category])
            
            # Add new words from this category
            merged_words_dict[category].extend(words_dict[category])
            
            # Remove duplicates while preserving order
            seen = set()
            merged_words_dict[category] = [
                word for word in merged_words_dict[category] 
                if not (word.lower() in seen or seen.add(word.lower()))
            ]
    else:
        # Just use the provided words
        merged_words_dict = words_dict
    
    # Process each category and add cards
    for category, words in merged_words_dict.items():
        for word in words:
            # Create note fields
            # Get translation
            from sonnet_translator import translate_text
            translation = translate_text(word, source_lang="es", target_lang="en") or f"[{language} translation]"
            
            fields = [
                word,                               # Word
                translation,                        # Translation
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
        json.dump(merged_words_dict, f, ensure_ascii=False, indent=2)
    
    # Store the deck in permanent storage if requested
    if store_deck:
        stored_path = save_deck_to_storage(output_path, deck_name)
        print(f"Deck saved to permanent storage: {stored_path}")
    
    return output_path
