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

# Auto-generate when text is entered
if text.strip():
    try:
        tts = gtts.gTTS(text=text, lang=LANGUAGES[language])
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            
            with open(tmp_file.name, 'rb') as f:
                audio_bytes = f.read()
            
            st.audio(audio_bytes, format='audio/mp3')
            
            os.unlink(tmp_file.name)
            
    except Exception as e:
        st.error(f"Error: {e}")
