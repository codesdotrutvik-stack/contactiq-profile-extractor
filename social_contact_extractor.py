import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Mesta AI", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #07080f !important;
    color: #e2e8f0 !important;
}
#MainMenu, footer, header { visibility: hidden !important; display: none !important; }
.block-container { padding: 0 2.5rem 5rem !important; max-width: 880px !important; }

.mesta-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1.4rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
[data-testid="stTextInputRootElement"] {
    background-color: transparent !important;
    border: none !important;
}
[data-baseweb="base-input"] {
    background-color: transparent !important;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #a78bfa, #7c3aed);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 0 18px rgba(124,58,237,0.4);
}
.header-title { font-size: 1.1rem; font-weight: 700; color: #f1f5f9; }
.header-sub { font-size: 0.67rem; color: #475569; margin-top: 1px; }
.online-dot {
    width: 7px; height: 7px; background: #22c55e;
    border-radius: 50%; box-shadow: 0 0 6px #22c55e; display: inline-block;
}
.model-badge {
    font-size: 0.67rem; background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    padding: 4px 12px; border-radius: 20px; color: #64748b;
}

/* INPUT - VISIBILITY FIXED & WHITE BORDER REMOVED */
.stTextInput > div > div > input {
    background: #161726 !important;
    border: 1px solid rgba(139,92,246,0.3) !important;
    border-radius: 50px !important;
    padding: 15px 24px !important;
    color: #f1f5f9 !important;
    font-size: 0.93rem !important;
    font-family: 'Inter', sans-serif !important;
    caret-color: #a78bfa !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: #94a3b8 !important;
    opacity: 0.6 !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(139,92,246,0.7) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
    background: #1a1c30 !important;
    outline: none !important;
}

/* BUTTONS */
.stButton > button {
    background: #12131e !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #64748b !important;
    border-radius: 50px !important;
    padding: 9px 22px !important;
    font-size: 0.82rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1a1b2e !important;
    color: #e2e8f0 !important;
    border-color: rgba(139,92,246,0.4) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    border: none !important; color: white !important;
    box-shadow: 0 0 22px rgba(124,58,237,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 32px rgba(124,58,237,0.55) !important;
}

/* BUBBLES */
.user-bubble {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: white; padding: 13px 18px;
    border-radius: 20px 20px 4px 20px;
    margin: 10px 0; margin-left: auto;
    max-width: 70%; font-size: 0.88rem; line-height: 1.55;
    text-align: right; box-shadow: 0 4px 20px rgba(124,58,237,0.2);
}
.ai-bubble {
    background: #12131e; border: 1px solid rgba(255,255,255,0.07);
    color: #e2e8f0; padding: 13px 18px;
    border-radius: 20px 20px 20px 4px;
    margin: 10px 0; max-width: 70%;
    font-size: 0.88rem; line-height: 1.55;
}
.ai-name {
    font-size: 0.68rem; font-weight: 600; color: #a78bfa;
    margin-bottom: 6px; display: flex; align-items: center; gap: 5px;
}
.msg-time { font-size: 0.6rem; color: #475569; margin-top: 6px; }

.section-label {
    font-size: 0.63rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #475569; margin: 1.6rem 0 0.9rem 0;
}
.divider { height: 1px; background: rgba(255,255,255,0.04); margin: 1.2rem 0; }
.mode-indicator { font-size: 0.72rem; color: #475569; margin-bottom: 1rem; }
.footer {
    text-align: center; font-size: 0.6rem; color: #1e293b;
    padding: 2rem; margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.03);
    letter-spacing: 1px; text-transform: uppercase;
}
.stSpinner > div { border-top-color: #7c3aed !important; }
</style>
""", unsafe_allow_html=True)

# CONFIG
MISTRAL_API_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None
if "output_mode" not in st.session_state:
    st.session_state.output_mode = "text"
if "voice_type" not in st.session_state:
    st.session_state.voice_type = "man"

# HEADER
st.markdown("""
<div class="mesta-header">
    <div class="header-left">
        <div class="header-logo">✦</div>
        <div>
            <div class="header-title">Mesta AI <span style="font-size:0.65rem;color:#7c3aed;">✔</span></div>
            <div class="header-sub">Intelligent Assistant</div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
        <span style="display:flex;align-items:center;gap:6px;">
            <span class="online-dot"></span>
            <span style="font-size:0.67rem;color:#334155;">Online</span>
        </span>
        <span class="model-badge">Mistral Small</span>
    </div>
</div>
""", unsafe_allow_html=True)

# HERO
st.markdown("""
<div style="text-align:center;padding:2.2rem 0 1rem 0;">
    <div style="font-size:2rem;font-weight:700;background:linear-gradient(135deg,#a78bfa,#818cf8,#60a5fa);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:0.4rem;">
        Welcome to Mesta AI ✦
    </div>
    <div style="font-size:0.9rem;color:#475569;">Your intelligent assistant — ask me anything</div>
</div>
""", unsafe_allow_html=True)

# WAVE ANIMATION
st.components.v1.html("""
<!DOCTYPE html>
<html>
<head>
<style>
body { margin:0; background:transparent; display:flex; flex-direction:column; align-items:center; justify-content:center; height:90px; overflow:hidden; }
.wave-wrap { display:flex; align-items:center; justify-content:center; gap:4px; height:60px; }
.bar {
    width:4px; border-radius:4px;
    background: linear-gradient(to top, #7c3aed, #a78bfa);
    height:8px; transition: height 0.1s;
}
#status { font-size:11px; color:#475569; margin-top:4px; letter-spacing:0.5px; font-family:Inter,sans-serif; }
#status.active { color:#a78bfa; }

@keyframes idle {
    0%,100% { height:8px; opacity:0.3; }
    50% { height:14px; opacity:0.6; }
}
.bar.idle { animation: idle 1.4s ease-in-out infinite; }
.bar.idle:nth-child(1)  { animation-delay:0.00s }
.bar.idle:nth-child(2)  { animation-delay:0.10s }
.bar.idle:nth-child(3)  { animation-delay:0.20s }
.bar.idle:nth-child(4)  { animation-delay:0.30s }
.bar.idle:nth-child(5)  { animation-delay:0.40s }
.bar.idle:nth-child(6)  { animation-delay:0.30s }
.bar.idle:nth-child(7)  { animation-delay:0.20s }
.bar.idle:nth-child(8)  { animation-delay:0.10s }
.bar.idle:nth-child(9)  { animation-delay:0.00s }
.bar.idle:nth-child(10) { animation-delay:0.15s }
.bar.idle:nth-child(11) { animation-delay:0.25s }
.bar.idle:nth-child(12) { animation-delay:0.35s }
</style>
</head>
<body>
<div class="wave-wrap" id="wave">
    <div class="bar idle"></div><div class="bar idle"></div>
    <div class="bar idle"></div><div class="bar idle"></div>
    <div class="bar idle"></div><div class="bar idle"></div>
    <div class="bar idle"></div><div class="bar idle"></div>
    <div class="bar idle"></div><div class="bar idle"></div>
    <div class="bar idle"></div><div class="bar idle"></div>
</div>
<div id="status">Ready</div>

<script>
var bars = document.querySelectorAll('.bar');
var statusEl = document.getElementById('status');
var animFrame = null;
var speaking = false;

var delays = [0, 0.08, 0.16, 0.24, 0.32, 0.24, 0.16, 0.08, 0, 0.12, 0.20, 0.28];
var speeds  = [0.45, 0.55, 0.40, 0.65, 0.50, 0.60, 0.45, 0.55, 0.40, 0.50, 0.65, 0.45];

function startSpeak() {
    speaking = true;
    bars.forEach(function(b) { b.classList.remove('idle'); });
    statusEl.textContent = 'Speaking...';
    statusEl.classList.add('active');
    animateBars();
}

function stopSpeak() {
    speaking = false;
    if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
    bars.forEach(function(b, i) {
        b.style.height = '8px';
        b.style.opacity = '0.3';
        setTimeout(function() { b.classList.add('idle'); }, 50);
    });
    statusEl.textContent = 'Ready';
    statusEl.classList.remove('active');
}

function animateBars() {
    if (!speaking) return;
    var t = Date.now() / 1000;
    bars.forEach(function(b, i) {
        var h = 8 + 40 * Math.abs(Math.sin((t / speeds[i]) + delays[i] * Math.PI * 2));
        b.style.height = h + 'px';
        b.style.opacity = '1';
    });
    animFrame = requestAnimationFrame(animateBars);
}

window.addEventListener('message', function(e) {
    if (!e.data) return;
    if (e.data.type === 'mesta_speak') startSpeak();
    if (e.data.type === 'mesta_stop')  stopSpeak();
});

window.mestaStartSpeak = startSpeak;
window.mestaStopSpeak  = stopSpeak;
</script>
</body>
</html>
""", height=100)

# TTS FUNCTION
def speak_text(text, voice_type="man"):
    safe = text.replace("'", "\\'").replace("\n", " ").replace('"', '\\"')

    if voice_type == "man":
        voice_filter = """
        v = allVoices.find(function(x){return x.lang.startsWith('en') && /david|mark|daniel|james|uk english male|english male/i.test(x.name);});
        if(!v) v = allVoices.find(function(x){return x.lang==='en-US' && x.name.toLowerCase().indexOf('female')===-1 && x.name.toLowerCase().indexOf('woman')===-1;});
        if(!v) v = allVoices.find(function(x){return x.lang.startsWith('en-');});
        msg.pitch = 0.8; msg.rate = 0.93;
        """
    elif voice_type == "woman":
        voice_filter = """
        v = allVoices.find(function(x){return x.lang.startsWith('en') && /samantha|zira|karen|victoria|susan|linda|female|woman/i.test(x.name);});
        if(!v) v = allVoices.find(function(x){return x.lang==='en-US';});
        msg.pitch = 1.25; msg.rate = 1.0;
        """
    else:
        voice_filter = """
        v = allVoices.find(function(x){return /google|neural|natural|premium|enhanced/i.test(x.name) && x.lang.startsWith('en');});
        if(!v) v = allVoices.find(function(x){return x.lang==='en-US' && /google/i.test(x.name);});
        if(!v) v = allVoices.find(function(x){return x.lang==='en-US';});
        msg.pitch = 1.0; msg.rate = 0.96;
        """

    return f"""
    <script>
    (function() {{
        function triggerWave(type) {{
            try {{
                var iframes = window.parent.document.querySelectorAll('iframe');
                iframes.forEach(function(f) {{
                    try {{ f.contentWindow.postMessage({{type: type}}, '*'); }} catch(e) {{}}
                }});
            }} catch(e) {{}}
        }}

        function doSpeak() {{
            var allVoices = window.speechSynthesis.getVoices();
            if (!allVoices || allVoices.length === 0) {{
                setTimeout(doSpeak, 200);
                return;
            }}
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe}');
            msg.lang = 'en-US';
            msg.volume = 1.0;
            var v = null;
            {voice_filter}
            if (v) msg.voice = v;

            msg.onstart = function() {{ triggerWave('mesta_speak'); }};
            msg.onend   = function() {{ triggerWave('mesta_stop');  }};
            msg.onerror = function() {{ triggerWave('mesta_stop');  }};

            window.speechSynthesis.speak(msg);
        }}

        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.onvoiceschanged = function() {{ doSpeak(); }};
        }} else {{
            doSpeak();
        }}
    }})();
    </script>
    """

# API - UPDATED with INCREASED max_tokens
def ask_mistral(question):
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": """You are Mesta AI, a coding expert assistant.

IMPORTANT RULES:
1. When asked for code, provide COMPLETE working code
2. NEVER summarize or shorten code - give full implementation
3. For Shopify sections, include: Liquid markup, full Schema, complete CSS
4. Code should be copy-paste ready and fully functional
5. Minimum 40-50 lines for complex requests
6. Include detailed comments

For Shopify hero banner, provide complete section.liquid file with:
- Full Liquid code with all HTML structure
- Complete schema with image, title, subtitle, button settings
- Full CSS styling (desktop + mobile responsive)
- Don't say "truncated" or "etc" - give actual code"""},
            {"role": "user", "content": question}
        ],
        "max_tokens": 2500  # INCREASED for longer responses
    }
    try:
        r = requests.post(MISTRAL_URL, json=data, headers=headers, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Connection issue: {str(e)}"

# PLAY PENDING AUDIO
if st.session_state.pending_audio:
    st.components.v1.html(st.session_state.pending_audio, height=0)
    st.session_state.pending_audio = None

# RESPONSE MODE
st.markdown('<div class="section-label">⚙ Response Mode</div>', unsafe_allow_html=True)
c1, c2, csp = st.columns([1, 1, 4])
with c1:
    if st.button("Text" if st.session_state.output_mode=="text" else "📝 Text",
                 use_container_width=True,
                 type="primary" if st.session_state.output_mode=="text" else "secondary"):
        st.session_state.output_mode = "text"
        st.rerun()
with c2:
    if st.button("Voice" if st.session_state.output_mode=="voice" else "🔊 Voice",
                 use_container_width=True,
                 type="primary" if st.session_state.output_mode=="voice" else "secondary"):
        st.session_state.output_mode = "voice"
        st.rerun()

# VOICE TYPE
if st.session_state.output_mode == "voice":
    st.markdown('<div class="section-label">🎙 Voice Type</div>', unsafe_allow_html=True)
    v1, v2, v3, vsp = st.columns([1, 1, 1, 3])
    with v1:
        if st.button("👨 Man" if st.session_state.voice_type=="man" else "👨 Man",
                     use_container_width=True,
                     type="primary" if st.session_state.voice_type=="man" else "secondary"):
            st.session_state.voice_type = "man"; st.rerun()
    with v2:
        if st.button("👩 Woman" if st.session_state.voice_type=="woman" else "👩 Woman",
                     use_container_width=True,
                     type="primary" if st.session_state.voice_type=="woman" else "secondary"):
            st.session_state.voice_type = "woman"; st.rerun()
    with v3:
        if st.button("🎭 Realistic" if st.session_state.voice_type=="realistic" else "🎭 Realistic",
                     use_container_width=True,
                     type="primary" if st.session_state.voice_type=="realistic" else "secondary"):
            st.session_state.voice_type = "realistic"; st.rerun()
    labels = {"man":"👨 Deep male voice", "woman":"👩 Female voice", "realistic":"🎭 Most natural available"}
    st.markdown(f'<div class="mode-indicator">{labels[st.session_state.voice_type]}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="mode-indicator">📝 Text replies only</div>', unsafe_allow_html=True)

# QUICK QUESTIONS
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-label">⚡ Quick Questions</div>', unsafe_allow_html=True)
quick_qs = [
    ("🖥", "Explain Quantum Computing"),
    ("💡", "Ideas for a startup"),
    ("📝", "Improve my resume"),
    ("🐍", "Write Python code for data analysis"),
    ("🤖", "Latest AI trends"),
    ("😄", "Tell me a joke"),
]
cols = st.columns(3)
for i, (icon, title) in enumerate(quick_qs):
    with cols[i % 3]:
        if st.button(f"{icon} {title}", use_container_width=True, key=f"qq_{i}"):
            with st.spinner("✦ Thinking..."):
                answer = ask_mistral(title)
                st.session_state.chat_history.append({
                    "q": title, "a": answer,
                    "t": datetime.now().strftime("%I:%M %p"),
                    "mode": st.session_state.output_mode,
                    "voice": st.session_state.voice_type
                })
                if st.session_state.output_mode == "voice":
                    st.session_state.pending_audio = speak_text(answer, st.session_state.voice_type)
                st.rerun()

# INPUT
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-label">💬 Ask Mesta</div>', unsafe_allow_html=True)
user_question = st.text_input("", placeholder="Ask Mesta anything...", key="text_input", label_visibility="collapsed")
a1, a2, a3 = st.columns([1.3, 1.3, 3])
with a1:
    ask_clicked = st.button("✦ Ask Mesta", use_container_width=True, type="primary")
with a2:
    clear_clicked = st.button("🗑 Clear Chat", use_container_width=True)

if ask_clicked and user_question:
    with st.spinner("✦ Thinking..."):
        answer = ask_mistral(user_question)
        st.session_state.chat_history.append({
            "q": user_question, "a": answer,
            "t": datetime.now().strftime("%I:%M %p"),
            "mode": st.session_state.output_mode,
            "voice": st.session_state.voice_type
        })
        if st.session_state.output_mode == "voice":
            st.session_state.pending_audio = speak_text(answer, st.session_state.voice_type)
        st.rerun()

if clear_clicked:
    st.session_state.chat_history = []
    st.session_state.pending_audio = None
    st.rerun()

# CONVERSATION
if st.session_state.chat_history:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">💬 Conversation</div>', unsafe_allow_html=True)
    for chat in reversed(st.session_state.chat_history[-15:]):
        voice_icon = ""
        if chat.get("mode") == "voice":
            voice_icon = " " + {"man":"👨🔊","woman":"👩🔊","realistic":"🎭🔊"}.get(chat.get("voice","man"),"🔊")
        st.markdown(f'<div class="user-bubble"><strong>You</strong><br>{chat["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'''<div class="ai-bubble">
            <div class="ai-name">✦ Mesta{voice_icon}</div>
            {chat["a"]}
            <div class="msg-time">{chat["t"]}</div>
        </div>''', unsafe_allow_html=True)

st.markdown('<div class="footer">✦ Mesta AI &nbsp;·&nbsp; Created by Nirbhay &nbsp;·&nbsp; Powered by Mistral AI</div>', unsafe_allow_html=True)