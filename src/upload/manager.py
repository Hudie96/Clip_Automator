"""
Upload manager for coordinating uploads to multiple platforms.

Usage:
    from src.upload import UploadManager

    manager = UploadManager()
    results = manager.upload_clip(
        clip_path="clips/my_clip.mp4",
        platforms=["youtube"],
        title="My Awesome Clip",
        description="Check out this moment!"
    )

CLI Usage:
    python src/upload/manager.py --file clips/clip.mp4 --platform youtube
    python src/upload/manager.py --file clips/clip.mp4 --platform youtube --title "My Clip"
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.upload.base import UploadResult
from src.upload.youtube import YouTubeUploader
from src.upload.tiktok import TikTokUploader

logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "upload_config.json")


class UploadManager:
    """
    Manages uploads to multiple social media platforms.

    Features:
        - Upload to multiple platforms simultaneously
        - Auto-generate titles from filenames
        - Log results to database
        - Configurable via upload_config.json
    """

    SUPPORTED_PLATFORMS = {
        'youtube': YouTubeUploader,
        'tiktok': TikTokUploader
    }

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize upload manager.

        Args:
            config_path: Path to upload_config.json
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._uploaders: Dict[str, object] = {}

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")

        # Return default config
        return {
            "youtube": {
                "enabled": False,
                "credentials_file": "config/youtube_credentials.json",
                "default_privacy": "unlisted"
            },
            "tiktok": {
                "enabled": False,
                "note": "TikTok upload requires manual setup"
            },
            "auto_upload": False,
            "default_description": "Clipped by Clip Automater"
        }

    def _get_uploader(self, platform: str):
        """
        Get or create an uploader for the specified platform.

        Args:
            platform: Platform name (youtube, tiktok)

        Returns:
            Uploader instance or None if platform not supported
        """
        platform = platform.lower()

        if platform not in self.SUPPORTED_PLATFORMS:
            logger.error(f"Unsupported platform: {platform}")
            return None

        # Return cached uploader if exists
        if platform in self._uploaders:
            return self._uploaders[platform]

        # Create new uploader based on config
        platform_config = self.config.get(platform, {})

        if platform == 'youtube':
            uploader = YouTubeUploader(
                credentials_file=platform_config.get(
                    'credentials_file',
                    'config/youtube_credentials.json'
                ),
                default_privacy=platform_config.get('default_privacy', 'unlisted')
            )
        elif platform == 'tiktok':
            uploader = TikTokUploader()
        else:
            return None

        self._uploaders[platform] = uploader
        return uploader

    def _generate_title(self, clip_path: str) -> str:
        """
        Generate a title from the clip filename.

        Examples:
            clips/xqc_2024-01-15_12-30-00.mp4 -> "xqc 2024-01-15 12:30:00"
            clips/highlight_001.mp4 -> "highlight 001"

        Args:
            clip_path: Path to the clip file

        Returns:
            Generated title string
        """
        filename = os.path.splitext(os.path.basename(clip_path))[0]

        # Replace underscores and hyphens with spaces
        title = filename.replace('_', ' ').replace('-', ':')

        # Clean up multiple spaces
        title = ' '.join(title.split())

        return title.title()  # Title case

    def _log_to_database(
        self,
        clip_path: str,
        results: List[UploadResult]
    ):
        """
        Log upload results to the database.

        Args:
            clip_path: Path to the uploaded clip
            results: List of UploadResult objects
        """
        try:
            from src.db.schema import get_connection
        except ImportError:
            logger.warning("Database not available. Skipping log.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Ensure uploads table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_path TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    video_url TEXT,
                    video_id TEXT,
                    error_message TEXT,
                    attempts INTEGER,
                    upload_time_seconds REAL,
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert results
            for result in results:
                cursor.execute("""
                    INSERT INTO uploads
                    (clip_path, platform, success, video_url, video_id,
                     error_message, attempts, upload_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    clip_path,
                    result.platform,
                    result.success,
                    result.video_url,
                    result.video_id,
                    result.error_message,
                    result.attempts,
                    result.upload_time_seconds
                ))

            conn.commit()
            conn.close()
            logger.info(f"Logged {len(results)} upload result(s) to database")

        except Exception as e:
            logger.error(f"Failed to log to database: {e}")

    def upload_clip(
        self,
        clip_path: str,
        platforms: List[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[UploadResult]:
        """
        Upload a clip to one or more platforms.

        Args:
            clip_path: Path to the video clip
            platforms: List of platforms to upload to (default: ['youtube'])
            title: Video title (auto-generated from filename if not provided)
            description: Video description (uses config default if not provided)
            tags: List of tags/hashtags

        Returns:
            List of UploadResult objects (one per platform)
        """
        platforms = platforms or ['youtube']
        tags = tags or []

        # Generate title if not provided
        if not title:
            title = self._generate_title(clip_path)
            logger.info(f"Auto-generated title: {title}")

        # Use default description if not provided
        if not description:
            description = self.config.get(
                'default_description',
                'Clipped by Clip Automater'
            )

        results = []

        for platform in platforms:
            platform = platform.lower()

            # Check if platform is enabled
            platform_config = self.config.get(platform, {})
            if not platform_config.get('enabled', False):
                logger.warning(
                    f"Platform '{platform}' is disabled in config. "
                    f"Enable it in {self.config_path}"
                )
                results.append(UploadResult(
                    success=False,
                    platform=platform,
                    error_message=f"Platform '{platform}' is disabled in configuration"
                ))
                continue

            # Get uploader
            uploader = self._get_uploader(platform)
            if not uploader:
                results.append(UploadResult(
                    success=False,
                    platform=platform,
                    error_message=f"Unsupported platform: {platform}"
                ))
                continue

            # Perform upload
            logger.info(f"Uploading to {platform}: {clip_path}")
            result = uploader.upload(
                video_path=clip_path,
                title=title,
                description=description,
                tags=tags
            )
            results.append(result)

            if result.success:
                logger.info(f"[{platform}] Upload successful: {result.video_url}")
            else:
                logger.error(f"[{platform}] Upload failed: {result.error_message}")

        # Log results to database
        self._log_to_database(clip_path, results)

        return results

    def get_upload_history(self, limit: int = 10) -> List[dict]:
        """
        Get recent upload history from database.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of upload records
        """
        try:
            from src.db.schema import get_connection
        except ImportError:
            logger.warning("Database not available.")
            return []

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM uploads
                ORDER BY uploaded_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get upload history: {e}")
            return []


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Upload clips to social media platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Upload to YouTube (default)
    python src/upload/manager.py --file clips/clip.mp4

    # Upload with custom title
    python src/upload/manager.py --file clips/clip.mp4 --title "Epic Moment!"

    # Upload to multiple platforms
    python src/upload/manager.py --file clips/clip.mp4 --platform youtube tiktok

    # Upload with tags
    python src/upload/manager.py --file clips/clip.mp4 --tags gaming highlights

Note: Configure API credentials in config/upload_config.json before uploading.
        """
    )

    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to the video clip to upload'
    )

    parser.add_argument(
        '--platform', '-p',
        nargs='+',
        default=['youtube'],
        help='Platform(s) to upload to (default: youtube)'
    )

    parser.add_argument(
        '--title', '-t',
        help='Video title (auto-generated from filename if not provided)'
    )

    parser.add_argument(
        '--description', '-d',
        help='Video description'
    )

    parser.add_argument(
        '--tags',
        nargs='+',
        default=[],
        help='Tags/hashtags for the video'
    )

    parser.add_argument(
        '--config', '-c',
        default=DEFAULT_CONFIG_PATH,
        help='Path to upload config file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Validate file exists
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    # Create manager and upload
    manager = UploadManager(config_path=args.config)

    print(f"\nUploading: {args.file}")
    print(f"Platforms: {', '.join(args.platform)}")
    if args.title:
        print(f"Title: {args.title}")
    print()

    results = manager.upload_clip(
        clip_path=args.file,
        platforms=args.platform,
        title=args.title,
        description=args.description,
        tags=args.tags
    )

    # Print results
    print("\n" + "=" * 50)
    print("Upload Results")
    print("=" * 50)

    success_count = 0
    for result in results:
        status = "SUCCESS" if result.success else "FAILED"
        print(f"\n[{result.platform.upper()}] {status}")

        if result.success:
            print(f"  URL: {result.video_url}")
            success_count += 1
        else:
            print(f"  Error: {result.error_message}")

        print(f"  Attempts: {result.attempts}")
        print(f"  Time: {result.upload_time_seconds:.1f}s")

    print("\n" + "=" * 50)
    print(f"Total: {success_count}/{len(results)} successful")
    print("=" * 50)

    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
