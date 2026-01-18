"""
VOD clipping module for creating clips from past broadcasts.

Components:
- VODClipper: Downloads and clips VOD segments using FFmpeg
- ChatAnalyzer: Analyzes chat replay to detect highlights
"""

from .vod_clipper import VODClipper
from .chat_analyzer import ChatAnalyzer

__all__ = ['VODClipper', 'ChatAnalyzer']
