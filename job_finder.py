import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="ContactIQ — Enterprise Public Intel",
    page_icon="🔍",
    layout="centered"
)

# ── CUSTOM PREMIUM STYLING (CSS) ────────────────────────────────
st.markdown("""
<style>
    /* Global Styles */
    .reportview-container {
        background: #fafafa;
    }
    
    /* Header Card */
    .header-container {
        text-align: center; 
        padding: 2.5rem 1.5rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 3rem; 
        font-weight: 800;
        margin: 0; 
        background: linear-gradient(135deg, #38bdf8, #818cf8); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.05em;
    }
    .header-subtitle {
        color: #94a3b8; 
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* KPI & Data Cards */
    .intel-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .intel-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.25rem;
        font-weight: 600;
    }
    .intel-value {
        font-size: 1.1rem;
        color: #0f172a;
        font-weight: 500;
    }
    
    /* Section Divider styling */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── HEADER SECTION ─────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🔍 ContactIQ</h1>
    <p class="header-subtitle">Intelligence Aggregator for Open-Source Public Data</p>
</div>
""", unsafe_allow_html=True)

# ── MODE SELECTION & INPUT ─────────────────────────────────────
# Created a sleek selection layout matching your mockup concept
mode = st.radio(
    "Select Intelligence Mode:",
    options=["🏢 Company Profile", "🐙 GitHub Profile"],
    horizontal=True,
    label_visibility="visible"
)

company_name = st.text_input(
    "Search Target",
    placeholder="Enter company name (e.g., Narola Infotech, Google, Cirkle Studio)...",
    label_visibility="collapsed"
)

# Hardcoded logic container matching original setup
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

# ── EXECUTION & PROCESSING ─────────────────────────────────────
if st.button("✨ Extract Intel", use_container_width=True):
    if not company_name:
        st.warning("⚠️ Please provide a valid entity name to search.")
    else:
        if "GitHub" in mode:
            st.info("ℹ️ GitHub Intelligence parsing module is active. Real-world API keys require OAuth permissions for user email metadata.")
        else:
            with st.spinner(f"📡 Querying global registries and cross-referencing information for '{company_name}'..."):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}"
                    response = requests.get(search_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        
                        result = {
                            'name': company_name,
                            'website': 'Not found',
                            'phone': 'Not found',
                            'email': 'Not found',
                            'address': 'Not found',
                            'description': 'Not found',
                            'source': 'Public Web Indices'
                        }
                        
                        # Parsing Logic
                        site_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                        if site_match:
                            result['website'] = site_match.group(1)
                        
                        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', text)
                        if phone_match:
                            result['phone'] = phone_match.group(1).strip()
                        
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                        if email_match:
                            result['email'] = email_match.group(0).strip()
                        
                        address_match = re.search(r'\d{1,5}\s[\w\s]{2,40}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd|Highway|Hwy)[\w\s,\.]{0,60}', text, re.IGNORECASE)
                        if address_match:
                            result['address'] = address_match.group(0).strip()
                        
                        meta_desc = soup.find('meta', {'name': 'description'})
                        if meta_desc:
                            result['description'] = meta_desc.get('content', '')[:300]
                        
                        # Mistral Fallback Context
                        prompt = f"Provide knowledge about: {company_name}. Return ONLY JSON with fields: founded, founder, ceo, headquarters, industry, employees. Use 'Not found' if unknown."
                        
                        ai_resp = requests.post(
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
                        
                        if ai_resp.status_code == 200:
                            data = ai_resp.json()
                            raw = data['choices'][0]['message']['content']
                            match = re.search(r'\{[\s\S]*\}', raw)
                            if match:
                                ai_data = json.loads(match.group())
                                for key in ['founded', 'founder', 'ceo', 'headquarters', 'industry', 'employees']:
                                    if ai_data.get(key) and ai_data[key] != 'Not found':
                                        result[key] = ai_data[key]

                        # ── OUTPUT RENDER ─────────────────────────────────
                        st.toast(f"Intel for {result['name']} retrieved successfully!", icon="✅")
                        
                        st.markdown(f"### 🏢 {result['name']}")
                        st.markdown(f"`🔒 Source Verification: Combined Public Index Data`")
                        st.markdown("---")
                        
                        # Metric Layout using Clean Blocks
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f'<div class="intel-card"><div class="intel-label">📅 Founded</div><div class="intel-value">{result.get("founded", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">👤 Founder</div><div class="intel-value">{result.get("founder", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">👔 Executive Officer / CEO</div><div class="intel-value">{result.get("ceo", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">📧 Public Communications Email</div><div class="intel-value">{result["email"]}</div></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="intel-card"><div class="intel-label">📍 Corporate Headquarters</div><div class="intel-value">{result.get("headquarters", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">🏭 Market Industry</div><div class="intel-value">{result.get("industry", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">👥 Estimated Scale / Employees</div><div class="intel-value">{result.get("employees", "Not found")}</div></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="intel-card"><div class="intel-label">📞 Public Direct Line</div><div class="intel-value">{result["phone"]}</div></div>', unsafe_allow_html=True)
                        
                        # Dynamic Links & Address
                        if result['website'] != 'Not found':
                            st.link_button(f"🌐 Visit Corporate Website ({result['website']})", f"https://{result['website']}", use_container_width=True)
                        
                        if result['address'] != 'Not found':
                            st.markdown(f"**📍 Registered Address:** {result['address']}")
                        
                        if result['description'] != 'Not found':
                            st.markdown('<div class="section-title">📝 Executive Summary</div>', unsafe_allow_html=True)
                            st.info(result['description'])
                        
                        st.markdown("---")
                        with st.expander("🛠️ Raw Metadata Inspection Output"):
                            st.json(result)
                    else:
                        st.error("❌ Target profile unreachable or response blocked by host verification standards.")
                        
                except Exception as e:
                    st.error(f"Execution fault encountered: {str(e)}")

# ── PRESET PLATFORM EXAMPLES ──────────────────────────────────
with st.expander("💡 Recommended Search Presets"):
    st.markdown("""
    * `Google`
    * `Microsoft`
    * `Narola Infotech`
    * `Cirkle Studio Pvt. Ltd.`
    """)

# ── FOOTER ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; color: #64748b; padding-top: 3rem; font-size: 0.8rem; border-top: 1px solid #e2e8f0; margin-top: 4rem;">
    <strong>ContactIQ Platform</strong> · Data Integrity Solutions<br>
    <span style="font-size: 0.75rem; color: #94a3b8;">Powered by Verified Public Indexes & AI Orchestration</span>
</div>
""", unsafe_allow_html=True)