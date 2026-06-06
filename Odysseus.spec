# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Odysseus Desktop.

Build:
    python -m PyInstaller Odysseus.spec --clean --noconfirm

Output:
    dist/Odysseus/          <- portable folder (zip this to share)
        Odysseus.exe
        static/
        ...

To debug hidden issues, change console=False to console=True below and rebuild.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

block_cipher = None

# ── Hidden imports ──
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "sqlalchemy.ext.baked",
    "sqlalchemy.sql.default_comparator",
    "bcrypt",
    "dotenv",
    "pydantic.deprecated.config",
    "pydantic._internal._config",
    "pydantic_settings",
    "qrcode.image.pil",
    "pyotp",
    "croniter",
    # pywebview / Windows
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "clr",
    "pythonnet",
]

datas = [
    ("static", "static"),
    ("config", "config"),
    ("services/hwfit/data", "services/hwfit/data"),
    (".env.example", "."),
    ("requirements.txt", "."),
]
binaries = []

# Collect data files, native libs, and hidden submodules for key packages.
for pkg in [
    "webview",         # native DLLs for pywebview
    "onnxruntime",     # fastembed depends on this
    "httpx",
    "mcp",
    "icalendar",
    "caldav",
    "markdown",
    "nh3",
    "qrcode",
    "pyotp",
    "croniter",
    "pytest",
]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# fastembed distributes .onnx model files inside the package -- collect them.
try:
    import fastembed
    import inspect
    fastembed_dir = os.path.dirname(inspect.getfile(fastembed))
    # Add the whole package directory so model blobs are preserved in the bundle
    if os.path.isdir(fastembed_dir):
        datas += [(fastembed_dir, "fastembed")]
except Exception:
    pass

# All local Python packages (routes, core, src, services, etc.)
for local in [
    "routes", "core", "src", "services", "integrations",
    "mcp_servers", "scripts", "companion",
]:
    hiddenimports += collect_submodules(local)

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "torchvision", "tensorflow"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Odysseus",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,   # <-- CHANGE TO True FOR DEBUG BUILDS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="docs/odysseus.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Odysseus",
)
