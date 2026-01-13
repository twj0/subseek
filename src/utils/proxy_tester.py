"""
代理节点测试模块

该模块提供测试代理节点可用性的功能，特别针对中国代理进行优化
"""

import socket
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import json
from typing import List, Dict, Tuple, Optional, Any

class ProxyTester:
    """代理节点测试器"""
    
    def __init__(self, timeout: int = 10, max_workers: int = 20):
        self.timeout = timeout
        self.max_workers = max_workers
        self.test_urls = {
            'domestic': 'http://httpbin.org/ip',  # 国内可访问的测试URL
            'international': 'https://www.google.com',  # 国际访问测试
            'baidu': 'https://www.baidu.com',  # 百度测试
            'github': 'https://api.github.com'  # GitHub API测试
        }
        
    def test_proxy_connectivity(self, proxy_url: str) -> Tuple[bool, Dict[str, Any]]:
        """测试单个代理的连通性"""
        result = {
            'proxy': proxy_url,
            'connected': False,
            'response_time': None,
            'working_tests': [],
            'failed_tests': [],
            'error': None
        }
        
        try:
            # 解析代理URL
            parsed = urlparse(proxy_url)
            proxy_dict = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # 测试TCP连接
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            try:
                sock.connect((parsed.hostname, parsed.port))
                sock.close()
                result['connected'] = True
                result['response_time'] = round((time.time() - start_time) * 1000, 2)
            except Exception as e:
                result['error'] = f"TCP连接失败: {str(e)}"
                return False, result
            
            # 测试HTTP请求
            session = requests.Session()
            session.proxies.update(proxy_dict)
            session.timeout = self.timeout
            
            # 测试不同目标
            for test_name, test_url in self.test_urls.items():
                try:
                    response = session.get(test_url, timeout=self.timeout)
                    if response.status_code == 200:
                        result['working_tests'].append(test_name)
                    else:
                        result['failed_tests'].append(f"{test_name}: HTTP {response.status_code}")
                except Exception as e:
                    result['failed_tests'].append(f"{test_name}: {str(e)}")
            
            return True, result
            
        except Exception as e:
            result['error'] = str(e)
            return False, result
    
    def test_proxy_batch(self, proxy_urls: List[str]) -> List[Dict[str, Any]]:
        """批量测试代理"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有测试任务
            future_to_proxy = {
                executor.submit(self.test_proxy_connectivity, proxy): proxy 
                for proxy in proxy_urls
            }
            
            # 收集结果
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    success, result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'proxy': proxy,
                        'connected': False,
                        'error': f"测试异常: {str(e)}",
                        'working_tests': [],
                        'failed_tests': []
                    })
        
        return results
    
    def filter_working_proxies(self, test_results: List[Dict[str, Any]], 
                             min_working_tests: int = 1) -> List[str]:
        """筛选可用的代理"""
        working_proxies = []
        
        for result in test_results:
            if (result['connected'] and 
                len(result['working_tests']) >= min_working_tests and
                not result.get('error')):
                working_proxies.append(result['proxy'])
        
        return working_proxies
    
    def get_proxy_stats(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取代理测试统计信息"""
        total = len(test_results)
        connected = sum(1 for r in test_results if r['connected'])
        working = sum(1 for r in test_results if len(r['working_tests']) > 0)
        
        # 响应时间统计
        response_times = [r['response_time'] for r in test_results if r.get('response_time')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 测试成功率统计
        test_stats = {}
        for test_name in self.test_urls.keys():
            success_count = sum(1 for r in test_results if test_name in r['working_tests'])
            test_stats[test_name] = {
                'success': success_count,
                'rate': success_count / total if total > 0 else 0
            }
        
        return {
            'total_proxies': total,
            'connected_proxies': connected,
            'working_proxies': working,
            'connection_rate': connected / total if total > 0 else 0,
            'working_rate': working / total if total > 0 else 0,
            'avg_response_time': round(avg_response_time, 2),
            'test_stats': test_stats
        }

def test_china_proxies(proxy_urls: List[str], timeout: int = 10, 
                       max_workers: int = 20) -> Tuple[List[str], Dict[str, Any]]:
    """
    测试中国代理的主函数
    
    Args:
        proxy_urls: 代理URL列表
        timeout: 超时时间（秒）
        max_workers: 最大并发数
        
    Returns:
        Tuple[List[str], Dict]: 可用代理列表和统计信息
    """
    tester = ProxyTester(timeout=timeout, max_workers=max_workers)
    
    print(f"开始测试 {len(proxy_urls)} 个代理...")
    start_time = time.time()
    
    # 批量测试
    test_results = tester.test_proxy_batch(proxy_urls)
    
    # 筛选可用代理
    working_proxies = tester.filter_working_proxies(test_results, min_working_tests=1)
    
    # 获取统计信息
    stats = tester.get_proxy_stats(test_results)
    stats['test_duration'] = round(time.time() - start_time, 2)
    
    print(f"测试完成！")
    print(f"总代理数: {stats['total_proxies']}")
    print(f"连接成功: {stats['connected_proxies']}")
    print(f"可用代理: {stats['working_proxies']}")
    print(f"连接成功率: {stats['connection_rate']:.2%}")
    print(f"可用率: {stats['working_rate']:.2%}")
    print(f"平均响应时间: {stats['avg_response_time']}ms")
    print(f"测试耗时: {stats['test_duration']}秒")
    
    return working_proxies, stats
