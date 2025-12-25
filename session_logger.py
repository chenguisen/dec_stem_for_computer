#!/usr/bin/env python3
"""
会话日志记录器
用于记录处理过程、参数和结果
"""

import os
import sys
from datetime import datetime


class SessionLogger:
    """会话日志记录类"""

    def __init__(self, session_path):
        """
        初始化日志记录器

        Args:
            session_path: 会话文件夹路径
        """
        self.session_path = session_path
        self.log_file = os.path.join(session_path, "log.txt")

    def start_session(self):
        """开始会话，写入开始信息"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("HAADF-STEM Image Deconvolution - Processing Log\n")
            f.write("="*70 + "\n\n")
            f.write(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Session folder: {self.session_path}\n")
            f.write(f"System: {sys.platform}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write("\n" + "-"*70 + "\n\n")

    def log_parameters(self, parameters):
        """
        记录处理参数

        Args:
            parameters: 参数字典
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n--- Parameters ---\n")
            for key, value in parameters.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "-"*70 + "\n\n")

    def log(self, message, level="INFO"):
        """
        记录日志消息

        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    def log_progress(self, progress):
        """
        记录进度消息

        Args:
            progress: 进度消息
        """
        self.log(progress, "PROGRESS")

    def log_error(self, error_message):
        """
        记录错误消息

        Args:
            error_message: 错误消息
        """
        self.log(error_message, "ERROR")

    def log_warning(self, warning_message):
        """
        记录警告消息

        Args:
            warning_message: 警告消息
        """
        self.log(warning_message, "WARNING")

    def log_result(self, result_info):
        """
        记录结果信息

        Args:
            result_info: 结果信息字典
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n--- Results ---\n")
            for key, value in result_info.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "-"*70 + "\n\n")

    def log_saved_files(self, saved_files):
        """
        记录保存的文件

        Args:
            saved_files: 已保存文件路径列表
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n--- Saved Files ---\n")
            for file_path in saved_files:
                f.write(f"- {file_path}\n")
            f.write("\n" + "-"*70 + "\n\n")

    def end_session(self):
        """结束会话，写入结束信息"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "="*70 + "\n")
            f.write(f"Session completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n")

    def get_log_file(self):
        """
        获取日志文件路径

        Returns:
            日志文件的绝对路径
        """
        return self.log_file


# 使用示例
if __name__ == "__main__":
    import tempfile

    # 创建临时会话文件夹进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = SessionLogger(temp_dir)

        # 开始会话
        logger.start_session()

        # 记录参数
        params = {
            "voltage_kv": 300.0,
            "defocus_nm": -44.0,
            "iterations": 15
        }
        logger.log_parameters(params)

        # 记录进度
        logger.log_progress("Loading image...")
        logger.log_progress("Generating probe...")
        logger.log_progress("Running deconvolution...")

        # 记录结果
        results = {
            "output_shape": "(512, 512)",
            "processing_time": "12.5s"
        }
        logger.log_result(results)

        # 记录保存的文件
        saved_files = [
            os.path.join(temp_dir, "original.mrc"),
            os.path.join(temp_dir, "probe.mrc"),
            os.path.join(temp_dir, "result.mrc")
        ]
        logger.log_saved_files(saved_files)

        # 结束会话
        logger.end_session()

        print(f"日志已创建: {logger.get_log_file()}")
        print("\n日志内容:")
        with open(logger.get_log_file(), 'r', encoding='utf-8') as f:
            print(f.read())
