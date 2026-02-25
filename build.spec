# -*- mode: python ; coding: utf-8 -*-
"""
QQ表情包管理器 - PyInstaller 打包配置

使用方法:
    pyinstaller build.spec              # 目录模式打包
    pyinstaller --onefile build.spec    # 单文件模式打包
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

PROJECT_DIR = os.path.abspath(os.path.dirname(SPEC))

hidden_imports = [
    'PyQt5',
    'PyQt5.sip',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'core',
    'core.database',
    'core.market_emoji',
    'core.favorite_emoji',
    'core.qq_path_detector',
    'new_ui',
    'new_ui.main_window',
    'new_ui.components',
    'new_ui.styles',
    'new_ui.base_page',
    'new_ui.settings_page',
    'new_ui.workers',
    'utils',
    'utils.clipboard',
    'utils.format_converter',
    'utils.logger',
    'utils.path_manager',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageFilter',
    'PIL.GifImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.WebPImagePlugin',
    'PIL.BmpImagePlugin',
    'sqlite3',
    'logging',
    'logging.handlers',
    'dataclasses',
    'win32clipboard',
    'win32con',
    'winreg',
]

excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'pytest',
    'unittest',
    'IPython',
    'jupyter',
    'PyQt5.QtBluetooth',
    'PyQt5.QtDBus',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtLocation',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuick3D',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtRemoteObjects',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtTest',
    'PyQt5.QtTextToSpeech',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebSockets',
    'PyQt5.QtWinExtras',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
    'PyQt5.QAxContainer',
]

a = Analysis(
    [os.path.join(PROJECT_DIR, 'main.py')],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_DIR, 'app_icon.ico'), '.'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries = [b for b in a.binaries if not b[0].startswith('api-ms-win-')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QQEmojiManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_DIR, 'app_icon.ico'),
    version_info=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QQEmojiManager',
)
