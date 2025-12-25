# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
用于打包 HAADF-STEM Deconvolution 为 Windows 可执行文件
"""

import os
import sys

# 基础配置
block_cipher = None  # 加密（可选）

# 主应用程序
a = Analysis(
    ['deconvolution_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 包含 stem_deconv 模块
        ('stem_deconv', 'stem_deconv'),
        # 包含测试数据（可选）
        ('testdata', 'testdata'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'numpy',
        'scipy',
        'matplotlib',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.figure',
        'mrcfile',
        'numba',  # 如果使用 numba
        'skimage',  # 如果使用 scikit-image
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib.tests',
        'numpy.tests',
        'scipy.tests',
        'tkinter',
        'pandas',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 可执行文件配置
exe = EXE(
    a,
    None,
    [],
    'HAADF_STEM_Deconvolution',
    None,
    False,
    'icon=icon.ico' if os.path.exists('icon.ico') else None,
    'v',
    '1.0.0',
    '1.0.0',
    'Copyright 2025',
    'HAADF-STEM Image Deconvolution',
    'HAADF-STEM Image Deconvolution Tool',
    '<http://github.com/chenguisen/dec_stem_for_computer>',
    'HAADF_STEM_Deconvolution',
    False,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    console=False,  # 不显示控制台窗口（GUI 应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    name='HAADF_STEM_Deconvolution',
)

# 收集包配置
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HAADF_STEM_Deconvolution',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    exclude_binaries=True,
    name='HAADF_STEM_Deconvolution',
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    onefile=False,  # False = 打包为文件夹，True = 单个可执行文件
)
