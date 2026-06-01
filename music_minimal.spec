# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec для Music Minimal.
Запуск: pyinstaller music_minimal.spec
"""

import sys
from pathlib import Path

block_cipher = None
project_dir = Path(SPECPATH)

a = Analysis(
    ['desktop_main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageTk',
        'pygame',
        'pygame.mixer',
        'vk_audio',
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.backends',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'mutagen',
        'mutagen.mp3',
        'colorthief',
        'requests',
        'tkinter',
        'tkinter.ttk',
        '_tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],
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
    name='MusicMinimal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
