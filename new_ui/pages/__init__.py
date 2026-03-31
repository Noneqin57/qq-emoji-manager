#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI页面模块
包含所有功能页面的独立实现
"""

from .path_detection_page import PathDetectionPage
from .market_emoji_page import MarketEmojiPage
from .favorite_emoji_page import FavoriteEmojiPage
from .convert_page import ConvertPage
from .preview_page import PreviewPage
from .settings_page import SettingsPage
from .base_organize_page import BaseOrganizePage

__all__ = [
    "PathDetectionPage",
    "MarketEmojiPage",
    "FavoriteEmojiPage",
    "ConvertPage",
    "PreviewPage",
    "SettingsPage",
    "BaseOrganizePage",
]
