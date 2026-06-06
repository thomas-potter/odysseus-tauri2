# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Odysseus Desktop.

Build:
    python -m PyInstaller Odysseus.spec --clean --noconfirm

Output:
    dist/Odysseus/          <- portable folder (zip this to share)
        Odysseus.exe
        static/
        config/
        ...
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# ── Hidden imports & data collection ──
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
    "qrcode.image pil",
    "pyotp",
    "croniter",
]

datas = [
    ("static", "static"),
    ("config", "config"),
    ("services/hwfit/data", "services/hwfit/data"),
    (".env.example", "."),
    ("requirements.txt", "."),
]
binaries = []

# Collect heavy packages that have data files, native libs, or hidden submodules.
for pkg in [
    "chromadb",
    "fastembed",
    "onnxruntime",
    "httpx",
    "mcp",
    "icalendar",
    "caldav",
    "markdown",
    "nh3",
    "qrcode",
    "pyotp",
    "croniter",
    "pytest",  # imported by some lazy test helpers
]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Ensure all local packages are fully pulled in (routes, core, src, etc.).
for local in ["routes", "core", "src", "services", "integrations", "mcp_servers", "scripts", "companion"]:
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
    excludes=["torch", "torchvision", "tensorflow"],  # keep bundle smaller if present
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
    upx=False,  # safer with ML/native libs; set True if you want smaller size
    console=False,  # <-- change to True for a debug build with a visible terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="docs/odysseus.ico",  # uncomment if you create a .ico
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
