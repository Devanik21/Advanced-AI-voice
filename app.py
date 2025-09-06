import streamlit as st
import gtts
import tempfile
import os
import base64
import time

# Configure page
st.set_page_config(
    page_title="gTTS Generator",
    page_icon="🎙️",
    layout="centered"
)

# Simple CSS for clean UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .text-area {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .generate-btn {
        background-color: #1f77b4;
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 20px 0;
    }
    .download-link {
        display: inline-block;
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Available languages for gTTS
LANGUAGES = {
    "English (US)": "en",
    "English (UK)": "en-uk",
    "English (Australia)": "en-au", 
    "English (India)": "en-in",
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

def text_to_speech(text, language):
    """Generate speech using gTTS"""
    try:
        tts = gtts.gTTS(text=text, lang=language, slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            temp_path = tmp_file.name
            tts.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(temp_path)
            return audio_data
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_download_link(audio_data, filename):
    """Create download link"""
    b64 = base64.b64encode(audio_data).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}" class="download-link">📥 Download Audio</a>'
    return href

def main():
    # Header
    st.markdown('<h1 class="main-header">🎙️ Text to Speech</h1>', unsafe_allow_html=True)
    
    # Language selection
    language_name = st.selectbox(
        "Select Language:",
        options=list(LANGUAGES.keys()),
        index=0
    )
    
    # Text input
    text_input = st.text_area(
        "Enter your text:",
        height=200,
        placeholder="Type or paste your text here...",
        help="Enter any text to convert to speech"
    )
    
    # Generate button
    if st.button("🎵 Generate Speech", type="primary"):
        if text_input.strip():
            with st.spinner("Generating audio..."):
                language_code = LANGUAGES[language_name]
                audio_data = text_to_speech(text_input, language_code)
                
                if audio_data:
                    st.success("✅ Audio generated!")
                    
                    # Play audio
                    st.audio(audio_data, format='audio/mp3')
                    
                    # Download link
                    filename = f"tts_audio_{int(time.time())}.mp3"
                    download_link = get_download_link(audio_data, filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # Stats
                    word_count = len(text_input.split())
                    char_count = len(text_input)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Words", word_count)
                    with col2:
                        st.metric("Characters", char_count)
        else:
            st.warning("Please enter some text!")

if __name__ == "__main__":
    main()
