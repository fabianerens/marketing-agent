"""
Core module for YouTube Marketing Agent.

This module provides the core functionality for analyzing YouTube channels:
- YouTube API client
- KPI calculation
- Format mining and clustering
- SQLite caching
"""

from .models import (
    VideoData,
    VideoKPIs,
    FormatCluster,
    AnalysisResult,
    ChannelInfo,
)
from .youtube_client import YouTubeClient
from .kpi import KPICalculator
from .format_mining import FormatMiner
from .cache import CacheManager

__all__ = [
    "VideoData",
    "VideoKPIs",
    "FormatCluster",
    "AnalysisResult",
    "ChannelInfo",
    "YouTubeClient",
    "KPICalculator",
    "FormatMiner",
    "CacheManager",
]
