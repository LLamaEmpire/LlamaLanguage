
import os
import requests
from typing import Optional

def translate_text(text: str, source_lang: str = "es", target_lang: str = "en") -> Optional[str]:
    """
    Translate text using Sonnet API.
    
    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        
    Returns:
        Translated text or None if translation fails
    """
    api_key = os.environ.get("SONNET_API_KEY")
    if not api_key:
        print("Warning: SONNET_API_KEY not found in environment variables")
        return None
        
    try:
        response = requests.post(
            "https://api.sonnet.sh/v1/translate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
        )
        response.raise_for_status()
        return response.json()["translation"]
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return None
