# YouTube Marketing Analysis Agent

## Context

This project demonstrates how to build an AI-powered marketing analysis tool using:
- **Google ADK (Agent Development Kit)**: For the intelligent agent orchestration
- **YouTube Data API v3**: For fetching channel and video data
- **Gradio**: For the user-friendly web interface
- **Pydantic**: For type-safe data models
- **SQLite**: For API response caching

The agent analyzes YouTube channels, identifies successful video format patterns, calculates engagement KPIs, and generates actionable marketing recommendations using Google's Gemini AI.

## Project Structure

```
marketing-agent/
├── core/                      # Core business logic
│   ├── __init__.py           # Module exports
│   ├── models.py             # Pydantic data models
│   ├── youtube_client.py     # YouTube API wrapper
│   ├── cache.py              # SQLite caching layer
│   ├── kpi.py                # KPI calculation engine
│   └── format_mining.py      # Pattern detection & clustering
├── agent/                    # Google ADK agent
│   ├── __init__.py          # Agent exports
│   ├── agent.py             # Agent definition & instructions
│   └── tools.py             # Tool implementations
├── app/                     # Gradio UI
│   ├── __init__.py
│   └── gradio_app.py        # Web interface
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_kpi.py
│   └── test_format_mining.py
├── data/                    # SQLite cache (gitignored)
├── app.py                   # Main launcher
├── pyproject.toml           # Dependencies & config
├── .env.example             # Environment variables template
├── .env                     # Your API keys (gitignored)
├── Makefile                 # Build automation
├── run.sh                   # Quick start (Unix)
├── run.bat                  # Quick start (Windows)
└── README.md                # Full documentation
```

## Running the Project

### Quick Start

**Unix/Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```bat
run.bat
```

### Using Make

```bash
# First-time setup (installs deps + creates .env)
make setup

# Start the app
make run

# Run tests
make test

# See all commands
make help
```

### Manual Start

**With uv (recommended):**
```bash
# Install dependencies
uv sync

# Run app
uv run python app.py
```

**With pip:**
```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .

# Run app
python app.py
```

The Gradio UI will launch at: **http://localhost:7860**

## Agent Architecture

### ADK Agent (agent/agent.py)

The agent is configured with:
- **Model**: Gemini 2.0 Flash (configurable via `GEMINI_MODEL` env var)
- **Temperature**: 0.7 (balanced creativity/precision)
- **Tools**:
  - `analyze_youtube_channel`: Main analysis pipeline
  - `get_channel_info`: Quick channel metadata lookup
  - `clear_cache`: Cache management

**Agent Instructions** define how the agent:
1. Calls tools with user parameters
2. Interprets returned data (channel info, video KPIs, format clusters)
3. Generates structured recommendations:
   - Top Formats (3-8): Pattern + KPIs + replication steps
   - Quick Wins: Actionable insights
   - Risks & Limitations: Caveats

### Tools (agent/tools.py)

**`analyze_youtube_channel`** orchestrates:
1. Channel ID resolution
2. Video fetching (with caching)
3. KPI calculation
4. Format mining
5. Returns structured JSON for agent analysis

### Core Modules

**youtube_client.py**: YouTube API integration
- Channel resolution (URL/@handle/ID → channel_id)
- Video list retrieval (pagination)
- Batch video details fetching (50/request)
- Rate limit handling

**kpi.py**: KPI calculation
- View velocity (views/day)
- Engagement rates (like_rate, comment_rate)
- Engagement score (weighted combination × log scale)
- Duration categorization (short/medium/long)

**format_mining.py**: Pattern detection
- Title normalization (remove emojis, lowercase)
- Prefix clustering (first 3 words)
- Keyword extraction (common terms)
- Episode detection (Ep X, Part X, #X patterns)
- Median KPI aggregation per cluster

**cache.py**: SQLite caching
- 12-hour TTL (configurable)
- Caches: channel info, video lists, video details
- Auto-expiration on read

## Configuration

### Environment Variables (.env)

**Required:**
- `YOUTUBE_API_KEY`: Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- `GOOGLE_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

**Optional:**
- `GEMINI_MODEL`: Model name (default: `gemini-2.0-flash-exp`)
- `CACHE_TTL_HOURS`: Cache duration (default: `12`)
- `CACHE_DB_PATH`: SQLite location (default: `./data/cache.db`)
- `DEBUG`: Enable debug logs (default: `false`)

### Gradio UI Parameters

- **Channel Input**: URL, @handle, or channel ID
- **Max Videos**: 5-100 (default: 30)
- **Days Back**: Optional date filter (1-365)
- **KPI Weights**: Like vs comment importance (default: 0.6/0.4)
- **Filters**: Exclude keywords, minimum views
- **Marketing Goal**: Context for AI recommendations

## Development

### Adding Dependencies

**With uv:**
```bash
uv add <package-name>
```

**With pip:**
```bash
pip install <package-name>
# Then update pyproject.toml
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov=agent

# Specific test
pytest tests/test_kpi.py -v
```

### Code Quality

```bash
# Format
make format  # or: black .

# Lint
make lint    # or: ruff check .
```

## API Quotas

### YouTube Data API v3

**Daily Quota**: 10,000 units (default)

**Cost per Operation**:
- Channel info: 1 unit
- Playlist items: 1 unit/page
- Video details: 1 unit/request (up to 50 videos)

**Example**: Analyzing 30 videos ≈ 3-5 units (with caching)

**Quota Management**:
- Enable caching (automatic)
- Analyze fewer videos
- Request quota increase in Google Cloud Console

### Google AI (Gemini)

**Free Tier**: 60 requests/minute, 1500 requests/day

**Sufficient for**: Most analysis tasks (1 request per channel analysis)

## Troubleshooting

### "API key not configured"
→ Check `.env` file exists and contains valid keys

### "Could not resolve channel"
→ Verify channel URL/handle, try direct channel ID (UC...)

### "Quota exceeded"
→ Wait 24h or request quota increase, enable caching

### "No formats found"
→ Increase max videos (30 → 50+), channel may lack patterns

### Cache issues
→ Delete `data/cache.db` to clear cache

## Further Reading

- [Full Documentation](README.md)
- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [Google ADK Docs](https://github.com/google/adk-toolkit)
- [Gradio Docs](https://www.gradio.app/docs)

