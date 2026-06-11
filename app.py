import streamlit as st
import requests
import json
from datetime import datetime
import base64

api_key = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"
url = "https://api.mistral.ai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #bfdbfe;
        margin: 0;
    }
    .stButton button {
        background-color: #1e3a8a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #3b82f6;
    }
    .user-msg {
        background-color: #dbeafe;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #1e3a8a;
    }
    .ai-msg {
        background-color: white;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #10b981;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .quiz-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border: 1px solid #e5e7eb;
    }
    .score-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    .progress-bar {
        background-color: #e5e7eb;
        border-radius: 10px;
        height: 10px;
        margin: 10px 0;
    }
    .progress-fill {
        background-color: #3b82f6;
        border-radius: 10px;
        height: 10px;
        width: 0%;
    }
    .theme-card {
        cursor: pointer;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid transparent;
    }
    .theme-card:hover {
        border-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📚 AI Study Buddy Pro</h1>
    <p>Your Personal AI Teacher – Learn Anything, Anytime!</p>
</div>
""", unsafe_allow_html=True)

if "chat" not in st.session_state:
    st.session_state.chat = []
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "theme" not in st.session_state:
    st.session_state.theme = "blue"
if "learning_progress" not in st.session_state:
    st.session_state.learning_progress = {}

def ask_ai(question, mode):
    if mode == "Simple (Like I'm 5)":
        prompt = "Explain like the student is 5 years old. Very simple words. Short sentences."
    elif mode == "Detailed":
        prompt = "Explain in detail with examples."
    else:
        prompt = "Explain clearly and simply."
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

def generate_quiz(topic, num_questions):
    prompt = f"""Generate {num_questions} multiple choice questions about {topic}. 
    Format EXACTLY like this:
    Q1: [Question]
    A) [Option 1]
    B) [Option 2]
    C) [Option 3]
    D) [Option 4]
    Answer: [Letter]
    
    Q2: [Question]
    ..."""
    
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()["choices"][0]["message"]["content"]

def parse_quiz(quiz_text, num_q):
    questions = []
    lines = quiz_text.split('\n')
    current_q = {}
    for line in lines:
        line = line.strip()
        if line.startswith('Q') and ':' in line:
            if current_q:
                questions.append(current_q)
            current_q = {'question': line.split(':', 1)[1].strip(), 'options': [], 'answer': ''}
        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
            current_q['options'].append(line)
        elif line.startswith('Answer:'):
            current_q['answer'] = line.split(':')[1].strip()
    if current_q:
        questions.append(current_q)
    return questions[:num_q]

def update_progress(topic):
    if topic not in st.session_state.learning_progress:
        st.session_state.learning_progress[topic] = 0
    st.session_state.learning_progress[topic] = min(100, st.session_state.learning_progress[topic] + 10)

def download_chat():
    chat_text = f"AI Study Buddy Chat - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for msg in st.session_state.chat:
        chat_text += f"🧑‍🎓 You: {msg['q']}\n\n"
        chat_text += f"🤖 AI: {msg['a']}\n\n"
        chat_text += "="*50 + "\n\n"
    return chat_text

tabs = st.tabs(["💬 Chat", "📝 Quiz", "🎨 Themes", "📊 Progress", "💾 History"])

with tabs[0]:
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### ⚙️ Settings")
        mode = st.selectbox("Select Mode", ["Simple (Like I'm 5)", "Normal", "Detailed"])
    
    with col1:
        st.markdown("### 💬 Ask your question")
        user_input = st.text_area("", height=100, placeholder="Example: What is Python? Explain loops...", key="chat_input")
        
        if st.button("🚀 Ask AI", use_container_width=True) and user_input:
            with st.spinner("🧠 AI is thinking..."):
                answer = ask_ai(user_input, mode)
                st.session_state.chat.append({"q": user_input, "a": answer, "time": datetime.now().strftime("%H:%M")})
                update_progress("General Learning")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 💬 Conversation")
    
    if len(st.session_state.chat) == 0:
        st.info("No messages yet. Ask me something!")
    
    for item in reversed(st.session_state.chat[-20:]):
        st.markdown(f'<div class="user-msg"><strong>🧑‍🎓 You</strong> <span style="color:gray;font-size:10px;">{item.get("time", "")}</span><br>{item["q"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-msg"><strong>🤖 AI Teacher</strong><br>{item["a"]}</div>', unsafe_allow_html=True)
        st.markdown("---")
    
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat = []
            st.rerun()
    with col2:
        if st.button("📥 Download Chat", use_container_width=True):
            chat_content = download_chat()
            b64 = base64.b64encode(chat_content.encode()).decode()
            href = f'<a href="data:text/plain;base64,{b64}" download="chat_history.txt">📁 Click to Download</a>'
            st.markdown(href, unsafe_allow_html=True)

with tabs[1]:
    st.markdown("### 📝 Quiz Generator")
    
    col1, col2 = st.columns(2)
    with col1:
        quiz_topic = st.text_input("Quiz Topic:", placeholder="Python, AI, History, Science...")
    with col2:
        num_q = st.slider("Number of Questions:", 3, 10, 5)
    
    if st.button("🎯 Generate Quiz", use_container_width=True) and quiz_topic:
        with st.spinner("Creating quiz..."):
            quiz_raw = generate_quiz(quiz_topic, num_q)
            st.session_state.quiz_data = parse_quiz(quiz_raw, num_q)
            st.session_state.quiz_score = 0
            st.session_state.quiz_answers = {}
            st.rerun()
    
    if st.session_state.quiz_data:
        st.markdown("---")
        st.markdown(f"### 📋 Quiz: {quiz_topic}")
        
        for i, q in enumerate(st.session_state.quiz_data):
            with st.container():
                st.markdown(f'<div class="quiz-card"><b>Q{i+1}: {q["question"]}</b></div>', unsafe_allow_html=True)
                
                if q['options']:
                    answer = st.radio("", q['options'], key=f"quiz_{i}", index=None, label_visibility="collapsed")
                    if answer:
                        selected_letter = answer[0]
                        is_correct = (selected_letter == q['answer'])
                        if is_correct:
                            st.success("✅ Correct!")
                        else:
                            st.error(f"❌ Wrong! Correct answer: {q['answer']}")
        
        if st.button("✅ Submit Quiz", use_container_width=True):
            score = 0
            for i, q in enumerate(st.session_state.quiz_data):
                pass
            st.balloons()
            st.success(f"🎉 Quiz Completed! Check your answers above!")
    
    st.markdown("---")
    st.markdown("### 🔥 Popular Quiz Topics")
    popular_topics = ["Python Programming", "Machine Learning", "World History", "General Science", "English Grammar"]
    cols = st.columns(3)
    for i, topic in enumerate(popular_topics):
        with cols[i % 3]:
            if st.button(topic, use_container_width=True):
                with st.spinner("Creating quiz..."):
                    quiz_raw = generate_quiz(topic, 5)
                    st.session_state.quiz_data = parse_quiz(quiz_raw, 5)
                    st.rerun()

with tabs[2]:
    st.markdown("### 🎨 Choose Your Theme")
    
    themes = {
        "Blue": "#1e3a8a",
        "Green": "#15803d",
        "Purple": "#6d28d9",
        "Orange": "#ea580c",
        "Red": "#dc2626",
        "Pink": "#db2777"
    }
    
    cols = st.columns(3)
    for i, (theme_name, theme_color) in enumerate(themes.items()):
        with cols[i % 3]:
            if st.button(f"🎨 {theme_name}", use_container_width=True):
                st.session_state.theme = theme_color
                st.markdown(f"""
                <style>
                    .stButton button {{ background-color: {theme_color}; }}
                    .main-header {{ background: linear-gradient(135deg, {theme_color} 0%, #60a5fa 100%); }}
                    .user-msg {{ border-left-color: {theme_color}; }}
                </style>
                """, unsafe_allow_html=True)
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Font Size")
    font_size = st.slider("Adjust Font Size", 12, 24, 14)
    st.markdown(f"<style>body, .stMarkdown {{ font-size: {font_size}px; }}</style>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎨 Current Theme")
    st.markdown(f'<div style="background-color: {st.session_state.theme}; padding: 20px; border-radius: 10px; text-align: center; color: white;">Active Theme</div>', unsafe_allow_html=True)

with tabs[3]:
    st.markdown("### 📊 Your Learning Progress")
    
    total_topics = len(st.session_state.learning_progress)
    if total_topics > 0:
        avg_progress = sum(st.session_state.learning_progress.values()) / total_topics
        st.markdown(f'<div class="score-card"><h2>📈 Overall Progress</h2><h1>{int(avg_progress)}%</h1></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📚 Topics Covered")
        
        for topic, progress in st.session_state.learning_progress.items():
            st.markdown(f"**{topic}**")
            st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {progress}%;"></div></div>', unsafe_allow_html=True)
            st.caption(f"{progress}% completed")
            st.markdown("---")
    else:
        st.info("No learning data yet. Start asking questions to track your progress!")
    
    st.markdown("---")
    st.markdown("### 🏆 Achievements")
    
    achievements = []
    if len(st.session_state.chat) >= 10:
        achievements.append("🗣️ Chat Master (10+ messages)")
    if len(st.session_state.learning_progress) >= 3:
        achievements.append("📚 Multi-Topic Learner")
    if st.session_state.quiz_data:
        achievements.append("🎯 Quiz Taker")
    
    if achievements:
        for ach in achievements:
            st.success(f"🏅 {ach}")
    else:
        st.info("Keep learning to unlock achievements!")

with tabs[4]:
    st.markdown("### 💾 Chat History")
    
    if len(st.session_state.chat) > 0:
        st.markdown(f"**Total Messages:** {len(st.session_state.chat)}")
        st.markdown(f"**Last Activity:** {st.session_state.chat[-1].get('time', 'N/A') if st.session_state.chat else 'N/A'}")
        
        st.markdown("---")
        st.markdown("### 📜 Recent Conversations")
        
        for i, msg in enumerate(reversed(st.session_state.chat[-15:])):
            with st.expander(f"Q: {msg['q'][:50]}..."):
                st.markdown(f"**🧑‍🎓 Question:** {msg['q']}")
                st.markdown(f"**🤖 Answer:** {msg['a'][:300]}...")
                st.caption(f"Time: {msg.get('time', 'N/A')}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export All Chats", use_container_width=True):
                chat_content = download_chat()
                b64 = base64.b64encode(chat_content.encode()).decode()
                href = f'<a href="data:text/plain;base64,{b64}" download="full_chat_history.txt">📁 Click to Download</a>'
                st.markdown(href, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ Delete All History", use_container_width=True):
                st.session_state.chat = []
                st.session_state.learning_progress = {}
                st.rerun()
    else:
        st.info("No chat history yet. Start a conversation!")

st.markdown("""
<div style="text-align: center; color: #6b7280; margin-top: 2rem; padding: 1rem;">
    Made with ❤️ using Mistral AI | AI Study Buddy Pro | All Features
</div>
""", unsafe_allow_html=True)