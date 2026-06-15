import streamlit as st
import requests
import base64
from datetime import datetime
from gtts import gTTS
import io

st.set_page_config(page_title="Mesta AI", page_icon="✨")

st.title("✨ Mesta AI")
st.caption("Intelligent Assistant")

# API Config
MISTRAL_API_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

if "history" not in st.session_state:
    st.session_state.history = []

def ask_mistral(question):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 200
    }
    try:
        response = requests.post(MISTRAL_URL, json=data, headers=headers, timeout=15)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Connection issue. Please try again."

def speak(text):
    """Convert text to speech and play"""
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()
        b64 = base64.b64encode(audio_bytes).decode()
        return f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}"></audio>'
    except:
        return ""

# Input
user_input = st.text_input("Ask Mesta anything...", key="input")

col1, col2 = st.columns(2)
with col1:
    if st.button("Ask", type="primary", use_container_width=True):
        if user_input:
            with st.spinner("Thinking..."):
                answer = ask_mistral(user_input)
                st.session_state.history.append({
                    "q": user_input,
                    "a": answer,
                    "t": datetime.now().strftime("%I:%M %p")
                })
                audio_html = speak(answer)
                if audio_html:
                    st.markdown(audio_html, unsafe_allow_html=True)
                st.rerun()

with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# Quick Questions
st.divider()
st.markdown("### Quick Questions")

quick_qs = ["Who are you?", "What can you do?", "Tell me a joke", "Future of AI"]

cols = st.columns(4)
for i, q in enumerate(quick_qs):
    with cols[i]:
        if st.button(q, use_container_width=True):
            with st.spinner("Thinking..."):
                answer = ask_mistral(q)
                st.session_state.history.append({
                    "q": q,
                    "a": answer,
                    "t": datetime.now().strftime("%I:%M %p")
                })
                audio_html = speak(answer)
                if audio_html:
                    st.markdown(audio_html, unsafe_allow_html=True)
                st.rerun()

# History
if st.session_state.history:
    st.divider()
    st.markdown("### Conversation")
    
    for chat in reversed(st.session_state.history[-15:]):
        st.markdown(f"**You:** {chat['q']}")
        st.markdown(f"**Mesta:** {chat['a']}")
        st.markdown(f"*{chat['t']}*")
        st.markdown("---")

st.divider()
st.caption("Mesta AI · Created by Nirbhay")