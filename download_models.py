import spacy
import nltk

# Download spaCy models
try:
    print("Downloading Spanish spaCy model...")
    spacy.cli.download("es_core_news_sm")
    print("Spanish model downloaded successfully!")
except Exception as e:
    print(f"Error downloading Spanish model: {e}")

# Download NLTK data
try:
    print("Downloading NLTK data...")
    nltk.download('punkt')
    print("NLTK data downloaded successfully!")
except Exception as e:
    print(f"Error downloading NLTK data: {e}")

print("Download complete!")