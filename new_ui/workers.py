# -*- coding: utf-8 -*-
"""
后台线程工作器
使用 QThread 执行耗时操作，避免阻塞 UI 线程
"""

import os
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QPixmap

from utils.logger import get_logger

logger = get_logger("workers")


class WorkerThread(QThread):
    """工作线程基类"""

    progress = pyqtSignal(int, str)  # (percent, message)
    finished = pyqtSignal(dict)       # result dict
    error = pyqtSignal(str)           # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self._mutex = QMutex()

    def cancel(self):
        """请求取消"""
        self._mutex.lock()
        self._cancelled = True
        self._mutex.unlock()

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        self._mutex.lock()
        val = self._cancelled
        self._mutex.unlock()
        return val


class MarketOrganizeWorker(WorkerThread):
    """市场表情整理工作线程"""

    def __init__(self, json_dir: Path, emoji_dir: Path, output_dir: Path,
                 naming_mode: str, parent=None):
        super().__init__(parent)
        self.json_dir = json_dir
        self.emoji_dir = emoji_dir
        self.output_dir = output_dir
        self.naming_mode = naming_mode

    def run(self):
        try:
            from core.market_emoji import MarketEmojiClassifier

            self.progress.emit(10, "正在扫描文件...")
            classifier = MarketEmojiClassifier(self.json_dir, self.emoji_dir, self.output_dir)

            self.progress.emit(30, "正在解析表情信息...")
            if not classifier.load_json_data():
                self.error.emit("未找到JSON配置文件")
                return

            if self.is_cancelled():
                self.finished.emit({"cancelled": True})
                return

            self.progress.emit(50, "正在扫描表情文件...")
            emoji_list = classifier.scan_emoji_files()
            if not emoji_list:
                self.error.emit("未找到表情文件")
                return

            if self.is_cancelled():
                self.finished.emit({"cancelled": True})
                return

            total = len(emoji_list)
            self.progress.emit(70, f"找到 {total} 个表情，开始整理...")

            def progress_callback(current, total_count):
                if self.is_cancelled():
                    return
                pct = 70 + int((current / total_count) * 25)
                self.progress.emit(pct, f"正在处理: {current}/{total_count}")

            result = classifier.classify(
                progress_callback=progress_callback,
                naming_mode=self.naming_mode,
            )

            if self.is_cancelled():
                result["cancelled"] = True

            self.progress.emit(100, "整理完成！")
            self.finished.emit(result)

        except Exception as e:
            logger.exception("市场表情整理失败")
            self.error.emit(str(e))


class FavoriteOrganizeWorker(WorkerThread):
    """收藏表情整理工作线程"""

    def __init__(self, source_dir: Path, output_dir: Path,
                 prefix: str, start_index: int, thumb_dir: Path = None,
                 filter_by_thumb: bool = True, parent=None):
        super().__init__(parent)
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.prefix = prefix
        self.start_index = start_index
        self.thumb_dir = thumb_dir
        self.filter_by_thumb = filter_by_thumb

    def run(self):
        try:
            from core.favorite_emoji import FavoriteEmojiClassifier

            self.progress.emit(5, "正在初始化...")
            classifier = FavoriteEmojiClassifier(
                self.source_dir, 
                self.output_dir,
                thumb_dir=self.thumb_dir
            )
            classifier.set_naming_pattern(self.prefix, self.start_index)

            # 根据是否有 Thumb 目录决定是否筛选
            if self.thumb_dir and self.thumb_dir.exists():
                self.progress.emit(10, "正在扫描并筛选个人收藏表情...")
            else:
                self.progress.emit(10, "正在扫描文件...")

            emoji_list = classifier.scan_emoji_files(filter_by_thumb=self.filter_by_thumb)
            
            if not emoji_list:
                self.error.emit("未找到表情文件")
                return

            if self.is_cancelled():
                self.finished.emit({"cancelled": True})
                return

            # 获取扫描统计信息
            stats = classifier.get_scan_stats()
            
            # 显示筛选结果
            if self.filter_by_thumb and stats.get('total_in_thumb', 0) > 0:
                msg = f"Ori 共 {stats['total_in_ori']} 个文件, Thumb 共 {stats['total_in_thumb']} 个, 匹配 {stats['matched_count']} 个"
            else:
                msg = f"找到 {len(emoji_list)} 个表情文件"
            
            total = len(emoji_list)
            self.progress.emit(30, f"{msg}，开始整理...")

            def progress_callback(current, total_count):
                if self.is_cancelled():
                    return
                pct = 30 + int((current / total_count) * 65)
                self.progress.emit(pct, f"正在处理: {current}/{total_count}")

            result = classifier.classify(progress_callback=progress_callback)

            if self.is_cancelled():
                result["cancelled"] = True

            # 添加扫描统计到结果
            result["scan_stats"] = stats

            self.progress.emit(100, "整理完成！")
            self.finished.emit(result)

        except Exception as e:
            logger.exception("收藏表情整理失败")
            self.error.emit(str(e))


class ConvertWorker(WorkerThread):
    """格式转换工作线程（包含文件扫描）"""

    def __init__(self, source_dir: Path, output_dir: Path, parent=None):
        super().__init__(parent)
        self.source_dir = source_dir
        self.output_dir = output_dir

    def run(self):
        try:
            from utils.format_converter import WeChatEmojiConverter
            
            # 在工作线程中扫描文件
            self.progress.emit(5, "正在扫描文件...")
            image_files = []
            extensions = {'.gif', '.png', '.jpg', '.jpeg', '.webp', '.bmp'}
            
            for root, dirs, files in os.walk(self.source_dir):
                if self.is_cancelled():
                    self.finished.emit({"cancelled": True})
                    return
                    
                for file in files:
                    if self.is_cancelled():
                        self.finished.emit({"cancelled": True})
                        return
                        
                    if file.lower().endswith(tuple(extensions)):
                        image_files.append(Path(root) / file)
            
            if not image_files:
                self.error.emit("未找到图片文件")
                return
            
            total = len(image_files)
            self.progress.emit(15, f"找到 {total} 个文件，开始转换...")
            
            converter = WeChatEmojiConverter(self.output_dir)
            success_count = 0
            failed_count = 0

            for i, input_file in enumerate(image_files):
                if self.is_cancelled():
                    break

                try:
                    result_path = converter.convert_emoji(input_file, input_file.stem)
                    if result_path:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.debug("转换文件失败 %s: %s", input_file, e)
                    failed_count += 1

                pct = 15 + int((i + 1) / total * 80)
                self.progress.emit(pct, f"正在转换: {i + 1}/{total}")

            self.progress.emit(100, "转换完成！")
            self.finished.emit({
                "success": success_count,
                "failed": failed_count,
                "total": total,
                "cancelled": self.is_cancelled(),
                "output_dir": str(self.output_dir),
            })

        except Exception as e:
            logger.exception("格式转换失败")
            self.error.emit(str(e))


class PreviewLoadWorker(WorkerThread):
    """预览图加载工作线程"""

    preview_ready = pyqtSignal(int, QPixmap, str)  # (index, pixmap, filename)

    def __init__(self, emoji_files: list, size: int = 80, parent=None):
        super().__init__(parent)
        self.emoji_files = emoji_files
        self.size = size

    def run(self):
        try:
            from PIL import Image
            import io

            total = len(self.emoji_files)

            for i, emoji_path in enumerate(self.emoji_files):
                if self.is_cancelled():
                    break

                try:
                    with Image.open(emoji_path) as img:
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)

                        buffer = io.BytesIO()
                        img.save(buffer, format="PNG")
                        pixmap = QPixmap()
                        pixmap.loadFromData(buffer.getvalue())

                        self.preview_ready.emit(i, pixmap, emoji_path.name)
                except Exception:
                    pass

                if (i + 1) % 10 == 0 or i == total - 1:
                    pct = int((i + 1) / total * 100)
                    self.progress.emit(pct, f"加载预览: {i + 1}/{total}")

            self.finished.emit({
                "total": total,
                "cancelled": self.is_cancelled(),
            })

        except Exception as e:
            logger.exception("预览加载失败")
            self.error.emit(str(e))
