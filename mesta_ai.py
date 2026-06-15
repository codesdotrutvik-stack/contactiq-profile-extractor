import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Mesta AI", page_icon="✨", layout="wide")

# ============================================================
# SIMPLE CSS
# ============================================================
st.markdown("""
<style>
.stApp {
    background: #f8fafc;
}
.block-container {
    padding: 2rem;
}
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
.msg-time {
    font-size: 0.6rem;
    color: #888;
    margin-top: 4px;
}
</style>

<script>
function speakText(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'en-US';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
        document.getElementById('statusMsg').innerHTML = '🔊 Speaking...';
        msg.onend = function() {
            document.getElementById('statusMsg').innerHTML = '● Ready';
        };
    }
}
</script>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.title("✨ Mesta AI")
st.caption("Intelligent Assistant")

# ============================================================
# STATUS
# ============================================================
st.markdown('<p id="statusMsg" style="text-align:center;color:#64748b;">● Ready</p>', unsafe_allow_html=True)

# ============================================================
# CONFIG
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

# ============================================================
# INPUT
# ============================================================
st.markdown("### 💬 Ask Mesta")

user_input = st.text_input("", placeholder="Type your question here...", key="user_input", label_visibility="collapsed")

col1, col2 = st.columns([1, 4])
with col1:
    ask_clicked = st.button("🔊 Ask", type="primary", use_container_width=True)
with col2:
    clear_clicked = st.button("🗑️ Clear", use_container_width=True)

# ============================================================
# PROCESS
# ============================================================
if ask_clicked and user_input:
    with st.spinner("✨ Thinking..."):
        answer = ask_mistral(user_input)
        st.session_state.chat_history.append({
            "q": user_input,
            "a": answer,
            "t": datetime.now().strftime("%I:%M %p")
        })
        # Speak the answer
        safe_answer = answer.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        st.markdown(f'<script>speakText("{safe_answer}");</script>', unsafe_allow_html=True)
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
                safe_answer = answer.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
                st.markdown(f'<script>speakText("{safe_answer}");</script>', unsafe_allow_html=True)
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