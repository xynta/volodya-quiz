# -*- mode: python ; coding: utf-8 -*-
"""Сборка консольного квиза в один исполняемый файл (PyInstaller 6.x).

Собирает console_quiz.py со встроенным data/questions.json.
Aiogram и прочую «ботовую» обвязку исключаем — консольной игре они не нужны,
бинарник остаётся компактным.

Сборка (Mac и Windows одинаково):  pyinstaller stukalova_quiz.spec
Результат: dist/stukalova_quiz  (на Windows — dist/stukalova_quiz.exe)
"""

a = Analysis(
    ['console_quiz.py'],
    pathex=[],
    binaries=[],
    datas=[('data/questions.json', 'data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['aiogram', 'aiohttp', 'magic_filter'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='stukalova_quiz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
