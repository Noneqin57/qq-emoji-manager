#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ表情包管理器 - 主入口
"""

import sys
import os
from pathlib import Path

# 检测是否在打包环境中
is_frozen = getattr(sys, 'frozen', False)

if is_frozen:
    # 打包环境：使用 _MEIPASS 作为基础路径
    base_path = Path(sys._MEIPASS)
    
    # 尝试找到 Qt 插件路径（支持单文件和目录模式）
    qt_plugin_paths = [
        base_path / "PyQt5" / "Qt5" / "plugins",
        base_path / "_internal" / "PyQt5" / "Qt5" / "plugins",
    ]
    
    for qt_plugin_path in qt_plugin_paths:
        if qt_plugin_path.exists():
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(qt_plugin_path)
            break
    
    # 添加 Qt 库到 PATH
    qt_bin_paths = [
        base_path / "PyQt5" / "Qt5" / "bin",
        base_path / "_internal" / "PyQt5" / "Qt5" / "bin",
    ]
    for qt_bin_path in qt_bin_paths:
        if qt_bin_path.exists():
            os.environ['PATH'] = str(qt_bin_path) + os.pathsep + os.environ.get('PATH', '')
else:
    # 开发环境：设置Qt平台插件路径
    venv_path = Path(sys.executable).parent.parent
    qt_plugin_paths = [
        venv_path / "Lib" / "site-packages" / "PyQt5" / "Qt5" / "plugins",
        venv_path / "lib" / "site-packages" / "PyQt5" / "Qt5" / "plugins",
    ]
    
    for plugin_path in qt_plugin_paths:
        if plugin_path.exists():
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(plugin_path)
            break

def main():
    """主函数"""
    # 导入和设置日志
    try:
        from utils.logger import setup_logging, get_logger
        setup_logging()
        logger = get_logger("main")
    except Exception as e:
        print(f"日志初始化失败: {e}", file=sys.stderr)
        logger = None

    try:
        # 导入并运行主窗口（QApplication 在 main_window 中创建）
        from new_ui.main_window import main as modern_main
        modern_main()
    except Exception as e:
        error_msg = f"启动失败: {e}"
        if logger:
            logger.exception(error_msg)
        else:
            print(error_msg, file=sys.stderr)
        
        # 显示错误对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "启动错误", f"程序启动失败:\n{e}")
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
