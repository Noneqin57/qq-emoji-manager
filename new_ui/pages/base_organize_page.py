#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理页面基类
提供"配置卡片 + 操作卡片 + 进度卡片"的通用布局
消除 MarketEmojiPage / FavoriteEmojiPage / ConvertPage 的重复代码
"""

from abc import abstractmethod

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QMessageBox
)
from PyQt5.QtGui import QFont

from ..components import Card, PageHeader, ActionBar
from ..base_page import BaseWorkerPage


class BaseOrganizePage(BaseWorkerPage):
    """
    整理操作页面的通用基类
    
    子类只需实现:
    - _build_config_card(): 返回配置卡片及其内部控件引用
    - _build_action_bar(): 返回操作栏
    - start_operation(): 启动具体业务逻辑
    """

    def __init__(self, page_title: str, page_subtitle: str,
                 progress_title: str = "📈 处理进度", parent=None):
        super().__init__(parent)
        self._page_title = page_title
        self._page_subtitle = page_subtitle
        self._progress_title = progress_title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        header = PageHeader(self._page_title, self._page_subtitle)
        layout.addWidget(header)

        self.config_card, self._config_refs = self._build_config_card()
        layout.addWidget(self.config_card)

        action_card = Card()
        action_bar = self._build_action_bar()
        action_card.layout.addWidget(action_bar)
        layout.addWidget(action_card)

        progress_card = Card()
        progress_label = QLabel(self._progress_title)
        progress_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        progress_card.layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_card.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("info_label")
        progress_card.layout.addWidget(self.status_label)

        layout.addWidget(progress_card, 1)

    @abstractmethod
    def _build_config_card(self) -> tuple:
        """
        构建配置卡片
        
        Returns:
            (Card实例, 控件引用dict) — 控件引用供 start_operation() 使用
        """
        pass

    @abstractmethod
    def _build_action_bar(self) -> ActionBar:
        """
        构建操作栏，包含开始/取消按钮
        
        实现时应设置:
        - self.start_btn: 主按钮引用
        - self.cancel_btn: 取消按钮引用
        """
        pass

    @abstractmethod
    def start_operation(self):
        """启动整理操作"""
        pass

    def _set_running(self, running: bool):
        self._is_running = running
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(not running)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setVisible(running)
