#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块
提供统一的日志记录功能，支持控制台和文件双输出
线程安全设计
"""

import logging
import logging.handlers
import sys
import threading
from pathlib import Path
from typing import Optional

_initialized = False
_init_lock = threading.Lock()

# 日志文件最大大小 (5MB)
MAX_LOG_SIZE = 5 * 1024 * 1024
# 保留的备份文件数量
BACKUP_COUNT = 3


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> bool:
    """
    初始化日志系统（线程安全）
    
    Args:
        level: 日志级别
        log_file: 日志文件路径，为None则使用默认路径
        
    Returns:
        是否初始化成功
    """
    global _initialized
    
    with _init_lock:
        if _initialized:
            return True
        
        try:
            root_logger = logging.getLogger("qq_emoji")
            root_logger.setLevel(level)
            
            # 清除现有处理器（防止重复添加）
            root_logger.handlers.clear()
            
            formatter = logging.Formatter(
                "[%(asctime)s] [%(threadName)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            
            # 控制台输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            # 文件输出（使用 RotatingFileHandler 限制文件大小）
            if log_file is None:
                log_dir = Path(__file__).parent.parent / "data"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = str(log_dir / "app.log")
            
            try:
                # 使用 RotatingFileHandler 实现日志轮转
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=MAX_LOG_SIZE,
                    backupCount=BACKUP_COUNT,
                    encoding="utf-8"
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except OSError as e:
                root_logger.warning("无法创建日志文件: %s，仅使用控制台输出", log_file)
            
            _initialized = True
            return True
            
        except Exception as e:
            print(f"初始化日志系统失败: {e}", file=sys.stderr)
            return False


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    
    Args:
        name: 日志器名称（通常为模块名）
        
    Returns:
        Logger实例
    """
    if not _initialized:
        setup_logging()
    
    return logging.getLogger(f"qq_emoji.{name}")


def set_log_level(level: int) -> None:
    """
    设置日志级别
    
    Args:
        level: 日志级别 (logging.DEBUG, logging.INFO, etc.)
    """
    root_logger = logging.getLogger("qq_emoji")
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)
