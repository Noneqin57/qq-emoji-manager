# -*- coding: utf-8 -*-
"""
现代化UI组件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class Card(QFrame):
    """卡片组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)


class IconButton(QPushButton):
    """带图标的按钮"""
    
    def __init__(self, icon_text, text, parent=None):
        super().__init__(f"{icon_text} {text}", parent)
        self.setCursor(Qt.PointingHandCursor)


class SidebarButton(QPushButton):
    """侧边栏按钮"""
    
    clicked_signal = pyqtSignal(str)
    
    def __init__(self, icon, text, page_id, parent=None):
        super().__init__(f"{icon}  {text}", parent)
        self.setObjectName("sidebar_btn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.page_id = page_id
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        self.clicked_signal.emit(self.page_id)


class ModernLineEdit(QLineEdit):
    """现代化输入框"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(40)


class ModernComboBox(QComboBox):
    """现代化下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)


class PageHeader(QWidget):
    """页面头部组件"""
    
    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("page_header")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("page_title")
        title_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        layout.addWidget(title_label)
        
        # 副标题
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("page_subtitle")
            subtitle_label.setFont(QFont("Microsoft YaHei UI", 11))
            layout.addWidget(subtitle_label)


class ActionBar(QWidget):
    """操作栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.layout = layout
    
    def add_primary_button(self, text, callback):
        """添加主按钮"""
        btn = QPushButton(text)
        btn.setObjectName("primary_btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn
    
    def add_secondary_button(self, text, callback):
        """添加次要按钮"""
        btn = QPushButton(text)
        btn.setObjectName("secondary_btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn
    
    def add_stretch(self):
        """添加弹性空间"""
        self.layout.addStretch()


class InfoCard(Card):
    """信息卡片"""
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #374151;")
        self.layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel(content)
        content_label.setObjectName("info_label")
        content_label.setWordWrap(True)
        self.layout.addWidget(content_label)


class StatusBadge(QLabel):
    """状态徽章"""
    
    def __init__(self, text, status="info", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(self._get_style(status))
    
    def _get_style(self, status):
        styles = {
            "success": "background-color: #D1FAE5; color: #065F46; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;",
            "warning": "background-color: #FEF3C7; color: #92400E; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;",
            "error": "background-color: #FEE2E2; color: #991B1B; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;",
            "info": "background-color: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;",
        }
        return styles.get(status, styles["info"])
