# YouTube Marketing Analysis Agent

## Projektbeschreibung

Dieses Projekt ist ein KI-gestützter Marketing-Analyse-Agent, der im Rahmen eines des Kurses OnlineMarketing2 entwickelt wurde. Der Agent analysiert YouTube-Kanäle, um erfolgreiche Videoformate zu identifizieren und datenbasierte Marketingempfehlungen zu generieren.

### Ziele des Projekts

- **YouTube-Kanal-Analyse**: Automatisierte Analyse von bis zu 100 Videos pro Kanal
- **KPI-Berechnung**: Berechnung von Engagement-Metriken wie View Velocity, Like-Rate und Engagement Score
- **Format-Erkennung**: Identifikation wiederkehrender Muster und erfolgreicher Videoformate
- **KI-Empfehlungen**: Generierung von Handlungsempfehlungen durch Google Gemini AI

### Technologie-Stack

- **Google ADK**: Agent Development Kit für die KI-Orchestrierung
- **YouTube Data API v3**: Datenabruf von YouTube
- **Gradio**: Web-Interface für die Benutzerinteraktion
- **Pydantic**: Typsichere Datenmodelle
- **SQLite**: Caching zur Minimierung von API-Aufrufen

---

## Installation

### Voraussetzungen

- Python 3.10 oder höher
- YouTube Data API v3 Key ([Google Cloud Console](https://console.cloud.google.com/apis/credentials))
- Google AI API Key ([Google AI Studio](https://aistudio.google.com/app/apikey))

### Schritt 1: Repository klonen

```bash
git clone https://github.com/fabianerens/marketing-agent.git
cd marketing-agent
```

### Schritt 2: Abhängigkeiten installieren

**Mit uv (empfohlen):**
```bash
pip install uv
uv sync
```

**Mit pip:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -e .
```

### Schritt 3: Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Die `.env` Datei bearbeiten und API-Keys eintragen:

```env
YOUTUBE_API_KEY=dein_youtube_api_key
GOOGLE_API_KEY=dein_google_ai_api_key
```

### Schritt 4: Anwendung starten

```bash
uv run python app/gradio_app.py
```

Die Anwendung ist dann unter **http://localhost:7860** erreichbar.

---

## Funktionen und Verwendung

### Web-Interface

Nach dem Start öffnet sich eine Gradio-Oberfläche mit folgenden Eingabemöglichkeiten:

| Parameter | Beschreibung |
|-----------|--------------|
| **YouTube Channel** | URL, @Handle oder Channel-ID |
| **Max Videos** | Anzahl der zu analysierenden Videos (5-100) |
| **Tage zurück** | Zeitfilter (leer = alle Videos) |
| **Gewichtung** | Balance zwischen Likes und Kommentaren (0-1) |
| **Keywords ausschließen** | Komma-getrennte Liste |
| **Minimum Views** | Mindestanzahl an Aufrufen |
| **Marketing Ziel** | Optionale Zielbeschreibung für kontextbezogene Empfehlungen |

### Analyse-Ablauf

1. **Eingabe**: Kanal-URL eingeben und Parameter konfigurieren
2. **Datenerfassung**: Agent ruft Videodaten über die YouTube API ab
3. **KPI-Berechnung**: Engagement-Metriken werden für jedes Video berechnet
4. **Format-Mining**: Algorithmus erkennt Muster in Titeln und Inhalten
5. **KI-Analyse**: Gemini generiert strukturierte Empfehlungen

### Berechnete KPIs

| Metrik | Formel | Beschreibung |
|--------|--------|--------------|
| **View Velocity** | Views / Tage | Aufrufe pro Tag |
| **Like Rate** | Likes / Views | Anteil der Likes |
| **Comment Rate** | Comments / Views | Anteil der Kommentare |
| **Engagement Score** | (like_weight × like_rate + comment_weight × comment_rate) × log(views) | Kombinierte Engagement-Bewertung |

### Agent-Architektur

```
┌─────────────────────────────────────────┐
│             Gradio UI                    │
│  (Benutzereingabe & Ergebnisanzeige)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│          Google ADK Agent               │
│    (Orchestrierung & KI-Empfehlungen)   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌───────────────────┐
│  Agent Tools  │    │   Core Module     │
│ - analyze     │────│ - YouTubeClient   │
│ - get_info    │    │ - KPICalculator   │
│ - clear_cache │    │ - FormatMiner     │
└───────────────┘    │ - CacheManager    │
                     └───────────────────┘
                              │
                              ▼
                     ┌───────────────────┐
                     │  YouTube Data API │
                     └───────────────────┘
```

---

## Projektstruktur

```
marketing-agent/
├── agent/                 # Google ADK Agent
│   ├── agent.py          # Agent-Definition & Instruktionen
│   └── tools.py          # Tool-Implementierungen
├── app/                   # Benutzeroberfläche
│   └── gradio_app.py     # Gradio Web-Interface
├── core/                  # Kernlogik
│   ├── youtube_client.py # YouTube API Integration
│   ├── cache.py          # SQLite Caching
│   ├── kpi.py            # KPI-Berechnung
│   ├── format_mining.py  # Muster-Erkennung
│   └── models.py         # Pydantic Datenmodelle
├── tests/                 # Unit Tests
├── pyproject.toml        # Abhängigkeiten
└── README.md             # Diese Datei
```

---

## Reflexion: Herausforderungen und Learnings

**1. API-Integration ist komplex**
Die Implementierung der YouTube Data API war aufwendiger als erwartet. Pagination, Quota-Management und die Verarbeitung der Eingabe erforderten sorgfältige Fehlerbehandlung.

**2. Unterschiede zwischen Vorlesung und Praxis**
Nicht alles, was in der Vorlesung funktioniert hat, lief zuhause direkt. Unterschiedliche Python-Versionen, fehlende Abhängigkeiten und Umgebungskonfigurationen führten zu unerwarteten Problemen.

**3. KI-Tools haben Grenzen**
Eine KI kann nicht jeden Fehler direkt lösen. Besonders bei komplexen Abhängigkeiten zwischen Modulen oder subtilen Bugs war manuelles Debugging unerlässlich.

**4. Caching ist essentiell**
Ohne Caching wäre die YouTube API-Quota schnell aufgebraucht. Die Implementierung einer SQLite-basierten Cache-Schicht war notwendig, um wiederholte Analysen zu ermöglichen.

**5. Dokumentation braucht Zeit**
Eine saubere Dokumentation während der Entwicklung zu pflegen ist zeitaufwendig, spart aber später erheblich Zeit beim Debugging und bei der Wartung.

### Wichtigste Learnings

| Learning | Erkenntnis |
|----------|------------|
| **Ordnerstruktur** | Eine klare Trennung (core/, agent/, app/) macht den Code wartbar und testbar |
| **API-Quotas** | Immer Caching implementieren und Rate-Limits beachten |
| **Fehlerbehandlung** | Spezifische Error-Types helfen bei der Problemdiagnose |
| **Iteratives Vorgehen** | Kleine, testbare Schritte sind besser als große Änderungen |
| **Umgebungsvariablen** | Sensible Daten (API-Keys) nie im Code, immer in .env |

---

## Lizenz

MIT License

---

## Kontakt

**Autor**: Fabian Erens

**Repository**: https://github.com/fabianerens/marketing-agent
