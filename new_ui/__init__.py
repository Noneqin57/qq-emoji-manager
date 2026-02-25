# -*- coding: utf-8 -*-
"""
全新现代化UI模块
采用卡片式布局、圆角设计、柔和阴影
"""

from .main_window import ModernMainWindow
from .components import *
from .styles import StyleSheet

__all__ = [
    'ModernMainWindow',
    'StyleSheet',
    'Card',
    'IconButton',
    'ModernLineEdit',
    'ModernComboBox',
]
