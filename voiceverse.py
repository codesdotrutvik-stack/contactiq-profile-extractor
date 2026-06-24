import streamlit as st
import assemblyai as aai
import requests
import json
from gtts import gTTS
import io
import base64
import os
from datetime import datetime

# ============================================
# 🔑 API KEYS
# ============================================
ASSEMBLYAI_KEY = "5e874d691c74442f8b602827e6d26752"
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

aai.settings.api_key = ASSEMBLYAI_KEY
HISTORY_FILE = "voiceverse_history.json"

# ============================================
# 🧠 CORE FUNCTIONS
# ============================================
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        return []
    except:
        return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[-50:], f, indent=2)
    except:
        pass

def speech_to_text(audio_bytes):
    try:
        temp_file = "temp_voice_input.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(temp_file)
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return transcript.text if transcript.text else None
    except:
        return None

def detect_language(text):
    for char in text:
        cp = ord(char)
        if 0x0A80 <= cp <= 0x0AFF: return "gu"
        if 0x0900 <= cp <= 0x097F: return "hi"
        if 0x0600 <= cp <= 0x06FF: return "ar"
        if 0x0980 <= cp <= 0x09FF: return "bn"
        if 0x00C0 <= cp <= 0x00FF: return "pt"
    portuguese_words = ["você", "obrigado", "por favor", "bom dia", "tudo bem", "como", "está"]
    for word in portuguese_words:
        if word in text.lower():
            return "pt"
    return "en"

def get_ai_response(text, chat_history=None, callback=None):
    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_KEY}",
            "Content-Type": "application/json"
        }
        
        if st.session_state.selected_language == "auto":
            target_lang = detect_language(text)
        else:
            target_lang = st.session_state.selected_language
        
        lang_map = {
            "en": "English", "gu": "Gujarati", "hi": "Hindi",
            "ar": "Arabic", "bn": "Bengali", "pt": "Portuguese",
            "es": "Spanish", "fr": "French", "de": "German", "ja": "Japanese"
        }
        lang_name = lang_map.get(target_lang, "English")
        
        system_content = (
            f"You are a helpful conversational voice assistant. "
            f"CRITICAL: You MUST respond ONLY in {lang_name} language. "
            f"Keep response under 3 sentences. Do not use bullet points."
        )
        
        system_msg = {"role": "system", "content": system_content}
        history_msgs = chat_history[-50:] if chat_history else []
        messages = [system_msg] + history_msgs + [{"role": "user", "content": text}]
        
        data = {
            "model": "mistral-small-latest",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.2
        }
        
        if callback:
            callback("typing")
        
        response = requests.post(url, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            if callback:
                callback("done")
            return content
        else:
            if callback:
                callback("done")
            return "I am unable to capture the response. Please ask again."
    except:
        if callback:
            callback("done")
        return "I am unable to capture the response. Please ask again."

def text_to_speech(text):
    try:
        if st.session_state.selected_language != "auto":
            lang = st.session_state.selected_language
        else:
            lang = detect_language(text)
        
        supported_langs = ["en", "gu", "hi", "ar", "bn", "es", "fr", "de", "ja", "pt"]
        if lang not in supported_langs:
            lang = "en"
        
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except:
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except:
            return None

def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def export_history(conversation):
    if not conversation:
        return "No conversation history."
    lines = []
    for entry in conversation:
        lines.append(f"{entry.get('timestamp', '')} - You: {entry.get('user', '')}")
        lines.append(f"{entry.get('timestamp', '')} - AI: {entry.get('ai', '')}")
        lines.append("")
    return "\n".join(lines)

# ============================================
# 🗂️ SESSION STATE
# ============================================
if "conversation" not in st.session_state:
    st.session_state.conversation = load_history()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
    for entry in st.session_state.conversation:
        if entry.get("user"):
            st.session_state.chat_messages.append({"role": "user", "content": entry["user"]})
        if entry.get("ai"):
            st.session_state.chat_messages.append({"role": "assistant", "content": entry["ai"]})
if "current_user_text" not in st.session_state:
    st.session_state.current_user_text = ""
if "current_ai_text" not in st.session_state:
    st.session_state.current_ai_text = ""
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None
if "pending_audio_bytes" not in st.session_state:
    st.session_state.pending_audio_bytes = None
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "auto"
if "all_conversations" not in st.session_state:
    st.session_state.all_conversations = []

# ============================================
# 🔊 AUTOPLAY AUDIO
# ============================================
if st.session_state.pending_audio_bytes:
    autoplay_audio(st.session_state.pending_audio_bytes)
    st.session_state.pending_audio_bytes = None

# ============================================
# 🎨 UI SETUP
# ============================================
st.set_page_config(page_title="VoiceVerse Pro", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
}

.stApp {
    background: #080B14 !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(124,58,237,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 85% 110%, rgba(236,72,153,0.10) 0%, transparent 55%),
        radial-gradient(ellipse 50% 30% at 10% 90%, rgba(99,102,241,0.08) 0%, transparent 50%) !important;
    min-height: 100vh;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 0 1.5rem 3rem !important; max-width: 780px !important; }

/* ── HEADER ── */
.vv-header {
    text-align: center;
    padding: 2.6rem 0 0.8rem;
}
.vv-logo-ring {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 68px; height: 68px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6D28D9, #A855F7, #EC4899);
    box-shadow: 0 0 32px rgba(168,85,247,0.45), 0 0 80px rgba(168,85,247,0.15);
    margin-bottom: 1.1rem;
    font-size: 1.9rem;
    animation: halo-pulse 3s ease-in-out infinite;
}
@keyframes halo-pulse {
    0%,100% { box-shadow: 0 0 32px rgba(168,85,247,0.45), 0 0 80px rgba(168,85,247,0.15); }
    50%      { box-shadow: 0 0 52px rgba(168,85,247,0.65), 0 0 110px rgba(168,85,247,0.25); }
}
.vv-title {
    font-family: 'Sora', sans-serif !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #FFFFFF 0%, #C4B5FD 45%, #F0ABFC 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.8px;
    margin: 0 0 6px !important;
    line-height: 1.1;
}
.vv-subtitle {
    color: #4B5563 !important;
    font-size: 0.83rem;
    font-weight: 400;
    letter-spacing: 0.4px;
    margin: 0 !important;
}
.vv-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(124,58,237,0.1);
    border: 1px solid rgba(168,85,247,0.2);
    border-radius: 999px;
    padding: 5px 14px 5px 10px;
    font-size: 0.7rem;
    color: #A78BFA;
    font-weight: 600;
    margin-top: 14px;
    letter-spacing: 0.5px;
}
.vv-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 8px rgba(52,211,153,0.6);
    animation: dot-blink 2s ease-in-out infinite;
}
@keyframes dot-blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── CHAT CARD ── */
.chat-card {
    background: rgba(12, 18, 35, 0.75);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 28px;
    padding: 1.4rem 1.4rem 1.4rem;
    margin: 1.4rem 0 0.5rem;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    box-shadow:
        0 8px 40px rgba(0,0,0,0.5),
        0 1px 0 rgba(255,255,255,0.04) inset,
        0 -1px 0 rgba(99,102,241,0.08) inset;
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
}
.chat-messages-scroll {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    height: 440px;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0.4rem 0.3rem 0.4rem 0.3rem;
    scroll-behavior: smooth;
    scrollbar-width: thin;
    scrollbar-color: rgba(99,102,241,0.3) transparent;
}
.chat-messages-scroll::-webkit-scrollbar { width: 4px; }
.chat-messages-scroll::-webkit-scrollbar-track { background: transparent; }
.chat-messages-scroll::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.3);
    border-radius: 999px;
}
.chat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 36px;
    background: linear-gradient(to bottom, rgba(12,18,35,0.85), transparent);
    border-radius: 28px 28px 0 0;
    pointer-events: none;
    z-index: 2;
}
.chat-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 36px;
    background: linear-gradient(to top, rgba(12,18,35,0.85), transparent);
    border-radius: 0 0 28px 28px;
    pointer-events: none;
    z-index: 2;
}
.msg-time {
    font-size: 0.62rem;
    color: #1E293B;
    text-align: center;
    margin: 0.3rem 0 0.6rem;
    font-weight: 500;
    letter-spacing: 0.3px;
}
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
}
.empty-icon { font-size: 2.8rem; opacity: 0.3; display: block; margin-bottom: 0.7rem; }
.empty-text { color: #1E293B; font-size: 0.88rem; font-weight: 500; }

/* ── USER BUBBLE ── */
.user-bubble-wrap { display: flex; justify-content: flex-end; flex-direction: column; align-items: flex-end; }
.bubble-label-user {
    font-size: 0.67rem;
    color: rgba(167,139,250,0.6);
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 5px;
    padding-right: 4px;
}
.bubble-user {
    background: linear-gradient(135deg, #6D28D9 0%, #8B5CF6 50%, #A855F7 100%);
    color: #fff !important;
    padding: 0.95rem 1.3rem;
    border-radius: 22px 22px 5px 22px;
    max-width: 78%;
    font-size: 0.91rem;
    font-weight: 500;
    line-height: 1.6;
    box-shadow: 0 6px 24px rgba(109,40,217,0.45), 0 1px 0 rgba(255,255,255,0.12) inset;
    word-break: break-word;
}

/* ── AI BUBBLE ── */
.ai-bubble-wrap { display: flex; flex-direction: column; align-items: flex-start; max-width: 82%; }
.bubble-label-ai {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.67rem;
    color: #6D28D9;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 5px;
    padding-left: 2px;
}
.ai-dot {
    width: 18px; height: 18px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7C3AED, #EC4899);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem;
    box-shadow: 0 2px 8px rgba(124,58,237,0.5);
}
.bubble-ai {
    background: rgba(17, 24, 45, 0.95);
    border: 1px solid rgba(99,102,241,0.18);
    color: #CBD5E1 !important;
    padding: 1rem 1.3rem;
    border-radius: 5px 22px 22px 22px;
    font-size: 0.91rem;
    line-height: 1.7;
    word-break: break-word;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.03) inset;
    backdrop-filter: blur(12px);
}

/* ── TYPING INDICATOR ── */
.typing-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(17, 24, 45, 0.95);
    border: 1px solid rgba(99,102,241,0.18);
    padding: 0.7rem 1.2rem;
    border-radius: 20px 20px 4px 20px;
    color: #CBD5E1;
    font-size: 0.9rem;
    font-weight: 500;
    margin: 0.5rem 0;
}
.typing-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #A78BFA;
    border-radius: 50%;
    animation: typing-bounce 1.4s infinite both;
}
.typing-dot:nth-child(1) { animation-delay: 0s; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
    0%,80%,100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
}

/* ── MIC DIVIDER ── */
.mic-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.6rem 0 0.7rem;
}
.mic-divider-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.18), transparent);
}
.mic-divider-label {
    color: #2D3748;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    white-space: nowrap;
}

/* ── AUDIO INPUT ── */
div[data-testid="stAudioInput"] {
    background: rgba(12,18,35,0.88) !important;
    border: 1px solid rgba(99,102,241,0.22) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    box-shadow: 0 4px 28px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.02) inset !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    overflow: hidden !important;
}
div[data-testid="stAudioInput"]:focus-within {
    border-color: rgba(168,85,247,0.5) !important;
    box-shadow: 0 4px 28px rgba(0,0,0,0.4), 0 0 24px rgba(168,85,247,0.15) !important;
}
div[data-testid="stAudioInput"] > div,
div[data-testid="stAudioInput"] > div > div,
div[data-testid="stAudioInput"] > div > div > div {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

/* ── BUTTONS ── */
div[data-testid="stButton"] button {
    background: rgba(239,68,68,0.06) !important;
    border: 1px solid rgba(239,68,68,0.18) !important;
    color: #EF4444 !important;
    border-radius: 14px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.3px !important;
    width: 100% !important;
}
div[data-testid="stButton"] button:hover {
    background: rgba(239,68,68,0.12) !important;
    border-color: rgba(239,68,68,0.35) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(239,68,68,0.12) !important;
}
/* New Conversation button - Green */
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    border: 1px solid rgba(16,185,129,0.3) !important;
    color: #FFFFFF !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #059669, #047857) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(16,185,129,0.3) !important;
}
div[data-testid="stDownloadButton"] button {
    background: rgba(52,211,153,0.06) !important;
    border: 1px solid rgba(52,211,153,0.18) !important;
    color: #34D399 !important;
    border-radius: 14px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.3px !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background: rgba(52,211,153,0.12) !important;
    border-color: rgba(52,211,153,0.35) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(52,211,153,0.12) !important;
}

/* ── SIDEBAR DARK STYLES ── */
.css-1d391kg, .css-1d391kg p, .css-1d391kg div {
    color: #CBD5E1 !important;
    background: #0d1117 !important;
}
.css-1d391kg .stSelectbox label {
    color: #94A3B8 !important;
    font-weight: 600 !important;
}
.css-1d391kg .stSelectbox div {
    background: rgba(30,41,59,0.4) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 10px !important;
    color: #CBD5E1 !important;
}
.css-1d391kg .stMarkdown {
    color: #CBD5E1 !important;
}
.css-1d391kg .stButton button {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
    color: #A78BFA !important;
}
.css-1d391kg .stButton button:hover {
    background: rgba(99,102,241,0.2) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.25); border-radius: 999px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# 🏠 HEADER
# ============================================
st.markdown("""
<div class="vv-header">
    <div class="vv-logo-ring">🎙️</div><br>
    <div class="vv-title">VoiceVerse Pro</div>
    <div class="vv-subtitle">Conversational Voice Intelligence</div>
    <div><span class="vv-status-pill"><span class="vv-dot"></span>AI Online &nbsp;·&nbsp; Real-time</span></div>
</div>
""", unsafe_allow_html=True)

# ============================================
# 💬 CHAT WINDOW
# ============================================
def build_chat_html(conversation, current_user, current_ai):
    all_entries = []
    for entry in conversation:
        all_entries.append(entry)

    if not all_entries and not current_user:
        return """
        <div class="chat-card">
            <div class="empty-state">
                <span class="empty-icon">🎙️</span>
                <div class="empty-text">Tap the mic below to start talking</div>
            </div>
        </div>"""

    bubbles_html = ""
    for entry in all_entries:
        ts = entry.get('timestamp', '')
        u  = entry.get('user', '')
        a  = entry.get('ai', '')
        if ts:
            bubbles_html += f'<div class="msg-time">{ts}</div>'
        if u:
            bubbles_html += f"""
            <div class="user-bubble-wrap">
                <div class="bubble-label-user">You</div>
                <div class="bubble-user">{u}</div>
            </div>"""
        if a:
            bubbles_html += f"""
            <div class="ai-bubble-wrap">
                <div class="bubble-label-ai"><span class="ai-dot">✦</span>VoiceVerse AI</div>
                <div class="bubble-ai">{a}</div>
            </div>"""

    return f"""
    <div class="chat-card">
        <div class="chat-messages-scroll" id="chat-scroll-box">
            {bubbles_html}
        </div>
    </div>
    <script>
        setTimeout(function() {{
            var box = document.getElementById('chat-scroll-box');
            if (box) box.scrollTop = box.scrollHeight;
        }}, 100);
    </script>"""

st.markdown(build_chat_html(
    st.session_state.conversation,
    st.session_state.current_user_text,
    st.session_state.current_ai_text
), unsafe_allow_html=True)

# ============================================
# 🎤 MIC INPUT
# ============================================
st.markdown("""
<div class="mic-divider">
    <div class="mic-divider-line"></div>
    <div class="mic-divider-label">🎤 &nbsp;Speak</div>
    <div class="mic-divider-line"></div>
</div>
""", unsafe_allow_html=True)

audio_input = st.audio_input("Voice Input", key="voice_stream_bridge", label_visibility="collapsed")

# ============================================
# ⚡ PROCESSING
# ============================================
if audio_input is not None:
    audio_bytes = audio_input.getvalue()

    if st.session_state.last_processed_audio != audio_bytes:
        st.session_state.last_processed_audio = audio_bytes

        typing_placeholder = st.empty()

        with st.spinner("✦ Processing your voice..."):
            user_text = speech_to_text(audio_bytes)

            if user_text:
                def update_typing(status):
                    if status == "typing":
                        typing_placeholder.markdown("""
                        <div class="typing-indicator">
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                            <span style="margin-left: 4px;">AI is typing...</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        typing_placeholder.empty()

                ai_response = get_ai_response(user_text, st.session_state.chat_messages, update_typing)
                typing_placeholder.empty()
                ai_audio = text_to_speech(ai_response)

                st.session_state.chat_messages.append({"role": "user", "content": user_text})
                st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})

                st.session_state.current_user_text = user_text
                st.session_state.current_ai_text = ai_response

                entry = {
                    "timestamp": datetime.now().strftime("%I:%M %p"),
                    "user": user_text,
                    "ai": ai_response
                }
                st.session_state.conversation.append(entry)
                save_history(st.session_state.conversation)

                if ai_audio:
                    st.session_state.pending_audio_bytes = ai_audio

                st.rerun()
            else:
                typing_placeholder.empty()
                st.error("Could not detect voice. Please try again.")

# ============================================
# 📥 BUTTONS - Clear, New, Export
# ============================================
if st.session_state.conversation:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.conversation = []
            st.session_state.chat_messages = []
            st.session_state.current_user_text = ""
            st.session_state.current_ai_text = ""
            st.session_state.last_processed_audio = None
            st.session_state.pending_audio_bytes = None
            save_history([])
            st.rerun()
    with col2:
        # New Conversation button - Green color
        if st.button("✨ New Conversation", use_container_width=True, type="primary"):
            if st.session_state.conversation:
                st.session_state.all_conversations.append({
                    "timestamp": datetime.now().strftime("%I:%M %p, %d %b"),
                    "conversation": st.session_state.conversation.copy(),
                    "messages": st.session_state.chat_messages.copy()
                })
                st.session_state.conversation = []
                st.session_state.chat_messages = []
                st.session_state.current_user_text = ""
                st.session_state.current_ai_text = ""
                st.session_state.last_processed_audio = None
                st.session_state.pending_audio_bytes = None
                save_history([])
                st.rerun()
    with col3:
        if st.session_state.all_conversations or st.session_state.conversation:
            all_text = []
            if st.session_state.conversation:
                all_text.append("=== Current Conversation ===")
                for entry in st.session_state.conversation:
                    all_text.append(f"{entry.get('timestamp', '')} - You: {entry.get('user', '')}")
                    all_text.append(f"{entry.get('timestamp', '')} - AI: {entry.get('ai', '')}")
                    all_text.append("")
            if st.session_state.all_conversations:
                for idx, conv in enumerate(st.session_state.all_conversations):
                    all_text.append(f"\n=== Conversation {idx+1} ({conv.get('timestamp', '')}) ===")
                    for entry in conv.get('conversation', []):
                        all_text.append(f"{entry.get('timestamp', '')} - You: {entry.get('user', '')}")
                        all_text.append(f"{entry.get('timestamp', '')} - AI: {entry.get('ai', '')}")
                        all_text.append("")
            
            export_data = "\n".join(all_text)
            st.download_button(
                label="📥 Export All History",
                data=export_data,
                file_name=f"VoiceVerse_All_History_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ============================================
# 🎯 SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 🌐 Language Settings")
    
    lang_options = ["auto", "en", "gu", "hi", "ar", "bn", "pt", "es", "fr", "de", "ja"]
    lang_labels = {
        "auto": "🤖 Auto-detect",
        "en": "🇬🇧 English",
        "gu": "🇮🇳 Gujarati",
        "hi": "🇮🇳 Hindi",
        "ar": "🇸🇦 Arabic",
        "bn": "🇧🇩 Bengali",
        "pt": "🇵🇹 Portuguese",
        "es": "🇪🇸 Spanish",
        "fr": "🇫🇷 French",
        "de": "🇩🇪 German",
        "ja": "🇯🇵 Japanese"
    }
    
    selected_lang = st.selectbox(
        "Output Language",
        options=lang_options,
        format_func=lambda x: lang_labels.get(x, x),
        index=lang_options.index(st.session_state.selected_language)
    )
    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        # Language change: conversation stays, only language changes
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.caption(f"Total conversations: {len(st.session_state.conversation)}")
    st.caption(f"Saved conversations: {len(st.session_state.all_conversations)}")
    
    st.markdown("---")
    st.markdown("### 📜 Saved Conversations")
    if st.session_state.all_conversations:
        for idx, conv in enumerate(st.session_state.all_conversations):
            if st.button(f"📁 {idx+1}. {conv.get('timestamp', '')}", key=f"conv_{idx}", use_container_width=True):
                # Load saved conversation
                st.session_state.conversation = conv.get('conversation', [])
                st.session_state.chat_messages = conv.get('messages', [])
                if st.session_state.conversation:
                    last = st.session_state.conversation[-1]
                    st.session_state.current_user_text = last.get('user', '')
                    st.session_state.current_ai_text = last.get('ai', '')
                st.rerun()
    else:
        st.caption("No saved conversations yet.")
    
    st.markdown("---")
    st.markdown("### ❤️ About")
    st.caption("VoiceVerse Pro – Conversational Voice Intelligence")
    st.caption("Powered by AssemblyAI · Mistral AI · gTTS")