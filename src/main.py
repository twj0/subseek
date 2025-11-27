import os
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
    total = 0
    skipped_existing = 0
    skipped_dead_or_invalid = 0
    for link in links:
        total += 1
        link_hash = hashlib.md5(link.encode("utf-8")).hexdigest()
        exists = session.query(ProxyNode).filter_by(unique_hash=link_hash).first()
        if exists:
            skipped_existing += 1
            continue
        if not is_node_alive(link):
            skipped_dead_or_invalid += 1
            continue
        protocol = link.split("://")[0]
        new_node = ProxyNode(protocol=protocol, link=link, unique_hash=link_hash, source=source)
        session.add(new_node)
        count += 1
    try:
        session.commit()
        print(
            f"[{source}] Parsed {total} links, saved {count} new nodes, "
            f"skipped existing={skipped_existing}, dead/invalid={skipped_dead_or_invalid}."
        )
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

    """
    主函数，协调整个数据收集和处理流程
    包括获取GitHub仓库、处理文件内容、搜索网络映射平台以及导出订阅列表
    """
    run_github = os.environ.get("RUN_GITHUB", "1") == "1"
    run_platforms = os.environ.get("RUN_PLATFORMS", "1") == "1"

    print("Start collecting...")  # 开始收集的提示信息

    if run_github:
        repos = get_github_repos()  # 获取GitHub仓库列表
        print(f"Found {len(repos)} repositories.")  # 打印找到的仓库数量
        for repo in repos:  # 遍历每个仓库
            print(f"Processing {repo}...")  # 处理当前仓库的提示信息
            contents = fetch_file_content(repo)  # 获取仓库中的文件内容
            for content in contents:  # 遍历每个文件内容
                links = parse_content(content)  # 解析内容中的链接
                if links:  # 如果找到链接
                    save_nodes(links, repo)  # 保存链接和对应的仓库信息
    else:
        print("Skipping GitHub repository collection.")

    if run_platforms:
        print("\nSearching network mapping platforms...")  # 搜索网络映射平台的提示信息
        urls = search_all_platforms(PLATFORM_KEYWORDS)  # 在所有平台上搜索URL
        print(f"Found {len(urls)} URLs from platforms.")  # 打印从平台找到的URL数量
        for url in urls:  # 遍历每个URL
            print(f"Fetching {url}...")  # 获取URL内容的提示信息
            content = fetch_url_content(url)  # 获取URL的内容
            if content:  # 如果内容存在
                links = parse_content(content)  # 解析内容中的链接
                if links:  # 如果找到链接
                    save_nodes(links, f"platform:{url}")  # 保存链接和对应的平台URL信息
    else:
        print("Skipping network mapping platforms.")

    export_subscription()  # 导出最终的订阅列表
    print("Done.")  # 完成处理的提示信息

if __name__ == "__main__":
    main()
