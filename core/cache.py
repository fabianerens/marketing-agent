"""
SQLite-based caching for YouTube API responses.

Caches:
- Channel info
- Video lists
- Video details

TTL: 12 hours (configurable)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CacheManager:
    """SQLite cache manager with TTL support."""

    def __init__(self, db_path: str = "./data/cache.db", ttl_hours: int = 12):
        """
        Initialize cache manager.

        Args:
            db_path: Path to SQLite database file
            ttl_hours: Time-to-live in hours for cached entries
        """
        self.db_path = db_path
        self.ttl_hours = ttl_hours

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Channel cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel_cache (
                    channel_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL
                )
            """)

            # Video list cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_list_cache (
                    cache_key TEXT PRIMARY KEY,
                    video_ids TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL
                )
            """)

            # Video details cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_cache (
                    video_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_channel_cached_at
                ON channel_cache(cached_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_cached_at
                ON video_cache(cached_at)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _is_expired(self, cached_at: str) -> bool:
        """
        Check if a cache entry is expired.

        Args:
            cached_at: ISO format timestamp string

        Returns:
            True if expired
        """
        cached_time = datetime.fromisoformat(cached_at)
        age = datetime.utcnow() - cached_time
        return age > timedelta(hours=self.ttl_hours)

    def get_channel(self, channel_id: str) -> Optional[dict]:
        """
        Get cached channel info.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel data dict or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT data, cached_at FROM channel_cache WHERE channel_id = ?",
                    (channel_id,)
                )
                row = cursor.fetchone()

                if row and not self._is_expired(row['cached_at']):
                    return json.loads(row['data'])

                # Clean up expired entry
                if row:
                    cursor.execute("DELETE FROM channel_cache WHERE channel_id = ?", (channel_id,))
                    conn.commit()

        except Exception as e:
            logger.error(f"Error reading channel cache: {e}")

        return None

    def set_channel(self, channel_id: str, data: dict):
        """
        Cache channel info.

        Args:
            channel_id: YouTube channel ID
            data: Channel data dict
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO channel_cache (channel_id, data, cached_at)
                    VALUES (?, ?, ?)
                    """,
                    (channel_id, json.dumps(data), datetime.utcnow().isoformat())
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error writing channel cache: {e}")

    def get_video_list(self, cache_key: str) -> Optional[List[str]]:
        """
        Get cached video ID list.

        Args:
            cache_key: Unique key for this video list query

        Returns:
            List of video IDs or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT video_ids, cached_at FROM video_list_cache WHERE cache_key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()

                if row and not self._is_expired(row['cached_at']):
                    return json.loads(row['video_ids'])

                # Clean up expired entry
                if row:
                    cursor.execute("DELETE FROM video_list_cache WHERE cache_key = ?", (cache_key,))
                    conn.commit()

        except Exception as e:
            logger.error(f"Error reading video list cache: {e}")

        return None

    def set_video_list(self, cache_key: str, video_ids: List[str]):
        """
        Cache video ID list.

        Args:
            cache_key: Unique key for this video list query
            video_ids: List of video IDs
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO video_list_cache (cache_key, video_ids, cached_at)
                    VALUES (?, ?, ?)
                    """,
                    (cache_key, json.dumps(video_ids), datetime.utcnow().isoformat())
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error writing video list cache: {e}")

    def get_video(self, video_id: str) -> Optional[dict]:
        """
        Get cached video details.

        Args:
            video_id: YouTube video ID

        Returns:
            Video data dict or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT data, cached_at FROM video_cache WHERE video_id = ?",
                    (video_id,)
                )
                row = cursor.fetchone()

                if row and not self._is_expired(row['cached_at']):
                    return json.loads(row['data'])

                # Clean up expired entry
                if row:
                    cursor.execute("DELETE FROM video_cache WHERE video_id = ?", (video_id,))
                    conn.commit()

        except Exception as e:
            logger.error(f"Error reading video cache: {e}")

        return None

    def set_video(self, video_id: str, data: dict):
        """
        Cache video details.

        Args:
            video_id: YouTube video ID
            data: Video data dict
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO video_cache (video_id, data, cached_at)
                    VALUES (?, ?, ?)
                    """,
                    (video_id, json.dumps(data), datetime.utcnow().isoformat())
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error writing video cache: {e}")

    def clear_expired(self):
        """Remove all expired cache entries."""
        try:
            cutoff = (datetime.utcnow() - timedelta(hours=self.ttl_hours)).isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM channel_cache WHERE cached_at < ?", (cutoff,))
                cursor.execute("DELETE FROM video_list_cache WHERE cached_at < ?", (cutoff,))
                cursor.execute("DELETE FROM video_cache WHERE cached_at < ?", (cutoff,))

                deleted = cursor.rowcount
                conn.commit()

                logger.info(f"Cleared {deleted} expired cache entries")

        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")

    def clear_all(self):
        """Clear all cache entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM channel_cache")
                cursor.execute("DELETE FROM video_list_cache")
                cursor.execute("DELETE FROM video_cache")
                conn.commit()

                logger.info("Cleared all cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
