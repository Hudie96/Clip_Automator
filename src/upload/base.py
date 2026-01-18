"""
Abstract base class for social media uploaders.

All platform-specific uploaders should inherit from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import time
import logging

logger = logging.getLogger(__name__)


class UploadStatus(Enum):
    """Status of an upload operation."""
    PENDING = "pending"
    AUTHENTICATING = "authenticating"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class UploadResult:
    """Result of an upload operation."""
    success: bool
    platform: str
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 1
    upload_time_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __str__(self):
        if self.success:
            return f"[{self.platform}] Upload successful: {self.video_url}"
        return f"[{self.platform}] Upload failed: {self.error_message}"


class Uploader(ABC):
    """
    Abstract base class for platform uploaders.

    Subclasses must implement:
        - authenticate(): Set up API credentials
        - upload(): Upload a video to the platform
    """

    PLATFORM_NAME: str = "unknown"
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5

    def __init__(self):
        self._status = UploadStatus.PENDING
        self._authenticated = False
        self._last_error: Optional[str] = None

    @property
    def status(self) -> UploadStatus:
        """Current upload status."""
        return self._status

    @property
    def is_authenticated(self) -> bool:
        """Whether the uploader has valid credentials."""
        return self._authenticated

    @property
    def last_error(self) -> Optional[str]:
        """Last error message, if any."""
        return self._last_error

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform API.

        Returns:
            True if authentication successful, False otherwise.
        """
        pass

    @abstractmethod
    def _do_upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> UploadResult:
        """
        Platform-specific upload implementation.

        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags/keywords

        Returns:
            UploadResult with success/failure info
        """
        pass

    def upload(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> UploadResult:
        """
        Upload a video with automatic retry on failure.

        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags/keywords (optional)

        Returns:
            UploadResult with upload details
        """
        tags = tags or []
        attempts = 0
        last_result = None
        start_time = time.time()

        while attempts < self.MAX_RETRIES:
            attempts += 1

            try:
                # Ensure authenticated
                if not self._authenticated:
                    self._status = UploadStatus.AUTHENTICATING
                    if not self.authenticate():
                        return UploadResult(
                            success=False,
                            platform=self.PLATFORM_NAME,
                            error_message=f"Authentication failed: {self._last_error}",
                            attempts=attempts
                        )

                # Attempt upload
                self._status = UploadStatus.UPLOADING
                logger.info(f"[{self.PLATFORM_NAME}] Upload attempt {attempts}/{self.MAX_RETRIES}")

                result = self._do_upload(video_path, title, description, tags)
                result.attempts = attempts
                result.upload_time_seconds = time.time() - start_time

                if result.success:
                    self._status = UploadStatus.COMPLETED
                    logger.info(f"[{self.PLATFORM_NAME}] Upload successful: {result.video_url}")
                    return result

                last_result = result
                self._last_error = result.error_message

            except Exception as e:
                self._last_error = str(e)
                logger.error(f"[{self.PLATFORM_NAME}] Upload error: {e}")
                last_result = UploadResult(
                    success=False,
                    platform=self.PLATFORM_NAME,
                    error_message=str(e),
                    attempts=attempts
                )

            # Retry logic
            if attempts < self.MAX_RETRIES:
                self._status = UploadStatus.RETRY
                logger.info(f"[{self.PLATFORM_NAME}] Retrying in {self.RETRY_DELAY_SECONDS}s...")
                time.sleep(self.RETRY_DELAY_SECONDS)

        # All retries exhausted
        self._status = UploadStatus.FAILED
        if last_result:
            last_result.upload_time_seconds = time.time() - start_time
            return last_result

        return UploadResult(
            success=False,
            platform=self.PLATFORM_NAME,
            error_message="Upload failed after all retries",
            attempts=attempts,
            upload_time_seconds=time.time() - start_time
        )

    def validate_video(self, video_path: str) -> tuple[bool, str]:
        """
        Validate that a video file exists and is uploadable.

        Args:
            video_path: Path to the video file

        Returns:
            Tuple of (is_valid, error_message)
        """
        import os

        if not os.path.exists(video_path):
            return False, f"Video file not found: {video_path}"

        if not os.path.isfile(video_path):
            return False, f"Path is not a file: {video_path}"

        # Check file extension
        valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        ext = os.path.splitext(video_path)[1].lower()
        if ext not in valid_extensions:
            return False, f"Invalid video format: {ext}. Supported: {valid_extensions}"

        # Check file size (basic check)
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if size_mb < 0.1:
            return False, f"Video file too small ({size_mb:.2f} MB)"

        return True, ""
