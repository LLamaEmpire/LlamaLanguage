import io
import os
import re
import PyPDF2
from typing import List, Dict, Any, Optional, Tuple

def extract_text_from_pdf(pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
    """
    Extract text from a PDF file with optional page range specification.
    
    Args:
        pdf_path: Path to the PDF file
        page_range: Tuple of (start_page, end_page) to extract (1-indexed as shown to user)
                    If None, extracts all pages
        
    Returns:
        Extracted text as a string
    """
    text = ""
    
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            
            # Determine page range
            if page_range:
                start_page = max(0, page_range[0] - 1)  # Convert from 1-indexed to 0-indexed
                end_page = min(num_pages, page_range[1])  # Convert from 1-indexed to 0-indexed
            else:
                start_page = 0
                end_page = num_pages
            
            # Extract text from each page in the range
            for page_num in range(start_page, end_page):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Clean the text
        text = clean_text(text)
        return text
    
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def clean_text(text: str) -> str:
    """
    Clean the extracted text by removing unwanted characters and normalizing whitespace.
    
    Args:
        text: The raw extracted text
        
    Returns:
        Cleaned text
    """
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    
    # Remove page numbers (common formats)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Remove header/footer patterns (if found)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Remove urls
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove extra newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def get_paragraphs(text: str) -> List[str]:
    """
    Split the text into paragraphs.
    
    Args:
        text: The cleaned text
        
    Returns:
        List of paragraphs
    """
    # Split text by double newlines
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Filter out empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs
