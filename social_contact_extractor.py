# app.py - Fixed Multi-Platform Profile Analyzer
# Complete working version with ChromeDriver error handling

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
import subprocess
import sys
from urllib.parse import urlparse, urljoin
from datetime import datetime
import platform

# ============== SELENIUM SETUP WITH ERROR HANDLING ==============
def setup_selenium():
    """Setup Selenium with proper error handling and ChromeDriver management"""
    try:
        # Check if Chrome is installed
        chrome_paths = []
        if platform.system() == "Windows":
            chrome_paths = [
                "C:/Program Files/Google/Chrome/Application/chrome.exe",
                "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
            ]
        elif platform.system() == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]
        else:  # Linux
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]
        
        chrome_installed = any(os.path.exists(path) for path in chrome_paths)
        
        if not chrome_installed:
            return None, "Chrome browser not found. Please install Google Chrome or Chromium."
        
        # Try to import selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
        except ImportError as e:
            return None, f"Selenium not installed: {str(e)}. Run: pip install selenium webdriver-manager"
        
        # Try to import webdriver_manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.utils import ChromeType
        except ImportError:
            return None, "webdriver-manager not installed. Run: pip install webdriver-manager"
        
        return (webdriver, Options, Service, By, WebDriverWait, EC, 
                TimeoutException, NoSuchElementException, WebDriverException, 
                ChromeDriverManager, ChromeType), "Success"
        
    except Exception as e:
        return None, f"Selenium setup failed: {str(e)}"

SELENIUM_SETUP = setup_selenium()
SELENIUM_AVAILABLE = SELENIUM_SETUP[0] is not None
SELENIUM_ERROR = SELENIUM_SETUP[1] if not SELENIUM_AVAILABLE else None

# ============== PAGE CONFIG ==============
st.set_page_config(
    page_title="Multi-Platform Profile Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============== STYLES ==============
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
    .chrome-fix-box { background: #e8f5e9; color: #1b5e20; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50; margin: 15px 0; }
    </style>
""", unsafe_allow_html=True)

# ============== SELENIUM SCRAPER ==============
class SeleniumScraper:
    def __init__(self):
        self.driver = None
        self.setup_success = False
        self.error_message = None
        
    def init_driver(self):
        """Initialize Chrome driver with fallback options"""
        if not SELENIUM_AVAILABLE:
            self.error_message = SELENIUM_ERROR or "Selenium not available"
            return None
        
        try:
            webdriver, Options, Service, By, WebDriverWait, EC, TimeoutException, NoSuchElementException, WebDriverException, ChromeDriverManager, ChromeType = SELENIUM_SETUP[0]
            
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
            
            # Try multiple ways to get ChromeDriver
            driver = None
            errors = []
            
            # Method 1: Use webdriver_manager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                errors.append(f"webdriver_manager failed: {str(e)}")
                
                # Method 2: Try without service (let selenium find it)
                try:
                    driver = webdriver.Chrome(options=options)
                except Exception as e2:
                    errors.append(f"Direct Chrome failed: {str(e2)}")
                    
                    # Method 3: Try with ChromeDriverManager from specific path
                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        from selenium.webdriver.chrome.service import Service as ChromeService
                        chrome_driver_path = ChromeDriverManager().install()
                        # On Linux, sometimes the path needs to be fixed
                        if platform.system() == "Linux" and "chromedriver-linux64" in chrome_driver_path:
                            # Try to use the chromedriver directly
                            service = ChromeService(chrome_driver_path)
                            driver = webdriver.Chrome(service=service, options=options)
                    except Exception as e3:
                        errors.append(f"Fallback failed: {str(e3)}")
            
            if driver is None:
                self.error_message = " | ".join(errors)
                return None
            
            # Execute CDP command to hide automation
            try:
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
                })
            except:
                pass
            
            self.driver = driver
            self.setup_success = True
            return driver
            
        except Exception as e:
            self.error_message = f"Driver initialization failed: {str(e)}"
            return None
    
    def get_page(self, url, wait_time=10):
        if not self.driver:
            self.init_driver()
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            time.sleep(5)
            
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            try:
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            except:
                return None
    
    def get_youtube_data(self, url):
        """Special method for YouTube with dynamic content waiting."""
        if not self.driver:
            self.init_driver()
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            time.sleep(8)
            
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#subscriber-count, yt-formatted-string#subscriber-count, .yt-formatted-string"))
                )
            except:
                pass
            
            time.sleep(3)
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            try:
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            except:
                return None
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# ============== DISPLAY FUNCTIONS ==============
def display_youtube(data):
    st.subheader("📺 YouTube Channel")
    
    cols = st.columns(3)
    
    subscribers = data.get('subscribers', 'N/A')
    videos = data.get('video_count', 'N/A')
    views = data.get('view_count', 'N/A')
    
    metrics = [
        (cols[0], "👥 Subscribers", subscribers, "#ff0000"),
        (cols[1], "🎬 Videos", videos, "#ff6d00"),
        (cols[2], "👀 Views", views, "#00c853")
    ]
    
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
                <div class="metric-box" style="border-color: {color};">
                    <p style="font-size: 0.9rem; color: #666;">{label}</p>
                    <h2 style="color: {color}; margin: 0;">{value}</h2>
                </div>
            """, unsafe_allow_html=True)
    
    if data.get('channel_name'):
        st.markdown(f"**Channel:** {data['channel_name']}")
    if data.get('handle'):
        st.markdown(f"**Handle:** @{data['handle']}")
    if data.get('joined_date'):
        st.markdown(f"**📅 Joined:** {data['joined_date']}")
    if data.get('location'):
        st.markdown(f"**📍 Location:** {data['location']}")
    
    if data.get('description'):
        with st.expander("📝 Description"):
            st.write(data['description'])
            if data.get('links') and len(data['links']) > 0:
                st.markdown("**🔗 Links:**")
                for link in data['links']:
                    st.markdown(f"• [{link}]({link})")

def display_linkedin(data):
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
                    <li><b>Manual Export:</b> LinkedIn allows PDF profile export</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 What we attempted to extract"):
            st.write(f"**URL:** {data.get('profile_url', 'N/A')}")
            st.write(f"**Username:** {data.get('username', 'N/A')}")
            st.write(f"**Page Title:** {data.get('page_title', 'N/A')}")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("""<div style="width:150px;height:150px;background:#ddd;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:3rem;">👤</div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**Name:** {data.get('name', 'N/A')}")
            st.markdown(f"**Headline:** {data.get('headline', 'N/A')}")
            st.markdown(f"**Location:** {data.get('location', 'N/A')}")

def display_facebook(data):
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
            st.markdown(f"""
                <div class="address-box">
                    <b>📍 Address:</b><br>
                    {data['address'].replace(', ', '<br>')}
                </div>
            """, unsafe_allow_html=True)
        
        if data.get('phone'):
            st.markdown(f"**📞 Phone:** {data['phone']}")
        if data.get('email'):
            st.markdown(f"**✉️ Email:** {data['email']}")
        if data.get('website'):
            st.markdown(f"**🌐 Website:** [{data['website']}]({data['website']})")

def display_instagram(data):
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

def display_company(data):
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
            soup = self.selenium.get_youtube_data(url)
            
            if not soup:
                results['error'] = 'Selenium failed to load YouTube page'
                return results
            
            visible_text = soup.get_text(separator=' ', strip=True)
            
            subscriber_patterns = [
                r'([\d,.]+[KMBkmb]?)\s*subscribers?',
                r'subscribers?\s*[:·]\s*([\d,.]+[KMBkmb]?)',
                r'([\d,]+(?:\.\d+)?)\s*subscribers?',
            ]
            
            for pattern in subscriber_patterns:
                match = re.search(pattern, visible_text, re.IGNORECASE)
                if match:
                    results['subscribers'] = match.group(1).strip()
                    break
            
            video_patterns = [
                r'([\d,.]+[KMBkmb]?)\s*videos?',
                r'videos?\s*[:·]\s*([\d,.]+[KMBkmb]?)',
                r'([\d,]+(?:\.\d+)?)\s*videos?',
            ]
            
            for pattern in video_patterns:
                match = re.search(pattern, visible_text, re.IGNORECASE)
                if match:
                    results['video_count'] = match.group(1).strip()
                    break
            
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                results['channel_name'] = meta_title.get('content', '').replace(' - YouTube', '').strip()
            
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                results['description'] = meta_desc.get('content')
            
            if results['description']:
                links = re.findall(r'https?://[^\s<>\"{}|\\^`\[\]]+', results['description'])
                results['links'] = list(set(links))
                contacts = self.extract_contact_patterns(results['description'])
                results['public_email'] = contacts['emails'][0] if contacts['emails'] else None
            
            if not results['subscribers']:
                sub_texts = soup.find_all(text=re.compile(r'[\d,.]+[KMBkmb]?\s*subscribers?', re.IGNORECASE))
                for text in sub_texts:
                    match = re.search(r'([\d,.]+[KMBkmb]?)', str(text))
                    if match:
                        results['subscribers'] = match.group(1)
                        break
            
        except Exception as e:
            results['error'] = f'YouTube analysis failed: {str(e)}'
        
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
            
            follower_patterns = [
                r'([\d,]+(?:\.\d+)?[KMBkmb]?)\s*followers?',
                r'followers?\s*[:·]\s*([\d,]+(?:\.\d+)?[KMBkmb]?)',
                r'([\d,]+(?:\.\d+)?)\s*people\s*follow\s*this',
            ]
            
            for pattern in follower_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    results['followers'] = match.group(1).strip()
                    break
            
            address_patterns = [
                r'(Post\s+Box\s+No\s*\d+[^.]{10,150})',
                r'(\d+[^,]{5,50}(?:Road|Street|Avenue|Marg)[^,]{5,100}(?:,\s*[A-Za-z\s]+){1,4})',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*(?:Gujarat|Maharashtra|Delhi|Rajasthan)[^,]{0,50}(?:,\s*India)?)',
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip()
                    if len(candidate) > 15:
                        results['address'] = candidate
                        break
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'l.php' in href and 'u=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'u' in parsed:
                        results['website'] = parsed['u'][0]
                        break
            
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
                
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    text = link.get_text().lower()
                    
                    if any(word in href or word in text for word in ['contact', 'reach']):
                        results['contact_page'] = urljoin(url, link['href'])
                    
                    if any(word in href or word in text for word in ['about', 'team']):
                        results['about_page'] = urljoin(url, link['href'])
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
            profile_data = {'error': 'Instagram analysis requires authentication'}
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

# ChromeDriver fix instructions
if not SELENIUM_AVAILABLE:
    st.markdown(f"""
        <div class="error-box">
            ⚠️ <b>Selenium/ChromeDriver Error:</b> {SELENIUM_ERROR or "ChromeDriver not available"}
        </div>
        <div class="chrome-fix-box">
            <h4>🔧 How to Fix ChromeDriver Issues:</h4>
            <ol>
                <li><b>Install Google Chrome</b> - Download from <a href="https://www.google.com/chrome/" target="_blank">google.com/chrome</a></li>
                <li><b>Install required packages:</b><br>
                <code>pip install selenium webdriver-manager</code></li>
                <li><b>If Chrome is installed, try:</b>
                    <ul>
                        <li>Restart your computer</li>
                        <li>Run: <code>pip install --upgrade selenium webdriver-manager</code></li>
                        <li>On Linux: <code>sudo apt-get install chromium-browser</code></li>
                    </ul>
                </li>
                <li><b>Alternative - Manual ChromeDriver download:</b>
                    <ul>
                        <li>Download from <a href="https://chromedriver.chromium.org/" target="_blank">chromedriver.chromium.org</a></li>
                        <li>Add to PATH or place in project directory</li>
                    </ul>
                </li>
            </ol>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="success-box">
            ✅ <b>Selenium Ready:</b> Real browser automation active for all platforms.
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
        "Company Website": "https://www.spacex.com"
    }
    for name, url in examples.items():
        st.code(f"{name}: {url}", language=None)

if analyze_button and profile_url:
    if not profile_url.startswith(('http://', 'https://')):
        st.error("❌ Please enter a valid URL starting with http:// or https://")
    else:
        if not SELENIUM_AVAILABLE:
            st.error("❌ Selenium is not available. Please fix ChromeDriver issues first.")
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
                st.info("Instagram scraping is limited. Please use the official API.")
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
                st.markdown(f"""
                    <div class="address-box">
                        <h4>📍 Address Found</h4>
                        <p style="font-size: 1.1rem; line-height: 1.6;">
                            {addresses[0].replace(', ', '<br>')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
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
        <b>YouTube:</b> Selenium for dynamic content • <b>LinkedIn:</b> API required • <b>Facebook:</b> Selenium automation<br>
        <b>Note:</b> First run downloads ChromeDriver automatically. If you see errors, install Chrome browser.
    </div>
""", unsafe_allow_html=True)