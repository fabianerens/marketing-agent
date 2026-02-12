"""
KPI Calculator for YouTube videos.

Calculates:
- View Velocity (views per day)
- Like Rate (likes / views)
- Comment Rate (comments / views)
- Engagement Score (weighted combination)
- Duration categorization
"""

import logging
import math
from datetime import datetime
from typing import List
from .models import VideoData, VideoKPIs

logger = logging.getLogger(__name__)


class KPICalculator:
    """Calculator for video KPIs and metrics."""

    # Duration thresholds (in seconds)
    SHORT_THRESHOLD = 60  # <= 60s = Shorts
    MEDIUM_THRESHOLD = 600  # <= 10 min = Medium
    # > 10 min = Long

    def __init__(self, like_weight: float = 0.6, comment_weight: float = 0.4):
        """
        Initialize KPI calculator.

        Args:
            like_weight: Weight for like_rate in engagement score (0-1)
            comment_weight: Weight for comment_rate in engagement score (0-1)
        """
        # Normalize weights to sum to 1
        total = like_weight + comment_weight
        self.like_weight = like_weight / total if total > 0 else 0.5
        self.comment_weight = comment_weight / total if total > 0 else 0.5

    def calculate_video_kpis(self, video: VideoData) -> VideoKPIs:
        """
        Calculate KPIs for a single video.

        Args:
            video: VideoData object

        Returns:
            VideoKPIs object with calculated metrics
        """
        # Calculate age in days
        age = datetime.utcnow() - video.published_at.replace(tzinfo=None)
        age_days = max(age.total_seconds() / 86400, 0.01)  # Avoid division by zero

        # View velocity
        view_velocity = video.view_count / age_days if age_days > 0 else 0

        # Engagement rates (robust to zero views)
        like_rate = video.like_count / video.view_count if video.view_count > 0 else 0
        comment_rate = video.comment_count / video.view_count if video.view_count > 0 else 0

        # Engagement score: weighted combination * log scale of views
        # This balances relative engagement with absolute popularity
        engagement_score = (
            (self.like_weight * like_rate + self.comment_weight * comment_rate)
            * math.log1p(video.view_count)
        )

        # Categorize duration
        is_short = video.duration_seconds <= self.SHORT_THRESHOLD
        duration_bucket = self._categorize_duration(video.duration_seconds)

        return VideoKPIs(
            video_id=video.video_id,
            title=video.title,
            published_at=video.published_at,
            age_days=round(age_days, 2),
            duration_seconds=video.duration_seconds,
            is_short=is_short,
            views=video.view_count,
            likes=video.like_count,
            comments=video.comment_count,
            view_velocity=round(view_velocity, 2),
            like_rate=round(like_rate, 6),
            comment_rate=round(comment_rate, 6),
            engagement_score=round(engagement_score, 2),
            duration_bucket=duration_bucket,
        )

    def calculate_batch_kpis(self, videos: List[VideoData]) -> List[VideoKPIs]:
        """
        Calculate KPIs for multiple videos.

        Args:
            videos: List of VideoData objects

        Returns:
            List of VideoKPIs objects
        """
        kpis = []
        for video in videos:
            try:
                kpi = self.calculate_video_kpis(video)
                kpis.append(kpi)
            except Exception as e:
                logger.warning(f"Error calculating KPIs for video {video.video_id}: {e}")
                continue

        return kpis

    def _categorize_duration(self, duration_seconds: int) -> str:
        """
        Categorize video duration.

        Args:
            duration_seconds: Duration in seconds

        Returns:
            Category: "short", "medium", or "long"
        """
        if duration_seconds <= self.SHORT_THRESHOLD:
            return "short"
        elif duration_seconds <= self.MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "long"

    def filter_by_kpis(
        self,
        videos: List[VideoKPIs],
        min_views: int = 0,
        exclude_keywords: List[str] = None
    ) -> List[VideoKPIs]:
        """
        Filter videos by KPI thresholds and keywords.

        Args:
            videos: List of VideoKPIs
            min_views: Minimum view count
            exclude_keywords: Keywords to exclude (case-insensitive)

        Returns:
            Filtered list of VideoKPIs
        """
        filtered = []
        exclude_keywords = [kw.lower() for kw in (exclude_keywords or [])]

        for video in videos:
            # Check view threshold
            if video.views < min_views:
                continue

            # Check excluded keywords
            if exclude_keywords:
                title_lower = video.title.lower()
                if any(kw in title_lower for kw in exclude_keywords):
                    continue

            filtered.append(video)

        return filtered

    def rank_by_metric(
        self,
        videos: List[VideoKPIs],
        metric: str = "engagement_score",
        top_n: int = None
    ) -> List[VideoKPIs]:
        """
        Rank videos by a specific metric.

        Args:
            videos: List of VideoKPIs
            metric: Metric name to sort by
            top_n: Return only top N videos (optional)

        Returns:
            Sorted list of VideoKPIs
        """
        try:
            sorted_videos = sorted(
                videos,
                key=lambda v: getattr(v, metric, 0),
                reverse=True
            )

            if top_n:
                return sorted_videos[:top_n]

            return sorted_videos

        except AttributeError:
            logger.error(f"Invalid metric: {metric}")
            return videos
