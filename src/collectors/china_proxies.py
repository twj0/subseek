"""
中国代理节点收集器模块

该模块提供从各种中国代理源收集代理节点的功能
"""

import requests
import re
import time
import json
from typing import List, Dict, Any
from urllib.parse import urlparse
import base64

class ChinaProxyCollector:
    """中国代理节点收集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 中国代理源配置
        self.proxy_sources = {
            'github_repos': [
                'fate0/proxylist',
                'clowmound/ProxyList', 
                'TheSpeedX/PROXY-List',
                'Python3WebSpider/ProxyPool',
                'ouyangc/ProxyPoolNew'
            ],
            'api_endpoints': [
                # 'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=CN',
                'https://proxylist.geonode.com/api/proxy-list?limit=50&country=CN',
                'https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list'
            ],
            'free_proxy_sites': [
                'https://free-proxy-list.net/',
                'https://www.us-proxy.org/',
                'https://www.socks-proxy.net/'
            ]
        }
    
    def collect_from_github(self) -> List[str]:
        """从GitHub仓库收集中国代理"""
        proxies = []
        
        for repo in self.proxy_sources['github_repos']:
            try:
                # 获取仓库的代理文件
                raw_url = f"https://raw.githubusercontent.com/{repo}/master/proxy.txt"
                response = self.session.get(raw_url, timeout=10)
                
                if response.status_code == 200:
                    proxy_text = response.text
                    # 解析代理格式
                    proxy_list = self._parse_proxy_list(proxy_text)
                    # 筛选中国IP
                    china_proxies = self._filter_china_proxies(proxy_list)
                    proxies.extend(china_proxies)
                    
                time.sleep(1)  # 避免API限制
                
            except Exception as e:
                print(f"Error collecting from {repo}: {e}")
                
        return proxies
    
    def collect_from_apis(self) -> List[str]:
        """从API端点收集代理"""
        proxies = []
        
        for api_url in self.proxy_sources['api_endpoints']:
            try:
                response = self.session.get(api_url, timeout=15)
                
                if response.status_code == 200:
                    if 'json' in response.headers.get('content-type', ''):
                        # JSON格式响应
                        data = response.json()
                        proxy_list = self._parse_json_proxies(data)
                    else:
                        # 文本格式响应
                        proxy_list = self._parse_proxy_list(response.text)
                    
                    # 筛选中国代理
                    china_proxies = self._filter_china_proxies(proxy_list)
                    proxies.extend(china_proxies)
                    
                time.sleep(2)  # 避免API限制
                
            except Exception as e:
                print(f"Error collecting from API {api_url}: {e}")
                
        return proxies
    
    def _parse_proxy_list(self, text: str) -> List[Dict[str, Any]]:
        """解析代理列表文本"""
        proxies = []
        
        # 支持多种格式
        patterns = [
            # IP:PORT格式
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)',
            # 带协议的格式
            r'(http|https|socks4|socks5)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)',
            # JSON格式中的IP:PORT
            r'"ip":\s*"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})".*?"port":\s*"?(\d+)"?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) == 2:
                    ip, port = match
                    protocol = 'http'
                elif len(match) == 3:
                    protocol, ip, port = match
                else:
                    continue
                    
                proxies.append({
                    'ip': ip,
                    'port': int(port),
                    'protocol': protocol.lower(),
                    'country': 'unknown'
                })
        
        return proxies
    
    def _parse_json_proxies(self, data: Any) -> List[Dict[str, Any]]:
        """解析JSON格式的代理数据"""
        proxies = []
        
        try:
            if isinstance(data, dict):
                if 'data' in data:
                    proxy_data = data['data']
                elif 'proxies' in data:
                    proxy_data = data['proxies']
                else:
                    proxy_data = [data]
            elif isinstance(data, list):
                proxy_data = data
            else:
                return proxies
            
            for item in proxy_data:
                if isinstance(item, dict):
                    ip = item.get('ip') or item.get('host') or item.get('address')
                    port = item.get('port')
                    protocol = item.get('protocol', 'http')
                    country = item.get('country', 'unknown')
                    
                    if ip and port:
                        proxies.append({
                            'ip': ip,
                            'port': int(port),
                            'protocol': protocol.lower(),
                            'country': country.lower()
                        })
                        
        except Exception as e:
            print(f"Error parsing JSON proxies: {e}")
            
        return proxies
    
    def _filter_china_proxies(self, proxies: List[Dict[str, Any]]) -> List[str]:
        """筛选中国代理并转换为标准格式"""
        china_proxies = []
        china_indicators = ['cn', 'china', 'chinese', 'hong kong', 'hk', 'taiwan', 'tw']
        
        # 中国IP段（简化版本）
        china_ip_ranges = [
            '1.0.1.0', '1.0.2.0', '1.0.8.0', '1.0.32.0',
            '14.0.0.0', '27.0.0.0', '36.0.0.0', '39.0.0.0',
            '42.0.0.0', '49.0.0.0', '58.0.0.0', '59.0.0.0',
            '60.0.0.0', '61.0.0.0', '101.0.0.0', '103.0.0.0',
            '106.0.0.0', '110.0.0.0', '111.0.0.0', '112.0.0.0',
            '113.0.0.0', '114.0.0.0', '115.0.0.0', '116.0.0.0',
            '117.0.0.0', '118.0.0.0', '119.0.0.0', '120.0.0.0',
            '121.0.0.0', '122.0.0.0', '123.0.0.0', '124.0.0.0',
            '125.0.0.0', '171.0.0.0', '172.0.0.0', '175.0.0.0',
            '180.0.0.0', '182.0.0.0', '183.0.0.0', '202.0.0.0',
            '203.0.0.0', '210.0.0.0', '211.0.0.0', '218.0.0.0',
            '219.0.0.0', '220.0.0.0', '221.0.0.0', '222.0.0.0',
            '223.0.0.0'
        ]
        
        def is_china_ip(ip: str) -> bool:
            """简单判断是否为中国IP"""
            for prefix in china_ip_ranges:
                if ip.startswith(prefix):
                    return True
            return False
        
        for proxy in proxies:
            # 通过国家代码筛选
            if proxy['country'] and any(indicator in proxy['country'].lower() for indicator in china_indicators):
                china_proxies.append(f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}")
            # 通过IP段筛选
            elif is_china_ip(proxy['ip']):
                china_proxies.append(f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}")
        
        return china_proxies
    
    def collect_all_china_proxies(self) -> List[str]:
        """收集所有中国代理"""
        all_proxies = []
        
        print("开始从GitHub收集中国代理...")
        github_proxies = self.collect_from_github()
        all_proxies.extend(github_proxies)
        print(f"从GitHub收集到 {len(github_proxies)} 个代理")
        
        print("开始从API收集中国代理...")
        api_proxies = self.collect_from_apis()
        all_proxies.extend(api_proxies)
        print(f"从API收集到 {len(api_proxies)} 个代理")
        
        # 去重
        unique_proxies = list(set(all_proxies))
        print(f"总共收集到 {len(unique_proxies)} 个唯一的中国代理")
        
        return unique_proxies

def get_china_proxy_links():
    """获取中国代理链接的主函数"""
    collector = ChinaProxyCollector()
    return collector.collect_all_china_proxies()
