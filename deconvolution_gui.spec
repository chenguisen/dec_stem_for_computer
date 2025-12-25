# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['deconvolution_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 添加需要的资源文件
        ('stem_deconv/', 'stem_deconv/'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'numpy',
        'scipy',
        'scipy.optimize',
        'scipy.interpolate',
        'scipy.ndimage',
        'matplotlib',
        'matplotlib.backends.backend_qt',
        'matplotlib.backends.backend_qtagg',
        'mrcfile',
        'stem_deconv.core',
        'stem_deconv.display',
        'stem_deconv.io',
        'stem_deconv.physics',
        'stem_deconv.postprocess',
        'stem_deconv.regularization',
        'stem_deconv.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HAADF_STEM_Deconvolution',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以创建GUI应用程序
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定路径
)