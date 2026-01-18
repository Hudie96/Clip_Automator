"""
Social media upload framework for clips.

Supports YouTube and TikTok (placeholder) uploads.
Configure credentials in config/upload_config.json.
"""

from .base import Uploader, UploadStatus, UploadResult
from .youtube import YouTubeUploader
from .tiktok import TikTokUploader
from .manager import UploadManager

__all__ = [
    'Uploader',
    'UploadStatus',
    'UploadResult',
    'YouTubeUploader',
    'TikTokUploader',
    'UploadManager'
]
