#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式转换页面
将表情包转换为微信兼容格式
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtGui import QFont

from ..components import Card, PageHeader, ActionBar, ModernLineEdit, ModernComboBox
from ..base_page import BaseWorkerPage
from ..workers import ConvertWorker
from utils.logger import get_logger

logger = get_logger("convert_page")


class ConvertPage(BaseWorkerPage):
    """格式转换页面"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        header = PageHeader(
            "格式转换",
            "将表情包转换为微信兼容格式"
        )
        layout.addWidget(header)

        convert_card = Card()

        source_layout = QHBoxLayout()
        source_layout.setSpacing(12)
        source_layout.addWidget(QLabel("源目录:"))
        self.source_input = ModernLineEdit()
        source_layout.addWidget(self.source_input, 1)
        source_btn = QPushButton("📁 浏览")
        source_btn.setObjectName("secondary_btn")
        source_btn.clicked.connect(self.browse_source_dir)
        source_layout.addWidget(source_btn)
        convert_card.layout.addLayout(source_layout)

        output_layout = QHBoxLayout()
        output_layout.setSpacing(12)
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_input = ModernLineEdit()
        output_layout.addWidget(self.output_input, 1)
        output_btn = QPushButton("📁 浏览")
        output_btn.setObjectName("secondary_btn")
        output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(output_btn)
        convert_card.layout.addLayout(output_layout)

        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)
        format_layout.addWidget(QLabel("目标格式:"))
        self.format_combo = ModernComboBox()
        self.format_combo.addItems(["GIF (推荐)", "PNG", "JPG", "WebP"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        convert_card.layout.addLayout(format_layout)

        layout.addWidget(convert_card)

        progress_card = Card()
        progress_label = QLabel("📈 转换进度")
        progress_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        progress_card.layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_card.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("info_label")
        progress_card.layout.addWidget(self.status_label)

        layout.addWidget(progress_card, 1)

        action_card = Card()
        action_bar = ActionBar()
        action_bar.add_stretch()

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_worker)
        action_bar.layout.addWidget(self.cancel_btn)

        action_bar.add_primary_button("🔄 开始转换", self.start_convert)
        self.start_btn = action_bar.layout.itemAt(action_bar.layout.count() - 1).widget()
        action_card.layout.addWidget(action_bar)

        layout.addWidget(action_card)

    def browse_source_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择源目录")
        if path:
            self.source_input.setText(path)

    def browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_input.setText(path)

    def start_convert(self):
        source_path = self.source_input.text()
        output_path = self.output_input.text()

        if not source_path:
            QMessageBox.warning(self, "提示", "请选择源目录")
            return
        if not output_path:
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return

        source_obj = Path(source_path)
        if not source_obj.exists():
            QMessageBox.warning(self, "错误", f"源目录不存在: {source_path}")
            return

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
        self.status_label.setText("准备转换...")

        self._worker = ConvertWorker(source_obj, output_obj)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_convert_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_convert_finished(self, result):
        self._set_running(False)
        self._worker = None

        if result.get("cancelled"):
            self.status_label.setText("已取消")
            return

        self.progress_bar.setValue(100)
        self.status_label.setText("转换完成！")

        QMessageBox.information(
            self, "完成",
            f"转换完成!\n成功: {result.get('success', 0)}\n"
            f"失败: {result.get('failed', 0)}\n"
            f"输出目录: {result.get('output_dir', '')}"
        )

    def _on_error(self, error_msg):
        self._set_running(False)
        self._worker = None
        self.status_label.setText(f"转换失败: {error_msg}")
        if hasattr(self, 'result_text'):
            self.result_text.append(f"❌ 错误: {error_msg}\n")
        QMessageBox.critical(self, "错误", f"转换失败: {error_msg}")
