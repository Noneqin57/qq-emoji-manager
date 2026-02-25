#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI页面基类模块
提供通用功能以减少代码重复
"""

from PyQt5.QtWidgets import QWidget, QProgressBar, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
from typing import Optional


class BaseWorkerPage(QWidget):
    """
    带有工作线程的页面基类
    提供通用的进度显示、取消操作等功能
    """
    
    # 子类可以重新定义这些信号
    progress_updated = pyqtSignal(int, str)
    work_finished = pyqtSignal(dict)
    work_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._is_running = False
    
    def _set_running(self, running: bool):
        """
        切换运行/空闲UI状态
        子类应该重写此方法以更新特定的UI元素
        """
        self._is_running = running
        
        # 如果有标准的按钮，更新它们的状态
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(not running)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setVisible(running)
    
    def _cancel_worker(self):
        """取消当前运行的工作线程"""
        if self._worker:
            self._worker.cancel()
            if hasattr(self, 'status_label'):
                self.status_label.setText("正在取消...")
    
    def _on_progress(self, pct: int, msg: str):
        """处理进度更新"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(pct)
        if hasattr(self, 'status_label'):
            self.status_label.setText(msg)
        
        # 发射信号供外部使用
        self.progress_updated.emit(pct, msg)
    
    def _on_error(self, error_msg: str):
        """处理错误"""
        self._set_running(False)
        self._worker = None
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"错误: {error_msg}")
        
        QMessageBox.critical(self, "错误", error_msg)
        
        # 发射信号供外部使用
        self.work_error.emit(error_msg)
    
    def _on_work_finished(self, result: dict):
        """
        处理工作完成
        子类应该重写此方法以处理特定的结果
        """
        self._set_running(False)
        self._worker = None
        
        if result.get("cancelled"):
            if hasattr(self, 'status_label'):
                self.status_label.setText("已取消")
            return
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(100)
        if hasattr(self, 'status_label'):
            self.status_label.setText("处理完成！")
        
        # 发射信号供外部使用
        self.work_finished.emit(result)
    
    def is_running(self) -> bool:
        """检查是否有工作正在运行"""
        return self._is_running
    
    def cleanup(self):
        """清理资源，在页面销毁前调用"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)  # 等待最多1秒
            self._worker = None


class ValidationMixin:
    """
    输入验证混入类
    提供常用的输入验证方法
    """
    
    @staticmethod
    def validate_path_input(path: str, field_name: str, parent=None) -> bool:
        """
        验证路径输入是否有效
        
        Args:
            path: 路径字符串
            field_name: 字段名称（用于错误提示）
            parent: 父窗口（用于显示对话框）
            
        Returns:
            路径是否有效
        """
        if not path:
            if parent:
                QMessageBox.warning(parent, "提示", f"请选择{field_name}")
            return False
        return True
    
    @staticmethod
    def validate_number_input(value: str, field_name: str, 
                              min_val: int = None, max_val: int = None,
                              parent=None) -> Optional[int]:
        """
        验证数字输入
        
        Args:
            value: 输入字符串
            field_name: 字段名称
            min_val: 最小值
            max_val: 最大值
            parent: 父窗口
            
        Returns:
            解析后的数字，如果无效返回None
        """
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                if parent:
                    QMessageBox.warning(parent, "提示", f"{field_name}不能小于{min_val}")
                return None
            if max_val is not None and num > max_val:
                if parent:
                    QMessageBox.warning(parent, "提示", f"{field_name}不能大于{max_val}")
                return None
            return num
        except ValueError:
            if parent:
                QMessageBox.warning(parent, "提示", f"{field_name}必须是有效的数字")
            return None
    
    @staticmethod
    def validate_required_input(value: str, field_name: str, parent=None) -> bool:
        """
        验证必填输入
        
        Args:
            value: 输入值
            field_name: 字段名称
            parent: 父窗口
            
        Returns:
            输入是否有效
        """
        if not value or not value.strip():
            if parent:
                QMessageBox.warning(parent, "提示", f"请输入{field_name}")
            return False
        return True
