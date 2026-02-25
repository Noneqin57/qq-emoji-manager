#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场表情分类模块
从JSON/JTMP文件读取表情信息并重命名文件
"""

import json
import shutil
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger("market_emoji")


@dataclass
class MarketEmojiInfo:
    """市场表情信息"""
    emoji_id: str
    name: str
    keywords: List[str]
    file_path: Path
    json_path: Path
    album_id: str = ""
    album_name: str = ""


class MarketEmojiClassifier:
    """市场表情分类器"""
    
    def __init__(self, json_dir: Path, emoji_dir: Path, output_dir: Path):
        """
        初始化分类器
        
        Args:
            json_dir: JSON/JTMP文件目录
            emoji_dir: 表情文件目录
            output_dir: 输出目录
        """
        self.json_dir = Path(json_dir)
        self.emoji_dir = Path(emoji_dir)
        self.output_dir = Path(output_dir)
        self.emoji_list: List[MarketEmojiInfo] = []
        
        # 图片ID -> (名称, 关键词, 专辑ID, 专辑名)
        self.name_mapping: Dict[str, tuple] = {}
        
        # 专辑ID -> 专辑信息
        self.albums: Dict[str, dict] = {}
        
        # 线程锁，保护并发操作
        self._lock = threading.Lock()
        
    def load_json_data(self) -> bool:
        """
        加载JSON/JTMP文件数据
        
        Returns:
            是否成功加载
        """
        if not self.json_dir.exists():
            logger.warning("JSON目录不存在: %s", self.json_dir)
            return False
        
        # 支持 .json 和 .jtmp 文件
        json_files = list(self.json_dir.glob("*.json")) + list(self.json_dir.glob("*.jtmp"))
        if not json_files:
            logger.warning("未找到JSON/JTMP文件: %s", self.json_dir)
            return False
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 解析表情包专辑数据
                self._parse_album_data(data, json_file)
                            
            except (json.JSONDecodeError, OSError) as e:
                logger.error("读取JSON文件失败 %s: %s", json_file, e)
                continue
        
        logger.info("成功加载 %d 个表情包专辑", len(self.albums))
        logger.info("成功加载 %d 个表情名称映射", len(self.name_mapping))
        return len(self.name_mapping) > 0
    
    def _parse_album_data(self, data: dict, json_file: Path):
        """解析表情包专辑数据"""
        # 获取专辑信息
        album_id = data.get('id', '')
        album_name = data.get('name', '未知表情包')
        album_mark = data.get('mark', '')
        
        # 保存专辑信息
        self.albums[album_id] = {
            'name': album_name,
            'mark': album_mark,
            'file': json_file.name
        }
        
        # 解析表情图片列表
        imgs = data.get('imgs', [])
        for img in imgs:
            img_id = img.get('id', '')
            img_name = img.get('name', '')
            keywords = img.get('keywords', [])
            
            if img_id and img_name:
                # 存储映射：图片ID -> (名称, 关键词, 专辑ID, 专辑名)
                self.name_mapping[img_id] = (img_name, keywords, album_id, album_name)
    
    def scan_emoji_files(self) -> List[MarketEmojiInfo]:
        """
        扫描表情文件
        
        市场表情目录结构通常为：
        marketface/
          ├── 240647/           (专辑ID文件夹)
          │   ├── abc123.png    (图片ID文件)
          │   ├── abc123_thu.png (缩略图，需要去除_thu后缀匹配)
          │   └── def456.gif
          └── 240648/
              └── ...
        
        Returns:
            表情信息列表
        """
        if not self.emoji_dir.exists():
            logger.warning("表情目录不存在: %s", self.emoji_dir)
            return []
        
        self.emoji_list = []
        
        # 支持的图片格式
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp']
        
        # 需要去除的常见后缀
        suffixes_to_remove = ['_thu', '_hd', '_big', '_small', '_preview']
        
        # 扫描表情目录及其子目录
        for ext in extensions:
            for file_path in self.emoji_dir.rglob(ext):
                # 获取图片ID（文件名，不含扩展名）
                img_id = file_path.stem
                
                # 尝试从父目录获取专辑ID
                parent_dir = file_path.parent.name
                album_id_from_path = parent_dir if parent_dir in self.albums else ""
                
                # 查找对应的名称 - 先尝试完整匹配
                matched = False
                name, keywords, album_id, album_name = img_id, [], album_id_from_path, ""
                
                if img_id in self.name_mapping:
                    name, keywords, album_id, album_name = self.name_mapping[img_id]
                    matched = True
                else:
                    # 尝试去除后缀再匹配
                    for suffix in suffixes_to_remove:
                        if img_id.endswith(suffix):
                            base_id = img_id[:-len(suffix)]
                            if base_id in self.name_mapping:
                                name, keywords, album_id, album_name = self.name_mapping[base_id]
                                matched = True
                                break
                
                if not matched:
                    # 未找到映射，使用默认值
                    name = img_id
                    keywords = []
                    album_id = album_id_from_path
                    album_name = self.albums.get(album_id_from_path, {}).get('name', '')
                
                emoji_info = MarketEmojiInfo(
                    emoji_id=img_id,
                    name=name,
                    keywords=keywords,
                    file_path=file_path,
                    json_path=self.json_dir,
                    album_id=album_id,
                    album_name=album_name
                )
                self.emoji_list.append(emoji_info)
        
        logger.info("扫描到 %d 个表情文件", len(self.emoji_list))
        return self.emoji_list
    
    def classify(self, progress_callback: Optional[Callable[[int, int], None]] = None, 
                 naming_mode: str = 'album_name') -> Dict:
        """
        执行分类（重命名并复制到输出目录）
        
        Args:
            progress_callback: 进度回调函数(current, total)
            naming_mode: 命名模式
                - 'name': 使用表情名称（如"开心.png"）
                - 'album_name': 使用专辑名+表情名（如"长一君1_爱音.png"）
                - 'keywords': 使用关键词（如"爱音.png"）
                - 'album_id': 使用专辑ID+表情名（如"240647_爱音.png"）
            
        Returns:
            分类结果统计
        """
        if not self.emoji_list:
            logger.info("没有表情文件需要分类")
            return {'total': 0, 'success': 0, 'failed': 0}

        # 创建输出目录
        market_dir = self.output_dir / "市场表情"
        market_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'total': len(self.emoji_list),
            'success': 0,
            'failed': 0,
            'output_dir': str(market_dir),
            'albums': {},
            'unmatched': 0
        }
        
        # 使用集合跟踪已使用的文件名，避免重名检查时的竞态条件
        # 使用线程锁保护并发操作
        used_names: Set[str] = set()
        
        for i, emoji in enumerate(self.emoji_list):
            try:
                # 根据命名模式生成文件名
                if naming_mode == 'album_name' and emoji.album_name:
                    # 专辑名_表情名
                    safe_album = self._safe_filename(emoji.album_name)
                    safe_name = self._safe_filename(emoji.name)
                    final_name = f"{safe_album}_{safe_name}"
                elif naming_mode == 'album_id' and emoji.album_id:
                    # 专辑ID_表情名
                    safe_name = self._safe_filename(emoji.name)
                    final_name = f"{emoji.album_id}_{safe_name}"
                elif naming_mode == 'keywords' and emoji.keywords:
                    # 使用第一个关键词
                    final_name = self._safe_filename(emoji.keywords[0])
                else:
                    # 仅使用表情名称
                    final_name = self._safe_filename(emoji.name)
                
                # 添加扩展名
                new_name = f"{final_name}{emoji.file_path.suffix}"
                dest_path = market_dir / new_name
                
                # 处理重名 - 使用线程锁保护集合操作，避免竞态条件
                with self._lock:
                    counter = 1
                    while new_name in used_names or dest_path.exists():
                        # 添加唯一标识符避免竞态条件
                        unique_id = str(uuid.uuid4())[:8]
                        new_name = f"{final_name}_{counter}_{unique_id}{emoji.file_path.suffix}"
                        dest_path = market_dir / new_name
                        counter += 1
                        # 防止无限循环
                        if counter > 1000:
                            raise RuntimeError(f"无法为文件生成唯一名称: {final_name}")
                    
                    # 记录已使用的名称（在锁内）
                    used_names.add(new_name)
                
                # 复制文件
                shutil.copy2(emoji.file_path, dest_path)
                
                # 更新统计信息（需要锁保护）
                with self._lock:
                    result['success'] += 1
                    if emoji.album_name:
                        if emoji.album_name not in result['albums']:
                            result['albums'][emoji.album_name] = 0
                        result['albums'][emoji.album_name] += 1
                    
                    if emoji.emoji_id not in self.name_mapping:
                        result['unmatched'] += 1
                
            except (OSError, RuntimeError) as e:
                logger.error("处理表情失败 %s: %s", emoji.file_path, e)
                result['failed'] += 1
            
            # 更新进度
            if progress_callback:
                progress_callback(i + 1, len(self.emoji_list))
        
        logger.info("分类完成: 成功 %d, 失败 %d", result['success'], result['failed'])
        return result
    
    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        if not name:
            return "未命名"
        
        # 移除或替换非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name.strip()
    
    def get_album_summary(self) -> str:
        """获取表情包专辑摘要"""
        lines = []
        lines.append(f"共加载 {len(self.albums)} 个表情包专辑:\n")
        lines.append("=" * 50 + "\n")
        
        for album_id, album_info in sorted(self.albums.items(), key=lambda x: x[0]):
            # 统计该专辑的表情数量
            count = sum(1 for k, v in self.name_mapping.items() if v[2] == album_id)
            lines.append(f"专辑ID: {album_id}\n")
            lines.append(f"  名称: {album_info['name']}\n")
            lines.append(f"  表情数: {count} 个\n")
            if album_info['mark']:
                mark_preview = album_info['mark'][:80] + "..." if len(album_info['mark']) > 80 else album_info['mark']
                lines.append(f"  描述: {mark_preview}\n")
            lines.append("\n")
        
        return "".join(lines)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_albums': len(self.albums),
            'total_emojis': len(self.name_mapping),
            'albums': {aid: info['name'] for aid, info in self.albums.items()}
        }
