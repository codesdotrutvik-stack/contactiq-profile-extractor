# app.py - YouTube Fix with Selenium for dynamic content

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urlparse, urljoin
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ============== LIGHT MODE CONFIG ==============
st.set_page_config(
    page_title="Multi-Platform Profile Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa !important; color: #212529 !important; }
    .main-header { font-size: 2.5rem; font-weight: bold; color: #0d6efd; text-align: center; }
    .sub-header { font-size: 1.1rem; color: #6c757d; text-align: center; margin-bottom: 2rem; }
    .warning-box { background-color: #fff3cd; color: #664d03; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107; }
    .info-box { background-color: #cff4fc; color: #055160; padding: 15px; border-radius: 10px; border-left: 5px solid #0dcaf0; }
    .success-box { background-color: #d1e7dd; color: #0f5132; padding: 15px; border-radius: 10px; border-left: 5px solid #198754; }
    .error-box { background-color: #f8d7da; color: #842029; padding: 15px; border-radius: 10px; border-left: 5px solid #dc3545; }
    .result-box { background-color: #ffffff; color: #212529; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .contact-found { background-color: #d1e7dd; color: #0f5132; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #198754; }
    .badge { padding: 10px 15px; border-radius: 10px; text-align: center; font-weight: bold; color: white; }
    .metric-box { background: white; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #e9ecef; }
    .address-box { background: #e7f3ff; color: #004085; padding: 15px; border-radius: 10px; border-left: 5px solid #0d6efd; margin: 10px 0; }
    .followers-box { background: #fff3e0; color: #e65100; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; margin: 10px 0; }
    .linkedin-info { background: #e3f2fd; color: #1565c0; padding: 20px; border-radius: 12px; border-left: 5px solid #2196f3; margin: 15px 0; }
    .youtube-stats { background: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; border-left: 5px solid #f44336; margin: 10px 0; }
    .footer { text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; }
    </style>
""", unsafe_allow_html=True)


# ============== SELENIUM HELPER ==============

class SeleniumScraper:
    def __init__(self):
        self.driver = None
    
    def init_driver(self):
        if not SELENIUM_AVAILABLE:
            return None
            
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            self.driver = driver
            return driver
        except Exception as e:
            st.error(f"❌ ChromeDriver failed: {str(e)}")
            return None
    
    def get_page(self, url, wait_time=10):
        if not self.driver:
            self.init_driver()
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            time.sleep(5)
            
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except TimeoutException:
            try:
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            except:
                return None
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            return None
    
    def get_youtube_data(self, url):
        """Special method for YouTube with dynamic content waiting."""
        if not self.driver:
            self.init_driver()
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            # Wait longer for YouTube dynamic content
            time.sleep(8)
            
            # Try to find subscriber count element
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#subscriber-count, yt-formatted-string#subscriber-count, .yt-formatted-string"))
                )
            except:
                pass
            
            time.sleep(3)
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            st.error(f"❌ YouTube loading error: {str(e)}")
            try:
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            except:
                return None
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


# ============== DISPLAY FUNCTIONS ==============

def display_youtube(data):
    """Display YouTube data with better formatting."""
    st.subheader("📺 YouTube Channel")
    
    # Stats in big boxes
    cols = st.columns(3)
    
    subscribers = data.get('subscribers', 'N/A')
    videos = data.get('video_count', 'N/A')
    views = data.get('view_count', 'N/A')
    
    # Format numbers nicely
    if subscribers and subscribers != 'N/A':
        subscribers_display = subscribers
    else:
        subscribers_display = 'N/A'
    
    if videos and videos != 'N/A':
        videos_display = videos
    else:
        videos_display = 'N/A'
    
    metrics = [
        (cols[0], "👥 Subscribers", subscribers_display, "#ff0000"),
        (cols[1], "🎬 Videos", videos_display, "#ff6d00"),
        (cols[2], "👀 Views", views if views != 'N/A' else 'N/A', "#00c853")
    ]
    
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
                <div class="metric-box" style="border-color: {color};">
                    <p style="font-size: 0.9rem; color: #666;">{label}</p>
                    <h2 style="color: {color}; margin: 0;">{value}</h2>
                </div>
            """, unsafe_allow_html=True)
    
    # Channel info
    if data.get('channel_name'):
        st.markdown(f"**Channel:** {data['channel_name']}")
    if data.get('handle'):
        st.markdown(f"**Handle:** @{data['handle']}")
    if data.get('joined_date'):
        st.markdown(f"**📅 Joined:** {data['joined_date']}")
    if data.get('location'):
        st.markdown(f"**📍 Location:** {data['location']}")
    
    # Description with links
    if data.get('description'):
        with st.expander("📝 Description"):
            st.write(data['description'])
            if data.get('links') and len(data['links']) > 0:
                st.markdown("**🔗 Links:**")
                for link in data['links']:
                    st.markdown(f"• [{link}]({link})")
    
    # Banner image
    if data.get('banner_image'):
        st.image(data['banner_image'], use_column_width=True)
    
    # Profile image
    if data.get('profile_image'):
        st.image(data['profile_image'], width=200)


def display_linkedin(data):
    """Display LinkedIn data with API suggestion."""
    st.subheader("💼 LinkedIn Profile")
    
    if data.get('is_blocked') or data.get('name') in ['Sign Up', 'Join now', 'LinkedIn', None]:
        st.markdown("""
            <div class="linkedin-info">
                <h4>🔒 LinkedIn Access Restricted</h4>
                <p>LinkedIn has detected automated access and shown a login/signup page.</p>
                <p><b>Why this happens:</b></p>
                <ul>
                    <li>LinkedIn has <b>aggressive anti-scraping</b> measures</li>
                    <li>Requires <b>authenticated session</b> (cookies/login)</li>
                    <li>Even Selenium gets detected after a few requests</li>
                </ul>
                <p><b>Real Solutions:</b></p>
                <ol>
                    <li><b>LinkedIn API (Official):</b> <a href="https://developer.linkedin.com/" target="_blank">developer.linkedin.com</a></li>
                    <li><b>LinkedIn Sales Navigator:</b> Paid tool with export features</li>
                    <li><b>PhantomBuster:</b> Cloud-based scraping service</li>
                    <li><b>Manual Export:</b> LinkedIn allows PDF profile export</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 What we attempted to extract"):
            st.write(f"**URL:** {data.get('profile_url', 'N/A')}")
            st.write(f"**Username:** {data.get('username', 'N/A')}")
            st.write(f"**Page Title:** {data.get('page_title', 'N/A')}")
            if data.get('page_text_sample'):
                st.write(f"**Page Text Sample:** {data['page_text_sample'][:200]}...")
        
        # Manual entry
        st.markdown("---")
        st.markdown("### 📝 Manual Data Entry (If you have access)")
        
        with st.expander("➕ Add LinkedIn Data Manually"):
            manual_name = st.text_input("Name", value=data.get('name') if data.get('name') not in ['Sign Up', 'Join now', None] else "")
            manual_headline = st.text_input("Headline/Title")
            manual_location = st.text_input("Location")
            manual_email = st.text_input("Email (if visible on profile)")
            manual_phone = st.text_input("Phone (if visible on profile)")
            
            if st.button("💾 Save Manual Data"):
                st.success("✅ Data saved! (Note: This is for display only, not stored permanently)")
                st.json({
                    "name": manual_name,
                    "headline": manual_headline,
                    "location": manual_location,
                    "email": manual_email,
                    "phone": manual_phone,
                    "source": "manual_entry"
                })
    
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if data.get('profile_image') and 'linkedin.com' not in data['profile_image']:
                st.image(data['profile_image'], width=150)
            else:
                st.markdown("""<div style="width:150px;height:150px;background:#ddd;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:3rem;">👤</div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**Name:** {data.get('name', 'N/A')}")
            st.markdown(f"**Headline:** {data.get('headline', 'N/A')}")
            st.markdown(f"**Location:** {data.get('location', 'N/A')}")
            if data.get('connections'):
                st.markdown(f"**Connections:** {data['connections']}")
            if data.get('followers'):
                st.markdown(f"**Followers:** {data['followers']}")


def display_facebook(data):
    """Display Facebook data."""
    st.subheader("📘 Facebook Page")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Page:** {data.get('page_name', 'N/A')}")
        st.markdown(f"**Category:** {data.get('category', 'N/A')}")
        
        followers = data.get('followers', 'N/A')
        st.markdown(f"""
            <div class="followers-box">
                <h4>👥 Followers</h4>
                <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">{followers}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if data.get('following'):
            st.markdown(f"**👤 Following:** {data['following']}")
    
    with col2:
        if data.get('address') and data['address'] != 'N/A':
            st.markdown("""
                <div class="address-box">
                    <b>📍 Address:</b><br>
                    {}
                </div>
            """.format(data['address'].replace(', ', '<br>')), unsafe_allow_html=True)
        
        if data.get('phone'):
            st.markdown(f"**📞 Phone:** {data['phone']}")
        if data.get('email'):
            st.markdown(f"**✉️ Email:** {data['email']}")
        if data.get('website'):
            st.markdown(f"**🌐 Website:** [{data['website']}]({data['website']})")
        if data.get('hours'):
            st.markdown(f"**🕐 Hours:** {data['hours']}")
    
    if data.get('description'):
        with st.expander("📝 Description"):
            st.write(data['description'])


def display_instagram(data):
    """Display Instagram data."""
    st.subheader("📸 Instagram Profile")
    
    cols = st.columns(4)
    metrics = [
        (cols[0], "📷 Posts", data.get('posts_count', 'N/A')),
        (cols[1], "👥 Followers", data.get('followers', 'N/A')),
        (cols[2], "👤 Following", data.get('following', 'N/A')),
        (cols[3], "🏢 Business", "Yes" if data.get('is_business') else "No")
    ]
    
    for col, label, value in metrics:
        with col:
            st.markdown(f"""
                <div class="metric-box">
                    <p style="font-size: 0.9rem; color: #666;">{label}</p>
                    <h3>{value}</h3>
                </div>
            """, unsafe_allow_html=True)
    
    if data.get('full_name'):
        st.markdown(f"**Full Name:** {data['full_name']}")
    if data.get('bio'):
        st.markdown(f"**Bio:** {data['bio']}")
    if data.get('external_url'):
        st.markdown(f"**🔗 Link:** [{data['external_url']}]({data['external_url']})")
    if data.get('profile_image'):
        st.image(data['profile_image'], width=200)


def display_company(data):
    """Display company website data."""
    st.subheader("🏢 Company Website")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Title:** {data.get('title', 'N/A')}")
        if data.get('description'):
            st.markdown(f"**Description:** {data['description'][:200]}...")
    with col2:
        if data.get('contact_page'):
            st.markdown(f"**📞 Contact:** [Visit]({data['contact_page']})")
        if data.get('about_page'):
            st.markdown(f"**ℹ️ About:** [Visit]({data['about_page']})")
    
    if data.get('emails'):
        with st.expander(f"✉️ Emails ({len(data['emails'])})"):
            for email in data['emails']:
                st.code(email)
    
    if data.get('phones'):
        with st.expander(f"📞 Phones ({len(data['phones'])})"):
            for phone in data['phones']:
                st.code(phone)
    
    if data.get('addresses'):
        with st.expander(f"📍 Addresses ({len(data['addresses'])})"):
            for addr in data['addresses']:
                st.write(f"• {addr}")


# ============== ANALYZER CLASS ==============

class MultiPlatformAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.selenium = SeleniumScraper()
        self.results = {
            'profile_url': None,
            'platform': None,
            'username': None,
            'profile_data': {},
            'contact_info': {},
            'analysis_timestamp': datetime.now().isoformat(),
            'data_source': 'public_only',
            'compliance_note': 'Only publicly available information analyzed'
        }
    
    def identify_platform(self, url):
        if not url:
            return 'unknown'
        domain = urlparse(url).netloc.lower()
        if 'linkedin.com' in domain:
            return 'linkedin'
        elif 'instagram.com' in domain or 'instagr.am' in domain:
            return 'instagram'
        elif 'facebook.com' in domain or 'fb.com' in domain:
            return 'facebook'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        else:
            return 'company_website'
    
    def extract_username(self, url, platform):
        if not url:
            return None
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if platform == 'linkedin':
            parts = path.split('/')
            return parts[1] if len(parts) >= 2 and parts[0] in ['in', 'company'] else path
        elif platform == 'youtube':
            if '/channel/' in path:
                return path.split('/channel/')[1].split('/')[0]
            elif path.startswith('@'):
                return path[1:]
            elif path.startswith('c/'):
                return path[2:]
            return path
        elif platform in ['instagram', 'twitter', 'facebook']:
            return path.split('/')[0] if path else None
        else:
            return parsed.netloc.replace('www.', '')
    
    def extract_contact_patterns(self, text):
        if not text:
            return {'emails': [], 'phones': [], 'websites': []}
        
        contacts = {'emails': [], 'phones': [], 'websites': []}
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        contacts['emails'] = list(set(re.findall(email_pattern, text)))
        
        phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        contacts['phones'] = list(set(re.findall(phone_pattern, text)))
        
        web_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        contacts['websites'] = list(set(re.findall(web_pattern, text)))
        
        return contacts
    
    def analyze_youtube_selenium(self, url, username):
        """YouTube with Selenium for dynamic content."""
        results = {
            'platform': 'youtube',
            'username': username,
            'profile_url': url,
            'channel_name': None,
            'handle': username,
            'subscribers': None,
            'video_count': None,
            'view_count': None,
            'description': None,
            'joined_date': None,
            'location': None,
            'links': [],
            'profile_image': None,
            'banner_image': None,
            'public_email': None,
            'error': None
        }
        
        try:
            # Use special YouTube method with longer wait
            soup = self.selenium.get_youtube_data(url)
            
            if not soup:
                results['error'] = 'Selenium failed to load YouTube page'
                return results
            
            # Method 1: Try to find ytInitialData (YouTube's initial data)
            scripts = soup.find_all('script')
            yt_data = None
            
            for script in scripts:
                if script.string and 'ytInitialData' in script.string:
                    try:
                        # Extract JSON from script
                        json_match = re.search(r'ytInitialData\s*=\s*({.+?});', script.string, re.DOTALL)
                        if json_match:
                            yt_data = json.loads(json_match.group(1))
                            break
                    except:
                        pass
            
            # Method 2: Extract from meta tags
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                results['channel_name'] = meta_title.get('content', '').replace(' - YouTube', '').strip()
            
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                results['description'] = meta_desc.get('content')
            
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                results['banner_image'] = meta_image.get('content')
            
            # Method 3: Parse from visible text (more reliable for stats)
            visible_text = soup.get_text(separator=' ', strip=True)
            
            # YouTube subscriber patterns (from rendered page)
            subscriber_patterns = [
                r'([\d,.]+[KMBkmb]?)\s*subscribers?',  # 15M subscribers, 6.1K subscribers
                r'subscribers?\s*[:·]\s*([\d,.]+[KMBkmb]?)',  # subscribers: 15M
                r'([\d,]+(?:\.\d+)?)\s*subscribers?',  # 15,000,000 subscribers
            ]
            
            for pattern in subscriber_patterns:
                match = re.search(pattern, visible_text, re.IGNORECASE)
                if match:
                    results['subscribers'] = match.group(1).strip()
                    break
            
            # Video count patterns
            video_patterns = [
                r'([\d,.]+[KMBkmb]?)\s*videos?',  # 6.1K videos
                r'videos?\s*[:·]\s*([\d,.]+[KMBkmb]?)',
                r'([\d,]+(?:\.\d+)?)\s*videos?',
            ]
            
            for pattern in video_patterns:
                match = re.search(pattern, visible_text, re.IGNORECASE)
                if match:
                    results['video_count'] = match.group(1).strip()
                    break
            
            # View count (total channel views - harder to find)
            # Usually in about page, not main page
            view_patterns = [
                r'([\d,.]+[KMBkmb]?)\s*views?',  # May appear in about section
                r'total\s*views?\s*[:·]\s*([\d,.]+[KMBkmb]?)',
            ]
            
            for pattern in view_patterns:
                match = re.search(pattern, visible_text, re.IGNORECASE)
                if match:
                    results['view_count'] = match.group(1).strip()
                    break
            
            # Try to extract from ytInitialData if available
            if yt_data:
                try:
                    # Navigate through YouTube's complex JSON structure
                    header = yt_data.get('header', {})
                    c4_tabbed_header = header.get('c4TabbedHeaderRenderer', {})
                    
                    # Subscriber count from header
                    subscriber_text = c4_tabbed_header.get('subscriberCountText', {}).get('simpleText', '')
                    if subscriber_text:
                        sub_match = re.search(r'([\d,.]+[KMBkmb]?)', subscriber_text)
                        if sub_match:
                            results['subscribers'] = sub_match.group(1)
                    
                    # Channel name
                    title = c4_tabbed_header.get('title', '')
                    if title:
                        results['channel_name'] = title
                    
                    # Banner images
                    banners = c4_tabbed_header.get('banner', {}).get('thumbnails', [])
                    if banners:
                        results['banner_image'] = banners[-1].get('url')
                    
                    # Avatar
                    avatars = c4_tabbed_header.get('avatar', {}).get('thumbnails', [])
                    if avatars:
                        results['profile_image'] = avatars[-1].get('url')
                    
                except Exception as e:
                    pass
            
            # Extract links from description
            if results['description']:
                links = re.findall(r'https?://[^\s<>\"{}|\\^`\[\]]+', results['description'])
                results['links'] = list(set(links))
                
                # Email from description
                contacts = self.extract_contact_patterns(results['description'])
                results['public_email'] = contacts['emails'][0] if contacts['emails'] else None
            
            # If still no subscribers, try to find in specific elements
            if not results['subscribers']:
                # Look for text that contains numbers followed by K, M, B
                # and near "subscriber" word
                sub_texts = soup.find_all(text=re.compile(r'[\d,.]+[KMBkmb]?\s*subscribers?', re.IGNORECASE))
                for text in sub_texts:
                    match = re.search(r'([\d,.]+[KMBkmb]?)', str(text))
                    if match:
                        results['subscribers'] = match.group(1)
                        break
            
            # If still no video count
            if not results['video_count']:
                vid_texts = soup.find_all(text=re.compile(r'[\d,.]+[KMBkmb]?\s*videos?', re.IGNORECASE))
                for text in vid_texts:
                    match = re.search(r'([\d,.]+[KMBkmb]?)', str(text))
                    if match:
                        results['video_count'] = match.group(1)
                        break
            
            # Handle extraction
            if not results['handle'] and results['channel_name']:
                # Try to get from URL or meta
                handle_match = re.search(r'@(\w+)', url)
                if handle_match:
                    results['handle'] = handle_match.group(1)
            
        except Exception as e:
            results['error'] = f'YouTube analysis failed: {str(e)}'
        
        return results
    
    def analyze_instagram_selenium(self, url, username):
        """Instagram with Selenium."""
        results = {
            'platform': 'instagram',
            'username': username,
            'profile_url': url,
            'full_name': None,
            'bio': None,
            'followers': None,
            'following': None,
            'posts_count': None,
            'profile_image': None,
            'is_business': False,
            'external_url': None,
            'public_email': None,
            'public_phone': None,
            'error': None
        }
        
        try:
            soup = self.selenium.get_page(url, wait_time=15)
            
            if not soup:
                results['error'] = 'Selenium failed to load page'
                return results
            
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                title_content = meta_title.get('content', '')
                name_match = re.search(r'^([^(]+)\s*\(@', title_content)
                if name_match:
                    results['full_name'] = name_match.group(1).strip()
            
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                desc = meta_desc.get('content', '')
                numbers = re.findall(r'([\d,MK]+)\s*(?:Followers|Following|Posts)', desc)
                if len(numbers) >= 3:
                    results['followers'] = numbers[0]
                    results['following'] = numbers[1]
                    results['posts_count'] = numbers[2]
            
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                results['profile_image'] = meta_image.get('content')
            
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'description' in data:
                        results['bio'] = data['description']
                except:
                    pass
            
            if not results['bio'] and meta_desc:
                desc = meta_desc.get('content', '')
                bio_match = re.search(r'-\s*See.*?\.\s*(.+)', desc)
                if bio_match:
                    results['bio'] = bio_match.group(1).strip()
            
            if results['bio']:
                contacts = self.extract_contact_patterns(results['bio'])
                results['public_email'] = contacts['emails'][0] if contacts['emails'] else None
                results['public_phone'] = contacts['phones'][0] if contacts['phones'] else None
                
                business_indicators = ['business', 'shop', 'store', 'official', 'contact']
                results['is_business'] = any(word in results['bio'].lower() for word in business_indicators)
            
            link_pattern = r'linktr\.ee/\w+|bit\.ly/\w+|beacons\.ai/\w+'
            if results['bio']:
                link_match = re.search(link_pattern, results['bio'])
                if link_match:
                    results['external_url'] = f"https://{link_match.group(0)}"
            
        except Exception as e:
            results['error'] = f'Instagram analysis failed: {str(e)}'
        
        return results
    
    def analyze_facebook_selenium(self, url, username):
        """Facebook with Selenium."""
        results = {
            'platform': 'facebook',
            'username': username,
            'profile_url': url,
            'page_name': None,
            'category': None,
            'followers': None,
            'following': None,
            'description': None,
            'address': None,
            'phone': None,
            'email': None,
            'website': None,
            'hours': None,
            'public_email': None,
            'public_phone': None,
            'error': None
        }
        
        try:
            soup = self.selenium.get_page(url, wait_time=15)
            
            if not soup:
                results['error'] = 'Selenium failed to load page'
                return results
            
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                results['page_name'] = meta_title.get('content', '').split('|')[0].strip()
            
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                results['description'] = meta_desc.get('content')
            
            visible_text = soup.get_text(separator=' ', strip=True)
            
            login_contamination = [
                'Email or phone', 'Password', 'Log In', 'Forgotten account?',
                'Create New Account', 'Sign Up', 'or phone number'
            ]
            clean_text = visible_text
            for contam in login_contamination:
                clean_text = clean_text.replace(contam, ' ')
            
            contacts = self.extract_contact_patterns(clean_text)
            results['public_email'] = contacts['emails'][0] if contacts['emails'] else None
            results['public_phone'] = contacts['phones'][0] if contacts['phones'] else None
            results['email'] = results['public_email']
            results['phone'] = results['public_phone']
            
            # Followers extraction
            follower_patterns = [
                r'([\d,]+(?:\.\d+)?[KMBkmb]?)\s*followers?',
                r'followers?\s*[:·]\s*([\d,]+(?:\.\d+)?[KMBkmb]?)',
                r'([\d,]+(?:\.\d+)?)\s*people\s*follow\s*this',
                r'([\d,]+(?:\.\d+)?)\s*follower',
            ]
            
            for pattern in follower_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    results['followers'] = match.group(1).strip()
                    break
            
            # Following
            following_patterns = [
                r'([\d,]+(?:\.\d+)?[KMBkmb]?)\s*following',
                r'following\s*[:·]\s*([\d,]+(?:\.\d+)?[KMBkmb]?)',
                r'([\d,]+)\s*people\s*followed',
            ]
            
            for pattern in following_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    results['following'] = match.group(1).strip()
                    break
            
            if not results['followers'] and meta_desc:
                meta_content = meta_desc.get('content', '')
                for pattern in follower_patterns:
                    match = re.search(pattern, meta_content, re.IGNORECASE)
                    if match:
                        results['followers'] = match.group(1).strip()
                        break
            
            # Address
            address_patterns = [
                r'(Post\s+Box\s+No\s*\d+[^.]{10,150})',
                r'(\d+[^,]{5,50}(?:Road|Street|Avenue|Marg)[^,]{5,100}(?:,\s*[A-Za-z\s]+){1,4})',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*(?:Gujarat|Maharashtra|Delhi|Rajasthan)[^,]{0,50}(?:,\s*India)?)',
                r'([A-Za-z\s]+(?:Road|Street|Marg|Nagar|Colony)[^,]{5,80}(?:,\s*[A-Za-z\s]+){1,3})'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip()
                    if (len(candidate) > 15 and 
                        any(keyword in candidate.lower() for keyword in 
                            ['road', 'street', 'avenue', 'marg', 'nagar', 'colony', 'post', 'box', 'surat', 'gujarat', 'india', 'delhi', 'mumbai'])):
                        results['address'] = candidate
                        break
            
            # Website
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'l.php' in href and 'u=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'u' in parsed:
                        results['website'] = parsed['u'][0]
                        break
            
            # Hours
            hours_match = re.search(r'(?:Hours|Open)[:\s]*([^.]{10,100})', clean_text, re.IGNORECASE)
            if hours_match:
                results['hours'] = hours_match.group(1).strip()
            
        except Exception as e:
            results['error'] = f'Facebook analysis failed: {str(e)}'
        
        return results
    
    def analyze_linkedin_selenium(self, url, username):
        """LinkedIn with Selenium."""
        results = {
            'platform': 'linkedin',
            'username': username,
            'profile_url': url,
            'name': None,
            'headline': None,
            'location': None,
            'profile_image': None,
            'connections': None,
            'followers': None,
            'public_email': None,
            'is_blocked': False,
            'page_title': None,
            'page_text_sample': None,
            'error': None
        }
        
        try:
            soup = self.selenium.get_page(url, wait_time=15)
            
            if not soup:
                results['error'] = 'Selenium failed to load page'
                return results
            
            page_title = soup.find('title')
            if page_title:
                results['page_title'] = page_title.get_text().strip()
                title_text = page_title.get_text().lower()
                
                if any(blocked in title_text for blocked in ['sign up', 'join now', 'log in', 'login', 'linkedin: log in']):
                    results['is_blocked'] = True
            
            visible_text = soup.get_text(separator=' ', strip=True)
            results['page_text_sample'] = visible_text[:200]
            
            login_indicators = ['sign up', 'join now', 'email or phone', 'password', 'forgot password']
            if any(indicator in visible_text.lower() for indicator in login_indicators):
                results['is_blocked'] = True
            
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                og_title = meta_title.get('content', '')
                if og_title and not any(blocked in og_title.lower() for blocked in ['sign up', 'linkedin']):
                    results['name'] = og_title.split('|')[0].strip()
            
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                results['headline'] = meta_desc.get('content', '')
            
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                img_url = meta_image.get('content')
                if img_url and 'linkedin.com' not in img_url:
                    results['profile_image'] = img_url
            
            loc_match = re.search(r'([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?)\s*(?:Area|Region)', visible_text)
            if loc_match:
                results['location'] = loc_match.group(1).strip()
            
            conn_match = re.search(r'(\d+)\+?\s*connections?', visible_text, re.IGNORECASE)
            if conn_match:
                results['connections'] = conn_match.group(1)
            
            follower_match = re.search(r'([\d,]+(?:\.\d+)?[KMB]?)\s*followers?', visible_text, re.IGNORECASE)
            if follower_match:
                results['followers'] = follower_match.group(1)
            
            contacts = self.extract_contact_patterns(visible_text)
            results['public_email'] = contacts['emails'][0] if contacts['emails'] else None
            
            if results['is_blocked']:
                results['name'] = results['name'] or 'Sign Up'
                results['error'] = 'LinkedIn requires authentication. Use official API or manual entry.'
            
        except Exception as e:
            results['error'] = f'LinkedIn analysis failed: {str(e)}'
        
        return results
    
    def analyze_company_website(self, url, domain):
        """Company website."""
        results = {
            'platform': 'company_website',
            'domain': domain,
            'website_url': url,
            'title': None,
            'description': None,
            'emails': [],
            'phones': [],
            'addresses': [],
            'social_links': [],
            'contact_page': None,
            'about_page': None,
            'error': None
        }
        
        try:
            response = self.session.get(url, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title_tag = soup.find('title')
                if title_tag:
                    results['title'] = title_tag.get_text().strip()
                
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    results['description'] = meta_desc.get('content', '')
                
                visible_text = soup.get_text(separator=' ', strip=True)
                
                contacts = self.extract_contact_patterns(visible_text)
                results['emails'] = contacts['emails']
                results['phones'] = contacts['phones']
                
                address_patterns = [
                    r'(?:Address|Headquarters|Office|Location)[:\s]*([^.]{15,200})',
                    r'(\d+[^.]{10,100}(?:Road|Street|Avenue|City|Nagar)[^.]{10,100})'
                ]
                for pattern in address_patterns:
                    matches = re.findall(pattern, visible_text, re.IGNORECASE)
                    results['addresses'].extend(matches)
                
                social_platforms = {
                    'linkedin': r'linkedin\.com/(?:in|company)/[\w-]+',
                    'twitter': r'twitter\.com/[\w-]+',
                    'facebook': r'facebook\.com/[\w.-]+',
                    'instagram': r'instagram\.com/[\w.]+',
                    'youtube': r'youtube\.com/(?:c|channel|@)[\w-]+'
                }
                
                for platform, pattern in social_platforms.items():
                    matches = re.findall(pattern, response.text)
                    if matches:
                        results['social_links'].append({
                            'platform': platform,
                            'url': f"https://{matches[0]}"
                        })
                
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    text = link.get_text().lower()
                    
                    if any(word in href or word in text for word in ['contact', 'reach']):
                        results['contact_page'] = urljoin(url, link['href'])
                    
                    if any(word in href or word in text for word in ['about', 'team']):
                        results['about_page'] = urljoin(url, link['href'])
                
                if results['contact_page']:
                    try:
                        contact_resp = self.session.get(results['contact_page'], timeout=10)
                        if contact_resp.status_code == 200:
                            contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                            contact_text = contact_soup.get_text(separator=' ', strip=True)
                            contact_contacts = self.extract_contact_patterns(contact_text)
                            for email in contact_contacts['emails']:
                                if email not in results['emails']:
                                    results['emails'].append(email)
                            for phone in contact_contacts['phones']:
                                if phone not in results['phones']:
                                    results['phones'].append(phone)
                    except:
                        pass
            else:
                results['error'] = f'HTTP {response.status_code}'
                
        except Exception as e:
            results['error'] = f'Website analysis failed: {str(e)}'
        
        return results
    
    def analyze_profile(self, url):
        """Main dispatcher."""
        self.results['profile_url'] = url
        platform = self.identify_platform(url)
        username = self.extract_username(url, platform)
        
        self.results['platform'] = platform
        self.results['username'] = username
        
        if platform == 'youtube':
            profile_data = self.analyze_youtube_selenium(url, username)
        elif platform == 'instagram':
            profile_data = self.analyze_instagram_selenium(url, username)
        elif platform == 'facebook':
            profile_data = self.analyze_facebook_selenium(url, username)
        elif platform == 'linkedin':
            profile_data = self.analyze_linkedin_selenium(url, username)
        elif platform == 'company_website':
            profile_data = self.analyze_company_website(url, username)
        else:
            profile_data = {'error': f'Platform {platform} not supported', 'platform': platform}
        
        self.results['profile_data'] = profile_data
        self.results['contact_info'] = {
            'emails': profile_data.get('public_email') or profile_data.get('email') or profile_data.get('emails', []),
            'phones': profile_data.get('public_phone') or profile_data.get('phone') or profile_data.get('phones', []),
            'addresses': profile_data.get('address') or profile_data.get('addresses', []),
            'websites': profile_data.get('website') or profile_data.get('external_url') or profile_data.get('links', [])
        }
        
        self.selenium.close()
        return self.results


# ============== MAIN UI ==============

st.markdown('<p class="main-header">🔍 Multi-Platform Profile Analyzer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">LinkedIn • Instagram • Facebook • YouTube • Company Websites<br>Dynamic Content Support • Only Public Data</p>', unsafe_allow_html=True)

if SELENIUM_AVAILABLE:
    st.markdown("""
        <div class="success-box">
            ✅ <b>Selenium Ready:</b> Real browser automation active for all platforms.
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="warning-box">
            ⚠️ <b>Selenium Not Found:</b> Install with `pip install selenium webdriver-manager`
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="warning-box">
        ⚠️ <b>Legal Notice:</b> Only <b>publicly available</b> information analyzed.
    </div>
""", unsafe_allow_html=True)

st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    profile_url = st.text_input(
        "Enter Profile URL",
        placeholder="https://youtube.com/@NASA or https://facebook.com/page",
        help="YouTube now uses Selenium for dynamic content"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze Profile", use_container_width=True, type="primary")

with st.expander("📋 Example URLs"):
    examples = {
        "YouTube (Dynamic)": "https://youtube.com/@NASA",
        "Facebook (With Address)": "https://facebook.com/VNSGUNIVERSITY",
        "Instagram": "https://instagram.com/nasa",
        "LinkedIn (Limited)": "https://linkedin.com/in/nirbhay-bhuva-749715171",
        "Company": "https://www.spacex.com"
    }
    for name, url in examples.items():
        st.code(f"{name}: {url}", language=None)

if analyze_button and profile_url:
    if not profile_url.startswith(('http://', 'https://')):
        st.error("❌ Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("🔍 Analyzing... Opening real browser. YouTube needs 15-25 seconds for dynamic content..."):
            analyzer = MultiPlatformAnalyzer()
            results = analyzer.analyze_profile(profile_url)
        
        st.markdown("---")
        
        platform = results.get('platform', 'unknown')
        platform_colors = {
            'linkedin': '#0077b5',
            'instagram': '#e4405f',
            'facebook': '#1877f2',
            'youtube': '#ff0000',
            'company_website': '#6c757d',
            'unknown': '#dc3545'
        }
        
        plat_color = platform_colors.get(str(platform).lower(), '#6c757d')
        
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <div class="badge" style="background-color: {plat_color}; min-width: 150px;">
                    {str(platform).upper()}
                </div>
                <div style="font-size: 1.2rem; color: #666;">
                    @{results.get('username', 'unknown')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        profile_data = results.get('profile_data', {})
        
        if 'error' in profile_data and profile_data['error']:
            st.markdown(f"""
                <div class="error-box">
                    ⚠️ {profile_data['error']}
                </div>
            """, unsafe_allow_html=True)
        
        # Display based on platform
        if platform == 'youtube':
            display_youtube(profile_data)
        elif platform == 'linkedin':
            display_linkedin(profile_data)
        elif platform == 'facebook':
            display_facebook(profile_data)
        elif platform == 'instagram':
            display_instagram(profile_data)
        elif platform == 'company_website':
            display_company(profile_data)
        
        # Contact Summary
        st.markdown("---")
        st.subheader("📧 Contact Information Found")
        
        contact_info = results.get('contact_info', {})
        
        addresses = contact_info.get('addresses', [])
        if addresses:
            if isinstance(addresses, str):
                addresses = [addresses]
            st.markdown("""
                <div class="address-box">
                    <h4>📍 Address Found</h4>
                    <p style="font-size: 1.1rem; line-height: 1.6;">
                        {}
                    </p>
                </div>
            """.format(addresses[0].replace(', ', '<br>')), unsafe_allow_html=True)
        
        col_email, col_phone, col_web = st.columns(3)
        
        with col_email:
            emails = contact_info.get('emails', [])
            if emails:
                if isinstance(emails, str):
                    emails = [emails]
                st.markdown(f"""
                    <div class="metric-box">
                        <h3>✉️</h3>
                        <p><b>{len(emails)}</b> Email(s)</p>
                        <p style="font-size: 0.8rem;">{emails[0]}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No email found")
        
        with col_phone:
            phones = contact_info.get('phones', [])
            if phones:
                if isinstance(phones, str):
                    phones = [phones]
                st.markdown(f"""
                    <div class="metric-box">
                        <h3>📞</h3>
                        <p><b>{len(phones)}</b> Phone(s)</p>
                        <p style="font-size: 0.8rem;">{phones[0]}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No phone found")
        
        with col_web:
            websites = contact_info.get('websites', [])
            if websites:
                if isinstance(websites, str):
                    websites = [websites]
                st.markdown(f"""
                    <div class="metric-box">
                        <h3>🌐</h3>
                        <p><b>{len(websites)}</b> Website(s)</p>
                        <p style="font-size: 0.8rem;"><a href="{websites[0]}" target="_blank">Visit</a></p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No website found")
        
        with st.expander("🔍 View All Contact Details"):
            st.json(contact_info)
        
        with st.expander("🔧 View Raw Analysis Data"):
            st.json(results)

st.markdown("""
    <div class="footer">
        🔒 Only analyzes publicly available information • Respects platform ToS<br>
        <b>YouTube:</b> Selenium for dynamic content • <b>LinkedIn:</b> API required • <b>Facebook/Instagram:</b> Selenium automation<br>
        <b>Note:</b> First run downloads ChromeDriver automatically
    </div>
""", unsafe_allow_html=True)