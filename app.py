import streamlit as st
import os
import tempfile
import time
import PyPDF2
from typing import Optional, Tuple, Dict, List
from pdf_processor import extract_text_from_pdf, find_word_sentences
from nlp_processor import categorize_words
from anki_manager import compare_with_existing_decks, create_anki_deck
from audio_generator import generate_audio_for_words
from utils import get_existing_decks, save_temp_file, get_existing_words
from csv_exporter import export_words_to_csv, export_category_to_csv
from local_script_integration import save_csv_for_local_processing, prepare_anki_script_config, prepare_audio_script_config, save_script_configuration
from deck_storage import get_stored_decks, delete_stored_deck

# Set page config
st.set_page_config(
    page_title="Spanish Learning Platform",
    page_icon="🇪🇸",
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
if 'word_sentences' not in st.session_state:
    st.session_state.word_sentences = {}
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = ""
if 'generated_csv_path' not in st.session_state:
    st.session_state.generated_csv_path = None
if 'category_csv_paths' not in st.session_state:
    st.session_state.category_csv_paths = {}

# Main app
st.title("Spanish Learning Platform")
st.write("Upload a Spanish PDF, extract words, categorize them, and create Anki decks with audio.")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Set language to Spanish only
language = "Spanish"
st.sidebar.info("This platform is dedicated to Spanish language learning only.")

# Anki deck upload
st.sidebar.subheader("Upload Existing Anki Deck")
uploaded_deck = st.sidebar.file_uploader(
    "Upload an Anki deck (.apkg file)",
    type="apkg",
    help="Upload an existing Anki deck to compare with extracted words."
)

# Initialize session state for uploaded decks if it doesn't exist
if 'custom_deck_paths' not in st.session_state:
    st.session_state.custom_deck_paths = []
if 'uploaded_deck_names' not in st.session_state:
    st.session_state.uploaded_deck_names = []

# Store uploaded deck in session state
if uploaded_deck is not None:
    # Only process the deck if it's not already been uploaded
    if uploaded_deck.name not in st.session_state.uploaded_deck_names:
        deck_temp_path = save_temp_file(uploaded_deck)
        st.session_state.custom_deck_paths.append(deck_temp_path)
        st.session_state.uploaded_deck_names.append(uploaded_deck.name)
        st.sidebar.success(f"Deck '{uploaded_deck.name}' uploaded successfully!")
    
    # Clear the file uploader
    # This is a workaround to prevent the same file from being processed multiple times
    uploaded_deck = None

# Display all uploaded decks and provide a way to clear them
if st.session_state.uploaded_deck_names:
    st.sidebar.write(f"Uploaded decks: {', '.join(st.session_state.uploaded_deck_names)}")
    if st.sidebar.button("Clear uploaded decks"):
        st.session_state.custom_deck_paths = []
        st.session_state.uploaded_deck_names = []
        st.sidebar.success("All uploaded decks have been cleared")

# Existing deck selection
existing_decks = get_existing_decks()
if st.session_state.custom_deck_paths:
    # Add uploaded decks with their names for better identification
    named_decks = []
    for i, path in enumerate(st.session_state.custom_deck_paths):
        if i < len(st.session_state.uploaded_deck_names):
            named_decks.append(f"{st.session_state.uploaded_deck_names[i]} ({path})")
        else:
            named_decks.append(path)
    existing_decks.extend(named_decks)

selected_decks = st.sidebar.multiselect(
    "Select decks to compare with",
    existing_decks,
    default=existing_decks[:1] if existing_decks else []
)

# Word type selection
st.sidebar.subheader("Word Types to Include")
word_types = {
    "nouns": st.sidebar.checkbox("Nouns", value=True),
    "verbs": st.sidebar.checkbox("Verbs", value=True),
    "adjectives": st.sidebar.checkbox("Adjectives", value=True),
    "adverbs": st.sidebar.checkbox("Adverbs", value=True),
    "proper_nouns": st.sidebar.checkbox("Proper Nouns", value=False),
    "numbers": st.sidebar.checkbox("Numbers", value=False),
    "other": st.sidebar.checkbox("Other", value=False)
}

# Advanced options
with st.sidebar.expander("Advanced Options"):
    min_word_length = st.slider("Minimum word length", 1, 10, 3)
    audio_enabled = st.checkbox("Generate audio", value=True)
    
    # Google Cloud TTS option
    st.subheader("Audio Generation")
    st.info("This platform supports Google Cloud Text-to-Speech for high-quality audio. " +
           "To use this service, please provide your Google Cloud credentials file.")
    
    # Google Cloud credentials file uploader
    gc_credentials = st.file_uploader(
        "Upload Google Cloud credentials file (JSON)",
        type="json",
        key="gc_credentials",
        help="Upload your Google Cloud service account credentials to enable high-quality audio."
    )
    
    if gc_credentials is not None:
        # Save the credentials to a temporary file and set the environment variable
        temp_cred_path = save_temp_file(gc_credentials)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_cred_path
        st.success("Google Cloud credentials loaded successfully!")
    
    # Note about audio quality
    st.caption("If Google Cloud credentials are not provided, the platform will use the default gTTS service.")

# File uploader with explicit type and additional help text
uploaded_file = st.file_uploader(
    "Choose a PDF file", 
    type="pdf",
    help="Upload a PDF file to extract and categorize words (max 200MB)."
)

# Display a notice about file size limitations
st.caption("Note: If you're having trouble uploading large files, try uploading a smaller PDF file.")

# Option to use sample PDF
use_sample = st.checkbox("Use sample PDF instead", value=False)
if use_sample:
    if os.path.exists("sample.pdf"):
        st.success("Using sample PDF file")
        with open("sample.pdf", "rb") as f:
            # Create a synthetic UploadedFile
            class SyntheticUploadedFile:
                def __init__(self, content):
                    self._content = content
                def getvalue(self):
                    return self._content
            
            uploaded_file = SyntheticUploadedFile(f.read())
    else:
        st.error("Sample PDF not found. Please upload your own PDF file.")

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
            st.session_state.pdf_text = pdf_text
            
            # Store the PDF name (either from uploaded file or sample)
            if use_sample:
                st.session_state.pdf_name = "sample.pdf"
            else:
                # Get the original filename from the uploaded file
                try:
                    # Try to access the name attribute if it's a standard UploadedFile
                    st.session_state.pdf_name = uploaded_file.name
                except:
                    # Fall back to just the temp file path if it's a synthetic file
                    st.session_state.pdf_name = os.path.basename(temp_file_path)
            
            progress_bar.progress(20)
            
            # Step 2: Categorize words using NLP
            status_text.text("Categorizing words...")
            
            # Get existing words to prevent duplicates
            existing_words_set = get_existing_words()
            
            categorized_words = categorize_words(
                pdf_text, 
                language, 
                min_length=min_word_length, 
                word_types=word_types,  # Use the selected word types
                existing_words=existing_words_set  # Pass existing words for de-duplication
            )
            st.session_state.extracted_words = categorized_words
            
            # Extract all words from all categories for sentence extraction
            all_words = []
            for category, words in categorized_words.items():
                all_words.extend(words)
            
            # Find sentences containing these words
            status_text.text("Extracting example sentences...")
            word_sentences = find_word_sentences(pdf_text, all_words)
            st.session_state.word_sentences = word_sentences
            
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
                deck_path = create_anki_deck(new_words, audio_files, deck_name, language, store_deck=True)
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
        
        # Create tabs for word categories
        tabs = st.tabs(list(st.session_state.extracted_words.keys()))
        for i, category in enumerate(st.session_state.extracted_words.keys()):
            with tabs[i]:
                words = st.session_state.extracted_words[category]
                if words:
                    # Show which words are new and which are existing
                    new_words_in_category = st.session_state.new_words.get(category, [])
                    existing_words_in_category = st.session_state.existing_words.get(category, [])
                    
                    # Display as a table with word status
                    word_status = []
                    for word in words:
                        if word in new_words_in_category:
                            word_status.append("✅ New")
                        elif word in existing_words_in_category:
                            word_status.append("🔄 Already in deck")
                        else:
                            word_status.append("⚠️ Not categorized")
                    
                    # Create a dataframe for display
                    word_df = {"Word": words, "Status": word_status}
                    st.dataframe(word_df, use_container_width=True)
                    
                    # Add a toggle to show example sentences for the words
                    if st.checkbox(f"Show example sentences for {category}", key=f"show_sentences_{category}"):
                        for word in words:
                            if word in st.session_state.word_sentences:
                                sentences = st.session_state.word_sentences[word]
                                if sentences:
                                    st.write(f"**{word}**: {sentences[0]}")
                else:
                    st.write("No words found in this category.")
        
        # Option to download the generated deck
        st.subheader("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Anki Deck:")
            if st.session_state.new_words and sum(len(words) for words in st.session_state.new_words.values()) > 0:
                # Add option to create a new deck
                st.subheader("Create Anki Deck")

                # Allow merging with existing deck
                merge_with_existing = st.checkbox("Merge with existing deck")
                selected_deck_for_merge = None
                
                if merge_with_existing:
                    # Get all stored Spanish decks for merging
                    stored_decks = get_stored_decks(language_filter="Spanish")
                    if stored_decks:
                        deck_options = [deck_info['name'] for deck_info in stored_decks]
                        deck_options.insert(0, "Select a deck")
                        
                        # Let user select a deck to merge with
                        selected_deck_name = st.selectbox(
                            "Select deck to merge with:",
                            deck_options
                        )
                        
                        if selected_deck_name != "Select a deck":
                            # Find the selected deck info
                            for deck_info in stored_decks:
                                if deck_info['name'] == selected_deck_name:
                                    selected_deck_for_merge = deck_info['path']
                                    break
                    else:
                        st.warning("No existing decks found for merging. Creating a new deck instead.")
                        merge_with_existing = False
                
                # Option to add custom deck name
                custom_deck_name = st.text_input(
                    "Custom deck name (optional):",
                    value=f"New_Spanish_Words_{time.strftime('%Y%m%d_%H%M%S')}"
                )
                
                if st.button("Generate Anki Deck"):
                    if audio_enabled:
                        audio_files = generate_audio_for_words(st.session_state.new_words, language)
                    else:
                        audio_files = {}
                        
                    # Create a new deck or merge with existing
                    deck_path = create_anki_deck(
                        st.session_state.new_words, 
                        audio_files, 
                        custom_deck_name, 
                        language,
                        store_deck=True,
                        existing_deck_path=selected_deck_for_merge,
                        merge_existing=merge_with_existing
                    )
                    
                    st.session_state.generated_deck_path = deck_path
                    st.success(f"Anki deck created successfully{'! Words have been merged with the selected deck.' if merge_with_existing else '!'}")
                    st.rerun()
                
            # Show download option if a deck was generated
            if st.session_state.generated_deck_path:
                with open(st.session_state.generated_deck_path, "rb") as file:
                    st.download_button(
                        label="Download Anki Deck",
                        data=file,
                        file_name=os.path.basename(st.session_state.generated_deck_path),
                        mime="application/octet-stream"
                    )
            elif not st.session_state.new_words or sum(len(words) for words in st.session_state.new_words.values()) == 0:
                st.info("No new words found, so no Anki deck was created.")
        
        with col2:
            st.write("CSV Export (for local scripts):")
            
            # Add option to export all words as CSV
            if st.session_state.new_words and sum(len(words) for words in st.session_state.new_words.values()) > 0:
                if st.button("Export All New Words as CSV"):
                    # Generate CSV with all new words and their sentences
                    pdf_name = st.session_state.pdf_name
                    csv_path = export_words_to_csv(
                        st.session_state.new_words,
                        st.session_state.word_sentences,
                        pdf_name,
                        language
                    )
                    st.session_state.generated_csv_path = csv_path
                    
                    # Create a configuration file for local scripts
                    config = prepare_anki_script_config(
                        csv_path,
                        f"New_{language}_Words_{time.strftime('%Y%m%d_%H%M%S')}",
                        language
                    )
                    
                    # Save the configuration
                    config_path = save_script_configuration(
                        config,
                        f"anki_config_{language}"
                    )
                    
                    st.success(f"CSV file and script configuration created successfully!")
            
            # Display download button for CSV if it exists
            if st.session_state.generated_csv_path and os.path.exists(st.session_state.generated_csv_path):
                with open(st.session_state.generated_csv_path, "rb") as file:
                    st.download_button(
                        label="Download CSV for Local Scripts",
                        data=file,
                        file_name=os.path.basename(st.session_state.generated_csv_path),
                        mime="text/csv"
                    )
        
        # Add export buttons for each category
        st.subheader("Export by Category")
        category_cols = st.columns(3)
        
        # Clear previous category exports if the user clicks this button
        if st.button("Clear Previous Category Exports"):
            st.session_state.category_csv_paths = {}
            st.success("All category exports cleared")
        
        # Create export buttons for each category
        for i, category in enumerate(st.session_state.new_words.keys()):
            words = st.session_state.new_words[category]
            if words:
                with category_cols[i % 3]:
                    # Format category name for display
                    category_display = category.replace("_", " ").title()
                    
                    if st.button(f"Export {category_display} as CSV"):
                        # Generate CSV with category words and their sentences
                        pdf_name = st.session_state.pdf_name
                        
                        # Use simple timestamp in filename for identification
                        timestamp = time.strftime('%Y%m%d_%H%M%S')
                        base_name = f"{os.path.splitext(pdf_name)[0]}_{timestamp}"
                        
                        csv_path = export_category_to_csv(
                            category,
                            words,
                            st.session_state.word_sentences,
                            base_name,
                            language
                        )
                        
                        # Store the path in session state
                        st.session_state.category_csv_paths[category] = csv_path
                        
                        # Create a configuration file for local scripts
                        config = prepare_anki_script_config(
                            csv_path,
                            f"{category}_{language}_{time.strftime('%Y%m%d_%H%M%S')}",
                            language
                        )
                        
                        # Save the configuration
                        config_path = save_script_configuration(
                            config,
                            f"anki_config_{category}_{language}"
                        )
                        
                        st.success(f"CSV file for {category_display} created! Use it with your local scripts.")
                    
                    # Show download button if category export exists
                    if category in st.session_state.category_csv_paths and os.path.exists(st.session_state.category_csv_paths[category]):
                        with open(st.session_state.category_csv_paths[category], "rb") as file:
                            st.download_button(
                                label=f"Download {category_display} CSV",
                                data=file,
                                file_name=os.path.basename(st.session_state.category_csv_paths[category]),
                                mime="text/csv",
                                key=f"download_{category}"  # Unique key for each button
                            )
    
    # Display error message if there was an error
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

# Add a section for deck management
st.markdown("---")
st.header("Spanish Anki Deck Management")
st.write("Here you can view, manage, and delete stored Spanish Anki decks.")

# Get Spanish stored decks only
stored_decks = get_stored_decks(language_filter="Spanish")

if stored_decks:
    # Create a table to display stored decks
    deck_table = {"Deck Name": [], "Created Date": [], "Actions": []}
    
    for i, deck_info in enumerate(stored_decks):
        deck_name = deck_info['name']
        deck_path = deck_info['path']
        
        # Extract timestamp from filename
        timestamp = deck_info.get('timestamp', 'Unknown date')
        if timestamp != 'Unknown date':
            # Format timestamp for display (YYYYMMDD_HHMMSS to YYYY-MM-DD HH:MM:SS)
            try:
                date_part, time_part = timestamp.split('_')
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:]}"
            except:
                formatted_date = timestamp
                
        else:
            formatted_date = timestamp
        
        deck_table["Deck Name"].append(deck_name)
        deck_table["Created Date"].append(formatted_date)
        
        # For actions, we'll use buttons with unique keys
        deck_table["Actions"].append(f"Delete {deck_name}")
    
    # Display the table
    st.dataframe(deck_table, use_container_width=True)
    
    # Add action buttons below the table
    st.subheader("Deck Actions")
    
    # Show a dropdown to select a deck
    selected_deck_index = st.selectbox(
        "Select a deck to manage:",
        range(len(stored_decks)),
        format_func=lambda i: stored_decks[i]['name']
    )
    
    # Get the selected deck info
    selected_deck = stored_decks[selected_deck_index]
    deck_path = selected_deck['path']
    
    # Display actions for the selected deck
    col1, col2 = st.columns(2)
    with col1:
        # Download option
        with open(deck_path, "rb") as file:
            st.download_button(
                label=f"Download {selected_deck['name']}",
                data=file,
                file_name=selected_deck['name'],
                mime="application/octet-stream"
            )
    
    with col2:
        # Delete option
        if st.button(f"Delete {selected_deck['name']}"):
            success = delete_stored_deck(deck_path)
            if success:
                st.success(f"Deck {selected_deck['name']} deleted successfully!")
                st.rerun()  # Refresh the page
            else:
                st.error(f"Failed to delete deck {selected_deck['name']}")
else:
    st.info("No stored decks found. Decks you create will be stored here for future use.")

# Footer
st.markdown("---")
st.markdown("© 2025 Spanish Learning Platform")
