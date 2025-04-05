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

def sanitize_filename(text: str) -> str:
    """
    Sanitize text to be used as a filename.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for use as a filename
    """
    # Replace characters that are not allowed in filenames
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    result = text
    for char in invalid_chars:
        result = result.replace(char, '_')
    
    # Limit the length to avoid overly long filenames
    max_length = 100
    if len(result) > max_length:
        result = result[:max_length]
        
    return result

def generate_audio_gcloud(word: str, language: str = "es-ES", output_dir: Optional[str] = None) -> Optional[str]:
    """
    Generate audio for a word using Google Cloud Text-to-Speech.
    
    Args:
        word: The word to generate audio for
        language: Language code for the word (default: es-ES for Spanish)
        output_dir: Optional directory to save the audio file to. If None, a temporary file is used.
        
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
        
        # Create a file to store the audio
        if output_dir:
            # Create the output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create a filename based on the word and language
            safe_word = sanitize_filename(word)
            audio_filename = f"{safe_word}_{language.replace('-', '_')}.mp3"
            audio_file_path = os.path.join(output_dir, audio_filename)
            
            # Write the audio content to the file
            with open(audio_file_path, "wb") as audio_file:
                audio_file.write(response.audio_content)
        else:
            # Use a temporary file if no output directory is specified
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(response.audio_content)
                audio_file_path = temp_file.name
        
        return audio_file_path
    
    except Exception as e:
        print(f"Error generating audio with Google Cloud TTS: {e}")
        return None

def generate_audio_batch_gcloud(words: List[str], language: str = "es-ES", output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Generate audio for a batch of words using Google Cloud TTS.
    
    Args:
        words: List of words to generate audio for
        language: Language code for the words (default: es-ES for Spanish)
        output_dir: Optional directory to save the audio files to
        
    Returns:
        Dictionary mapping words to audio file paths
    """
    audio_files = {}
    for word in words:
        try:
            audio_path = generate_audio_gcloud(word, language, output_dir)
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