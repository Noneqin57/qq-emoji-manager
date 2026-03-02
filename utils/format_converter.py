#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式转换模块
实现QQ表情包格式转换为微信兼容格式
"""

import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Callable
from PIL import Image
import io
from utils.logger import get_logger

logger = get_logger("format_converter")


class WeChatEmojiConverter:
    """微信表情包转换器"""
    
    # 微信表情包规格
    WECHAT_SPECS = {
        'max_size': 500 * 1024,  # 500KB
        'max_width': 240,        # 最大宽度
        'max_height': 240,       # 最大高度
        'recommended_size': 120, # 推荐尺寸
        'formats': ['GIF', 'PNG', 'JPG', 'JPEG']
    }
    
    def __init__(self, output_dir: Path):
        """
        初始化转换器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def convert_emoji(self, input_path: Path, output_name: str = None) -> Optional[Path]:
        """
        转换单个表情包为微信格式
        
        Args:
            input_path: 输入文件路径
            output_name: 输出文件名（不含扩展名）
            
        Returns:
            输出文件路径，失败返回None
        """
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                logger.warning("文件不存在: %s", input_path)
                return None
            
            # 打开图片
            with Image.open(input_path) as img:
                # 获取原始格式
                original_format = img.format
                
                # 转换为RGBA模式（保留透明度）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # 调整尺寸
                img = self._resize_for_wechat(img)
                
                # 确定输出格式
                if original_format == 'GIF' or getattr(img, 'is_animated', False):
                    # GIF动画特殊处理
                    output_format = 'GIF'
                    output_path = self._save_gif(img, input_path, output_name)
                else:
                    # 静态图片
                    if img.mode == 'RGBA':
                        output_format = 'PNG'
                    else:
                        output_format = 'JPEG'
                    
                    output_path = self._save_static_image(img, output_format, output_name)
                
                return output_path
                
        except (OSError, Image.UnidentifiedImageError, ValueError) as e:
            logger.error("转换失败 %s: %s", input_path, e)
            return None
    
    def _resize_for_wechat(self, img: Image.Image) -> Image.Image:
        """
        调整图片尺寸以适应微信规格
        
        Args:
            img: PIL Image对象
            
        Returns:
            调整后的Image对象
        """
        width, height = img.size
        max_size = self.WECHAT_SPECS['max_width']
        
        # 如果尺寸超过限制，等比例缩放
        if width > max_size or height > max_size:
            # 计算缩放比例
            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    def _save_static_image(self, img: Image.Image, format: str, output_name: str = None) -> Path:
        """
        保存静态图片
        
        Args:
            img: PIL Image对象
            format: 输出格式
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        if output_name is None:
            output_name = f"wechat_emoji_{hash(img.tobytes())}"
        
        ext = 'png' if format == 'PNG' else 'jpg'
        output_path = self.output_dir / f"{output_name}.{ext}"
        
        # 处理重名
        counter = 1
        while output_path.exists():
            output_path = self.output_dir / f"{output_name}_{counter}.{ext}"
            counter += 1
        
        # 保存图片
        if format == 'PNG':
            img.save(output_path, 'PNG', optimize=True)
        else:
            # JPEG不支持透明度，需要转换
            if img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            img.save(output_path, 'JPEG', quality=85, optimize=True)
        
        # 检查文件大小
        self._optimize_file_size(output_path, format)
        
        return output_path
    
    def _save_gif(self, img: Image.Image, input_path: Path, output_name: str = None) -> Path:
        """
        保存GIF动画
        
        Args:
            img: PIL Image对象
            input_path: 原始文件路径
            output_name: 输出文件名
            
        Returns:
            输出文件路径
        """
        if output_name is None:
            output_name = f"wechat_emoji_{hash(img.tobytes())}"
        
        output_path = self.output_dir / f"{output_name}.gif"
        
        # 处理重名
        counter = 1
        while output_path.exists():
            output_path = self.output_dir / f"{output_name}_{counter}.gif"
            counter += 1
        
        # 尝试直接复制原GIF（如果尺寸合适）
        try:
            file_size = input_path.stat().st_size
            if file_size <= self.WECHAT_SPECS['max_size']:
                # 检查尺寸
                with Image.open(input_path) as check_img:
                    if check_img.width <= self.WECHAT_SPECS['max_width'] and \
                       check_img.height <= self.WECHAT_SPECS['max_height']:
                        shutil.copy2(input_path, output_path)
                        return output_path
        except OSError as e:
            logger.debug("直接复制GIF失败，将重新处理: %s", e)
        
        # 需要重新处理GIF
        try:
            with Image.open(input_path) as gif:
                frames = []
                
                # 处理每一帧
                for frame_num in range(getattr(gif, 'n_frames', 1)):
                    gif.seek(frame_num)
                    frame = gif.copy()
                    
                    # 调整尺寸
                    frame = self._resize_for_wechat(frame)
                    
                    # 转换为P模式（调色板）以减小文件大小
                    if frame.mode != 'P':
                        frame = frame.convert('P', palette=Image.ADAPTIVE, colors=128)
                    
                    frames.append(frame)
                
                # 保存GIF
                if frames:
                    frames[0].save(
                        output_path,
                        'GIF',
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                        optimize=True
                    )
        except (OSError, ValueError) as e:
            logger.error("处理GIF失败: %s", e)
            # 回退到复制原文件
            shutil.copy2(input_path, output_path)
        
        # 检查文件大小
        self._optimize_file_size(output_path, 'GIF')
        
        return output_path
    
    def _optimize_file_size(self, file_path: Path, format: str):
        """
        优化文件大小
        
        Args:
            file_path: 文件路径
            format: 文件格式
        """
        max_size = self.WECHAT_SPECS['max_size']
        temp_files = []  # 跟踪临时文件以便清理
        
        try:
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size <= max_size:
                return
            
            # 尝试压缩
            with Image.open(file_path) as img:
                if format == 'GIF':
                    # GIF压缩：减少颜色数
                    for colors in [128, 64, 32]:
                        temp_path = file_path.with_suffix('.temp.gif')
                        temp_files.append(temp_path)
                        try:
                            img.save(temp_path, 'GIF', optimize=True, colors=colors)
                            
                            if temp_path.stat().st_size <= max_size:
                                shutil.move(temp_path, file_path)
                                return
                        finally:
                            # 清理临时文件
                            if temp_path.exists():
                                temp_path.unlink()
                                if temp_path in temp_files:
                                    temp_files.remove(temp_path)
                else:
                    # 静态图片压缩
                    for quality in [80, 70, 60]:
                        temp_path = file_path.with_suffix('.temp.jpg')
                        temp_files.append(temp_path)
                        try:
                            if img.mode == 'RGBA':
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[-1])
                                img_rgb = background
                            else:
                                img_rgb = img.convert('RGB')
                            
                            img_rgb.save(temp_path, 'JPEG', quality=quality, optimize=True)
                            
                            if temp_path.stat().st_size <= max_size:
                                # 替换原文件
                                new_path = file_path.with_suffix('.jpg')
                                shutil.move(temp_path, new_path)
                                if new_path != file_path and file_path.exists():
                                    file_path.unlink()
                                return
                        finally:
                            # 清理临时文件
                            if temp_path.exists():
                                temp_path.unlink()
                                if temp_path in temp_files:
                                    temp_files.remove(temp_path)
        except (OSError, Image.UnidentifiedImageError) as e:
            logger.error("优化文件大小失败: %s", e)
        finally:
            # 确保所有临时文件都被清理
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except OSError as e:
                    logger.debug("清理临时文件失败 %s: %s", temp_file, e)
    
    def batch_convert(self, input_dir: Path, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """
        批量转换表情包
        
        Args:
            input_dir: 输入目录
            progress_callback: 进度回调函数
            
        Returns:
            转换结果统计
        """
        input_dir = Path(input_dir)
        if not input_dir.exists():
            logger.warning("输入目录不存在: %s", input_dir)
            return {'total': 0, 'success': 0, 'failed': 0}
        
        # 扫描所有图片文件
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.bmp']:
            image_files.extend(input_dir.glob(ext))
        
        result = {
            'total': len(image_files),
            'success': 0,
            'failed': 0,
            'output_dir': str(self.output_dir)
        }
        
        for i, image_file in enumerate(image_files):
            output_path = self.convert_emoji(image_file)
            
            if output_path:
                result['success'] += 1
            else:
                result['failed'] += 1
            
            if progress_callback:
                progress_callback(i + 1, len(image_files))
        
        logger.info("批量转换完成: 成功 %d, 失败 %d", result['success'], result['failed'])
        return result
    
    def create_wechat_sticker_pack(self, name: str, emojis: List[Path], author: str = "") -> Optional[Path]:
        """
        创建微信表情包专辑
        
        Args:
            name: 专辑名称
            emojis: 表情包文件列表
            author: 作者名称
            
        Returns:
            专辑文件路径，失败返回None
        """
        try:
            pack_dir = self.output_dir / f"{name}_微信表情包"
            pack_dir.mkdir(parents=True, exist_ok=True)
            
            # 转换所有表情包
            converted = []
            for i, emoji_path in enumerate(emojis[:16], 1):  # 微信最多16个
                output_path = self.convert_emoji(emoji_path, f"emoji_{i:02d}")
                if output_path:
                    converted.append(output_path)
            
            # 创建说明文件
            readme_path = pack_dir / "使用说明.txt"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"""微信表情包专辑: {name}
作者: {author}
表情数量: {len(converted)}

使用说明:
1. 打开微信
2. 进入"我" -> "表情"
3. 点击右上角设置图标
4. 选择"添加的单个表情"
5. 点击"+"号添加表情
6. 选择本文件夹中的图片

注意事项:
- 每个表情大小不超过500KB
- 建议尺寸为120x120像素
- 支持GIF动画表情
""")
            
            logger.info("创建表情包专辑: %s", pack_dir)
            return pack_dir

        except OSError as e:
            logger.error("创建表情包专辑失败: %s", e)
            return None
