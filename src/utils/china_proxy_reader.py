"""
中国代理读取器

从data文件夹读取中国代理配置，供主程序使用
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import requests

class ChinaProxyReader:
    """中国代理读取器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.china_proxy_dir = self.data_dir / "china_proxies"
        self.config_file = self.china_proxy_dir / "china_proxy_config.json"
        self.working_proxies_file = self.china_proxy_dir / "working_china_proxies.txt"
        self.converted_proxies_file = self.china_proxy_dir / "converted_china_proxies.txt"
    
    def load_china_proxy_config(self) -> Optional[Dict[str, Any]]:
        """加载中国代理配置文件"""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查配置文件结构
            if 'working_proxies' in config and 'stats' in config:
                return config
            elif 'proxies' in config and 'stats' in config:
                # 兼容旧格式
                return {
                    'working_proxies': config.get('proxies', []),
                    'converted_proxies': config.get('stats', {}).get('converted_proxies', []),
                    'stats': config.get('stats', {}),
                    'timestamp': config.get('timestamp')
                }
            else:
                print("配置文件格式不正确")
                return None
        except Exception as e:
            print(f"加载中国代理配置失败: {e}")
            return None
    
    def load_working_proxies(self) -> List[str]:
        """加载可用的中国代理列表"""
        if not self.working_proxies_file.exists():
            return []
        
        try:
            with open(self.working_proxies_file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except Exception as e:
            print(f"加载可用代理失败: {e}")
            return []
    
    def load_converted_proxies(self) -> List[str]:
        """加载转换后的代理列表"""
        if not self.converted_proxies_file.exists():
            return []
        
        try:
            with open(self.converted_proxies_file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except Exception as e:
            print(f"加载转换代理失败: {e}")
            return []
    
    def get_random_proxy(self, proxy_type: str = "http") -> Optional[str]:
        """获取随机代理"""
        if proxy_type == "http":
            proxies = self.load_working_proxies()
        elif proxy_type == "converted":
            proxies = self.load_converted_proxies()
        else:
            return None
        
        if not proxies:
            return None
        
        return random.choice(proxies)
    
    def get_proxy_for_testing(self) -> Optional[Dict[str, str]]:
        """获取用于测试的代理配置"""
        config = self.load_china_proxy_config()
        if not config:
            return None
        
        working_proxies = config.get("working_proxies", [])
        if not working_proxies:
            return None
        
        # 选择一个随机的可用代理
        proxy_url = random.choice(working_proxies)
        parsed = urlparse(proxy_url)
        
        if not parsed.hostname or not parsed.port:
            return None
        
        return {
            "http": proxy_url,
            "https": proxy_url,
            "host": parsed.hostname,
            "port": str(parsed.port)
        }
    
    def test_proxy_connectivity(self, proxy_config: Dict[str, str], 
                              test_url: str = "http://httpbin.org/ip",
                              timeout: int = 10) -> bool:
        """测试代理连通性"""
        try:
            response = requests.get(
                test_url,
                proxies=proxy_config,
                timeout=timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"代理测试失败: {e}")
            return False
    
    def get_working_proxy_for_validation(self, max_attempts: int = 3) -> Optional[Dict[str, str]]:
        """获取一个确实可用的代理用于节点验证"""
        config = self.load_china_proxy_config()
        if not config:
            return None
        
        working_proxies = config.get("working_proxies", [])
        if not working_proxies:
            return None
        
        # 随机尝试几个代理
        attempts = 0
        while attempts < max_attempts and attempts < len(working_proxies):
            proxy_url = random.choice(working_proxies)
            parsed = urlparse(proxy_url)
            
            if parsed.hostname and parsed.port:
                proxy_config = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                if self.test_proxy_connectivity(proxy_config):
                    print(f"找到可用的中国代理: {proxy_url}")
                    return proxy_config
            
            attempts += 1
        
        print("未找到可用的中国代理")
        return None
    
    def is_china_proxy_available(self) -> bool:
        """检查是否有可用的中国代理"""
        config = self.load_china_proxy_config()
        if not config:
            return False
        
        working_proxies = config.get("working_proxies", [])
        return len(working_proxies) > 0
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        config = self.load_china_proxy_config()
        if not config:
            return {
                "available": False,
                "message": "没有找到中国代理配置文件"
            }
        
        stats = config.get("stats", {})
        working_proxies = config.get("working_proxies", [])
        converted_proxies = config.get("converted_proxies", [])
        
        return {
            "available": True,
            "timestamp": config.get("timestamp"),
            "working_count": len(working_proxies),
            "converted_count": len(converted_proxies),
            "collection_stats": stats.get("collection", {}),
            "conversion_stats": stats.get("conversion", {}),
            "test_stats": stats.get("test_stats", {})
        }

# 全局实例
_china_proxy_reader = None

def get_china_proxy_reader() -> ChinaProxyReader:
    """获取中国代理读取器实例"""
    global _china_proxy_reader
    if _china_proxy_reader is None:
        _china_proxy_reader = ChinaProxyReader()
    return _china_proxy_reader

def get_china_proxy_for_validation() -> Optional[Dict[str, str]]:
    """获取用于验证的中国代理"""
    reader = get_china_proxy_reader()
    return reader.get_working_proxy_for_validation()

def is_china_proxy_enabled() -> bool:
    """检查是否启用中国代理"""
    # 检查环境变量
    if os.environ.get("USE_CHINA_PROXY", "1") != "1":
        return False
    
    # 检查是否有可用的代理
    reader = get_china_proxy_reader()
    return reader.is_china_proxy_available()

def get_china_proxy_stats() -> Dict[str, Any]:
    """获取中国代理统计信息"""
    reader = get_china_proxy_reader()
    return reader.get_proxy_stats()
