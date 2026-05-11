# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['src/bertytype/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/bertytype', 'bertytype'),
        *collect_data_files('sounddevice'),
    ],
    hiddenimports=[
        'PIL',
        'pystray',
        'pyautogui',
        'pyperclip',
        'sounddevice',
        'numpy',
        'pydub',
        'requests',
        'loguru',
        'scipy',
        'scipy.signal',
        'pystray._win32',
        'PIL._tkinter_finder',
        'win32api',
        'win32con',
        'win32gui',
        'pythoncom',
        'pywintypes',
        'pyautogui._pyautogui_win',
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
    name='bertytype',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['pywintypes*.dll', 'vcruntime*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/bertytype/assets/icon.ico',
)
