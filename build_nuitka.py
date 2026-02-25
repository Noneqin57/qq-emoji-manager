#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka打包脚本
解决沙箱环境下缓存目录权限问题
"""

import os
import sys
import subprocess
from pathlib import Path

project_dir = Path(__file__).parent
cache_dir = project_dir / ".nuitka_cache"
cache_dir.mkdir(parents=True, exist_ok=True)

os.environ["NUITKA_CACHE_DIR"] = str(cache_dir)
os.environ["NUITKA_HOME"] = str(cache_dir)

cmd = [
    sys.executable, "-m", "nuitka",
    "--standalone",
    "--onefile",
    "--windows-console-mode=disable",
    "--enable-plugin=pyqt5",
    "--include-data-files=app_icon.ico=app_icon.ico",
    "--windows-icon-from-ico=app_icon.ico",
    "--output-dir=dist",
    "--assume-yes-for-downloads",
    "--follow-imports",
    "--include-package=core",
    "--include-package=new_ui",
    "--include-package=utils",
    "main.py"
]

print(f"缓存目录: {cache_dir}")
print(f"执行命令: {' '.join(cmd)}")
print("=" * 60)

result = subprocess.run(cmd, cwd=project_dir, env=os.environ)
sys.exit(result.returncode)
