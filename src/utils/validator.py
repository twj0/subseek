import base64
import json
import socket
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

    parsed = urlparse(link)
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