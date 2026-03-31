#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收藏表情页面
整理收藏的表情，支持通过 Thumb 目录筛选个人收藏
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit, QCheckBox
)
from PyQt5.QtGui import QFont

from ..components import Card, PageHeader, ActionBar, ModernLineEdit
from ..base_page import BaseWorkerPage
from ..workers import FavoriteOrganizeWorker
from utils.path_manager import path_manager, detect_thumb_dir
from utils.logger import get_logger

logger = get_logger("favorite_emoji_page")


class FavoriteEmojiPage(BaseWorkerPage):
    """收藏表情页面"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        header = PageHeader(
            "收藏表情",
            "整理收藏的表情，支持通过 Thumb 目录筛选个人收藏"
        )
        layout.addWidget(header)

        config_card = Card()

        source_layout = QHBoxLayout()
        source_layout.setSpacing(12)
        source_layout.addWidget(QLabel("源目录(Ori):"))
        self.source_input = ModernLineEdit()
        self.source_input.setPlaceholderText("选择 personal_emoji/Ori 目录")
        source_layout.addWidget(self.source_input, 1)
        source_btn = QPushButton("📁 浏览")
        source_btn.setObjectName("secondary_btn")
        source_btn.clicked.connect(self.browse_source_dir)
        source_layout.addWidget(source_btn)
        config_card.layout.addLayout(source_layout)

        thumb_layout = QHBoxLayout()
        thumb_layout.setSpacing(12)
        thumb_layout.addWidget(QLabel("缩略图目录(Thumb):"))
        self.thumb_input = ModernLineEdit()
        self.thumb_input.setPlaceholderText("选择 personal_emoji/Thumb 目录（可选，用于筛选个人收藏）")
        thumb_layout.addWidget(self.thumb_input, 1)
        thumb_btn = QPushButton("📁 浏览")
        thumb_btn.setObjectName("secondary_btn")
        thumb_btn.clicked.connect(self.browse_thumb_dir)
        thumb_layout.addWidget(thumb_btn)
        config_card.layout.addLayout(thumb_layout)

        naming_layout = QHBoxLayout()
        naming_layout.setSpacing(12)
        naming_layout.addWidget(QLabel("文件名前缀:"))
        self.prefix_input = ModernLineEdit("emoji")
        naming_layout.addWidget(self.prefix_input)
        naming_layout.addWidget(QLabel("起始序号:"))
        self.start_num_input = ModernLineEdit("1")
        self.start_num_input.setFixedWidth(80)
        naming_layout.addWidget(self.start_num_input)
        naming_layout.addStretch()
        config_card.layout.addLayout(naming_layout)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        self.filter_checkbox = QCheckBox("仅导出个人收藏表情（通过 Thumb 目录筛选）")
        self.filter_checkbox.setChecked(True)
        self.filter_checkbox.setToolTip(
            "勾选后，仅导出在 Thumb 目录中有对应缩略图的文件。\n"
            "这可以过滤掉 Ori 目录中混杂的其他表情源文件。"
        )
        filter_layout.addWidget(self.filter_checkbox)
        filter_layout.addStretch()
        config_card.layout.addLayout(filter_layout)

        layout.addWidget(config_card)

        action_card = Card()
        action_bar = ActionBar()
        action_bar.add_stretch()

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_worker)
        action_bar.layout.addWidget(self.cancel_btn)

        action_bar.add_primary_button("⭐ 开始整理", self.start_organize)
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

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("处理结果将显示在这里...")
        self.result_text.setMinimumHeight(120)
        progress_card.layout.addWidget(self.result_text)

        layout.addWidget(progress_card, 1)

    def browse_thumb_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择缩略图目录(Thumb)")
        if path:
            self.thumb_input.setText(path)

    def start_organize(self):
        source_path = self.source_input.text()
        thumb_path = self.thumb_input.text().strip() or None
        output_path = path_manager.paths.favorite_output_dir
        prefix = self.prefix_input.text()
        start_num_text = self.start_num_input.text()
        filter_by_thumb = self.filter_checkbox.isChecked()

        if not source_path:
            QMessageBox.warning(self, "提示", "请选择源目录(Ori)")
            return
        if not prefix:
            QMessageBox.warning(self, "提示", "请输入文件名前缀")
            return

        try:
            start_num = int(start_num_text)
            if start_num < 0:
                QMessageBox.warning(self, "提示", "起始序号不能为负数")
                return
        except ValueError:
            QMessageBox.warning(self, "提示", "起始序号必须是有效的数字")
            return

        source_obj = Path(source_path)
        if not source_obj.exists():
            QMessageBox.warning(self, "错误", f"源目录不存在: {source_path}")
            return

        thumb_obj = None
        if thumb_path:
            thumb_obj = Path(thumb_path)
            if not thumb_obj.exists():
                reply = QMessageBox.question(
                    self, "提示",
                    f"Thumb 目录不存在: {thumb_path}\n是否继续（不使用筛选）？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                thumb_obj = None

        try:
            output_obj = Path(output_path)
            output_obj.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            QMessageBox.warning(self, "错误", f"无法创建输出目录，权限不足: {output_path}")
            return
        except OSError as e:
            QMessageBox.warning(self, "错误", f"无法创建输出目录: {e}")
            return

        self._set_running(True)
        self.progress_bar.setValue(0)
        self.result_text.setText("正在准备...\n")

        self._worker = FavoriteOrganizeWorker(
            source_obj, output_obj, prefix, start_num,
            thumb_dir=thumb_obj,
            filter_by_thumb=filter_by_thumb
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_favorite_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_favorite_finished(self, result):
        self._set_running(False)
        self._worker = None

        if result.get("cancelled"):
            self.status_label.setText("已取消")
            self.result_text.append("操作已取消\n")
            return

        self.progress_bar.setValue(100)
        self.status_label.setText("整理完成！")
        
        stats = result.get("scan_stats", {})
        if stats.get("total_in_thumb", 0) > 0:
            self.result_text.append("📊 筛选统计:\n")
            self.result_text.append(f"  Ori 目录文件: {stats.get('total_in_ori', 0)}\n")
            self.result_text.append(f"  Thumb 目录文件: {stats.get('total_in_thumb', 0)}\n")
            self.result_text.append(f"  匹配成功: {stats.get('matched_count', 0)}\n")
            self.result_text.append(f"  已过滤: {stats.get('filtered_count', 0)}\n\n")
        
        self.result_text.append(f"✅ 整理完成!\n")
        self.result_text.append(f"成功: {result.get('success', 0)}\n")
        self.result_text.append(f"失败: {result.get('failed', 0)}\n")
        self.result_text.append(f"输出目录: {result.get('output_dir', '')}\n")

        QMessageBox.information(
            self, "完成",
            f"整理完成!\n成功: {result.get('success', 0)}, 失败: {result.get('failed', 0)}"
        )

    def browse_source_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择源目录(Ori)")
        if path:
            self.source_input.setText(path)
            resolved_thumb = detect_thumb_dir(path)
            if resolved_thumb:
                self.thumb_input.setText(resolved_thumb)
