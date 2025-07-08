import streamlit as st

st.set_page_config( page_title = "Voice Assistant", layout = "wide")

# Libraries
import os
import time
import pyttsx3
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

# $env:GROQ_API_KEY="paste your api key here"

# loading the API key from local enviornment for safty purpose
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing API key in ENV")
    st.stop()

# Client to connect with Groq cloud
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# initializing speech recognizer
@st.cache_resource
def get_recognizer():
    return sr.Recognizer()

recognizer = get_recognizer()

# initializing text to speech engine
def get_tts_engine():
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        st.error("Failed to initialize the TTS Engine")
        return None
    
# function for speak
def speak(text, voice_gender = "girl"):
    try:
        engine = get_tts_engine()
        if engine is None:
            return
        
        voices = engine.getProperty("voices")
        if voices:
            if voice_gender == "boy":
                for voice in voices:
                    if "male" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            else:
                for voice in voices:
                    if "female" in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            
        engine.setProperty('rate', 200)
        engine.setProperty('volumn', 0.8)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        st.error(f"TTS error: {e}")

# help to listen from the microphone
def listen_to_speech():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration = 1)
            audio = recognizer.listen(source, phrase_time_limit=10)

        text = recognizer.recognize_google(audio)
        return text.lower()
    except sr.UnknownValueError:
        return "Sorry, I don't Catch You"
    except sr.RequestError:
        return "Speech service not available"
    except Exception as e:
        return f"Some Error occur: {e}"
    
# connect with LLM model through Groq Cloud
def get_ai_response(messages):
    try:
        response = client.chat.completions.create(
            model = MODEL,
            messages = messages,
            temperature=0.7,
        )

        result = response.choices[0].message.content
        return result.strip() if result else "Sorry, I could not generate a response"
    except Exception as e:
        return f"Error in getting AI response: {e}"
    
# Glue main code
def main():
    st.title("My Personal Voice Assistant")
    st.markdown("---")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "Reply like Brahmanandam, south indian hero. Reply only one line"}
            ]

    # Here We are creating streamlit session message list
    # This will help us to pass all previous messages to LLM for better reply
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("CONTROLS")

        tts_enabled = st.checkbox("Enable Text-to-Speech", value = True)

        voice_gender = st.selectbox(
            "Voice Gender",
            options = ["girl", "boy"],
            index = 1,
            help="Choose between girl or boy voice for your assistant"
        )

        if st.button("Start voice input", type = "primary", use_container_width=True):
            user_input = listen_to_speech()

            if user_input and user_input not in [ "Sorry, I don't Catch You", "Speech service not available" ]:
                st.session_state.messages.append({"role": "user", "content" : user_input })
                st.session_state.chat_history.append({"role" : "user", "content": user_input })

                # get AI reply
                with st.spinner("Thninking..."):
                    ai_response = get_ai_response(st.session_state.chat_history)
                    st.session_state.messages.append({"role": "user", "content" : ai_response })  # to pass conversation to LLM
                    st.session_state.chat_history.append({"role" : "user", "content": ai_response }) # for display data on screen

                # speak the reply if enbled
                if tts_enabled:
                    speak(ai_response, voice_gender)

                st.rerun()

        st.markdown("---")

        st.subheader("TEXT INPUT")
        user_text = st.text_input("Type your Message")

        if st.button("Send", type = "secondary", use_container_width=True) and user_text:
            st.session_state.messages.append({"role": "user", "content" : user_text })
            st.session_state.chat_history.append({"role" : "user", "content": user_text })

            # get AI reply
            with st.spinner("Thninking..."):
                ai_response = get_ai_response(st.session_state.chat_history)
                st.session_state.messages.append({"role": "user", "content" : ai_response })  # to pass conversation to LLM
                st.session_state.chat_history.append({"role" : "user", "content": ai_response })

            # speak the reply if enbled
            if tts_enabled:
                speak(ai_response, voice_gender)

            st.rerun()

        st.markdown("---")

        # Clear conversation
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = [
                            {"role": "system", "content": "Reply like Brahmanandam, south indian hero. Reply only one line"}
                        ]
            st.rerun()

    st.subheader("Conversation")

    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("Assistant"):
                st.write(message["content"])

    # Welcome message
    if not st.session_state.messages:
        st.info("WELCOME: Use the Voice Button to start the conversation")

    st.markdown("---")
    st.markdown(
        """
        <div style = "text-align: center">
        <p> Powered by GROQ and STREAMLIT * Copyright: Puneet Kansal</p>
        </div>
        """,
        unsafe_allow_html=True
    )
if __name__=="__main__":
    main()