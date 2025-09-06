import streamlit as st
import gtts
import tempfile
import os
import time
import hashlib

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

# Initialize session state for caching
if 'cached_audio' not in st.session_state:
    st.session_state.cached_audio = {}
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'request_count' not in st.session_state:
    st.session_state.request_count = 0

def get_text_hash(text, language):
    """Generate hash for caching"""
    return hashlib.md5(f"{text}_{language}".encode()).hexdigest()

def can_make_request():
    """Check if we can make a request (rate limiting)"""
    current_time = time.time()
    
    # Reset counter every hour
    if current_time - st.session_state.last_request_time > 3600:
        st.session_state.request_count = 0
        st.session_state.last_request_time = current_time
    
    # Allow max 10 requests per hour (conservative limit)
    return st.session_state.request_count < 10

# Title
st.title("🎙️ Text to Speech")

# Rate limit info
col1, col2 = st.columns([3, 1])
with col1:
    language = st.selectbox("Language:", list(LANGUAGES.keys()))
with col2:
    remaining = max(0, 10 - st.session_state.request_count)
    st.metric("Requests left", remaining)

# Text input
text = st.text_area("Enter text:", height=200, placeholder="Type or paste your text here...")

# Auto-generate when text is entered (with caching and rate limiting)
if text.strip():
    text_hash = get_text_hash(text, language)
    
    # Check if we have cached audio for this text+language combo
    if text_hash in st.session_state.cached_audio:
        st.audio(st.session_state.cached_audio[text_hash], format='audio/mp3')
        
        # Download button
        st.download_button(
            label="📥 Download as MP3",
            data=st.session_state.cached_audio[text_hash],
            file_name="speech.mp3",
            mime="audio/mp3"
        )
        
        st.success("✅ Using cached audio (no API call needed)")
        
    elif can_make_request():
        try:
            with st.spinner("Generating audio..."):
                # Add small delay to be respectful to the API
                time.sleep(1)
                
                tts = gtts.gTTS(text=text, lang=LANGUAGES[language], slow=False)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tts.save(tmp_file.name)
                    
                    with open(tmp_file.name, 'rb') as f:
                        audio_bytes = f.read()
                    
                    # Cache the results
                    st.session_state.cached_audio[text_hash] = audio_bytes
                    st.session_state.request_count += 1
                    
                    os.unlink(tmp_file.name)
                    
                    st.audio(audio_bytes, format='audio/mp3')
                    
                    # Download button
                    st.download_button(
                        label="📥 Download as MP3",
                        data=audio_bytes,
                        file_name="speech.mp3",
                        mime="audio/mp3"
                    )
                    
                    st.success(f"✅ Audio generated! ({st.session_state.request_count}/10 requests used)")
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                st.error("⚠️ Rate limit reached. Please wait a few minutes before trying again.")
                st.info("💡 Try using shorter text or wait for the limit to reset.")
            elif "403" in error_msg:
                st.error("🚫 Access forbidden. The service might be temporarily unavailable.")
            else:
                st.error(f"❌ Error: {error_msg}")
    else:
        st.warning("⏳ Rate limit reached (10 requests/hour). Please wait before making more requests.")
        st.info("💡 Previously generated audio is still available from cache above!")
        
        # Still show cached audio if available
        if text_hash in st.session_state.cached_audio:
            st.audio(st.session_state.cached_audio[text_hash], format='audio/mp3')
            st.download_button(
                label="📥 Download as MP3",
                data=st.session_state.cached_audio[text_hash],
                file_name="speech.mp3",
                mime="audio/mp3"
            )
