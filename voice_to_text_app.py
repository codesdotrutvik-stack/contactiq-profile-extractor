import streamlit as st
import assemblyai as aai
from datetime import datetime
import os
import requests
import json
import hashlib
import re

st.set_page_config(page_title="Transcriptr", page_icon="🎙️", layout="wide")

ASSEMBLYAI_KEY = "5e874d691c74442f8b602827e6d26752"
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"
aai.settings.api_key = ASSEMBLYAI_KEY

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

def get_google_drive_direct_link(url):
    """Convert Google Drive share link to direct download URL"""
    # Pattern for drive.google.com/file/d/.../view
    match = re.search(r'/file/d/([^/]+)/', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    # Pattern for drive.google.com/open?id=...
    match = re.search(r'[?&]id=([^&]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');

*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; font-family:'Inter',sans-serif; }

.stApp { background:#07070e; min-height:100vh; }

.block-container {
    padding: 2.5rem 2rem 5rem 2rem !important;
    max-width: 820px !important;
    position: relative;
    z-index: 1;
}

@keyframes fadeUp {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes shimmer {
    0%   { background-position:-200% center; }
    100% { background-position:200% center; }
}
@keyframes pulse {
    0%,100% { opacity:1; }
    50%      { opacity:0.4; }
}

/* ─── HEADER ────────────────────────────────────── */
.tr-header { text-align:center; padding:2.8rem 0 2.2rem; animation:fadeUp 0.7s ease both; }
.tr-badge {
    display:inline-flex; align-items:center; gap:7px;
    background:rgba(139,92,246,0.1);
    border:1px solid rgba(139,92,246,0.22);
    border-radius:100px;
    padding:5px 16px;
    font-size:0.65rem; font-weight:700;
    color:#a78bfa; letter-spacing:2.5px; text-transform:uppercase;
    margin-bottom:1.4rem;
}
.tr-badge .live-dot {
    width:6px; height:6px; border-radius:50%;
    background:#8b5cf6; box-shadow:0 0 8px #8b5cf6;
    animation:pulse 2s infinite;
}
.tr-logo {
    font-family:'Syne',sans-serif;
    font-size:3.4rem; font-weight:800;
    letter-spacing:-0.05em; line-height:1;
    margin-bottom:0.5rem;
}
.tr-logo .w { color:#e2e8f0; }
.tr-logo .acc {
    background:linear-gradient(135deg,#8b5cf6 0%,#6366f1 55%,#38bdf8 100%);
    background-size:200% auto;
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    animation:shimmer 5s linear infinite;
}
.tr-tagline { 
    color: #94a3b8; 
    font-size:0.8rem; 
    letter-spacing:0.04em; 
}
.tr-pills {
    display:flex; justify-content:center; gap:8px; flex-wrap:wrap;
    margin-top:1.2rem;
}
.tr-pill {
    display:inline-flex; align-items:center; gap:5px;
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:100px; padding:4px 12px;
    font-size:0.68rem; font-weight:500; color:#94a3b8;
}

/* ─── TAB SWITCHER ──────────────────────────────── */
.tab-bar {
    display:flex; gap:4px;
    background:rgba(255,255,255,0.025);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:14px; padding:5px; margin-bottom:1.4rem;
}
.tab-btn {
    flex:1; text-align:center;
    padding:10px 0; border-radius:10px;
    font-size:0.78rem; font-weight:600;
    cursor:pointer; transition:all 0.2s;
    color:#334155; border:none; background:transparent;
}
.tab-btn.active {
    background:linear-gradient(135deg,#7c3aed,#6366f1);
    color:#fff;
    box-shadow:0 2px 12px rgba(124,58,237,0.3);
}

/* ─── INPUT PANEL ───────────────────────────────── */
.input-panel {
    background:rgba(255,255,255,0.022);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:18px; padding:1.8rem 1.8rem 1.4rem;
    margin-bottom:1.2rem; animation:fadeUp 0.5s ease both;
    transition:border-color 0.25s;
}
.input-panel:hover { border-color:rgba(139,92,246,0.18); }
.panel-title {
    font-size:0.68rem; font-weight:700; 
    color: #cbd5e1;
    text-transform:uppercase; letter-spacing:2px;
    margin-bottom:1.1rem;
    display:flex; align-items:center; gap:8px;
}
.panel-title svg { flex-shrink:0; }

/* ─── RECORD ZONE ───────────────────────────────── */
.rec-hint {
    color: #94a3b8; 
    font-size:0.75rem; text-align:center;
    padding:0.4rem 0 0.8rem; letter-spacing:0.02em;
}

/* ─── FILE UPLOADER ─────────────────────────────── */
[data-testid="stFileUploader"] {
    background:rgba(255,255,255,0.015) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius:12px !important;
    transition:border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color:rgba(139,92,246,0.3) !important;
    background:rgba(139,92,246,0.03) !important;
}
[data-testid="stFileUploader"] span { color:#94a3b8 !important; }
[data-testid="stFileUploader"] .stFileUploaderLabel { color:#94a3b8 !important; }

/* ─── VIDEO/AUDIO ───────────────────────────────── */
[data-testid="stVideo"],[data-testid="stAudio"] {
    width:100% !important; border-radius:12px !important;
    overflow:hidden !important; margin-bottom:0.5rem !important;
}

/* ─── TRANSCRIPTION BOX ─────────────────────────── */
.tr-box {
    background:rgba(255,255,255,0.022);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:14px;
    padding:20px 22px;
    min-height:150px; max-height:480px;
    color:#d1d5db; font-size:0.88rem; line-height:1.85;
    white-space:pre-wrap; overflow-y:auto;
    animation:fadeUp 0.5s ease both;
    margin-bottom:0;
}
.tr-box-gold { border-color:rgba(251,191,36,0.18) !important; }

/* ─── ACTION ROW ──────────────────────────────────── */
.action-row {
    display:grid; grid-template-columns:1fr 1fr 1fr;
    gap:10px; margin-top:12px;
}
.action-row .stButton,
.action-row [data-testid="stDownloadButton"] {
    height:40px !important;
}
.action-row .stButton > button,
.action-row [data-testid="stDownloadButton"] > button {
    height:40px !important; width:100% !important;
    padding:0 !important; font-size:0.78rem !important;
    font-weight:600 !important;
}

/* ─── SECTION LABEL ─────────────────────────────── */
.tr-section {
    display:flex; align-items:center; gap:9px;
    color: #94a3b8; 
    font-size:0.64rem; font-weight:700;
    text-transform:uppercase; letter-spacing:2.5px;
    margin:2rem 0 1rem;
}
.tr-section::after {
    content:''; flex:1; height:1px;
    background:rgba(255,255,255,0.05);
}

/* ─── HISTORY ───────────────────────────────────── */
.hist-card {
    display:flex; align-items:stretch;
    background:rgba(255,255,255,0.028);
    border:1px solid rgba(255,255,255,0.07);
    border-radius:16px; overflow:hidden;
    margin-bottom:10px;
    transition:border-color 0.2s, background 0.2s;
    animation:fadeUp 0.4s ease both;
}
.hist-card:hover {
    border-color:rgba(139,92,246,0.22);
    background:rgba(139,92,246,0.03);
}
.hist-main { flex:1; padding:14px 16px; min-width:0; }
.hist-top {
    display:flex; justify-content:space-between;
    align-items:center; margin-bottom:7px;
}
.hist-badge {
    font-size:0.62rem; font-weight:800;
    color:#a78bfa; text-transform:uppercase; letter-spacing:1.5px;
    background:rgba(124,58,237,0.12);
    border:1px solid rgba(124,58,237,0.2);
    border-radius:6px; padding:2px 8px;
}
.hist-time { 
    color: #94a3b8; 
    font-size:0.65rem; font-weight:500; 
}
.hist-preview {
    color:#cbd5e1; 
    font-size:0.8rem; line-height:1.55;
    overflow:hidden;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
}
/* Download side panel */
.hist-dl-side {
    width:52px; min-width:52px;
    background:rgba(139,92,246,0.06);
    border-left:1px solid rgba(139,92,246,0.1);
    display:flex; align-items:center; justify-content:center;
    transition:background 0.2s;
    cursor:pointer;
}
.hist-dl-side:hover { background:rgba(139,92,246,0.14); }

/* Override download button inside hist side */
.hist-dl-col [data-testid="stDownloadButton"] button {
    background:rgba(139,92,246,0.07) !important;
    border:none !important;
    border-left:1px solid rgba(139,92,246,0.12) !important;
    border-radius:0 !important;
    color:#8b5cf6 !important;
    font-size:1.1rem !important; font-weight:700 !important;
    height:100% !important; min-height:72px !important;
    width:100% !important;
    box-shadow:none !important; padding:0 !important;
    transition:background 0.2s !important;
}
.hist-dl-col [data-testid="stDownloadButton"] button:hover {
    background:rgba(139,92,246,0.18) !important;
}

/* ─── BUTTONS ────────────────────────────────────── */
.stButton > button {
    background:linear-gradient(135deg,#7c3aed,#6366f1) !important;
    color:#fff !important; border:none !important;
    border-radius:10px !important; font-weight:600 !important;
    font-size:0.8rem !important;
    letter-spacing:0.02em !important;
    transition:all 0.2s !important;
    box-shadow:0 2px 12px rgba(124,58,237,0.2) !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#6d28d9,#4f46e5) !important;
    transform:translateY(-1px) !important;
    box-shadow:0 4px 22px rgba(124,58,237,0.36) !important;
}
.stButton > button[kind="secondary"] {
    background:rgba(255,255,255,0.04) !important;
    color:#94a3b8 !important; box-shadow:none !important;
    border:1px solid rgba(255,255,255,0.08) !important;
}
.stButton > button[kind="secondary"]:hover {
    background:rgba(255,255,255,0.08) !important;
    color:#cbd5e1 !important; transform:none !important;
}
[data-testid="stDownloadButton"] button {
    background:linear-gradient(135deg,#7c3aed,#6366f1) !important;
    color:#fff !important; border:none !important;
    border-radius:10px !important; font-weight:600 !important;
    font-size:0.8rem !important; box-shadow:0 2px 12px rgba(124,58,237,0.2) !important;
    transition:all 0.2s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background:linear-gradient(135deg,#6d28d9,#4f46e5) !important;
    transform:translateY(-1px) !important;
    box-shadow:0 4px 22px rgba(124,58,237,0.36) !important;
}

/* ─── CHECKBOX ───────────────────────────────────── */
[data-testid="stCheckbox"] label { 
    color: #cbd5e1 !important; 
    font-size:0.8rem !important; 
}

/* ─── SELECT ─────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background:rgba(255,255,255,0.04) !important;
    border:1px solid rgba(255,255,255,0.09) !important;
    border-radius:10px !important; color:#cbd5e1 !important;
}
[data-testid="stSelectbox"] select { color:#cbd5e1 !important; }

/* ─── CAPTION ────────────────────────────────────── */
.stCaption p,[data-testid="stCaptionContainer"] p { 
    color: #94a3b8 !important; 
    font-size:0.7rem !important; 
}

/* ─── STATUS ─────────────────────────────────────── */
.tr-ok {
    display:flex; align-items:center; gap:10px;
    background:rgba(16,185,129,0.07); border:1px solid rgba(16,185,129,0.18);
    border-radius:10px; padding:10px 14px; color:#34d399;
    font-size:0.8rem; font-weight:500; margin:0.7rem 0;
    animation:fadeUp 0.4s ease;
}
.tr-err {
    background:rgba(239,68,68,0.07); border:1px solid rgba(239,68,68,0.18);
    border-radius:10px; padding:10px 14px; color:#f87171;
    font-size:0.8rem; margin:0.7rem 0;
}
.tr-warn {
    background:rgba(251,191,36,0.07); border:1px solid rgba(251,191,36,0.18);
    border-radius:10px; padding:10px 14px; color:#fbbf24;
    font-size:0.8rem; margin:0.7rem 0;
}

/* ─── SCROLLBAR ──────────────────────────────────── */
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#4c1d95; border-radius:10px; }

/* ─── FOOTER ─────────────────────────────────────── */
.tr-footer {
    text-align:center; color:#94a3b8;
    font-size:0.6rem; font-weight:500; letter-spacing:1px;
    padding:1.5rem 0 0.5rem;
}
.tr-footer em { color:#6d28d9; font-style:normal; }

/* ─── MISC ───────────────────────────────────────── */
.tr-hr {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(139,92,246,0.12),transparent);
    margin:2rem 0 0; border:none;
}
.spacer-sm { height:0.6rem; }
#MainMenu,footer,header { visibility:hidden; }
[data-testid="stDecoration"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ──────────────────────────────────────────
if "history"               not in st.session_state: st.session_state.history               = load_history()
if "transcribed_text"      not in st.session_state: st.session_state.transcribed_text      = ""
if "original_text"         not in st.session_state: st.session_state.original_text         = ""
if "translated_text"       not in st.session_state: st.session_state.translated_text       = ""
if "last_processed_audio"  not in st.session_state: st.session_state.last_processed_audio  = None
if "last_processed_file"   not in st.session_state: st.session_state.last_processed_file   = None
if "show_translate"        not in st.session_state: st.session_state.show_translate        = False
if "input_mode"            not in st.session_state: st.session_state.input_mode            = "record"

# ─── HELPERS ────────────────────────────────────────────────
def translate_text(text, target_lang):
    lang_map = {"Hindi":"Hindi","Gujarati":"Gujarati","Spanish":"Spanish",
                "French":"French","German":"German","Chinese":"Chinese","Japanese":"Japanese"}
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization":f"Bearer {MISTRAL_KEY}","Content-Type":"application/json"}
    prompt = f"Translate to {lang_map.get(target_lang, 'Hindi')}. Only the translation.\n\n{text}"
    data = {"model":"mistral-small-latest","messages":[{"role":"user","content":prompt}],"max_tokens":2000}
    try:
        r = requests.post(url,json=data,headers=headers,timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "Translation failed."

def format_transcript(transcript, conversation_mode):
    if conversation_mode and transcript.utterances:
        return "".join(f"**Speaker {u.speaker}:** {u.text}\n\n" for u in transcript.utterances)
    return transcript.text

def add_to_history(text, full_text, mode):
    entry = {"text":text[:500]+("..." if len(text)>500 else ""),
             "full_text":full_text,
             "time":datetime.now().strftime("%I:%M %p, %d %b"),
             "mode":mode}
    st.session_state.history.insert(0, entry)
    save_history(st.session_state.history)

def do_transcribe(file_path, conversation_mode, mode_label):
    config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)
    if transcript.text:
        formatted = format_transcript(transcript, conversation_mode)
        st.session_state.transcribed_text = formatted
        st.session_state.original_text    = transcript.text
        st.session_state.translated_text  = ""
        add_to_history(formatted, formatted, mode_label)
        return True
    return False

# ─── HEADER ─────────────────────────────────────────────────
st.markdown("""
<div class="tr-header">
  <div class="tr-badge"><span class="live-dot"></span>AI · Live Transcription</div>
  <div class="tr-logo">
    <span class="w">Trans</span><span class="acc">criptr</span>
  </div>
  <div class="tr-tagline">Multi-speaker transcription &amp; AI translation, in seconds.</div>
  <div class="tr-pills">
    <span class="tr-pill">🎙 Record Live</span>
    <span class="tr-pill">📁 Upload File</span>
    <span class="tr-pill">🌐 URL Import</span>
    <span class="tr-pill">👥 Speaker Labels</span>
    <span class="tr-pill">🌐 Translate</span>
    <span class="tr-pill">📜 History</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── TAB SWITCHER ────────────────────────────────────────────
col_t1, col_t2, col_t3 = st.columns(3)
with col_t1:
    if st.button("🎙  Record", use_container_width=True,
                 type="primary" if st.session_state.input_mode=="record" else "secondary"):
        st.session_state.input_mode = "record"
        st.rerun()
with col_t2:
    if st.button("📁  Upload", use_container_width=True,
                 type="primary" if st.session_state.input_mode=="upload" else "secondary"):
        st.session_state.input_mode = "upload"
        st.rerun()
with col_t3:
    if st.button("🌐  URL", use_container_width=True,
                 type="primary" if st.session_state.input_mode=="url" else "secondary"):
        st.session_state.input_mode = "url"
        st.rerun()

# ─── RECORD PANEL ────────────────────────────────────────────
if st.session_state.input_mode == "record":
    st.markdown("""
    <div class="input-panel">
      <div class="panel-title">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
        Live Recording
      </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="rec-hint">Press the mic icon below to start — auto-transcribes on stop</p>', unsafe_allow_html=True)
    audio_value = st.audio_input("rec", key="audio_recorder", label_visibility="collapsed")

    audio_hash = hashlib.md5(audio_value.getvalue()).hexdigest() if audio_value else None
    if audio_value and audio_hash != st.session_state.last_processed_audio:
        st.session_state.last_processed_audio = audio_hash
        with st.spinner("Transcribing recording…"):
            try:
                tmp = "temp_audio.wav"
                with open(tmp,"wb") as f: f.write(audio_value.getvalue())
                ok = do_transcribe(tmp, True, "Conversation")
                if ok:
                    st.markdown('<div class="tr-ok">✓ &nbsp;Transcription complete!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="tr-err">⚠ No speech detected.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="tr-err">⚠ {e}</div>', unsafe_allow_html=True)
            finally:
                try: os.remove("temp_audio.wav")
                except: pass

    st.markdown('</div>', unsafe_allow_html=True)

# ─── UPLOAD PANEL ────────────────────────────────────────────
elif st.session_state.input_mode == "upload":
    st.markdown("""
    <div class="input-panel">
      <div class="panel-title">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        Upload Audio / Video
      </div>
    """, unsafe_allow_html=True)

    st.caption("MP3 · WAV · M4A · FLAC · WebM · MP4 · MOV · AVI · MKV (up to 200MB)")

    uploaded_file = st.file_uploader("u", type=["mp3","wav","m4a","flac","webm","mp4","mov","avi","mkv"], label_visibility="collapsed")

    if uploaded_file:
        file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
        if "video" in uploaded_file.type or uploaded_file.name.lower().endswith((".mp4",".mov",".avi",".mkv")):
            st.video(uploaded_file)
        else:
            st.audio(uploaded_file, format="audio/wav")
        st.caption(f"📄 {uploaded_file.name}  ·  {len(uploaded_file.getvalue())/(1024*1024):.2f} MB")
        conversation_mode = st.checkbox("Speaker labels (Conversation Mode)", value=True)

        if st.button("Transcribe", type="primary", use_container_width=True):
            if file_hash != st.session_state.last_processed_file:
                st.session_state.last_processed_file = file_hash
                with st.spinner("Processing audio…"):
                    try:
                        ext = uploaded_file.name.split(".")[-1]
                        tmp = f"temp_upload.{ext}"
                        with open(tmp,"wb") as f: f.write(uploaded_file.getbuffer())
                        mode = "Conversation" if conversation_mode else "Standard"
                        ok = do_transcribe(tmp, conversation_mode, mode)
                        if ok:
                            st.markdown('<div class="tr-ok">✓ &nbsp;Transcription complete!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="tr-err">⚠ No speech detected.</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="tr-err">⚠ {e}</div>', unsafe_allow_html=True)
                    finally:
                        try: os.remove(tmp)
                        except: pass
            else:
                st.markdown('<div class="tr-warn">⚠ Already transcribed.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─── URL PANEL ────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="input-panel">
      <div class="panel-title">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        Import from URL (no size limit)
      </div>
    """, unsafe_allow_html=True)

    st.caption("Paste a direct link to an audio/video file (supports any size up to 5GB)")

    url_input = st.text_input("File URL", placeholder="https://drive.google.com/... or https://example.com/file.mp3", label_visibility="collapsed")

    if url_input:
        # Convert Google Drive share link to direct download link
        direct_url = get_google_drive_direct_link(url_input)
        if direct_url != url_input:
            st.info(f"🔗 Direct download URL: {direct_url}")

    conversation_mode = st.checkbox("Speaker labels (Conversation Mode)", value=True)

    if st.button("Transcribe from URL", type="primary", use_container_width=True) and url_input:
        with st.spinner("Processing remote file…"):
            try:
                direct = get_google_drive_direct_link(url_input)
                config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
                transcriber = aai.Transcriber(config=config)
                transcript = transcriber.transcribe(direct)
                if transcript.text:
                    formatted = format_transcript(transcript, conversation_mode)
                    st.session_state.transcribed_text = formatted
                    st.session_state.original_text = transcript.text
                    st.session_state.translated_text = ""
                    mode = "Conversation" if conversation_mode else "Standard"
                    add_to_history(formatted, formatted, mode)
                    st.markdown('<div class="tr-ok">✓ &nbsp;Transcription complete!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="tr-err">⚠ No speech detected. Make sure the file is publicly accessible.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="tr-err">⚠ {e}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─── TRANSCRIPTION OUTPUT ────────────────────────────────────
if st.session_state.transcribed_text:
    st.markdown("""
    <div class="tr-section">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      Transcription
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="tr-box">{st.session_state.transcribed_text}</div>', unsafe_allow_html=True)

    st.markdown('<div class="action-row">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            label="↓  Download",
            data=st.session_state.transcribed_text,
            file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain", use_container_width=True, key="dl_main"
        )
    with c2:
        if st.button("✕  Clear", key="clear_tr", use_container_width=True, type="secondary"):
            st.session_state.transcribed_text = ""
            st.session_state.original_text = ""
            st.session_state.translated_text = ""
            st.session_state.show_translate = False
            st.rerun()
    with c3:
        lbl = "✕  Close Translate" if st.session_state.show_translate else "⇄  Translate"
        if st.button(lbl, key="tr_toggle", use_container_width=True):
            st.session_state.show_translate = not st.session_state.show_translate
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── TRANSLATION ─────────────────────────────────────────────
if st.session_state.show_translate and st.session_state.transcribed_text:
    st.markdown("""
    <div class="tr-section">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      Translate
    </div>
    """, unsafe_allow_html=True)
    col_l, col_b = st.columns([3,1])
    with col_l:
        target_lang = st.selectbox("lang", ["Hindi","Gujarati","Spanish","French","German","Chinese","Japanese"], label_visibility="collapsed")
    with col_b:
        go = st.button("Go →", type="primary", use_container_width=True)
    if go:
        with st.spinner("Translating…"):
            translated = translate_text(st.session_state.transcribed_text, target_lang)
            st.session_state.translated_text = translated
    if st.session_state.translated_text:
        st.markdown(f'<div class="tr-box tr-box-gold">{st.session_state.translated_text}</div>', unsafe_allow_html=True)
        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
        st.download_button(
            label="↓  Download Translation",
            data=st.session_state.translated_text,
            file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain", use_container_width=True, key="dl_translation"
        )

# ─── HISTORY ─────────────────────────────────────────────────
if st.session_state.history:
    st.markdown("""
    <div class="tr-section">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="1 4 1 10 7 10"/>
        <path d="M3.51 15a9 9 0 1 0 .49-3.78"/>
      </svg>
      History
    </div>
    """, unsafe_allow_html=True)

    for idx, item in enumerate(st.session_state.history):
        col_main, col_dl = st.columns([10, 1])

        with col_main:
            st.markdown(f"""
            <div class="hist-card" style="margin-bottom:0;">
              <div class="hist-main">
                <div class="hist-top">
                  <span class="hist-badge">{item['mode']}</span>
                  <span class="hist-time">{item['time']}</span>
                </div>
                <div class="hist-preview">{item['text']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with col_dl:
            st.markdown('<div class="hist-dl-col">', unsafe_allow_html=True)
            st.download_button(
                label="↓",
                data=item.get("full_text", item["text"]),
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"dl_h_{idx}",
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)
    if st.button("Clear All History", use_container_width=True, type="secondary"):
        st.session_state.history = []
        save_history(st.session_state.history)
        st.rerun()

# ─── FOOTER ──────────────────────────────────────────────────
st.markdown('<div class="tr-hr"></div>', unsafe_allow_html=True)
st.markdown('<div class="tr-footer">Transcriptr &nbsp;·&nbsp; AssemblyAI + Mistral &nbsp;·&nbsp; <em>by Nirbhay</em></div>', unsafe_allow_html=True)