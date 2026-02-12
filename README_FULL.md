# 🎬 YouTube Marketing Analysis Agent

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![uv](https://img.shields.io/badge/uv-managed-430f8e.svg?style=flat&logo=python&logoColor=white)
![Gradio Version](https://img.shields.io/badge/gradio-6.1.0-orange.svg)
![Google ADK](https://img.shields.io/badge/Google_ADK-1.20.0-4285F4.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎓 University Project

**YouTube Channel Marketing Analysis Agent using Google ADK**

This university project demonstrates how to build an AI-powered marketing analysis tool that:
- Analyzes YouTube channels using the YouTube Data API v3
- Identifies successful video format patterns (series, recurring themes, content types)
- Calculates engagement KPIs (view velocity, engagement score, like/comment rates)
- Generates actionable marketing recommendations using Google's Gemini AI

Repository: https://github.com/fabianerens/marketing-agent.git

---

## ✨ Key Features

- 🎯 **YouTube Channel Analysis**: Fetch and analyze up to 100 videos per channel
- 📊 **KPI Calculation**: View velocity, engagement score, like/comment rates
- 🔍 **Format Mining**: Automatically detect video series, recurring patterns, and content clusters
- 🤖 **AI-Powered Recommendations**: Gemini-powered insights and actionable advice
- 🎨 **Gradio UI**: User-friendly web interface with parameter controls
- 💾 **Smart Caching**: SQLite-based caching with 12-hour TTL to minimize API usage
- 🔧 **Configurable**: Adjust KPI weights, filters, date ranges, and more

---

## 🏗 Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Gradio UI                           │
│  (User Input: Channel, Parameters, Filters, Marketing Goal) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Google ADK Agent                         │
│  (Orchestrates analysis pipeline + generates recommendations)│
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
┌────────────────────┐   ┌────────────────────┐
│   Agent Tools      │   │   Core Modules     │
│ - analyze_channel  │───│ - YouTubeClient    │
│ - get_channel_info │   │ - KPICalculator    │
│ - clear_cache      │   │ - FormatMiner      │
└────────────────────┘   │ - CacheManager     │
                         └────────────────────┘
                                  │
                                  ▼
                         ┌────────────────────┐
                         │  YouTube Data API  │
                         │  (v3 REST API)     │
                         └────────────────────┘
```

### Data Flow

1. **Input**: User provides channel identifier + analysis parameters
2. **Channel Resolution**: Convert URL/@handle/ID → channel_id
3. **Data Fetching**: Retrieve channel info + video list + video details (batched)
4. **Caching**: Check SQLite cache before API calls (12h TTL)
5. **KPI Calculation**: Compute views, engagement rates, view velocity for each video
6. **Format Mining**: Cluster videos by title patterns, keywords, duration
7. **AI Analysis**: Agent generates structured recommendations using Gemini
8. **Output**: Display results in Gradio UI (markdown + tables)

### Module Structure

```
marketing-agent/
├── core/                  # Core business logic
│   ├── youtube_client.py  # YouTube API wrapper
│   ├── cache.py          # SQLite caching layer
│   ├── kpi.py            # KPI calculation engine
│   ├── format_mining.py  # Pattern detection & clustering
│   └── models.py         # Pydantic data models
├── agent/                # ADK agent
│   ├── agent.py          # Agent definition & instructions
│   └── tools.py          # Tool implementations
├── app/                  # Gradio UI
│   └── gradio_app.py     # Web interface
├── tests/                # Unit tests
│   ├── test_kpi.py
│   └── test_format_mining.py
├── data/                 # SQLite cache (gitignored)
├── app.py                # Main launcher
├── pyproject.toml        # Dependencies
├── .env.example          # Example environment variables
└── README.md            # This file
```

---

## 🚀 Setup Instructions

### 1️⃣ Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **uv** package manager (optional, but recommended)
- **YouTube Data API v3 key** ([Get one here](https://console.cloud.google.com/apis/credentials))
- **Google AI API key** (Gemini) ([Get one here](https://aistudio.google.com/app/apikey))

Install `uv` (recommended):

```bash
pip install uv
```

Or use standard pip/venv.

### 2️⃣ Clone Repository

```bash
git clone https://github.com/fabianerens/marketing-agent.git
cd marketing-agent
```

### 3️⃣ Install Dependencies

**Using uv (recommended):**

```bash
uv sync
```

**Using pip:**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 4️⃣ Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# Google AI (Gemini) for ADK Agent
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Gemini model configuration
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Cache TTL in hours (default: 12)
CACHE_TTL_HOURS=12

# Optional: Database path for SQLite cache
CACHE_DB_PATH=./data/cache.db

# Optional: Enable debug logging
DEBUG=false
```

**Getting API Keys:**

1. **YouTube Data API v3**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project (or select existing)
   - Enable "YouTube Data API v3"
   - Create credentials → API Key
   - Copy the API key to `.env`

2. **Google AI (Gemini)**:
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Get API Key"
   - Copy the API key to `.env`

### 5️⃣ Run the Application

**Using uv:**

```bash
uv run python app.py
```

**Using standard Python:**

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python app.py
```

The Gradio UI will start at: **http://localhost:7860**

---

## 📖 Usage Guide

### Basic Workflow

1. **Enter Channel Identifier**
   - YouTube URL: `https://www.youtube.com/channel/UCxxx`
   - Handle: `@MrBeast`
   - Direct ID: `UCxxx...`

2. **Configure Analysis Parameters**
   - **Max Videos**: Number of videos to analyze (5-100)
   - **Days Back**: Optional date filter (e.g., last 90 days)
   - **KPI Weights**: Adjust like vs comment importance
   - **Filters**: Exclude keywords, set minimum views

3. **Set Marketing Goal** (Optional)
   - Describe your objective for contextualized recommendations
   - Example: "Increase engagement on tech reviews"

4. **Analyze**
   - Click "Analyze Channel"
   - Wait for analysis (10-60 seconds depending on video count)

5. **Review Results**
   - **Channel Overview**: Subscriber count, video count
   - **Top Formats**: Identified patterns with KPI breakdown
   - **Quick Wins**: Actionable insights
   - **Risks & Limitations**: Important caveats

### Example Analysis Output

```markdown
## Channel Overview
- Channel: MrBeast (200M subscribers, 741 videos)
- Analysis scope: 30 videos (last 6 months)

## Top Performing Formats

### 1. "$1 vs $X Challenge" Series
- **Pattern**: Price comparison challenges with escalating budgets
- **Performance**:
  - Median Views: 85M
  - View Velocity: 2.1M views/day
  - Engagement Score: 1,245
- **Video Count**: 8 videos
- **Best Example**: "$1 vs $500,000 Hotel Room" - 156M views
- **Why It Works**:
  - High curiosity factor (extreme price differences)
  - Clear structure and recurring format
  - Strong thumbnail contrast
- **How to Replicate**:
  1. Identify extreme price comparisons in your niche
  2. Create consistent title format: "$X vs $Y [Item/Experience]"
  3. Use side-by-side comparisons in thumbnails
  4. Maintain 12-18 minute duration for maximum retention

### 2. "I Gave Away..." Philanthropy Series
[...]

## Quick Wins
- Short-form content (<60s) shows 3x view velocity - consider YouTube Shorts
- Videos with numbers in title perform 42% better
- Thursday uploads receive 18% more engagement

## Risks & Limitations
- Data based on public metrics (some stats may be hidden by creator)
- Past performance doesn't guarantee future success
- Algorithm changes can shift what works
- Respect YouTube's Terms of Service in content creation
```

---

## 🧪 Running Tests

**Run all tests:**

```bash
pytest
```

**With coverage:**

```bash
pytest --cov=core --cov=agent
```

**Specific test file:**

```bash
pytest tests/test_kpi.py
```

---

## 📊 KPI Definitions

### Calculated Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Views** | Direct from API | Total view count |
| **View Velocity** | `views / age_days` | Views per day (accounts for video age) |
| **Like Rate** | `likes / views` | Percentage of viewers who liked |
| **Comment Rate** | `comments / views` | Percentage of viewers who commented |
| **Engagement Score** | `(like_weight × like_rate + comment_weight × comment_rate) × log(views + 1)` | Combines relative engagement with absolute popularity |

### Duration Buckets

- **Short**: ≤ 60 seconds (YouTube Shorts)
- **Medium**: 61-600 seconds (10 minutes)
- **Long**: > 600 seconds (10+ minutes)

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | **Required** |
| `GOOGLE_API_KEY` | Google AI (Gemini) key | **Required** |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.0-flash-exp` |
| `CACHE_TTL_HOURS` | Cache time-to-live | `12` |
| `CACHE_DB_PATH` | SQLite cache location | `./data/cache.db` |
| `DEBUG` | Enable debug logging | `false` |

### Adjustable Parameters

**In Gradio UI:**
- **Max Videos**: 5-100 (default: 30)
- **Days Back**: 1-365 or None for all videos
- **Like Weight**: 0.0-1.0 (default: 0.6)
- **Comment Weight**: 0.0-1.0 (default: 0.4)
- **Exclude Keywords**: Comma-separated list
- **Minimum Views**: Integer threshold

---

## 🛠️ Development

### Project Structure

```
core/                   # Core business logic (pure Python, no UI)
  youtube_client.py     # YouTube API integration
  cache.py             # SQLite caching
  kpi.py               # KPI calculation
  format_mining.py     # Pattern detection
  models.py            # Pydantic models

agent/                 # Google ADK agent
  agent.py            # Agent definition
  tools.py            # Tool implementations

app/                  # User interfaces
  gradio_app.py       # Gradio web UI

tests/                # Unit tests
  test_kpi.py
  test_format_mining.py
```

### Adding New KPIs

1. Add calculation logic to `core/kpi.py`
2. Update `VideoKPIs` model in `core/models.py`
3. Add tests to `tests/test_kpi.py`

### Extending Format Detection

1. Add new clustering logic to `core/format_mining.py`
2. Update agent instructions in `agent/agent.py` if needed
3. Add tests to `tests/test_format_mining.py`

---

## 🚨 Troubleshooting

### API Quota Exceeded

**Error**: "YouTube API quota exceeded"

**Solution**:
- YouTube Data API has daily quota limits (10,000 units/day by default)
- Each video details request costs ~5 units
- Use caching (automatic) to minimize API calls
- Analyze fewer videos or wait 24 hours for quota reset
- Request quota increase in Google Cloud Console

### Invalid Channel

**Error**: "Could not resolve channel identifier"

**Solution**:
- Verify the channel URL/handle is correct
- Try direct channel ID (starts with "UC")
- Some channels may have privacy settings

### No Formats Found

**Warning**: "No format clusters detected"

**Solution**:
- Increase max videos (default: 30 → try 50+)
- Channel may lack recurring patterns
- Adjust `min_cluster_size` in `format_mining.py` (default: 3)

### Cache Issues

**Problem**: Stale data or cache corruption

**Solution**:
```bash
# Clear cache via UI (under development)
# Or manually delete:
rm -rf data/cache.db
```

---

## 📚 Technical Background

### YouTube Data API

**Endpoints Used:**
- `channels().list()` - Channel metadata
- `playlistItems().list()` - Uploads playlist (video IDs)
- `videos().list()` - Video details (batched, up to 50/request)

**Quota Costs:**
- Channel info: 1 unit
- Playlist items: 1 unit per page (50 videos)
- Video details: 1 unit per request (up to 50 videos)

**Rate Limits:**
- Default: 10,000 units/day
- Requests: 100/100 seconds

### Format Mining Algorithm

**Pattern Detection:**
1. **Title Normalization**: Remove emojis, lowercase, collapse spaces
2. **Prefix Clustering**: First 3 words as pattern key
3. **Keyword Extraction**: Common words across titles (min 2 occurrences)
4. **Episode Detection**: Patterns like "Ep X", "Part X", "#X"
5. **Duration Grouping**: Short/Medium/Long buckets
6. **Aggregation**: Median KPIs per cluster

**Minimum Cluster Size**: 3 videos (configurable)

### Engagement Score Formula

```python
engagement_score = (
    (like_weight * like_rate + comment_weight * comment_rate)
    * log(views + 1)
)
```

**Why log(views)?**
- Balances relative engagement (rates) with absolute popularity (views)
- Prevents very high-view videos from dominating despite low engagement rates
- log scale: 1K views ≈ 7, 1M views ≈ 14, 100M views ≈ 18

---

## 🔒 Privacy & Terms of Service

**Data Collection:**
- This tool only accesses **public** YouTube data via official API
- No authentication required (read-only public data)
- No personal user data collected

**Caching:**
- Video metadata cached locally (SQLite)
- Cache auto-expires after 12 hours
- No data shared with third parties

**YouTube ToS Compliance:**
- Uses official YouTube Data API v3
- Respects rate limits and quota
- Does not scrape HTML or bypass API restrictions
- Recommendations are advisory only - respect platform guidelines

**Disclaimer:**
- This tool is for educational and research purposes
- Past performance does not guarantee future results
- Always follow YouTube's Community Guidelines and ToS
- Use insights responsibly and ethically

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

This is a university project, but contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact

**Project Team**: Fabian Erens

**Repository**: https://github.com/fabianerens/marketing-agent

**Issues**: https://github.com/fabianerens/marketing-agent/issues

---

## 🙏 Acknowledgments

- **Google ADK**: Agent Development Kit framework
- **YouTube Data API v3**: Official YouTube API
- **Gradio**: UI framework
- **Gemini AI**: Natural language recommendations
- **University Project**: Part of our coursework on AI agents

---

## 📖 Further Reading

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Google ADK Documentation](https://github.com/google/adk-toolkit)
- [Gradio Documentation](https://www.gradio.app/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Happy Analyzing!** 🎬📊🚀
