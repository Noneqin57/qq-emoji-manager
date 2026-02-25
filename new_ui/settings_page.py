# -*- coding: utf-8 -*-
"""
设置页面
包含导出路径设置、路径记忆和表情包预览功能（带分页和LRU缓存）
"""

import sys
from collections import OrderedDict
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QTabWidget,
    QScrollArea, QGridLayout, QFrame, QGroupBox,
    QSizePolicy, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PIL import Image
import io

# 导入路径管理器
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.path_manager import path_manager
from utils.logger import get_logger

logger = get_logger("settings_page")

ITEMS_PER_PAGE = 60
COLUMNS = 6


class LRUCache:
    """基于 OrderedDict 的 LRU 缓存"""

    def __init__(self, max_size: int = 100):
        self._cache = OrderedDict()
        self._max_size = max_size

    def get(self, key):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value

    def __contains__(self, key):
        return key in self._cache

    def clear(self):
        self._cache.clear()


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # LRU 图片缓存
        self.image_cache = LRUCache(max_size=100)

        # 分页状态
        self._market_files = []
        self._favorite_files = []
        self._market_page = 0
        self._favorite_page = 0

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 页面标题
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        layout.addWidget(title)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 导出设置标签页
        self.export_tab = self.create_export_tab()
        self.tab_widget.addTab(self.export_tab, "📁 导出设置")

        # 表情包预览标签页
        self.preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "👁 表情包预览")

        layout.addWidget(self.tab_widget)

    def create_export_tab(self):
        """创建导出设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 导出路径设置组
        path_group = QGroupBox("导出路径设置")
        path_layout = QVBoxLayout(path_group)

        # 说明文字
        desc_label = QLabel("设置表情包的默认导出保存路径。整理后的表情将被保存到此目录。")
        desc_label.setWordWrap(True)
        path_layout.addWidget(desc_label)

        # 路径输入行
        input_layout = QHBoxLayout()

        self.export_path_input = QLineEdit()
        self.export_path_input.setPlaceholderText("请选择或输入导出路径...")
        input_layout.addWidget(self.export_path_input, 1)

        browse_btn = QPushButton("📁 浏览...")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.clicked.connect(self.browse_export_path)
        input_layout.addWidget(browse_btn)

        path_layout.addLayout(input_layout)

        # 默认路径按钮
        default_btn_layout = QHBoxLayout()
        default_btn_layout.addStretch()

        use_default_btn = QPushButton("🏠 使用默认路径（桌面）")
        use_default_btn.setObjectName("secondary_btn")
        use_default_btn.clicked.connect(self.use_default_path)
        default_btn_layout.addWidget(use_default_btn)

        path_layout.addLayout(default_btn_layout)

        layout.addWidget(path_group)

        # 保存按钮
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_btn)

        layout.addLayout(save_layout)

        layout.addStretch()

        return tab

    def create_preview_tab(self):
        """创建表情包预览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 路径设置区
        path_frame = QFrame()
        path_layout = QVBoxLayout(path_frame)
        path_layout.setSpacing(8)

        # 第一行：市场表情路径
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(QLabel("市场表情:"))
        self.market_path_input = QLineEdit()
        self.market_path_input.setPlaceholderText("选择市场表情目录...")
        row1.addWidget(self.market_path_input, 1)
        market_browse_btn = QPushButton("浏览...")
        market_browse_btn.setObjectName("secondary_btn")
        market_browse_btn.clicked.connect(self.browse_market_path)
        row1.addWidget(market_browse_btn)
        path_layout.addLayout(row1)

        # 第二行：收藏表情路径（Ori 目录）
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(QLabel("收藏表情(Ori):"))
        self.favorite_path_input = QLineEdit()
        self.favorite_path_input.setPlaceholderText("选择收藏表情目录 (personal_emoji/Ori)...")
        row2.addWidget(self.favorite_path_input, 1)
        favorite_browse_btn = QPushButton("浏览...")
        favorite_browse_btn.setObjectName("secondary_btn")
        favorite_browse_btn.clicked.connect(self.browse_favorite_path)
        row2.addWidget(favorite_browse_btn)
        path_layout.addLayout(row2)

        # 第三行：缩略图目录（Thumb 目录）
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        row3.addWidget(QLabel("缩略图(Thumb):"))
        self.thumb_path_input = QLineEdit()
        self.thumb_path_input.setPlaceholderText("选择缩略图目录 (personal_emoji/Thumb)，用于筛选个人收藏...")
        row3.addWidget(self.thumb_path_input, 1)
        thumb_browse_btn = QPushButton("浏览...")
        thumb_browse_btn.setObjectName("secondary_btn")
        thumb_browse_btn.clicked.connect(self.browse_thumb_path)
        row3.addWidget(thumb_browse_btn)
        path_layout.addLayout(row3)

        # 第四行：筛选选项和加载按钮
        row4 = QHBoxLayout()
        row4.setSpacing(12)
        
        # 筛选复选框
        self.filter_favorites_checkbox = QCheckBox("仅显示个人收藏（通过 Thumb 筛选）")
        self.filter_favorites_checkbox.setChecked(True)
        self.filter_favorites_checkbox.setToolTip(
            "勾选后，收藏表情预览仅显示在 Thumb 目录中有对应缩略图的文件。\n"
            "这可以过滤掉 Ori 目录中混杂的其他表情源文件。"
        )
        row4.addWidget(self.filter_favorites_checkbox)
        
        row4.addStretch()
        
        # 加载按钮
        load_btn = QPushButton("🔄 加载预览")
        load_btn.setObjectName("primary_btn")
        load_btn.clicked.connect(self.load_preview)
        row4.addWidget(load_btn)
        
        path_layout.addLayout(row4)

        layout.addWidget(path_frame)

        # 创建子标签页
        self.preview_tabs = QTabWidget()

        # 市场表情预览页（含分页控件）
        self.market_preview_widget = self._create_paginated_preview("market")
        self.preview_tabs.addTab(self.market_preview_widget, "🛒 市场表情")

        # 收藏表情预览页
        self.favorite_preview_widget = self._create_paginated_preview("favorite")
        self.preview_tabs.addTab(self.favorite_preview_widget, "⭐ 收藏表情")

        layout.addWidget(self.preview_tabs)

        # 状态标签
        self.preview_status = QLabel("请选择表情目录并点击加载预览")
        self.preview_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_status)

        return tab

    def _create_paginated_preview(self, category: str):
        """创建带分页的预览组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 分页控制条
        page_bar = QHBoxLayout()
        page_bar.addStretch()

        prev_btn = QPushButton("< 上一页")
        prev_btn.setObjectName("secondary_btn")
        prev_btn.setVisible(False)
        page_bar.addWidget(prev_btn)

        page_label = QLabel("")
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setStyleSheet("padding: 0 16px;")
        page_bar.addWidget(page_label)

        next_btn = QPushButton("下一页 >")
        next_btn.setObjectName("secondary_btn")
        next_btn.setVisible(False)
        page_bar.addWidget(next_btn)

        page_bar.addStretch()
        layout.addLayout(page_bar)

        # 预览网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setObjectName("preview_scroll_area")

        container = QWidget()
        container.setObjectName("preview_container")
        grid = QGridLayout(container)
        grid.setSpacing(16)
        grid.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # 保存引用
        if category == "market":
            self.market_scroll = scroll
            self.market_prev_btn = prev_btn
            self.market_next_btn = next_btn
            self.market_page_label = page_label
            prev_btn.clicked.connect(lambda: self._change_page("market", -1))
            next_btn.clicked.connect(lambda: self._change_page("market", 1))
        else:
            self.favorite_scroll = scroll
            self.favorite_prev_btn = prev_btn
            self.favorite_next_btn = next_btn
            self.favorite_page_label = page_label
            prev_btn.clicked.connect(lambda: self._change_page("favorite", -1))
            next_btn.clicked.connect(lambda: self._change_page("favorite", 1))

        return widget

    def _change_page(self, category: str, delta: int):
        """翻页"""
        if category == "market":
            total = len(self._market_files)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            new_page = self._market_page + delta
            if 0 <= new_page < total_pages:
                self._market_page = new_page
                self._render_page(self.market_scroll, self._market_files, self._market_page)
                self._update_page_controls("market")
        else:
            total = len(self._favorite_files)
            total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
            new_page = self._favorite_page + delta
            if 0 <= new_page < total_pages:
                self._favorite_page = new_page
                self._render_page(self.favorite_scroll, self._favorite_files, self._favorite_page)
                self._update_page_controls("favorite")

    def _update_page_controls(self, category: str):
        """更新分页控件状态"""
        if category == "market":
            files = self._market_files
            page = self._market_page
            prev_btn = self.market_prev_btn
            next_btn = self.market_next_btn
            label = self.market_page_label
        else:
            files = self._favorite_files
            page = self._favorite_page
            prev_btn = self.favorite_prev_btn
            next_btn = self.favorite_next_btn
            label = self.favorite_page_label

        total_pages = max(1, (len(files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        has_pages = total_pages > 1

        prev_btn.setVisible(has_pages)
        next_btn.setVisible(has_pages)
        prev_btn.setEnabled(page > 0)
        next_btn.setEnabled(page < total_pages - 1)

        if has_pages:
            label.setText(f"第 {page + 1} / {total_pages} 页 (共 {len(files)} 个)")
        else:
            label.setText(f"共 {len(files)} 个" if files else "")

    def browse_export_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "选择导出目录",
            self.export_path_input.text() or str(path_manager.default_output_dir)
        )
        if path:
            self.export_path_input.setText(path)

    def use_default_path(self):
        default_path = str(path_manager.default_output_dir)
        self.export_path_input.setText(default_path)

    def save_settings(self):
        export_path = self.export_path_input.text().strip()

        if not export_path:
            QMessageBox.warning(self, "提示", "请先设置导出路径")
            return

        success = path_manager.set_output_paths(
            market_dir=export_path + "/market",
            favorite_dir=export_path + "/favorite",
            convert_dir=export_path + "/convert"
        )

        if success:
            QMessageBox.information(self, "成功", "设置已保存！")
        else:
            QMessageBox.warning(self, "警告", "部分路径设置失败，请检查路径权限")

    def load_settings(self):
        paths = path_manager.get_all_paths()

        market_output = paths.get("market_output", "")
        if market_output:
            self.export_path_input.setText(str(Path(market_output).parent))
        else:
            self.export_path_input.setText(str(path_manager.default_output_dir))

        market_emoji = paths.get("market_emoji", "")
        if market_emoji:
            self.market_path_input.setText(market_emoji)

        favorite_emoji = paths.get("favorite_emoji", "")
        if favorite_emoji:
            self.favorite_path_input.setText(favorite_emoji)
            # 自动检测并填充 Thumb 目录
            favorite_obj = Path(favorite_emoji)
            if favorite_obj.name.upper() == "ORI":
                thumb_candidate = favorite_obj.parent / "Thumb"
                if thumb_candidate.exists():
                    self.thumb_path_input.setText(str(thumb_candidate))
        
        # 如果路径管理器中有 Thumb 路径，优先使用
        favorite_thumb = paths.get("favorite_thumb", "")
        if favorite_thumb and Path(favorite_thumb).exists():
            self.thumb_path_input.setText(favorite_thumb)

        # 检查是否需要提示自动检测
        has_any_path = bool(market_emoji or favorite_emoji)
        if not has_any_path:
            self._show_auto_detect_hint()

        self.update_path_status()

    def _show_auto_detect_hint(self):
        """显示自动检测提示"""
        from PyQt5.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setWindowTitle("首次使用提示")
        msg.setText("未检测到表情路径配置")
        msg.setInformativeText(
            "您可以通过以下方式设置路径：\n\n"
            "1. 点击左侧【路径检测】页面，使用自动查找功能\n"
            "2. 在本页面手动浏览选择表情目录\n\n"
            "推荐先使用【路径检测】页面的自动查找功能。"
        )
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def update_path_status(self):
        summary = path_manager.get_status_summary()
        logger.debug(summary)

    def get_export_path(self):
        return path_manager.default_output_dir

    def browse_market_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择市场表情目录")
        if path:
            self.market_path_input.setText(path)

    def browse_thumb_path(self):
        """浏览缩略图目录"""
        path = QFileDialog.getExistingDirectory(self, "选择缩略图目录(Thumb)")
        if path:
            self.thumb_path_input.setText(path)

    def browse_favorite_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择收藏表情目录(Ori)")
        if path:
            self.favorite_path_input.setText(path)
            # 自动检测并填充 Thumb 目录
            path_obj = Path(path)
            if path_obj.name.upper() == "ORI":
                thumb_candidate = path_obj.parent / "Thumb"
                if thumb_candidate.exists():
                    self.thumb_path_input.setText(str(thumb_candidate))
                    logger.info("自动检测到 Thumb 目录: %s", thumb_candidate)

    def load_preview(self):
        """加载预览"""
        market_path = self.market_path_input.text()
        favorite_path = self.favorite_path_input.text()
        thumb_path = self.thumb_path_input.text().strip() or None
        filter_favorites = self.filter_favorites_checkbox.isChecked()

        # 加载市场表情
        if market_path and Path(market_path).exists():
            self._market_files = self._scan_emoji_files(market_path)
            self._market_page = 0
            self._render_page(self.market_scroll, self._market_files, 0)
            self._update_page_controls("market")
        else:
            self._market_files = []
            self._clear_grid(self.market_scroll)
            self._show_empty_message(self.market_scroll, "未设置市场表情目录或目录不存在")
            self._update_page_controls("market")

        # 加载收藏表情（支持筛选）
        if favorite_path and Path(favorite_path).exists():
            if filter_favorites and thumb_path and Path(thumb_path).exists():
                # 使用 Thumb 目录筛选
                self._favorite_files = self._scan_and_filter_favorites(favorite_path, thumb_path)
                logger.info("使用 Thumb 筛选: Ori=%d, Thumb=%d, 匹配=%d",
                           len(self._scan_emoji_files(favorite_path)),
                           len(list(Path(thumb_path).glob("*.png"))),
                           len(self._favorite_files))
            else:
                # 不筛选
                self._favorite_files = self._scan_emoji_files(favorite_path)
            
            self._favorite_page = 0
            self._render_page(self.favorite_scroll, self._favorite_files, 0)
            self._update_page_controls("favorite")
        else:
            self._favorite_files = []
            self._clear_grid(self.favorite_scroll)
            self._show_empty_message(self.favorite_scroll, "未设置收藏表情目录或目录不存在")
            self._update_page_controls("favorite")

        total = len(self._market_files) + len(self._favorite_files)
        self.preview_status.setText(f"已加载预览 - 共找到 {total} 个表情文件")

    def _scan_and_filter_favorites(self, ori_path: str, thumb_path: str) -> list:
        """
        扫描并筛选个人收藏表情
        通过匹配 Ori 和 Thumb 目录中的文件名来筛选
        """
        ori_dir = Path(ori_path)
        thumb_dir = Path(thumb_path)
        
        # 获取 Thumb 目录中的文件名集合（不含扩展名）
        thumb_names = set()
        for f in thumb_dir.iterdir():
            if f.is_file() and f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
                thumb_names.add(f.stem.upper())
        
        # 扫描 Ori 目录，仅保留在 Thumb 中有对应缩略图的文件
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp',
                       '*.PNG', '*.JPG', '*.JPEG', '*.GIF', '*.WEBP']
        emoji_files = []
        for ext in extensions:
            for f in ori_dir.glob(ext):
                if f.stem.upper() in thumb_names:
                    emoji_files.append(f)
        
        return sorted(set(emoji_files))

    def _scan_emoji_files(self, path: str) -> list:
        """扫描表情文件"""
        path_obj = Path(path)
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp',
                       '*.PNG', '*.JPG', '*.JPEG', '*.GIF', '*.WEBP']
        emoji_files = []
        for ext in extensions:
            emoji_files.extend(path_obj.rglob(ext))
        return sorted(set(emoji_files))

    def _render_page(self, scroll_area, all_files, page):
        """渲染指定页"""
        self._clear_grid(scroll_area)

        start = page * ITEMS_PER_PAGE
        end = min(start + ITEMS_PER_PAGE, len(all_files))
        page_files = all_files[start:end]

        if not page_files:
            self._show_empty_message(scroll_area, "没有表情文件")
            return

        container = scroll_area.widget()
        grid = container.layout()
        thumb_size = 90

        for idx, emoji_path in enumerate(page_files):
            try:
                frame = self._create_emoji_frame(emoji_path, thumb_size)
                if frame:
                    row = idx // COLUMNS
                    col = idx % COLUMNS
                    grid.addWidget(frame, row, col, alignment=Qt.AlignCenter)
            except Exception as e:
                logger.error("加载表情失败 %s: %s", emoji_path, e)

        for i in range(COLUMNS):
            grid.setColumnStretch(i, 1)

    def _create_emoji_frame(self, emoji_path, size):
        """创建表情框架"""
        frame = QFrame()
        frame.setObjectName("emoji_frame")
        frame.setFixedSize(size + 16, size + 40)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 图片标签
        img_label = QLabel()
        img_label.setFixedSize(size, size)
        img_label.setAlignment(Qt.AlignCenter)

        # 加载图片
        pixmap = self._load_thumbnail(emoji_path, size)
        if pixmap:
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("📷")

        layout.addWidget(img_label)

        # 文件名标签
        name = emoji_path.stem
        if len(name) > 10:
            name = name[:10] + "..."

        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 10px;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        return frame

    def _load_thumbnail(self, image_path, size):
        """加载缩略图（使用 LRU 缓存）"""
        cache_key = str(image_path)

        cached = self.image_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                img.thumbnail((size, size), Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())

                self.image_cache.put(cache_key, pixmap)
                return pixmap
        except Exception as e:
            logger.error("加载缩略图失败 %s: %s", image_path, e)
            return None

    def _clear_grid(self, scroll_area):
        """清空网格"""
        container = scroll_area.widget()
        grid = container.layout()

        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty_message(self, scroll_area, message):
        """显示空消息"""
        container = scroll_area.widget()
        grid = container.layout()

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        grid.addWidget(label, 0, 0, 1, COLUMNS)


def main():
    """测试函数"""
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    window = SettingsPage()
    window.setWindowTitle("设置 - QQ表情包管理器")
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
