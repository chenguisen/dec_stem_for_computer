#!/usr/bin/env python3
"""
配置管理器
用于管理应用程序配置，包括输出路径、会话文件夹设置等
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file=None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为 None 则使用默认路径
        """
        self.config_dir = self._get_config_dir()
        self.config_file = config_file or os.path.join(self.config_dir, "config.json")
        self.config = self._load_config()

    def _get_config_dir(self):
        """
        获取配置目录路径

        Returns:
            配置目录的绝对路径
        """
        # Windows: C:\Users\<用户名>\AppData\Roaming\HAADF_STEM_Config
        # Linux/macOS: ~/.config/HAADF_STEM_Config
        if sys.platform == "win32":
            config_dir = os.path.join(os.getenv('APPDATA', ''), 'HAADF_STEM_Config')
        else:
            config_dir = os.path.join(os.path.expanduser("~"), '.config', 'HAADF_STEM_Config')

        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def _load_config(self):
        """
        加载配置文件

        Returns:
            配置字典
        """
        default_config = {
            "application": {
                "name": "HAADF-STEM Image Deconvolution",
                "version": "1.0.0"
            },
            "paths": {
                "default_output": "outputs",
                "auto_create_session_folder": True,
                "session_folder_format": "session_%Y%m%d_%H%M%S"
            },
            "ui": {
                "default_theme": "Dark Mode",
                "remember_window_size": True,
                "window_width": 1400,
                "window_height": 900
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    return self._merge_config(default_config, loaded_config)
            except Exception as e:
                print(f"警告: 加载配置文件失败，使用默认配置: {e}")
                return default_config
        else:
            # 首次运行，创建默认配置文件
            self._save_config(default_config)
            return default_config

    def _merge_config(self, default, loaded):
        """
        合并配置

        Args:
            default: 默认配置
            loaded: 加载的配置

        Returns:
            合并后的配置
        """
        def deep_merge(d1, d2):
            """深度合并字典"""
            for k, v2 in d2.items():
                if k in d1 and isinstance(d1[k], dict) and isinstance(v2, dict):
                    deep_merge(d1[k], v2)
                else:
                    d1[k] = v2
            return d1

        return deep_merge(default.copy(), loaded)

    def _save_config(self, config):
        """
        保存配置文件

        Args:
            config: 要保存的配置字典
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")

    def get(self, *keys):
        """
        获取配置值

        Args:
            *keys: 配置键的路径，如 get('paths', 'default_output')

        Returns:
            配置值，如果不存在则返回 None
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def set(self, value, *keys):
        """
        设置配置值

        Args:
            value: 要设置的值
            *keys: 配置键的路径
        """
        config = self.config
        for i, key in enumerate(keys[:-1]):
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self._save_config(self.config)

    def get_output_base_path(self):
        """
        获取基础输出路径（相对于可执行文件目录）

        Returns:
            输出路径的绝对路径
        """
        # 获取可执行文件所在目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            exe_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            exe_dir = os.path.dirname(os.path.abspath(__file__))

        output_path = self.get('paths', 'default_output')

        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(output_path):
            output_path = os.path.join(exe_dir, output_path)

        return output_path

    def create_session_folder(self):
        """
        创建新的会话文件夹

        Returns:
            会话文件夹的绝对路径

        文件夹命名规则:
        - 如果 auto_create_session_folder = True:
          使用 session_folder_format 格式，支持时间戳占位符
        - 如果 auto_create_session_folder = False:
          返回固定的输出路径
        """
        base_path = self.get_output_base_path()

        auto_create = self.get('paths', 'auto_create_session_folder')

        if auto_create:
            # 自动创建带时间戳的文件夹
            folder_format = self.get('paths', 'session_folder_format', 'session_%Y%m%d_%H%M%S')

            # 格式化文件夹名称
            try:
                session_name = datetime.now().strftime(folder_format)
            except Exception as e:
                print(f"警告: 格式化文件夹名称失败，使用默认格式: {e}")
                session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")

            session_path = os.path.join(base_path, session_name)
        else:
            # 使用固定的输出路径
            session_path = base_path

        # 确保目录存在
        os.makedirs(session_path, exist_ok=True)

        return session_path

    def save_session_parameters(self, session_path, parameters):
        """
        保存会话参数到 JSON 文件

        Args:
            session_path: 会话文件夹路径
            parameters: 参数字典
        """
        try:
            param_file = os.path.join(session_path, "parameters.json")

            # 添加时间戳和版本信息
            session_info = {
                "timestamp": datetime.now().isoformat(),
                "version": self.get('application', 'version'),
                "parameters": parameters
            }

            with open(param_file, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=4, ensure_ascii=False)

            return param_file
        except Exception as e:
            print(f"警告: 保存参数文件失败: {e}")
            return None

    def get_ui_config(self):
        """
        获取 UI 配置

        Returns:
            UI 配置字典
        """
        return self.get('ui', {})

    def save_ui_config(self, ui_config):
        """
        保存 UI 配置

        Args:
            ui_config: UI 配置字典
        """
        current_ui = self.get('ui', {})
        current_ui.update(ui_config)
        self.set(current_ui, 'ui')

    def get_config_file_path(self):
        """
        获取配置文件路径（用于显示给用户）

        Returns:
            配置文件的绝对路径
        """
        return self.config_file

    def get_default_output_path(self):
        """
        获取默认输出路径（用于 UI 显示）

        Returns:
            默认输出路径字符串
        """
        return self.get('paths', 'default_output', 'outputs')


# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    config = ConfigManager()

    # 测试读取配置
    print("配置文件路径:", config.get_config_file_path())
    print("默认输出路径:", config.get_default_output_path())
    print("自动创建会话文件夹:", config.get('paths', 'auto_create_session_folder'))
    print("会话文件夹格式:", config.get('paths', 'session_folder_format'))

    # 测试创建会话文件夹
    session_folder = config.create_session_folder()
    print("\n创建的会话文件夹:", session_folder)

    # 测试保存参数
    test_params = {
        "image_path": "test.mrc",
        "voltage_kv": 300.0,
        "iterations": 15
    }
    config.save_session_parameters(session_folder, test_params)
    print("参数文件已保存:", os.path.join(session_folder, "parameters.json"))
