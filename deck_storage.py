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

def extract_words_from_apkg(deck_path: str) -> Dict[str, List[str]]:
    """
    Extract words from an Anki deck file.
    
    Args:
        deck_path: Path to the Anki deck file
        
    Returns:
        Dictionary of categorized words
    """
    import sqlite3
    import zipfile
    import tempfile
    
    print(f"DEBUG: Opening deck file: {deck_path}")
    
    # Initialize empty word dictionary
    words_dict = {
        "nouns": [],
        "verbs": [],
        "adjectives": [],
        "adverbs": [],
        "other": []
    }
    
    # Create a temporary directory to extract the apkg
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Extract the apkg (it's just a zip file)
            with zipfile.ZipFile(deck_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                print(f"DEBUG: Successfully extracted deck to {temp_dir}")
            
            # Connect to the extracted database
            db_path = os.path.join(temp_dir, 'collection.anki2')
            if not os.path.exists(db_path):
                print(f"DEBUG: Database file not found at {db_path}")
                print(f"DEBUG: Directory contents: {os.listdir(temp_dir)}")
                return words_dict
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try multiple approaches to extract words
            
            # Approach 1: Get model configurations to understand field structure
            try:
                cursor.execute("SELECT models FROM col")
                model_data = cursor.fetchone()
                if model_data and model_data[0]:
                    # Parse the model data (it's stored as JSON)
                    import json
                    try:
                        models = json.loads(model_data[0])
                        print(f"DEBUG: Successfully parsed model data, found {len(models)} models")
                        
                        # Extract field names from models
                        field_names = []
                        for model_id, model in models.items():
                            if 'flds' in model:
                                for field in model['flds']:
                                    if 'name' in field:
                                        field_name = field['name'].lower()
                                        if any(keyword in field_name for keyword in ['word', 'term', 'vocabulary', 'spanish', 'french', 'german']):
                                            field_names.append(field['ord'])  # Field order/index
                    except json.JSONDecodeError:
                        print("DEBUG: Failed to parse model data as JSON")
                        field_names = []
            except Exception as e:
                print(f"DEBUG: Error getting model data: {str(e)}")
                field_names = []
            
            # Approach 2: Get all notes (which contain the actual card content)
            try:
                cursor.execute("""
                    SELECT id, flds, sfld FROM notes 
                    WHERE flds IS NOT NULL AND length(trim(flds)) > 0
                """)
                notes = cursor.fetchall()
                print(f"DEBUG: Found {len(notes)} notes")
                
                # Process each note
                for note in notes:
                    note_id, flds, sfld = note
                    
                    # Try to extract words from the sorted field (sfld) first
                    # This is usually the front of the card and often contains the word
                    if sfld:
                        words = [sfld.strip()]
                    else:
                        # Otherwise, split all fields and try to find the word
                        fields = flds.split('\x1f')
                        
                        # If we identified likely word fields from the model, use those
                        if field_names:
                            words = [fields[i] for i in field_names if i < len(fields)]
                        else:
                            # Otherwise, use the first field as the word (common convention)
                            words = [fields[0]] if fields else []
                    
                    # Process each potential word
                    for word in words:
                        # Clean the word
                        word = re.sub('<[^<]+?>', '', word).strip()
                        
                        # Skip empty words or non-word characters
                        if not word or not any(c.isalnum() for c in word):
                            continue
                        
                        # Skip long strings that are likely sentences
                        if len(word.split()) > 3:
                            continue
                        
                        # Try to determine the category
                        category = categorize_word(word)
                        
                        # Add the word to the appropriate category if not already present
                        if word not in words_dict[category]:
                            words_dict[category].append(word)
                            
                            # Also try to get the translation from other fields
                            # This could help with categorization
                            if flds and len(fields) > 1:
                                for field in fields[1:]:
                                    # Skip empty fields or HTML-only fields
                                    clean_field = re.sub('<[^<]+?>', '', field).strip()
                                    if not clean_field:
                                        continue
                                    
                                    # If this looks like a translation, use it to help categorize
                                    if len(clean_field.split()) <= 3:
                                        # This could be a translation, use it for additional categorization
                                        pass
            except Exception as e:
                print(f"DEBUG: Error processing notes: {str(e)}")
            
            # Approach 3: Try to get cards directly
            try:
                cursor.execute("""
                    SELECT c.id, n.flds, n.sfld
                    FROM cards c
                    JOIN notes n ON c.nid = n.id
                    WHERE n.flds IS NOT NULL AND length(trim(n.flds)) > 0
                """)
                cards = cursor.fetchall()
                print(f"DEBUG: Found {len(cards)} cards")
                
                # Process cards similar to notes
                for card in cards:
                    card_id, flds, sfld = card
                    
                    # Process similar to notes approach
                    if sfld:
                        words = [sfld.strip()]
                    else:
                        fields = flds.split('\x1f')
                        words = [fields[0]] if fields else []
                    
                    for word in words:
                        # Clean and process as before
                        word = re.sub('<[^<]+?>', '', word).strip()
                        if not word or not any(c.isalnum() for c in word) or len(word.split()) > 3:
                            continue
                        
                        category = categorize_word(word)
                        if word not in words_dict[category]:
                            words_dict[category].append(word)
            except Exception as e:
                print(f"DEBUG: Error processing cards: {str(e)}")
            
            # Close the connection
            conn.close()
        
        except Exception as e:
            print(f"ERROR extracting words from deck: {str(e)}")
            return words_dict
    
    return words_dict

def categorize_word(word: str) -> str:
    """
    Categorize a word based on common patterns.
    
    Args:
        word: Word to categorize
        
    Returns:
        Category name (nouns, verbs, adjectives, adverbs, other)
    """
    # Default to "other" if we can't categorize
    category = "other"
    
    # Verb patterns in Spanish
    if any(word.endswith(suffix) for suffix in ['ar', 'er', 'ir', 'arse', 'erse', 'irse']):
        category = "verbs"
    # Adverb patterns
    elif word.endswith('mente'):
        category = "adverbs"
    # Adjective patterns
    elif any(word.endswith(suffix) for suffix in ['o', 'a', 'os', 'as', 'oso', 'osa', 'ble']):
        category = "adjectives"
    # Common noun endings
    elif any(word.endswith(suffix) for suffix in ['ción', 'sión', 'dad', 'tad', 'eza']):
        category = "nouns"
    elif word[0].isupper():
        category = "nouns"
    
    return category

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
    
    # Extract words from the deck and create companion JSON
    if deck_path.endswith('.apkg'):
        try:
            words_dict = extract_words_from_apkg(deck_path)
            new_json_path = new_path.replace('.apkg', '.json')
            with open(new_json_path, 'w', encoding='utf-8') as f:
                json.dump(words_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not extract words from deck: {str(e)}")
            # If extraction fails, copy existing JSON if available
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
    
    print(f"DEBUG: get_stored_decks called with language_filter: {language_filter}")
    print(f"DEBUG: Looking for decks in directory: {DECK_STORAGE_DIR}")
    
    decks = []
    for filename in os.listdir(DECK_STORAGE_DIR):
        filepath = os.path.join(DECK_STORAGE_DIR, filename)
        print(f"DEBUG: Checking file: {filename}, full path: {filepath}")
        
        # Include both .apkg files and files without extension (which are valid JSON files)
        if filename.endswith('.apkg') or (os.path.isfile(filepath) and '.' not in filename):
            path = filepath
            
            # For files without extension, check if they're valid JSON
            if '.' not in filename:
                print(f"DEBUG: File without extension found: {filename}")
                if not is_valid_json_file(path):
                    print(f"DEBUG: File is not a valid JSON file, skipping: {filename}")
                    continue
                else:
                    print(f"DEBUG: Valid JSON file without extension: {filename}")
            
            # Extract language from filename
            language = extract_language_from_filename(filename)
            print(f"DEBUG: Extracted language: {language} for file: {filename}")
            
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
            
            # For .apkg files, also remove the companion JSON if it exists
            if deck_path.endswith('.apkg'):
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
        
        # Handle files without extension (which are already JSON files)
        if '.' not in deck_path:
            json_path = deck_path
        else:
            json_path = deck_path.replace('.apkg', '.json')
        
        # Process the JSON file if it exists and is valid
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