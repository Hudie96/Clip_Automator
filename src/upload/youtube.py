"""
YouTube uploader using Google API Python Client.

Requires:
    - google-api-python-client
    - google-auth-oauthlib

Setup:
    1. Create a project in Google Cloud Console
    2. Enable YouTube Data API v3
    3. Create OAuth 2.0 credentials (Desktop app)
    4. Download credentials and save to config/youtube_credentials.json
    5. Run the uploader once to complete OAuth flow

Documentation:
    https://developers.google.com/youtube/v3/guides/uploading_a_video
"""

import os
import json
import logging
from typing import List, Optional

from .base import Uploader, UploadResult, UploadStatus

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CREDENTIALS_FILE = "config/youtube_credentials.json"
DEFAULT_TOKEN_FILE = "config/youtube_token.json"

# YouTube API scopes
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_SCOPES = [YOUTUBE_UPLOAD_SCOPE]


class YouTubeUploader(Uploader):
    """
    YouTube video uploader using OAuth2.

    Usage:
        uploader = YouTubeUploader()
        if uploader.authenticate():
            result = uploader.upload(
                video_path="clip.mp4",
                title="My Clip",
                description="An awesome clip",
                tags=["gaming", "highlights"]
            )
            print(result.video_url)
    """

    PLATFORM_NAME = "youtube"

    # Privacy status options
    PRIVACY_PUBLIC = "public"
    PRIVACY_UNLISTED = "unlisted"
    PRIVACY_PRIVATE = "private"

    # Video categories (common ones)
    CATEGORY_GAMING = "20"
    CATEGORY_ENTERTAINMENT = "24"
    CATEGORY_PEOPLE_BLOGS = "22"

    def __init__(
        self,
        credentials_file: str = DEFAULT_CREDENTIALS_FILE,
        token_file: str = DEFAULT_TOKEN_FILE,
        default_privacy: str = PRIVACY_UNLISTED,
        default_category: str = CATEGORY_GAMING
    ):
        """
        Initialize YouTube uploader.

        Args:
            credentials_file: Path to OAuth client secrets JSON
            token_file: Path to store/load auth tokens
            default_privacy: Default privacy status for uploads
            default_category: Default video category ID
        """
        super().__init__()
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.default_privacy = default_privacy
        self.default_category = default_category
        self._youtube_service = None

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube using OAuth2.

        On first run, opens a browser for user authorization.
        Subsequent runs use the saved token.

        Returns:
            True if authentication successful
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError as e:
            self._last_error = (
                f"Missing required packages: {e}. "
                "Install with: pip install google-api-python-client google-auth-oauthlib"
            )
            logger.error(self._last_error)
            return False

        self._status = UploadStatus.AUTHENTICATING
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, YOUTUBE_SCOPES)
                logger.info("Loaded existing YouTube credentials")
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed YouTube credentials")
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                # Need new authorization
                if not os.path.exists(self.credentials_file):
                    self._last_error = (
                        f"Credentials file not found: {self.credentials_file}. "
                        "Download OAuth credentials from Google Cloud Console."
                    )
                    logger.error(self._last_error)
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, YOUTUBE_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Completed YouTube OAuth flow")
                except Exception as e:
                    self._last_error = f"OAuth flow failed: {e}"
                    logger.error(self._last_error)
                    return False

            # Save credentials for next run
            try:
                os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                with open(self.token_file, 'w') as f:
                    f.write(creds.to_json())
                logger.info(f"Saved YouTube credentials to {self.token_file}")
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        # Build YouTube service
        try:
            self._youtube_service = build('youtube', 'v3', credentials=creds)
            self._authenticated = True
            logger.info("YouTube API authenticated successfully")
            return True
        except Exception as e:
            self._last_error = f"Failed to build YouTube service: {e}"
            logger.error(self._last_error)
            return False

    def _do_upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> UploadResult:
        """
        Upload video to YouTube.

        Args:
            video_path: Path to video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            tags: List of tags

        Returns:
            UploadResult with video URL on success
        """
        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as e:
            return UploadResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Missing google-api-python-client: {e}"
            )

        # Validate video file
        is_valid, error = self.validate_video(video_path)
        if not is_valid:
            return UploadResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=error
            )

        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube limit
                'description': description[:5000],  # YouTube limit
                'tags': tags[:500],  # Reasonable limit
                'categoryId': self.default_category
            },
            'status': {
                'privacyStatus': self.default_privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        # Create media upload
        try:
            media = MediaFileUpload(
                video_path,
                mimetype='video/*',
                resumable=True,
                chunksize=256 * 1024  # 256KB chunks
            )
        except Exception as e:
            return UploadResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Failed to read video file: {e}"
            )

        # Execute upload
        try:
            request = self._youtube_service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            self._status = UploadStatus.UPLOADING

            # Resumable upload with progress
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"YouTube upload progress: {progress}%")

            video_id = response.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            logger.info(f"YouTube upload complete: {video_url}")

            return UploadResult(
                success=True,
                platform=self.PLATFORM_NAME,
                video_url=video_url,
                video_id=video_id,
                metadata={
                    'title': title,
                    'privacy': self.default_privacy,
                    'category': self.default_category
                }
            )

        except Exception as e:
            error_msg = str(e)

            # Parse common YouTube API errors
            if 'quotaExceeded' in error_msg:
                error_msg = "YouTube API quota exceeded. Try again tomorrow."
            elif 'uploadLimitExceeded' in error_msg:
                error_msg = "Daily upload limit exceeded."
            elif 'videoLengthExceeded' in error_msg:
                error_msg = "Video exceeds maximum length."
            elif 'invalidMetadata' in error_msg:
                error_msg = "Invalid video metadata (title, description, or tags)."

            return UploadResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=error_msg
            )

    def upload(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy: Optional[str] = None,
        category: Optional[str] = None
    ) -> UploadResult:
        """
        Upload video to YouTube with optional overrides.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            privacy: Override default privacy (public/unlisted/private)
            category: Override default category ID

        Returns:
            UploadResult with video URL on success
        """
        # Temporarily override defaults if provided
        orig_privacy = self.default_privacy
        orig_category = self.default_category

        if privacy:
            self.default_privacy = privacy
        if category:
            self.default_category = category

        try:
            return super().upload(video_path, title, description, tags)
        finally:
            # Restore defaults
            self.default_privacy = orig_privacy
            self.default_category = orig_category


if __name__ == "__main__":
    # Test authentication
    import sys

    logging.basicConfig(level=logging.INFO)

    uploader = YouTubeUploader()

    if uploader.authenticate():
        print("YouTube authentication successful!")
        print("You can now upload videos.")
    else:
        print(f"Authentication failed: {uploader.last_error}")
        sys.exit(1)
