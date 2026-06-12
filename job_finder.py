import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Job Finder AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== CUSTOM CSS ======================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
   
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .header h1 { color: white; margin: 0; font-size: 1.8rem; }
    .header p { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 0.85rem; }

    /* Floating Chat Button */
    .floating-chat-btn {
        position: fixed;
        bottom: 25px;
        right: 25px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        cursor: pointer;
        z-index: 1000;
        border: none;
    }

    /* Chat Window */
    .chat-window {
        position: fixed;
        bottom: 90px;
        right: 25px;
        width: 380px;
        height: 520px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        z-index: 999;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }

    .chat-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        font-weight: 600;
    }

    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        background: #f8fafc;
    }

    .chat-input-area {
        padding: 1rem;
        border-top: 1px solid #e5e7eb;
        background: white;
    }

    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    .api-success, .saved-badge {
        background: #d1fae5;
        color: #065f46;
        padding: 0.6rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>💼 Job Finder AI</h1>
    <p>Live jobs from Adzuna API • Save jobs permanently • Get company insights</p>
</div>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
ADZUNA_APP_ID = "cab85cad"
ADZUNA_API_KEY = "9c920a8f1b37a639553a98541e0ba2e8"
MISTRAL_API_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

CITIES = ["All", "Ahmedabad", "Surat", "Rajkot", "Vadodara", "Bangalore", "Mumbai", "Hyderabad"]
POPULAR_ROLES = ["Python Developer", "Shopify Developer", "Frontend Developer", "WordPress Developer", "Full Stack Developer", "Data Scientist", "React Developer", "Java Developer", "DevOps Engineer"]

SAVED_JOBS_FILE = "saved_jobs.json"

# ====================== FUNCTIONS ======================
def load_saved_jobs():
    try:
        if os.path.exists(SAVED_JOBS_FILE):
            with open(SAVED_JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except:
        return []

def save_saved_jobs(jobs):
    try:
        with open(SAVED_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def fetch_jobs(role, location):
    location_name = location if location != "All" else "India"
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": 12,
        "what": role,
        "where": location_name,
        "sort_by": "date"
    }
    try:
        response = requests.get(url, params=params, timeout=25)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for result in data.get("results", []):
                salary_min = result.get("salary_min", 0)
                salary_max = result.get("salary_max", 0)
                if salary_min and salary_max and salary_min > 0:
                    salary = f"₹{int(salary_min/100000)}-{int(salary_max/100000)} LPA"
                elif salary_min and salary_min > 0:
                    salary = f"₹{int(salary_min/100000)} LPA"
                else:
                    salary = "Not disclosed"

                company = result.get("company", {})
                company_name = company.get("display_name", "Private Limited") if isinstance(company, dict) else "Private Limited"

                jobs.append({
                    "id": result.get("id"),
                    "title": result.get("title", "N/A"),
                    "company": company_name,
                    "location": result.get("location", {}).get("display_name", location_name) if isinstance(result.get("location"), dict) else location_name,
                    "salary": salary,
                    "description": result.get("description", "")[:400] if result.get("description") else "No description",
                    "url": result.get("redirect_url", "#"),
                    "created": result.get("created", "Recently")
                })
            return jobs, None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

def get_company_details(company_name, job_title):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Provide brief info about {company_name} for {job_title} role.\nReturn format:\n- Industry:\n- Required Experience:\n- Key Skills:\n- Interview Tips:"
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return f"- Industry: Technology\n- Company: {company_name}"

def chat_with_mistral(message, history):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    
    messages = [{"role": "system", "content": "You are a helpful career advisor and job search assistant. Help users with job search, resume tips, interview preparation, and career advice."}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    data = {
        "model": "mistral-small-latest",
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=20)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Sorry, I'm unable to respond right now."

# ====================== SESSION STATE ======================
if "saved_jobs" not in st.session_state:
    st.session_state.saved_jobs = load_saved_jobs()
if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "searched" not in st.session_state:
    st.session_state.searched = False
if "company_details" not in st.session_state:
    st.session_state.company_details = {}
if "search_role" not in st.session_state:
    st.session_state.search_role = "Python Developer"
if "search_city" not in st.session_state:
    st.session_state.search_city = "Surat"
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("### 🔍 Search Jobs")
    st.session_state.search_role = st.text_input("Job Role", value=st.session_state.search_role)
    st.session_state.search_city = st.selectbox("City", CITIES, index=CITIES.index(st.session_state.search_city) if st.session_state.search_city in CITIES else 0)
    
    if st.button("🔍 Search Jobs", use_container_width=True, type="primary"):
        with st.spinner("Searching..."):
            jobs, error = fetch_jobs(st.session_state.search_role, st.session_state.search_city)
            if jobs:
                st.session_state.jobs = jobs
                st.session_state.searched = True
                st.session_state.company_details = {}
                st.success(f"✅ Found {len(jobs)} jobs")
            else:
                st.session_state.jobs = []
                st.session_state.searched = True
                st.error(error)

    st.markdown("---")
    st.markdown("### 📌 Quick Filters")
    for role in POPULAR_ROLES[:5]:
        if st.button(role, key=f"quick_{role}", use_container_width=True):
            st.session_state.search_role = role
            st.rerun()

    st.markdown("---")
    st.success("✅ API Active")
    st.markdown("---")
    st.markdown(f"### 📌 Saved Jobs ({len(st.session_state.saved_jobs)})")
    if st.button("🗑️ Clear All Saved", use_container_width=True):
        st.session_state.saved_jobs = []
        save_saved_jobs([])
        st.rerun()

# ====================== LOAD DEFAULT JOBS ======================
if not st.session_state.searched and not st.session_state.jobs:
    with st.spinner("Loading jobs..."):
        default_jobs, _ = fetch_jobs("Python Developer", "Surat")
        if default_jobs:
            st.session_state.jobs = default_jobs
            st.session_state.searched = True

# ====================== MAIN CONTENT ======================
if st.session_state.searched and st.session_state.jobs:
    st.markdown(f"""
    <div class="api-success">
        🎯 {len(st.session_state.jobs)} jobs found for '{st.session_state.search_role}' in {st.session_state.search_city}
    </div>
    """, unsafe_allow_html=True)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{len(st.session_state.jobs)}</div><div class="stat-label">Jobs Found</div></div>', unsafe_allow_html=True)
    with col2:
        companies = len(set(j.get("company") for j in st.session_state.jobs))
        st.markdown(f'<div class="stat-box"><div class="stat-number">{companies}</div><div class="stat-label">Companies</div></div>', unsafe_allow_html=True)
    with col3:
        locations = len(set(j.get("location") for j in st.session_state.jobs))
        st.markdown(f'<div class="stat-box"><div class="stat-number">{locations}</div><div class="stat-label">Locations</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    for idx, job in enumerate(st.session_state.jobs):
        is_saved = any(j.get('id') == job.get('id') for j in st.session_state.saved_jobs)
        with st.expander(f"💼 {job['title']} - {job['company']} (📍 {job['location']})", expanded=False):
            st.markdown(f"**Company:** {job['company']}  |  **Location:** {job['location']}  |  **Salary:** {job['salary']}")
            st.markdown("#### 📝 Description")
            st.write(job['description'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if not is_saved:
                    if st.button("⭐ Save", key=f"save_{idx}"):
                        st.session_state.saved_jobs.append(job)
                        save_saved_jobs(st.session_state.saved_jobs)
                        st.success("Saved!")
                        st.rerun()
                else:
                    st.markdown('<span class="saved-badge">✓ Saved</span>', unsafe_allow_html=True)
            with col2:
                st.markdown(f"[📋 Apply Now]({job['url']})", unsafe_allow_html=True)
            with col3:
                if st.button("🏢 Company Info", key=f"info_{idx}"):
                    details = get_company_details(job['company'], job['title'])
                    st.session_state.company_details[idx] = details
                    st.rerun()
            if idx in st.session_state.company_details:
                st.info(st.session_state.company_details[idx])

# Saved Jobs Section
if st.session_state.saved_jobs:
    st.markdown("---")
    st.markdown("## ⭐ Saved Jobs")
    for idx, job in enumerate(st.session_state.saved_jobs):
        with st.expander(f"💼 {job['title']} - {job['company']}", expanded=False):
            st.write(f"**Location:** {job['location']} | **Salary:** {job['salary']}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"[📋 Apply]({job['url']})", unsafe_allow_html=True)
            with col2:
                if st.button("❌ Remove", key=f"remove_{idx}"):
                    st.session_state.saved_jobs.pop(idx)
                    save_saved_jobs(st.session_state.saved_jobs)
                    st.rerun()

# ====================== FLOATING CHATBOT ======================
# Chat Button
if st.button("💬", key="chat_btn", help="Talk to AI Career Assistant"):
    st.session_state.chat_open = not st.session_state.chat_open

# Chat Window
if st.session_state.chat_open:
    with st.container():
        st.markdown("""
        <div class="chat-window">
            <div class="chat-header">
                💼 AI Career Assistant <span style="float:right; cursor:pointer;" onclick="this.closest('.chat-window').style.display='none';">✕</span>
            </div>
            <div class="chat-messages" id="chat-messages">
        """, unsafe_allow_html=True)

        # Display chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**Assistant:** {msg['content']}")

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat Input
        user_input = st.text_input("Ask anything about jobs, careers, interviews...", key="chat_input", label_visibility="collapsed")
        
        if st.button("Send", key="send_chat"):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                with st.spinner("Thinking..."):
                    reply = chat_with_mistral(user_input, st.session_state.chat_history)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("💼 Job Finder AI | Powered by Adzuna API + Mistral AI")