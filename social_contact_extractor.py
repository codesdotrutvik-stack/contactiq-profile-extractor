import streamlit as st
import requests
import re
import json
from googlesearch import search
from bs4 import BeautifulSoup
from datetime import datetime

MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

st.set_page_config(page_title="CompanyIQ", page_icon="🏢", layout="centered")

st.markdown("""
<div style="text-align:center;padding:1.5rem 0;">
    <h1 style="background:linear-gradient(135deg,#0EA5E9,#6366F1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏢 CompanyIQ</h1>
    <p style="color:#666;">Extract company info from Google + AI</p>
</div>
""", unsafe_allow_html=True)

company_name = st.text_input("Company Name", placeholder="Vasundhara Infotech LLP")

if st.button("🔍 Extract", use_container_width=True):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        with st.spinner(f"🔍 Searching for '{company_name}'..."):
            try:
                # ── Step 1: Google Search ──
                query = f"{company_name} company contact phone email address website"
                urls = list(search(query, num_results=5))
                
                result = {
                    'name': company_name,
                    'website': 'Not found',
                    'phone': 'Not found',
                    'email': 'Not found',
                    'address': 'Not found',
                    'description': 'Not found',
                    'source': 'Google Search + Mistral AI'
                }
                
                # ── Step 2: Visit first URL ──
                if urls:
                    first_url = urls[0]
                    result['website'] = first_url.replace('https://', '').replace('www.', '').split('/')[0]
                    
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        response = requests.get(first_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            text = soup.get_text(separator=' ', strip=True)
                            
                            # Phone
                            phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', text)
                            if phone_match:
                                result['phone'] = phone_match.group(1).strip()
                            
                            # Email
                            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                            if email_match:
                                result['email'] = email_match.group(0).strip()
                            
                            # Address
                            address_match = re.search(r'\d{1,5}\s[\w\s]{2,40}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd)[\w\s,\.]{0,60}', text, re.IGNORECASE)
                            if address_match:
                                result['address'] = address_match.group(0).strip()
                    except:
                        pass
                
                # ── Step 3: Mistral AI ──
                prompt = f"""
                Provide information about this company: {company_name}
                Return JSON: {{"founded":"", "founder":"", "ceo":"", "headquarters":"", "industry":"", "employees":""}}
                """
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
                
                # ── Display ──
                st.success(f"✅ Information for '{result['name']}' extracted!")
                st.markdown("---")
                st.markdown(f"### 🏢 {result['name']}")
                st.caption(f"📌 Source: {result['source']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**📅 Founded:** {result.get('founded', 'Not found')}")
                    st.markdown(f"**👤 Founder:** {result.get('founder', 'Not found')}")
                    st.markdown(f"**👔 CEO:** {result.get('ceo', 'Not found')}")
                    st.markdown(f"**📧 Email:** {result['email']}")
                with col2:
                    st.markdown(f"**📍 Headquarters:** {result.get('headquarters', 'Not found')}")
                    st.markdown(f"**🏭 Industry:** {result.get('industry', 'Not found')}")
                    st.markdown(f"**👥 Employees:** {result.get('employees', 'Not found')}")
                    st.markdown(f"**📞 Phone:** {result['phone']}")
                
                if result['website'] != 'Not found':
                    st.markdown(f"**🌐 Website:** [{result['website']}](https://{result['website']})")
                if result['address'] != 'Not found':
                    st.markdown(f"**📍 Address:** {result['address']}")
                
                st.markdown("---")
                st.caption(f"🕐 Extracted: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
                with st.expander("📋 Raw Data"):
                    st.json(result)
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("💡 Try installing: pip install googlesearch-python")