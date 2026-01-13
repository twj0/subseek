import base64
import json
import socket
import requests
from urllib.parse import urlparse


def _decode_base64(data):
    """
    解码Base64编码的数据
    
    Args:
        data (str): Base64编码的字符串
        
    Returns:
        str: 解码后的UTF-8字符串，解码失败时忽略错误
    """
    data = data.strip()
    padding = -len(data) % 4
    if padding:
        data += "=" * padding
    return base64.b64decode(data).decode("utf-8", errors="ignore")


def _extract_host_port(link):
    """
    从链接中提取主机名和端口号
    
    Args:
        link (str): 包含服务器信息的链接字符串，支持vmess协议或标准URL格式
        
    Returns:
        tuple: (host, port) 主机名和端口号的元组，解析失败时返回(None, None)
    """
    if not isinstance(link, str):
        return None, None

    link = link.strip()

    if link.startswith("vmess://"):
        b64 = link[8:]
        try:
            decoded = _decode_base64(b64)
            obj = json.loads(decoded)
            host = obj.get("add") or obj.get("host")
            port_value = obj.get("port")
            if not host or not port_value:
                return None, None
            try:
                port = int(port_value)
            except (TypeError, ValueError):
                return None, None
            return host, port
        except Exception:
            return None, None

    try:
        parsed = urlparse(link)
    except ValueError:
        return None, None
    host = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        return None, None
    if not host or not port:
        return None, None

    return host, int(port)


def is_node_alive(link, timeout=3.0):
    """
    检查节点是否存活
    
    Args:
        link (str): 包含服务器信息的链接字符串
        timeout (float): 连接超时时间（秒），默认为3.0秒
        
    Returns:
        bool: 节点存活返回True，否则返回False
    """
    host, port = _extract_host_port(link)
    if not host or not port:
        return False

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def is_node_alive_with_china_proxy(link, timeout=10.0):
    """
    使用中国代理检查节点是否存活
    
    Args:
        link (str): 包含服务器信息的链接字符串
        timeout (float): 连接超时时间（秒），默认为10.0秒
        
    Returns:
        bool: 节点存活返回True，否则返回False
    """
    # 首先尝试直接连接
    if is_node_alive(link, timeout=3.0):
        return True
    
    # 如果直接连接失败，尝试使用中国代理
    try:
        from .china_proxy_reader import get_china_proxy_for_validation
        
        proxy_config = get_china_proxy_for_validation()
        if not proxy_config:
            # 没有可用的中国代理，返回直接连接的结果
            return False
        
        host, port = _extract_host_port(link)
        if not host or not port:
            return False
        
        # 使用代理进行HTTP CONNECT测试
        proxies = {
            'http': proxy_config.get('http'),
            'https': proxy_config.get('https')
        }
        
        # 尝试通过代理访问目标
        test_url = f"http://{host}:{port}"
        try:
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                allow_redirects=False
            )
            # 如果返回任何响应，说明代理可以连接到目标
            return True
        except requests.exceptions.ConnectTimeout:
            # 连接超时，但可能代理正在工作
            return False
        except requests.exceptions.ProxyError:
            # 代理错误，尝试下一个代理
            return False
        except Exception:
            # 其他错误，认为不可用
            return False
            
    except ImportError:
        # 中国代理读取器不可用，使用直接连接
        return is_node_alive(link, timeout)
    except Exception:
        return False