import streamlit as st
import requests
import base64
import os
from datetime import datetime
from gtts import gTTS

st.set_page_config(page_title="Mesta AI", page_icon="✨", layout="wide")

# ============================================================
# SIMPLE CSS
# ============================================================
st.markdown("""
<style>
.stApp { background: #f8fafc; }
.user-bubble {
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    color: white;
    padding: 10px 16px;
    border-radius: 18px;
    margin: 8px 0;
    margin-left: auto;
    max-width: 75%;
    text-align: right;
}
.ai-bubble {
    background: white;
    border: 1px solid #ddd;
    padding: 10px 16px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 75%;
}
.msg-time { font-size: 0.6rem; color: #888; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("✨ Mesta AI")
st.caption("Intelligent Assistant")

# ============================================================
# API CONFIG
# ============================================================
MISTRAL_API_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================
# FUNCTIONS
# ============================================================
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

def text_to_speech(text):
    """Convert text to speech and return audio HTML"""
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        audio_file = "temp_speech.mp3"
        tts.save(audio_file)
        
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}"></audio>'
        
        try:
            os.remove(audio_file)
        except:
            pass
        
        return audio_html
    except Exception as e:
        return ""

# ============================================================
# INPUT
# ============================================================
user_input = st.text_input("", placeholder="Ask Mesta anything...", key="user_input", label_visibility="collapsed")

col1, col2 = st.columns([1, 4])
with col1:
    ask_clicked = st.button("🔊 Ask", type="primary", use_container_width=True)
with col2:
    clear_clicked = st.button("🗑️ Clear", use_container_width=True)

if ask_clicked and user_input:
    with st.spinner("✨ Thinking..."):
        answer = ask_mistral(user_input)
        st.session_state.chat_history.append({
            "q": user_input,
            "a": answer,
            "t": datetime.now().strftime("%I:%M %p")
        })
        # Play voice
        audio_html = text_to_speech(answer)
        if audio_html:
            st.markdown(audio_html, unsafe_allow_html=True)
        st.rerun()

if clear_clicked:
    st.session_state.chat_history = []
    st.rerun()

# ============================================================
# QUICK QUESTIONS
# ============================================================
st.divider()
st.markdown("### 🔥 Quick Questions")

quick_qs = ["Who are you?", "What can you do?", "Tell me a joke", "Future of AI"]

cols = st.columns(4)
for i, q in enumerate(quick_qs):
    with cols[i]:
        if st.button(q, use_container_width=True):
            with st.spinner("✨ Thinking..."):
                answer = ask_mistral(q)
                st.session_state.chat_history.append({
                    "q": q,
                    "a": answer,
                    "t": datetime.now().strftime("%I:%M %p")
                })
                audio_html = text_to_speech(answer)
                if audio_html:
                    st.markdown(audio_html, unsafe_allow_html=True)
                st.rerun()

# ============================================================
# CHAT HISTORY
# ============================================================
if st.session_state.chat_history:
    st.divider()
    st.markdown("### 💬 Conversation")
    
    for chat in reversed(st.session_state.chat_history[-15:]):
        st.markdown(f'<div class="user-bubble"><strong>You</strong><br>{chat["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-bubble"><strong>✨ Mesta</strong><br>{chat["a"]}<div class="msg-time">{chat["t"]}</div></div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("✨ Mesta AI · Created by Nirbhay · Powered by Mistral AI")