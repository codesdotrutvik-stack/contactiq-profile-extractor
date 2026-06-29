from playwright.sync_api import sync_playwright
import time
import re
import json

class SocialMediaScraper:
    def __init__(self, headless=False):
        """
        headless=False એટલે બ્રાઉઝર ખુલ્લું દેખાશે
        headless=True એટલે બેકગ્રાઉન્ડમાં ચાલશે (ઝડપી)
        """
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
    
    def start(self):
        """બ્રાઉઝર શરૂ કરો"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = self.browser.new_page(
            viewport={'width': 1280, 'height': 800}
        )
        # વેબસાઇટને ઓળખાવા માટે User-Agent સેટ કરો
        self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return self.page
    
    def close(self):
        """બ્રાઉઝર બંધ કરો"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def wait_for_element(self, selector, timeout=10000):
        """એલિમેન્ટ લોડ થાય ત્યાં સુધી રાહ જુઓ"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    # ==================== INSTAGRAM ====================
    def scrape_instagram(self, username):
        """Instagram પ્રોફાઇલમાંથી ડેટા ફેચ કરો"""
        data = {
            'platform': 'Instagram',
            'username': username,
            'full_name': 'N/A',
            'bio': 'N/A',
            'followers': 'N/A',
            'following': 'N/A',
            'posts': 'N/A',
            'business': 'N/A',
            'external_url': 'N/A',
            'is_private': False,
            'error': None
        }
        
        try:
            print(f"\n🔍 Instagram પ્રોફાઇલ સ્ક્રેપ કરી રહ્યા છીએ: @{username}")
            url = f"https://www.instagram.com/{username}/"
            self.page.goto(url, wait_until='networkidle')
            time.sleep(3)
            
            # ચેક કરો કે પ્રોફાઇલ પ્રાઇવેટ છે કે નહીં
            if self.page.query_selector("text=This Account is Private"):
                data['is_private'] = True
                data['error'] = "આ એકાઉન્ટ પ્રાઇવેટ છે"
                return data
            
            # પૂરું નામ
            fullname_selector = "h1._ap3a, h2._ap3a"
            if self.wait_for_element(fullname_selector, 5000):
                data['full_name'] = self.page.query_selector(fullname_selector).inner_text().strip()
            
            # બાયો - મોટા ભાગના Instagram selectors
            bio_selectors = [
                "div._ap3a div._aacl._aaco._aacu._aacx._aad7._aade",
                "div._aacl._aaco._aacu._aacx._aad7._aade",
                "section h2 + div span"
            ]
            for selector in bio_selectors:
                elem = self.page.query_selector(selector)
                if elem:
                    data['bio'] = elem.inner_text().strip()
                    break
            
            # આંકડા (posts, followers, following)
            stats_selector = "li._acap span._ac2a, section ul li span"
            stats_elements = self.page.query_selector_all(stats_selector)
            stats_texts = [elem.inner_text().strip() for elem in stats_elements if elem.inner_text().strip()]
            
            if len(stats_texts) >= 3:
                data['posts'] = stats_texts[0]
                data['followers'] = stats_texts[1]
                data['following'] = stats_texts[2]
            
            # બાહ્ય URL
            ext_url_selector = "a._ac6s, a._ap30"
            ext_url_elem = self.page.query_selector(ext_url_selector)
            if ext_url_elem:
                data['external_url'] = ext_url_elem.get_attribute('href')
            
            # શું વ્યવસાયિક એકાઉન્ટ છે?
            if self.page.query_selector("span:has-text('Business'), span:has-text('Creator')"):
                data['business'] = 'Yes'
            else:
                data['business'] = 'No'
            
            # પ્રોફાઇલ પિક્ચર URL
            img_elem = self.page.query_selector("img._aad0")
            if img_elem:
                data['profile_pic'] = img_elem.get_attribute('src')
            
            print(f"✅ Instagram ડેટા મળ્યો!")
            
        except Exception as e:
            data['error'] = str(e)
            print(f"❌ Instagram ભૂલ: {e}")
        
        return data
    
    # ==================== YOUTUBE ====================
    def scrape_youtube(self, channel_id):
        """YouTube ચેનલમાંથી ડેટા ફેચ કરો"""
        data = {
            'platform': 'YouTube',
            'channel_id': channel_id,
            'channel_name': 'N/A',
            'subscribers': 'N/A',
            'videos': 'N/A',
            'description': 'N/A',
            'joined_date': 'N/A',
            'country': 'N/A',
            'error': None
        }
        
        try:
            print(f"\n🔍 YouTube ચેનલ સ્ક્રેપ કરી રહ્યા છીએ: @{channel_id}")
            url = f"https://www.youtube.com/@{channel_id}"
            self.page.goto(url, wait_until='networkidle')
            time.sleep(3)
            
            # ચેનલનું નામ
            name_selector = "ytd-channel-name #text"
            if self.wait_for_element(name_selector, 5000):
                data['channel_name'] = self.page.query_selector(name_selector).inner_text().strip()
            
            # સબ્સ્ક્રાઇબર્સ
            subs_selector = "#subscriber-count"
            if self.wait_for_element(subs_selector, 3000):
                data['subscribers'] = self.page.query_selector(subs_selector).inner_text().strip()
            
            # વિડિઓસની સંખ્યા
            videos_selector = "ytd-channel-stats #text"
            video_elems = self.page.query_selector_all(videos_selector)
            if len(video_elems) >= 2:
                data['videos'] = video_elems[1].inner_text().strip()
            
            # ચેનલ વર્ણન
            desc_selector = "#description-text"
            if self.wait_for_element(desc_selector, 3000):
                data['description'] = self.page.query_selector(desc_selector).inner_text().strip()
            
            # ક્યારે જોઈન કર્યું
            date_selector = "#right-column #owner #info #date"
            if self.wait_for_element(date_selector, 3000):
                data['joined_date'] = self.page.query_selector(date_selector).inner_text().strip()
            
            # દેશ
            country_selector = "#right-column #owner #info #country"
            if self.wait_for_element(country_selector, 3000):
                data['country'] = self.page.query_selector(country_selector).inner_text().strip()
            
            print(f"✅ YouTube ડેટા મળ્યો!")
            
        except Exception as e:
            data['error'] = str(e)
            print(f"❌ YouTube ભૂલ: {e}")
        
        return data
    
    # ==================== FACEBOOK ====================
    def scrape_facebook(self, username):
        """Facebook પ્રોફાઇલમાંથી ડેટા ફેચ કરો"""
        data = {
            'platform': 'Facebook',
            'username': username,
            'full_name': 'N/A',
            'bio': 'N/A',
            'followers': 'N/A',
            'likes': 'N/A',
            'about': 'N/A',
            'education': 'N/A',
            'work': 'N/A',
            'location': 'N/A',
            'error': None
        }
        
        try:
            print(f"\n🔍 Facebook પ્રોફાઇલ સ્ક્રેપ કરી રહ્યા છીએ: @{username}")
            url = f"https://www.facebook.com/{username}"
            self.page.goto(url, wait_until='networkidle')
            time.sleep(5)
            
            # Facebook લોગિન પેજ આવે તો
            if self.page.query_selector("input[name='email']"):
                print("⚠️ Facebook લોગિન જરૂરી છે. કૃપા કરીને મેન્યુઅલી લોગિન કરો.")
                print("ℹ️ આપણે આગળ વધતા પહેલા 30 સેકન્ડ રાહ જોશું...")
                time.sleep(30)
            
            # પૂરું નામ
            name_selectors = [
                "h1",
                "span.x1lliihq",
                "div.x1iorvi4 span"
            ]
            for selector in name_selectors:
                elem = self.page.query_selector(selector)
                if elem and elem.inner_text().strip():
                    data['full_name'] = elem.inner_text().strip()
                    break
            
            # About/Bio
            bio_selector = "div[data-testid='profile_bio_text'], div.x1iyjqo2 span"
            if self.wait_for_element(bio_selector, 3000):
                data['bio'] = self.page.query_selector(bio_selector).inner_text().strip()
            
            # Followers
            followers_selector = "span.x1yk3o3k:has-text('followers'), div[role='tooltip']"
            followers_elem = self.page.query_selector(followers_selector)
            if followers_elem:
                data['followers'] = followers_elem.inner_text().strip()
            
            # Location
            location_selectors = [
                "span:has-text('Lives in')",
                "span:has-text('From')",
                "div.x1iyjqo2 span"
            ]
            for selector in location_selectors:
                elem = self.page.query_selector(selector)
                if elem:
                    text = elem.inner_text().strip()
                    if 'Lives in' in text or 'From' in text:
                        data['location'] = text
                        break
            
            # Work/Education - Facebook પર 'About' સેક્શનમાંથી
            about_selector = "div[data-testid='profile_details'] div"
            if self.wait_for_element(about_selector, 3000):
                about_text = self.page.query_selector(about_selector).inner_text().strip()
                data['about'] = about_text
                
                # Work શોધો
                if 'Work' in about_text or 'works at' in about_text.lower():
                    work_match = re.search(r'Work(.*?)(?=Education|College|$)', about_text, re.DOTALL)
                    if work_match:
                        data['work'] = work_match.group(1).strip()
                
                # Education શોધો
                if 'Education' in about_text or 'studied at' in about_text.lower():
                    edu_match = re.search(r'Education(.*?)(?=Work|College|$)', about_text, re.DOTALL)
                    if edu_match:
                        data['education'] = edu_match.group(1).strip()
            
            print(f"✅ Facebook ડેટા મળ્યો!")
            
        except Exception as e:
            data['error'] = str(e)
            print(f"❌ Facebook ભૂલ: {e}")
        
        return data
    
    # ==================== SCREENSHOT ====================
    def take_screenshot(self, filename="screenshot.png"):
        """સ્ક્રીનશોટ લો"""
        try:
            self.page.screenshot(path=filename, full_page=True)
            print(f"📸 Screenshot સેવ થયો: {filename}")
            return True
        except Exception as e:
            print(f"❌ Screenshot ભૂલ: {e}")
            return False


# ==================== MAIN FUNCTION ====================
def main():
    """મુખ્ય ફંક્શન - ત્રણેય પ્લેટફોર્મ સ્ક્રેપ કરો"""
    
    scraper = SocialMediaScraper(headless=False)  # False = બ્રાઉઝર ખુલ્લું દેખાશે
    scraper.start()
    
    all_data = {}
    
    try:
        # 1. Instagram
        insta_username = input("\n📸 Instagram યુઝરનામ દાખલ કરો (દા.ત. cristiano): ").strip()
        if insta_username:
            insta_data = scraper.scrape_instagram(insta_username)
            all_data['instagram'] = insta_data
        
        # 2. YouTube
        yt_channel = input("\n🎥 YouTube ચેનલ ID દાખલ કરો (દા.ત. MrBeast): ").strip()
        if yt_channel:
            yt_data = scraper.scrape_youtube(yt_channel)
            all_data['youtube'] = yt_data
        
        # 3. Facebook
        fb_username = input("\n📘 Facebook યુઝરનામ દાખલ કરો (દા.ત. zuck): ").strip()
        if fb_username:
            fb_data = scraper.scrape_facebook(fb_username)
            all_data['facebook'] = fb_data
        
        # 📊 બધો ડેટા શો કરો
        print("\n" + "="*60)
        print("📊  સ્ક્રેપિંગ રિઝલ્ટ્સ")
        print("="*60)
        
        for platform, data in all_data.items():
            if data and not data.get('error'):
                print(f"\n🔹 {platform.upper()}")
                print("-"*40)
                for key, value in data.items():
                    if key not in ['platform', 'error'] and value not in ['N/A', None]:
                        print(f"   {key.replace('_', ' ').title()}: {value}")
            elif data and data.get('error'):
                print(f"\n🔹 {platform.upper()}: ❌ {data['error']}")
        
        # 💾 JSON માં સેવ કરો
        with open('profile_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        print("\n💾 ડેટા 'profile_data.json' માં સેવ થયો")
        
        # 📸 Screenshot લો
        scraper.take_screenshot("profile_screenshot.png")
        
    except KeyboardInterrupt:
        print("\n⏹️ પ્રોગ્રામ બંધ કરવામાં આવ્યો")
    except Exception as e:
        print(f"❌ મુખ્ય ભૂલ: {e}")
    finally:
        scraper.close()
        print("\n🔚 સ્ક્રેપર બંધ થયો")


if __name__ == "__main__":
    main()