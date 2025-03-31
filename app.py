import streamlit as st
import os
import tempfile
import time
import PyPDF2
from typing import Optional, Tuple
from pdf_processor import extract_text_from_pdf
from nlp_processor import categorize_words
from anki_manager import compare_with_existing_decks, create_anki_deck
from audio_generator import generate_audio_for_words
from utils import get_existing_decks, save_temp_file

# Set page config
st.set_page_config(
    page_title="Language Learning Platform",
    page_icon="📚",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'extracted_words' not in st.session_state:
    st.session_state.extracted_words = {}
if 'new_words' not in st.session_state:
    st.session_state.new_words = {}
if 'existing_words' not in st.session_state:
    st.session_state.existing_words = {}
if 'generated_deck_path' not in st.session_state:
    st.session_state.generated_deck_path = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# Main app
st.title("Language Learning Platform")
st.write("Upload a PDF, extract words, categorize them, and create Anki decks with audio.")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Language selection
language = st.sidebar.selectbox(
    "Select language",
    ["French", "Spanish", "German", "Italian", "Japanese", "Chinese", "Russian"],
    index=0
)

# Existing deck selection
existing_decks = get_existing_decks()
selected_decks = st.sidebar.multiselect(
    "Select existing decks to compare with",
    existing_decks,
    default=existing_decks[:1] if existing_decks else []
)

# Advanced options
with st.sidebar.expander("Advanced Options"):
    min_word_length = st.slider("Minimum word length", 1, 10, 3)
    include_proper_nouns = st.checkbox("Include proper nouns", value=False)
    audio_enabled = st.checkbox("Generate audio", value=True)

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Save uploaded file to a temporary file to determine the number of pages
    temp_file_path = save_temp_file(uploaded_file)
    
    # Get the total number of pages in the PDF
    try:
        with open(temp_file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
        
        # Page range selection
        st.write(f"PDF has {total_pages} pages")
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Start page", min_value=1, max_value=total_pages, value=1)
        with col2:
            end_page = st.number_input("End page", min_value=start_page, max_value=total_pages, value=total_pages)
        
        page_range = (start_page, end_page)
        st.write(f"Selected pages: {start_page} to {end_page}")
    
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        page_range = None
    
    # Create a button to start processing
    if st.button("Process PDF"):
        st.session_state.error_message = None
        st.session_state.processing_complete = False
        
        # Display progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Ensure page range is defined
            # The variables start_page, end_page, and page_range should already be set above,
            # but let's provide a fallback just in case
            try:
                # Check if page_range exists and is valid
                if not page_range or not isinstance(page_range, tuple) or len(page_range) != 2:
                    start_page = 1
                    with open(temp_file_path, "rb") as file:
                        reader = PyPDF2.PdfReader(file)
                        end_page = len(reader.pages)
                    page_range = (start_page, end_page)
            except NameError:
                # If variables don't exist at all, define them
                start_page = 1
                with open(temp_file_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    end_page = len(reader.pages)
                page_range = (start_page, end_page)
                
            # Step 1: Extract text from PDF with page range
            status_text.text(f"Extracting text from pages {start_page} to {end_page}...")
            pdf_text = extract_text_from_pdf(temp_file_path, page_range)
            progress_bar.progress(20)
            
            # Step 2: Categorize words using NLP
            status_text.text("Categorizing words...")
            categorized_words = categorize_words(
                pdf_text, 
                language, 
                min_length=min_word_length, 
                include_proper_nouns=include_proper_nouns
            )
            st.session_state.extracted_words = categorized_words
            progress_bar.progress(40)
            
            # Step 3: Compare with existing decks
            status_text.text("Comparing with existing decks...")
            new_words, existing_words = compare_with_existing_decks(
                categorized_words, 
                selected_decks
            )
            st.session_state.new_words = new_words
            st.session_state.existing_words = existing_words
            progress_bar.progress(60)
            
            # Step 4: Generate audio for new words (if enabled)
            if audio_enabled:
                status_text.text("Generating audio for new words...")
                audio_files = generate_audio_for_words(new_words, language)
                progress_bar.progress(80)
            else:
                audio_files = {}
                progress_bar.progress(80)
            
            # Step 5: Create a new Anki deck
            status_text.text("Creating Anki deck...")
            if new_words:
                deck_name = f"New_{language}_Words_{time.strftime('%Y%m%d_%H%M%S')}"
                deck_path = create_anki_deck(new_words, audio_files, deck_name, language)
                st.session_state.generated_deck_path = deck_path
            else:
                st.session_state.generated_deck_path = None
            
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            st.session_state.processing_complete = True
            
        except Exception as e:
            st.session_state.error_message = f"Error: {str(e)}"
            status_text.text(f"Error occurred: {str(e)}")
            progress_bar.progress(0)
    
    # Display results if processing is complete
    if st.session_state.processing_complete:
        st.header("Results")
        
        # Display summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Words Extracted", sum(len(words) for words in st.session_state.extracted_words.values()))
        with col2:
            st.metric("New Words", sum(len(words) for words in st.session_state.new_words.values()))
        with col3:
            st.metric("Already Known Words", sum(len(words) for words in st.session_state.existing_words.values()))
        
        # Display categorized words
        st.subheader("Extracted Words by Category")
        
        tabs = st.tabs(list(st.session_state.extracted_words.keys()))
        for i, category in enumerate(st.session_state.extracted_words.keys()):
            with tabs[i]:
                words = st.session_state.extracted_words[category]
                if words:
                    # Show which words are new and which are existing
                    new_words_in_category = st.session_state.new_words.get(category, [])
                    existing_words_in_category = st.session_state.existing_words.get(category, [])
                    
                    # Display as a table
                    word_status = [("✅ New" if word in new_words_in_category else "🔄 Existing") for word in words]
                    word_df = {"Word": words, "Status": word_status}
                    st.dataframe(word_df, use_container_width=True)
                else:
                    st.write("No words found in this category.")
        
        # Option to download the generated deck
        if st.session_state.generated_deck_path:
            with open(st.session_state.generated_deck_path, "rb") as file:
                st.download_button(
                    label="Download Anki Deck",
                    data=file,
                    file_name=os.path.basename(st.session_state.generated_deck_path),
                    mime="application/octet-stream"
                )
        else:
            st.info("No new words found, so no Anki deck was created.")
    
    # Display error message if there was an error
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

# Footer
st.markdown("---")
st.markdown("© 2023 Language Learning Platform")
