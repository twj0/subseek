import base64
import re

def parse_content(text):
    """Parse proxy links from text content"""
    links = []

    try:
        clean_text = text.replace(" ", "").replace("\n", "")
        decoded = base64.b64decode(clean_text + '=' * (-len(clean_text) % 4)).decode('utf-8', errors='ignore')
        text += "\n" + decoded
    except:
        pass

    patterns = [
        r'(vmess://[a-zA-Z0-9+/=]+)',
        r'(vless://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(ss://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(trojan://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)'
    ]

    for pattern in patterns:
        found = re.findall(pattern, text)
        links.extend(found)

    return links
