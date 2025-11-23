# Project Structure

```
subseek/
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # Entry point
│   ├── collectors/               # Data collectors
│   │   ├── __init__.py
│   │   ├── github.py            # GitHub repository collector
│   │   └── platforms.py         # Network mapping platforms (Hunter/Quake/DDG)
│   ├── database/                 # Database models
│   │   ├── __init__.py
│   │   └── models.py            # SQLAlchemy models
│   ├── exporters/                # Export functionality
│   │   ├── __init__.py
│   │   └── subscription.py      # Subscription file exporter
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── parser.py            # Proxy link parser
├── config/                       # Configuration
│   ├── __init__.py
│   └── settings.py              # Settings and environment variables
├── data/                         # Data directory (generated)
│   ├── .gitkeep
│   ├── nodes.db                 # SQLite database (generated)
│   ├── sub.txt                  # Plain text subscription (generated)
│   └── sub_base64.txt           # Base64 subscription (generated)
├── .github/
│   └── workflows/
│       └── daily-scrape.yml     # GitHub Actions workflow
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker Compose configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── .dockerignore                 # Docker ignore rules
├── README.md                     # Project documentation
└── PROJECT_STRUCTURE.md          # This file
```

## Module Responsibilities

### src/collectors/
- **github.py**: Search GitHub repositories and fetch subscription files
- **platforms.py**: Search network mapping platforms (Hunter, Quake, DuckDuckGo)

### src/database/
- **models.py**: SQLAlchemy ORM models and database initialization

### src/exporters/
- **subscription.py**: Export collected nodes to subscription files

### src/utils/
- **parser.py**: Parse proxy links from various formats (Base64, plain text)

### config/
- **settings.py**: Centralized configuration and environment variables
