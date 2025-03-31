import os
import tempfile
import glob
from typing import List, Dict, Any, Optional

def get_existing_decks() -> List[str]:
    """
    Get a list of existing Anki deck paths.
    
    Returns:
        List of paths to existing Anki decks
    """
    # Look for .apkg files in the current directory
    deck_files = glob.glob("*.apkg")
    
    # If no decks are found, return an empty list
    if not deck_files:
        # Create a dummy deck for testing purposes
        dummy_deck = "example_deck.apkg"
        # Create a companion JSON file with some sample words
        dummy_json = "example_deck.json"
        
        # Only create these files if they don't exist
        if not os.path.exists(dummy_json):
            import json
            sample_words = {
                "Nouns": ["house", "car", "book", "tree", "friend"],
                "Verbs": ["run", "walk", "talk", "eat", "sleep"],
                "Adjectives": ["big", "small", "happy", "sad", "good"]
            }
            with open(dummy_json, 'w') as f:
                json.dump(sample_words, f, indent=2)
        
        # Return the dummy deck
        return [dummy_deck]
    
    return deck_files

def save_temp_file(uploaded_file) -> str:
    """
    Save an uploaded file to a temporary location.
    
    Args:
        uploaded_file: The uploaded file object from Streamlit
        
    Returns:
        Path to the saved temporary file
    """
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(uploaded_file.getvalue())
    temp_file.close()
    
    return temp_file.name

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
