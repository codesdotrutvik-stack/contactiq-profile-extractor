import re
from urllib.parse import urlparse, urljoin

def find_official_website(company_name):
    """Better website discovery"""
    try:
        query = f"{company_name} official website OR 'contact us' OR 'about us'"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a')
        for link in links:
            href = link.get('href', '')
            if 'url?q=' in href:
                actual_url = href.split('url?q=')[1].split('&')[0]
                if company_name.lower().replace(' ', '') in actual_url.lower() or \
                   any(ext in actual_url for ext in ['.com', '.io', '.in', '.co.in']):
                    if not any(bad in actual_url for bad in ['facebook', 'linkedin', 'instagram', 'youtube', 'twitter']):
                        return actual_url
        return None
    except:
        return None


def scrape_contact_page(website_url):
    """Direct company website + contact page scraping"""
    try:
        # Main page
        response = requests.get(website_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = soup.get_text(separator=' ')
        
        info = {'phone': None, 'email': None, 'address': None}
        
        # Improved Phone Regex (Indian numbers bhi support)
        phone_patterns = [
            r'(\+91[-\s]?)?[6-9]\d{9}',
            r'(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})'
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                info['phone'] = match.group(0).strip()
                break
        
        # Better Email
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if emails:
            # Prefer info@, contact@, hello@ etc.
            priority = ['info@', 'contact@', 'hello@', 'admin@', 'hr@']
            for p in priority:
                for e in emails:
                    if p in e.lower():
                        info['email'] = e
                        break
                if info['email']: break
            if not info['email']:
                info['email'] = emails[0]
        
        # Address (Improved)
        address_match = re.search(r'(?:Address|Location)[:\s]*(.+?)(?=\d{6}|Contact|Phone|Email|\n|$)', text, re.I)
        if address_match:
            info['address'] = address_match.group(1).strip()[:150]
        
        return info
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
        'description': 'Not found',
        'source': 'Google + Website Scraping + Mistral'
    }
    
    try:
        # 1. Try direct website scraping (Most Important)
        website = find_official_website(company_name)
        if website:
            result['website'] = website.replace('https://', '').replace('http://', '')
            contact_data = scrape_contact_page(website)
            if contact_data:
                if contact_data['phone']: result['phone'] = contact_data['phone']
                if contact_data['email']: result['email'] = contact_data['email']
                if contact_data['address']: result['address'] = contact_data['address']
        
        # 2. Google Search (backup)
        google_data = search_company_google(company_name)
        if google_data:
            for k, v in google_data.items():
                if v and result[k] == 'Not found':
                    result[k] = v
        
        # 3. Mistral (for structured info)
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