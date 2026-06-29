import streamlit as st
import re
import time
import json
from datetime import datetime
from urllib.parse import urlparse

# Selenium Imports with graceful fallback
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    st.error("Selenium not installed. Run: `pip install selenium webdriver-manager`")

st.set_page_config(page_title="Multi-Platform Analyzer | CodesDot", layout="wide")

st.title("🔍 Multi-Platform Public Profile Analyzer")
st.caption("YouTube • Facebook • Instagram • LinkedIn • Websites")

if not SELENIUM_AVAILABLE:
    st.stop()

class ProfileAnalyzer:
    def __init__(self):
        self.driver = None
    
    def init_driver(self):
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver = driver
            return driver
        except Exception as e:
            st.error(f"❌ ChromeDriver Error: {str(e)}")
            st.info("Tip: Close all Chrome windows and try again.")
            return None
    
    def get_page(self, url, wait=12):
        if not self.driver:
            self.init_driver()
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            time.sleep(6)
            WebDriverWait(self.driver, wait).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return self.driver.page_source
        except:
            try:
                return self.driver.page_source
            except:
                return None

    def close(self):
        if self.driver:
            self.driver.quit()

# ====================== UI ======================

url = st.text_input("Enter Profile URL", 
                    value="https://www.facebook.com/VNSGUNIVERSITY",
                    placeholder="Paste any social profile link")

if st.button("🔍 Analyze Profile", type="primary", use_container_width=True):
    if url:
        analyzer = ProfileAnalyzer()
        with st.spinner("Opening browser & analyzing... (15-25 seconds for YouTube/Facebook)"):
            html = analyzer.get_page(url)
            analyzer.close()
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')  # You'll need to import BeautifulSoup
                text = soup.get_text()
                
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                phones = re.findall(r'[\+]?[0-9][0-9\s\-\(\)]{8,}', text)
                
                st.success("✅ Analysis Complete")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📧 Emails")
                    st.write(emails[:5] if emails else "No email found")
                with col2:
                    st.subheader("📱 Phones")
                    st.write(phones[:5] if phones else "No phone found")
                
                with st.expander("Raw Text"):
                    st.text_area("Preview", text[:1000], height=400)
            else:
                st.error("Failed to load page")
    else:
        st.warning("Enter URL")

st.caption("CodesDot Solution LLP - Final Test Task")