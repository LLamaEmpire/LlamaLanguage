import os
import tempfile
from typing import Dict, List, Optional
from gtts import gTTS

def generate_audio_for_word(word: str, language: str) -> Optional[str]:
    """
    Generate audio for a single word using Google Text-to-Speech.
    
    Args:
        word: The word to generate audio for
        language: Language code for the word
        
    Returns:
        Path to the generated audio file or None if generation failed
    """
    # Map language names to gTTS language codes
    language_map = {
        "French": "fr",
        "Spanish": "es",
        "German": "de",
        "Italian": "it",
        "Japanese": "ja",
        "Chinese": "zh-CN",
        "Russian": "ru",
        "English": "en"
    }
    
    lang_code = language_map.get(language, "en")
    
    try:
        # Create a temporary file for the audio
        fd, temp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        
        # Generate the audio using gTTS
        tts = gTTS(text=word, lang=lang_code, slow=False)
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
    
    # Process all words in all categories
    for category, words in words_dict.items():
        for word in words:
            # Generate audio for the word
            audio_path = generate_audio_for_word(word, language)
            
            # Store the audio path if generation was successful
            if audio_path:
                audio_files[word] = audio_path
    
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
    
    for word in words:
        audio_path = generate_audio_for_word(word, language)
        if audio_path:
            audio_files[word] = audio_path
    
    return audio_files
