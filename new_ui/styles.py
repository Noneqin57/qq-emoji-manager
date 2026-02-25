# -*- coding: utf-8 -*-
"""
现代化样式系统
支持浅色/深色主题
"""


class StyleSheet:
    """样式表集合"""

    # 色彩系统
    PRIMARY = "#6366F1"
    PRIMARY_HOVER = "#5558E3"
    PRIMARY_LIGHT = "#EEF2FF"

    SECONDARY = "#8B5CF6"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"

    GRAY_50 = "#F9FAFB"
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    GRAY_300 = "#D1D5DB"
    GRAY_400 = "#9CA3AF"
    GRAY_500 = "#6B7280"
    GRAY_600 = "#4B5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1F2937"
    GRAY_900 = "#111827"

    WHITE = "#FFFFFF"

    # 深色主题色彩
    DARK_BG = "#0F172A"
    DARK_SURFACE = "#1E293B"
    DARK_BORDER = "#334155"
    DARK_TEXT = "#E2E8F0"
    DARK_TEXT_SECONDARY = "#94A3B8"
    DARK_INPUT_BG = "#1E293B"
    DARK_HOVER = "#334155"
    DARK_PRIMARY_LIGHT = "#312E81"

    @classmethod
    def _build_stylesheet(cls, theme="light"):
        """构建样式表"""
        if theme == "dark":
            bg = cls.DARK_BG
            surface = cls.DARK_SURFACE
            border = cls.DARK_BORDER
            text = cls.DARK_TEXT
            text_secondary = cls.DARK_TEXT_SECONDARY
            input_bg = cls.DARK_INPUT_BG
            hover_bg = cls.DARK_HOVER
            primary_light = cls.DARK_PRIMARY_LIGHT
            sidebar_bg = cls.DARK_SURFACE
            sidebar_border = cls.DARK_BORDER
            card_bg = cls.DARK_SURFACE
            title_color = cls.DARK_TEXT
            subtitle_color = cls.DARK_TEXT_SECONDARY
            btn_secondary_bg = cls.DARK_SURFACE
            btn_secondary_text = cls.DARK_TEXT
            btn_secondary_border = cls.DARK_BORDER
            btn_secondary_hover = cls.DARK_HOVER
            info_label_color = cls.DARK_TEXT_SECONDARY
            groupbox_title = cls.DARK_TEXT_SECONDARY
            progress_bg = cls.DARK_BORDER
            scrollbar_handle = cls.GRAY_600
            scrollbar_hover = cls.GRAY_500
        else:
            bg = cls.GRAY_50
            surface = cls.WHITE
            border = cls.GRAY_200
            text = cls.GRAY_800
            text_secondary = cls.GRAY_600
            input_bg = cls.WHITE
            hover_bg = cls.GRAY_100
            primary_light = cls.PRIMARY_LIGHT
            sidebar_bg = cls.WHITE
            sidebar_border = cls.GRAY_200
            card_bg = cls.WHITE
            title_color = cls.GRAY_900
            subtitle_color = cls.GRAY_500
            btn_secondary_bg = cls.WHITE
            btn_secondary_text = cls.GRAY_700
            btn_secondary_border = cls.GRAY_300
            btn_secondary_hover = cls.GRAY_50
            info_label_color = cls.GRAY_500
            groupbox_title = cls.GRAY_700
            progress_bg = cls.GRAY_200
            scrollbar_handle = cls.GRAY_300
            scrollbar_hover = cls.GRAY_400

        return f"""
        /* 全局样式 */
        QWidget {{
            font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
            font-size: 16px;
            color: {text};
        }}

        /* 主窗口 */
        QMainWindow {{
            background-color: {bg};
        }}

        /* 侧边栏 */
        #sidebar {{
            background-color: {sidebar_bg};
            border-right: 1px solid {sidebar_border};
        }}

        /* 侧边栏按钮 */
        #sidebar_btn {{
            background-color: transparent;
            border: none;
            padding: 14px 18px;
            text-align: left;
            color: {text_secondary};
            font-size: 16px;
            border-radius: 8px;
            margin: 4px 8px;
        }}

        #sidebar_btn:hover {{
            background-color: {hover_bg};
            color: {text};
        }}

        #sidebar_btn:checked {{
            background-color: {primary_light};
            color: {cls.PRIMARY};
            font-weight: 600;
        }}

        /* 主内容区 */
        #content_area {{
            background-color: {bg};
        }}

        /* 卡片 */
        #card {{
            background-color: {card_bg};
            border-radius: 12px;
            border: 1px solid {border};
        }}

        /* 标题 */
        #page_title {{
            font-size: 28px;
            font-weight: 700;
            color: {title_color};
        }}

        #page_subtitle {{
            font-size: 16px;
            color: {subtitle_color};
        }}

        /* 输入框 */
        QLineEdit {{
            padding: 12px 16px;
            border: 1px solid {border};
            border-radius: 8px;
            background-color: {input_bg};
            color: {text};
            font-size: 16px;
        }}

        QLineEdit:focus {{
            border-color: {cls.PRIMARY};
            background-color: {primary_light};
        }}

        QLineEdit:hover {{
            border-color: {cls.GRAY_400};
        }}

        /* 按钮 */
        QPushButton#primary_btn {{
            background-color: {cls.PRIMARY};
            color: {cls.WHITE};
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px;
        }}

        QPushButton#primary_btn:hover {{
            background-color: {cls.PRIMARY_HOVER};
        }}

        QPushButton#primary_btn:disabled {{
            background-color: {cls.GRAY_400};
            color: {cls.GRAY_200};
        }}

        QPushButton#secondary_btn {{
            background-color: {btn_secondary_bg};
            color: {btn_secondary_text};
            border: 1px solid {btn_secondary_border};
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 16px;
        }}

        QPushButton#secondary_btn:hover {{
            background-color: {btn_secondary_hover};
            border-color: {cls.GRAY_400};
        }}

        /* 下拉框 */
        QComboBox {{
            padding: 12px 16px;
            border: 1px solid {border};
            border-radius: 8px;
            background-color: {input_bg};
            color: {text};
            min-width: 150px;
            font-size: 16px;
        }}

        QComboBox:focus {{
            border-color: {cls.PRIMARY};
        }}

        QComboBox QAbstractItemView {{
            background-color: {surface};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {primary_light};
            selection-color: {cls.PRIMARY};
        }}

        /* 文本域 */
        QTextEdit {{
            padding: 12px;
            border: 1px solid {border};
            border-radius: 8px;
            background-color: {input_bg};
            color: {text};
            font-size: 15px;
            line-height: 1.5;
        }}

        QTextEdit:focus {{
            border-color: {cls.PRIMARY};
        }}

        /* 分组框 */
        QGroupBox {{
            font-weight: 600;
            font-size: 16px;
            border: 1px solid {border};
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            padding: 16px;
            background-color: {surface};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {groupbox_title};
        }}

        /* 进度条 */
        QProgressBar {{
            border: none;
            border-radius: 4px;
            background-color: {progress_bg};
            text-align: center;
            color: {text_secondary};
            height: 10px;
            font-size: 14px;
        }}

        QProgressBar::chunk {{
            background-color: {cls.PRIMARY};
            border-radius: 4px;
        }}

        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {scrollbar_handle};
            border-radius: 4px;
            min-height: 40px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {scrollbar_hover};
        }}

        /* 标签 */
        QLabel#info_label {{
            color: {info_label_color};
            font-size: 15px;
        }}

        QLabel#success_label {{
            color: {cls.SUCCESS};
            font-weight: 500;
        }}

        QLabel#warning_label {{
            color: {cls.WARNING};
            font-weight: 500;
        }}

        QLabel#error_label {{
            color: {cls.DANGER};
            font-weight: 500;
        }}

        /* Tab widget */
        QTabWidget::pane {{
            border: 1px solid {border};
            border-radius: 8px;
            background: {surface};
        }}

        QTabBar::tab {{
            background: {hover_bg};
            color: {text_secondary};
            padding: 14px 28px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-size: 16px;
        }}

        QTabBar::tab:selected {{
            background: {surface};
            color: {cls.PRIMARY};
            border-bottom: 2px solid {cls.PRIMARY};
        }}

        QTabBar::tab:hover {{
            background: {border};
        }}

        /* Scroll area */
        QScrollArea {{
            border: none;
            background: transparent;
        }}

        /* 预览区域容器 */
        QWidget#preview_container {{
            background-color: {surface};
        }}

        /* 表情框架 */
        QFrame#emoji_frame {{
            background-color: {card_bg};
            border: 1px solid {border};
            border-radius: 8px;
        }}

        /* 预览标签 */
        QLabel#preview_label {{
            background-color: {hover_bg};
            border-radius: 8px;
            border: 2px solid {border};
        }}

        QLabel#preview_label:hover {{
            border-color: {cls.PRIMARY};
        }}

        /* 复选框 */
        QCheckBox {{
            font-size: 16px;
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
        }}
        """

    @classmethod
    def get_main_stylesheet(cls):
        """获取浅色主样式表"""
        return cls._build_stylesheet("light")

    @classmethod
    def get_dark_stylesheet(cls):
        """获取深色主样式表"""
        return cls._build_stylesheet("dark")
