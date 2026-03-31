#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场表情页面
整理从QQ市场下载的表情包，支持多种命名方式
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ..styles import StyleSheet
from ..components import Card, PageHeader, ActionBar, ModernLineEdit, ModernComboBox
from ..base_page import BaseWorkerPage
from ..workers import MarketOrganizeWorker
from utils.path_manager import path_manager
from utils.logger import get_logger

logger = get_logger("market_emoji_page")


class MarketEmojiPage(BaseWorkerPage):
    """市场表情页面"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        header = PageHeader(
            "市场表情",
            "整理从QQ市场下载的表情包，支持多种命名方式"
        )
        layout.addWidget(header)

        config_card = Card()

        json_layout = QHBoxLayout()
        json_layout.setSpacing(12)
        json_layout.addWidget(QLabel("JSON目录:"))
        self.json_input = ModernLineEdit()
        json_layout.addWidget(self.json_input, 1)
        json_btn = QPushButton("📁 浏览")
        json_btn.setObjectName("secondary_btn")
        json_btn.clicked.connect(self.browse_json_dir)
        json_layout.addWidget(json_btn)
        config_card.layout.addLayout(json_layout)

        emoji_layout = QHBoxLayout()
        emoji_layout.setSpacing(12)
        emoji_layout.addWidget(QLabel("表情目录:"))
        self.emoji_input = ModernLineEdit()
        emoji_layout.addWidget(self.emoji_input, 1)
        emoji_btn = QPushButton("📁 浏览")
        emoji_btn.setObjectName("secondary_btn")
        emoji_btn.clicked.connect(self.browse_emoji_dir)
        emoji_layout.addWidget(emoji_btn)
        config_card.layout.addLayout(emoji_layout)

        naming_layout = QHBoxLayout()
        naming_layout.setSpacing(12)
        naming_layout.addWidget(QLabel("命名方式:"))
        self.naming_combo = ModernComboBox()
        self.naming_combo.addItems(["专辑名称", "专辑ID", "表情名称", "关键词"])
        naming_layout.addWidget(self.naming_combo)
        naming_layout.addStretch()
        config_card.layout.addLayout(naming_layout)

        layout.addWidget(config_card)

        action_card = Card()
        action_bar = ActionBar()
        action_bar.add_stretch()

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_worker)
        action_bar.layout.addWidget(self.cancel_btn)

        action_bar.add_primary_button("🚀 开始整理", self.start_organize)
        self.start_btn = action_bar.layout.itemAt(action_bar.layout.count() - 1).widget()
        action_card.layout.addWidget(action_bar)

        layout.addWidget(action_card)

        progress_card = Card()
        progress_label = QLabel("📈 处理进度")
        progress_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        progress_card.layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_card.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("info_label")
        progress_card.layout.addWidget(self.status_label)

        layout.addWidget(progress_card, 1)

    def browse_json_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择JSON目录")
        if path:
            self.json_input.setText(path)

    def browse_emoji_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择表情目录")
        if path:
            self.emoji_input.setText(path)

    def start_organize(self):
        json_path = self.json_input.text()
        emoji_path = self.emoji_input.text()
        naming_mode = self.naming_combo.currentText()

        if not json_path:
            QMessageBox.warning(self, "提示", "请选择JSON目录")
            return
        if not emoji_path:
            QMessageBox.warning(self, "提示", "请选择表情目录")
            return

        json_obj = Path(json_path)
        emoji_obj = Path(emoji_path)

        if not json_obj.exists():
            QMessageBox.warning(self, "错误", f"JSON目录不存在: {json_path}")
            return
        if not emoji_obj.exists():
            QMessageBox.warning(self, "错误", f"表情目录不存在: {emoji_path}")
            return

        output_dir = Path(path_manager.paths.market_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        naming_modes = {
            "专辑名称": "album_name",
            "专辑ID": "album_id",
            "表情名称": "name",
            "关键词": "keywords"
        }
        naming_mode_key = naming_modes.get(naming_mode, "album_name")

        self._set_running(True)
        self.progress_bar.setValue(0)

        self._worker = MarketOrganizeWorker(
            json_obj, emoji_obj, output_dir, naming_mode_key
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_market_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_market_finished(self, result):
        self._set_running(False)
        self._worker = None

        if result.get("cancelled"):
            self.status_label.setText("已取消")
            return

        self.progress_bar.setValue(100)
        self.status_label.setText("整理完成！")

        result_msg = f"""
        <h3>✅ 整理完成！</h3>
        <ul>
            <li>总数量: {result.get('total', 0)}</li>
            <li>成功: {result.get('success', 0)}</li>
            <li>失败: {result.get('failed', 0)}</li>
            <li>未匹配: {result.get('unmatched', 0)}</li>
        </ul>
        <p>输出目录: {result.get('output_dir', '')}</p>
        """

        albums = result.get('albums', {})
        if albums:
            result_msg += "<h4>专辑统计:</h4><ul>"
            for album, count in albums.items():
                result_msg += f"<li>{album}: {count}个</li>"
            result_msg += "</ul>"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("整理完成")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(result_msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
