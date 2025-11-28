"""
GitHub仓库收集器模块

该模块提供了从GitHub搜索和获取订阅相关仓库文件内容的功能。
"""

import requests
import time
from config.settings import GITHUB_TOKEN, GITHUB_KEYWORDS

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json"
}

def get_github_repos():
    """
    根据配置的关键字搜索GitHub仓库
    
    通过GitHub API搜索与配置关键字相关的仓库，并返回仓库全名列表。
    搜索按照更新时间降序排列，每页最多50个结果。
    
    Returns:
        list: 包含仓库全名的去重列表，格式为 'owner/repo_name'
    """
    repos = []
    for keyword in GITHUB_KEYWORDS:
        # 搜索仓库的语法
        # q: 搜索关键词
        # q=keyword: 搜索关键词
        # sort: 按照更新时间排序
        # order: 降序
        # per_page: 每页显示的仓库数量
        url = f"https://api.github.com/search/repositories?q={keyword}&sort=updated&order=desc&per_page=30"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                #print(items)
                for item in items:
                    repos.append(item['full_name'])
            else:
                print(f"Error searching {keyword}: {resp.status_code}")
        except Exception as e:
            print(f"Exception searching {keyword}: {e}")
        time.sleep(2)
    return list(set(repos))

def fetch_file_content(repo_full_name):
    """
    获取指定仓库中可能包含订阅信息的文件内容
    
    该函数会尝试在仓库的main和master分支中查找常见订阅文件，
    并根据文件扩展名和关键词进行筛选。
    
    Args:
        repo_full_name (str): 仓库的全名，格式为 'owner/repo_name'
        
    Returns:
        list: 包含文件内容的字符串列表
    """
    common_files = ["subscribe/v2ray.txt", "v2ray.txt", "clash.yaml", "config.yaml", "sub.txt", "nodes.txt"]
    exts = (".txt", ".yaml", ".yml", ".json", ".conf")
    keywords = ("v2ray", "clash", "sub", "nodes", "proxy")
    contents = []

    for branch in ["main", "master"]:
        tree_url = f"https://api.github.com/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
        try:
            resp = requests.get(tree_url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            tree = data.get("tree", [])
            # 仓库内的文件路径
            blob_paths = [item.get("path") for item in tree if item.get("type") == "blob" and item.get("path")]
            candidate_paths = set()
            # 先找一些常见的文件名，如果找到了就直接返回
            for path in blob_paths:
                if path in common_files:
                    candidate_paths.add(path)
            # 再进行模糊匹配，找到包含关键词的文件
            for path in blob_paths:
                lower = path.lower()
                if not lower.endswith(exts):
                    continue
                if not any(k in lower for k in keywords):
                    continue
                candidate_paths.add(path)
                if len(candidate_paths) >= 30:
                    break

            base_url = f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/"
            for path in candidate_paths:
                try:
                    resp_file = requests.get(base_url + path, timeout=5)
                    if resp_file.status_code == 200:
                        contents.append(resp_file.text)
                except:
                    pass
        except Exception as e:
            print(f"Exception fetching tree for {repo_full_name}@{branch}: {e}")
    return contents
