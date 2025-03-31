import csv
import os
import time
from typing import Dict, List, Optional, Tuple

def export_words_to_csv(
    words_dict: Dict[str, List[str]], 
    word_sentences: Dict[str, List[str]], 
    pdf_name: str, 
    language: str
) -> str:
    """
    Export words to a CSV file with the required structure:
    
    Number | Spanish Word | Spanish Sentence | English Word | English Sentence
    
    Args:
        words_dict: Dictionary of categorized words
        word_sentences: Dictionary mapping words to example sentences
        pdf_name: Name of the PDF (used in the output filename)
        language: Language of the words
        
    Returns:
        Path to the CSV file
    """
    # Create a timestamp for the filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Generate a clean filename base from the PDF name
    # Remove extension and any special characters
    base_name = os.path.splitext(os.path.basename(pdf_name))[0]
    base_name = ''.join(c if c.isalnum() else '_' for c in base_name)
    
    # Generate the output filename
    output_path = f"{base_name}_{language}_words_{timestamp}.csv"
    
    # Flatten the words dictionary to get all words
    all_words = []
    for category, words in words_dict.items():
        for word in words:
            all_words.append((word, category))
    
    # Sort words alphabetically
    all_words.sort(key=lambda x: x[0])
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header row
        writer.writerow(['Number', f'{language} Word', f'{language} Sentence', 'English Word', 'English Sentence'])
        
        # Write data rows
        for i, (word, category) in enumerate(all_words, 1):
            # Get sentences for this word (if available)
            sentences = word_sentences.get(word, [])
            sentence = sentences[0] if sentences else ""
            
            # Write row with placeholder for English translation
            writer.writerow([
                i,                           # Number
                word,                        # Language Word
                sentence,                    # Language Sentence
                f"[{word} in English]",      # English Word (placeholder)
                f"[English translation]"     # English Sentence (placeholder)
            ])
    
    return output_path


def export_category_to_csv(
    category: str,
    words: List[str],
    word_sentences: Dict[str, List[str]],
    pdf_name: str,
    language: str
) -> str:
    """
    Export words of a specific category to a CSV file.
    
    Args:
        category: Category name (e.g., "Nouns", "Verbs")
        words: List of words in this category
        word_sentences: Dictionary mapping words to example sentences
        pdf_name: Name of the PDF (used in the output filename)
        language: Language of the words
        
    Returns:
        Path to the CSV file
    """
    # Create a timestamp for the filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Generate a clean filename base from the PDF name
    # Remove extension and any special characters
    base_name = os.path.splitext(os.path.basename(pdf_name))[0]
    base_name = ''.join(c if c.isalnum() else '_' for c in base_name)
    
    # Generate the output filename (including category)
    category_clean = category.lower().replace(' ', '_')
    output_path = f"{base_name}_{category_clean}_{timestamp}.csv"
    
    # Sort words alphabetically
    sorted_words = sorted(words)
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header row
        writer.writerow(['Number', f'{language} Word', f'{language} Sentence', 'English Word', 'English Sentence'])
        
        # Write data rows
        for i, word in enumerate(sorted_words, 1):
            # Get sentences for this word (if available)
            sentences = word_sentences.get(word, [])
            sentence = sentences[0] if sentences else ""
            
            # Write row with placeholder for English translation
            writer.writerow([
                i,                           # Number
                word,                        # Language Word
                sentence,                    # Language Sentence
                f"[{word} in English]",      # English Word (placeholder)
                f"[English translation]"     # English Sentence (placeholder)
            ])
    
    return output_path