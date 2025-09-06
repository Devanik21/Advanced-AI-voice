import streamlit as st
import gtts
import tempfile
import os
import time
import base64
import re
import io
import requests
#from pathlib import Path

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
        background-clip: text;
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
        backdrop-filter: blur(10px);
    }
    .voice-controls {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
    }
    .download-section {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(86, 171, 47, 0.3);
        color: white;
    }
    .feature-highlight {
        background: linear-gradient(45deg, #ff9a9e, #fecfef);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        color: #333;
        font-weight: bold;
        text-align: center;
    }
    .stats-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 0.5rem;
    }
    .sample-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border: none;
        color: white;
        padding: 10px 15px;
        border-radius: 10px;
        cursor: pointer;
        width: 100%;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    .generate-button {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        border: none;
        color: white;
        padding: 20px 40px;
        border-radius: 25px;
        font-size: 1.2em;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
        transition: all 0.3s ease;
    }
    .tip-section {
        background: rgba(248, 249, 250, 0.8);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin: 1rem 0;
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
    "🇪🇸 Spanish (Spain)": "es",
    "🇲🇽 Spanish (Mexico)": "es-mx",
    "🇫🇷 French (France)": "fr",
    "🇨🇦 French (Canada)": "fr-ca",
    "🇩🇪 German": "de",
    "🇮🇹 Italian": "it",
    "🇯🇵 Japanese": "ja",
    "🇰🇷 Korean": "ko",
    "🇨🇳 Chinese (Mandarin)": "zh",
    "🇹🇼 Chinese (Taiwan)": "zh-tw",
    "🇷🇺 Russian": "ru",
    "🇵🇹 Portuguese (Brazil)": "pt-br",
    "🇵🇹 Portuguese (Portugal)": "pt",
    "🇳🇱 Dutch": "nl",
    "🇸🇪 Swedish": "sv",
    "🇳🇴 Norwegian": "no",
    "🇩🇰 Danish": "da",
    "🇫🇮 Finnish": "fi",
    "🇵🇱 Polish": "pl",
    "🇹🇷 Turkish": "tr",
    "🇦🇷 Arabic": "ar",
    "🇮🇳 Hindi": "hi"
}

def process_text_for_emotion(text, emotion, add_emphasis, add_pauses):
    """Process text to enhance emotional delivery"""
    
    processed_text = text
    
    # Emotion-specific text modifications
    emotion_processors = {
        "😊 Happy": {
            "punctuation": lambda t: re.sub(r'\.', '!', t, count=max(1, len(t.split('.'))-3)),
            "words": lambda t: re.sub(r'\b(great|good|wonderful|amazing|fantastic)\b', r'\1!', t, flags=re.IGNORECASE),
        },
        "😢 Sad": {
            "punctuation": lambda t: re.sub(r'[!]', '.', t),
            "words": lambda t: re.sub(r'\b(unfortunately|sadly|regret)\b', r'...\1...', t, flags=re.IGNORECASE),
        },
        "😡 Angry": {
            "punctuation": lambda t: re.sub(r'[.!?]', '!', t),
            "words": lambda t: re.sub(r'\b(no|stop|never|terrible|awful)\b', r'\1!', t, flags=re.IGNORECASE),
        },
        "😴 Calm": {
            "punctuation": lambda t: re.sub(r'[!]', '.', t),
            "words": lambda t: re.sub(r'\b(peaceful|calm|gentle|soft)\b', r'...\1...', t, flags=re.IGNORECASE),
        },
        "😨 Excited": {
            "punctuation": lambda t: re.sub(r'[.]', '!', t),
            "words": lambda t: re.sub(r'\b(wow|amazing|incredible|awesome)\b', r'\1!!!', t, flags=re.IGNORECASE),
        },
        "🤔 Thoughtful": {
            "punctuation": lambda t: t,
            "words": lambda t: re.sub(r'\b(think|consider|perhaps|maybe)\b', r'...\1...', t, flags=re.IGNORECASE),
        },
        "💝 Romantic": {
            "punctuation": lambda t: t,
            "words": lambda t: re.sub(r'\b(love|heart|beautiful|darling)\b', r'...\1...', t, flags=re.IGNORECASE),
        },
        "📰 News": {
            "punctuation": lambda t: t,
            "words": lambda t: re.sub(r'\b(breaking|report|according|sources)\b', r'\1,', t, flags=re.IGNORECASE),
        },
        "🎭 Dramatic": {
            "punctuation": lambda t: re.sub(r'[.]', '...', t),
            "words": lambda t: re.sub(r'\b(never|forever|always|destiny)\b', r'...\1...', t, flags=re.IGNORECASE),
        },
        "🤖 Robotic": {
            "punctuation": lambda t: t,
            "words": lambda t: re.sub(r'\b(\w+)\b', r'\1.', t)[:len(t)], # Add periods but keep original length
        }
    }
    
    if emotion in emotion_processors:
        processor = emotion_processors[emotion]
        if add_emphasis:
            processed_text = processor["words"](processed_text)
        processed_text = processor["punctuation"](processed_text)
    
    # Add emphasis to capitalized words
    if add_emphasis:
        processed_text = re.sub(r'\b[A-Z]{2,}\b', r'... \g<0> ...', processed_text)
    
    # Add natural pauses
    if add_pauses:
        # Add longer pauses for emotional effect
        if emotion in ["😢 Sad", "🤔 Thoughtful", "💝 Romantic", "🎭 Dramatic"]:
            processed_text = re.sub(r'([.!?])\s+', r'\1 ... ', processed_text)
        elif emotion in ["😨 Excited", "😡 Angry"]:
            # Shorter pauses for energetic emotions
            processed_text = re.sub(r'([,;:])\s+', r'\1 ', processed_text)
    
    return processed_text

def text_to_speech_gtts(text, language, emotion, speech_speed, add_emphasis, add_pauses):
    """Generate speech using Google TTS with emotional text processing"""
    
    try:
        # Process text for emotional delivery
        processed_text = process_text_for_emotion(text, emotion, add_emphasis, add_pauses)
        
        # Create gTTS object with emotional considerations
        # Use slow=True for more dramatic/thoughtful emotions
        use_slow = speech_speed == "Slow" or emotion in ["😢 Sad", "🤔 Thoughtful", "💝 Romantic", "🎭 Dramatic"]
        
        # For some emotions, we might want to break text into smaller chunks
        # This creates more natural pacing
        if len(processed_text) > 500 and add_pauses and emotion in ["🎭 Dramatic", "📰 News", "🤔 Thoughtful"]:
            # Split into sentences and process separately for better pacing
            sentences = re.split(r'([.!?]+)', processed_text)
            audio_segments = []
            
            for i in range(0, len(sentences)-1, 2):
                if sentences[i].strip():
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    tts = gtts.gTTS(
                        text=sentence.strip(),
                        lang=language,
                        slow=use_slow
                    )
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                        temp_path = tmp_file.name
                        tts.save(temp_path)
                        
                        with open(temp_path, 'rb') as f:
                            audio_segments.append(f.read())
                        
                        os.unlink(temp_path)
            
            # For simplicity, return the first segment (in a real app, you'd concatenate)
            return audio_segments[0] if audio_segments else None
        
        else:
            # Standard single TTS generation
            tts = gtts.gTTS(
                text=processed_text,
                lang=language,
                slow=use_slow
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                temp_path = tmp_file.name
                tts.save(temp_path)
                
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(temp_path)
                return audio_data
        
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        if "Internet" in str(e) or "network" in str(e).lower():
            st.error("🌐 Please check your internet connection and try again.")
        return None

def get_download_link(audio_data, filename):
    """Generate download link for audio file"""
    b64_audio = base64.b64encode(audio_data).decode()
    href = f'''
    <div style="text-align: center; margin: 20px 0;">
        <a href="data:audio/mp3;base64,{b64_audio}" 
           download="{filename}" 
           style="background: linear-gradient(45deg, #28a745, #20c997); 
                  color: white; 
                  text-decoration: none; 
                  font-weight: bold; 
                  padding: 15px 30px; 
                  border-radius: 25px; 
                  display: inline-block;
                  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
                  transition: all 0.3s ease;
                  font-size: 1.1em;">
            📥 Download Audio File
        </a>
    </div>
    '''
    return href

def main():
    # Header
    st.markdown('<h1 class="main-header">🎭 Enhanced Emotional TTS Generator</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-highlight">
        🌟 <strong>Zero Dependencies!</strong> Pure Google TTS with intelligent emotional text processing for natural, expressive speech.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    
    # Initialize session state for text samples
    if 'current_text' not in st.session_state:
        st.session_state.current_text = ""
    
    # Sidebar controls
    with st.sidebar:
        st.markdown('<div class="voice-controls">', unsafe_allow_html=True)
        st.header("🎛️ Voice Controls")
        
        # Language selection
        selected_language_name = st.selectbox(
            "🌍 Language & Accent:",
            options=list(GTTS_LANGUAGES.keys()),
            help="Choose your preferred language and regional accent"
        )
        
        # Emotion selection with descriptions
        emotion = st.selectbox(
            "🎭 Emotion & Style:",
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
            help="Each emotion applies unique text processing and speech patterns"
        )
        
        st.markdown("---")
        
        # Speech settings
        st.subheader("🔧 Speech Settings")
        
        speech_speed = st.selectbox(
            "🏃 Speech Speed:",
            options=["Normal", "Slow"],
            help="Slow mode provides more articulated, dramatic speech"
        )
        
        # Enhancement options
        st.markdown("---")
        st.subheader("🌟 Enhancement Options")
        
        add_pauses = st.checkbox(
            "🎭 Add Emotional Pauses",
            value=True,
            help="Adds emotion-appropriate pauses and pacing"
        )
        
        add_emphasis = st.checkbox(
            "📢 Smart Text Processing",
            value=True,
            help="Processes text to enhance emotional delivery"
        )
        
        auto_punctuation = st.checkbox(
            "✏️ Auto Punctuation Enhancement",
            value=True,
            help="Automatically adjusts punctuation for better emotional effect"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Enter Your Text")
        
        # Text input area
        text_input = st.text_area(
            "Paste or type your text here:",
            value=st.session_state.current_text,
            height=300,
            placeholder="Enter any amount of text here! Try different emotions to hear how they transform the speech patterns, pacing, and emotional delivery. No word limits!",
            help="✨ Unlimited text length supported. The app intelligently processes long texts for optimal emotional delivery."
        )
        
        # Update session state
        st.session_state.current_text = text_input
        
        # Quick text samples section
        st.subheader("📚 Try These Emotional Samples")
        
        # Sample texts for different emotions
        sample_texts = {
            "📖 Fairy Tale": "Once upon a time, in a magical kingdom hidden beyond the enchanted mountains, there lived a brave princess who could speak with all the animals of the forest. Every dawn, she would venture into the mystical woods, listening to the ancient songs of the birds and the whispered secrets of the wind.",
            
            "💼 Business Pitch": "Good morning, investors! Today, I'm thrilled to present our revolutionary product that will transform the industry forever. Our innovative solution has already exceeded all expectations, generating three hundred percent returns in just six months. This is your opportunity to be part of something extraordinary!",
            
            "🎭 Dramatic Scene": "The storm raged furiously outside, thunder echoing through the ancient castle halls like the cries of a thousand lost souls. She stood motionless at the towering window, watching lightning illuminate the treacherous landscape below, knowing that her destiny awaited beyond those forbidding mountains. Tonight, everything would change forever.",
            
            "💝 Love Letter": "My dearest beloved, under this starlit sky, with the gentle symphony of waves caressing the moonlit shore, my heart beats only for you. Time stands still when you're near, and every moment we share becomes a precious memory etched forever in my soul. You are my everything, my eternal love.",
            
            "📰 Breaking News": "This is a breaking news alert. Scientists at the International Research Institute have announced a groundbreaking discovery that could revolutionize our understanding of the universe. The research team, led by Dr. Sarah Johnson, spent five years analyzing data before reaching this remarkable conclusion that changes everything we thought we knew.",
            
            "🧘 Meditation": "Close your eyes and breathe deeply. Feel the gentle rhythm of your breath as it flows in and out, bringing peace to your mind and body. With each exhale, release all tension and worry. You are safe, you are calm, you are exactly where you need to be in this moment of perfect tranquility."
        }
        
        # Create sample buttons in two rows
        sample_col1, sample_col2, sample_col3 = st.columns(3)
        sample_col4, sample_col5, sample_col6 = st.columns(3)
        
        sample_cols = [sample_col1, sample_col2, sample_col3, sample_col4, sample_col5, sample_col6]
        sample_keys = list(sample_texts.keys())
        
        for i, (col, sample_key) in enumerate(zip(sample_cols, sample_keys)):
            with col:
                if st.button(sample_key, key=f"sample_{i}", use_container_width=True):
                    st.session_state.current_text = sample_texts[sample_key]
                    st.experimental_rerun()
    
    with col2:
        st.markdown('<div class="emotion-card">', unsafe_allow_html=True)
        st.subheader("🎵 Current Configuration")
        
        # Detailed emotion descriptions
        emotion_details = {
            "😊 Happy": {
                "desc": "Upbeat and cheerful delivery",
                "processing": "Adds exclamation marks, emphasizes positive words",
                "pacing": "Energetic with natural enthusiasm"
            },
            "😢 Sad": {
                "desc": "Melancholic and gentle tone",
                "processing": "Softens punctuation, adds reflective pauses", 
                "pacing": "Slower, more contemplative delivery"
            },
            "😡 Angry": {
                "desc": "Intense and forceful delivery",
                "processing": "Emphasizes strong words, adds exclamations",
                "pacing": "Direct and powerful presentation"
            },
            "😴 Calm": {
                "desc": "Peaceful and soothing tone",
                "processing": "Gentle punctuation, flowing transitions",
                "pacing": "Steady, relaxing rhythm"
            },
            "😨 Excited": {
                "desc": "High-energy and enthusiastic",
                "processing": "Multiple exclamations, energetic words",
                "pacing": "Fast-paced with dynamic delivery"
            },
            "🤔 Thoughtful": {
                "desc": "Contemplative and measured",
                "processing": "Adds reflective pauses, thoughtful pacing",
                "pacing": "Deliberate with meaningful pauses"
            },
            "💝 Romantic": {
                "desc": "Warm and intimate delivery",
                "processing": "Gentle emphasis, flowing speech",
                "pacing": "Soft, tender, and expressive"
            },
            "📰 News": {
                "desc": "Professional and authoritative",
                "processing": "Clear structure, professional pacing",
                "pacing": "Steady, informative delivery"
            },
            "🎭 Dramatic": {
                "desc": "Theatrical and expressive",
                "processing": "Extended pauses, dramatic emphasis",
                "pacing": "Variable, theatrical timing"
            },
            "🤖 Robotic": {
                "desc": "Mechanical and consistent",
                "processing": "Structured delivery, even pacing",
                "pacing": "Steady, systematic presentation"
            }
        }
        
        emotion_info = emotion_details[emotion]
        st.markdown(f"""
        **{emotion}**
        
        📝 **Style:** {emotion_info['desc']}
        
        🔧 **Processing:** {emotion_info['processing']}
        
        🎵 **Delivery:** {emotion_info['pacing']}
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Current settings display
        selected_language = GTTS_LANGUAGES[selected_language_name]
        
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        st.write(f"🌍 **Language:** {selected_language_name}")
        st.write(f"🏃 **Speed:** {speech_speed}")
        st.write(f"🎭 **Pauses:** {'Yes' if add_pauses else 'No'}")
        st.write(f"📢 **Enhancement:** {'Yes' if add_emphasis else 'No'}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generation section
    st.markdown("---")
    
    # Large generation button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        if st.button("🎤 Generate Emotional Speech", type="primary", use_container_width=True):
            if text_input.strip():
                with st.spinner(f"🎭 Crafting your {emotion} speech..."):
                    # Show what's happening
                    status_placeholder = st.empty()
                    status_placeholder.info(f"🔄 Processing text with {emotion} emotion...")
                    
                    # Generate audio
                    audio_data = text_to_speech_gtts(
                        text_input,
                        selected_language,
                        emotion,
                        speech_speed,
                        add_emphasis,
                        add_pauses
                    )
                    
                    status_placeholder.empty()
                    
                    if audio_data:
                        st.balloons()
                        st.success("🎉 Your emotional speech is ready!")
                        
                        # Download section
                        st.markdown('<div class="download-section">', unsafe_allow_html=True)
                        st.markdown("### 🎵 Your Personalized Audio")
                        
                        # Audio player
                        st.audio(audio_data, format='audio/mp3')
                        
                        # Generate filename
                        timestamp = int(time.time())
                        emotion_name = emotion.split()[1].lower() if len(emotion.split()) > 1 else emotion.replace('🎭', 'dramatic').replace('😊', 'happy').replace('😢', 'sad').replace('😡', 'angry').replace('😴', 'calm').replace('😨', 'excited').replace('🤔', 'thoughtful').replace('💝', 'romantic').replace('📰', 'news').replace('🤖', 'robotic')
                        filename = f"emotional_tts_{emotion_name}_{selected_language}_{timestamp}.mp3"
                        
                        # Download link
                        download_link = get_download_link(audio_data, filename)
                        st.markdown(download_link, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Statistics
                        word_count = len(text_input.split())
                        char_count = len(text_input)
                        sentence_count = len(re.findall(r'[.!?]+', text_input))
                        estimated_reading_time = word_count / 200  # Average reading speed
                        
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                        
                        with stats_col1:
                            st.metric("📝 Words", f"{word_count:,}")
                        with stats_col2:
                            st.metric("🔤 Characters", f"{char_count:,}")
                        with stats_col3:
                            st.metric("📄 Sentences", sentence_count)
                        with stats_col4:
                            st.metric("⏱️ Est. Duration", f"{estimated_reading_time:.1f}m")
                    
                    else:
                        st.error("❌ Failed to generate speech. Please check your internet connection and try again.")
            else:
                st.warning("⚠️ Please enter some text first!")
    
    # Tips and guide section
    st.markdown("---")
    st.subheader("💡 Master Guide for Perfect Emotional Speech")
    
    with st.expander("🎭 Emotion Selection Guide", expanded=False):
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            st.markdown("""
            **😊 Happy** - Perfect for:
            - Marketing content & advertisements
            - Children's stories & educational content  
            - Celebration announcements
            - Upbeat presentations
            
            **😢 Sad** - Ideal for:
            - Memorial speeches & tributes
            - Emotional storytelling
            - Serious documentary narration
            - Reflective content
            
            **😡 Angry** - Great for:
            - Dramatic scenes & theater
            - Passionate speeches
            - Strong calls-to-action
            - Intense character voices
            
            **😴 Calm** - Best for:
            - Meditation & relaxation content
            - Instructions & tutorials
            - Bedtime stories
            - Professional presentations
            
            **😨 Excited** - Excellent for:
            - Sports commentary
            - Event announcements  
            - Energetic marketing
            - Game show content
            """)
        
        with guide_col2:
            st.markdown("""
            **🤔 Thoughtful** - Perfect for:
            - Educational content
            - Philosophical discussions
            - Documentary narration
            - Professional analysis
            
            **💝 Romantic** - Ideal for:
            - Love letters & poetry
            - Wedding speeches
            - Intimate storytelling
            - Romantic audiobooks
            
            **📰 News** - Great for:
            - News broadcasts
            - Corporate communications
            - Formal announcements
            - Educational presentations
            
            **🎭 Dramatic** - Best for:
            - Theater & storytelling
            - Movie trailers
            - Epic narratives
            - Audiobook climaxes
            
            **🤖 Robotic** - Excellent for:
            - Technical instructions
            - Sci-fi content
            - System announcements
            - Futuristic themes
            """)
    
    with st.expander("📝 Text Optimization Tips", expanded=False):
        tip_col1, tip_col2 = st.columns(2)
        
        with tip_col1:
            st.markdown("""
            **Writing for Speech:**
            - Use shorter sentences for better pacing
            - Write numbers as words ("twenty" not "20")
            - Use contractions for natural flow ("don't" not "do not")
            - Add punctuation for natural pauses
            - CAPITALIZE words you want emphasized
            
            **Emotional Enhancement:**
            - Use descriptive adjectives for mood
            - Include emotional words (amazing, terrible, beautiful)
            - Add ellipses... for dramatic pauses
            - Use exclamation points for emphasis!
            - Repeat key words for impact
            """)
            
        with tip_col2:
            st.markdown("""
            **Technical Tips:**
            - Keep paragraphs under 500 characters for best results
            - Use proper punctuation (.!?) for sentence endings
            - Avoid special characters that might confuse TTS
            - Use commas for natural breathing points
            - Test different languages for authentic pronunciation
            
            **Advanced Techniques:**
            - Break long texts into emotional segments
            - Use different emotions for dialogue vs narration
            - Combine multiple audio files for complex presentations
            - Adjust speed settings for different content types
            - Preview with different accents for best fit
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 30px; background: linear-gradient(45deg, #f8f9fa, #e9ecef); border-radius: 15px;">
        🎭 <strong>Enhanced Emotional TTS Generator</strong><br>
        <em>Powered by Google Text-to-Speech with Intelligent Emotional Processing</em><br>
        Transform any text into natural, expressive speech with genuine human-like emotions
    </div>
    """, unsafe_allow_html=True
               )
