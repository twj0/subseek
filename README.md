# SubSeek 

一个用于自动从 GitHub 免费节点仓库中收集代理节点，并导出为订阅文件的轻量级工具。

> 仅供技术研究使用，请确保你的使用符合当地法律法规以及 GitHub 的使用条款。

## 功能概览

- **GitHub 搜索**：按关键词（如 `v2ray free`、`clash free` 等）搜索最近更新的免费节点仓库。
- **订阅文件抓取**：尝试从常见路径下载 `v2ray.txt`、`clash.yaml`、`sub.txt` 等文件。
- **节点解析**：解析 `vmess://`、`vless://`、`ss://`、`trojan://` 等链接，必要时尝试 Base64 解码。
- **去重存储**：使用 SQLite 通过 `unique_hash` 去重存储到本地数据库。
- **导出订阅**：自动生成：
  - `data/sub.txt`：纯文本节点列表（每行一个链接）。
  - `data/sub_base64.txt`：对 `sub.txt` 整体 Base64 编码后的字符串，可直接作为订阅使用。


## 环境变量

- `GH_TOKEN`（必选，推荐）
  - GitHub Personal Access Token，用于提高 GitHub API 限额。
  - 在本地/VPS 上通过 `.env` 或环境变量设置；
  - 在 GitHub Actions 中通过仓库 `Secrets` 设置。

- `DB_PATH`（可选）
  - 覆盖默认的 SQLite 数据库路径，默认值为 `data/nodes.db`。
  - 通过环境变量 `DB_PATH` 设置时，`models.py` 会使用该路径。

---

## 在 VPS 上使用（推荐：Docker / docker-compose）

适用于 **有 VPS** 的用户。

### 1. 准备环境

- 已安装：
  - Docker
  - docker compose 插件（或 `docker-compose`）

### 2. 克隆项目并配置环境变量

```bash
git clone https://github.com/your-name/subseek.git
cd subseek

cp .env.example .env
# 编辑 .env，填写你自己的 GH_TOKEN
```

`.env` 文件中：

```bash
GH_TOKEN=your_github_personal_access_token_here
```

### 3. 构建镜像

```bash
docker compose build
```

### 4. 手动运行一次爬虫

```bash
docker compose run --rm subseek
```

运行结束后，会在 `data/` 下生成：

- `nodes.db`：SQLite 数据库，保存去重后的节点信息；
- `sub.txt`：每行一个节点链接，可直接作为通用订阅文本；
- `sub_base64.txt`：对 `sub.txt` 整体 Base64 编码后的字符串，可作为部分客户端的订阅内容。

### 5. 在 VPS 上定时运行（cron 调度）

无需让容器一直运行，推荐由宿主机的 `cron` 定时执行一次性任务。例如每天凌晨 4 点运行一次：

```bash
crontab -e
```

添加类似条目（请根据实际路径修改）：

```bash
0 4 * * * cd /opt/subseek && docker compose run --rm subseek >> /var/log/subseek.log 2>&1
```

这样：

- 任务由宿主机调度；
- 每天执行一次完整的抓取 + 解析 + 导出流程；
- 日志写入 `/var/log/subseek.log` 便于排查问题。

### 6. 暴露订阅文件（raw `sub.txt`）

假设你在 VPS 上使用 Nginx，可以把 `data/` 目录作为静态目录暴露出去，例如：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /opt/subseek/data;

    location / {
        autoindex off;
    }
}
```

这样：

- `http://your-domain.com/sub.txt` 会直接返回纯文本订阅；
- `http://your-domain.com/sub_base64.txt` 会返回 Base64 订阅字符串。

在 Clash / v2rayN / 小火箭 等客户端中，将订阅地址设置为上述 URL 即可。

> 提示：如果你已经有现成的 Nginx/Caddy 反向代理，也可以只为 `sub.txt` 增加一个 `location`，不必单独起一个站点。

---

## 没有 VPS 的用户：使用 GitHub Actions

对于没有 VPS 的用户，可以直接依赖 GitHub Actions 的免费 Runner，每天自动抓取并更新仓库中的 `data/sub.txt` 文件，通过 `raw.githubusercontent.com` 作为订阅地址。

### 1. 配置仓库 Secret

在 GitHub 仓库中：

- 打开 `Settings -> Secrets and variables -> Actions -> New repository secret`；
- 创建名为：`GH_TOKEN` 的 Secret；
- 值为你的 GitHub Personal Access Token（至少需要访问公开仓库的权限）。

### 2. 工作流说明

本仓库包含工作流文件：

- `.github/workflows/daily-scrape.yml`

它会：

- 每天 UTC 0 点（北京时间 8 点）自动运行一次；
- 安装依赖，执行 `python main.py` 完成抓取和导出；
- 如果 `data/sub.txt` 或 `data/sub_base64.txt` 有变化，会自动 `git commit` 并 `push` 回仓库。

### 3. 订阅地址（raw `sub.txt`）

假设你的仓库地址为：

- `https://github.com/your-name/subseek`

分支为 `main`，那么订阅地址可以是：

```text
https://raw.githubusercontent.com/your-name/subseek/main/data/sub.txt
```

Base64 订阅地址类似：

```text
https://raw.githubusercontent.com/your-name/subseek/main/data/sub_base64.txt
```

将上述 URL 填入客户端的订阅地址即可。

---

## 本地直接运行（可选）

如果你不想用 Docker，也可以在本地直接运行（需要 Python 3.11+）：

```bash
git clone https://github.com/your-name/subseek.git
cd subseek

python -m venv .venv
source .venv/bin/activate  # Windows 上使用 .venv\\Scripts\\activate

pip install -r requirements.txt

export GH_TOKEN=your_github_personal_access_token_here  # Windows 上用 set GH_TOKEN=...
python main.py
```

运行结束后，同样会在 `data/` 目录下看到生成的数据库和订阅文件。

---

## 注意事项

- **隐私与安全**：
  - 不要把真实的 `GH_TOKEN` 写入仓库文件（包括 `.env`），只应保留 `.env.example` 之类的示例。
  - 对节点的使用请遵守当地法律法规和服务提供方的政策。

- **性能与限额**：
  - 没有 `GH_TOKEN` 时，GitHub API 会很快触及匿名访问限额，导致抓取失败或不完整。
  - 建议始终配置 `GH_TOKEN`，并控制抓取频率（如每天 1 次）。

- **后续可以优化的方向**：
  - 增加节点可用性测试（TCP 连通、延迟测量等）；
  - 更精细的去重策略（基于 IP/Port/UUID 等关键字段）；
  - 提供简单的 Web API（如使用 FastAPI）动态输出订阅。