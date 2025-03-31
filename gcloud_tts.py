import os
import tempfile
from google.cloud import texttospeech
from typing import Optional, List, Dict

def init_google_cloud_tts():
    """
    Initialize Google Cloud Text-to-Speech client.
    Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set.
    
    Returns:
        Google Cloud TTS client or None if credentials not available
    """
    try:
        # Check if credentials are available
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return None
            
        # Create the client
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        print(f"Error initializing Google Cloud TTS: {e}")
        return None

def generate_audio_gcloud(word: str, language: str = "es-ES") -> Optional[str]:
    """
    Generate audio for a word using Google Cloud Text-to-Speech.
    
    Args:
        word: The word to generate audio for
        language: Language code for the word (default: es-ES for Spanish)
        
    Returns:
        Path to the generated audio file or None if generation failed
    """
    # Initialize client
    client = init_google_cloud_tts()
    
    # If client initialization failed, return None
    if client is None:
        print("Google Cloud TTS client not initialized. Check credentials.")
        return None
    
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=word)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        # Select the type of audio file to return
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(response.audio_content)
            audio_file_path = temp_file.name
        
        return audio_file_path
    
    except Exception as e:
        print(f"Error generating audio with Google Cloud TTS: {e}")
        return None

def generate_audio_batch_gcloud(words: List[str], language: str = "es-ES") -> Dict[str, str]:
    """
    Generate audio for a batch of words using Google Cloud TTS.
    
    Args:
        words: List of words to generate audio for
        language: Language code for the words (default: es-ES for Spanish)
        
    Returns:
        Dictionary mapping words to audio file paths
    """
    audio_files = {}
    for word in words:
        try:
            audio_path = generate_audio_gcloud(word, language)
            if audio_path:
                audio_files[word] = audio_path
        except Exception as e:
            print(f"Error generating audio for '{word}': {e}")
    
    return audio_files

def is_gcloud_tts_available() -> bool:
    """
    Check if Google Cloud TTS is available (credentials are set).
    
    Returns:
        True if Google Cloud TTS is available, False otherwise
    """
    return init_google_cloud_tts() is not None