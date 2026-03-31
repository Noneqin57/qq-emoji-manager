#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包预览页面（带分页）
预览所有表情包，支持复制到剪贴板
"""

from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from ..components import Card, PageHeader, ModernLineEdit
from ..workers import PreviewLoadWorker
from utils.logger import get_logger

logger = get_logger("preview_page")

ITEMS_PER_PAGE = 60
COLUMNS = 6


class PreviewPage(QWidget):
    """表情包预览页面（带分页）"""

    def __init__(self):
        super().__init__()
        self.emoji_files = []
        self.current_page = 0
        self.total_pages = 0
        self._worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        header = PageHeader(
            "表情包预览",
            "预览所有表情包，支持复制到剪贴板"
        )
        layout.addWidget(header)

        preview_card = Card()

        path_layout = QHBoxLayout()
        path_layout.setSpacing(12)
        path_layout.addWidget(QLabel("表情目录:"))
        self.preview_path_input = ModernLineEdit()
        path_layout.addWidget(self.preview_path_input, 1)
        browse_btn = QPushButton("📁 浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(browse_btn)
        load_btn = QPushButton("👁 加载预览")
        load_btn.setObjectName("primary_btn")
        load_btn.clicked.connect(self.load_preview)
        path_layout.addWidget(load_btn)
        preview_card.layout.addLayout(path_layout)

        self.status_label = QLabel("请选择表情目录并点击加载")
        self.status_label.setObjectName("info_label")
        preview_card.layout.addWidget(self.status_label)

        page_bar = QHBoxLayout()
        page_bar.addStretch()

        self.prev_btn = QPushButton("< 上一页")
        self.prev_btn.setObjectName("secondary_btn")
        self.prev_btn.clicked.connect(self._prev_page)
        self.prev_btn.setVisible(False)
        page_bar.addWidget(self.prev_btn)

        self.page_label = QLabel("")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("padding: 0 16px;")
        page_bar.addWidget(self.page_label)

        self.next_btn = QPushButton("下一页 >")
        self.next_btn.setObjectName("secondary_btn")
        self.next_btn.clicked.connect(self._next_page)
        self.next_btn.setVisible(False)
        page_bar.addWidget(self.next_btn)

        page_bar.addStretch()
        preview_card.layout.addLayout(page_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_area.setObjectName("preview_scroll_area")

        self.preview_container = QWidget()
        self.preview_container.setObjectName("preview_container")
        self.preview_grid = QGridLayout(self.preview_container)
        self.preview_grid.setSpacing(16)

        self.scroll_area.setWidget(self.preview_container)
        preview_card.layout.addWidget(self.scroll_area)

        layout.addWidget(preview_card, 1)

    def browse_directory(self):
        path = QFileDialog.getExistingDirectory(self, "选择表情目录")
        if path:
            self.preview_path_input.setText(path)

    def load_preview(self):
        path = self.preview_path_input.text()
        if not path:
            QMessageBox.warning(self, "提示", "请选择表情目录")
            return

        path_obj = Path(path)
        if not path_obj.exists():
            QMessageBox.warning(self, "错误", f"目录不存在: {path}")
            return

        self.emoji_files = []
        for ext in ['*.gif', '*.png', '*.jpg', '*.jpeg', '*.webp']:
            self.emoji_files.extend(path_obj.glob(ext))
            self.emoji_files.extend(path_obj.glob(ext.upper()))

        if not self.emoji_files:
            self.status_label.setText("未找到表情文件")
            QMessageBox.information(self, "提示", "未找到表情文件")
            return

        self.current_page = 0
        self.total_pages = max(1, (len(self.emoji_files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self.status_label.setText(f"找到 {len(self.emoji_files)} 个表情文件")
        self._display_current_page()

    def _display_current_page(self):
        while self.preview_grid.count():
            item = self.preview_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        start = self.current_page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(self.emoji_files))
        page_files = self.emoji_files[start:end]

        for i, emoji_path in enumerate(page_files):
            preview_label = QLabel()
            preview_label.setObjectName("preview_label")
            preview_label.setFixedSize(100, 100)
            preview_label.setAlignment(Qt.AlignCenter)
            preview_label.setText("...")
            preview_label.setToolTip(emoji_path.name)
            row = i // COLUMNS
            col = i % COLUMNS
            self.preview_grid.addWidget(preview_label, row, col)

        self._update_page_controls()

        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        self._worker = PreviewLoadWorker(page_files, size=80)
        self._worker.preview_ready.connect(self._on_preview_ready)
        self._worker.start()

    def _on_preview_ready(self, index, pixmap, filename):
        item = self.preview_grid.itemAt(index)
        if item and item.widget():
            label = item.widget()
            if not pixmap.isNull():
                scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled)
            else:
                label.setText("❓")

    def _update_page_controls(self):
        has_pages = self.total_pages > 1
        self.prev_btn.setVisible(has_pages)
        self.next_btn.setVisible(has_pages)
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
        if has_pages:
            self.page_label.setText(f"第 {self.current_page + 1} / {self.total_pages} 页")
        else:
            self.page_label.setText("")

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._display_current_page()

    def _next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._display_current_page()
