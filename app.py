import streamlit as st
import gtts
import tempfile
import os

# Configure page
st.set_page_config(
    page_title="Text to Speech",
    page_icon="🎙️",
    layout="centered"
)

# Languages for gTTS
LANGUAGES = {
    "English": "en",
    "Spanish": "es", 
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Russian": "ru",
    "Arabic": "ar",
    "Hindi": "hi"
}

# Title
st.title("🎙️ Text to Speech")

# Language selection
language = st.selectbox("Language:", list(LANGUAGES.keys()))

# Text input
text = st.text_area("Enter text:", height=200, placeholder="Type or paste your text here...")

# Initialize session state for caching
if 'cached_audio' not in st.session_state:
    st.session_state.cached_audio = None
if 'cached_text' not in st.session_state:
    st.session_state.cached_text = ""
if 'cached_language' not in st.session_state:
    st.session_state.cached_language = ""

# Auto-generate when text is entered (with caching)
if text.strip():
    # Check if we need to regenerate (text or language changed)
    if (text != st.session_state.cached_text or 
        language != st.session_state.cached_language):
        
        try:
            tts = gtts.gTTS(text=text, lang=LANGUAGES[language])
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                with open(tmp_file.name, 'rb') as f:
                    audio_bytes = f.read()
                
                # Cache the results
                st.session_state.cached_audio = audio_bytes
                st.session_state.cached_text = text
                st.session_state.cached_language = language
                
                os.unlink(tmp_file.name)
                
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Display cached audio
    if st.session_state.cached_audio:
        st.audio(st.session_state.cached_audio, format='audio/mp3')
        
        # Download button
        st.download_button(
            label="📥 Download as MP3",
            data=st.session_state.cached_audio,
            file_name="speech.mp3",
            mime="audio/mp3"
        )
