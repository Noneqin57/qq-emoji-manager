# -*- coding: utf-8 -*-
"""
全新现代化主窗口
采用侧边栏导航 + 卡片式布局
"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

from __version__ import __version__
from .styles import StyleSheet
from .components import SidebarButton
from .pages import (
    PathDetectionPage, MarketEmojiPage, FavoriteEmojiPage,
    ConvertPage, SettingsPage
)
from utils.path_manager import path_manager, detect_thumb_dir
from utils.logger import get_logger

logger = get_logger("main_window")


class ModernMainWindow(QMainWindow):
    """现代化主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QQ表情包管理器")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._dark_mode = False
        self.setStyleSheet(StyleSheet.get_main_stylesheet())

        self.init_ui()
        self.show_welcome_animation()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar, 0)

        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        logo_label = QLabel("🎨 表情包管理")
        logo_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        logo_label.setStyleSheet(f"color: {StyleSheet.PRIMARY}; padding: 10px;")
        layout.addWidget(logo_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {StyleSheet.GRAY_200}; margin: 10px 0;")
        line.setFixedHeight(1)
        layout.addWidget(line)

        self.nav_buttons = []
        nav_items = [
            ("🔍", "路径检测", "path"),
            ("🛒", "市场表情", "market"),
            ("⭐", "收藏表情", "favorite"),
            ("🔄", "格式转换", "convert"),
            ("⚙️", "设置", "settings"),
        ]

        for icon, text, page_id in nav_items:
            btn = SidebarButton(icon, text, page_id)
            btn.clicked_signal.connect(self._on_nav_clicked)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self.theme_btn = QPushButton("🌙 深色模式")
        self.theme_btn.setObjectName("secondary_btn")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        version_label = QLabel(f"v{__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {StyleSheet.GRAY_400}; font-size: 12px;")
        layout.addWidget(version_label)

        return sidebar

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        if self._dark_mode:
            self.setStyleSheet(StyleSheet.get_dark_stylesheet())
            self.theme_btn.setText("☀️ 浅色模式")
        else:
            self.setStyleSheet(StyleSheet.get_main_stylesheet())
            self.theme_btn.setText("🌙 深色模式")

    def _create_content_area(self):
        content = QFrame()
        content.setObjectName("content_area")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        self.page_stack = QStackedWidget()

        self.pages = {}
        self.pages["path"] = PathDetectionPage(self)
        self.pages["market"] = MarketEmojiPage()
        self.pages["favorite"] = FavoriteEmojiPage()
        self.pages["convert"] = ConvertPage()
        self.pages["settings"] = SettingsPage()

        for page_id, page in self.pages.items():
            self.page_stack.addWidget(page)

        layout.addWidget(self.page_stack)

        self.nav_buttons[0].setChecked(True)

        return content

    def set_market_paths(self, json_dir: str, emoji_dir: str):
        market_page = self.pages.get("market")
        if market_page:
            market_page.json_input.setText(json_dir)
            market_page.emoji_input.setText(emoji_dir)

        path_manager.set_market_paths(json_dir, emoji_dir)

        settings_page = self.pages.get("settings")
        if settings_page:
            if emoji_dir:
                settings_page.market_path_input.setText(emoji_dir)

    def set_favorite_path(self, emoji_dir: str, thumb_dir: str = None):
        resolved_thumb = detect_thumb_dir(emoji_dir, thumb_dir) if emoji_dir else None

        favorite_page = self.pages.get("favorite")
        if favorite_page:
            favorite_page.source_input.setText(emoji_dir)
            if resolved_thumb:
                favorite_page.thumb_input.setText(resolved_thumb)

        path_manager.set_favorite_paths(emoji_dir, resolved_thumb)

        settings_page = self.pages.get("settings")
        if settings_page:
            if emoji_dir:
                settings_page.favorite_path_input.setText(emoji_dir)
            if resolved_thumb:
                settings_page.thumb_path_input.setText(resolved_thumb)

    def auto_detect_and_fill_paths(self):
        try:
            if path_manager.auto_detect_from_tencent_files():
                paths = path_manager.get_all_paths()

                if paths.get("market_json") and paths.get("market_emoji"):
                    self.set_market_paths(paths["market_json"], paths["market_emoji"])

                if paths.get("favorite_emoji"):
                    self.set_favorite_path(paths["favorite_emoji"], paths.get("favorite_thumb"))

                settings_page = self.pages.get("settings")
                if settings_page:
                    settings_page.load_settings()

                return True, "路径自动检测成功"
            else:
                return False, "无法自动检测路径，请手动设置"
        except Exception as e:
            return False, f"自动检测失败: {e}"

    def _on_nav_clicked(self, page_id):
        for btn in self.nav_buttons:
            btn.setChecked(btn.page_id == page_id)

        page_index = list(self.pages.keys()).index(page_id)
        self.page_stack.setCurrentIndex(page_index)

    def show_welcome_animation(self):
        self.setWindowOpacity(0.0)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


def main():
    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
