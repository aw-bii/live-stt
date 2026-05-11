# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['src/bertytype_setup/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/bertytype_setup', 'bertytype_setup'),
        *collect_data_files('certifi'),
    ],
    hiddenimports=[
        'requests',
        'certifi',
        'huggingface_hub',
        'filelock',
        'packaging',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'transformers',
        'numpy',
        'scipy',
        'sounddevice',
        'pystray',
        'pyautogui',
        'loguru',
    ],
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
    name='bertytype-setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/bertytype/assets/icon.ico',
)
