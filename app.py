import streamlit as st
import pyttsx3
import tempfile
import os
import io
import time
from pathlib import Path
import base64

# Configure page
st.set_page_config(
    page_title="Emotional TTS Generator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #ff6b6b;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .emotion-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    .voice-controls {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #007bff;
    }
    .text-area {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
    }
    .download-section {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize TTS engine
@st.cache_resource
def init_tts():
    engine = pyttsx3.init()
    return engine

def get_available_voices(engine):
    voices = engine.getProperty('voices')
    voice_options = {}
    for i, voice in enumerate(voices):
        name = voice.name
        gender = "Female" if "female" in name.lower() or "woman" in name.lower() else "Male"
        voice_options[f"{name} ({gender})"] = voice.id
    return voice_options

def apply_emotion_settings(engine, emotion, custom_rate, custom_volume, custom_pitch):
    # Emotion-based voice adjustments
    emotion_settings = {
        "😊 Happy": {"rate_mod": 1.2, "volume": 0.9, "pitch_mod": 1.1},
        "😢 Sad": {"rate_mod": 0.7, "volume": 0.6, "pitch_mod": 0.8},
        "😡 Angry": {"rate_mod": 1.3, "volume": 1.0, "pitch_mod": 1.2},
        "😴 Calm": {"rate_mod": 0.8, "volume": 0.7, "pitch_mod": 0.9},
        "😨 Excited": {"rate_mod": 1.4, "volume": 0.95, "pitch_mod": 1.3},
        "🤔 Thoughtful": {"rate_mod": 0.9, "volume": 0.8, "pitch_mod": 0.95},
        "💝 Romantic": {"rate_mod": 0.85, "volume": 0.75, "pitch_mod": 0.9},
        "📰 News": {"rate_mod": 1.0, "volume": 0.85, "pitch_mod": 1.0},
        "🎭 Dramatic": {"rate_mod": 0.9, "volume": 0.9, "pitch_mod": 1.1},
        "🤖 Robotic": {"rate_mod": 1.1, "volume": 0.8, "pitch_mod": 1.0}
    }
    
    settings = emotion_settings.get(emotion, {"rate_mod": 1.0, "volume": 0.8, "pitch_mod": 1.0})
    
    # Apply custom settings with emotion modifiers
    final_rate = int(custom_rate * settings["rate_mod"])
    final_volume = min(1.0, custom_volume * settings["volume"])
    
    engine.setProperty('rate', final_rate)
    engine.setProperty('volume', final_volume)
    
    return engine

def text_to_speech(text, voice_id, emotion, rate, volume, pitch, add_pauses):
    engine = init_tts()
    
    # Set voice
    engine.setProperty('voice', voice_id)
    
    # Apply emotion settings
    engine = apply_emotion_settings(engine, emotion, rate, volume, pitch)
    
    # Add natural pauses
    if add_pauses:
        text = add_natural_pauses(text)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        temp_path = tmp_file.name
    
    try:
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        
        # Read the audio file
        with open(temp_path, 'rb') as f:
            audio_data = f.read()
        
        return audio_data
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

def add_natural_pauses(text):
    """Add natural pauses to make speech more human-like"""
    # Add pauses after sentences
    text = text.replace('. ', '. <break time="0.8s"/> ')
    text = text.replace('! ', '! <break time="0.8s"/> ')
    text = text.replace('? ', '? <break time="0.8s"/> ')
    
    # Add short pauses after commas
    text = text.replace(', ', ', <break time="0.3s"/> ')
    
    # Add pauses after colons and semicolons
    text = text.replace(': ', ': <break time="0.5s"/> ')
    text = text.replace('; ', '; <break time="0.5s"/> ')
    
    return text

def get_download_link(audio_data, filename):
    """Generate download link for audio file"""
    b64_audio = base64.b64encode(audio_data).decode()
    href = f'<a href="data:audio/wav;base64,{b64_audio}" download="{filename}" style="color: white; text-decoration: none; font-weight: bold; background: #28a745; padding: 10px 20px; border-radius: 5px; display: inline-block;">📥 Download Audio File</a>'
    return href

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🎭 Emotional Text-to-Speech Generator</h1>', unsafe_allow_html=True)
    
    # Initialize TTS
    engine = init_tts()
    voices = get_available_voices(engine)
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Voice Controls")
        
        # Voice selection
        selected_voice_name = st.selectbox(
            "Select Voice:",
            options=list(voices.keys()),
            help="Choose a voice that matches your content"
        )
        
        # Emotion selection
        emotion = st.selectbox(
            "🎭 Emotion/Style:",
            options=[
                "😊 Happy",
                "😢 Sad", 
                "😡 Angry",
                "😴 Calm",
                "😨 Excited",
                "🤔 Thoughtful",
                "💝 Romantic",
                "📰 News",
                "🎭 Dramatic",
                "🤖 Robotic"
            ],
            help="Choose the emotional tone for your speech"
        )
        
        st.markdown("---")
        
        # Voice tuning parameters
        st.subheader("🔧 Fine Tuning")
        
        rate = st.slider(
            "Speech Rate (WPM):",
            min_value=50,
            max_value=300,
            value=180,
            step=10,
            help="Words per minute - slower for clarity, faster for excitement"
        )
        
        volume = st.slider(
            "Volume:",
            min_value=0.1,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Audio volume level"
        )
        
        pitch = st.slider(
            "Pitch Modifier:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Higher values = higher pitch"
        )
        
        # Additional options
        st.markdown("---")
        st.subheader("🌟 Enhancement Options")
        
        add_pauses = st.checkbox(
            "Add Natural Pauses",
            value=True,
            help="Automatically add pauses for more natural speech"
        )
        
        emphasize_caps = st.checkbox(
            "Emphasize CAPITAL WORDS",
            value=True,
            help="Speak capitalized words with more emphasis"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Enter Your Text")
        
        # Text input with sample
        sample_text = "Hello! Welcome to our emotional text-to-speech generator. This tool can transform your written words into natural, expressive speech with various emotional tones. Try typing your own text or use this sample to test different voices and emotions!"
        
        text_input = st.text_area(
            "Paste or type your text here:",
            value="",
            height=200,
            placeholder=f"Example: {sample_text}",
            help="No word limit! Paste any amount of text."
        )
        
        # Quick text options
        st.subheader("📚 Quick Text Samples")
        col_sample1, col_sample2, col_sample3 = st.columns(3)
        
        with col_sample1:
            if st.button("📖 Story Sample"):
                text_input = "Once upon a time, in a land far away, there lived a brave knight who embarked on an incredible journey. The path was filled with challenges, but determination guided every step forward."
        
        with col_sample2:
            if st.button("📰 News Sample"):
                text_input = "Breaking news: Scientists have made a groundbreaking discovery that could change our understanding of the universe. The research team spent years analyzing data before reaching this remarkable conclusion."
        
        with col_sample3:
            if st.button("💼 Business Sample"):
                text_input = "Thank you for joining today's presentation. We're excited to share our latest innovations and discuss how they can benefit your organization. Let's begin with our key findings."
    
    with col2:
        st.subheader("🎵 Voice Preview")
        
        # Emotion description
        emotion_descriptions = {
            "😊 Happy": "Upbeat, cheerful, and energetic",
            "😢 Sad": "Slower, softer, melancholic tone",
            "😡 Angry": "Intense, faster, with emphasis",
            "😴 Calm": "Peaceful, steady, relaxing",
            "😨 Excited": "Fast-paced, enthusiastic",
            "🤔 Thoughtful": "Measured, contemplative",
            "💝 Romantic": "Warm, gentle, intimate",
            "📰 News": "Professional, clear, authoritative",
            "🎭 Dramatic": "Expressive, theatrical",
            "🤖 Robotic": "Mechanical, consistent pace"
        }
        
        st.info(f"**{emotion}**\n\n{emotion_descriptions[emotion]}")
        
        # Voice info
        selected_voice_id = voices[selected_voice_name]
        st.write(f"**Selected Voice:** {selected_voice_name}")
        st.write(f"**Rate:** {rate} WPM")
        st.write(f"**Volume:** {int(volume*100)}%")
        st.write(f"**Pitch:** {pitch}x")
    
    # Generate speech section
    st.markdown("---")
    st.subheader("🎤 Generate Speech")
    
    if st.button("🎵 Generate Audio", type="primary", use_container_width=True):
        if text_input.strip():
            with st.spinner("🎭 Generating emotional speech... Please wait!"):
                # Process text based on options
                processed_text = text_input
                if emphasize_caps:
                    # Add emphasis tags to capital words
                    import re
                    processed_text = re.sub(r'\b[A-Z]{2,}\b', r'<emphasis level="strong">\g<0></emphasis>', processed_text)
                
                # Generate audio
                audio_data = text_to_speech(
                    processed_text,
                    selected_voice_id,
                    emotion,
                    rate,
                    volume,
                    pitch,
                    add_pauses
                )
                
                if audio_data:
                    st.success("🎉 Audio generated successfully!")
                    
                    # Create download section
                    st.markdown('<div class="download-section">', unsafe_allow_html=True)
                    
                    # Audio player
                    st.audio(audio_data, format='audio/wav')
                    
                    # Download link
                    filename = f"tts_audio_{emotion.replace(' ', '_')}_{int(time.time())}.wav"
                    download_link = get_download_link(audio_data, filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Statistics
                    word_count = len(text_input.split())
                    char_count = len(text_input)
                    estimated_duration = (word_count / rate) * 60  # seconds
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Words", word_count)
                    with col_stat2:
                        st.metric("Characters", char_count)
                    with col_stat3:
                        st.metric("Duration", f"{estimated_duration:.1f}s")
                
                else:
                    st.error("❌ Failed to generate audio. Please try again.")
        else:
            st.warning("⚠️ Please enter some text first!")
    
    # Tips section
    st.markdown("---")
    st.subheader("💡 Tips for Better Results")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **Text Formatting:**
        - Use punctuation for natural pauses
        - CAPITALIZE words you want emphasized
        - Write numbers as words (e.g., "twenty" not "20")
        - Use simple, clear sentences
        """)
    
    with tips_col2:
        st.markdown("""
        **Voice Settings:**
        - Lower rate for dramatic/sad content
        - Higher rate for excited/happy content  
        - Adjust pitch for age/gender preferences
        - Test different voices for your content type
        """)

if __name__ == "__main__":
    main()
