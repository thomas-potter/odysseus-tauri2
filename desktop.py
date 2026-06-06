#!/usr/bin/env python3
"""Odysseus Desktop — native window wrapper.

Runs the FastAPI backend in a background thread and opens the UI in a
system-native webview window (Edge WebView2 on Windows, WebKit on macOS,
GTK/WebKit2 on Linux).

Usage (development):
    python desktop.py

Usage (frozen):
    dist/Odysseus/Odysseus.exe
"""
import os
import sys
import threading
import time
import urllib.request
from io import StringIO
from pathlib import Path

# When frozen by PyInstaller, keep runtime files (.env, data/, logs/)
# next to the executable rather than wherever the shortcut was launched from.
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))


# ── First-time setup (silent if already done) ──
def _first_time_setup():
    data_dir = Path("data")
    env_file = Path(".env")
    if data_dir.exists() and env_file.exists():
        return

    print("[desktop] First run detected — running setup.py …")
    try:
        import setup
    except Exception as exc:
        print(f"[desktop] Could not import setup.py: {exc}")
        return

    # Capture stdout so we can extract a generated temp password.
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    try:
        setup.main()
    except SystemExit:
        pass
    except Exception as exc:
        buffer.write(f"\n[desktop] Setup error: {exc}\n")
    sys.stdout = old_stdout
    output = buffer.getvalue()

    # Persist the log next to the exe so users can read it even in --windowed mode.
    Path("first-run.log").write_text(output, encoding="utf-8")

    # On Windows, pop up a message box if a random password was generated.
    if sys.platform == "win32":
        for line in output.splitlines():
            if "Temporary password:" in line:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"{line}\n\nFull details saved to first-run.log",
                    "Odysseus — First Run",
                    0,
                )
                break


_first_time_setup()

# ── Start FastAPI in a background thread ──
HOST = os.environ.get("ODYSSEUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("ODYSSEUS_PORT", "7860"))


def _server_worker():
    import uvicorn
    # Import here so setup.py has a chance to create .env before heavy imports fire.
    from app import app as fastapi_app
    uvicorn.run(
        fastapi_app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False,
    )


server = threading.Thread(target=_server_worker, daemon=True)
server.start()

# ── Wait for the server to become ready ──
_url = f"http://{HOST}:{PORT}"
print(f"[desktop] Waiting for Odysseus at {_url} …")
_ready = False
for _ in range(240):  # up to 2 minutes (first run downloads embedding models)
    try:
        with urllib.request.urlopen(_url, timeout=1) as r:
            if r.status == 200:
                _ready = True
                break
    except Exception:
        pass
    time.sleep(0.5)

# ── Open native window (or an error window on failure) ──
import webview

if not _ready:
    webview.create_window(
        "Odysseus — Error",
        html=(
            f"<h2>Odysseus failed to start</h2>"
            f"<p>Could not reach {_url}</p>"
            f"<p>Check <code>first-run.log</code> or run from a terminal to see errors.</p>"
        ),
        width=600,
        height=400,
    )
    webview.start()
    sys.exit(1)

webview.create_window(
    "Odysseus",
    _url,
    width=1600,
    height=1000,
    min_size=(1024, 768),
    text_select=True,
)
webview.start()
