"""
Tests for KPI calculation.
"""

import pytest
from datetime import datetime, timedelta
from core.models import VideoData
from core.kpi import KPICalculator


def test_kpi_calculation_basic():
    """Test basic KPI calculation for a video."""
    # Create test video
    published = datetime.utcnow() - timedelta(days=10)
    video = VideoData(
        video_id="test123",
        title="Test Video",
        published_at=published,
        duration_seconds=300,
        view_count=10000,
        like_count=500,
        comment_count=100,
    )

    calculator = KPICalculator()
    kpis = calculator.calculate_video_kpis(video)

    # Assertions
    assert kpis.video_id == "test123"
    assert kpis.views == 10000
    assert kpis.likes == 500
    assert kpis.comments == 100

    # View velocity should be ~1000 views/day
    assert 900 < kpis.view_velocity < 1100

    # Like rate should be 0.05 (5%)
    assert abs(kpis.like_rate - 0.05) < 0.001

    # Comment rate should be 0.01 (1%)
    assert abs(kpis.comment_rate - 0.01) < 0.001

    # Engagement score should be calculated
    assert kpis.engagement_score > 0


def test_kpi_duration_categorization():
    """Test duration bucket categorization."""
    calculator = KPICalculator()
    published = datetime.utcnow() - timedelta(days=1)

    # Short video (<= 60s)
    short_video = VideoData(
        video_id="short",
        title="Short",
        published_at=published,
        duration_seconds=30,
        view_count=1000,
        like_count=50,
        comment_count=10,
    )
    kpis = calculator.calculate_video_kpis(short_video)
    assert kpis.is_short is True
    assert kpis.duration_bucket == "short"

    # Medium video (60s - 600s)
    medium_video = VideoData(
        video_id="medium",
        title="Medium",
        published_at=published,
        duration_seconds=300,
        view_count=1000,
        like_count=50,
        comment_count=10,
    )
    kpis = calculator.calculate_video_kpis(medium_video)
    assert kpis.is_short is False
    assert kpis.duration_bucket == "medium"

    # Long video (> 600s)
    long_video = VideoData(
        video_id="long",
        title="Long",
        published_at=published,
        duration_seconds=1800,
        view_count=1000,
        like_count=50,
        comment_count=10,
    )
    kpis = calculator.calculate_video_kpis(long_video)
    assert kpis.is_short is False
    assert kpis.duration_bucket == "long"


def test_kpi_zero_views_handling():
    """Test KPI calculation with zero views (edge case)."""
    published = datetime.utcnow() - timedelta(days=1)
    video = VideoData(
        video_id="zero",
        title="Zero Views",
        published_at=published,
        duration_seconds=300,
        view_count=0,
        like_count=0,
        comment_count=0,
    )

    calculator = KPICalculator()
    kpis = calculator.calculate_video_kpis(video)

    # Should not crash
    assert kpis.views == 0
    assert kpis.like_rate == 0
    assert kpis.comment_rate == 0
    assert kpis.view_velocity == 0


def test_kpi_filtering():
    """Test video filtering by KPIs."""
    calculator = KPICalculator()
    published = datetime.utcnow() - timedelta(days=1)

    videos = [
        VideoData(
            video_id=f"vid{i}",
            title=f"Video {i} Test Keyword" if i % 2 == 0 else f"Video {i}",
            published_at=published,
            duration_seconds=300,
            view_count=i * 1000,
            like_count=i * 50,
            comment_count=i * 10,
        )
        for i in range(1, 6)
    ]

    video_kpis = calculator.calculate_batch_kpis(videos)

    # Filter by min_views
    filtered = calculator.filter_by_kpis(video_kpis, min_views=3000)
    assert len(filtered) == 3  # Videos 3, 4, 5

    # Filter by excluded keywords
    filtered = calculator.filter_by_kpis(video_kpis, exclude_keywords=["test", "keyword"])
    assert len(filtered) == 3  # Odd-numbered videos (1, 3, 5)


def test_kpi_ranking():
    """Test video ranking by metrics."""
    calculator = KPICalculator()
    published = datetime.utcnow() - timedelta(days=1)

    videos = [
        VideoData(
            video_id=f"vid{i}",
            title=f"Video {i}",
            published_at=published,
            duration_seconds=300,
            view_count=(6 - i) * 1000,  # Descending views
            like_count=i * 50,  # Ascending likes
            comment_count=i * 10,
        )
        for i in range(1, 6)
    ]

    video_kpis = calculator.calculate_batch_kpis(videos)

    # Rank by views (descending)
    ranked = calculator.rank_by_metric(video_kpis, metric="views", top_n=3)
    assert len(ranked) == 3
    assert ranked[0].video_id == "vid1"  # Most views
    assert ranked[1].video_id == "vid2"
    assert ranked[2].video_id == "vid3"

    # Rank by like_rate (descending)
    ranked = calculator.rank_by_metric(video_kpis, metric="like_rate")
    assert len(ranked) == 5
    # vid5 should have highest like_rate (50*5 / 1000 = 0.25)
    assert ranked[0].video_id == "vid5"


def test_kpi_custom_weights():
    """Test KPI calculation with custom engagement weights."""
    published = datetime.utcnow() - timedelta(days=1)
    video = VideoData(
        video_id="test",
        title="Test",
        published_at=published,
        duration_seconds=300,
        view_count=10000,
        like_count=500,
        comment_count=100,
    )

    # Like-heavy weighting
    calc1 = KPICalculator(like_weight=0.9, comment_weight=0.1)
    kpis1 = calc1.calculate_video_kpis(video)

    # Comment-heavy weighting
    calc2 = KPICalculator(like_weight=0.1, comment_weight=0.9)
    kpis2 = calc2.calculate_video_kpis(video)

    # Both should calculate, but engagement scores will differ
    assert kpis1.engagement_score > 0
    assert kpis2.engagement_score > 0
    # Like-heavy should be higher (since like_rate > comment_rate in this case)
    assert kpis1.engagement_score > kpis2.engagement_score
