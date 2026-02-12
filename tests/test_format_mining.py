"""
Tests for format mining and clustering.
"""

import pytest
from datetime import datetime, timedelta
from core.models import VideoKPIs
from core.format_mining import FormatMiner


def create_test_video_kpi(
    video_id: str,
    title: str,
    views: int = 1000,
    duration_seconds: int = 300,
    age_days: float = 10.0,
) -> VideoKPIs:
    """Helper to create test VideoKPIs."""
    published = datetime.utcnow() - timedelta(days=age_days)
    return VideoKPIs(
        video_id=video_id,
        title=title,
        published_at=published,
        age_days=age_days,
        duration_seconds=duration_seconds,
        is_short=duration_seconds <= 60,
        views=views,
        likes=int(views * 0.05),
        comments=int(views * 0.01),
        view_velocity=views / age_days,
        like_rate=0.05,
        comment_rate=0.01,
        engagement_score=views * 0.06,
        duration_bucket="medium" if 60 < duration_seconds <= 600 else "short" if duration_seconds <= 60 else "long",
    )


def test_title_normalization():
    """Test title normalization removes emojis and punctuation."""
    miner = FormatMiner()

    # Test emoji removal
    normalized = miner._normalize_title("🔥 Amazing Video!!! 💯")
    assert "🔥" not in normalized
    assert "💯" not in normalized
    assert "amazing video" in normalized.lower()

    # Test punctuation handling
    normalized = miner._normalize_title("How to Code: Python (Part 1)")
    assert "how to code python part 1" in normalized.lower()

    # Test multiple spaces collapsed
    normalized = miner._normalize_title("Test    Video    Title")
    assert "test video title" in normalized.lower()


def test_prefix_clustering():
    """Test clustering by title prefix."""
    miner = FormatMiner()

    videos = [
        create_test_video_kpi("1", "Series Name Episode 1", views=5000),
        create_test_video_kpi("2", "Series Name Episode 2", views=6000),
        create_test_video_kpi("3", "Series Name Episode 3", views=5500),
        create_test_video_kpi("4", "Other Video Title", views=3000),
        create_test_video_kpi("5", "Another Random Video", views=2000),
    ]

    formats = miner.find_formats(videos)

    # Should find at least one cluster (the "Series Name" videos)
    assert len(formats) >= 1

    # The series cluster should have 3 videos
    series_cluster = next((f for f in formats if f.video_count == 3), None)
    assert series_cluster is not None
    assert "1" in series_cluster.video_ids
    assert "2" in series_cluster.video_ids
    assert "3" in series_cluster.video_ids


def test_episode_number_clustering():
    """Test clustering by episode numbers."""
    miner = FormatMiner()

    videos = [
        create_test_video_kpi("1", "Tutorial Part 1", views=5000),
        create_test_video_kpi("2", "Tutorial Part 2", views=6000),
        create_test_video_kpi("3", "Tutorial Part 3", views=5500),
        create_test_video_kpi("4", "Random Video", views=3000),
    ]

    formats = miner.find_formats(videos)

    # Should detect the "Part X" pattern
    assert len(formats) >= 1

    # Find cluster with the tutorial videos
    tutorial_cluster = next(
        (f for f in formats if f.video_count == 3),
        None
    )
    assert tutorial_cluster is not None


def test_keyword_clustering():
    """Test clustering by common keywords."""
    miner = FormatMiner()

    videos = [
        create_test_video_kpi("1", "Python Tutorial for Beginners", views=5000, duration_seconds=600),
        create_test_video_kpi("2", "Python Tutorial Advanced", views=6000, duration_seconds=600),
        create_test_video_kpi("3", "Python Tutorial Intermediate", views=5500, duration_seconds=600),
        create_test_video_kpi("4", "JavaScript Basics", views=3000, duration_seconds=400),
        create_test_video_kpi("5", "Random Vlog", views=2000, duration_seconds=300),
    ]

    formats = miner.find_formats(videos)

    # Should find Python tutorial cluster
    assert len(formats) >= 1

    # Python cluster should have 3 videos
    python_cluster = next((f for f in formats if f.video_count == 3), None)
    assert python_cluster is not None
    assert any(kw in ["python", "tutorial"] for kw in python_cluster.common_keywords)


def test_min_cluster_size():
    """Test minimum cluster size enforcement."""
    # Require at least 4 videos per cluster
    miner = FormatMiner(min_cluster_size=4)

    videos = [
        create_test_video_kpi("1", "Series Ep 1", views=5000),
        create_test_video_kpi("2", "Series Ep 2", views=6000),
        create_test_video_kpi("3", "Series Ep 3", views=5500),  # Only 3 videos
        create_test_video_kpi("4", "Other Video", views=3000),
    ]

    formats = miner.find_formats(videos)

    # Should not find any clusters (only 3 similar videos, need 4)
    assert len(formats) == 0


def test_cluster_kpi_aggregation():
    """Test that cluster aggregates KPIs correctly."""
    miner = FormatMiner()

    videos = [
        create_test_video_kpi("1", "Tutorial Part 1", views=1000),
        create_test_video_kpi("2", "Tutorial Part 2", views=2000),
        create_test_video_kpi("3", "Tutorial Part 3", views=3000),
        create_test_video_kpi("4", "Tutorial Part 4", views=4000),
    ]

    formats = miner.find_formats(videos)

    assert len(formats) >= 1

    cluster = formats[0]

    # Median views should be 2500 (median of 1000, 2000, 3000, 4000)
    assert 2400 <= cluster.median_views <= 2600

    # Best video should be the one with highest engagement score
    assert cluster.best_video_id in ["3", "4"]  # Higher views = higher engagement

    # Should have sample titles
    assert len(cluster.sample_titles) > 0


def test_empty_input():
    """Test behavior with empty or insufficient input."""
    miner = FormatMiner(min_cluster_size=3)

    # Empty list
    formats = miner.find_formats([])
    assert len(formats) == 0

    # Too few videos
    videos = [
        create_test_video_kpi("1", "Video 1", views=1000),
        create_test_video_kpi("2", "Video 2", views=2000),
    ]
    formats = miner.find_formats(videos)
    assert len(formats) == 0


def test_duration_bucket_in_cluster():
    """Test that duration bucket is considered in clustering."""
    miner = FormatMiner()

    # Same keywords, but different duration buckets
    videos = [
        create_test_video_kpi("1", "Quick Tutorial Python", views=5000, duration_seconds=50),  # short
        create_test_video_kpi("2", "Quick Tutorial Python", views=5000, duration_seconds=50),  # short
        create_test_video_kpi("3", "Quick Tutorial Python", views=5000, duration_seconds=50),  # short
        create_test_video_kpi("4", "Quick Tutorial Python", views=5000, duration_seconds=900),  # long
        create_test_video_kpi("5", "Quick Tutorial Python", views=5000, duration_seconds=900),  # long
        create_test_video_kpi("6", "Quick Tutorial Python", views=5000, duration_seconds=900),  # long
    ]

    formats = miner.find_formats(videos)

    # Should potentially create separate clusters for short vs long
    # (depending on the clustering algorithm)
    assert len(formats) >= 1
