import base64
import json
import socket
from urllib.parse import urlparse


def _decode_base64(data):
    data = data.strip()
    padding = -len(data) % 4
    if padding:
        data += "=" * padding
    return base64.b64decode(data).decode("utf-8", errors="ignore")


def _extract_host_port(link):
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
    port = parsed.port
    if not host or not port:
        return None, None

    return host, int(port)


def is_node_alive(link, timeout=3.0):
    host, port = _extract_host_port(link)
    if not host or not port:
        return False

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False
