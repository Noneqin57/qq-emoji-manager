#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收藏表情分类模块
支持自定义前缀和序号命名
支持通过 Ori/Thumb 文件名匹配筛选个人收藏表情包
"""

import shutil
from pathlib import Path
from typing import List, Optional, Callable, Dict, Set
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger("favorite_emoji")


@dataclass
class FavoriteEmojiInfo:
    """收藏表情信息"""
    original_name: str
    file_path: Path
    new_name: Optional[str] = None


@dataclass
class ScanResult:
    """扫描结果"""
    emoji_list: List[FavoriteEmojiInfo]
    total_in_ori: int
    total_in_thumb: int
    matched_count: int
    filtered_count: int


class FavoriteEmojiClassifier:
    """收藏表情分类器"""
    
    def __init__(self, emoji_dir: Path, output_dir: Path, thumb_dir: Optional[Path] = None):
        """
        初始化分类器
        
        Args:
            emoji_dir: 表情文件目录（Ori 目录）
            output_dir: 输出目录
            thumb_dir: 缩略图目录（Thumb 目录），用于筛选个人收藏表情
        """
        self.emoji_dir = Path(emoji_dir)
        self.output_dir = Path(output_dir)
        self.thumb_dir = Path(thumb_dir) if thumb_dir else None
        self.emoji_list: List[FavoriteEmojiInfo] = []
        self.prefix: str = "收藏"
        self.start_index: int = 1
        
        # 扫描统计
        self._scan_stats = {
            'total_in_ori': 0,
            'total_in_thumb': 0,
            'matched_count': 0,
            'filtered_count': 0
        }
    
    def set_naming_pattern(self, prefix: str, start_index: int = 1):
        """
        设置命名模式
        
        Args:
            prefix: 文件名前缀
            start_index: 起始序号
        """
        self.prefix = prefix.strip()
        self.start_index = start_index
    
    def set_thumb_dir(self, thumb_dir: Path):
        """
        设置缩略图目录
        
        Args:
            thumb_dir: 缩略图目录路径
        """
        self.thumb_dir = Path(thumb_dir)
    
    def get_thumb_names(self) -> Set[str]:
        """
        获取 Thumb 目录中的文件名集合（不含扩展名）
        
        Returns:
            文件名集合（大写）
        """
        if not self.thumb_dir or not self.thumb_dir.exists():
            logger.warning("Thumb 目录未设置或不存在")
            return set()
        
        thumb_names = set()
        for f in self.thumb_dir.iterdir():
            if f.is_file():
                thumb_names.add(f.stem.upper())
        
        logger.info("Thumb 目录中共有 %d 个文件", len(thumb_names))
        return thumb_names
    
    def scan_emoji_files(self, filter_by_thumb: bool = True) -> List[FavoriteEmojiInfo]:
        """
        扫描表情文件
        
        Args:
            filter_by_thumb: 是否通过 Thumb 目录筛选个人收藏表情
                - True: 仅保留在 Thumb 中有对应缩略图的文件（推荐）
                - False: 保留 Ori 目录中的所有文件
        
        Returns:
            表情信息列表
        """
        if not self.emoji_dir.exists():
            logger.warning("表情目录不存在: %s", self.emoji_dir)
            return []
        
        self.emoji_list = []
        self._scan_stats = {
            'total_in_ori': 0,
            'total_in_thumb': 0,
            'matched_count': 0,
            'filtered_count': 0
        }
        
        # 获取 Thumb 文件名集合（用于筛选）
        thumb_names = set()
        if filter_by_thumb and self.thumb_dir:
            thumb_names = self.get_thumb_names()
            self._scan_stats['total_in_thumb'] = len(thumb_names)
        
        # 支持的图片格式
        extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        
        # 扫描 Ori 目录
        all_files = []
        for file_path in sorted(self.emoji_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                all_files.append(file_path)
        
        self._scan_stats['total_in_ori'] = len(all_files)
        
        # 根据筛选模式处理文件
        if filter_by_thumb and thumb_names:
            # 筛选模式：仅保留匹配的文件
            for file_path in all_files:
                file_stem = file_path.stem.upper()
                if file_stem in thumb_names:
                    emoji_info = FavoriteEmojiInfo(
                        original_name=file_path.name,
                        file_path=file_path
                    )
                    self.emoji_list.append(emoji_info)
                    self._scan_stats['matched_count'] += 1
                else:
                    self._scan_stats['filtered_count'] += 1
            
            logger.info("扫描完成: Ori 共 %d 个文件, Thumb 共 %d 个文件, 匹配 %d 个, 过滤 %d 个",
                       self._scan_stats['total_in_ori'],
                       self._scan_stats['total_in_thumb'],
                       self._scan_stats['matched_count'],
                       self._scan_stats['filtered_count'])
        else:
            # 非筛选模式：保留所有文件
            for file_path in all_files:
                emoji_info = FavoriteEmojiInfo(
                    original_name=file_path.name,
                    file_path=file_path
                )
                self.emoji_list.append(emoji_info)
            
            logger.info("扫描完成: 共 %d 个文件（未筛选）", len(self.emoji_list))
        
        return self.emoji_list
    
    def get_scan_stats(self) -> Dict:
        """
        获取扫描统计信息
        
        Returns:
            统计信息字典
        """
        return self._scan_stats.copy()
    
    def preview_names(self) -> List[Dict]:
        """
        预览命名结果
        
        Returns:
            命名预览列表
        """
        preview = []
        
        for i, emoji in enumerate(self.emoji_list):
            index = self.start_index + i
            new_name = f"{self.prefix}_{index}{emoji.file_path.suffix}"
            
            preview.append({
                'original': emoji.original_name,
                'new_name': new_name,
                'index': index
            })
            
        return preview
    
    def classify(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """
        执行分类（重命名并复制到输出目录）
        
        Args:
            progress_callback: 进度回调函数(current, total)
            
        Returns:
            分类结果统计
        """
        if not self.emoji_list:
            logger.info("没有表情文件需要分类")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # 创建输出目录
        favorite_dir = self.output_dir / "收藏表情"
        favorite_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'total': len(self.emoji_list),
            'success': 0,
            'failed': 0,
            'output_dir': str(favorite_dir),
            'prefix': self.prefix,
            'start_index': self.start_index,
            'scan_stats': self._scan_stats
        }
        
        for i, emoji in enumerate(self.emoji_list):
            try:
                # 生成新文件名
                index = self.start_index + i
                new_name = f"{self.prefix}_{index}{emoji.file_path.suffix}"
                dest_path = favorite_dir / new_name
                
                # 处理重名（虽然使用序号不应该重名，但以防万一）
                counter = 0
                original_new_name = new_name
                while dest_path.exists():
                    counter += 1
                    new_name = f"{self.prefix}_{index}_{counter}{emoji.file_path.suffix}"
                    dest_path = favorite_dir / new_name
                
                # 复制文件
                shutil.copy2(emoji.file_path, dest_path)
                
                # 更新表情信息
                emoji.new_name = new_name
                result['success'] += 1
                
            except OSError as e:
                logger.error("处理表情失败 %s: %s", emoji.file_path, e)
                result['failed'] += 1
            
            # 更新进度
            if progress_callback:
                progress_callback(i + 1, len(self.emoji_list))
        
        logger.info("分类完成: 成功 %d, 失败 %d", result['success'], result['failed'])
        return result
