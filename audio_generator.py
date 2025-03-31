import os
import tempfile
from typing import Dict, List, Optional
from gtts import gTTS

# Import Google Cloud TTS functionality
from gcloud_tts import is_gcloud_tts_available, generate_audio_gcloud

def generate_audio_for_word(word: str, language: str) -> Optional[str]:
    """
    Generate audio for a single word using either Google Cloud Text-to-Speech (if available)
    or fallback to gTTS.
    
    Args:
        word: The word to generate audio for
        language: Language code for the word
        
    Returns:
        Path to the generated audio file or None if generation failed
    """
    # Map language names to language codes
    language_map = {
        "French": {"gtts": "fr", "gcloud": "fr-FR"},
        "Spanish": {"gtts": "es", "gcloud": "es-ES"},
        "German": {"gtts": "de", "gcloud": "de-DE"},
        "Italian": {"gtts": "it", "gcloud": "it-IT"},
        "Japanese": {"gtts": "ja", "gcloud": "ja-JP"},
        "Chinese": {"gtts": "zh-CN", "gcloud": "zh-CN"},
        "Russian": {"gtts": "ru", "gcloud": "ru-RU"},
        "English": {"gtts": "en", "gcloud": "en-US"}
    }
    
    lang_info = language_map.get(language, {"gtts": "en", "gcloud": "en-US"})
    
    # First try using Google Cloud TTS if available
    if is_gcloud_tts_available():
        try:
            gcloud_audio_path = generate_audio_gcloud(word, lang_info["gcloud"])
            if gcloud_audio_path:
                return gcloud_audio_path
        except Exception as e:
            print(f"Error with Google Cloud TTS for '{word}': {str(e)}. Falling back to gTTS.")
    
    # Fallback to gTTS if Google Cloud TTS is not available or fails
    try:
        # Create a temporary file for the audio
        fd, temp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        
        # Generate the audio using gTTS
        tts = gTTS(text=word, lang=lang_info["gtts"], slow=False)
        tts.save(temp_path)
        
        return temp_path
    
    except Exception as e:
        print(f"Error generating audio for '{word}': {str(e)}")
        return None

def generate_audio_for_words(words_dict: Dict[str, List[str]], language: str) -> Dict[str, str]:
    """
    Generate audio for multiple words.
    
    Args:
        words_dict: Dictionary of categorized words
        language: Language of the words
        
    Returns:
        Dictionary mapping words to audio file paths
    """
    audio_files = {}
    
    # Process all words in all categories with rate limit handling
    import time
    total_words = sum(len(words) for words in words_dict.values())
    processed_count = 0
    
    for category, words in words_dict.items():
        # Process only a subset of words per category to avoid rate limiting (max 50 words)
        words_to_process = words[:min(50, len(words))]
        for word in words_to_process:
            # Generate audio for the word
            audio_path = generate_audio_for_word(word, language)
            
            # Store the audio path if generation was successful
            if audio_path:
                audio_files[word] = audio_path
            
            # Add a small delay between requests to avoid rate limiting
            processed_count += 1
            if processed_count % 5 == 0:  # Add delay every 5 words
                time.sleep(1)  # Sleep for 1 second
            
            # Show progress
            if processed_count % 10 == 0:
                print(f"Generated audio for {processed_count}/{total_words} words...")
    
    return audio_files

def generate_audio_batch(words: List[str], language: str) -> Dict[str, str]:
    """
    Generate audio for a batch of words.
    
    Args:
        words: List of words to generate audio for
        language: Language of the words
        
    Returns:
        Dictionary mapping words to audio file paths
    """
    audio_files = {}
    import time
    
    # Limit to max 50 words per batch
    words_to_process = words[:min(50, len(words))]
    total_words = len(words_to_process)
    
    for i, word in enumerate(words_to_process):
        audio_path = generate_audio_for_word(word, language)
        if audio_path:
            audio_files[word] = audio_path
        
        # Add a small delay between requests to avoid rate limiting
        if i % 5 == 0 and i > 0:  # Add delay every 5 words
            time.sleep(1)  # Sleep for 1 second
        
        # Show progress
        if i % 10 == 0 and i > 0:
            print(f"Generated audio for {i}/{total_words} words in batch...")
    
    return audio_files
