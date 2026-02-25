#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ表情包管理器 - 统一打包脚本
支持 PyInstaller 和 Nuitka 两种打包方式

使用方法:
    python build.py              # 默认使用 PyInstaller
    python build.py --nuitka     # 使用 Nuitka
    python build.py --clean      # 清理构建产物
    python build.py --all        # 同时生成两种打包
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"


def clean():
    """清理构建产物"""
    print("=" * 50)
    print("Cleaning build artifacts...")
    print("=" * 50)
    
    dirs_to_clean = [DIST_DIR, BUILD_DIR, PROJECT_DIR / "__pycache__"]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Removing: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)
    
    for pattern in ["*.spec"]:
        for file in PROJECT_DIR.glob(pattern):
            if file.name != "build.spec":
                print(f"Removing: {file}")
                file.unlink()
    
    nuitka_cache = PROJECT_DIR / ".nuitka_cache"
    if nuitka_cache.exists():
        print(f"Removing: {nuitka_cache}")
        shutil.rmtree(nuitka_cache, ignore_errors=True)
    
    print("Clean completed!\n")


def check_dependencies(tool: str):
    """检查打包工具是否已安装"""
    if tool == "pyinstaller":
        try:
            import PyInstaller
            print(f"PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            print("Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    elif tool == "nuitka":
        try:
            import nuitka
            print("Nuitka is installed")
        except ImportError:
            print("Installing Nuitka...")
            subprocess.run([sys.executable, "-m", "pip", "install", "nuitka"], check=True)
            
            print("\nNote: Nuitka requires a C compiler (gcc or MSVC).")
            print("For Windows, you may need to install:")
            print("  - MinGW-w64: https://www.mingw-w64.org/")
            print("  - Or Visual Studio Build Tools")


def build_pyinstaller():
    """使用 PyInstaller 打包"""
    print("=" * 50)
    print("Building with PyInstaller...")
    print("=" * 50)
    
    check_dependencies("pyinstaller")
    
    spec_file = PROJECT_DIR / "build.spec"
    if not spec_file.exists():
        print(f"Error: {spec_file} not found!")
        return False
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        output_dir = DIST_DIR / "QQEmojiManager"
        print(f"\nBuild successful!")
        print(f"Output directory: {output_dir}")
        if output_dir.exists():
            exe_path = output_dir / "QQEmojiManager.exe"
            if exe_path.exists():
                print(f"Executable: {exe_path}")
                print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print(f"Build failed with code: {result.returncode}")
        return False


def build_nuitka():
    """使用 Nuitka 打包"""
    print("=" * 50)
    print("Building with Nuitka...")
    print("=" * 50)
    
    check_dependencies("nuitka")
    
    output_dir = DIST_DIR / "nuitka"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={PROJECT_DIR / 'app_icon.ico'}",
        "--enable-plugin=pyqt5",
        "--include-package=core",
        "--include-package=new_ui",
        "--include-package=utils",
        "--include-data-files=app_icon.ico=app_icon.ico",
        f"--output-dir={output_dir}",
        "--assume-yes-for-downloads",
        "--follow-imports",
        "--prefer-source-code",
        main_py := str(PROJECT_DIR / "main.py"),
    ]
    
    excludes = [
        "tkinter", "matplotlib", "numpy", "scipy", "pandas",
        "pytest", "unittest", "IPython", "jupyter",
    ]
    for excl in excludes:
        cmd.insert(-1, f"--nofollow-import-to={excl}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        print(f"\nBuild successful!")
        print(f"Output directory: {output_dir}")
        
        for exe in output_dir.glob("*.exe"):
            print(f"Executable: {exe}")
            print(f"Size: {exe.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print(f"Build failed with code: {result.returncode}")
        return False


def build_pyinstaller_onefile():
    """使用 PyInstaller 打包为单文件"""
    print("=" * 50)
    print("Building with PyInstaller (onefile)...")
    print("=" * 50)
    
    check_dependencies("pyinstaller")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--icon={PROJECT_DIR / 'app_icon.ico'}",
        "--name=QQEmojiManager",
        "--add-data=app_icon.ico;.",
        "--hidden-import=PyQt5.sip",
        "--hidden-import=core",
        "--hidden-import=core.database",
        "--hidden-import=core.market_emoji",
        "--hidden-import=core.favorite_emoji",
        "--hidden-import=core.qq_path_detector",
        "--hidden-import=new_ui",
        "--hidden-import=new_ui.main_window",
        "--hidden-import=new_ui.components",
        "--hidden-import=new_ui.styles",
        "--hidden-import=new_ui.workers",
        "--hidden-import=new_ui.settings_page",
        "--hidden-import=new_ui.base_page",
        "--hidden-import=utils",
        "--hidden-import=utils.clipboard",
        "--hidden-import=utils.format_converter",
        "--hidden-import=utils.logger",
        "--hidden-import=utils.path_manager",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.GifImagePlugin",
        "--hidden-import=PIL.PngImagePlugin",
        "--hidden-import=win32clipboard",
        "--hidden-import=win32con",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=pytest",
        str(PROJECT_DIR / "main.py"),
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        exe_path = DIST_DIR / "QQEmojiManager.exe"
        if exe_path.exists():
            print(f"\nBuild successful!")
            print(f"Executable: {exe_path}")
            print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print(f"Build failed with code: {result.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="QQ表情包管理器打包脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python build.py                    # 使用 PyInstaller 打包(目录模式)
    python build.py --onefile          # 使用 PyInstaller 打包(单文件模式)
    python build.py --nuitka           # 使用 Nuitka 打包
    python build.py --clean            # 清理构建产物
    python build.py --all              # 生成所有打包版本
        """
    )
    
    parser.add_argument(
        "--nuitka", 
        action="store_true",
        help="使用 Nuitka 打包"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="打包为单文件(仅 PyInstaller)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理构建产物"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="生成所有打包版本"
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
        return
    
    if args.all:
        clean()
        build_pyinstaller()
        build_pyinstaller_onefile()
        build_nuitka()
        return
    
    if args.nuitka:
        build_nuitka()
    elif args.onefile:
        build_pyinstaller_onefile()
    else:
        build_pyinstaller()


if __name__ == "__main__":
    main()
