"""
代理协议转换器

将HTTP/SOCKS代理转换为标准代理协议格式（vmess、vless、trojan等）
"""

import json
import base64
import uuid
import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse

class ProtocolConverter:
    """代理协议转换器"""
    
    def __init__(self):
        # 默认配置
        self.default_config = {
            'vmess': {
                'v': '2',
                'ps': 'china-proxy',
                'add': '',  # 将从代理URL中提取
                'port': '',  # 将从代理URL中提取
                'id': '',  # 将生成UUID
                'aid': '0',
                'scy': 'auto',
                'net': 'ws',
                'type': 'none',
                'host': '',
                'path': '/',
                'tls': 'tls'
            },
            'vless': {
                'version': '',
                'ps': 'china-proxy',
                'add': '',
                'port': '',
                'id': '',
                'type': 'ws',
                'host': '',
                'path': '/',
                'tls': 'tls'
            },
            'trojan': {
                'password': '',
                'sni': '',
                'type': 'ws',
                'host': '',
                'path': '/',
                'allowInsecure': '1'
            }
        }
    
    def convert_http_to_vmess(self, proxy_url: str, custom_name: str = None) -> str:
        """将HTTP代理转换为vmess协议"""
        parsed = urlparse(proxy_url)
        if not parsed.hostname or not parsed.port:
            return None
        
        config = self.default_config['vmess'].copy()
        config['add'] = parsed.hostname
        config['port'] = str(parsed.port)
        config['id'] = str(uuid.uuid4())
        config['ps'] = custom_name or f"china-proxy-{parsed.hostname}"
        
        # 生成vmess链接
        vmess_json = json.dumps(config, separators=(',', ':'))
        vmess_b64 = base64.b64encode(vmess_json.encode()).decode()
        return f"vmess://{vmess_b64}"
    
    def convert_http_to_vless(self, proxy_url: str, custom_name: str = None) -> str:
        """将HTTP代理转换为vless协议"""
        parsed = urlparse(proxy_url)
        if not parsed.hostname or not parsed.port:
            return None
        
        config = self.default_config['vless'].copy()
        config['add'] = parsed.hostname
        config['port'] = str(parsed.port)
        config['id'] = str(uuid.uuid4())
        config['ps'] = custom_name or f"china-proxy-{parsed.hostname}"
        
        # 生成vless链接
        vless_url = f"vless://{config['id']}@{config['add']}:{config['port']}?type={config['type']}&path={config['path']}&host={config['host']}&tls={config['tls']}#{config['ps']}"
        return vless_url
    
    def convert_http_to_trojan(self, proxy_url: str, custom_name: str = None) -> str:
        """将HTTP代理转换为trojan协议"""
        parsed = urlparse(proxy_url)
        if not parsed.hostname or not parsed.port:
            return None
        
        config = self.default_config['trojan'].copy()
        password = str(uuid.uuid4())
        config['sni'] = parsed.hostname
        
        # 生成trojan链接
        trojan_url = f"trojan://{password}@{parsed.hostname}:{parsed.port}?type={config['type']}&path={config['path']}&host={config['host']}&sni={config['sni']}#{custom_name or f'china-proxy-{parsed.hostname}'}"
        return trojan_url
    
    def convert_http_to_ss(self, proxy_url: str, custom_name: str = None) -> str:
        """将HTTP代理转换为shadowsocks协议"""
        parsed = urlparse(proxy_url)
        if not parsed.hostname or not parsed.port:
            return None
        
        # 生成随机密码和方法
        password = str(uuid.uuid4()).replace('-', '')[:16]
        method = 'aes-256-gcm'
        
        # 组合用户信息
        userinfo = f"{method}:{password}"
        userinfo_b64 = base64.b64encode(userinfo.encode()).decode()
        
        # 生成ss链接
        ss_url = f"ss://{userinfo_b64}@{parsed.hostname}:{parsed.port}#{custom_name or f'china-proxy-{parsed.hostname}'}"
        return ss_url
    
    def convert_proxy_list(self, proxy_urls: List[str], 
                         target_protocols: List[str] = None) -> List[str]:
        """
        批量转换代理协议
        
        Args:
            proxy_urls: HTTP代理URL列表
            target_protocols: 目标协议列表，默认转换为所有协议
            
        Returns:
            转换后的代理链接列表
        """
        if target_protocols is None:
            target_protocols = ['vmess', 'vless', 'trojan', 'ss']
        
        converted_links = []
        
        for i, proxy_url in enumerate(proxy_urls):
            parsed = urlparse(proxy_url)
            if not parsed.hostname or not parsed.port:
                continue
            
            custom_name = f"china-proxy-{parsed.hostname}-{i+1}"
            
            if 'vmess' in target_protocols:
                vmess_link = self.convert_http_to_vmess(proxy_url, custom_name + "-vmess")
                if vmess_link:
                    converted_links.append(vmess_link)
            
            if 'vless' in target_protocols:
                vless_link = self.convert_http_to_vless(proxy_url, custom_name + "-vless")
                if vless_link:
                    converted_links.append(vless_link)
            
            if 'trojan' in target_protocols:
                trojan_link = self.convert_http_to_trojan(proxy_url, custom_name + "-trojan")
                if trojan_link:
                    converted_links.append(trojan_link)
            
            if 'ss' in target_protocols:
                ss_link = self.convert_http_to_ss(proxy_url, custom_name + "-ss")
                if ss_link:
                    converted_links.append(ss_link)
        
        return converted_links
    
    def create_balancer_config(self, proxy_urls: List[str], 
                             protocol: str = 'vmess') -> Dict[str, Any]:
        """
        创建负载均衡配置
        
        Args:
            proxy_urls: 代理URL列表
            protocol: 目标协议
            
        Returns:
            负载均衡配置字典
        """
        converted_links = self.convert_proxy_list(proxy_urls, [protocol])
        
        balancer_config = {
            'type': 'selector',
            'name': 'China-Proxies-Balancer',
            'proxies': []
        }
        
        for link in converted_links:
            if protocol == 'vmess':
                # 解析vmess链接
                try:
                    vmess_data = json.loads(base64.b64decode(link.split('://')[1]).decode())
                    balancer_config['proxies'].append({
                        'name': vmess_data['ps'],
                        'type': 'vmess',
                        'server': vmess_data['add'],
                        'port': int(vmess_data['port']),
                        'uuid': vmess_data['id'],
                        'alterId': int(vmess_data['aid']),
                        'cipher': vmess_data['scy'],
                        'tls': vmess_data['tls'] == 'tls',
                        'skip-cert-verify': True,
                        'network': vmess_data['net'],
                        'ws-opts': {
                            'path': vmess_data['path'],
                            'headers': {
                                'Host': vmess_data['host']
                            }
                        }
                    })
                except:
                    continue
        
        return balancer_config

def convert_china_proxies(proxy_urls: List[str], 
                         target_protocols: List[str] = None) -> List[str]:
    """
    转换中国代理的主函数
    
    Args:
        proxy_urls: 中国代理URL列表
        target_protocols: 目标协议列表
        
    Returns:
        转换后的代理链接列表
    """
    converter = ProtocolConverter()
    return converter.convert_proxy_list(proxy_urls, target_protocols)
