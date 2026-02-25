# -*- coding: utf-8 -*-
"""
全新现代化主窗口
采用侧边栏导航 + 卡片式布局
"""

import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, QSizePolicy,
    QFileDialog, QMessageBox, QTextEdit, QComboBox, QGroupBox,
    QProgressBar, QLineEdit, QScrollArea, QGridLayout, QCheckBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap

from .styles import StyleSheet
from .components import (
    Card, SidebarButton, PageHeader, ActionBar,
    ModernLineEdit, ModernComboBox, StatusBadge
)
from .settings_page import SettingsPage
from .workers import (
    MarketOrganizeWorker, FavoriteOrganizeWorker,
    ConvertWorker, PreviewLoadWorker
)
from utils.logger import get_logger

logger = get_logger("main_window")

# 导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.qq_path_detector import QQPathDetector
from core.market_emoji import MarketEmojiClassifier
from core.favorite_emoji import FavoriteEmojiClassifier
from utils.format_converter import WeChatEmojiConverter
from utils.path_manager import path_manager


class ModernMainWindow(QMainWindow):
    """现代化主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QQ表情包管理器")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 当前主题
        self._dark_mode = False

        # 应用样式
        self.setStyleSheet(StyleSheet.get_main_stylesheet())

        # 初始化UI
        self.init_ui()

        # 显示欢迎动画
        self.show_welcome_animation()

    def init_ui(self):
        """初始化界面"""
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)

        # 主布局 - 水平分割
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建侧边栏
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar, 0)

        # 创建内容区
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)

    def _create_sidebar(self):
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(8)

        # Logo区域
        logo_label = QLabel("🎨 表情包管理")
        logo_label.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        logo_label.setStyleSheet(f"color: {StyleSheet.PRIMARY}; padding: 10px;")
        layout.addWidget(logo_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {StyleSheet.GRAY_200}; margin: 10px 0;")
        line.setFixedHeight(1)
        layout.addWidget(line)

        # 导航按钮
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

        # 弹性空间
        layout.addStretch()

        # 主题切换按钮
        self.theme_btn = QPushButton("🌙 深色模式")
        self.theme_btn.setObjectName("secondary_btn")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # 底部信息
        version_label = QLabel("v2.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {StyleSheet.GRAY_400}; font-size: 12px;")
        layout.addWidget(version_label)

        return sidebar

    def _toggle_theme(self):
        """切换深色/浅色主题"""
        self._dark_mode = not self._dark_mode
        if self._dark_mode:
            self.setStyleSheet(StyleSheet.get_dark_stylesheet())
            self.theme_btn.setText("☀️ 浅色模式")
        else:
            self.setStyleSheet(StyleSheet.get_main_stylesheet())
            self.theme_btn.setText("🌙 深色模式")

    def _create_content_area(self):
        """创建内容区"""
        content = QFrame()
        content.setObjectName("content_area")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 页面堆叠
        self.page_stack = QStackedWidget()

        # 创建各个页面
        self.pages = {}
        self.pages["path"] = PathDetectionPage(self)
        self.pages["market"] = MarketEmojiPage()
        self.pages["favorite"] = FavoriteEmojiPage()
        self.pages["convert"] = ConvertPage()
        self.pages["settings"] = SettingsPage()

        for page_id, page in self.pages.items():
            self.page_stack.addWidget(page)

        layout.addWidget(self.page_stack)

        # 默认选中第一个
        self.nav_buttons[0].setChecked(True)

        return content

    def set_market_paths(self, json_dir: str, emoji_dir: str):
        """设置市场表情路径"""
        market_page = self.pages.get("market")
        if market_page:
            market_page.json_input.setText(json_dir)
            market_page.emoji_input.setText(emoji_dir)

        # 同时更新路径管理器
        if json_dir:
            path_manager.paths.market_json_dir = json_dir
        if emoji_dir:
            path_manager.paths.market_emoji_dir = emoji_dir
        path_manager.save_config()

        # 同步更新设置页面的预览路径输入框
        settings_page = self.pages.get("settings")
        if settings_page:
            if emoji_dir:
                settings_page.market_path_input.setText(emoji_dir)

    def set_favorite_path(self, emoji_dir: str, thumb_dir: str = None):
        """设置收藏表情路径"""
        favorite_page = self.pages.get("favorite")
        if favorite_page:
            favorite_page.source_input.setText(emoji_dir)

            # 自动检测并填充 Thumb 目录
            if emoji_dir:
                source_obj = Path(emoji_dir)
                if source_obj.name.upper() == "ORI":
                    # 优先使用传入的 thumb_dir，否则自动检测
                    if thumb_dir and Path(thumb_dir).exists():
                        favorite_page.thumb_input.setText(thumb_dir)
                    else:
                        thumb_candidate = source_obj.parent / "Thumb"
                        if thumb_candidate.exists():
                            favorite_page.thumb_input.setText(str(thumb_candidate))

        # 同时更新路径管理器
        if emoji_dir:
            path_manager.paths.favorite_emoji_dir = emoji_dir
        if thumb_dir:
            path_manager.paths.favorite_thumb_dir = thumb_dir
        path_manager.save_config()

        # 同步更新设置页面的预览路径输入框
        settings_page = self.pages.get("settings")
        if settings_page:
            if emoji_dir:
                settings_page.favorite_path_input.setText(emoji_dir)
            # 自动检测并填充 Thumb 目录到设置页面
            if emoji_dir:
                source_obj = Path(emoji_dir)
                if source_obj.name.upper() == "ORI":
                    # 优先使用传入的 thumb_dir，否则自动检测
                    if thumb_dir and Path(thumb_dir).exists():
                        settings_page.thumb_path_input.setText(thumb_dir)
                    else:
                        thumb_candidate = source_obj.parent / "Thumb"
                        if thumb_candidate.exists():
                            settings_page.thumb_path_input.setText(str(thumb_candidate))

    def auto_detect_and_fill_paths(self):
        """自动检测并填充所有路径"""
        try:
            # 尝试自动检测
            if path_manager.auto_detect_from_tencent_files():
                # 获取检测到的路径
                paths = path_manager.get_all_paths()

                # 填充市场表情页面
                if paths.get("market_json") and paths.get("market_emoji"):
                    self.set_market_paths(paths["market_json"], paths["market_emoji"])

                # 填充收藏表情页面（同时传入 Thumb 路径）
                if paths.get("favorite_emoji"):
                    self.set_favorite_path(paths["favorite_emoji"], paths.get("favorite_thumb"))

                # 更新设置页面
                settings_page = self.pages.get("settings")
                if settings_page:
                    settings_page.load_settings()

                return True, "路径自动检测成功"
            else:
                return False, "无法自动检测路径，请手动设置"
        except Exception as e:
            return False, f"自动检测失败: {e}"

    def _on_nav_clicked(self, page_id):
        """导航点击处理"""
        # 更新按钮状态
        for btn in self.nav_buttons:
            btn.setChecked(btn.page_id == page_id)

        # 切换页面
        page_index = list(self.pages.keys()).index(page_id)
        self.page_stack.setCurrentIndex(page_index)

    def show_welcome_animation(self):
        """显示欢迎动画"""
        # 窗口淡入
        self.setWindowOpacity(0.0)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


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


class MarketEmojiPage(QWidget):
    """市场表情页面"""

    def __init__(self):
        super().__init__()
        self._worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # 页面头部
        header = PageHeader(
            "市场表情",
            "整理从QQ市场下载的表情包，支持多种命名方式"
        )
        layout.addWidget(header)

        # 配置卡片
        config_card = Card()

        # 路径配置
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

        # 表情目录
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

        # 命名方式
        naming_layout = QHBoxLayout()
        naming_layout.setSpacing(12)
        naming_layout.addWidget(QLabel("命名方式:"))
        self.naming_combo = ModernComboBox()
        self.naming_combo.addItems(["专辑名称", "专辑ID", "表情名称", "关键词"])
        naming_layout.addWidget(self.naming_combo)
        naming_layout.addStretch()
        config_card.layout.addLayout(naming_layout)

        layout.addWidget(config_card)

        # 操作卡片
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

        # 进度卡片
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

    def _set_running(self, running: bool):
        """切换运行/空闲UI状态"""
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setVisible(running)

    def _cancel_worker(self):
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("正在取消...")

    def start_organize(self):
        """开始整理（后台线程）"""
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

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

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

    def _on_error(self, msg):
        self._set_running(False)
        self._worker = None
        self.status_label.setText(f"整理失败: {msg}")
        QMessageBox.critical(self, "错误", f"整理失败: {msg}")


class FavoriteEmojiPage(QWidget):
    """收藏表情页面"""

    def __init__(self):
        super().__init__()
        self._worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # 页面头部
        header = PageHeader(
            "收藏表情",
            "整理收藏的表情，支持通过 Thumb 目录筛选个人收藏"
        )
        layout.addWidget(header)

        # 配置卡片
        config_card = Card()

        # 源目录（Ori 目录）
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

        # Thumb 目录（可选，用于筛选）
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

        # 命名规则
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

        # 筛选选项
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

        # 操作卡片
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

        # 进度卡片
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

        # 结果文本
        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("处理结果将显示在这里...")
        self.result_text.setMinimumHeight(120)
        progress_card.layout.addWidget(self.result_text)

        layout.addWidget(progress_card, 1)

    def _set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setVisible(running)

    def _cancel_worker(self):
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("正在取消...")

    def browse_thumb_dir(self):
        """浏览 Thumb 目录"""
        path = QFileDialog.getExistingDirectory(self, "选择缩略图目录(Thumb)")
        if path:
            self.thumb_input.setText(path)

    def start_organize(self):
        """开始整理（后台线程）"""
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

        # 验证 Thumb 目录
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

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_favorite_finished(self, result):
        self._set_running(False)
        self._worker = None

        if result.get("cancelled"):
            self.status_label.setText("已取消")
            self.result_text.append("操作已取消\n")
            return

        self.progress_bar.setValue(100)
        self.status_label.setText("整理完成！")
        
        # 显示筛选统计
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

    def _on_error(self, msg):
        self._set_running(False)
        self._worker = None
        self.status_label.setText(f"整理失败: {msg}")
        self.result_text.append(f"❌ 错误: {msg}\n")
        QMessageBox.critical(self, "错误", f"整理失败: {msg}")

    def browse_source_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择源目录(Ori)")
        if path:
            self.source_input.setText(path)
            # 自动检测并填充 Thumb 目录
            source_obj = Path(path)
            if source_obj.name.upper() == "ORI":
                thumb_candidate = source_obj.parent / "Thumb"
                if thumb_candidate.exists():
                    self.thumb_input.setText(str(thumb_candidate))


class ConvertPage(QWidget):
    """格式转换页面"""

    def __init__(self):
        super().__init__()
        self._worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # 页面头部
        header = PageHeader(
            "格式转换",
            "将表情包转换为微信兼容格式"
        )
        layout.addWidget(header)

        # 转换卡片
        convert_card = Card()

        # 源目录
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

        # 输出目录
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

        # 格式选择
        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)
        format_layout.addWidget(QLabel("目标格式:"))
        self.format_combo = ModernComboBox()
        self.format_combo.addItems(["GIF (推荐)", "PNG", "JPG", "WebP"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        convert_card.layout.addLayout(format_layout)

        layout.addWidget(convert_card)

        # 进度卡片
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

        # 操作卡片
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

    def _set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.cancel_btn.setVisible(running)

    def _cancel_worker(self):
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("正在取消...")

    def start_convert(self):
        """开始转换（后台线程，文件扫描也在后台进行）"""
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

        # 文件扫描已移至工作线程，避免阻塞UI
        self._set_running(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("准备转换...")

        self._worker = ConvertWorker(source_obj, output_obj)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_convert_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

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

    def _on_error(self, msg):
        self._set_running(False)
        self._worker = None
        self.status_label.setText(f"转换失败: {msg}")
        QMessageBox.critical(self, "错误", f"转换失败: {msg}")


class PreviewPage(QWidget):
    """表情包预览页面（带分页）"""

    ITEMS_PER_PAGE = 60
    COLUMNS = 6

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

        # 页面头部
        header = PageHeader(
            "表情包预览",
            "预览所有表情包，支持复制到剪贴板"
        )
        layout.addWidget(header)

        # 预览卡片
        preview_card = Card()

        # 路径选择
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

        # 状态标签
        self.status_label = QLabel("请选择表情目录并点击加载")
        self.status_label.setObjectName("info_label")
        preview_card.layout.addWidget(self.status_label)

        # 分页控制
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

        # 预览区域
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
        """加载预览"""
        path = self.preview_path_input.text()
        if not path:
            QMessageBox.warning(self, "提示", "请选择表情目录")
            return

        path_obj = Path(path)
        if not path_obj.exists():
            QMessageBox.warning(self, "错误", f"目录不存在: {path}")
            return

        # 扫描表情文件
        self.emoji_files = []
        for ext in ['*.gif', '*.png', '*.jpg', '*.jpeg', '*.webp']:
            self.emoji_files.extend(path_obj.glob(ext))
            self.emoji_files.extend(path_obj.glob(ext.upper()))

        if not self.emoji_files:
            self.status_label.setText("未找到表情文件")
            QMessageBox.information(self, "提示", "未找到表情文件")
            return

        self.current_page = 0
        self.total_pages = max(1, (len(self.emoji_files) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.status_label.setText(f"找到 {len(self.emoji_files)} 个表情文件")
        self._display_current_page()

    def _display_current_page(self):
        """显示当前页"""
        # 清空现有预览
        while self.preview_grid.count():
            item = self.preview_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        start = self.current_page * self.ITEMS_PER_PAGE
        end = min(start + self.ITEMS_PER_PAGE, len(self.emoji_files))
        page_files = self.emoji_files[start:end]

        # 创建占位标签
        for i, emoji_path in enumerate(page_files):
            preview_label = QLabel()
            preview_label.setObjectName("preview_label")
            preview_label.setFixedSize(100, 100)
            preview_label.setAlignment(Qt.AlignCenter)
            preview_label.setText("...")
            preview_label.setToolTip(emoji_path.name)
            row = i // self.COLUMNS
            col = i % self.COLUMNS
            self.preview_grid.addWidget(preview_label, row, col)

        # 更新分页控件
        self._update_page_controls()

        # 在后台加载图片
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        self._worker = PreviewLoadWorker(page_files, size=80)
        self._worker.preview_ready.connect(self._on_preview_ready)
        self._worker.start()

    def _on_preview_ready(self, index, pixmap, filename):
        """单张预览图加载完成"""
        item = self.preview_grid.itemAt(index)
        if item and item.widget():
            label = item.widget()
            if not pixmap.isNull():
                scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled)
            else:
                label.setText("❓")

    def _update_page_controls(self):
        """更新分页控件"""
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


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用字体
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    # 创建主窗口
    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
