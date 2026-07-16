#!/usr/bin/env python3
"""Native window wrapper for the AI Command Center.

Starts the local server (if not already running) and opens the chat UI in a
GTK/WebKit window so the command center runs as its own program instead of a
browser tab. Falls back to a Firefox window if WebKit is unavailable.
"""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import time

APP_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.environ.get("COMMAND_CENTER_UI_PORT", "8765"))
URL = f"http://{HOST}:{PORT}/"


def port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((HOST, PORT)) == 0


def ensure_server() -> subprocess.Popen | None:
    """Start server.py if nothing is listening; return the child if we own it."""
    if port_open():
        return None
    proc = subprocess.Popen(
        [sys.executable, str(APP_DIR / "server.py"), "--host", HOST, "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        if port_open():
            return proc
        if proc.poll() is not None:
            raise SystemExit("CommandCenterUI: server failed to start (see server.py output)")
        time.sleep(0.25)
    proc.terminate()
    raise SystemExit("CommandCenterUI: server did not come up on time")


def ensure_lab() -> None:
    """Bring the lab up with the app: all-in-one open (TASK-089).

    Best-effort by design — the chat window must open even if the lab can't
    start; the sidebar keeps showing lab state and a manual start button.
    """
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(f"{URL}api/lab/status", timeout=5) as response:
            status = json.load(response)
        if status.get("agents"):
            return
        request = urllib.request.Request(f"{URL}api/lab/start", data=b"{}", method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Origin", URL.rstrip("/"))
        urllib.request.urlopen(request, timeout=10).read()
    except Exception as exc:
        print(f"CommandCenterUI: lab autostart skipped: {exc}", file=sys.stderr)


def run_webkit_window() -> int:
    import gi

    gi.require_version("Gdk", "3.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("WebKit2", "4.1")
    from gi.repository import Gdk, Gtk, WebKit2

    window = Gtk.Window(title="AI Command Center")
    window.set_default_size(1180, 780)
    window.set_icon_name("utilities-terminal")
    view = WebKit2.WebView()
    view.load_uri(URL)
    window.add(view)
    window.connect("destroy", Gtk.main_quit)

    def on_key(_widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if event.keyval == Gdk.KEY_F5 or (ctrl and event.keyval in (Gdk.KEY_r, Gdk.KEY_R)):
            view.reload_bypass_cache()
            return True
        return False

    window.connect("key-press-event", on_key)
    window.show_all()
    Gtk.main()
    return 0


def run_firefox_window() -> int:
    return subprocess.run(["firefox", "--new-window", URL], check=False).returncode


def main() -> int:
    server = ensure_server()
    ensure_lab()
    try:
        try:
            return run_webkit_window()
        except (ImportError, ValueError):
            return run_firefox_window()
    finally:
        if server is not None:
            server.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
