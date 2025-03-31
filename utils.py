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
    # Get Spanish decks from the storage system only
    stored_decks = get_stored_decks(language_filter="Spanish")
    stored_deck_paths = [deck_info['path'] for deck_info in stored_decks]
    
    # Return stored decks only - we no longer look for local decks
    return stored_deck_paths

def get_existing_words() -> Set[str]:
    """
    Get a set of Spanish words from all existing Anki decks.
    
    Returns:
        Set of Spanish words that exist in decks
    """
    # Get words only from stored Spanish decks
    all_words = get_words_from_all_stored_decks(language="Spanish")
    
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
