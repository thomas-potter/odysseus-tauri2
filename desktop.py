#!/usr/bin/env python3
"""Odysseus Desktop — native window wrapper.

Runs the FastAPI backend in a background thread and opens the UI in a
system-native webview window (Edge WebView2 on Windows, WebKit on macOS,
GTK/WebKit2 on Linux).
"""
import os
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

# ── Keep runtime files (.env, data/, logs/) next to the executable ──
if getattr(sys, "frozen", False):
    _exe_dir = os.path.dirname(sys.executable)
    os.chdir(_exe_dir)
    os.environ.setdefault("ODYSSEUS_BASE_DIR", _exe_dir)

LOG_PATH = Path("desktop.log")

# ── Redirect stdout/stderr to a log file so console=False is not a black hole ──
class TeeLogger:
    def __init__(self, filepath, orig):
        self.file = open(filepath, "a", encoding="utf-8")
        self.orig = orig

    def isatty(self):
        return False

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        self.file.write(data)
        self.file.flush()
        self.orig.write(data)
        self.orig.flush()

    def flush(self):
        self.file.flush()
        self.orig.flush()


sys.stdout = TeeLogger(LOG_PATH, sys.stdout)
sys.stderr = TeeLogger(LOG_PATH, sys.stderr)

print("\n" + "=" * 60)
print(f"Odysseus Desktop starting")
print(f"  frozen:    {getattr(sys, 'frozen', False)}")
print(f"  exe:       {sys.executable}")
print(f"  _MEIPASS:  {getattr(sys, '_MEIPASS', 'n/a')}")
print(f"  cwd:       {os.getcwd()}")
print("=" * 60)

# ── First-time setup (silent if already done) ──
def _first_time_setup():
    data_dir = Path("data")
    env_file = Path(".env")
    if data_dir.exists() and env_file.exists():
        print("[desktop] Setup already done.")
        return

    print("[desktop] First run detected — running setup.py ...")
    try:
        import setup
        setup.main()
        print("[desktop] Setup finished successfully.")
    except Exception as exc:
        print(f"[desktop] Setup error (non-fatal): {exc}")
        traceback.print_exc()


_first_time_setup()

# ── Configuration ──
HOST = os.environ.get("ODYSSEUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("ODYSSEUS_PORT", "7860"))
URL = f"http://{HOST}:{PORT}"

# ── Start FastAPI in a background thread ──
def _server_worker():
    try:
        import uvicorn
        from app import app as fastapi_app
        uvicorn.run(
            fastapi_app,
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=False,
        )
    except Exception as exc:
        print(f"[desktop] Server crashed: {exc}")
        traceback.print_exc()


server = threading.Thread(target=_server_worker, daemon=True)
server.start()

# ── Wait for the server to become ready ──
print(f"[desktop] Waiting for server at {URL} ...")
_ready = False
for _ in range(240):  # up to 2 minutes (first run downloads embedding models)
    try:
        with urllib.request.urlopen(URL, timeout=1) as r:
            if r.status == 200:
                _ready = True
                break
    except Exception:
        pass
    time.sleep(0.5)

# ── If the server never started, show an error window ──
if not _ready:
    print("[desktop] Server did NOT become ready.")
    try:
        import webview
        webview.create_window(
            "Odysseus — Error",
            html=(
                f"<h2>Odysseus failed to start</h2>"
                f"<p>Could not reach the server at {URL}</p>"
                f"<p>See <b>desktop.log</b> next to the .exe for full details.</p>"
                f"<hr><pre>{traceback.format_exc()}</pre>"
            ),
            width=700,
            height=450,
        )
        webview.start()
    except Exception:
        traceback.print_exc()
        # Fallback: open the log in notepad
        os.system(f'start notepad "{LOG_PATH}"')
    sys.exit(1)

# ── Open native window ──
try:
    import webview
    print("[desktop] Opening webview window ...")
    webview.create_window(
        "Odysseus",
        URL,
        width=1600,
        height=1000,
        min_size=(1024, 768),
        text_select=True,
    )
    webview.start()
except Exception as exc:
    print(f"[desktop] Webview failed: {exc}")
    traceback.print_exc()
    os.system(f'start notepad "{LOG_PATH}"')
    sys.exit(1)
