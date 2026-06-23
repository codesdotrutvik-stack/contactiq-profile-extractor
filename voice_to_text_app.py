import streamlit as st
import assemblyai as aai
from datetime import datetime
import os
import requests
import json
import hashlib

st.set_page_config(page_title="Voice to Text Pro", page_icon="✨", layout="wide")

# ============================================================
# API KEYS
# ============================================================
ASSEMBLYAI_KEY = "5e874d691c74442f8b602827e6d26752"
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

aai.settings.api_key = ASSEMBLYAI_KEY

# ============================================================
# HISTORY FILE
# ============================================================
HISTORY_FILE = "history.json"

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
            json.dump(history, f, indent=2)
    except:
        pass

# ============================================================
# PREMIUM CSS — Next-Level Dark Design
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');

*, *::before, *::after {
    margin: 0; padding: 0; box-sizing: border-box;
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #080810;
    min-height: 100vh;
}

.block-container {
    padding: 2.5rem 2rem 4rem 2rem !important;
    max-width: 860px !important;
    position: relative;
    z-index: 1;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position: 200% center; }
}

/* ── HEADER ─────────────────────────────────────────── */
.vtp-header {
    text-align: center;
    padding: 2.5rem 0 2rem;
    animation: fadeUp 0.7s ease both;
}
.vtp-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(139,92,246,0.12);
    border: 1px solid rgba(139,92,246,0.28);
    border-radius: 100px;
    padding: 5px 14px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #a78bfa;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.vtp-badge .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #8b5cf6;
    box-shadow: 0 0 8px #8b5cf6;
}
.vtp-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1.1;
    letter-spacing: -0.04em;
    margin-bottom: 0.8rem;
}
.vtp-title .accent {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #38bdf8 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 5s linear infinite;
}
.vtp-sub {
    color: #475569;
    font-size: 0.88rem;
    letter-spacing: 0.02em;
}

/* ── CARDS ──────────────────────────────────────────── */
.vtp-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.25s, box-shadow 0.25s;
    animation: fadeUp 0.5s ease both;
}
.vtp-card:hover {
    border-color: rgba(139,92,246,0.2);
    box-shadow: 0 0 32px rgba(139,92,246,0.05);
}
.vtp-card-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1rem;
}

/* ── FILE UPLOADER ──────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.015) !important;
    border: 1.5px dashed rgba(139,92,246,0.2) !important;
    border-radius: 14px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(139,92,246,0.45) !important;
}

/* ── VIDEO / AUDIO ──────────────────────────────────── */
[data-testid="stVideo"], [data-testid="stAudio"] {
    width: 100% !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── TRANSCRIPTION BOX ──────────────────────────────── */
.vtp-textbox {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 20px 22px;
    min-height: 140px;
    color: #94a3b8;
    font-size: 0.88rem;
    line-height: 1.85;
    white-space: pre-wrap;
    max-height: 480px;
    overflow-y: auto;
    animation: fadeUp 0.5s ease both;
}
.vtp-textbox-translated {
    border-color: rgba(251,191,36,0.15);
}

/* ── SECTION LABEL ──────────────────────────────────── */
.vtp-section {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #334155;
    font-size: 0.66rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.8rem 0 0.9rem;
}
.vtp-section::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.04);
}

/* ── HISTORY ITEMS ──────────────────────────────────── */
.hist-wrap {
    display: flex;
    align-items: stretch;
    gap: 0;
    margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    overflow: hidden;
    transition: border-color 0.2s;
    animation: fadeUp 0.4s ease both;
}
.hist-wrap:hover {
    border-color: rgba(139,92,246,0.18);
}
.hist-body {
    flex: 1;
    background: rgba(255,255,255,0.02);
    padding: 14px 16px;
}
.hist-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 7px;
}
.hist-mode {
    font-size: 0.7rem;
    font-weight: 700;
    color: #7c3aed;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.hist-time {
    color: #1e293b;
    font-size: 0.66rem;
    font-weight: 500;
}
.hist-text {
    color: #334155;
    font-size: 0.8rem;
    line-height: 1.6;
}

/* ── BUTTONS ────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    padding: 9px 20px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 14px rgba(124,58,237,0.22) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #6d28d9, #4f46e5) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 24px rgba(124,58,237,0.38) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.04) !important;
    color: #475569 !important;
    box-shadow: none !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #94a3b8 !important;
}

/* Download icon button inside history — style the dl button */
[data-testid="stDownloadButton"] button {
    background: rgba(139,92,246,0.08) !important;
    border: 1px solid rgba(139,92,246,0.18) !important;
    color: #8b5cf6 !important;
    box-shadow: none !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    padding: 6px 10px !important;
    font-weight: 700 !important;
    transition: all 0.18s !important;
    height: 100% !important;
    min-height: 60px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(139,92,246,0.18) !important;
    border-color: rgba(139,92,246,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── CHECKBOX ───────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    color: #475569 !important;
    font-size: 0.8rem !important;
}

/* ── SELECT ─────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #cbd5e1 !important;
}

/* ── CAPTION ────────────────────────────────────────── */
.stCaption p, [data-testid="stCaptionContainer"] p {
    color: #334155 !important;
    font-size: 0.7rem !important;
}

/* ── STATUS MESSAGES ────────────────────────────────── */
.vtp-success {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(16,185,129,0.07);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    color: #34d399;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 0.8rem;
    animation: fadeUp 0.4s ease;
}
.vtp-error {
    background: rgba(239,68,68,0.07);
    border: 1px solid rgba(239,68,68,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    color: #f87171;
    font-size: 0.8rem;
    margin-bottom: 0.8rem;
}
.vtp-warn {
    background: rgba(251,191,36,0.07);
    border: 1px solid rgba(251,191,36,0.18);
    border-radius: 10px;
    padding: 10px 14px;
    color: #fbbf24;
    font-size: 0.8rem;
    margin-bottom: 0.8rem;
}

/* ── SCROLLBAR ──────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #4c1d95; border-radius: 10px; }

/* ── DIVIDER ────────────────────────────────────────── */
.vtp-hr {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.12), transparent);
    margin: 1.8rem 0 1rem;
    border: none;
}

/* ── FOOTER ─────────────────────────────────────────── */
.vtp-footer {
    text-align: center;
    color: #1e293b;
    font-size: 0.6rem;
    font-weight: 500;
    letter-spacing: 0.8px;
    padding-bottom: 1rem;
}
.vtp-footer span { color: #6d28d9; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = load_history()
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "original_text" not in st.session_state:
    st.session_state.original_text = ""
if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""
if "copy_msg" not in st.session_state:
    st.session_state.copy_msg = ""
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None
if "last_processed_file" not in st.session_state:
    st.session_state.last_processed_file = None

# ============================================================
# FUNCTIONS
# ============================================================
def translate_text(text, target_lang):
    lang_map = {
        "Hindi": "Hindi", "Gujarati": "Gujarati",
        "Spanish": "Spanish", "French": "French",
        "German": "German", "Chinese": "Chinese", "Japanese": "Japanese"
    }
    language = lang_map.get(target_lang, "Hindi")
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"}
    prompt = f"Translate the following text to {language}. Only output the translation.\n\nText:\n{text}"
    data = {"model": "mistral-small-latest", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Translation failed."

def format_transcript(transcript, conversation_mode):
    if conversation_mode and transcript.utterances:
        formatted = ""
        for utterance in transcript.utterances:
            formatted += f"**Speaker {utterance.speaker}:** {utterance.text}\n\n"
        return formatted
    return transcript.text

def add_to_history(text, full_text, mode):
    entry = {
        "text": text[:500] + ("..." if len(text) > 500 else ""),
        "full_text": full_text,
        "time": datetime.now().strftime("%I:%M %p, %d %b"),
        "mode": mode
    }
    st.session_state.history.insert(0, entry)
    save_history(st.session_state.history)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="vtp-header">
    <div class="vtp-badge">
        <span class="dot"></span>
        AI-Powered · Real-Time
    </div>
    <div class="vtp-title">Voice to Text <span class="accent">Pro</span></div>
    <div class="vtp-sub">Upload audio &nbsp;·&nbsp; Record live &nbsp;·&nbsp; Transcribe &nbsp;·&nbsp; Translate</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# STATUS MSG
# ============================================================
if st.session_state.copy_msg:
    st.markdown(f'<div class="vtp-success">✓ &nbsp;{st.session_state.copy_msg}</div>', unsafe_allow_html=True)
    st.session_state.copy_msg = ""

# ============================================================
# RECORD SECTION  — no extra boxes, clean single card
# ============================================================
st.markdown("""
<div class="vtp-card">
    <div class="vtp-card-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
        Record Voice
    </div>
""", unsafe_allow_html=True)

audio_value = st.audio_input("record", key="audio_recorder", label_visibility="collapsed")

audio_hash = None
if audio_value is not None:
    audio_hash = hashlib.md5(audio_value.getvalue()).hexdigest()

if audio_value is not None and audio_hash != st.session_state.last_processed_audio:
    st.session_state.last_processed_audio = audio_hash
    with st.spinner("Transcribing your recording…"):
        try:
            temp_file = "temp_audio.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_value.getvalue())
            config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(temp_file)
            if transcript.text:
                formatted = format_transcript(transcript, True)
                st.session_state.transcribed_text = formatted
                st.session_state.original_text = transcript.text
                add_to_history(formatted, formatted, "Conversation")
                st.markdown('<div class="vtp-success">✓ &nbsp;Transcription complete!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="vtp-error">⚠ No speech detected. Please try again.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="vtp-error">⚠ {str(e)}</div>', unsafe_allow_html=True)
        finally:
            try:
                if os.path.exists(temp_file): os.remove(temp_file)
            except: pass

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# UPLOAD SECTION
# ============================================================
st.markdown("""
<div class="vtp-card">
    <div class="vtp-card-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        Upload File
    </div>
""", unsafe_allow_html=True)

st.caption("MP3 · WAV · M4A · FLAC · WebM · MP4 · MOV · AVI · MKV")

uploaded_file = st.file_uploader(
    "upload", type=["mp3","wav","m4a","flac","webm","mp4","mov","avi","mkv"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
    file_type = uploaded_file.type
    if "video" in file_type or uploaded_file.name.lower().endswith((".mp4",".mov",".avi",".mkv")):
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file, format="audio/wav")

    file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
    st.caption(f"📄 {uploaded_file.name}  ·  {file_size:.2f} MB")

    conversation_mode = st.checkbox("Speaker labels (Conversation Mode)", value=True)

    if st.button("Transcribe", type="primary", use_container_width=True):
        if file_hash != st.session_state.last_processed_file:
            st.session_state.last_processed_file = file_hash
            with st.spinner("Processing audio…"):
                try:
                    file_ext = uploaded_file.name.split('.')[-1]
                    temp_file = f"temp_upload.{file_ext}"
                    with open(temp_file, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
                    transcriber = aai.Transcriber(config=config)
                    transcript = transcriber.transcribe(temp_file)
                    if transcript.text:
                        formatted = format_transcript(transcript, conversation_mode)
                        st.session_state.transcribed_text = formatted
                        st.session_state.original_text = transcript.text
                        st.session_state.translated_text = ""
                        mode = "Conversation" if conversation_mode else "Standard"
                        add_to_history(formatted, formatted, mode)
                        st.markdown('<div class="vtp-success">✓ &nbsp;Transcription complete!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="vtp-error">⚠ No speech detected.</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="vtp-error">⚠ {str(e)}</div>', unsafe_allow_html=True)
                finally:
                    try:
                        if os.path.exists(temp_file): os.remove(temp_file)
                    except: pass
        else:
            st.markdown('<div class="vtp-warn">⚠ This file has already been transcribed.</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TRANSCRIPTION OUTPUT
# ============================================================
if st.session_state.transcribed_text:
    st.markdown("""
    <div class="vtp-section">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        Transcription
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="vtp-textbox">{st.session_state.transcribed_text}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="↓  Download",
            data=st.session_state.transcribed_text,
            file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_btn_main"
        )
    with col2:
        if st.button("✕  Clear", key="clear_transcription", use_container_width=True, type="secondary"):
            st.session_state.transcribed_text = ""
            st.session_state.original_text = ""
            st.session_state.translated_text = ""
            st.rerun()
    with col3:
        if st.button("⇄  Translate", key="translate_btn", use_container_width=True):
            st.session_state.show_translate = not st.session_state.get("show_translate", False)
            st.rerun()

# ============================================================
# TRANSLATION
# ============================================================
if st.session_state.get("show_translate", False) and st.session_state.transcribed_text:
    st.markdown("""
    <div class="vtp-section">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        Translate
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        target_lang = st.selectbox(
            "Language",
            ["Hindi", "Gujarati", "Spanish", "French", "German", "Chinese", "Japanese"],
            label_visibility="collapsed"
        )
    with col2:
        translate_btn = st.button("Go →", type="primary", use_container_width=True)

    if translate_btn:
        with st.spinner("Translating…"):
            translated = translate_text(st.session_state.transcribed_text, target_lang)
            if translated:
                st.session_state.translated_text = translated
                st.markdown(f'<div class="vtp-textbox vtp-textbox-translated">{translated}</div>', unsafe_allow_html=True)
                st.download_button(
                    label="↓  Download Translation",
                    data=translated,
                    file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_translation_btn",
                    use_container_width=True
                )

# ============================================================
# HISTORY  — download icon on the RIGHT side of each item
# ============================================================
if st.session_state.history:
    st.markdown("""
    <div class="vtp-section">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="1 4 1 10 7 10"/>
            <path d="M3.51 15a9 9 0 1 0 .49-3.78"/>
        </svg>
        History
    </div>
    """, unsafe_allow_html=True)

    for idx, item in enumerate(st.session_state.history):
        col_body, col_dl = st.columns([11, 1])

        with col_body:
            st.markdown(f"""
            <div class="hist-wrap" style="margin-bottom:0;">
                <div class="hist-body">
                    <div class="hist-header-row">
                        <span class="hist-mode">{item['mode']}</span>
                        <span class="hist-time">{item['time']}</span>
                    </div>
                    <div class="hist-text">{item['text']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_dl:
            # Icon-only download button aligned with the card
            st.download_button(
                label="↓",
                data=item.get('full_text', item['text']),
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"dl_hist_{idx}",
                use_container_width=True,
            )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    if st.button("Clear All History", use_container_width=True, type="secondary"):
        st.session_state.history = []
        save_history(st.session_state.history)
        st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown('<div class="vtp-hr"></div>', unsafe_allow_html=True)
st.markdown('<div class="vtp-footer">✦ Voice to Text Pro &nbsp;·&nbsp; AssemblyAI + Mistral &nbsp;·&nbsp; <span>by Nirbhay</span></div>', unsafe_allow_html=True)