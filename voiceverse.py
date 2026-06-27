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
SAVED_HISTORY_FILE = "saved_conversations.json"

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

def load_saved_conversations():
    try:
        if os.path.exists(SAVED_HISTORY_FILE):
            with open(SAVED_HISTORY_FILE, "r") as f:
                return json.load(f)
        return []
    except:
        return []

def save_saved_conversations(conversations):
    try:
        with open(SAVED_HISTORY_FILE, "w") as f:
            # FIX: keep only last 5
            json.dump(conversations[-5:], f, indent=2)
    except:
        pass

# FIX: get preview text like Claude AI history
def get_preview(conversation):
    for entry in conversation:
        u = entry.get("user", "").strip()
        if u:
            words = u.split()
            preview = " ".join(words[:6])
            return preview + ("…" if len(words) > 6 else "")
    return "Conversation"

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
    st.markdown(f"""
        <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)

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
    st.session_state.all_conversations = load_saved_conversations()

# ============================================
# 🔊 AUTOPLAY AUDIO
# ============================================
if st.session_state.pending_audio_bytes:
    autoplay_audio(st.session_state.pending_audio_bytes)
    st.session_state.pending_audio_bytes = None

# ============================================
# 🎨 PAGE CONFIG
# ============================================
st.set_page_config(page_title="VoiceVerse Pro", page_icon="🎙️", layout="wide")

# ============================================
# 💅 CSS
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; -webkit-font-smoothing: antialiased; margin: 0; padding: 0; }

.stApp {
    background: #05070F !important;
    background-image:
        radial-gradient(ellipse 100% 60% at 50% 0%, rgba(109,40,217,0.20) 0%, transparent 65%),
        radial-gradient(ellipse 50% 40% at 90% 100%, rgba(236,72,153,0.09) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 5% 80%, rgba(79,70,229,0.06) 0%, transparent 50%) !important;
    min-height: 100vh;
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }

.block-container {
    padding: 0 2.5rem 4rem !important;
    max-width: 840px !important;
    margin: 0 auto !important;
}

[data-testid="stSidebar"] {
    background: rgba(7, 10, 22, 0.98) !important;
    border-right: 1px solid rgba(99,102,241,0.13) !important;
    backdrop-filter: blur(30px) !important;
    -webkit-backdrop-filter: blur(30px) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; background: transparent !important; }
[data-testid="stSidebar"] .stVerticalBlock { gap: 0 !important; }
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #8892A4 !important; margin-bottom: 1px; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] { padding: 0 1.4rem !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] label { color: #8892A4 !important; font-size: 0.75rem !important; font-weight: 600 !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(15, 21, 45, 0.85) !important;
    border: 1px solid rgba(99,102,241,0.22) !important;
    border-radius: 12px !important; color: #C4CFDE !important; font-size: 0.88rem !important;
}
[data-testid="stSidebar"] hr { border: none !important; border-top: 1px solid rgba(99,102,241,0.1) !important; margin: 0 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] { padding: 0 1.4rem !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: rgba(15, 21, 45, 0.7) !important;
    border: 1px solid rgba(99,102,241,0.14) !important;
    color: #C4CFDE !important;
    border-radius: 12px !important; font-size: 0.82rem !important; font-weight: 500 !important;
    padding: 0.65rem 1rem !important; transition: all 0.22s ease !important;
    text-align: left !important; width: 100% !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: rgba(79,70,229,0.14) !important;
    border-color: rgba(167,139,250,0.32) !important;
    color: #E2E8F0 !important; transform: translateX(4px) !important;
}

/* ── HEADER ── */
.vv-header { text-align: center; padding: 3rem 0 1.6rem; position: relative; }
.vv-header::before {
    content: ''; position: absolute; top: -20px; left: 50%; transform: translateX(-50%);
    width: 340px; height: 220px;
    background: radial-gradient(ellipse, rgba(109,40,217,0.14) 0%, transparent 70%);
    pointer-events: none; animation: orb-float 6s ease-in-out infinite;
}
@keyframes orb-float { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(-14px)} }

/* FIX: New logo — waveform bars in rounded square */
.vv-logo-container { position: relative; display: inline-block; margin-bottom: 1.5rem; }
.vv-orbit-ring {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 112px; height: 112px; border-radius: 50%;
    border: 1px dashed rgba(167,139,250,0.22);
    animation: ring-spin 14s linear infinite;
}
.vv-orbit-ring::before {
    content: ''; position: absolute; top: -4px; left: 50%;
    width: 8px; height: 8px; border-radius: 50%;
    background: #A78BFA; box-shadow: 0 0 10px rgba(167,139,250,0.9);
    transform: translateX(-50%);
}
@keyframes ring-spin { from{transform:translate(-50%,-50%) rotate(0deg)} to{transform:translate(-50%,-50%) rotate(360deg)} }

.vv-logo-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 78px; height: 78px; border-radius: 22px;
    background: linear-gradient(145deg, #0d1030, #1a1060);
    box-shadow: 0 0 0 1px rgba(167,139,250,0.3), 0 0 45px rgba(124,58,237,0.6), inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative; z-index: 1;
    animation: logo-pulse 4s ease-in-out infinite;
    overflow: hidden;
}
.vv-logo-ring::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 0;
    background: linear-gradient(90deg, #4F46E5, #A855F7, #EC4899);
}
@keyframes logo-pulse {
    0%,100% { box-shadow: 0 0 0 1px rgba(167,139,250,0.3), 0 0 45px rgba(124,58,237,0.6), inset 0 1px 0 rgba(255,255,255,0.08); }
    50%      { box-shadow: 0 0 0 1px rgba(167,139,250,0.55), 0 0 70px rgba(124,58,237,0.8), inset 0 1px 0 rgba(255,255,255,0.08); }
}

/* Waveform bars */
.vv-waveform { display: flex; align-items: center; gap: 3px; height: 34px; }
.vv-bar { width: 4px; border-radius: 3px; background: linear-gradient(to top, #4F46E5, #A855F7); animation: bar-dance 1.4s ease-in-out infinite; }
.vv-bar:nth-child(1){height:10px;animation-delay:0s}
.vv-bar:nth-child(2){height:20px;animation-delay:0.15s}
.vv-bar:nth-child(3){height:30px;animation-delay:0.3s}
.vv-bar:nth-child(4){height:20px;animation-delay:0.45s}
.vv-bar:nth-child(5){height:10px;animation-delay:0.6s}
@keyframes bar-dance { 0%,100%{transform:scaleY(0.6);opacity:0.7} 50%{transform:scaleY(1.2);opacity:1} }

.vv-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2.9rem !important; font-weight: 700 !important;
    background: linear-gradient(135deg, #FFFFFF 0%, #C4B5FD 40%, #E879F9 80%, #F0ABFC 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; background-clip: text !important;
    letter-spacing: -1.2px; line-height: 1.1; margin-bottom: 0.45rem !important;
    animation: title-shimmer 5s ease-in-out infinite;
}
@keyframes title-shimmer { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
.vv-subtitle { color: #64748B !important; font-size: 0.82rem !important; font-weight: 500 !important; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 1.3rem !important; }

.vv-badge-row { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 0.4rem; }
.vv-badge { display: inline-flex; align-items: center; gap: 7px; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.22); border-radius: 999px; padding: 5px 15px 5px 9px; font-size: 0.73rem; color: #A5B4FC !important; font-weight: 600; letter-spacing: 0.4px; }
.vv-badge-dot { width: 7px; height: 7px; border-radius: 50%; background: #34D399; box-shadow: 0 0 10px rgba(52,211,153,0.8); animation: dot-pulse 2s ease-in-out infinite; }
@keyframes dot-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.75)} }
.vv-badge-pink  { background: rgba(236,72,153,0.1); border-color: rgba(236,72,153,0.22); color: #F9A8D4 !important; }
.vv-badge-green { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.22); color: #6EE7B7 !important; }

.stats-strip { display: flex; gap: 10px; margin: 1.3rem 0 0; justify-content: center; }
.stat-chip { background: rgba(10,14,30,0.75); border: 1px solid rgba(99,102,241,0.14); border-radius: 14px; padding: 10px 22px; text-align: center; backdrop-filter: blur(10px); }
.stat-num { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: #A78BFA; line-height: 1; }
.stat-label { font-size: 0.63rem; color: #64748B; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-top: 4px; }

/* ── CHAT ── */
.chat-window { position: relative; background: rgba(8,12,28,0.9); border: 1px solid rgba(99,102,241,0.14); border-radius: 28px; margin: 2rem 0 0; overflow: hidden; box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset, 0 24px 64px rgba(0,0,0,0.65), 0 0 80px rgba(99,102,241,0.05); animation: window-appear 0.55s cubic-bezier(0.16,1,0.3,1) both; }
@keyframes window-appear { from{opacity:0;transform:translateY(22px)} to{opacity:1;transform:translateY(0)} }
.chat-titlebar { display: flex; align-items: center; justify-content: space-between; padding: 13px 20px; background: rgba(10,14,32,0.95); border-bottom: 1px solid rgba(99,102,241,0.1); }
.chat-titlebar-dots { display: flex; gap: 7px; }
.chrome-dot { width: 11px; height: 11px; border-radius: 50%; }
.chrome-dot-1 { background: #FF5F57; box-shadow: 0 0 7px rgba(255,95,87,0.5); }
.chrome-dot-2 { background: #FFBD2E; box-shadow: 0 0 7px rgba(255,189,46,0.5); }
.chrome-dot-3 { background: #28C840; box-shadow: 0 0 7px rgba(40,200,64,0.5); }
.chat-titlebar-title { font-size: 0.74rem; font-weight: 600; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase; }
.chat-titlebar-indicator { display: flex; align-items: center; gap: 6px; font-size: 0.7rem; color: #34D399; font-weight: 600; }
.indicator-dot { width: 6px; height: 6px; border-radius: 50%; background: #34D399; box-shadow: 0 0 8px rgba(52,211,153,0.7); animation: blink-slow 2.5s ease-in-out infinite; }
@keyframes blink-slow { 0%,100%{opacity:1} 50%{opacity:0.3} }
.chat-messages { height: 430px; overflow-y: auto; overflow-x: hidden; padding: 1.6rem 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; scroll-behavior: smooth; scrollbar-width: thin; scrollbar-color: rgba(99,102,241,0.2) transparent; }
.chat-messages::-webkit-scrollbar { width: 3px; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.2); border-radius: 999px; }
.chat-fade-top    { position: absolute; top: 53px; left: 0; right: 0; height: 46px; background: linear-gradient(to bottom, rgba(8,12,28,0.92), transparent); pointer-events: none; z-index: 2; }
.chat-fade-bottom { position: absolute; bottom: 0; left: 0; right: 0; height: 48px; background: linear-gradient(to top, rgba(8,12,28,0.92), transparent); pointer-events: none; z-index: 2; }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 16px; padding: 2rem; }
.empty-icon-ring { width: 80px; height: 80px; border-radius: 50%; border: 1px solid rgba(99,102,241,0.22); display: flex; align-items: center; justify-content: center; font-size: 2rem; background: rgba(79,70,229,0.07); animation: empty-float 3.5s ease-in-out infinite; box-shadow: 0 0 30px rgba(79,70,229,0.12); }
@keyframes empty-float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
.empty-title { color: #4B5563; font-size: 0.95rem; font-weight: 600; text-align: center; }
.empty-hint  { color: #374151; font-size: 0.78rem; text-align: center; line-height: 1.5; }
.msg-timestamp { text-align: center; font-size: 0.63rem; color: #374151; font-weight: 600; letter-spacing: 0.5px; margin: 0.3rem 0; }
.user-wrap { display: flex; flex-direction: column; align-items: flex-end; animation: slide-in-right 0.38s cubic-bezier(0.16,1,0.3,1) both; }
@keyframes slide-in-right { from{opacity:0;transform:translateX(18px)} to{opacity:1;transform:translateX(0)} }
.user-tag { font-size: 0.63rem; color: #818CF8; font-weight: 700; letter-spacing: 1.3px; text-transform: uppercase; margin-bottom: 5px; padding-right: 3px; }
.user-bubble { background: linear-gradient(145deg, #5B21B6, #7C3AED, #9333EA); color: #fff !important; padding: 1rem 1.4rem; border-radius: 20px 20px 4px 20px; max-width: 76%; font-size: 0.91rem; font-weight: 500; line-height: 1.65; word-break: break-word; box-shadow: 0 8px 32px rgba(124,58,237,0.42), 0 1px 0 rgba(255,255,255,0.1) inset; }
.ai-wrap { display: flex; flex-direction: column; align-items: flex-start; max-width: 82%; animation: slide-in-left 0.38s cubic-bezier(0.16,1,0.3,1) both; }
@keyframes slide-in-left { from{opacity:0;transform:translateX(-18px)} to{opacity:1;transform:translateX(0)} }
.ai-tag { display: flex; align-items: center; gap: 8px; font-size: 0.63rem; color: #818CF8; font-weight: 700; letter-spacing: 1.3px; text-transform: uppercase; margin-bottom: 5px; padding-left: 2px; }
.ai-avatar { width: 21px; height: 21px; border-radius: 50%; background: linear-gradient(135deg, #4F46E5, #7C3AED, #A855F7); display: flex; align-items: center; justify-content: center; font-size: 0.58rem; box-shadow: 0 2px 8px rgba(79,70,229,0.55); }
.ai-bubble { background: rgba(12,18,40,0.95); border: 1px solid rgba(99,102,241,0.18); color: #D1D9E6 !important; padding: 1rem 1.4rem; border-radius: 4px 20px 20px 20px; font-size: 0.91rem; line-height: 1.72; word-break: break-word; backdrop-filter: blur(16px); box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 1px 0 rgba(255,255,255,0.03) inset; }
.typing-bubble { display: inline-flex; align-items: center; gap: 5px; background: rgba(12,18,40,0.95); border: 1px solid rgba(99,102,241,0.18); padding: 0.85rem 1.2rem; border-radius: 4px 20px 20px 20px; }
.typing-dot { width: 8px; height: 8px; border-radius: 50%; background: #818CF8; }
.typing-dot:nth-child(1){animation:dot-bounce 1.4s infinite 0s}
.typing-dot:nth-child(2){animation:dot-bounce 1.4s infinite 0.2s}
.typing-dot:nth-child(3){animation:dot-bounce 1.4s infinite 0.4s}
@keyframes dot-bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.35} 40%{transform:scale(1.15);opacity:1} }

.mic-section { margin: 1.9rem 0 0.8rem; }
.mic-label-row { display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; }
.mic-label-line { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.25), transparent); }
.mic-label-text { font-size: 0.66rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 2.2px; white-space: nowrap; }
.mic-label-icon { font-size: 0.85rem; }

div[data-testid="stAudioInput"] { background: rgba(8,12,28,0.92) !important; border: 1px solid rgba(99,102,241,0.22) !important; border-radius: 22px !important; backdrop-filter: blur(20px) !important; box-shadow: 0 8px 40px rgba(0,0,0,0.5) !important; transition: all 0.35s cubic-bezier(0.16,1,0.3,1) !important; overflow: hidden !important; }
div[data-testid="stAudioInput"]:focus-within { border-color: rgba(167,139,250,0.48) !important; box-shadow: 0 8px 40px rgba(0,0,0,0.5), 0 0 32px rgba(124,58,237,0.22) !important; }
div[data-testid="stAudioInput"] > div, div[data-testid="stAudioInput"] > div > div, div[data-testid="stAudioInput"] > div > div > div { background: transparent !important; background-color: transparent !important; box-shadow: none !important; border-radius: 0 !important; }

div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button { background: rgba(239,68,68,0.06) !important; border: 1px solid rgba(239,68,68,0.18) !important; color: #F87171 !important; border-radius: 16px !important; font-size: 0.81rem !important; font-weight: 600 !important; padding: 0.78rem 1rem !important; transition: all 0.25s !important; width: 100% !important; }
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover { background: rgba(239,68,68,0.12) !important; transform: translateY(-2px) !important; }
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, #4F46E5, #6D28D9) !important; border-color: rgba(99,102,241,0.4) !important; color: #FFFFFF !important; box-shadow: 0 4px 20px rgba(79,70,229,0.3) !important; }
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"]:hover { background: linear-gradient(135deg, #4338CA, #5B21B6) !important; transform: translateY(-2px) !important; }
div[data-testid="stHorizontalBlock"] div[data-testid="stDownloadButton"] button { background: rgba(16,185,129,0.06) !important; border: 1px solid rgba(16,185,129,0.2) !important; color: #6EE7B7 !important; border-radius: 16px !important; font-size: 0.81rem !important; font-weight: 600 !important; padding: 0.78rem 1rem !important; transition: all 0.25s !important; width: 100% !important; }
div[data-testid="stHorizontalBlock"] div[data-testid="stDownloadButton"] button:hover { background: rgba(16,185,129,0.12) !important; transform: translateY(-2px) !important; }

[data-testid="stSpinner"] { color: #A78BFA !important; }
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.2); border-radius: 999px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# 🏠 HEADER
# ============================================
total_msgs  = len(st.session_state.conversation)
total_saved = len(st.session_state.all_conversations)

st.markdown(f"""
<div class="vv-header">
    <div class="vv-logo-container">
        <div class="vv-orbit-ring"></div>
        <div class="vv-logo-ring">
            <div class="vv-waveform">
                <div class="vv-bar"></div>
                <div class="vv-bar"></div>
                <div class="vv-bar"></div>
                <div class="vv-bar"></div>
                <div class="vv-bar"></div>
            </div>
        </div>
    </div>
    <div class="vv-title">VoiceVerse Pro</div>
    <div class="vv-subtitle">Conversational Voice Intelligence</div>
    <div class="vv-badge-row">
        <span class="vv-badge"><span class="vv-badge-dot"></span>AI Online</span>
        <span class="vv-badge vv-badge-pink">⚡ Real-time</span>
        <span class="vv-badge vv-badge-green">🎵 Voice Ready</span>
    </div>
    <div class="stats-strip">
        <div class="stat-chip"><div class="stat-num">{total_msgs}</div><div class="stat-label">Messages</div></div>
        <div class="stat-chip"><div class="stat-num">{total_saved}</div><div class="stat-label">Saved</div></div>
        <div class="stat-chip"><div class="stat-num">10</div><div class="stat-label">Languages</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# 💬 CHAT WINDOW
# ============================================
def build_chat_html(conversation):
    if not conversation:
        return """<div class="chat-window">
            <div class="chat-titlebar">
                <div class="chat-titlebar-dots"><div class="chrome-dot chrome-dot-1"></div><div class="chrome-dot chrome-dot-2"></div><div class="chrome-dot chrome-dot-3"></div></div>
                <div class="chat-titlebar-title">VoiceVerse Chat</div>
                <div class="chat-titlebar-indicator"><div class="indicator-dot"></div>Live</div>
            </div>
            <div class="chat-fade-top"></div>
            <div class="chat-messages">
                <div class="empty-state">
                    <div class="empty-icon-ring">🎙️</div>
                    <div class="empty-title">Start your conversation</div>
                    <div class="empty-hint">Tap the mic below and speak —<br>I'll respond instantly in your language</div>
                </div>
            </div>
            <div class="chat-fade-bottom"></div>
        </div>"""

    bubbles = ""
    for entry in conversation:
        ts = entry.get("timestamp", "")
        u  = entry.get("user", "")
        a  = entry.get("ai", "")
        if ts:
            bubbles += f'<div class="msg-timestamp">{ts}</div>'
        if u:
            bubbles += f'<div class="user-wrap"><div class="user-tag">You</div><div class="user-bubble">{u}</div></div>'
        if a:
            bubbles += f'<div class="ai-wrap"><div class="ai-tag"><div class="ai-avatar">✦</div>VoiceVerse AI</div><div class="ai-bubble">{a}</div></div>'

    return f"""<div class="chat-window">
        <div class="chat-titlebar">
            <div class="chat-titlebar-dots"><div class="chrome-dot chrome-dot-1"></div><div class="chrome-dot chrome-dot-2"></div><div class="chrome-dot chrome-dot-3"></div></div>
            <div class="chat-titlebar-title">VoiceVerse Chat</div>
            <div class="chat-titlebar-indicator"><div class="indicator-dot"></div>Live</div>
        </div>
        <div class="chat-fade-top"></div>
        <div class="chat-messages" id="chat-scroll">{bubbles}</div>
        <div class="chat-fade-bottom"></div>
    </div>
    <script>
        (function(){{var b=document.getElementById('chat-scroll');if(b)b.scrollTop=b.scrollHeight;}})();
        setTimeout(function(){{var b=document.getElementById('chat-scroll');if(b)b.scrollTop=b.scrollHeight;}},150);
    </script>"""

st.markdown(build_chat_html(st.session_state.conversation), unsafe_allow_html=True)

# ============================================
# 🎤 MIC SECTION
# ============================================
st.markdown("""
<div class="mic-section">
    <div class="mic-label-row">
        <div class="mic-label-line"></div>
        <span class="mic-label-icon">🎤</span>
        <div class="mic-label-text">Speak to AI</div>
        <div class="mic-label-line"></div>
    </div>
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

        with st.spinner("✦ Transcribing your voice..."):
            user_text = speech_to_text(audio_bytes)

            if user_text:
                def update_typing(status):
                    if status == "typing":
                        typing_placeholder.markdown("""
                        <div class="ai-wrap" style="padding:0 0 0.5rem;">
                            <div class="ai-tag"><div class="ai-avatar">✦</div>VoiceVerse AI</div>
                            <div class="typing-bubble">
                                <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        typing_placeholder.empty()

                ai_response = get_ai_response(user_text, st.session_state.chat_messages, update_typing)
                typing_placeholder.empty()
                ai_audio = text_to_speech(ai_response)

                st.session_state.chat_messages.append({"role": "user", "content": user_text})
                st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                st.session_state.current_user_text = user_text
                st.session_state.current_ai_text   = ai_response
                st.session_state.conversation.append({
                    "timestamp": datetime.now().strftime("%I:%M %p"),
                    "user": user_text,
                    "ai":   ai_response
                })
                save_history(st.session_state.conversation)
                if ai_audio:
                    st.session_state.pending_audio_bytes = ai_audio
                st.rerun()
            else:
                typing_placeholder.empty()
                st.error("⚠️ Could not detect voice. Please try again.")

# ============================================
# 📥 ACTION BUTTONS
# ============================================
if st.session_state.conversation:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            for _k in ["conversation","chat_messages","current_user_text",
                       "current_ai_text","last_processed_audio","pending_audio_bytes"]:
                if _k in st.session_state:
                    del st.session_state[_k]
            save_history([])
            st.rerun()
    with col2:
        if st.button("✨ New Chat", use_container_width=True, type="primary"):
            if st.session_state.get("conversation"):
                saved = st.session_state.all_conversations
                saved.append({
                    "timestamp":    datetime.now().strftime("%I:%M %p, %d %b"),
                    "conversation": st.session_state.conversation.copy(),
                    "messages":     st.session_state.chat_messages.copy(),
                    "preview":      get_preview(st.session_state.conversation)
                })
                # FIX: keep only last 5
                st.session_state.all_conversations = saved[-5:]
                save_saved_conversations(st.session_state.all_conversations)
            for _k in ["conversation","chat_messages","current_user_text",
                       "current_ai_text","last_processed_audio","pending_audio_bytes"]:
                if _k in st.session_state:
                    del st.session_state[_k]
            save_history([])
            st.rerun()
    with col3:
        if st.session_state.all_conversations or st.session_state.conversation:
            all_text = []
            if st.session_state.conversation:
                all_text.append("=== Current Conversation ===")
                for e in st.session_state.conversation:
                    all_text.append(f"{e.get('timestamp','')} - You: {e.get('user','')}")
                    all_text.append(f"{e.get('timestamp','')} - AI: {e.get('ai','')}")
                    all_text.append("")
            for idx, conv in enumerate(st.session_state.all_conversations):
                all_text.append(f"\n=== Conversation {idx+1} ({conv.get('timestamp','')}) ===")
                for e in conv.get("conversation", []):
                    all_text.append(f"{e.get('timestamp','')} - You: {e.get('user','')}")
                    all_text.append(f"{e.get('timestamp','')} - AI: {e.get('ai','')}")
                    all_text.append("")
            st.download_button(
                label="📥 Export",
                data="\n".join(all_text),
                file_name=f"VoiceVerse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# ============================================
# 🎯 SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1.8rem 1.6rem 1.4rem;">
        <div style="display:flex;align-items:center;gap:13px;">
            <div style="width:42px;height:42px;border-radius:14px;flex-shrink:0;background:linear-gradient(135deg,#4F46E5,#7C3AED);display:flex;align-items:center;justify-content:center;font-size:1.2rem;box-shadow:0 4px 18px rgba(79,70,229,0.45);">〜</div>
            <div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;color:#E2E8F0;letter-spacing:-0.2px;line-height:1.2;">VoiceVerse</div>
                <div style="font-size:0.62rem;color:#4B5563;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;margin-top:2px;">Pro Edition</div>
            </div>
        </div>
    </div>
    <div style="height:1px;background:rgba(99,102,241,0.1);margin:0 1.6rem;"></div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style="padding:1.3rem 1.6rem 0.5rem;">
        <div style="font-size:0.63rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1.8px;display:flex;align-items:center;gap:7px;margin-bottom:10px;">
            <span style="color:#818CF8;font-size:0.85rem;">🌐</span> Language
        </div></div>""", unsafe_allow_html=True)

    lang_options = ["auto","en","gu","hi","ar","bn","pt","es","fr","de","ja"]
    lang_labels  = {
        "auto":"🤖 Auto-detect","en":"🇬🇧 English","gu":"🇮🇳 Gujarati",
        "hi":"🇮🇳 Hindi","ar":"🇸🇦 Arabic","bn":"🇧🇩 Bengali",
        "pt":"🇵🇹 Portuguese","es":"🇪🇸 Spanish","fr":"🇫🇷 French",
        "de":"🇩🇪 German","ja":"🇯🇵 Japanese"
    }
    selected_lang = st.selectbox(
        "lang", options=lang_options,
        format_func=lambda x: lang_labels.get(x, x),
        index=lang_options.index(st.session_state.selected_language),
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.selected_language:
        if st.session_state.conversation:
            saved = st.session_state.all_conversations
            saved.append({
                "timestamp":    datetime.now().strftime("%I:%M %p, %d %b"),
                "conversation": st.session_state.conversation.copy(),
                "messages":     st.session_state.chat_messages.copy(),
                "preview":      get_preview(st.session_state.conversation)
            })
            st.session_state.all_conversations = saved[-5:]
            save_saved_conversations(st.session_state.all_conversations)
        st.session_state.selected_language    = selected_lang
        st.session_state.conversation         = []
        st.session_state.chat_messages        = []
        st.session_state.current_user_text    = ""
        st.session_state.current_ai_text      = ""
        st.session_state.last_processed_audio = None
        st.session_state.pending_audio_bytes  = None
        save_history([])
        st.rerun()

    msgs_sb  = len(st.session_state.conversation)
    saved_sb = len(st.session_state.all_conversations)
    st.markdown(f"""<div style="height:1px;background:rgba(99,102,241,0.1);margin:1.1rem 1.6rem 0;"></div>
    <div style="padding:1.2rem 1.6rem 0.6rem;">
        <div style="font-size:0.63rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1.8px;display:flex;align-items:center;gap:7px;margin-bottom:12px;">
            <span style="color:#818CF8;font-size:0.85rem;">📊</span> Stats
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;">
            <div style="background:rgba(79,70,229,0.09);border:1px solid rgba(79,70,229,0.17);border-radius:13px;padding:11px 10px;text-align:center;">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.6rem;font-weight:700;color:#A78BFA;line-height:1;">{msgs_sb}</div>
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.8px;font-weight:700;margin-top:3px;">Messages</div>
            </div>
            <div style="background:rgba(16,185,129,0.09);border:1px solid rgba(16,185,129,0.17);border-radius:13px;padding:11px 10px;text-align:center;">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.6rem;font-weight:700;color:#34D399;line-height:1;">{saved_sb}</div>
                <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;letter-spacing:0.8px;font-weight:700;margin-top:3px;">Saved</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # FIX: History — preview text, last 5 only, proper spacing
    st.markdown("""<div style="height:1px;background:rgba(99,102,241,0.1);margin:0.4rem 1.6rem 0;"></div>
    <div style="padding:1.2rem 1.6rem 0.7rem;">
        <div style="font-size:0.63rem;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:1.8px;display:flex;align-items:center;gap:7px;margin-bottom:10px;">
            <span style="color:#818CF8;font-size:0.85rem;">💾</span> History
        </div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.all_conversations:
        # Show last 5 only, newest first
        recent = list(reversed(st.session_state.all_conversations[-5:]))
        for idx, conv in enumerate(recent):
            real_idx = len(st.session_state.all_conversations) - 1 - idx
            # FIX: preview text instead of timestamp — like Claude AI
            preview = conv.get("preview") or get_preview(conv.get("conversation", []))
            st.markdown('<div style="padding:0 1.4rem 6px;">', unsafe_allow_html=True)
            if st.button(f"💬  {preview}", key=f"conv_{real_idx}", use_container_width=True):
                st.session_state.conversation        = conv.get("conversation", [])
                st.session_state.chat_messages       = conv.get("messages", [])
                st.session_state.current_user_text   = ""
                st.session_state.current_ai_text     = ""
                st.session_state.last_processed_audio = None
                st.session_state.pending_audio_bytes  = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""<div style="padding:0 1.6rem 1rem;">
            <div style="background:rgba(15,20,40,0.55);border:1px dashed rgba(99,102,241,0.14);border-radius:14px;padding:18px;text-align:center;">
                <div style="font-size:1.5rem;margin-bottom:7px;opacity:0.25;">💬</div>
                <div style="font-size:0.76rem;color:#4B5563;font-weight:500;">No saved conversations yet</div>
                <div style="font-size:0.68rem;color:#374151;margin-top:4px;">Start talking to save your first chat</div>
            </div></div>""", unsafe_allow_html=True)