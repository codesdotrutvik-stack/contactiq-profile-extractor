from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
import os
from urllib.parse import urljoin, urlparse
import json

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============================================
# HELPER FUNCTIONS
# ============================================

def extract_phone(text):
    """Extract phone numbers from text"""
    if not text:
        return []

    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10}',
        r'\d{3}-\d{3}-\d{4}',
        r'\(\d{3}\)\s*\d{3}-\d{4}',
        r'\d{3}\.\d{3}\.\d{4}',
    ]

    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        phones.extend(matches)

    # Clean and deduplicate
    valid = []
    seen = set()
    for p in phones:
        clean = re.sub(r'[^0-9+]', '', p)
        if 7 <= len(clean) <= 15 and clean not in seen:
            seen.add(clean)
            valid.append(p.strip())

    logger.info(f"Found {len(valid)} phone numbers")
    return valid[:5]  # Return top 5

def extract_email(text):
    """Extract email addresses from text"""
    if not text:
        return []

    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text, re.IGNORECASE)

    # Filter out invalid examples
    filtered = []
    seen = set()
    for e in emails:
        e = e.lower()
        if not any(x in e for x in ['example', 'domain.com', '.png', '.jpg', '.gif']):
            if e not in seen:
                seen.add(e)
                filtered.append(e)

    logger.info(f"Found {len(filtered)} email addresses")
    return filtered[:5]

def extract_address(text):
    """Extract address from text"""
    if not text:
        return None

    # Split into lines
    lines = text.split('\n')

    # Address keywords
    keywords = ['street', 'st', 'road', 'rd', 'avenue', 'ave', 'lane', 'ln',
                'drive', 'dr', 'suite', 'ste', 'building', 'bldg', 'floor',
                'plaza', 'square', 'blvd', 'boulevard', 'way', 'place', 'pl']

    # Look for lines with address patterns
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10 or len(line) > 200:
            continue

        # Check for address keywords
        has_keyword = any(kw in line.lower() for kw in keywords)
        has_number = bool(re.search(r'\d+', line))
        has_comma = ',' in line

        if has_keyword and has_number:
            logger.info(f"Found potential address: {line[:50]}...")
            return line

    # Try to find address with postal code
    zip_pattern = r'\b\d{5}(-\d{4})?\b|\b\d{6}\b'
    for line in lines:
        line = line.strip()
        if len(line) > 10 and len(line) < 200:
            if re.search(zip_pattern, line):
                logger.info(f"Found address with postal code: {line[:50]}...")
                return line

    # Try to find "Address:" pattern
    for line in lines:
        line = line.strip()
        if 'address' in line.lower() and ':' in line:
            parts = line.split(':', 1)
            if len(parts) > 1 and len(parts[1].strip()) > 10:
                address = parts[1].strip()
                logger.info(f"Found address from label: {address[:50]}...")
                return address

    return None

def get_business_name_from_url(url):
    """Extract business name from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')

    # Remove common TLDs
    for tld in ['.com', '.org', '.net', '.co', '.io', '.gov', '.edu']:
        if domain.endswith(tld):
            domain = domain[:-len(tld)]

    # Split by dots and take first part
    parts = domain.split('.')
    if parts:
        name = parts[0].replace('-', ' ').replace('_', ' ').title()
        logger.info(f"Extracted business name: {name}")
        return name

    return "Business"

# ============================================
# MAIN EXTRACTION FUNCTION
# ============================================

def extract_contacts_from_url(url):
    """Main function to extract contacts"""
    logger.info(f"Starting extraction for: {url}")

    # Clean URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Try different URL variations
    url_variations = [
        url,
        urljoin(url, '/'),
        urljoin(url, '/contact'),
        urljoin(url, '/contact-us'),
        urljoin(url, '/contact.html'),
        urljoin(url, '/about'),
        urljoin(url, '/about-us'),
        urljoin(url, '/reach-us'),
        urljoin(url, '/get-in-touch'),
        urljoin(url, '/help'),
        urljoin(url, '/support'),
        urljoin(url, '/company/contact'),
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    session = requests.Session()
    session.headers.update(headers)

    for page_url in url_variations[:8]:  # Try first 8 variations
        try:
            logger.info(f"Trying: {page_url}")

            response = session.get(page_url, timeout=15, allow_redirects=True)
            logger.info(f"Status: {response.status_code}, Length: {len(response.text)}")

            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Get text content
                text = soup.get_text(separator='\n', strip=True)

                # Extract information
                phones = extract_phone(text)
                emails = extract_email(text)
                address = extract_address(text)

                # If we found ANYTHING
                if phones or emails or address:
                    result = {
                        "business_name": get_business_name_from_url(url),
                        "website": url,
                        "page_used": page_url,
                        "phone_numbers": phones,
                        "emails": emails,
                        "address": address or "Not found",
                        "source_url": url,
                        "extracted_at": datetime.now().isoformat(),
                        "status": "success"
                    }
                    logger.info(f"SUCCESS: Found {len(phones)} phones, {len(emails)} emails")
                    return result

        except requests.Timeout:
            logger.warning(f"Timeout for {page_url}")
            continue
        except requests.ConnectionError:
            logger.warning(f"Connection error for {page_url}")
            continue
        except Exception as e:
            logger.warning(f"Error with {page_url}: {str(e)}")
            continue

    # If nothing found
    logger.warning("No contact information found on any page")
    return {
        "business_name": get_business_name_from_url(url),
        "website": url,
        "phone_numbers": [],
        "emails": [],
        "address": "Not found",
        "source_url": url,
        "extracted_at": datetime.now().isoformat(),
        "status": "no_data",
        "message": "No contact information found on website"
    }

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the frontend"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Template error: {str(e)}")
        return f"Error loading template: {str(e)}", 500

@app.route('/api/extract', methods=['POST'])
def extract_contacts():
    """API endpoint to extract contacts"""
    try:
        # Get URL from request
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing URL parameter"}), 400

        url = data['url'].strip()
        logger.info(f"Received URL: {url}")

        # Extract contacts
        result = extract_contacts_from_url(url)

        # Save to file for debugging
        try:
            with open('data/debug.json', 'w') as f:
                json.dump(result, f, indent=2)
        except:
            pass

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['POST'])
def test_scrape():
    """Debug endpoint to test scraping"""
    try:
        data = request.get_json()
        url = data.get('url', '')

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)

        return jsonify({
            "url": url,
            "status_code": response.status_code,
            "content_length": len(response.text),
            "content_preview": response.text[:500],
            "headers": dict(response.headers)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
