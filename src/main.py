"""
主程序入口模块
负责协调整个代理节点收集和处理流程
"""

import os
import time
import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.database.models import Session, ProxyNode
from src.collectors.github import get_github_repos, fetch_file_content
from src.collectors.platforms import search_all_platforms
from src.utils.parser import parse_content
from src.utils.validator import is_node_alive_with_china_proxy
from src.utils.china_proxy_reader import is_china_proxy_enabled, get_china_proxy_stats
from src.exporters.subscription import export_subscription
from config.settings import PLATFORM_KEYWORDS

def save_nodes(links, source):
    """
    保存解析到的代理节点链接到数据库
    
    Args:
        links (list): 代理节点链接列表
        source (str): 节点来源标识
        
    Returns:
        None
    """
    # 创建数据库会话
    session = Session()

    # 初始化计数器
    count = 0  # 成功保存的节点数量
    total = 0  # 总共处理的链接数量
    skipped_existing = 0  # 已存在而跳过的节点数量
    skipped_dead_or_invalid = 0  # 无效或失效而跳过的节点数量
    # 遍历所有代理链接
    for link in links:
        total += 1
        # 生成链接的唯一哈希值
        link_hash = hashlib.md5(link.encode("utf-8")).hexdigest()
        # 检查链接是否已存在于数据库中
        exists = session.query(ProxyNode).filter_by(unique_hash=link_hash).first()
        if exists:
            skipped_existing += 1
            continue
        # 检查节点是否可用
        if not is_node_alive_with_china_proxy(link):
            skipped_dead_or_invalid += 1
            continue
        # 提取协议类型
        protocol = link.split("://")[0]
        # 创建新的代理节点对象
        new_node = ProxyNode(protocol=protocol, link=link, unique_hash=link_hash, source=source)
        # 添加到会话中
        session.add(new_node)
        count += 1
    try:
        # 提交事务
        session.commit()
        # 打印处理结果统计信息
        print(
            f"[{source}] Parsed {total} links, saved {count} new nodes, "
            f"skipped existing={skipped_existing}, dead/invalid={skipped_dead_or_invalid}."
        )
    except Exception as e:
        # 发生错误时回滚事务
        session.rollback()
        print(f"Database error: {e}")
    finally:
        # 确保会话被关闭
        session.close()

def fetch_url_content(url):
    """
    获取指定URL的内容
    
    该函数通过HTTP GET请求获取指定URL的页面内容，并处理可能出现的异常情况。
    Args:
        url (str): 要获取内容的URL地址
        
    Returns:
        str or None: 成功时返回页面内容，失败时返回None
    异常处理:
        捕获所有可能的异常，在出现任何错误时静默返回None
    超时设置:
        请求超时时间设置为10秒
    """
    try:  # 尝试发送HTTP GET请求
        resp = requests.get(url, timeout=10)  # 发送GET请求，设置10秒超时
        if resp.status_code == 200:  # 检查响应状态码是否为200
            return resp.text  # 返回页面文本内容
    except:  # 捕获所有异常
        pass
    return None  # 默认返回None

def main():

    """
    主函数，协调整个数据收集和处理流程
    包括获取GitHub仓库、处理文件内容、搜索网络映射平台以及导出订阅列表
    """
    # 从环境变量读取配置，决定是否运行特定功能模块
    # RUN_GITHUB控制是否处理GitHub仓库，RUN_PLATFORMS控制是否处理网络映射平台
    run_github = os.environ.get("RUN_GITHUB", "1") == "1"
    run_platforms = os.environ.get("RUN_PLATFORMS", "1") == "1"

    total_start = time.perf_counter()  # 记录总开始时间

    print("Start collecting...")  # 开始收集的提示信息

    github_start = time.perf_counter()  # 记录GitHub处理阶段开始时间
    # GitHub仓库处理流程
    if run_github:
        repos = get_github_repos()  # 获取GitHub仓库列表
        print(f"Found {len(repos)} repositories.")  # 打印找到的仓库数量

        max_workers = int(os.environ.get("MAX_WORKERS", "8")) or 1  # 设置线程池最大工作线程数

        def handle_repo(repo):
            """处理单个仓库的函数"""
            print(f"Processing {repo}...")
            contents = fetch_file_content(repo)  # 获取仓库文件内容
            repo_links = []
            for content in contents:
                links = parse_content(content)  # 解析文件内容中的链接
                if links:
                    repo_links.extend(links)  # 收集所有链接
            return repo, repo_links

        github_results = []  # 存储GitHub处理结果
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # 创建线程池执行器
            futures = [executor.submit(handle_repo, repo) for repo in repos]  # 提交所有仓库处理任务
            for future in as_completed(futures):  # 等待所有任务完成
                repo, repo_links = future.result()
                if repo_links:
                    github_results.append((repo, repo_links))  # 保存有链接的结果

        for repo, repo_links in github_results:
            save_nodes(repo_links, repo)  # 保存链接和对应的仓库信息
    else:
        print("Skipping GitHub repository collection.")  # 跳过GitHub仓库收集的提示信息
    github_end = time.perf_counter()  # 记录GitHub处理阶段结束时间
    print(f"GitHub phase took {github_end - github_start:.2f} seconds.")  # 打印GitHub处理阶段耗时

    platform_start = time.perf_counter()  # 记录平台搜索阶段开始时间
    # 网络映射平台搜索流程
    if run_platforms:
        print("\nSearching network mapping platforms...")  # 搜索网络映射平台的提示信息
        urls = search_all_platforms(PLATFORM_KEYWORDS)  # 在所有平台上搜索URL
        print(f"Found {len(urls)} URLs from platforms.")  # 打印从平台找到的URL数量

        max_workers = int(os.environ.get("MAX_WORKERS", "8")) or 1  # 设置线程池最大工作线程数

        def handle_url(url):
            """处理单个URL的函数"""
            print(f"Fetching {url}...")
            content = fetch_url_content(url)  # 获取URL内容
            if not content:
                return url, []
            links = parse_content(content)  # 解析内容中的链接
            if not links:
                return url, []
            return url, links

        platform_results = []  # 存储平台搜索结果
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # 创建线程池执行器
            futures = [executor.submit(handle_url, url) for url in urls]  # 提交所有URL处理任务
            for future in as_completed(futures):  # 等待所有任务完成
                url, links = future.result()
                if links:
                    platform_results.append((url, links))  # 保存有链接的结果

        for url, links in platform_results:
            save_nodes(links, f"platform:{url}")  # 保存链接和对应的平台URL信息
    else:
        print("Skipping network mapping platforms.")  # 跳过网络映射平台搜索的提示信息
    platform_end = time.perf_counter()  # 记录平台搜索阶段结束时间
    print(f"Platform phase took {platform_end - platform_start:.2f} seconds.")  # 打印平台搜索阶段耗时

    # 显示中国代理状态
    if is_china_proxy_enabled():
        proxy_stats = get_china_proxy_stats()
        print(f"\n🇨🇳 中国代理状态: 可用 ({proxy_stats.get('working_count', 0)} 个代理)")
        print(f"代理将用于节点可用性测试，提高检测准确性")
    else:
        print(f"\n🇨🇳 中国代理状态: 未启用或无可用代理")
        print(f"将使用直接连接进行节点可用性测试")

    export_start = time.perf_counter()  # 记录导出阶段开始时间
    export_subscription()  # 导出最终的订阅列表
    export_end = time.perf_counter()  # 记录导出阶段结束时间
    print(f"Export phase took {export_end - export_start:.2f} seconds.")  # 打印导出阶段耗时

    total_end = time.perf_counter()  # 记录总结束时间
    print(f"Total elapsed time: {total_end - total_start:.2f} seconds.")  # 打印总耗时
    print("Done.")  # 完成处理的提示信息

if __name__ == "__main__":
    main()