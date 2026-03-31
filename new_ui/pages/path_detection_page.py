#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径检测页面
自动检测QQ表情资源路径，支持手动选择和自动查找
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QFont

from ..styles import StyleSheet
from ..components import Card, PageHeader, ActionBar, ModernLineEdit
from core.qq_path_detector import QQPathDetector
from utils.path_manager import path_manager
from utils.logger import get_logger

logger = get_logger("path_detection_page")


class PathDetectionPage(QWidget):
    """路径检测页面"""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_saved_paths()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # 页面头部
        header = PageHeader(
            "路径检测",
            "自动检测QQ表情资源路径，支持手动选择和自动查找"
        )
        layout.addWidget(header)

        # 主卡片
        main_card = Card()

        # 路径输入
        path_layout = QHBoxLayout()
        path_layout.setSpacing(12)

        path_label = QLabel("Tencent Files路径:")
        path_label.setStyleSheet("font-weight: 500;")
        path_layout.addWidget(path_label)

        self.path_input = ModernLineEdit("例如: D:\\QQliaotian\\Tencent Files")
        path_layout.addWidget(self.path_input, 1)

        browse_btn = QPushButton("📁 浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)

        main_card.layout.addLayout(path_layout)

        # 操作按钮
        action_bar = ActionBar()
        action_bar.add_stretch()
        action_bar.add_secondary_button("✨ 尝试自动查找", self.auto_find)
        action_bar.add_primary_button("🚀 开始检测", self.start_detection)
        main_card.layout.addWidget(action_bar)

        layout.addWidget(main_card)

        # 结果卡片
        result_card = Card()

        result_header = QLabel("📊 检测结果")
        result_header.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        result_header.setStyleSheet(f"color: {StyleSheet.GRAY_700};")
        result_card.layout.addWidget(result_header)

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("检测结果将显示在这里...")
        self.result_text.setMinimumHeight(200)
        result_card.layout.addWidget(self.result_text)

        layout.addWidget(result_card, 1)

    def browse_path(self):
        """浏览路径"""
        path = QFileDialog.getExistingDirectory(self, "选择Tencent Files目录")
        if path:
            self.path_input.setText(path)

    def load_saved_paths(self):
        """加载保存的路径"""
        paths = path_manager.get_all_paths()

        if paths.get("tencent_files"):
            self.path_input.setText(paths["tencent_files"])

            if path_manager.is_auto_detected():
                if self.main_window:
                    if paths.get("market_json"):
                        self.main_window.set_market_paths(
                            paths["market_json"],
                            paths.get("market_emoji", "")
                        )
                    if paths.get("favorite_emoji"):
                        self.main_window.set_favorite_path(
                            paths["favorite_emoji"],
                            paths.get("favorite_thumb", "")
                        )

                self.result_text.append("✅ 已加载上次保存的路径\n")
                self.result_text.append(f"QQ账号: {paths.get('qq_account', '未知')}\n")
                self.result_text.append("路径已自动填充到各页面\n\n")

    def auto_find(self):
        """自动查找"""
        self.result_text.setText("正在自动查找QQ路径...\n")

        try:
            detector = QQPathDetector()
            if detector.auto_detect():
                self.result_text.append(f"✅ 找到Tencent Files路径: {detector.tencent_files_path}\n")
                self.result_text.append(f"检测到 {len(detector.qq_accounts)} 个QQ账号\n\n")

                for account in detector.qq_accounts:
                    paths = detector.detected_paths.get(account)
                    if paths:
                        self.result_text.append(f"QQ账号: {account}\n")
                        self.result_text.append(f"  收藏表情: {'✓' if paths.favorite_exists else '✗'} {paths.favorite_emoji_dir}\n")
                        self.result_text.append(f"  市场表情: {'✓' if paths.market_exists else '✗'} {paths.market_emoji_dir}\n")
                        self.result_text.append(f"  JSON配置: {'✓' if paths.json_exists else '✗'} {paths.market_json_dir}\n\n")

                if detector.qq_accounts:
                    first_account = detector.qq_accounts[0]
                    paths = detector.detected_paths.get(first_account)
                    if paths and paths.tencent_files_root:
                        self.path_input.setText(str(paths.tencent_files_root))

                        if self.main_window:
                            if paths.json_exists and paths.market_json_dir:
                                self.main_window.set_market_paths(
                                    str(paths.market_json_dir),
                                    str(paths.market_emoji_dir)
                                )
                            if paths.favorite_exists and paths.favorite_emoji_dir:
                                self.main_window.set_favorite_path(
                                    str(paths.favorite_emoji_dir),
                                    str(paths.favorite_thumb_dir) if paths.favorite_thumb_dir else None
                                )
                            self.result_text.append("✅ 路径已自动填充到市场表情和收藏表情页面\n\n")
            else:
                self.result_text.append("❌ 未找到Tencent Files目录\n")
                self.result_text.append("请手动选择路径\n")
        except FileNotFoundError as e:
            self.result_text.append(f"❌ 路径不存在: {e}\n请检查Tencent Files路径是否正确。\n")
        except PermissionError as e:
            self.result_text.append(f"❌ 权限不足: {e}\n请尝试以管理员身份运行程序。\n")
        except Exception as e:
            self.result_text.append(f"❌ 自动查找失败: {e}\n")

    def start_detection(self):
        """开始检测"""
        path = self.path_input.text()
        if not path:
            QMessageBox.warning(self, "提示", "请先输入或选择路径")
            return

        path_obj = Path(path)
        if not path_obj.exists():
            QMessageBox.warning(self, "错误", f"路径不存在: {path}")
            return

        self.result_text.setText(f"正在检测路径: {path}\n\n")

        try:
            detector = QQPathDetector(path_obj)
            accounts = detector.detect_qq_accounts()

            if not accounts:
                self.result_text.append("❌ 未检测到QQ账号\n")
                return

            self.result_text.append(f"✅ 检测到 {len(accounts)} 个QQ账号:\n\n")

            for account in accounts:
                paths = detector.detect_emoji_paths(account)
                if paths:
                    self.result_text.append(f"QQ账号: {account}\n")
                    self.result_text.append(f"  收藏表情: {'✓' if paths.favorite_exists else '✗'}\n")
                    self.result_text.append(f"  市场表情: {'✓' if paths.market_exists else '✗'}\n")
                    self.result_text.append(f"  JSON配置: {'✓' if paths.json_exists else '✗'}\n\n")

                    if self.main_window:
                        if paths.json_exists and paths.market_json_dir:
                            self.main_window.set_market_paths(
                                str(paths.market_json_dir),
                                str(paths.market_emoji_dir)
                            )
                        if paths.favorite_exists and paths.favorite_emoji_dir:
                            self.main_window.set_favorite_path(
                                str(paths.favorite_emoji_dir),
                                str(paths.favorite_thumb_dir) if paths.favorite_thumb_dir else None
                            )
                        self.result_text.append("✅ 路径已自动填充到市场表情和收藏表情页面\n\n")
                        break
        except FileNotFoundError as e:
            self.result_text.append(f"❌ 路径不存在: {e}\n请检查输入路径是否正确。\n")
        except PermissionError as e:
            self.result_text.append(f"❌ 权限不足: {e}\n请检查目录读取权限。\n")
        except Exception as e:
            self.result_text.append(f"❌ 检测失败: {e}\n")
