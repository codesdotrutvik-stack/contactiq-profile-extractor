import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time

# ── MISTRAL API KEY ────────────────────────────────────────────
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="ContactIQ — Profile Extractor",
    page_icon="🔍",
    layout="centered"
)

# ── TITLE ──────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0;">
    <h1 style="font-size: 2.8rem; margin: 0; background: linear-gradient(135deg, #0EA5E9, #6366F1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🔍 ContactIQ
    </h1>
    <p style="color: #666; font-size: 1.1rem;">Extract public data from GitHub or Company profiles</p>
</div>
""", unsafe_allow_html=True)

# ── MODE TOGGLE ─────────────────────────────────────────────────
mode = st.radio(
    "Select Mode:",
    ["🐙 GitHub Profile", "🏢 Company Profile"],
    horizontal=True,
    index=0
)

st.markdown("---")

# ── INPUT ──────────────────────────────────────────────────────
if mode == "🐙 GitHub Profile":
    username = st.text_input("GitHub Username", placeholder="octocat", label_visibility="collapsed")
else:
    company_name = st.text_input("Company Name", placeholder="Google or Narola Infotech", label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    extract_btn = st.button("🔍 Extract Data", use_container_width=True)

# ════════════════════════════════════════════════════════════════
# ── GITHUB EXTRACTION ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_github_profile(username):
    """Fetch GitHub profile data using public API"""
    try:
        url = f"https://api.github.com/users/{username}"
        headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'ContactIQ-App'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            created = data.get('created_at', '')
            if created:
                try:
                    created = datetime.strptime(created, '%Y-%m-%dT%H:%M:%SZ').strftime('%d %b %Y')
                except:
                    created = created.split('T')[0]
            
            return {
                'status': 'success',
                'name': data.get('name') or data.get('login', 'Not found'),
                'username': data.get('login', 'Not found'),
                'email': data.get('email') or 'Not public',
                'location': data.get('location') or 'Not found',
                'company': data.get('company') or 'Not found',
                'bio': data.get('bio') or 'Not found',
                'blog': data.get('blog') or 'Not found',
                'twitter': data.get('twitter_username') or 'Not found',
                'public_repos': data.get('public_repos', 0),
                'followers': data.get('followers', 0),
                'following': data.get('following', 0),
                'created_at': created,
                'profile_url': data.get('html_url', ''),
                'avatar_url': data.get('avatar_url', '')
            }
        elif response.status_code == 404:
            return {'status': 'error', 'message': f"User '{username}' not found"}
        elif response.status_code == 403:
            return {'status': 'error', 'message': "Rate limit exceeded. Please try again later."}
        else:
            return {'status': 'error', 'message': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# ════════════════════════════════════════════════════════════════
# ── COMPANY EXTRACTION (Mistral AI + Wikipedia) ──────────────
# ════════════════════════════════════════════════════════════════

def get_wikipedia_data(query):
    """Get company data from Wikipedia"""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'description': data.get('description', '')
            }
    except:
        pass
    return None

def call_mistral_company(company_name, wiki_data):
    """Call Mistral AI to extract company details"""
    try:
        context = f"Company Name: {company_name}\n"
        if wiki_data and wiki_data.get('extract'):
            context += f"Wikipedia: {wiki_data['extract'][:2000]}\n"
        else:
            # If no Wikipedia data, still try with company name
            context += f"Please search your knowledge for company: {company_name}\n"
        
        prompt = f"""
        Extract company information from the following text and your knowledge:
        
        {context}
        
        Extract and return ONLY valid JSON:
        {{
            "name": "company name",
            "founded": "year founded or Not found",
            "founder": "founder name or Not found",
            "ceo": "CEO name or Not found",
            "headquarters": "location or Not found",
            "industry": "industry sector or Not found",
            "employees": "number of employees or Not found",
            "website": "company website or Not found",
            "email": "company email or Not found",
            "phone": "company phone or Not found",
            "address": "company address or Not found",
            "description": "brief description or Not found"
        }}
        """
        
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
            json={
                "model": "mistral-small-latest",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            raw = data['choices'][0]['message']['content']
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                return json.loads(json_match.group())
        return None
    except:
        return None

def get_company_info(company_name):
    """Main function to extract company information"""
    result = {
        'name': company_name,
        'founded': 'Not found',
        'founder': 'Not found',
        'ceo': 'Not found',
        'headquarters': 'Not found',
        'industry': 'Not found',
        'employees': 'Not found',
        'website': 'Not found',
        'email': 'Not found',
        'phone': 'Not found',
        'address': 'Not found',
        'description': 'Not found',
        'source': 'Wikipedia + Mistral AI'
    }
    
    try:
        # Step 1: Get Wikipedia data
        wiki_data = get_wikipedia_data(company_name)
        if wiki_data:
            result['description'] = wiki_data.get('extract', '')[:400]
            result['source'] = 'Wikipedia + Mistral AI'
        else:
            result['source'] = 'Mistral AI (Knowledge)'
        
        # Step 2: Call Mistral AI (with or without Wikipedia data)
        mistral_result = call_mistral_company(company_name, wiki_data)
        if mistral_result:
            for key in ['name', 'founded', 'founder', 'ceo', 'headquarters', 'industry', 
                       'employees', 'website', 'email', 'phone', 'address', 'description']:
                if mistral_result.get(key) and mistral_result[key] != 'Not found':
                    if key == 'name' and 'Not found' not in mistral_result[key]:
                        result[key] = mistral_result[key]
                    elif key != 'name':
                        result[key] = mistral_result[key]
        
        result['status'] = 'success'
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result

# ════════════════════════════════════════════════════════════════
# ── PROCESSING ──────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

if extract_btn:
    if mode == "🐙 GitHub Profile":
        if not username:
            st.warning("Please enter a GitHub username.")
        else:
            username = username.strip().replace('@', '').split('/')[-1]
            with st.spinner(f"🔍 Fetching @{username} from GitHub..."):
                result = get_github_profile(username)
            
            if result['status'] == 'error':
                st.error(f"❌ {result['message']}")
            else:
                st.success(f"✅ Profile @{result['username']} extracted successfully!")
                st.markdown("---")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(result['avatar_url'], width=100)
                with col2:
                    st.markdown(f"### {result['name']}")
                    st.caption(f"@{result['username']} · Joined {result['created_at']}")
                    st.markdown(f"📝 {result['bio']}")
                
                st.markdown("---")
                st.markdown("### 📬 Contact Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**📧 Email:** {result['email']}")
                    st.markdown(f"**📍 Location:** {result['location']}")
                    st.markdown(f"**🏢 Company:** {result['company']}")
                with col2:
                    st.markdown(f"**🌐 Blog:** {result['blog']}")
                    st.markdown(f"**🐦 Twitter:** {result['twitter']}")
                    st.markdown(f"**🔗 Profile:** [View on GitHub]({result['profile_url']})")
                
                st.markdown("---")
                st.markdown("### 📊 GitHub Stats")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Repositories", result['public_repos'])
                with col2:
                    st.metric("👥 Followers", result['followers'])
                with col3:
                    st.metric("👤 Following", result['following'])
                with col4:
                    st.metric("📅 Joined", result['created_at'])
                
                with st.expander("📋 Raw Data"):
                    st.json(result)
    
    else:  # Company Profile
        if not company_name:
            st.warning("Please enter a company name.")
        else:
            with st.spinner(f"🔍 Searching for '{company_name}'..."):
                result = get_company_info(company_name.strip())
            
            if result.get('status') == 'error':
                st.error(f"❌ {result.get('error', 'Unknown error')}")
            else:
                st.success(f"✅ Information for '{result['name']}' extracted!")
                st.markdown("---")
                
                st.markdown(f"### 🏢 {result['name']}")
                st.caption(f"📌 Source: {result['source']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**📅 Founded:** {result['founded']}")
                    st.markdown(f"**👤 Founder:** {result['founder']}")
                    st.markdown(f"**👔 CEO:** {result['ceo']}")
                    st.markdown(f"**📧 Email:** {result['email']}")
                with col2:
                    st.markdown(f"**📍 Headquarters:** {result['headquarters']}")
                    st.markdown(f"**🏭 Industry:** {result['industry']}")
                    st.markdown(f"**👥 Employees:** {result['employees']}")
                    st.markdown(f"**📞 Phone:** {result['phone']}")
                
                if result['website'] != 'Not found':
                    st.markdown(f"**🌐 Website:** [{result['website']}](https://{result['website']})")
                
                if result['address'] != 'Not found':
                    st.markdown(f"**📍 Address:** {result['address']}")
                
                if result['description'] != 'Not found':
                    st.markdown("---")
                    st.markdown("### 📝 About")
                    st.write(result['description'])
                
                st.markdown("---")
                st.caption(f"🕐 Extracted: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
                
                with st.expander("📋 Raw Data"):
                    st.json(result)

# ── SAMPLES ────────────────────────────────────────────────────
with st.expander("💡 Samples"):
    if mode == "🐙 GitHub Profile":
        st.markdown("""
        - `octocat`
        - `torvalds`
        - `gvanrossum`
        - `defunkt`
        """)
    else:
        st.markdown("""
        ### 🏢 Famous Companies
        - `Google`
        - `Microsoft`
        - `Amazon`
        - `Infosys`
        - `TCS`
        
        ### 🏭 Local Companies
        - `Narola Infotech`
        - `Codedsot Solutions LLP`
        - `Zomato`
        """)

# ── FOOTER ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem 0 0.5rem 0; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 2rem;">
    ContactIQ · Profile Extractor<br>
    <span style="font-size: 0.7rem;">GitHub API · Wikipedia · Mistral AI</span>
</div>
""", unsafe_allow_html=True)