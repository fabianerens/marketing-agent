"""
ADK Tools for YouTube Marketing Analysis.

These tools are exposed to the agent for orchestrating the analysis:
- analyze_youtube_channel: Main orchestration tool
- get_channel_info: Get channel metadata
- calculate_video_kpis: Calculate KPIs for videos
- find_video_formats: Discover format patterns
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core import (
    YouTubeClient,
    KPICalculator,
    FormatMiner,
    CacheManager,
    ChannelInfo,
    VideoKPIs,
    FormatCluster,
)

logger = logging.getLogger(__name__)

# Initialize core components (lazily)
youtube_client = None
cache_manager = None


def _get_youtube_client():
    """Get or create YouTube client instance."""
    global youtube_client
    if youtube_client is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        youtube_client = YouTubeClient(api_key=api_key)
    return youtube_client


def _get_cache_manager():
    """Get or create cache manager instance."""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager(
            db_path=os.getenv("CACHE_DB_PATH", "./data/cache.db"),
            ttl_hours=int(os.getenv("CACHE_TTL_HOURS", "12"))
        )
    return cache_manager


def analyze_youtube_channel(
    channel_identifier: str,
    max_videos: int = 30,
    days_back: Optional[int] = None,
    like_weight: float = 0.6,
    comment_weight: float = 0.4,
    exclude_keywords: Optional[List[str]] = None,
    min_views: int = 0,
    marketing_goal: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a YouTube channel and identify successful formats.

    This is the main orchestration tool that:
    1. Resolves channel identifier
    2. Fetches channel info and videos
    3. Calculates KPIs
    4. Mines format patterns
    5. Returns structured results

    Args:
        channel_identifier: YouTube channel URL, @handle, or channel_id
        max_videos: Maximum number of videos to analyze (default: 30)
        days_back: Only analyze videos from last N days (optional)
        like_weight: Weight for like rate in engagement score (0-1)
        comment_weight: Weight for comment rate in engagement score (0-1)
        exclude_keywords: Keywords to exclude from analysis
        min_views: Minimum view count threshold
        marketing_goal: User's marketing goal (for AI recommendations)

    Returns:
        Dictionary with analysis results including channel info, videos, and formats
    """
    try:
        logger.info(f"Starting analysis for channel: {channel_identifier}")

        # 1. Resolve channel ID
        channel_id = _get_youtube_client().resolve_channel_id(channel_identifier)
        if not channel_id:
            return {
                "success": False,
                "error": f"Could not resolve channel identifier: {channel_identifier}",
                "error_type": "INVALID_CHANNEL"
            }

        # 2. Get channel info
        channel_info = _get_youtube_client().get_channel_info(channel_id)
        if not channel_info:
            return {
                "success": False,
                "error": f"Could not fetch channel info for ID: {channel_id}",
                "error_type": "API_ERROR"
            }

        logger.info(f"Analyzing channel: {channel_info.title} ({channel_info.channel_id})")

        # 3. Fetch videos
        videos = _get_youtube_client().get_channel_videos(
            channel_id=channel_id,
            max_videos=max_videos,
            days_back=days_back
        )

        if not videos:
            return {
                "success": False,
                "error": "No videos found for this channel",
                "error_type": "NO_VIDEOS",
                "channel_info": channel_info.model_dump()
            }

        logger.info(f"Fetched {len(videos)} videos")

        # 4. Calculate KPIs
        kpi_calculator = KPICalculator(
            like_weight=like_weight,
            comment_weight=comment_weight
        )
        video_kpis = kpi_calculator.calculate_batch_kpis(videos)

        # 5. Apply filters
        filtered_kpis = kpi_calculator.filter_by_kpis(
            videos=video_kpis,
            min_views=min_views,
            exclude_keywords=exclude_keywords or []
        )

        if not filtered_kpis:
            return {
                "success": False,
                "error": "No videos remaining after applying filters",
                "error_type": "NO_VIDEOS_AFTER_FILTER",
                "channel_info": channel_info.model_dump()
            }

        logger.info(f"Analyzing {len(filtered_kpis)} videos after filters")

        # 6. Mine format patterns
        format_miner = FormatMiner(min_cluster_size=3)
        format_clusters = format_miner.find_formats(filtered_kpis)

        logger.info(f"Found {len(format_clusters)} format clusters")

        # 7. Prepare results
        date_range_start = min(v.published_at for v in filtered_kpis) if filtered_kpis else None
        date_range_end = max(v.published_at for v in filtered_kpis) if filtered_kpis else None

        result = {
            "success": True,
            "channel_info": channel_info.model_dump(),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "videos_analyzed": len(filtered_kpis),
            "date_range_start": date_range_start.isoformat() if date_range_start else None,
            "date_range_end": date_range_end.isoformat() if date_range_end else None,
            "all_videos": [v.model_dump() for v in filtered_kpis],
            "top_formats": [f.model_dump() for f in format_clusters],
            "marketing_goal": marketing_goal,
        }

        return result

    except Exception as e:
        logger.error(f"Error analyzing channel: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "UNEXPECTED_ERROR"
        }


def get_channel_info_tool(channel_identifier: str) -> Dict[str, Any]:
    """
    Get basic channel information without full analysis.

    Args:
        channel_identifier: YouTube channel URL, @handle, or channel_id

    Returns:
        Dictionary with channel info or error
    """
    try:
        channel_id = _get_youtube_client().resolve_channel_id(channel_identifier)
        if not channel_id:
            return {
                "success": False,
                "error": f"Could not resolve channel: {channel_identifier}"
            }

        channel_info = _get_youtube_client().get_channel_info(channel_id)
        if not channel_info:
            return {
                "success": False,
                "error": f"Could not fetch channel info"
            }

        return {
            "success": True,
            "channel_info": channel_info.model_dump()
        }

    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def clear_cache_tool() -> Dict[str, Any]:
    """
    Clear all cached data.

    Returns:
        Success message
    """
    try:
        _get_cache_manager().clear_all()
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }
