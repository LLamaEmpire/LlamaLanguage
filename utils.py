import os
import tempfile
import glob
import json
from typing import List, Dict, Any, Optional, Set
from deck_storage import get_stored_decks, get_words_from_all_stored_decks

def get_existing_decks() -> List[str]:
    """
    Get a list of existing Spanish Anki deck paths.
    
    Returns:
        List of paths to existing Spanish Anki decks
    """
    # Get Spanish decks from the storage system first
    stored_decks = get_stored_decks(language_filter="Spanish")
    stored_deck_paths = [deck_info['path'] for deck_info in stored_decks]
    
    # Look for Spanish .apkg files in the current directory that aren't in stored_decks
    current_decks = []
    for deck in glob.glob("*.apkg"):
        # Check if the deck is likely a Spanish deck
        if "spanish" in deck.lower() or "espanol" in deck.lower() or "español" in deck.lower():
            current_decks.append(deck)
    
    # Combine lists (prioritizing stored decks)
    all_decks = stored_deck_paths.copy()
    for deck in current_decks:
        # Only add if not already in the list
        if deck not in all_decks:
            all_decks.append(deck)
    
    # If no decks are found, create a sample Spanish deck for demonstration
    if not all_decks:
        # Create a dummy deck for testing purposes
        dummy_deck = "example_spanish_deck.apkg"
        # Create a companion JSON file with some sample Spanish words
        dummy_json = "example_spanish_deck.json"
        
        # Only create these files if they don't exist
        if not os.path.exists(dummy_json):
            sample_words = {
                "Nouns": ["casa", "coche", "libro", "árbol", "amigo/amiga"],
                "Verbs": ["correr", "caminar", "hablar", "comer", "dormir"],
                "Adjectives": ["grande/pequeño", "feliz/triste", "bueno/buena"]
            }
            with open(dummy_json, 'w') as f:
                json.dump(sample_words, f, indent=2)
        
        # Return the dummy deck
        return [dummy_deck]
    
    return all_decks

def get_existing_words() -> Set[str]:
    """
    Get a set of Spanish words from all existing Anki decks.
    
    Returns:
        Set of Spanish words that exist in decks
    """
    # Get words from all stored Spanish decks
    all_words = get_words_from_all_stored_decks(language="Spanish")
    
    # Also check local Spanish decks not in storage
    for deck in glob.glob("*.apkg"):
        # Only process Spanish decks
        if not ("spanish" in deck.lower() or "espanol" in deck.lower() or "español" in deck.lower()):
            continue
            
        json_file = deck.replace('.apkg', '.json')
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    deck_data = json.load(f)
                    for category, words in deck_data.items():
                        # Process both formats: simple words and normalized adjectives (word/wordFeminine)
                        processed_words = []
                        for word in words:
                            if '/' in word:
                                # Split and add both forms
                                parts = word.split('/')
                                processed_words.extend(parts)
                            else:
                                processed_words.append(word)
                                
                        all_words.update([w.lower() for w in processed_words])
            except Exception as e:
                print(f"Error reading deck data from {json_file}: {str(e)}")
    
    return all_words

def save_temp_file(uploaded_file) -> str:
    """
    Save an uploaded file to a temporary location.
    
    Args:
        uploaded_file: The uploaded file object from Streamlit
        
    Returns:
        Path to the saved temporary file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        
        # Handle file data in chunks to avoid memory issues with large files
        # Set a sensible chunk size (5MB)
        CHUNK_SIZE = 5 * 1024 * 1024  
        
        # Get and process file content in chunks
        file_content = uploaded_file.getvalue()
        for i in range(0, len(file_content), CHUNK_SIZE):
            chunk = file_content[i:i + CHUNK_SIZE]
            temp_file.write(chunk)
            
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise Exception(f"Failed to save uploaded file: {str(e)}")

def cleanup_temp_files(file_paths: List[str]) -> None:
    """
    Clean up temporary files.
    
    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing temporary file {file_path}: {str(e)}")

def parse_language_code(language: str) -> str:
    """
    Convert a language name to a standard language code.
    
    Args:
        language: Language name
        
    Returns:
        ISO language code
    """
    language_map = {
        "French": "fr",
        "Spanish": "es",
        "German": "de",
        "Italian": "it",
        "Japanese": "ja",
        "Chinese": "zh",
        "Russian": "ru",
        "English": "en"
    }
    
    return language_map.get(language, "en")

def get_language_from_code(code: str) -> str:
    """
    Convert a language code to a language name.
    
    Args:
        code: ISO language code
        
    Returns:
        Language name
    """
    code_map = {
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "zh": "Chinese",
        "ru": "Russian",
        "en": "English"
    }
    
    return code_map.get(code, "Unknown")
