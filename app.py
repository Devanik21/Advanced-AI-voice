import streamlit as st
from gtts import gTTS
import os

st.title("🎙️ AI Text-to-Speech (gTTS) App")
st.write("Paste your text below and generate a downloadable MP3 voice file.")

# Text input
text_input = st.text_area("Enter your text here:", height=200)

# Generate voice button
if st.button("Generate Voice"):
    if text_input.strip():
        tts = gTTS(text_input, lang='en')
        tts.save("output.mp3")

        # Download button
        with open("output.mp3", "rb") as file:
            st.download_button(
                label="⬇️ Download Voice",
                data=file,
                file_name="speech.mp3",
                mime="audio/mp3"
            )
        st.audio("output.mp3", format="audio/mp3")
    else:
        st.warning("Please enter some text first.")
