import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

# ── MISTRAL API KEY ────────────────────────────────────────────
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="ContactIQ — Social Contact Extractor",
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
    company_name = st.text_input("Company Name", placeholder="Vasundhara Infotech LLP", label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    extract_btn = st.button("🔍 Extract Data", use_container_width=True)

# ════════════════════════════════════════════════════════════════
# ── GITHUB EXTRACTION ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_github_profile(username):
    try:
        url = f"https://api.github.com/users/{username}"
        headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'ContactIQ'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
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
                'profile_url': data.get('html_url', ''),
                'avatar_url': data.get('avatar_url', '')
            }
        elif response.status_code == 404:
            return {'status': 'error', 'message': f"User '{username}' not found"}
        else:
            return {'status': 'error', 'message': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# ════════════════════════════════════════════════════════════════
# ── COMPANY EXTRACTION (Google Search + Mistral AI) ──────────
# ════════════════════════════════════════════════════════════════

def google_search_company(query):
    """Search Google and extract company info"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}+company+contact"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        info = {
            'phone': None,
            'email': None,
            'website': None,
            'address': None,
            'description': None,
            'founder': None,
            'employees': None
        }
        
        # Phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', text)
        if phone_match:
            info['phone'] = phone_match.group(1).strip()
        
        # Email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            info['email'] = email_match.group(0).strip()
        
        # Website
        website_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if website_match:
            info['website'] = website_match.group(1).strip()
        
        # Address
        address_match = re.search(r'\d{1,5}\s[\w\s]{2,40}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd|Highway|Hwy)[\w\s,\.]{0,60}', text, re.IGNORECASE)
        if address_match:
            info['address'] = address_match.group(0).strip()
        
        # Description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            info['description'] = meta_desc.get('content', '')[:300]
        
        # Employees
        employees_match = re.search(r'(\d+)\s*(?:employees|staff|people|team)', text, re.IGNORECASE)
        if employees_match:
            info['employees'] = employees_match.group(1)
        
        return info
    except:
        return None

def call_mistral_company(company_name):
    """Call Mistral AI for additional company details"""
    try:
        prompt = f"""
        Based on your knowledge, provide information about this company:
        {company_name}
        
        Return ONLY JSON:
        {{
            "founded": "year or Not found",
            "founder": "name or Not found",
            "ceo": "name or Not found",
            "headquarters": "location or Not found",
            "industry": "sector or Not found"
        }}
        """
        
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_KEY}", "Content-Type": "application/json"},
            json={
                "model": "mistral-small-latest",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            raw = data['choices'][0]['message']['content']
            match = re.search(r'\{[\s\S]*\}', raw)
            if match:
                return json.loads(match.group())
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
        'source': 'Google Search + Mistral AI'
    }
    
    try:
        # Step 1: Google Search
        google_data = google_search_company(company_name)
        if google_data:
            for key, value in google_data.items():
                if value:
                    if key == 'phone':
                        result['phone'] = value
                    elif key == 'email':
                        result['email'] = value
                    elif key == 'website':
                        result['website'] = value
                    elif key == 'address':
                        result['address'] = value
                    elif key == 'description':
                        result['description'] = value
                    elif key == 'employees':
                        result['employees'] = value
                    elif key == 'founder':
                        result['founder'] = value
        
        # Step 2: Mistral AI
        mistral_data = call_mistral_company(company_name)
        if mistral_data:
            for key in ['founded', 'founder', 'ceo', 'headquarters', 'industry']:
                if mistral_data.get(key) and mistral_data[key] != 'Not found':
                    result[key] = mistral_data[key]
        
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
            with st.spinner(f"🔍 Fetching @{username}..."):
                result = get_github_profile(username)
            
            if result['status'] == 'error':
                st.error(f"❌ {result['message']}")
            else:
                st.success(f"✅ Profile @{result['username']} extracted!")
                st.markdown("---")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(result['avatar_url'], width=100)
                with col2:
                    st.markdown(f"### {result['name']}")
                    st.caption(f"@{result['username']}")
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
                    st.markdown(f"**🔗 Profile:** [View]({result['profile_url']})")
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("📦 Repos", result['public_repos'])
                col2.metric("👥 Followers", result['followers'])
                col3.metric("👤 Following", result['following'])
                
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
        """)
    else:
        st.markdown("""
        ### 🏢 Try These Companies
        - `Vasundhara Infotech LLP`
        - `Google`
        - `Narola Infotech`
        - `Microsoft`
        - `Codedsot Solutions LLP`
        - `Amazon`
        - `Infosys`
        - `TCS`
        """)

# ── FOOTER ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem 0 0.5rem 0; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 2rem;">
    ContactIQ · Social Contact Extractor<br>
    <span style="font-size: 0.7rem;">GitHub API · Google Search · Mistral AI</span>
</div>
""", unsafe_allow_html=True)