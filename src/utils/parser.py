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
        r'(trojan://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(ssr://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(socks5://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(socks://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(hysteria://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(hy2://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(tuic://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
        r'(wireguard://[a-zA-Z0-9\-\._~:/?#\[\]@!$&\'()*+,;=%]+)',
    ]

    for pattern in patterns:
        found = re.findall(pattern, text)
        links.extend(found)

    unique_links = []
    seen = set()
    for link in links:
        if link in seen:
            continue
        seen.add(link)
        unique_links.append(link)

    return unique_links
