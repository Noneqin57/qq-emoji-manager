#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板操作模块
实现表情包复制到系统剪贴板功能
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image
import io
from utils.logger import get_logger

logger = get_logger("clipboard")

# Windows剪贴板API
if sys.platform == 'win32':
    import win32clipboard
    from win32con import CF_DIB, CF_BITMAP


def copy_image_to_clipboard(image_path: Path) -> bool:
    """
    复制图片到剪贴板
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        是否复制成功
    """
    if sys.platform != 'win32':
        logger.warning("剪贴板功能仅支持Windows系统")
        return False

    try:
        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning("文件不存在: %s", image_path)
            return False
        
        # 打开图片并转换为DIB格式
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果需要）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 保存为DIB格式到内存
            output = io.BytesIO()
            img.save(output, 'BMP')
            data = output.getvalue()
            output.close()
            
            # 移除BMP文件头，只保留DIB数据
            dib_data = data[14:]
        
        # 打开剪贴板并设置数据
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(CF_DIB, dib_data)
        win32clipboard.CloseClipboard()
        
        return True

    except (OSError, Image.UnidentifiedImageError) as e:
        logger.error("复制到剪贴板失败: %s", e)
        return False


def copy_file_to_clipboard(file_path: Path) -> bool:
    """
    复制文件到剪贴板（支持拖拽粘贴）
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否复制成功
    """
    if sys.platform != 'win32':
        logger.warning("剪贴板功能仅支持Windows系统")
        return False

    try:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning("文件不存在: %s", file_path)
            return False
        
        # 使用PowerShell复制文件到剪贴板
        ps_script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $fileList = New-Object System.Collections.Specialized.StringCollection
        $fileList.Add("{file_path.resolve()}")
        [System.Windows.Forms.Clipboard]::SetFileDropList($fileList)
        '''
        
        subprocess.run(['powershell', '-Command', ps_script], check=True)
        return True

    except (OSError, subprocess.SubprocessError) as e:
        logger.error("复制文件到剪贴板失败: %s", e)
        return False


def get_clipboard_image() -> Optional[Image.Image]:
    """
    从剪贴板获取图片
    
    Returns:
        PIL Image对象，如果没有图片返回None
    """
    if sys.platform != 'win32':
        return None
    
    try:
        win32clipboard.OpenClipboard()
        
        # 检查是否有DIB数据
        if win32clipboard.IsClipboardFormatAvailable(CF_DIB):
            dib_data = win32clipboard.GetClipboardData(CF_DIB)
            win32clipboard.CloseClipboard()
            
            # 添加BMP文件头
            bmp_header = b'BM' + (len(dib_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00' + (14).to_bytes(4, 'little')
            bmp_data = bmp_header + dib_data
            
            # 从内存加载图片
            image = Image.open(io.BytesIO(bmp_data))
            return image
        
        win32clipboard.CloseClipboard()
        return None
        
    except (OSError, ValueError) as e:
        logger.error("从剪贴板获取图片失败: %s", e)
        return None
