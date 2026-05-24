# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for yt-vd.

Builds both CLI and GUI executables.
Usage:
    uv run pyinstaller yt-vd.spec
"""

import sys
from pathlib import Path

block_cipher = None
src_dir = Path("src")

# ──────────────────────────────────────────────
# CLI Executable
# ──────────────────────────────────────────────

cli_analysis = Analysis(
    [str(src_dir / "__main__.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "yt_dlp",
        "typer",
        "rich",
        "questionary",
        "platformdirs",
        "core.config",
        "core.utils",
        "core.quality",
        "core.progress",
        "core.fragment_safety",
        "core.downloader",
        "core.parallel",
        "core.playlist",
        "core.audio",
        "core.subtitles",
        "core.metadata",
        "core.search",
        "core.history",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["customtkinter", "tkinter", "PIL"],  # Exclude GUI deps from CLI build
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

cli_pyz = PYZ(cli_analysis.pure, cli_analysis.zipped_data, cipher=block_cipher)

cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    cli_analysis.binaries,
    cli_analysis.zipfiles,
    cli_analysis.datas,
    [],
    name="yt-vd",
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
    icon=None,
)

# ──────────────────────────────────────────────
# GUI Executable
# ──────────────────────────────────────────────

gui_analysis = Analysis(
    [str(src_dir / "gui" / "app.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "yt_dlp",
        "customtkinter",
        "PIL",
        "platformdirs",
        "core.config",
        "core.utils",
        "core.quality",
        "core.progress",
        "core.fragment_safety",
        "core.downloader",
        "core.parallel",
        "core.playlist",
        "core.audio",
        "core.subtitles",
        "core.metadata",
        "core.search",
        "core.history",
        "gui.theme",
        "gui.frames.download",
        "gui.frames.playlist",
        "gui.frames.audio",
        "gui.frames.search",
        "gui.frames.history",
        "gui.frames.settings",
        "gui.widgets.url_input",
        "gui.widgets.progress",
        "gui.widgets.stats",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["typer", "questionary"],  # Exclude CLI deps from GUI build
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

gui_pyz = PYZ(gui_analysis.pure, gui_analysis.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    gui_pyz,
    gui_analysis.scripts,
    gui_analysis.binaries,
    gui_analysis.zipfiles,
    gui_analysis.datas,
    [],
    name="yt-vd-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
