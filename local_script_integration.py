import os
import subprocess
import tempfile
import json
import time
from typing import Dict, List, Optional, Tuple, Any

def save_csv_for_local_processing(csv_path: str) -> Dict[str, Any]:
    """
    Prepare a CSV file for local processing with user scripts.
    This function just returns the metadata needed for the user's local scripts.
    
    Args:
        csv_path: Path to the CSV file with word data
        
    Returns:
        Dictionary with metadata about the CSV file for local processing
    """
    return {
        "csv_path": csv_path,
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "filename": os.path.basename(csv_path),
        "full_path": os.path.abspath(csv_path)
    }


def prepare_anki_script_config(
    csv_path: str,
    deck_name: str,
    language: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Prepare configuration settings for the user's local Anki script.
    
    Args:
        csv_path: Path to the CSV file with word data
        deck_name: Name for the Anki deck
        language: Language of the words
        config: Optional additional configuration
        
    Returns:
        Dictionary with configuration for local Anki script
    """
    # Default configuration
    script_config = {
        "input_file": os.path.abspath(csv_path),
        "deck_name": deck_name,
        "language": language,
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "output_directory": os.getcwd()  # Default to current directory
    }
    
    # Add any additional config provided by the user
    if config is not None:
        script_config.update(config)
    
    return script_config


def prepare_audio_script_config(
    word_list: List[str],
    language: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Prepare configuration settings for the user's local audio generation script.
    
    Args:
        word_list: List of words to generate audio for
        language: Language of the words
        config: Optional additional configuration
        
    Returns:
        Dictionary with configuration for local audio script
    """
    # Create a temporary file with the word list
    fd, temp_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(word_list, f, ensure_ascii=False, indent=2)
    
    # Default configuration
    script_config = {
        "word_list_file": temp_path,
        "language": language,
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "output_directory": os.getcwd()  # Default to current directory
    }
    
    # Add any additional config provided by the user
    if config is not None:
        script_config.update(config)
    
    return script_config


def save_script_configuration(config: Dict[str, Any], filename: str) -> str:
    """
    Save configuration for local scripts to a JSON file.
    
    Args:
        config: Configuration dictionary
        filename: Base filename for the config file
        
    Returns:
        Path to the saved configuration file
    """
    # Generate output path
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = f"{filename}_{timestamp}.json"
    
    # Write config to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return output_path