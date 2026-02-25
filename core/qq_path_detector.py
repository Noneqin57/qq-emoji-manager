#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ路径自动检测模块
通过Tencent Files根目录自动定位表情资源
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger("qq_path_detector")


class PathSecurityError(Exception):
    """路径安全异常"""
    pass


def validate_path(path: Path, base_dir: Path = None) -> bool:
    """
    验证路径安全性
    
    Args:
        path: 要验证的路径
        base_dir: 基准目录，如果提供则检查路径是否在基准目录内
        
    Returns:
        路径是否安全有效
    """
    try:
        # 首先检查原始路径字符串中的危险模式
        original_path_str = str(path)
        dangerous_patterns = ['..', '~', '$']
        for pattern in dangerous_patterns:
            if pattern in original_path_str:
                logger.warning("路径包含危险模式: %s", path)
                return False
        
        resolved = path.resolve()
        
        # 如果提供了基准目录，检查路径是否在基准目录内
        if base_dir:
            base_resolved = base_dir.resolve()
            try:
                resolved.relative_to(base_resolved)
            except ValueError:
                logger.warning("路径不在基准目录内: %s", path)
                return False
        
        return True
    except (OSError, ValueError) as e:
        logger.error("路径验证失败: %s", e)
        return False


def safe_path_join(base: Path, *parts) -> Optional[Path]:
    """
    安全地连接路径，防止路径遍历攻击
    
    Args:
        base: 基准路径
        *parts: 路径组件
        
    Returns:
        安全的路径，如果检测到路径遍历则返回None
    """
    try:
        result = base
        for part in parts:
            # 移除危险字符
            safe_part = str(part).replace('..', '').replace('~', '')
            if not safe_part:
                continue
            result = result / safe_part
        
        # 验证最终路径
        if validate_path(result, base):
            return result
        return None
    except (TypeError, ValueError) as e:
        logger.error("路径连接失败: %s", e)
        return None


@dataclass
class QQEmojiPaths:
    """QQ表情路径集合"""
    tencent_files_root: Path
    qq_account: str
    
    # 收藏表情路径（Ori 目录 - 原始文件）
    favorite_emoji_dir: Path
    
    # 市场表情路径
    market_emoji_dir: Path
    
    # 市场表情JSON路径
    market_json_dir: Path
    
    # 收藏表情缩略图路径（Thumb 目录 - 用于筛选个人收藏）
    favorite_thumb_dir: Optional[Path] = None
    
    # 是否存在
    favorite_exists: bool = False
    favorite_thumb_exists: bool = False
    market_exists: bool = False
    json_exists: bool = False


class QQPathDetector:
    """QQ路径检测器"""
    
    # QQ账号格式验证（纯数字，5-12位）
    QQ_ACCOUNT_PATTERN = re.compile(r'^\d{5,12}$')
    
    def __init__(self, tencent_files_path: Optional[Path] = None):
        """
        初始化检测器
        
        Args:
            tencent_files_path: Tencent Files目录路径，如果为None则尝试自动检测
        """
        self.tencent_files_path = None
        self.qq_accounts: List[str] = []
        self.detected_paths: Dict[str, QQEmojiPaths] = {}
        
        # 验证并设置路径
        if tencent_files_path is not None:
            self.set_tencent_files_path(tencent_files_path)
    
    def set_tencent_files_path(self, path) -> bool:
        """
        设置Tencent Files路径（带验证）
        
        Args:
            path: 路径对象或字符串
            
        Returns:
            是否设置成功
        """
        try:
            path = Path(path)
            
            # 验证路径安全性
            if not validate_path(path):
                logger.warning("路径验证失败: %s", path)
                return False
            
            if not path.exists():
                logger.warning("路径不存在: %s", path)
                return False
            
            if not path.is_dir():
                logger.warning("路径不是目录: %s", path)
                return False
            
            self.tencent_files_path = path
            logger.info("设置Tencent Files路径: %s", path)
            return True
        except (TypeError, ValueError) as e:
            logger.error("设置路径失败: %s", e)
            return False
        
    def detect_qq_accounts(self) -> List[str]:
        """
        检测QQ账号目录
        
        Returns:
            QQ账号列表
        """
        if not self.tencent_files_path or not self.tencent_files_path.exists():
            logger.warning("Tencent Files路径未设置或不存在")
            return []
        
        self.qq_accounts = []
        
        try:
            # 遍历Tencent Files目录下的数字文件夹（QQ号）
            for item in self.tencent_files_path.iterdir():
                if item.is_dir() and self._is_valid_qq_account(item.name):
                    self.qq_accounts.append(item.name)
        except PermissionError as e:
            logger.error("权限不足，无法遍历目录: %s", e)
        except OSError as e:
            logger.error("遍历目录失败: %s", e)
        
        logger.info("检测到 %d 个QQ账号", len(self.qq_accounts))
        return self.qq_accounts
    
    def _is_valid_qq_account(self, account: str) -> bool:
        """
        验证QQ账号格式
        
        Args:
            account: 账号字符串
            
        Returns:
            是否为有效的QQ账号格式
        """
        return bool(self.QQ_ACCOUNT_PATTERN.match(account))
    
    def detect_emoji_paths(self, qq_account: str) -> Optional[QQEmojiPaths]:
        """
        检测指定QQ账号的表情路径
        
        Args:
            qq_account: QQ账号
            
        Returns:
            表情路径对象，如果未找到返回None
        """
        # 验证QQ账号格式
        if not self._is_valid_qq_account(qq_account):
            logger.warning("无效的QQ账号格式: %s", qq_account)
            return None
        
        if not self.tencent_files_path:
            logger.warning("Tencent Files路径未设置")
            return None
        
        # 安全地构建QQ路径
        qq_path = safe_path_join(self.tencent_files_path, qq_account)
        if qq_path is None or not qq_path.exists():
            logger.warning("QQ账号目录不存在: %s", qq_account)
            return None
        
        try:
            # 构建路径 - 使用安全路径连接
            # 新QQ路径 (nt_qq)
            nt_qq_path = safe_path_join(qq_path, "nt_qq", "nt_data", "Emoji")
            if nt_qq_path is None:
                logger.warning("无法构建表情路径")
                return None
            
            # 收藏表情路径（Ori 目录 - 原始文件）
            favorite_path = safe_path_join(nt_qq_path, "personal_emoji", "Ori")
            
            # 收藏表情缩略图路径（Thumb 目录 - 用于筛选个人收藏）
            thumb_path = safe_path_join(nt_qq_path, "personal_emoji", "Thumb")
            
            # 市场表情路径
            market_path = safe_path_join(nt_qq_path, "marketface")
            
            # JSON路径
            json_path = safe_path_join(market_path, "json") if market_path else None
            
            # 检查路径是否存在
            favorite_exists = favorite_path is not None and favorite_path.exists()
            thumb_exists = thumb_path is not None and thumb_path.exists()
            market_exists = market_path is not None and market_path.exists()
            json_exists = json_path is not None and json_path.exists()
            
            # 如果新路径不存在，尝试旧路径
            if not favorite_exists and not market_exists:
                # 旧QQ路径
                old_emoji_path = safe_path_join(qq_path, "Image", "Group2")
                if old_emoji_path and old_emoji_path.exists():
                    favorite_path = old_emoji_path
                    favorite_exists = True
                    # 旧路径没有 Thumb 目录
                    thumb_path = None
                    thumb_exists = False
            
            # 确保路径不为None
            if favorite_path is None or market_path is None or json_path is None:
                logger.warning("无法构建完整的表情路径")
                return None
            
            emoji_paths = QQEmojiPaths(
                tencent_files_root=self.tencent_files_path,
                qq_account=qq_account,
                favorite_emoji_dir=favorite_path,
                market_emoji_dir=market_path,
                market_json_dir=json_path,
                favorite_thumb_dir=thumb_path,
                favorite_exists=favorite_exists,
                favorite_thumb_exists=thumb_exists,
                market_exists=market_exists,
                json_exists=json_exists
            )
            
            self.detected_paths[qq_account] = emoji_paths
            logger.info("检测到QQ %s的表情路径: 收藏Ori=%s, 收藏Thumb=%s, 市场=%s, JSON=%s", 
                       qq_account, favorite_exists, thumb_exists, market_exists, json_exists)
            
            return emoji_paths
            
        except (OSError, ValueError) as e:
            logger.error("检测表情路径失败: %s", e)
            return None
    
    def auto_detect(self) -> bool:
        """
        自动检测所有QQ账号的表情路径
        
        Returns:
            是否检测到任何路径
        """
        # 如果没有指定路径，尝试自动检测
        if not self.tencent_files_path:
            found_path = self._find_tencent_files()
            if found_path:
                self.set_tencent_files_path(found_path)
        
        if not self.tencent_files_path or not self.tencent_files_path.exists():
            logger.warning("无法自动检测Tencent Files路径")
            return False
        
        # 检测所有QQ账号
        self.detect_qq_accounts()
        
        if not self.qq_accounts:
            logger.warning("未检测到QQ账号")
            return False
        
        # 检测每个账号的表情路径
        for account in self.qq_accounts:
            self.detect_emoji_paths(account)
        
        success = len(self.detected_paths) > 0
        if success:
            logger.info("自动检测成功，发现 %d 个账号的表情路径", len(self.detected_paths))
        return success
    
    def _find_tencent_files(self) -> Optional[Path]:
        """
        自动查找Tencent Files目录
        
        Returns:
            Tencent Files路径，如果未找到返回None
        """
        # 常见路径列表
        common_paths = [
            Path("D:/QQliaotian/Tencent Files"),
            Path("C:/Users") / Path.home().name / "Documents/Tencent Files",
            Path("C:/Tencent Files"),
            Path.home() / "Tencent Files",
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        return None
    
    def get_favorite_emoji_files(self, qq_account: str) -> List[Path]:
        """
        获取收藏表情文件列表
        
        Args:
            qq_account: QQ账号
            
        Returns:
            表情文件路径列表
        """
        if qq_account not in self.detected_paths:
            return []
        
        paths = self.detected_paths[qq_account]
        if not paths.favorite_exists:
            return []
        
        emoji_files = []
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.bmp']
        
        for ext in extensions:
            emoji_files.extend(paths.favorite_emoji_dir.glob(ext))
        
        return sorted(emoji_files)
    
    def get_market_emoji_files(self, qq_account: str) -> Dict[str, List[Path]]:
        """
        获取市场表情文件列表（按子文件夹分组）
        
        Args:
            qq_account: QQ账号
            
        Returns:
            按子文件夹分组的表情文件字典
        """
        if qq_account not in self.detected_paths:
            return {}
        
        paths = self.detected_paths[qq_account]
        if not paths.market_exists:
            return {}
        
        result = {}
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp']
        
        # 遍历所有子文件夹
        for subdir in paths.market_emoji_dir.iterdir():
            if subdir.is_dir() and subdir.name != "json":
                emoji_files = []
                for ext in extensions:
                    emoji_files.extend(subdir.glob(ext))
                
                if emoji_files:
                    result[subdir.name] = sorted(emoji_files)
        
        return result
    
    def get_market_json_files(self, qq_account: str) -> List[Path]:
        """
        获取市场表情JSON文件列表
        
        Args:
            qq_account: QQ账号
            
        Returns:
            JSON文件路径列表
        """
        if qq_account not in self.detected_paths:
            return []
        
        paths = self.detected_paths[qq_account]
        if not paths.json_exists:
            return []
        
        return sorted(paths.market_json_dir.glob("*.json"))
    
    def load_market_json_data(self, json_file: Path) -> Optional[dict]:
        """
        加载市场表情JSON数据
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            JSON数据字典，失败返回None
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("加载JSON文件失败 %s: %s", json_file, e)
            return None
    
    def get_summary(self) -> str:
        """
        获取检测结果摘要
        
        Returns:
            摘要文本
        """
        lines = []
        lines.append(f"Tencent Files路径: {self.tencent_files_path}")
        lines.append(f"检测到 {len(self.qq_accounts)} 个QQ账号")
        lines.append("")
        
        for account, paths in self.detected_paths.items():
            lines.append(f"QQ账号: {account}")
            lines.append(f"  收藏表情: {'✓' if paths.favorite_exists else '✗'} {paths.favorite_emoji_dir}")
            lines.append(f"  市场表情: {'✓' if paths.market_exists else '✗'} {paths.market_emoji_dir}")
            lines.append(f"  JSON配置: {'✓' if paths.json_exists else '✗'} {paths.market_json_dir}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """测试函数"""
    # 测试自动检测
    detector = QQPathDetector()

    if detector.auto_detect():
        logger.info("检测成功!")
        logger.info(detector.get_summary())

        # 测试获取文件
        for account in detector.qq_accounts:
            favorite_files = detector.get_favorite_emoji_files(account)
            logger.info("QQ %s 收藏表情: %d 个", account, len(favorite_files))

            market_files = detector.get_market_emoji_files(account)
            logger.info("QQ %s 市场表情: %d 个子文件夹", account, len(market_files))

            json_files = detector.get_market_json_files(account)
            logger.info("QQ %s JSON文件: %d 个", account, len(json_files))
    else:
        logger.warning("未检测到Tencent Files目录")


if __name__ == "__main__":
    main()
