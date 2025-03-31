import os
import shutil
import json
import time
import re
from typing import List, Dict, Any, Optional, Set, Tuple

# Directory for storing decks permanently
DECK_STORAGE_DIR = "stored_decks"

def ensure_storage_dir():
    """Ensure the deck storage directory exists."""
    if not os.path.exists(DECK_STORAGE_DIR):
        os.makedirs(DECK_STORAGE_DIR)

def save_deck_to_storage(deck_path: str, deck_name: Optional[str] = None, language: str = "Spanish") -> str:
    """
    Save an Anki deck to permanent storage.
    
    Args:
        deck_path: Path to the Anki deck file
        deck_name: Optional custom name for the deck
        language: Language of the deck (default: Spanish)
        
    Returns:
        Path to the stored deck
    """
    ensure_storage_dir()
    
    # If no custom name provided, use the original filename
    if deck_name is None:
        deck_name = os.path.basename(deck_path)
    
    # Create a unique filename to avoid overwrites
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(deck_name)
    
    # Make sure the language is included in the filename
    if language.lower() not in base_name.lower():
        base_name = f"{base_name}_{language}"
    
    new_name = f"{base_name}_{timestamp}{ext}"
    
    # New path in storage dir
    new_path = os.path.join(DECK_STORAGE_DIR, new_name)
    
    # Copy the deck file
    shutil.copy2(deck_path, new_path)
    
    # If there's a companion JSON file, copy it too
    json_path = deck_path.replace('.apkg', '.json')
    if os.path.exists(json_path):
        new_json_path = new_path.replace('.apkg', '.json')
        shutil.copy2(json_path, new_json_path)
    
    return new_path

def extract_language_from_filename(filename: str) -> str:
    """
    Extract language information from the filename.
    
    Args:
        filename: Name of the file to analyze
        
    Returns:
        Detected language or "Unknown"
    """
    # Common language patterns in filenames
    language_patterns = {
        "Spanish": ["spanish", "español", "espanol", "sp"],
        "French": ["french", "français", "francais", "fr"],
        "German": ["german", "deutsch", "de"],
        "Italian": ["italian", "italiano", "it"],
        "Japanese": ["japanese", "日本語", "jp"],
        "Chinese": ["chinese", "中文", "zh"],
        "Russian": ["russian", "русский", "ru"]
    }
    
    filename_lower = filename.lower()
    
    for language, patterns in language_patterns.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return language
    
    # Default to Spanish for this application
    return "Spanish"

def extract_display_name(filename: str) -> str:
    """
    Create a user-friendly display name from the filename.
    
    Args:
        filename: Raw filename to process
        
    Returns:
        Cleaned up display name
    """
    # Remove the extension
    name, _ = os.path.splitext(filename)
    
    # Remove timestamp patterns (YYYYMMDD_HHMMSS)
    name = re.sub(r'_\d{8}_\d{6}', '', name)
    
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    
    # Clean up any double spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Capitalize words
    name = ' '.join(word.capitalize() for word in name.split())
    
    return name

def get_stored_decks(language_filter: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get a list of all stored Anki decks.
    
    Args:
        language_filter: Optional language to filter decks by
        
    Returns:
        List of dictionaries containing deck info
    """
    ensure_storage_dir()
    
    decks = []
    for filename in os.listdir(DECK_STORAGE_DIR):
        if filename.endswith('.apkg'):
            path = os.path.join(DECK_STORAGE_DIR, filename)
            
            # Extract language from filename
            language = extract_language_from_filename(filename)
            
            # Apply language filter if specified
            if language_filter and language.lower() != language_filter.lower():
                continue
            
            # Extract timestamp from filename for sorting
            timestamp_match = re.search(r'_(\d{8})_(\d{6})', filename)
            timestamp = f"{timestamp_match.group(1)}_{timestamp_match.group(2)}" if timestamp_match else '00000000_000000'
            
            # Create a friendly display name
            display_name = extract_display_name(filename)
            
            decks.append({
                'name': display_name,
                'original_filename': filename,
                'path': path,
                'timestamp': timestamp,
                'language': language
            })
    
    # Sort by timestamp (newest first)
    decks.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return decks

def delete_stored_deck(deck_path: str) -> bool:
    """
    Delete a stored Anki deck.
    
    Args:
        deck_path: Path to the deck to delete
        
    Returns:
        Success status
    """
    try:
        if os.path.exists(deck_path):
            os.remove(deck_path)
            
            # Also remove the companion JSON if it exists
            json_path = deck_path.replace('.apkg', '.json')
            if os.path.exists(json_path):
                os.remove(json_path)
            
            return True
        return False
    except Exception as e:
        print(f"Error deleting deck: {str(e)}")
        return False

def is_valid_json_file(file_path: str) -> bool:
    """
    Check if a file is a valid JSON file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is a valid JSON file, False otherwise
    """
    try:
        # Try to read the first few bytes to check if it's a binary file
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # Check for common binary file signatures
            if header.startswith(b'PK') or header.startswith(b'\x1F\x8B'):
                return False
        
        # Try to parse as JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except UnicodeDecodeError:
        # Try with latin-1 encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                json.load(f)
            return True
        except:
            return False
    except:
        return False

def get_words_from_all_stored_decks(language: str = "Spanish") -> Set[str]:
    """
    Get all words from all stored decks of a specific language.
    
    Args:
        language: Language filter for the decks
        
    Returns:
        Set of all words
    """
    all_words = set()
    
    for deck_info in get_stored_decks(language_filter=language):
        deck_path = deck_info['path']
        json_path = deck_path.replace('.apkg', '.json')
        
        if os.path.exists(json_path) and is_valid_json_file(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    deck_words = json.load(f)
                    for category, words in deck_words.items():
                        # Handle both simple lists and normalized adjective formats (word/wordFeminine)
                        processed_words = []
                        for word in words:
                            if '/' in word:
                                # Split and add both forms
                                parts = word.split('/')
                                processed_words.extend(parts)
                            else:
                                processed_words.append(word)
                        
                        all_words.update([w.lower() for w in processed_words])
            except UnicodeDecodeError:
                # Try with different encodings if utf-8 fails
                try:
                    with open(json_path, 'r', encoding='latin-1') as f:
                        deck_words = json.load(f)
                        for category, words in deck_words.items():
                            # Handle both simple lists and normalized adjective formats (word/wordFeminine)
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
                    print(f"Error reading words with latin-1 encoding from {json_path}: {str(e)}")
            except Exception as e:
                print(f"Error reading words from {json_path}: {str(e)}")
    
    return all_words