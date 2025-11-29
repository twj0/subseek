import os
from itertools import product

##############################################################################################
# GitHub settings
##############################################################################################
# GitHub访问令牌，从环境变量GH_TOKEN获取，默认为空字符串
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")

# GitHub搜索中使用的完全由用户自定义的术语
# 可通过环境变量 GH_SEARCH_TERMS 覆盖，多个关键词用逗号分隔
# 例如: GH_SEARCH_TERMS="free v2ray,free proxy"
_DEFAULT_GITHUB_SEARCH_TERMS = ["free v2ray", "free proxy"]
_env_search_terms = os.environ.get("GH_SEARCH_TERMS", "")
GITHUB_SEARCH_TERMS = (
    [term.strip() for term in _env_search_terms.split(",") if term.strip()]
    if _env_search_terms
    else _DEFAULT_GITHUB_SEARCH_TERMS
)

# GitHub搜索关键词的最大数量限制，如果你想快点搜索的话可以调小这个值
# 可通过环境变量 MAX_GH_KW 覆盖
_DEFAULT_MAX_GITHUB_KEYWORDS = 2
MAX_GITHUB_KEYWORDS = int(os.environ.get("MAX_GH_KW", _DEFAULT_MAX_GITHUB_KEYWORDS))


def _build_github_keywords():
    """
    构建GitHub搜索关键词列表
    
    完全由用户在 GITHUB_SEARCH_TERMS 中自定义搜索关键词，
    按顺序选取并裁剪到 MAX_GITHUB_KEYWORDS 个。
    
    Returns:
        list: 包含生成的关键词字符串列表，长度不超过MAX_GITHUB_KEYWORDS
    """
    return GITHUB_SEARCH_TERMS[:MAX_GITHUB_KEYWORDS]


GITHUB_KEYWORDS = _build_github_keywords()

##############################################################################################
# Platform settings
##############################################################################################
# Platform API keys
# Hunter.io平台API密钥，从环境变量HUNTER_API_KEY获取，默认为空字符串
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")
# Quake平台API密钥，从环境变量QUAKE_API_KEY获取，默认为空字符串
QUAKE_API_KEY = os.environ.get("QUAKE_API_KEY", "")

# Platform search keywords
# 平台搜索中使用的协议相关术语
PLATFORM_PROTOCOL_TERMS = [
    "v2ray",
    "vmess",
    "vless",
    "trojan",
    "hy2",
    "clash",
    "ss",
]

# 平台搜索中使用的上下文相关术语（精简为高价值项）
PLATFORM_CONTEXT_TERMS = [
    "subscribe",
    "free",
    "nodes",
    "config",
    "proxy",
    "proxies",
    "node list",
    "proxy list"
]

# 平台搜索中使用的独立术语（精简版）
PLATFORM_SINGLE_TERMS = [
    "shadowsocks",
    "wireguard",
]

# 平台搜索关键词的最大数量限制
# 可通过环境变量 MAX_PLATFORM_KW 覆盖，GitHub Action 建议设为 15-25
_DEFAULT_MAX_PLATFORM_KEYWORDS = 25
MAX_PLATFORM_KEYWORDS = int(os.environ.get("MAX_PLATFORM_KW", _DEFAULT_MAX_PLATFORM_KEYWORDS))


def _build_platform_keywords():
    """
    构建平台搜索关键词列表
    
    首先添加协议术语和单术语，然后通过组合协议术语与上下文术语生成复合关键词，
    避免重复并限制总数。
    
    Returns:
        list: 包含生成的关键词字符串列表，长度不超过MAX_PLATFORM_KEYWORDS
    """
    keywords = []
    seen = set()

    # 1. 添加单术语和协议术语
    for term in PLATFORM_PROTOCOL_TERMS + PLATFORM_SINGLE_TERMS:
        if term not in seen:
            keywords.append(term)
            seen.add(term)

    # 2. 生成并添加组合术语
    # 使用 product 高效生成笛卡尔积
    generated_keywords = (f"{proto} {ctx}" for proto, ctx in product(PLATFORM_PROTOCOL_TERMS, PLATFORM_CONTEXT_TERMS))

    for kw in generated_keywords:
        if len(keywords) >= MAX_PLATFORM_KEYWORDS:
            break
        if kw not in seen:
            keywords.append(kw)
            seen.add(kw)
            
    return keywords[:MAX_PLATFORM_KEYWORDS]


PLATFORM_KEYWORDS = _build_platform_keywords()

# Database
# 数据库路径，从环境变量DB_PATH获取，默认为'data/nodes.db'
DB_PATH = os.environ.get('DB_PATH', 'data/nodes.db')

# Export paths
# 导出文件路径
EXPORT_PATH = os.environ.get("EXPORT_PATH", "data/sub.txt")
# Base64编码导出文件路径
EXPORT_BASE64_PATH = os.environ.get("EXPORT_BASE64_PATH", "data/sub_base64.txt")
