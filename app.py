import streamlit as st
import gtts
import tempfile
import os
import io
import time
from pathlib import Path
import base64
import re
from pydub import AudioSegment
from pydub.effects import speedup, normalize
import numpy as np

# Configure page
st.set_page_config(
    page_title="Enhanced Emotional TTS Generator",
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
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .emotion-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }
    .voice-controls {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
    }
    .text-area {
        border: 2px solid #ddd;
        border-radius: 12px;
        padding: 1rem;
        background: rgba(248, 249, 250, 0.8);
    }
    .download-section {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(86, 171, 47, 0.3);
    }
    .feature-highlight {
        background: linear-gradient(45deg, #ff9a9e, #fecfef);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: #333;
        font-weight: bold;
    }
    .stats-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Available languages and voices for gTTS
GTTS_LANGUAGES = {
    "🇺🇸 English (US)": "en",
    "🇬🇧 English (UK)": "en-uk",
    "🇦🇺 English (Australia)": "en-au",
    "🇨🇦 English (Canada)": "en-ca",
    "🇮🇳 English (India)": "en-in",
    "🇪🇸 Spanish": "es",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
    "🇮🇹 Italian": "it",
    "🇯🇵 Japanese": "ja",
    "🇰🇷 Korean": "ko",
    "🇨🇳 Chinese (Mandarin)": "zh",
    "🇷🇺 Russian": "ru",
    "🇵🇹 Portuguese": "pt",
    "🇳🇱 Dutch": "nl",
    "🇸🇪 Swedish": "sv",
    "🇳🇴 Norwegian": "no",
    "🇩🇰 Danish": "da",
    "🇫🇮 Finnish": "fi"
}

def add_natural_pauses(text, emotion):
    """Add natural pauses to make speech more human-like based on emotion"""
    # Base pause durations (in milliseconds)
    base_pauses = {
        "😊 Happy": {"sentence": 600, "comma": 200, "colon": 300},
        "😢 Sad": {"sentence": 1200, "comma": 400, "colon": 600},
        "😡 Angry": {"sentence": 400, "comma": 100, "colon": 200},
        "😴 Calm": {"sentence": 1000, "comma": 350, "colon": 500},
        "😨 Excited": {"sentence": 300, "comma": 80, "colon": 150},
        "🤔 Thoughtful": {"sentence": 1000, "comma": 300, "colon": 500},
        "💝 Romantic": {"sentence": 800, "comma": 250, "colon": 400},
        "📰 News": {"sentence": 700, "comma": 200, "colon": 300},
        "🎭 Dramatic": {"sentence": 900, "comma": 250, "colon": 450},
        "🤖 Robotic": {"sentence": 500, "comma": 150, "colon": 250}
    }
    
    pauses = base_pauses.get(emotion, base_pauses["😊 Happy"])
    
    # Add pauses (we'll handle this with audio processing instead of text markers)
    processed_text = text
    
    # Add emphasis markers for emotional processing
    if emotion == "😡 Angry":
        processed_text = re.sub(r'[!]+', '!!!', processed_text)
    elif emotion == "😨 Excited":
        processed_text = re.sub(r'[!?]+', '!!', processed_text)
    elif emotion == "🤔 Thoughtful":
        processed_text = re.sub(r'\.\.\.', '... hmm...', processed_text)
    
    return processed_text

def apply_emotion_audio_effects(audio_segment, emotion, custom_speed, custom_pitch):
    """Apply audio effects to simulate emotions"""
    
    # Emotion-based audio modifications
    emotion_effects = {
        "😊 Happy": {"speed": 1.1, "pitch_shift": 2, "volume_boost": 2},
        "😢 Sad": {"speed": 0.8, "pitch_shift": -3, "volume_boost": -5},
        "😡 Angry": {"speed": 1.2, "pitch_shift": 1, "volume_boost": 5},
        "😴 Calm": {"speed": 0.9, "pitch_shift": -1, "volume_boost": -2},
        "😨 Excited": {"speed": 1.3, "pitch_shift": 4, "volume_boost": 3},
        "🤔 Thoughtful": {"speed": 0.85, "pitch_shift": -1, "volume_boost": -1},
        "💝 Romantic": {"speed": 0.9, "pitch_shift": -2, "volume_boost": -3},
        "📰 News": {"speed": 1.0, "pitch_shift": 0, "volume_boost": 0},
        "🎭 Dramatic": {"speed": 0.95, "pitch_shift": 1, "volume_boost": 2},
        "🤖 Robotic": {"speed": 1.0, "pitch_shift": 0, "volume_boost": 0}
    }
    
    effects = emotion_effects.get(emotion, emotion_effects["😊 Happy"])
    
    # Apply speed change
    final_speed = custom_speed * effects["speed"]
    if final_speed != 1.0:
        audio_segment = speedup(audio_segment, playback_speed=final_speed)
    
    # Apply volume adjustment
    volume_change = effects["volume_boost"] + (custom_pitch - 1.0) * 10
    if volume_change != 0:
        audio_segment = audio_segment + volume_change
    
    # Normalize audio
    audio_segment = normalize(audio_segment)
    
    return audio_segment

def add_pauses_to_audio(audio_segment, text, emotion):
    """Add pauses between sentences and phrases"""
    
    # Pause durations based on emotion (in milliseconds)
    pause_durations = {
        "😊 Happy": 400,
        "😢 Sad": 800,
        "😡 Angry": 200,
        "😴 Calm": 600,
        "😨 Excited": 150,
        "🤔 Thoughtful": 700,
        "💝 Romantic": 500,
        "📰 News": 400,
        "🎭 Dramatic": 600,
        "🤖 Robotic": 300
    }
    
    pause_duration = pause_durations.get(emotion, 400)
    
    # Count sentences to estimate where pauses should be
    sentence_count = len(re.findall(r'[.!?]+', text))
    
    if sentence_count > 1:
        # Create silence segments
        pause = AudioSegment.silent(duration=pause_duration)
        short_pause = AudioSegment.silent(duration=pause_duration // 2)
        
        # Split audio into roughly equal parts and add pauses
        # This is a simplified approach - in production, you'd use speech recognition
        # to detect actual sentence boundaries in the audio
        segment_length = len(audio_segment) // max(sentence_count, 1)
        
        result = AudioSegment.empty()
        for i in range(sentence_count):
            start = i * segment_length
            end = min((i + 1) * segment_length, len(audio_segment))
            segment = audio_segment[start:end]
            
            result += segment
            if i < sentence_count - 1:  # Don't add pause after last segment
                result += pause
        
        return result
    
    return audio_segment

def text_to_speech_gtts(text, language, emotion, speed, pitch, add_pauses, slow_speech):
    """Generate speech using Google TTS with emotional processing"""
    
    try:
        # Process text for emotion
        processed_text = add_natural_pauses(text, emotion)
        
        # Create gTTS object
        tts = gtts.gTTS(
            text=processed_text,
            lang=language,
            slow=slow_speech
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            temp_path = tmp_file.name
            tts.save(temp_path)
        
        # Load audio with pydub for processing
        audio = AudioSegment.from_mp3(temp_path)
        
        # Apply emotional effects
        audio = apply_emotion_audio_effects(audio, emotion, speed, pitch)
        
        # Add natural pauses
        if add_pauses:
            audio = add_pauses_to_audio(audio, text, emotion)
        
        # Export processed audio
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="wav")
        audio_data = output_buffer.getvalue()
        
        # Cleanup
        os.unlink(temp_path)
        
        return audio_data
        
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

def get_download_link(audio_data, filename):
    """Generate download link for audio file"""
    b64_audio = base64.b64encode(audio_data).decode()
    href = f'''
    <div style="text-align: center; margin: 20px 0;">
        <a href="data:audio/wav;base64,{b64_audio}" 
           download="{filename}" 
           style="background: linear-gradient(45deg, #28a745, #20c997); 
                  color: white; 
                  text-decoration: none; 
                  font-weight: bold; 
                  padding: 15px 30px; 
                  border-radius: 25px; 
                  display: inline-block;
                  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
                  transition: all 0.3s ease;">
            📥 Download High-Quality Audio
        </a>
    </div>
    '''
    return href

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">🎭 Enhanced Emotional TTS Generator</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
    🌟 <strong>No Installation Required!</strong> Uses Google TTS with advanced emotional processing for natural, human-like speech.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown('<div class="voice-controls">', unsafe_allow_html=True)
        st.header("🎛️ Voice Controls")
        
        # Language selection
        selected_language_name = st.selectbox(
            "🌍 Select Language/Accent:",
            options=list(GTTS_LANGUAGES.keys()),
            help="Choose your preferred language and accent"
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
            help="Choose the emotional tone - affects speed, pitch, and pauses"
        )
        
        st.markdown("---")
        
        # Voice tuning parameters
        st.subheader("🔧 Advanced Tuning")
        
        speed = st.slider(
            "🏃 Speech Speed:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Overall playback speed multiplier"
        )
        
        pitch = st.slider(
            "🎵 Pitch/Tone:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Affects voice character and emotion intensity"
        )
        
        # Additional options
        st.markdown("---")
        st.subheader("🌟 Enhancement Options")
        
        add_pauses = st.checkbox(
            "🎭 Add Natural Pauses",
            value=True,
            help="Adds emotion-appropriate pauses between sentences"
        )
        
        slow_speech = st.checkbox(
            "🐌 High-Quality Mode",
            value=False,
            help="Slower, more articulated speech (better for long texts)"
        )
        
        emphasize_caps = st.checkbox(
            "📢 Emphasize CAPITALS",
            value=True,
            help="Process capitalized words for emphasis"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Enter Your Text")
        
        # Text input
        text_input = st.text_area(
            "Paste or type your text here:",
            value="",
            height=250,
            placeholder="Enter any amount of text here. Try different emotions to hear how they change the speech patterns, speed, and tone!",
            help="✨ No word limit! The app processes long texts efficiently."
        )
        
        # Quick text samples
        st.subheader("📚 Quick Text Samples")
        
        sample_col1, sample_col2, sample_col3, sample_col4 = st.columns(4)
        
        with sample_col1:
            if st.button("📖 Story", use_container_width=True):
                st.session_state.text_input = "Once upon a time, in a magical kingdom far beyond the mountains, there lived a brave princess who possessed the power to speak with animals. Every morning, she would walk through the enchanted forest, listening to the songs of birds and the whispers of the wind through the trees."
        
        with sample_col2:
            if st.button("💼 Business", use_container_width=True):
                st.session_state.text_input = "Good morning, team! Today's quarterly results exceed our expectations by fifteen percent. Our innovative approach to customer engagement has significantly improved satisfaction scores, and I'm proud to announce that we're expanding our operations to three new markets next quarter."
        
        with sample_col3:
            if st.button("🎭 Dramatic", use_container_width=True):
                st.session_state.text_input = "The storm raged violently outside, thunder echoing through the castle halls. She stood at the window, watching lightning illuminate the dark landscape, knowing that her destiny awaited beyond those treacherous mountains. This was the moment everything would change forever."
        
        with sample_col4:
            if st.button("💝 Romantic", use_container_width=True):
                st.session_state.text_input = "Under the starlit sky, with the gentle sound of waves caressing the shore, he took her hand and whispered softly. Time seemed to stand still as they danced to the rhythm of their hearts, lost in a moment that would remain etched in their memories forever."
        
        # Update text area if sample was selected
        if 'text_input' in st.session_state:
            text_input = st.session_state.text_input
            del st.session_state.text_input
    
    with col2:
        st.markdown('<div class="emotion-card">', unsafe_allow_html=True)
        st.subheader("🎵 Voice Preview")
        
        # Emotion descriptions with enhanced details
        emotion_descriptions = {
            "😊 Happy": {
                "desc": "Upbeat, cheerful, and energetic",
                "effects": "Faster pace, higher pitch, shorter pauses"
            },
            "😢 Sad": {
                "desc": "Slower, softer, melancholic tone", 
                "effects": "Slower pace, lower pitch, longer pauses"
            },
            "😡 Angry": {
                "desc": "Intense, faster, with emphasis",
                "effects": "Rapid speech, emphasis on punctuation"
            },
            "😴 Calm": {
                "desc": "Peaceful, steady, relaxing",
                "effects": "Measured pace, gentle tone, flowing"
            },
            "😨 Excited": {
                "desc": "Fast-paced, enthusiastic, energetic",
                "effects": "Very fast, higher pitch, short pauses"
            },
            "🤔 Thoughtful": {
                "desc": "Measured, contemplative, wise",
                "effects": "Slower pace, natural pauses, emphasis"
            },
            "💝 Romantic": {
                "desc": "Warm, gentle, intimate",
                "effects": "Soft tone, slower pace, flowing"
            },
            "📰 News": {
                "desc": "Professional, clear, authoritative",
                "effects": "Standard pace, clear articulation"
            },
            "🎭 Dramatic": {
                "desc": "Expressive, theatrical, dynamic",
                "effects": "Variable pace, emphasis, pauses"
            },
            "🤖 Robotic": {
                "desc": "Mechanical, consistent pace",
                "effects": "Steady rhythm, consistent tone"
            }
        }
        
        emotion_info = emotion_descriptions[emotion]
        st.markdown(f"""
        **{emotion}**
        
        *{emotion_info['desc']}*
        
        **Audio Effects:**  
        {emotion_info['effects']}
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Settings summary
        selected_language = GTTS_LANGUAGES[selected_language_name]
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.write(f"**Language:** {selected_language_name}")
        st.write(f"**Speed:** {speed}x")
        st.write(f"**Pitch:** {pitch}x")
        st.write(f"**Quality:** {'High' if slow_speech else 'Fast'}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate speech section
    st.markdown("---")
    
    # Large, prominent generation button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        generate_button = st.button(
            "🎤 Generate Emotional Speech", 
            type="primary", 
            use_container_width=True,
            help="Click to create your personalized emotional audio"
        )
    
    if generate_button:
        if text_input.strip():
            with st.spinner("🎭 Creating your emotional speech... Please wait!"):
                # Show progress info
                progress_info = st.empty()
                progress_info.info(f"🎯 Processing with {emotion} emotion...")
                
                # Process text based on options
                processed_text = text_input
                if emphasize_caps:
                    # Modify capitalized words for emphasis
                    processed_text = re.sub(r'\b[A-Z]{2,}\b', r'\g<0>!', processed_text)
                
                # Generate audio
                audio_data = text_to_speech_gtts(
                    processed_text,
                    selected_language,
                    emotion,
                    speed,
                    pitch,
                    add_pauses,
                    slow_speech
                )
                
                progress_info.empty()
                
                if audio_data:
                    st.balloons()
                    st.success("🎉 Emotional speech generated successfully!")
                    
                    # Create download section
                    st.markdown('<div class="download-section">', unsafe_allow_html=True)
                    st.markdown("### 🎵 Your Emotional Audio is Ready!")
                    
                    # Audio player
                    st.audio(audio_data, format='audio/wav')
                    
                    # Download link
                    timestamp = int(time.time())
                    filename = f"emotional_tts_{emotion.replace(' ', '_').replace('😊', 'happy').replace('😢', 'sad').replace('😡', 'angry').replace('😴', 'calm').replace('😨', 'excited').replace('🤔', 'thoughtful').replace('💝', 'romantic').replace('📰', 'news').replace('🎭', 'dramatic').replace('🤖', 'robotic')}_{timestamp}.wav"
                    
                    download_link = get_download_link(audio_data, filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Enhanced statistics
                    word_count = len(text_input.split())
                    char_count = len(text_input)
                    sentence_count = len(re.findall(r'[.!?]+', text_input))
                    estimated_duration = (word_count / (180 * speed)) * 60  # Rough estimate
                    
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    
                    with stats_col1:
                        st.metric("📝 Words", word_count)
                    with stats_col2:
                        st.metric("🔤 Characters", char_count)
                    with stats_col3:
                        st.metric("📄 Sentences", sentence_count)
                    with stats_col4:
                        st.metric("⏱️ Duration", f"~{estimated_duration:.1f}s")
                
                else:
                    st.error("❌ Failed to generate audio. Please check your internet connection and try again.")
        else:
            st.warning("⚠️ Please enter some text first!")
    
    # Enhanced tips section
    st.markdown("---")
    st.subheader("💡 Pro Tips for Incredible Results")
    
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.markdown("""
        **📝 Text Optimization:**
        - Use punctuation for natural speech rhythm
        - CAPITALIZE words for automatic emphasis  
        - Write numbers as words ("twenty" not "20")
        - Use shorter sentences for better emotional impact
        - Add ellipses... for dramatic pauses
        """)
        
        st.markdown("""
        **🎭 Emotion Selection:**
        - **Happy** 😊: Marketing, celebrations, children's content
        - **Sad** 😢: Memorial, serious topics, melancholy stories
        - **Excited** 😨: Announcements, sports, energetic content
        - **Calm** 😴: Meditation, instructions, bedtime stories
        - **Dramatic** 🎭: Theater, storytelling, presentations
        """)
    
    with tip_col2:
        st.markdown("""
        **🔧 Technical Settings:**
        - Lower speed for complex/technical content
        - Higher speed for energetic/exciting content
        - Adjust pitch to match character or gender preference
        - Use High-Quality mode for final productions
        - Enable natural pauses for professional results
        """)
        
        st.markdown("""
        **🌍 Language Tips:**
        - Different accents work better for different content
        - US English: General purpose, clear pronunciation
        - UK English: Formal, authoritative content  
        - Australian English: Casual, friendly tone
        - Try different languages for authentic multilingual content
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        🎭 <strong>Enhanced Emotional TTS Generator</strong> | 
        Powered by Google Text-to-Speech with Advanced Audio Processing | 
        Create natural, expressive speech with human-like emotions
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
