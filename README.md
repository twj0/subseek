*神秘地址*
```
https://raw.githubusercontent.com/twj0/subseek/refs/heads/master/data/sub_github.txt
```

```
https://raw.githubusercontent.com/twj0/subseek/refs/heads/master/data/sub_platform.txt
```

---

# SubSeek 

一个用于自动从 GitHub 免费节点仓库和网络映射平台中收集代理节点，并导出为订阅文件的轻量级工具。

> 仅供技术研究使用，请确保你的使用符合当地法律法规以及 GitHub 的使用条款。

## 功能特点

- 从 GitHub 搜索和收集代理节点
- 从网络映射平台（Hunter、Quake、DuckDuckGo）搜索代理节点
- 自动验证节点可用性
- 支持多种代理协议（vmess、vless、trojan、ss等）
- 导出为标准订阅格式和Base64编码格式
- 按来源分类导出（GitHub来源和平台来源）

## 工作原理

SubSeek 的工作流程分为以下几个主要步骤：

1. **GitHub仓库搜索**：通过GitHub API搜索包含代理节点配置的公开仓库
2. **平台搜索**：使用网络映射平台API和搜索引擎查找公开的代理节点
3. **内容解析**：从获取的文本内容中提取代理节点链接
4. **节点验证**：测试节点的连通性，只保存可用的节点
5. **导出订阅**：将收集的节点导出为订阅文件

---

## 安装与使用

### 一：GitHub Actions 自动运行
> 注意GitHub Actions 最大运行时长为6个小时

> 项目已配置 GitHub Actions 每日自动运行。


**配置步骤：**

#### 1. 配置 Secrets（必需）
进入仓库 **Settings > Secrets and variables > Actions > Secrets**，点击 **New repository secret** 添加：

| Secret 名称 | 说明 | 必需 |
|------------|------|------|
| `GH_TOKEN` | GitHub 个人访问令牌 | ✅ 是 |
| `HUNTER_API_KEY` | Hunter 平台 API 密钥 | ❌ 否 |
| `QUAKE_API_KEY` | Quake 平台 API 密钥 | ❌ 否 |

#### 2. 配置 Variables（可选）
进入仓库 **Settings > Secrets and variables > Actions > Variables**，点击 **New repository variable** 添加：

| Variable 名称 | 默认值 | 说明 | 建议值 |
|--------------|--------|------|--------|
| `MAX_WORKERS` | 8 | 并发线程数 | 4-16 |
| `GH_SEARCH_TERMS` | free v2ray,free proxy | GitHub 搜索关键词（逗号分隔） | 自定义 |
| `MAX_GH_KW` | 2 | 使用的关键词数量 | 2-5 |
| `GH_MAX_REPOS` | 100 | 搜索仓库总数量 | 50-200 |
| `GH_PER_PAGE` | 30 | 每页返回仓库数量 | 30-100 |
| `RUN_GITHUB` | 1 | 是否运行 GitHub 收集 | 0 或 1 |
| `RUN_PLATFORMS` | 0 | 是否运行平台搜索 | 0 或 1 |

**注意**：不配置 Variables 时，将使用默认值。

### 使用Docker（本地运行）

#### 使用预构建镜像（推荐）

项目在GitHub上自动构建Docker镜像，可直接拉取使用：

```bash
# 拉取最新镜像
docker pull ghcr.io/twj0/subseek:latest

# 运行容器（需要配置环境变量）
docker run --rm \
  -e GH_TOKEN="your_github_token" \
  -e HUNTER_API_KEY="your_hunter_key" \
  -e QUAKE_API_KEY="your_quake_key" \
  -v $(pwd)/data:/app/data \
  ghcr.io/twj0/subseek:latest
```

#### 本地构建运行

1. 复制环境变量配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入必要的API密钥：
```bash
nano .env
```

3. 使用Docker Compose启动：
```bash
docker-compose up -d
```

**注意**：Docker镜像在每次代码推送时自动构建并发布到GitHub Container Registry (ghcr.io)。

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
export GH_TOKEN="your_github_token"
export HUNTER_API_KEY="your_hunter_api_key"
export QUAKE_API_KEY="your_quake_api_key"
```

3. 运行程序：
```bash
python -m src.main
```

## 环境变量详解

### GitHub相关配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `GH_TOKEN` | 推荐 | 无 | GitHub个人访问令牌，用于提高API请求限制（强烈推荐配置） |
| `GH_SEARCH_TERMS` | 否 | "free v2ray,free proxy" | GitHub搜索关键词，多个用逗号分隔 |
| `MAX_GH_KW` | 否 | 2 | GitHub搜索关键词最大使用数量（建议：2-5） |
| `GH_MAX_REPOS` | 否 | 100 | GitHub搜索仓库总数量限制（建议：50-200，仅在GitHub Actions中使用） |
| `GH_PER_PAGE` | 否 | 30 | GitHub搜索每页返回的仓库数量（最大100，仅在GitHub Actions中使用） |

### 平台搜索相关配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `HUNTER_API_KEY` | 否 | 无 | Hunter平台API密钥（鹊桥平台：hunter.qianxin.com） |
| `QUAKE_API_KEY` | 否 | 无 | Quake平台API密钥（360 Quake平台：quake.360.net） |
| `MAX_PLATFORM_KW` | 否 | 25 | 平台搜索关键词最大数量（建议：15-30） |

### 运行控制

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `RUN_GITHUB` | 否 | 1 | 是否运行GitHub收集模块（1启用，0禁用） |
| `RUN_PLATFORMS` | 否 | 1 | 是否运行平台搜索模块（1启用，0禁用） |
| `MAX_WORKERS` | 否 | 8 | 并发处理的最大线程数（建议：4-16） |

### 导出配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `DB_PATH` | 否 | data/nodes.db | SQLite数据库文件路径 |
| `EXPORT_PATH` | 否 | data/sub.txt | 合并订阅文件导出路径 |
| `EXPORT_BASE64_PATH` | 否 | data/sub_base64.txt | Base64编码订阅文件导出路径 |

## 搜索原理详解

### GitHub搜索原理

1. **关键词构建**：系统使用预定义的协议术语搜索关键词("free v2ray,free proxy")
2. **API搜索**：通过GitHub API搜索仓库，按更新时间排序获取最新结果
3. **文件筛选**：在仓库中查找常见的订阅文件名（如"v2ray.txt"、"clash.yaml"）或包含关键词的文件
4. **内容获取**：获取筛选出的文件内容，准备进行解析

### 平台搜索原理

1. **多平台搜索**：同时使用Hunter、Quake和DuckDuckGo三个平台进行搜索
   - **Hunter**：使用`web.body="{关键词}"`语法搜索网页内容
   - **Quake**：使用`response:"{关键词}"`语法搜索响应内容
   - **DuckDuckGo**：使用`"{关键词}" (vmess OR vless OR trojan OR ss)`语法进行常规搜索

2. **结果合并去重**：将各平台返回的URL合并并去重，避免重复处理

### 节点解析与验证

1. **内容解析**：
   - 尝试Base64解码内容
   - 使用正则表达式匹配各种代理协议链接
   - 支持的协议包括：vmess、vless、ss、trojan、ssr、socks5、hysteria、hy2、tuic、wireguard

2. **节点验证**：
   - 从链接中提取主机和端口信息
   - 建立TCP连接测试节点可用性
   - 只保存可用的节点到数据库

## 输出文件说明

程序运行后会生成以下文件：

- `data/sub.txt`：所有可用节点的合并订阅文件
- `data/sub_base64.txt`：Base64编码的订阅文件
- `data/sub_github.txt`：仅来自GitHub的节点
- `data/sub_platform.txt`：仅来自平台搜索的节点
- `data/github/YYYY/MM/DD/sub_github.txt`：GitHub来源的按日归档节点，便于追溯不同日期的抓取结果
- `data/platform/YYYY/MM/DD/sub_platform.txt`：平台来源的按日归档节点，与GitHub归档结构一致
- `data/YYYY/MM/DD/`：按日期归档的历史订阅文件（所有来源的聚合导出的向后兼容位置）


## 常见问题

### 1. GitHub API限制

如果没有提供`GH_TOKEN`，GitHub API请求将受到严格限制。建议创建个人访问令牌：
1. 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. 创建新令牌，勾选`repo`权限
3. 将令牌添加到`.env`文件中的`GH_TOKEN`变量

### 2. 平台API密钥获取

- **Hunter**：访问 [Hunter.io](https://hunter.qianxin.com) 注册并获取API密钥
- **Quake**：访问 [360 Quake](https://quake.360.net) 注册并获取API密钥

### 3. 节点可用性低

如果发现收集的节点可用性较低，可以尝试：
- 增加`GITHUB_SLEEP_INTERVAL`以避免被限制
- 调整搜索关键词，使用更精确的术语
- 检查网络连接是否正常


>powered by windsurf & chatgpt
