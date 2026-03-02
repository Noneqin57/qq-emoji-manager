#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理器模块
集中管理所有表情资源的输入输出路径
支持打包环境（Nuitka/PyInstaller）
"""

import json
import os
import sys
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from utils.logger import get_logger

logger = get_logger("path_manager")


def detect_thumb_dir(ori_path: str, thumb_dir: str = None) -> Optional[str]:
    """
    从 Ori 路径自动检测 Thumb 目录

    Args:
        ori_path: 收藏表情 Ori 目录路径
        thumb_dir: 已知的 Thumb 目录路径（优先使用）

    Returns:
        Thumb 目录路径，未检测到返回 None
    """
    if thumb_dir and Path(thumb_dir).exists():
        return thumb_dir
    path_obj = Path(ori_path)
    if path_obj.name.upper() == "ORI":
        thumb_candidate = path_obj.parent / "Thumb"
        if thumb_candidate.exists():
            return str(thumb_candidate)
    return None

def get_app_data_dir() -> Path:
    """
    获取应用程序数据目录
    支持开发环境和打包环境
    
    Returns:
        应用程序数据目录路径
    """
    if getattr(sys, 'frozen', False):
        # 打包环境（Nuitka/PyInstaller）
        if sys.platform == 'win32':
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming'))
        else:
            app_data = Path.home() / '.config'
        
        app_dir = app_data / 'QQ表情包管理器'
    else:
        # 开发环境 - 使用项目目录
        app_dir = Path(__file__).parent.parent
    
    # 确保目录存在
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


@dataclass
class EmojiPaths:
    """表情路径数据类"""
    # 输出路径
    market_output_dir: str = ""
    favorite_output_dir: str = ""
    convert_output_dir: str = ""

    # 输入路径（从QQ自动检测）
    tencent_files_path: str = ""
    qq_account: str = ""
    market_json_dir: str = ""
    market_emoji_dir: str = ""
    favorite_emoji_dir: str = ""
    favorite_thumb_dir: str = ""  # 收藏表情缩略图目录

    # 收藏表情命名
    favorite_prefix: str = "收藏"
    favorite_start_index: int = 1

    # 状态标记
    auto_detected: bool = False
    paths_valid: bool = False


class PathManager:
    """路径管理器 - 单例模式（线程安全）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._io_lock = threading.Lock()

        # 获取应用程序数据目录
        self.app_data_dir = get_app_data_dir()

        # 项目根目录（用于开发环境）
        self.project_root = Path(__file__).parent.parent

        # 默认输出目录
        if getattr(sys, 'frozen', False):
            # 打包环境 - 使用exe所在目录
            self.default_output_dir = Path(sys.executable).parent / "result"
        else:
            # 开发环境 - 使用项目目录
            self.default_output_dir = self.app_data_dir / "result"

        # 配置文件路径（放在用户数据目录）
        self.config_file = self.app_data_dir / "data" / "path_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # 路径数据
        self.paths = EmojiPaths()

        # 加载配置
        self.load_config()

        # 如果没有设置输出路径，使用默认路径
        self._ensure_default_paths()
    
    def _ensure_default_paths(self):
        """确保默认输出路径已设置"""
        default_result = str(self.default_output_dir)
        
        if not self.paths.market_output_dir:
            self.paths.market_output_dir = str(self.default_output_dir / "market")
        
        if not self.paths.favorite_output_dir:
            self.paths.favorite_output_dir = str(self.default_output_dir / "favorite")
        
        if not self.paths.convert_output_dir:
            self.paths.convert_output_dir = str(self.default_output_dir / "convert")
        
        # 确保目录存在
        self._create_output_directories()
    
    def _create_output_directories(self):
        """创建输出目录"""
        dirs = [
            self.paths.market_output_dir,
            self.paths.favorite_output_dir,
            self.paths.convert_output_dir
        ]
        
        for dir_path in dirs:
            if dir_path:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error("创建目录失败 %s: %s", dir_path, e)
    
    def load_config(self):
        """从配置文件加载路径设置"""
        with self._io_lock:
            if not self.config_file.exists():
                logger.debug("配置文件不存在，使用默认设置")
                return

            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.paths = EmojiPaths(**data)
                logger.info("已加载配置: %s", self.config_file)
            except (json.JSONDecodeError, TypeError, OSError) as e:
                logger.error("加载配置失败: %s", e)

    def save_config(self):
        """保存路径设置到配置文件"""
        with self._io_lock:
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.paths), f, ensure_ascii=False, indent=2)
                logger.info("配置已保存: %s", self.config_file)
                return True
            except OSError as e:
                logger.error("保存配置失败: %s", e)
                return False
    
    def auto_detect_from_tencent_files(self, tencent_files_path: Optional[str] = None) -> bool:
        """
        从Tencent Files路径自动检测QQ表情路径
        
        Args:
            tencent_files_path: Tencent Files路径，如果为None则尝试自动查找
            
        Returns:
            是否成功检测到路径
        """
        try:
            from core.qq_path_detector import QQPathDetector
            
            detector = QQPathDetector()
            
            # 如果提供了路径，使用它；否则尝试自动检测
            if tencent_files_path:
                detector.tencent_files_path = Path(tencent_files_path)
                detector.detect_qq_accounts()
            else:
                if not detector.auto_detect():
                    logger.warning("自动检测Tencent Files路径失败")
                    return False
            
            if not detector.qq_accounts:
                logger.warning("未检测到QQ账号")
                return False
            
            # 使用第一个QQ账号
            first_account = detector.qq_accounts[0]
            paths_info = detector.detected_paths.get(first_account)
            
            if not paths_info:
                logger.warning("未获取到路径信息")
                return False
            
            # 更新路径
            self.paths.tencent_files_path = str(detector.tencent_files_path)
            self.paths.qq_account = first_account
            self.paths.market_json_dir = str(paths_info.market_json_dir) if paths_info.market_json_dir else ""
            self.paths.market_emoji_dir = str(paths_info.market_emoji_dir) if paths_info.market_emoji_dir else ""
            self.paths.favorite_emoji_dir = str(paths_info.favorite_emoji_dir) if paths_info.favorite_emoji_dir else ""
            self.paths.favorite_thumb_dir = str(paths_info.favorite_thumb_dir) if paths_info.favorite_thumb_dir else ""
            self.paths.auto_detected = True
            
            # 验证路径
            self.paths.paths_valid = self._validate_input_paths()
            
            # 保存配置
            self.save_config()
            
            logger.info("自动检测成功: QQ=%s", first_account)
            return True

        except Exception as e:
            logger.error("自动检测失败: %s", e)
            return False
    
    def _validate_input_paths(self) -> bool:
        """验证输入路径是否有效"""
        valid_count = 0
        required_paths = [
            self.paths.market_json_dir,
            self.paths.market_emoji_dir,
            self.paths.favorite_emoji_dir
        ]
        
        for path_str in required_paths:
            if path_str and Path(path_str).exists():
                valid_count += 1
        
        # 至少有一个有效路径就算成功
        return valid_count > 0
    
    def validate_output_path(self, path: str) -> Tuple[bool, str]:
        """
        验证输出路径是否可写
        
        Returns:
            (是否有效, 错误信息)
        """
        if not path:
            return False, "路径不能为空"
        
        path_obj = Path(path)
        
        try:
            # 尝试创建目录
            path_obj.mkdir(parents=True, exist_ok=True)
            
            # 测试写入权限
            test_file = path_obj / ".write_test"
            test_file.touch()
            test_file.unlink()
            
            return True, ""
        except PermissionError:
            return False, "没有权限写入该目录"
        except OSError as e:
            return False, f"路径验证失败: {e}"
    
    def set_output_paths(self, market_dir: str = None, favorite_dir: str = None, 
                        convert_dir: str = None) -> bool:
        """
        设置输出路径
        
        Returns:
            是否全部设置成功
        """
        success = True
        
        if market_dir:
            valid, error = self.validate_output_path(market_dir)
            if valid:
                self.paths.market_output_dir = market_dir
            else:
                logger.warning("市场表情输出路径无效: %s", error)
                success = False
        
        if favorite_dir:
            valid, error = self.validate_output_path(favorite_dir)
            if valid:
                self.paths.favorite_output_dir = favorite_dir
            else:
                logger.warning("收藏表情输出路径无效: %s", error)
                success = False
        
        if convert_dir:
            valid, error = self.validate_output_path(convert_dir)
            if valid:
                self.paths.convert_output_dir = convert_dir
            else:
                logger.warning("转换输出路径无效: %s", error)
                success = False
        
        if success:
            self.save_config()
        
        return success
    
    def get_market_paths(self) -> Dict[str, str]:
        """获取市场表情相关路径"""
        return {
            "json_dir": self.paths.market_json_dir,
            "emoji_dir": self.paths.market_emoji_dir,
            "output_dir": self.paths.market_output_dir
        }
    
    def get_favorite_paths(self) -> Dict[str, str]:
        """获取收藏表情相关路径"""
        return {
            "emoji_dir": self.paths.favorite_emoji_dir,
            "thumb_dir": self.paths.favorite_thumb_dir,
            "output_dir": self.paths.favorite_output_dir
        }
    
    def get_all_paths(self) -> Dict[str, str]:
        """获取所有路径"""
        return {
            # 输入路径
            "tencent_files": self.paths.tencent_files_path,
            "qq_account": self.paths.qq_account,
            "market_json": self.paths.market_json_dir,
            "market_emoji": self.paths.market_emoji_dir,
            "favorite_emoji": self.paths.favorite_emoji_dir,
            "favorite_thumb": self.paths.favorite_thumb_dir,
            # 输出路径
            "market_output": self.paths.market_output_dir,
            "favorite_output": self.paths.favorite_output_dir,
            "convert_output": self.paths.convert_output_dir,
        }
    
    def is_auto_detected(self) -> bool:
        """检查路径是否已自动检测"""
        return self.paths.auto_detected and self.paths.paths_valid
    
    def get_status_summary(self) -> str:
        """获取路径状态摘要"""
        lines = []
        lines.append("=" * 50)
        lines.append("路径管理状态")
        lines.append("=" * 50)
        
        # 自动检测状态
        if self.paths.auto_detected:
            lines.append(f"✅ 已自动检测 (QQ: {self.paths.qq_account})")
        else:
            lines.append("❌ 未自动检测")
        
        lines.append("")
        lines.append("输入路径:")
        
        # 输入路径状态
        paths_status = [
            ("Tencent Files", self.paths.tencent_files_path),
            ("市场表情JSON", self.paths.market_json_dir),
            ("市场表情", self.paths.market_emoji_dir),
            ("收藏表情(Ori)", self.paths.favorite_emoji_dir),
            ("缩略图(Thumb)", self.paths.favorite_thumb_dir),
        ]
        
        for name, path in paths_status:
            if path and Path(path).exists():
                lines.append(f"  ✅ {name}: {path}")
            elif path:
                lines.append(f"  ⚠️  {name}: {path} (不存在)")
            else:
                lines.append(f"  ❌ {name}: 未设置")
        
        lines.append("")
        lines.append("输出路径:")
        
        # 输出路径状态
        output_status = [
            ("市场表情输出", self.paths.market_output_dir),
            ("收藏表情输出", self.paths.favorite_output_dir),
            ("转换输出", self.paths.convert_output_dir),
        ]
        
        for name, path in output_status:
            if path:
                valid, _ = self.validate_output_path(path)
                status = "✅" if valid else "❌"
                lines.append(f"  {status} {name}: {path}")
            else:
                lines.append(f"  ❌ {name}: 未设置")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


# 全局路径管理器实例
path_manager = PathManager()
