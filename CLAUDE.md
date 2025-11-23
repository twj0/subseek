# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SubSeek is a proxy node aggregator that collects free proxy nodes from GitHub repositories and network mapping platforms, then exports them as subscription files. The tool searches for repositories containing proxy configurations, parses various proxy protocols (vmess, vless, ss, trojan), deduplicates them using SQLite, and generates subscription files.

## Development Commands

### Local Development
```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper (requires GH_TOKEN environment variable)
export GH_TOKEN=your_token  # Windows: set GH_TOKEN=your_token
python main.py              # Root entry point
# OR
python -m src.main          # Modular entry point
```

### Docker Development
```bash
# Build image
docker compose build

# Run once
docker compose run --rm subseek

# View logs
docker compose logs -f
```

### Testing
There are no automated tests in this project. Manual testing involves:
- Running the scraper and verifying `data/sub.txt` and `data/sub_base64.txt` are generated
- Checking the SQLite database at `data/nodes.db` for deduplicated nodes
- Verifying subscription files work with proxy clients

## Architecture

### Dual Entry Points
The project has two main entry points:
1. **Root-level** (`main.py`): Legacy entry point with inline implementations
2. **Modular** (`src/main.py`): Refactored modular structure

Both entry points perform the same workflow but the modular version separates concerns into distinct modules.

### Core Workflow
1. **Collection**: Search GitHub API for repositories with keywords like "v2ray free", "clash free"
2. **Fetching**: Download subscription files from common paths (v2ray.txt, clash.yaml, sub.txt, etc.)
3. **Parsing**: Extract proxy links using regex patterns, attempt Base64 decoding if needed
4. **Platform Search**: Query network mapping platforms (Hunter, Quake, DuckDuckGo) for additional sources
5. **Deduplication**: Store nodes in SQLite with MD5 hash-based uniqueness constraint
6. **Export**: Generate `data/sub.txt` (plain text) and `data/sub_base64.txt` (Base64 encoded)

### Module Structure (src/)
- **collectors/**: Data collection from GitHub and network platforms
  - `github.py`: GitHub API search and file fetching
  - `platforms.py`: Hunter/Quake/DDG searchers with API key support
- **database/**: SQLAlchemy ORM models
  - `models.py`: ProxyNode model with unique_hash deduplication
- **utils/**: Parsing utilities
  - `parser.py`: Regex-based proxy link extraction and Base64 decoding
- **exporters/**: Subscription file generation
  - `subscription.py`: Export to plain text and Base64 formats
- **config/**: Configuration management
  - `settings.py`: Environment variable handling

### Database Schema
SQLite database (`data/nodes.db`) with single table `proxy_nodes`:
- `id`: Primary key
- `protocol`: Proxy type (vmess, vless, ss, trojan)
- `link`: Full proxy URL
- `unique_hash`: MD5 hash of link for deduplication (unique constraint)
- `source`: Origin repository or platform URL
- `created_at`, `updated_at`: Timestamps

### Environment Variables
- `GH_TOKEN` (required): GitHub Personal Access Token for API rate limits
- `HUNTER_API_KEY` (optional): Hunter network mapping platform API key
- `QUAKE_API_KEY` (optional): Quake network mapping platform API key
- `DB_PATH` (optional): Override default SQLite database path (default: `data/nodes.db`)

## GitHub Actions Workflow
The `.github/workflows/daily-scrape.yml` workflow:
- Runs daily at UTC 0:00 (Beijing 8:00 AM)
- Uses `main.py` (root entry point) not the modular version
- Commits updated subscription files back to the repository
- Requires `GH_TOKEN` secret configured in repository settings

## Important Implementation Notes

### Proxy Link Parsing Strategy
The parser attempts two-phase extraction:
1. Direct regex matching for proxy protocols
2. Base64 decode the entire content and regex match again (handles encoded subscription files)

### Deduplication Logic
Uses MD5 hash of the entire proxy link as `unique_hash`. SQLite unique constraint prevents duplicates. This means identical links from different sources are stored only once.

### Rate Limiting
- GitHub API: 2-second delay between keyword searches
- Platform searches: 1-2 second delays between API calls
- File fetching: 5-second timeout per request

### Docker vs Local Execution
- Docker uses modular entry point (`python -m src.main`)
- GitHub Actions uses root entry point (`python main.py`)
- Both produce identical results but have different import paths
