import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from duckduckgo_search import DDGS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# ── MISTRAL API KEY ────────────────────────────────────────────
MISTRAL_KEY = "tXPmUYPeEqwD48MrvREFmn3GmvB7KqRk"

# ── PAGE CONFIG ────────────────────────────────────────────────
st.set_page_config(
    page_title="ContactIQ — Profile Extractor",
    page_icon="🔍",
    layout="centered"
)

st.markdown("""
<div style="text-align: center; padding: 1.5rem 0;">
    <h1 style="font-size: 2.8rem; margin: 0; background: linear-gradient(135deg, #0EA5E9, #6366F1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🔍 ContactIQ
    </h1>
    <p style="color: #666; font-size: 1.1rem;">Extract public data from Social Media profiles</p>
</div>
""", unsafe_allow_html=True)

# ── MODE TOGGLE ─────────────────────────────────────────────────
mode = st.radio(
    "Select Mode:",
    ["🐙 GitHub Profile", "🏢 Company Profile", "📘 Facebook Profile", "📸 Instagram Profile", "💼 LinkedIn Profile"],
    horizontal=True,
    index=0
)

st.markdown("---")

# ── INPUT ──────────────────────────────────────────────────────
if mode == "🐙 GitHub Profile":
    username = st.text_input("GitHub Username", placeholder="octocat", label_visibility="collapsed")
elif mode == "🏢 Company Profile":
    company_name = st.text_input("Company Name", placeholder="Google", label_visibility="collapsed")
elif mode == "📘 Facebook Profile":
    fb_username = st.text_input("Facebook Username/Page URL", placeholder="zuck or facebook.com/zuck", label_visibility="collapsed")
elif mode == "📸 Instagram Profile":
    ig_username = st.text_input("Instagram Username", placeholder="instagram", label_visibility="collapsed")
elif mode == "💼 LinkedIn Profile":
    li_url = st.text_input("LinkedIn Profile URL", placeholder="linkedin.com/in/username", label_visibility="collapsed")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    extract_btn = st.button("🔍 Extract Data", use_container_width=True)

# ════════════════════════════════════════════════════════════════
# ── SELENIUM SETUP ─────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_selenium_driver():
    """Setup headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Chrome Driver Error: {str(e)}")
        return None

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
# ── COMPANY EXTRACTION (DuckDuckGo + Mistral AI) ─────────────
# ════════════════════════════════════════════════════════════════

def search_company_duckduckgo(company_name):
    """Search company using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{company_name} company contact phone email address", max_results=5))

            info = {
                'phone': None,
                'email': None,
                'website': None,
                'address': None,
                'description': None,
                'body': ''
            }

            for result in results:
                body = result.get('body', '')
                info['body'] += body + ' '

                # Phone
                phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', body)
                if phone_match and not info['phone']:
                    info['phone'] = phone_match.group(1).strip()

                # Email
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body)
                if email_match and not info['email']:
                    info['email'] = email_match.group(0).strip()

                # Website
                website_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', body)
                if website_match and not info['website']:
                    info['website'] = website_match.group(1).strip()

                # Address
                address_match = re.search(r'\d{1,5}\s[\w\s]{2,40}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd)[\w\s,\.]{0,60}', body, re.IGNORECASE)
                if address_match and not info['address']:
                    info['address'] = address_match.group(0).strip()

                if not info['description']:
                    info['description'] = result.get('title', '') + ' ' + body[:200]

            return info
    except Exception as e:
        return None

def call_mistral_company(company_name):
    """Call Mistral AI for company details"""
    try:
        prompt = f"""
        Provide information about this company: {company_name}

        Return ONLY JSON:
        {{
            "founded": "year or Not found",
            "founder": "name or Not found",
            "ceo": "name or Not found",
            "headquarters": "location or Not found",
            "industry": "sector or Not found",
            "employees": "number or Not found"
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
        'description': 'Not found'
    }

    try:
        # Step 1: DuckDuckGo Search
        ddg_data = search_company_duckduckgo(company_name)
        if ddg_data:
            for key in ['phone', 'email', 'website', 'address', 'description']:
                if ddg_data.get(key):
                    result[key] = ddg_data[key]
            if ddg_data.get('body'):
                result['description'] = ddg_data['body'][:300]

        # Step 2: Mistral AI
        mistral_data = call_mistral_company(company_name)
        if mistral_data:
            for key in ['founded', 'founder', 'ceo', 'headquarters', 'industry', 'employees']:
                if mistral_data.get(key) and mistral_data[key] != 'Not found':
                    result[key] = mistral_data[key]

        result['status'] = 'success'
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)

    return result

# ════════════════════════════════════════════════════════════════
# ── FACEBOOK EXTRACTION (Selenium) ─────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_facebook_profile(username):
    """Extract Facebook public page data using Selenium"""
    driver = None
    try:
        # Clean username
        username = username.strip().replace('@', '').split('/')[-1]
        if 'facebook.com' in username:
            username = username.split('facebook.com/')[-1].split('?')[0].split('/')[0]

        url = f"https://www.facebook.com/{username}"

        driver = get_selenium_driver()
        if not driver:
            return {'status': 'error', 'message': 'Failed to initialize Chrome driver'}

        driver.get(url)
        time.sleep(5)  # Wait for page load

        result = {
            'status': 'success',
            'username': username,
            'profile_url': url,
            'name': 'Not found',
            'category': 'Not found',
            'followers': 'Not found',
            'likes': 'Not found',
            'description': 'Not found',
            'website': 'Not found',
            'email': 'Not found',
            'phone': 'Not found',
            'address': 'Not found',
            'page_type': 'Not found'
        }

        # Try to get page title/name
        try:
            title = driver.title
            if title and title != 'Facebook':
                result['name'] = title.replace(' | Facebook', '').replace(' - Facebook', '').strip()
        except:
            pass

        # Try to find name from h1
        try:
            name_elem = driver.find_element(By.TAG_NAME, 'h1')
            if name_elem:
                result['name'] = name_elem.text.strip()
        except:
            pass

        # Get page source for regex parsing
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract meta description
        try:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                result['description'] = meta_desc.get('content', 'Not found')
        except:
            pass

        # Extract followers/likes from page source
        followers_match = re.search(r'(\d+[.,]?\d*\s*[KMB]?)\s*followers', page_source, re.IGNORECASE)
        if followers_match:
            result['followers'] = followers_match.group(1).strip()

        likes_match = re.search(r'(\d+[.,]?\d*\s*[KMB]?)\s*likes', page_source, re.IGNORECASE)
        if likes_match:
            result['likes'] = likes_match.group(1).strip()

        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source)
        if email_match:
            result['email'] = email_match.group(0)

        # Extract phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', page_source)
        if phone_match:
            result['phone'] = phone_match.group(1).strip()

        # Extract website
        website_match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_source)
        if website_match and 'facebook.com' not in website_match.group(0):
            result['website'] = website_match.group(1)

        # Check if page exists
        if "This page isn't available" in page_source or "Content Not Found" in page_source:
            return {'status': 'error', 'message': f"Facebook page '{username}' not found or not accessible"}

        return result

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    finally:
        if driver:
            driver.quit()

# ════════════════════════════════════════════════════════════════
# ── INSTAGRAM EXTRACTION (Selenium) ────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_instagram_profile(username):
    """Extract Instagram public profile data using Selenium"""
    driver = None
    try:
        # Clean username
        username = username.strip().replace('@', '').split('/')[-1]

        url = f"https://www.instagram.com/{username}/"

        driver = get_selenium_driver()
        if not driver:
            return {'status': 'error', 'message': 'Failed to initialize Chrome driver'}

        driver.get(url)
        time.sleep(6)  # Wait for page load

        result = {
            'status': 'success',
            'username': username,
            'profile_url': url,
            'name': 'Not found',
            'bio': 'Not found',
            'followers': 'Not found',
            'following': 'Not found',
            'posts': 'Not found',
            'is_verified': False,
            'is_private': False,
            'profile_pic': 'Not found',
            'website': 'Not found',
            'category': 'Not found'
        }

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Check if private
        if "This Account is Private" in page_source or "is_private" in page_source:
            result['is_private'] = True
            result['bio'] = "This account is private. Limited data available."

        # Check if account exists
        if "Page Not Found" in page_source or "Sorry, this page" in page_source:
            return {'status': 'error', 'message': f"Instagram user '@{username}' not found"}

        # Extract from meta tags
        try:
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title:
                title_content = meta_title.get('content', '')
                result['name'] = title_content.split('(@')[0].strip() if '(@' in title_content else title_content.split('•')[0].strip()
        except:
            pass

        try:
            meta_desc = soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                desc = meta_desc.get('content', '')
                # Parse Instagram description format: "X Followers, Y Following, Z Posts - See..."
                followers_match = re.search(r'(\d+[.,]?\d*\s*[KMB]?)\s*Followers', desc, re.IGNORECASE)
                if followers_match:
                    result['followers'] = followers_match.group(1).strip()

                following_match = re.search(r'(\d+[.,]?\d*\s*[KMB]?)\s*Following', desc, re.IGNORECASE)
                if following_match:
                    result['following'] = following_match.group(1).strip()

                posts_match = re.search(r'(\d+[.,]?\d*\s*[KMB]?)\s*Posts', desc, re.IGNORECASE)
                if posts_match:
                    result['posts'] = posts_match.group(1).strip()
        except:
            pass

        # Extract profile picture
        try:
            meta_image = soup.find('meta', {'property': 'og:image'})
            if meta_image:
                result['profile_pic'] = meta_image.get('content', 'Not found')
        except:
            pass

        # Extract from shared data / JSON
        try:
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if 'name' in data and result['name'] == 'Not found':
                            result['name'] = data['name']
                        if 'description' in data:
                            result['bio'] = data['description']
        except:
            pass

        # Try to find bio from page structure
        try:
            # Look for bio in specific sections
            bio_elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_aa_c')]//span")
            if bio_elements:
                result['bio'] = bio_elements[0].text.strip()
        except:
            pass

        # Extract website from page source
        website_match = re.search(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_source)
        if website_match and 'instagram.com' not in website_match.group(0) and 'fbcdn.net' not in website_match.group(0):
            result['website'] = website_match.group(1)

        return result

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    finally:
        if driver:
            driver.quit()

# ════════════════════════════════════════════════════════════════
# ── LINKEDIN EXTRACTION (Selenium) ─────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_linkedin_profile(url_or_username):
    """Extract LinkedIn public profile data using Selenium"""
    driver = None
    try:
        # Handle URL or username input
        if 'linkedin.com' in url_or_username:
            url = url_or_username.strip()
            if not url.startswith('http'):
                url = 'https://' + url
        else:
            url = f"https://www.linkedin.com/in/{url_or_username.strip()}/"

        driver = get_selenium_driver()
        if not driver:
            return {'status': 'error', 'message': 'Failed to initialize Chrome driver'}

        driver.get(url)
        time.sleep(7)  # Wait for page load (LinkedIn is slow)

        result = {
            'status': 'success',
            'profile_url': url,
            'name': 'Not found',
            'headline': 'Not found',
            'location': 'Not found',
            'company': 'Not found',
            'education': 'Not found',
            'connections': 'Not found',
            'about': 'Not found',
            'experience': [],
            'skills': [],
            'profile_pic': 'Not found'
        }

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Check if profile exists
        if "This page doesn't exist" in page_source or "couldn't find" in page_source.lower():
            return {'status': 'error', 'message': "LinkedIn profile not found"}

        # Check if login required
        if "Sign in" in page_source and "Join now" in page_source:
            # Try to extract whatever public data is available
            pass

        # Extract from meta tags
        try:
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title:
                title = meta_title.get('content', '')
                result['name'] = title.split(' | ')[0].strip() if ' | ' in title else title.split(' - ')[0].strip()
        except:
            pass

        try:
            meta_desc = soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                result['headline'] = meta_desc.get('content', 'Not found')
        except:
            pass

        try:
            meta_image = soup.find('meta', {'property': 'og:image'})
            if meta_image:
                result['profile_pic'] = meta_image.get('content', 'Not found')
        except:
            pass

        # Extract from JSON-LD
        try:
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if 'name' in data and result['name'] == 'Not found':
                            result['name'] = data['name']
                        if 'jobTitle' in data:
                            result['headline'] = data['jobTitle']
                        if 'worksFor' in data:
                            if isinstance(data['worksFor'], dict):
                                result['company'] = data['worksFor'].get('name', 'Not found')
                            else:
                                result['company'] = str(data['worksFor'])
                        if 'address' in data and isinstance(data['address'], dict):
                            result['location'] = data['address'].get('addressLocality', 'Not found')
                        if 'description' in data:
                            result['about'] = data['description']
                        if 'image' in data:
                            result['profile_pic'] = data['image']
                        if 'alumniOf' in data:
                            if isinstance(data['alumniOf'], list):
                                result['education'] = ', '.join([edu.get('name', '') for edu in data['alumniOf'] if isinstance(edu, dict)])
                            elif isinstance(data['alumniOf'], dict):
                                result['education'] = data['alumniOf'].get('name', 'Not found')
        except:
            pass

        # Extract connections count
        connections_match = re.search(r'(\d+)\+?\s*connections?', page_source, re.IGNORECASE)
        if connections_match:
            result['connections'] = connections_match.group(1) + '+'

        # Extract location from text
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+)\s*•',
            r'Located\s+in\s+([A-Za-z\s,]+)',
            r'([A-Za-z\s]+,\s*[A-Z]{2})\s*\|'
        ]
        for pattern in location_patterns:
            loc_match = re.search(pattern, page_source)
            if loc_match:
                result['location'] = loc_match.group(1).strip()
                break

        return result

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    finally:
        if driver:
            driver.quit()

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

    elif mode == "🏢 Company Profile":
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

                st.markdown("---")
                st.caption(f"🕐 Extracted: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
                with st.expander("📋 Raw Data"):
                    st.json(result)

    elif mode == "📘 Facebook Profile":
        if not fb_username:
            st.warning("Please enter a Facebook username or page URL.")
        else:
            with st.spinner(f"🔍 Fetching Facebook profile '{fb_username}'..."):
                result = get_facebook_profile(fb_username)

            if result['status'] == 'error':
                st.error(f"❌ {result['message']}")
                st.info("💡 Tip: Facebook requires login for most profiles. Try public pages like 'Meta' or 'Google'.")
            else:
                st.success(f"✅ Facebook profile extracted!")
                st.markdown("---")

                st.markdown(f"### 📘 {result['name']}")
                st.caption(f"facebook.com/{result['username']}")

                if result['description'] != 'Not found':
                    st.markdown(f"📝 {result['description'][:200]}...")

                st.markdown("---")
                st.markdown("### 📬 Page Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**👥 Followers:** {result['followers']}")
                    st.markdown(f"**👍 Likes:** {result['likes']}")
                    st.markdown(f"**📧 Email:** {result['email']}")
                with col2:
                    st.markdown(f"**📞 Phone:** {result['phone']}")
                    st.markdown(f"**🌐 Website:** {result['website']}")
                    st.markdown(f"**📍 Address:** {result['address']}")

                st.markdown(f"**🔗 Profile:** [View on Facebook]({result['profile_url']})")

                with st.expander("📋 Raw Data"):
                    st.json(result)

    elif mode == "📸 Instagram Profile":
        if not ig_username:
            st.warning("Please enter an Instagram username.")
        else:
            with st.spinner(f"🔍 Fetching Instagram profile '@{ig_username}'..."):
                result = get_instagram_profile(ig_username)

            if result['status'] == 'error':
                st.error(f"❌ {result['message']}")
            else:
                st.success(f"✅ Instagram profile extracted!")
                st.markdown("---")

                col1, col2 = st.columns([1, 3])
                with col1:
                    if result['profile_pic'] != 'Not found':
                        st.image(result['profile_pic'], width=100)
                    else:
                        st.markdown("📸 No image")
                with col2:
                    st.markdown(f"### 📸 {result['name']}")
                    st.caption(f"@{result['username']}")
                    if result['is_verified']:
                        st.markdown("✅ Verified")
                    if result['is_private']:
                        st.markdown("🔒 Private Account")

                if result['bio'] != 'Not found':
                    st.markdown(f"📝 {result['bio']}")

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.metric("📸 Posts", result['posts'])
                col2.metric("👥 Followers", result['followers'])
                col3.metric("👤 Following", result['following'])

                if result['website'] != 'Not found':
                    st.markdown(f"**🌐 Website:** [{result['website']}](https://{result['website']})")

                st.markdown(f"**🔗 Profile:** [View on Instagram]({result['profile_url']})")

                with st.expander("📋 Raw Data"):
                    st.json(result)

    elif mode == "💼 LinkedIn Profile":
        if not li_url:
            st.warning("Please enter a LinkedIn profile URL or username.")
        else:
            with st.spinner(f"🔍 Fetching LinkedIn profile..."):
                result = get_linkedin_profile(li_url)

            if result['status'] == 'error':
                st.error(f"❌ {result['message']}")
                st.info("💡 Tip: LinkedIn requires login for most profiles. Public profiles show limited data.")
            else:
                st.success(f"✅ LinkedIn profile extracted!")
                st.markdown("---")

                col1, col2 = st.columns([1, 3])
                with col1:
                    if result['profile_pic'] != 'Not found':
                        st.image(result['profile_pic'], width=100)
                    else:
                        st.markdown("💼")
                with col2:
                    st.markdown(f"### 💼 {result['name']}")
                    st.markdown(f"🎯 {result['headline']}")

                st.markdown("---")
                st.markdown("### 📬 Professional Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🏢 Company:** {result['company']}")
                    st.markdown(f"**📍 Location:** {result['location']}")
                    st.markdown(f"**🎓 Education:** {result['education']}")
                with col2:
                    st.markdown(f"**👥 Connections:** {result['connections']}")
                    st.markdown(f"**🔗 Profile:** [View on LinkedIn]({result['profile_url']})")

                if result['about'] != 'Not found':
                    st.markdown("---")
                    st.markdown("### 📝 About")
                    st.markdown(result['about'])

                with st.expander("📋 Raw Data"):
                    st.json(result)

# ── SAMPLES ────────────────────────────────────────────────────
with st.expander("💡 Samples"):
    if mode == "🐙 GitHub Profile":
        st.markdown("""
        ### 🐙 GitHub Developers
        - `octocat` (GitHub Mascot)
        - `torvalds` (Linus Torvalds - Linux Creator)
        - `gvanrossum` (Guido van Rossum - Python Creator)
        - `defunkt` (GitHub Co-founder)
        - `karpathy` (Andrej Karpathy - AI Researcher)
        """)
    elif mode == "🏢 Company Profile":
        st.markdown("""
        - `Google`
        - `Microsoft`
        - `Infosys`
        - `TCS`
        - `Amazon`
        - `Apple`
        """)
    elif mode == "📘 Facebook Profile":
        st.markdown("""
        ### 📘 Facebook Pages (Public)
        - `Meta` (Meta Platforms)
        - `Google` 
        - `Microsoft`
        - `Tesla` 
        - `Amazon`
        - `zuck` (Mark Zuckerberg - if public)
        """)
    elif mode == "📸 Instagram Profile":
        st.markdown("""
        ### 📸 Instagram Accounts (Public)
        - `instagram` (Official)
        - `natgeo` (National Geographic)
        - `nasa` (NASA)
        - `google` 
        - `microsoft`
        - `teslamotors`
        """)
    elif mode == "💼 LinkedIn Profile":
        st.markdown("""
        ### 💼 LinkedIn Profiles (Public)
        - `satyanadella` (Satya Nadella)
        - `sundarpichai` (Sundar Pichai)
        - `timcook` (Tim Cook)
        - `elonmusk` (Elon Musk)
        - `billgates` (Bill Gates)
        💡 **Note:** Enter full URL like: `linkedin.com/in/username`
        """)

# ── FOOTER ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem 0 0.5rem 0; font-size: 0.8rem; border-top: 1px solid #eee; margin-top: 2rem;">
    ContactIQ · Profile Extractor<br>
    <span style="font-size: 0.7rem;">GitHub API · DuckDuckGo · Mistral AI · Selenium WebDriver</span>
</div>
""", unsafe_allow_html=True)
