"""
YouTube Data API v3 Client.

This module handles all interactions with the YouTube Data API:
- Channel resolution (URL -> channel_id)
- Video list retrieval
- Video details/statistics fetching
- Rate limit handling
"""

import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import ChannelInfo, VideoData

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Client for YouTube Data API v3."""

    def __init__(self, api_key: str):
        """
        Initialize YouTube API client.

        Args:
            api_key: YouTube Data API v3 key
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def resolve_channel_id(self, identifier: str) -> Optional[str]:
        """
        Resolve various channel identifiers to channel_id.

        Supports:
        - Channel URLs: https://www.youtube.com/channel/UC...
        - Custom URLs: https://www.youtube.com/c/channelname
        - User URLs: https://www.youtube.com/@username
        - Handles: @username
        - Direct channel IDs: UC...

        Args:
            identifier: Channel URL

        Returns:
            Channel ID or None if not found
        """
        try:
            # Direct channel ID
            if identifier.startswith('UC') and len(identifier) == 24:
                return identifier

            # Extract from URL
            if 'youtube.com' in identifier:
                # Channel URL: /channel/UC...
                match = re.search(r'/channel/([^/?]+)', identifier)
                if match:
                    return match.group(1)

                # Custom URL: /c/name or /@handle
                match = re.search(r'/(c|@)/([^/?]+)', identifier)
                if match:
                    username = match.group(2)
                    return self._resolve_username(username)

                # User URL: /user/name
                match = re.search(r'/user/([^/?]+)', identifier)
                if match:
                    username = match.group(1)
                    return self._resolve_username(username)

            # Handle: @username
            if identifier.startswith('@'):
                username = identifier[1:]
                return self._resolve_username(username)

            # Try as custom username
            return self._resolve_username(identifier)

        except Exception as e:
            logger.error(f"Error resolving channel ID for '{identifier}': {e}")
            return None

    def _resolve_username(self, username: str) -> Optional[str]:
        """
        Resolve username/handle to channel_id via search.

        Args:
            username: Username or handle (without @)

        Returns:
            Channel ID or None
        """
        try:
            # Try forUsername parameter (legacy)
            request = self.youtube.channels().list(
                part='id',
                forUsername=username,
                maxResults=1
            )
            response = request.execute()

            if response.get('items'):
                return response['items'][0]['id']

            # Try search API as fallback
            request = self.youtube.search().list(
                part='snippet',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()

            if response.get('items'):
                return response['items'][0]['snippet']['channelId']

            return None

        except HttpError as e:
            logger.error(f"HTTP error resolving username '{username}': {e}")
            return None

    def get_channel_info(self, channel_id: str) -> Optional[ChannelInfo]:
        """
        Get detailed channel information.

        Args:
            channel_id: YouTube channel ID

        Returns:
            ChannelInfo object or None
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()

            if not response.get('items'):
                return None

            item = response['items'][0]
            snippet = item.get('snippet', {})
            stats = item.get('statistics', {})

            return ChannelInfo(
                channel_id=channel_id,
                title=snippet.get('title', ''),
                description=snippet.get('description'),
                subscriber_count=int(stats.get('subscriberCount', 0)),
                video_count=int(stats.get('videoCount', 0)),
                view_count=int(stats.get('viewCount', 0)),
                thumbnail_url=snippet.get('thumbnails', {}).get('default', {}).get('url'),
                custom_url=snippet.get('customUrl'),
            )

        except HttpError as e:
            logger.error(f"HTTP error getting channel info: {e}")
            return None

    def get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """
        Get the uploads playlist ID for a channel.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Uploads playlist ID or None
        """
        try:
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()

            if response.get('items'):
                return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            return None

        except HttpError as e:
            logger.error(f"HTTP error getting uploads playlist: {e}")
            return None

    def get_video_ids_from_playlist(
        self,
        playlist_id: str,
        max_results: int = 50,
        days_back: Optional[int] = None
    ) -> List[str]:
        """
        Get video IDs from a playlist (usually uploads).

        Args:
            playlist_id: Playlist ID
            max_results: Maximum number of videos to fetch
            days_back: Only fetch videos from last N days (optional)

        Returns:
            List of video IDs
        """
        video_ids = []
        cutoff_date = None

        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        try:
            next_page_token = None

            while len(video_ids) < max_results:
                request = self.youtube.playlistItems().list(
                    part='contentDetails,snippet',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']

                    # Check date filter
                    if cutoff_date:
                        published_str = item['snippet']['publishedAt']
                        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                        if published < cutoff_date:
                            return video_ids  # Stop, we've gone too far back

                    video_ids.append(video_id)

                    if len(video_ids) >= max_results:
                        break

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

        except HttpError as e:
            logger.error(f"HTTP error fetching playlist items: {e}")

        return video_ids

    def get_video_details(self, video_ids: List[str]) -> List[VideoData]:
        """
        Get detailed information for multiple videos.

        Fetches in batches of 50 (API limit).

        Args:
            video_ids: List of video IDs

        Returns:
            List of VideoData objects
        """
        videos = []
        batch_size = 50

        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            videos.extend(self._fetch_video_batch(batch))

        return videos

    def _fetch_video_batch(self, video_ids: List[str]) -> List[VideoData]:
        """
        Fetch a batch of video details (max 50).

        Args:
            video_ids: List of video IDs (max 50)

        Returns:
            List of VideoData objects
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            )
            response = request.execute()

            videos = []
            for item in response.get('items', []):
                try:
                    snippet = item.get('snippet', {})
                    stats = item.get('statistics', {})
                    content = item.get('contentDetails', {})

                    # Parse duration
                    duration_str = content.get('duration', 'PT0S')
                    duration = isodate.parse_duration(duration_str)
                    duration_seconds = int(duration.total_seconds())

                    # Parse published date
                    published_str = snippet.get('publishedAt', '')
                    published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))

                    video_data = VideoData(
                        video_id=item['id'],
                        title=snippet.get('title', ''),
                        description=snippet.get('description'),
                        published_at=published,
                        duration_seconds=duration_seconds,
                        view_count=int(stats.get('viewCount', 0)),
                        like_count=int(stats.get('likeCount', 0)),
                        comment_count=int(stats.get('commentCount', 0)),
                        thumbnail_url=snippet.get('thumbnails', {}).get('default', {}).get('url'),
                        tags=snippet.get('tags', []),
                        category_id=snippet.get('categoryId'),
                    )
                    videos.append(video_data)

                except Exception as e:
                    logger.warning(f"Error parsing video {item.get('id')}: {e}")
                    continue

            return videos

        except HttpError as e:
            logger.error(f"HTTP error fetching video batch: {e}")
            return []

    def get_channel_videos(
        self,
        channel_id: str,
        max_videos: int = 30,
        days_back: Optional[int] = None
    ) -> List[VideoData]:
        """
        Get videos from a channel with details.

        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos
            days_back: Only fetch videos from last N days (optional)

        Returns:
            List of VideoData objects
        """
        # Get uploads playlist
        playlist_id = self.get_uploads_playlist_id(channel_id)
        if not playlist_id:
            logger.error(f"Could not find uploads playlist for channel {channel_id}")
            return []

        # Get video IDs
        video_ids = self.get_video_ids_from_playlist(playlist_id, max_videos, days_back)
        if not video_ids:
            logger.warning(f"No videos found for channel {channel_id}")
            return []

        # Get video details
        videos = self.get_video_details(video_ids)
        logger.info(f"Fetched {len(videos)} videos for channel {channel_id}")

        return videos
