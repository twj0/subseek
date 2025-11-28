"""
主程序入口模块
负责协调整个代理节点收集和处理流程
"""

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
        if not is_node_alive(link):
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

    print("Start collecting...")  # 开始收集的提示信息

    # GitHub仓库处理流程
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
        print("Skipping GitHub repository collection.")  # 跳过GitHub仓库收集的提示信息

    # 网络映射平台搜索流程
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
        print("Skipping network mapping platforms.")  # 跳过网络映射平台搜索的提示信息

    export_subscription()  # 导出最终的订阅列表
    print("Done.")  # 完成处理的提示信息

if __name__ == "__main__":
    main()