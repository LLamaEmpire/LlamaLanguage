import os
import shutil
import json
import time
from typing import List, Dict, Any, Optional, Set, Tuple

# Directory for storing decks permanently
DECK_STORAGE_DIR = "stored_decks"

def ensure_storage_dir():
    """Ensure the deck storage directory exists."""
    if not os.path.exists(DECK_STORAGE_DIR):
        os.makedirs(DECK_STORAGE_DIR)

def save_deck_to_storage(deck_path: str, deck_name: Optional[str] = None) -> str:
    """
    Save an Anki deck to permanent storage.
    
    Args:
        deck_path: Path to the Anki deck file
        deck_name: Optional custom name for the deck
        
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

def get_stored_decks() -> List[Dict[str, str]]:
    """
    Get a list of all stored Anki decks.
    
    Returns:
        List of dictionaries containing deck info
    """
    ensure_storage_dir()
    
    decks = []
    for filename in os.listdir(DECK_STORAGE_DIR):
        if filename.endswith('.apkg'):
            path = os.path.join(DECK_STORAGE_DIR, filename)
            # Extract timestamp from filename for sorting
            parts = filename.split('_')
            timestamp = None
            for part in parts:
                if len(part) == 8 and part.isdigit():  # Format YYYYMMDD
                    next_idx = parts.index(part) + 1
                    if next_idx < len(parts) and len(parts[next_idx]) == 6 and parts[next_idx].isdigit():  # Format HHMMSS
                        timestamp = f"{part}_{parts[next_idx]}"
                        break
            
            decks.append({
                'name': filename,
                'path': path,
                'timestamp': timestamp or '00000000_000000'  # Default for sorting
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

def get_words_from_all_stored_decks() -> Set[str]:
    """
    Get all words from all stored decks.
    
    Returns:
        Set of all words
    """
    all_words = set()
    
    for deck_info in get_stored_decks():
        deck_path = deck_info['path']
        json_path = deck_path.replace('.apkg', '.json')
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    deck_words = json.load(f)
                    for category, words in deck_words.items():
                        all_words.update([w.lower() for w in words])
            except Exception as e:
                print(f"Error reading words from {json_path}: {str(e)}")
    
    return all_words