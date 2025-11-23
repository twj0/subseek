import requests
import base64
import time
from config.settings import HUNTER_API_KEY, QUAKE_API_KEY

class HunterSearcher:
    def __init__(self, api_key=None):

        """
        初始化HunterSearcher类
        :param api_key: Hunter API的密钥，如果未提供则使用默认的HUNTER_API_KEY
        """
        self.api_key = api_key or HUNTER_API_KEY  # 设置API密钥，如果未提供则使用默认值
        self.base_url = "https://hunter.qianxin.com/openApi/search"  # 设置API的基础URL

    def search(self, query, page_size=20):
        if not self.api_key:
            return []

        query_b64 = base64.urlsafe_b64encode(query.encode("utf-8")).decode('utf-8')
        url = f"{self.base_url}?api-key={self.api_key}&search={query_b64}&page=1&page_size={page_size}&is_web=3"

        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()

            if data.get("code") != 200:
                print(f"Hunter Error: {data.get('message')}")
                return []

            return [item.get("url") for item in data.get("data", {}).get("arr", []) if item.get("url")]
        except Exception as e:
            print(f"Hunter Exception: {e}")
            return []

class QuakeSearcher:
    def __init__(self, api_key=None):

        """
        初始化QuakeSearcher类
        :param api_key: Quake API密钥，如果未提供则使用默认的QUAKE_API_KEY
        """
        self.api_key = api_key or QUAKE_API_KEY  # 设置API密钥
        self.base_url = "https://quake.360.net/api/v3/search/quake_service"  # 设置API基础URL

    def search(self, query, size=20):
        if not self.api_key:
            return []

        headers = {"X-QuakeToken": self.api_key, "Content-Type": "application/json"}
        payload = {"query": query, "start": 0, "size": size}

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
            data = resp.json()

            if data.get("code") != 0:
                print(f"Quake Error: {data.get('message')}")
                return []

            return [f"http://{item.get('ip')}:{item.get('port')}" for item in data.get("data", []) if item.get("ip")]
        except Exception as e:
            print(f"Quake Exception: {e}")
            return []

class DDGSearcher:
    def search(self, query, max_results=20):
        """
        使用DuckDuckGo搜索引擎进行搜索的方法
        :param query: 搜索关键词，用于指定搜索的内容
        :param max_results: 最大搜索结果数量，默认为20个结果
        :return: 搜索结果列表
        """
        try:
            # 导入DuckDuckGo搜索库
            from duckduckgo_search import DDGS
            # 初始化结果列表
            results = []
            # 创建DDGS上下文管理器
            with DDGS() as ddgs:
                # 遍历搜索结果，提取链接
                for r in ddgs.text(query, max_results=max_results):
                    # 将每个结果的链接添加到结果列表中
                    results.append(r['href'])
            # 返回搜索结果列表
            return results
        except ImportError:
            # 处理导入异常，提示用户安装必要的库
            print("DuckDuckGo search requires: pip install duckduckgo-search")
            return []
        except Exception as e:
            # 处理其他可能的异常，打印错误信息并返回空列表
            print(f"DDG Exception: {e}")
            return []

def search_all_platforms(keywords):
    urls = []
    hunter = HunterSearcher()
    quake = QuakeSearcher()
    ddg = DDGSearcher()

    for keyword in keywords:
        print(f"Searching for: {keyword}")
        hunter_query = f'web.body="{keyword}"'
        urls.extend(hunter.search(hunter_query))
        time.sleep(1)
        quake_query = f'response:"{keyword}"'
        urls.extend(quake.search(quake_query))
        time.sleep(1)
        ddg_query = f'"{keyword}" (vmess OR vless OR trojan OR ss)'
        urls.extend(ddg.search(ddg_query, max_results=10))
        time.sleep(2)

    return list(set(urls))  # 返回去重后的结果列表
