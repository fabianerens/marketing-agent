"""
Format Mining and Pattern Detection for YouTube videos.

Detects recurring patterns and clusters videos by:
- Title patterns (prefix/suffix, episode numbers)
- Duration buckets
- Common keywords
- Performance metrics
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
import emoji
import numpy as np
from sklearn.cluster import DBSCAN

from .models import VideoKPIs, FormatCluster

logger = logging.getLogger(__name__)


class FormatMiner:
    """Mines video format patterns and clusters."""

    def __init__(self, min_cluster_size: int = 3):
        """
        Initialize format miner.

        Args:
            min_cluster_size: Minimum videos required to form a cluster
        """
        self.min_cluster_size = min_cluster_size

    def find_formats(self, videos: List[VideoKPIs]) -> List[FormatCluster]:
        """
        Discover recurring formats in videos.

        Args:
            videos: List of VideoKPIs

        Returns:
            List of FormatCluster objects, sorted by median engagement
        """
        if len(videos) < self.min_cluster_size:
            logger.warning(f"Not enough videos ({len(videos)}) to form clusters")
            return []

        # Normalize titles
        normalized_videos = [
            (v, self._normalize_title(v.title))
            for v in videos
        ]

        # Extract features for clustering
        clusters_dict = defaultdict(list)

        # Pattern 1: Exact prefix matching (e.g., "Series Name Ep X")
        prefix_clusters = self._cluster_by_prefix(normalized_videos)
        for cluster_key, cluster_videos in prefix_clusters.items():
            if len(cluster_videos) >= self.min_cluster_size:
                clusters_dict[f"prefix_{cluster_key}"] = cluster_videos

        # Pattern 2: Common keywords + duration bucket
        keyword_clusters = self._cluster_by_keywords(normalized_videos)
        for cluster_key, cluster_videos in keyword_clusters.items():
            if len(cluster_videos) >= self.min_cluster_size:
                clusters_dict[f"keywords_{cluster_key}"] = cluster_videos

        # Pattern 3: Episode/Part numbers
        episode_clusters = self._cluster_by_episodes(normalized_videos)
        for cluster_key, cluster_videos in episode_clusters.items():
            if len(cluster_videos) >= self.min_cluster_size:
                clusters_dict[f"episodes_{cluster_key}"] = cluster_videos

        # Convert to FormatCluster objects
        format_clusters = []
        for cluster_id, cluster_videos in clusters_dict.items():
            cluster = self._create_cluster(cluster_id, cluster_videos)
            if cluster:
                format_clusters.append(cluster)

        # Sort by median engagement score
        format_clusters.sort(key=lambda c: c.median_engagement_score, reverse=True)

        logger.info(f"Found {len(format_clusters)} format clusters")
        return format_clusters

    def _normalize_title(self, title: str) -> str:
        """
        Normalize title: lowercase, remove emojis, extra punctuation.

        Args:
            title: Original title

        Returns:
            Normalized title
        """
        # Remove emojis
        title = emoji.replace_emoji(title, replace='')

        # Lowercase
        title = title.lower()

        # Remove extra punctuation (keep alphanumeric, spaces, basic punctuation)
        title = re.sub(r'[^\w\s\-\:]', ' ', title)

        # Collapse multiple spaces
        title = re.sub(r'\s+', ' ', title)

        return title.strip()

    def _cluster_by_prefix(
        self,
        normalized_videos: List[Tuple[VideoKPIs, str]]
    ) -> Dict[str, List[VideoKPIs]]:
        """
        Cluster videos by common title prefix.

        Args:
            normalized_videos: List of (VideoKPIs, normalized_title) tuples

        Returns:
            Dict of prefix -> list of videos
        """
        clusters = defaultdict(list)

        for video, norm_title in normalized_videos:
            # Extract first 3 words as prefix
            words = norm_title.split()
            if len(words) >= 3:
                prefix = ' '.join(words[:3])
                clusters[prefix].append(video)

        # Filter out single-video "clusters"
        return {k: v for k, v in clusters.items() if len(v) >= 2}

    def _cluster_by_keywords(
        self,
        normalized_videos: List[Tuple[VideoKPIs, str]]
    ) -> Dict[str, List[VideoKPIs]]:
        """
        Cluster videos by common keywords and duration bucket.

        Args:
            normalized_videos: List of (VideoKPIs, normalized_title) tuples

        Returns:
            Dict of keyword+duration -> list of videos
        """
        # Extract keywords from all titles
        all_keywords = []
        for _, norm_title in normalized_videos:
            words = norm_title.split()
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but'}
            keywords = [w for w in words if len(w) > 3 and w not in stop_words]
            all_keywords.extend(keywords)

        # Find most common keywords (potential series markers)
        keyword_counts = Counter(all_keywords)
        common_keywords = {kw for kw, count in keyword_counts.items() if count >= 2}

        # Cluster by keyword + duration
        clusters = defaultdict(list)

        for video, norm_title in normalized_videos:
            words = norm_title.split()
            video_keywords = set(words) & common_keywords

            if video_keywords:
                # Use most common keyword + duration bucket as cluster key
                main_keyword = sorted(
                    video_keywords,
                    key=lambda k: keyword_counts[k],
                    reverse=True
                )[0]

                cluster_key = f"{main_keyword}_{video.duration_bucket}"
                clusters[cluster_key].append(video)

        return {k: v for k, v in clusters.items() if len(v) >= 2}

    def _cluster_by_episodes(
        self,
        normalized_videos: List[Tuple[VideoKPIs, str]]
    ) -> Dict[str, List[VideoKPIs]]:
        """
        Cluster videos with episode/part numbers.

        Args:
            normalized_videos: List of (VideoKPIs, normalized_title) tuples

        Returns:
            Dict of series_name -> list of videos
        """
        clusters = defaultdict(list)

        # Patterns for episode numbers
        episode_patterns = [
            r'\bep\s*\d+',  # "ep 1", "ep1"
            r'\bepisode\s*\d+',  # "episode 1"
            r'\bpart\s*\d+',  # "part 1"
            r'\#\d+',  # "#1"
            r'\s\d+\s',  # " 1 " (surrounded by spaces)
        ]

        for video, norm_title in normalized_videos:
            for pattern in episode_patterns:
                match = re.search(pattern, norm_title)
                if match:
                    # Extract series name (everything before the episode marker)
                    series_name = norm_title[:match.start()].strip()
                    if len(series_name) > 5:  # Must have meaningful series name
                        clusters[series_name].append(video)
                    break  # Only match first pattern

        return {k: v for k, v in clusters.items() if len(v) >= self.min_cluster_size}

    def _create_cluster(
        self,
        cluster_id: str,
        videos: List[VideoKPIs]
    ) -> FormatCluster:
        """
        Create a FormatCluster from a group of videos.

        Args:
            cluster_id: Unique cluster identifier
            videos: List of videos in this cluster

        Returns:
            FormatCluster object
        """
        if not videos:
            return None

        # Calculate median KPIs
        views = [v.views for v in videos]
        view_velocities = [v.view_velocity for v in videos]
        like_rates = [v.like_rate for v in videos]
        comment_rates = [v.comment_rate for v in videos]
        engagement_scores = [v.engagement_score for v in videos]
        durations = [v.duration_seconds for v in videos]

        median_views = float(np.median(views))
        median_view_velocity = float(np.median(view_velocities))
        median_like_rate = float(np.median(like_rates))
        median_comment_rate = float(np.median(comment_rates))
        median_engagement_score = float(np.median(engagement_scores))
        avg_duration = float(np.mean(durations))

        # Find best performing video
        best_video = max(videos, key=lambda v: v.engagement_score)

        # Extract common keywords from titles
        all_words = []
        for video in videos:
            words = self._normalize_title(video.title).split()
            all_words.extend(words)

        word_counts = Counter(all_words)
        common_keywords = [
            word for word, count in word_counts.most_common(5)
            if count >= len(videos) * 0.5  # Appears in at least 50% of videos
        ]

        # Determine dominant duration bucket
        duration_buckets = [v.duration_bucket for v in videos]
        duration_bucket = Counter(duration_buckets).most_common(1)[0][0]

        # Generate pattern name and description
        pattern_name = self._generate_pattern_name(cluster_id, videos)
        description = self._generate_description(videos, common_keywords)

        # Sample titles (up to 5)
        sample_titles = [v.title for v in videos[:5]]

        return FormatCluster(
            cluster_id=cluster_id,
            pattern_name=pattern_name,
            description=description,
            video_count=len(videos),
            video_ids=[v.video_id for v in videos],
            sample_titles=sample_titles,
            best_video_id=best_video.video_id,
            best_video_title=best_video.title,
            median_views=round(median_views, 0),
            median_view_velocity=round(median_view_velocity, 2),
            median_like_rate=round(median_like_rate, 6),
            median_comment_rate=round(median_comment_rate, 6),
            median_engagement_score=round(median_engagement_score, 2),
            common_keywords=common_keywords,
            duration_bucket=duration_bucket,
            avg_duration_seconds=round(avg_duration, 0),
        )

    def _generate_pattern_name(self, cluster_id: str, videos: List[VideoKPIs]) -> str:
        """
        Generate a human-readable pattern name.

        Args:
            cluster_id: Cluster identifier
            videos: Videos in cluster

        Returns:
            Pattern name string
        """
        # Extract prefix/keyword from cluster_id
        parts = cluster_id.split('_', 1)
        if len(parts) > 1:
            pattern_type, pattern_key = parts
            # Clean up pattern key
            pattern_key = pattern_key.replace('_', ' ').title()
            return f"{pattern_key} Series"

        return f"Pattern {cluster_id[:20]}"

    def _generate_description(
        self,
        videos: List[VideoKPIs],
        common_keywords: List[str]
    ) -> str:
        """
        Generate cluster description.

        Args:
            videos: Videos in cluster
            common_keywords: Common keywords

        Returns:
            Description string
        """
        duration_bucket = Counter([v.duration_bucket for v in videos]).most_common(1)[0][0]
        duration_desc = {
            'short': 'Short-form videos',
            'medium': 'Medium-length videos',
            'long': 'Long-form videos'
        }.get(duration_bucket, 'Videos')

        keyword_str = ', '.join(common_keywords[:3]) if common_keywords else 'recurring theme'

        return f"{duration_desc} featuring {keyword_str}"
