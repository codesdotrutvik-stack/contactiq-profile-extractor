import streamlit as st
import requests
import re
import json
from datetime import datetime

MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

st.set_page_config(page_title="CompanyIQ", page_icon="🏢", layout="centered")

st.markdown("""
<div style="text-align:center;padding:1.5rem 0;">
    <h1 style="background:linear-gradient(135deg,#0EA5E9,#6366F1);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏢 CompanyIQ</h1>
    <p style="color:#666;">Extract company info using AI</p>
</div>
""", unsafe_allow_html=True)

company_name = st.text_input("Company Name", placeholder="Vasundhara Infotech LLP")

if st.button("🔍 Extract", use_container_width=True):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        with st.spinner(f"🤖 AI analyzing '{company_name}'..."):
            try:
                prompt = f"""
                Provide detailed information about this company: {company_name}
                
                Return ONLY valid JSON:
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
                        "max_tokens": 400,
                        "temperature": 0.1
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    raw = data['choices'][0]['message']['content']
                    match = re.search(r'\{[\s\S]*\}', raw)
                    if match:
                        result = json.loads(match.group())
                        
                        st.success(f"✅ Information for '{result.get('name', company_name)}' extracted!")
                        st.markdown("---")
                        st.markdown(f"### 🏢 {result.get('name', company_name)}")
                        st.caption("📌 Source: Mistral AI")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**📅 Founded:** {result.get('founded', 'Not found')}")
                            st.markdown(f"**👤 Founder:** {result.get('founder', 'Not found')}")
                            st.markdown(f"**👔 CEO:** {result.get('ceo', 'Not found')}")
                            st.markdown(f"**📧 Email:** {result.get('email', 'Not found')}")
                        with col2:
                            st.markdown(f"**📍 Headquarters:** {result.get('headquarters', 'Not found')}")
                            st.markdown(f"**🏭 Industry:** {result.get('industry', 'Not found')}")
                            st.markdown(f"**👥 Employees:** {result.get('employees', 'Not found')}")
                            st.markdown(f"**📞 Phone:** {result.get('phone', 'Not found')}")
                        
                        if result.get('website') and result['website'] != 'Not found':
                            st.markdown(f"**🌐 Website:** [{result['website']}](https://{result['website']})")
                        if result.get('address') and result['address'] != 'Not found':
                            st.markdown(f"**📍 Address:** {result['address']}")
                        if result.get('description') and result['description'] != 'Not found':
                            st.markdown("---")
                            st.markdown("### 📝 About")
                            st.write(result['description'])
                        
                        st.markdown("---")
                        st.caption(f"🕐 Extracted: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
                        with st.expander("📋 Raw Data"):
                            st.json(result)
                    else:
                        st.error("Could not parse AI response")
                        st.code(raw[:500])
                else:
                    st.error(f"AI Error: {response.status_code}")
                    st.code(response.text[:300])
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ── SAMPLES ────────────────────────────────────────────────────
with st.expander("💡 Sample Companies to Try"):
    st.markdown("""
    - `Google`
    - `Microsoft`
    - `Amazon`
    - `Infosys`
    - `TCS`
    - `Narola Infotech`
    - `Vasundhara Infotech LLP`
    """)

st.markdown("""
<div style="text-align:center;color:#999;padding:2rem 0 0.5rem 0;font-size:0.8rem;border-top:1px solid #eee;margin-top:2rem;">
    CompanyIQ · Powered by Mistral AI
</div>
""", unsafe_allow_html=True)