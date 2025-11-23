import requests
import hashlib
from src.database.models import Session, ProxyNode
from src.collectors.github import get_github_repos, fetch_file_content
from src.collectors.platforms import search_all_platforms
from src.utils.parser import parse_content
from src.utils.validator import is_node_alive
from src.exporters.subscription import export_subscription
from config.settings import PLATFORM_KEYWORDS

def save_nodes(links, source):
    session = Session()
    count = 0
    for link in links:
        link_hash = hashlib.md5(link.encode("utf-8")).hexdigest()
        exists = session.query(ProxyNode).filter_by(unique_hash=link_hash).first()
        if exists:
            continue
        if not is_node_alive(link):
            continue
        protocol = link.split("://")[0]
        new_node = ProxyNode(protocol=protocol, link=link, unique_hash=link_hash, source=source)
        session.add(new_node)
        count += 1
    try:
        session.commit()
        print(f"[{source}] Saved {count} new nodes.")
    except Exception as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()

def fetch_url_content(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        pass
    return None

def main():
    print("Start collecting...")
    repos = get_github_repos()
    print(f"Found {len(repos)} repositories.")
    for repo in repos:
        print(f"Processing {repo}...")
        contents = fetch_file_content(repo)
        for content in contents:
            links = parse_content(content)
            if links:
                save_nodes(links, repo)
    print("\nSearching network mapping platforms...")
    urls = search_all_platforms(PLATFORM_KEYWORDS)
    print(f"Found {len(urls)} URLs from platforms.")
    for url in urls:
        print(f"Fetching {url}...")
        content = fetch_url_content(url)
        if content:
            links = parse_content(content)
            if links:
                save_nodes(links, f"platform:{url}")
    export_subscription()
    print("Done.")

if __name__ == "__main__":
    main()
