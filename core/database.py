#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情包数据库管理模块
实现表情包元数据的持久化存储
支持打包环境（Nuitka/PyInstaller）
"""

import os
import sys
import sqlite3
import json
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager
from utils.logger import get_logger

logger = get_logger("database")


def get_app_data_dir() -> Path:
    """
    获取应用程序数据目录
    支持开发环境和打包环境
    
    Returns:
        应用程序数据目录路径
    """
    if getattr(sys, 'frozen', False):
        # 打包环境（Nuitka/PyInstaller）
        # 使用用户数据目录，避免单文件模式的只读限制
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


def get_default_db_path() -> Path:
    """
    获取默认数据库路径
    
    Returns:
        数据库文件路径
    """
    app_dir = get_app_data_dir()
    data_dir = app_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "emoji.db"


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class NotFoundError(DatabaseError):
    """记录不存在异常"""
    pass


class ValidationError(DatabaseError):
    """数据验证异常"""
    pass


@dataclass
class EmojiRecord:
    """表情包记录"""
    id: Optional[int] = None
    name: str = ""
    original_path: str = ""
    new_path: str = ""
    emoji_type: str = ""  # 'market' 或 'favorite'
    category: str = ""
    tags: str = ""  # JSON格式存储标签列表
    created_at: str = ""
    updated_at: str = ""
    
    def validate(self) -> None:
        """验证记录数据的有效性"""
        if not self.name:
            raise ValidationError("表情包名称不能为空")
        if not self.original_path:
            raise ValidationError("原始路径不能为空")
        if self.emoji_type not in ('market', 'favorite', ''):
            raise ValidationError(f"无效的表情类型: {self.emoji_type}")


class EmojiDatabase:
    """表情包数据库管理器"""

    # 连接超时时间（秒）
    CONNECTION_TIMEOUT = 30

    def __init__(self, db_path: Path = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为用户数据目录下的 emoji.db
        """
        if db_path is None:
            db_path = get_default_db_path()

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 线程锁，保护并发操作
        self._lock = threading.Lock()

        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=self.CONNECTION_TIMEOUT,
                isolation_level=None  # 自动提交模式，手动控制事务
            )
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error("数据库连接错误: %s", e)
            raise DatabaseError(f"数据库连接失败: {e}") from e
        finally:
            if conn:
                conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("BEGIN")
                
                # 创建表情包表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emojis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        original_path TEXT NOT NULL,
                        new_path TEXT,
                        emoji_type TEXT NOT NULL,
                        category TEXT,
                        tags TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_emoji_type ON emojis(emoji_type)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_category ON emojis(category)
                """)
                
                conn.commit()
                logger.info("数据库初始化成功: %s", self.db_path)
        except sqlite3.Error as e:
            logger.error("初始化数据库失败: %s", e)
            raise DatabaseError(f"初始化数据库失败: {e}") from e
    
    def add_emoji(self, record: EmojiRecord) -> int:
        """
        添加表情包记录
        
        Args:
            record: 表情包记录
            
        Returns:
            新记录的ID
            
        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        record.validate()
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("BEGIN")
                    
                    cursor.execute("""
                        INSERT INTO emojis (name, original_path, new_path, emoji_type, category, tags, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.name,
                        record.original_path,
                        record.new_path,
                        record.emoji_type,
                        record.category,
                        record.tags,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    logger.info("添加表情包记录成功: id=%d, name=%s", cursor.lastrowid, record.name)
                    return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error("添加表情包记录失败: %s", e)
                raise DatabaseError(f"添加表情包记录失败: {e}") from e
    
    def add_emoji_batch(self, records: List[EmojiRecord]) -> int:
        """
        批量添加表情包记录（使用事务）
        
        Args:
            records: 表情包记录列表
            
        Returns:
            成功添加的记录数
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        if not records:
            return 0
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN")
                    
                    count = 0
                    for record in records:
                        try:
                            record.validate()
                            cursor.execute("""
                                INSERT INTO emojis (name, original_path, new_path, emoji_type, category, tags, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                record.name,
                                record.original_path,
                                record.new_path,
                                record.emoji_type,
                                record.category,
                                record.tags,
                                datetime.now().isoformat(),
                                datetime.now().isoformat()
                            ))
                            count += 1
                        except ValidationError as e:
                            logger.warning("跳过无效记录: %s", e)
                            continue
                    
                    conn.commit()
                    logger.info("批量添加表情包记录成功: %d/%d", count, len(records))
                    return count
            except sqlite3.Error as e:
                logger.error("批量添加表情包记录失败: %s", e)
                raise DatabaseError(f"批量添加表情包记录失败: {e}") from e
    
    def get_emoji(self, emoji_id: int) -> Optional[EmojiRecord]:
        """
        获取单个表情包记录
        
        Args:
            emoji_id: 表情包ID
            
        Returns:
            表情包记录，如果不存在返回None
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM emojis WHERE id = ?", (emoji_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_record(row)
                return None
        except sqlite3.Error as e:
            logger.error("获取表情包记录失败: %s", e)
            raise DatabaseError(f"获取表情包记录失败: {e}") from e
    
    def get_all_emojis(self, emoji_type: str = None, limit: int = None, offset: int = 0) -> List[EmojiRecord]:
        """
        获取所有表情包记录
        
        Args:
            emoji_type: 筛选类型 ('market' 或 'favorite')
            limit: 返回记录数量限制（用于分页）
            offset: 偏移量（用于分页）
            
        Returns:
            表情包记录列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                sql = "SELECT * FROM emojis"
                params = []
                
                if emoji_type:
                    sql += " WHERE emoji_type = ?"
                    params.append(emoji_type)
                
                sql += " ORDER BY created_at DESC"
                
                if limit is not None:
                    sql += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [self._row_to_record(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("获取表情包列表失败: %s", e)
            raise DatabaseError(f"获取表情包列表失败: {e}") from e
    
    def search_emojis(self, keyword: str) -> List[EmojiRecord]:
        """
        搜索表情包
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的表情包记录列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        if not keyword:
            return []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM emojis 
                    WHERE name LIKE ? OR category LIKE ? OR tags LIKE ?
                    ORDER BY created_at DESC
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                
                rows = cursor.fetchall()
                return [self._row_to_record(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("搜索表情包失败: %s", e)
            raise DatabaseError(f"搜索表情包失败: {e}") from e
    
    def update_emoji(self, emoji_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新表情包记录
        
        Args:
            emoji_id: 表情包ID
            updates: 要更新的字段字典
            
        Returns:
            是否更新成功
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        if not updates:
            return False
        
        # 过滤不允许更新的字段
        allowed_fields = {'name', 'original_path', 'new_path', 'emoji_type', 'category', 'tags'}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False
        
        # 添加更新时间
        filtered_updates['updated_at'] = datetime.now().isoformat()
        
        # 构建更新语句
        fields = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values()) + [emoji_id]
        
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN")
                    cursor.execute(f"UPDATE emojis SET {fields} WHERE id = ?", values)
                    conn.commit()
                    
                    success = cursor.rowcount > 0
                    if success:
                        logger.info("更新表情包记录成功: id=%d", emoji_id)
                    return success
            except sqlite3.Error as e:
                logger.error("更新表情包记录失败: %s", e)
                raise DatabaseError(f"更新表情包记录失败: {e}") from e
    
    def delete_emoji(self, emoji_id: int) -> bool:
        """
        删除表情包记录
        
        Args:
            emoji_id: 表情包ID
            
        Returns:
            是否删除成功
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN")
                    cursor.execute("DELETE FROM emojis WHERE id = ?", (emoji_id,))
                    conn.commit()
                    
                    success = cursor.rowcount > 0
                    if success:
                        logger.info("删除表情包记录成功: id=%d", emoji_id)
                    return success
            except sqlite3.Error as e:
                logger.error("删除表情包记录失败: %s", e)
                raise DatabaseError(f"删除表情包记录失败: {e}") from e
    
    def delete_all_by_type(self, emoji_type: str) -> int:
        """
        删除指定类型的所有表情包
        
        Args:
            emoji_type: 表情包类型
            
        Returns:
            删除的记录数
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("BEGIN")
                    cursor.execute("DELETE FROM emojis WHERE emoji_type = ?", (emoji_type,))
                    conn.commit()
                    
                    count = cursor.rowcount
                    logger.info("删除指定类型表情包: type=%s, count=%d", emoji_type, count)
                    return count
            except sqlite3.Error as e:
                logger.error("删除表情包失败: %s", e)
                raise DatabaseError(f"删除表情包失败: {e}") from e
    
    def export_to_json(self, output_path: Path, emoji_type: str = None) -> bool:
        """
        导出数据到JSON文件
        
        Args:
            output_path: 输出文件路径
            emoji_type: 筛选类型，None表示导出所有
            
        Returns:
            是否导出成功
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            records = self.get_all_emojis(emoji_type)
            data = [asdict(record) for record in records]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("导出数据成功: path=%s, count=%d", output_path, len(records))
            return True
        except (OSError, json.JSONEncodeError) as e:
            logger.error("导出数据失败: %s", e)
            raise DatabaseError(f"导出数据失败: {e}") from e
    
    def import_from_json(self, json_path: Path) -> int:
        """
        从JSON文件导入数据
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            导入的记录数
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            json_path = Path(json_path)
            if not json_path.exists():
                raise DatabaseError(f"JSON文件不存在: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise DatabaseError("JSON文件格式错误：应为数组")
            
            records = []
            for item in data:
                try:
                    record = EmojiRecord(**item)
                    records.append(record)
                except TypeError as e:
                    logger.warning("跳过无效记录: %s", e)
                    continue
            
            return self.add_emoji_batch(records)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("导入数据失败: %s", e)
            raise DatabaseError(f"导入数据失败: {e}") from e
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 总数量
                cursor.execute("SELECT COUNT(*) FROM emojis")
                total = cursor.fetchone()[0]
                
                # 按类型统计
                cursor.execute("SELECT emoji_type, COUNT(*) FROM emojis GROUP BY emoji_type")
                type_counts = dict(cursor.fetchall())
                
                # 按分类统计
                cursor.execute("SELECT category, COUNT(*) FROM emojis WHERE category != '' GROUP BY category")
                category_counts = dict(cursor.fetchall())
                
                return {
                    'total': total,
                    'by_type': type_counts,
                    'by_category': category_counts
                }
        except sqlite3.Error as e:
            logger.error("获取统计信息失败: %s", e)
            raise DatabaseError(f"获取统计信息失败: {e}") from e
    
    def _row_to_record(self, row) -> EmojiRecord:
        """将数据库行转换为记录对象"""
        if hasattr(row, 'keys'):
            return EmojiRecord(
                id=row['id'],
                name=row['name'],
                original_path=row['original_path'],
                new_path=row['new_path'],
                emoji_type=row['emoji_type'],
                category=row['category'],
                tags=row['tags'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return EmojiRecord(
            id=row[0],
            name=row[1],
            original_path=row[2],
            new_path=row[3],
            emoji_type=row[4],
            category=row[5],
            tags=row[6],
            created_at=row[7],
            updated_at=row[8]
        )
    
    def backup_database(self, backup_path: Path) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否备份成功
        """
        try:
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            return True
        except sqlite3.Error as e:
            logger.error("备份数据库失败: %s", e)
            return False
    
    def restore_database(self, backup_path: Path) -> bool:
        """
        恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否恢复成功
        """
        try:
            with sqlite3.connect(backup_path) as source:
                with sqlite3.connect(self.db_path) as target:
                    source.backup(target)
            return True
        except sqlite3.Error as e:
            logger.error("恢复数据库失败: %s", e)
            return False
