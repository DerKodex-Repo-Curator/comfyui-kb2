#!/usr/bin/env python3
"""
ComfyUI WebSocket watcher daemon.

Connects to ws://localhost:8188/ws, listens for `executed` events, and
auto-downloads completed outputs to ../../outputs_watched/ relative to this
file. Dedupes via state/downloaded.txt. Auto-reconnects with backoff.

Designed for Luis's Windows portable install. Runs against
G:\\ComfyUI_Nunchaku_Portable_V3\\ComfyUI-Easy-Install\\.claude\\skills\\comfy_local\\.

Usage:
    python3 watcher.py            # run in foreground
    start_watcher.bat             # run as background daemon (recommended)

Stop: kill the PID in state/watcher.pid (or run stop_watcher.bat).
"""

from __future__ import annotations
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ---- config ----
COMFY_HOST = os.environ.get("COMFY_HOST", "127.0.0.1")
COMFY_PORT = int(os.environ.get("COMFY_PORT", "8188"))
WS_URL = f"ws://{COMFY_HOST}:{COMFY_PORT}/ws"
HTTP_URL = f"http://{COMFY_HOST}:{COMFY_PORT}"

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = (HERE / ".." / ".." / ".." / "outputs_watched").resolve()
STATE_DIR = HERE / "state"
LOG_FILE = STATE_DIR / "watcher.log"
PID_FILE = STATE_DIR / "watcher.pid"
DEDUPE_FILE = STATE_DIR / "downloaded.txt"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_dedupe() -> set[str]:
    if not DEDUPE_FILE.exists():
        return set()
    return {ln.strip() for ln in DEDUPE_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()}


def mark_downloaded(key: str) -> None:
    with open(DEDUPE_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")


def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def clear_pid() -> None:
    try:
        PID_FILE.unlink()
    except Exception:
        pass


def download_one(filename: str, subfolder: str, file_type: str, dedupe: set[str]) -> None:
    key = f"{file_type}|{subfolder}|{filename}"
    if key in dedupe:
        log(f"  (skip dupe) {filename}")
        return
    qs = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder or "",
        "type": file_type or "output",
    })
    url = f"{HTTP_URL}/view?{qs}"
    # Mirror ComfyUI's subfolder structure under OUTPUT_DIR
    out_subdir = OUTPUT_DIR / (subfolder or "")
    out_subdir.mkdir(parents=True, exist_ok=True)
    out_path = out_subdir / filename
    try:
        with urllib.request.urlopen(url, timeout=60) as resp, open(out_path, "wb") as f:
            f.write(resp.read())
        size_mb = out_path.stat().st_size / 1024 / 1024
        log(f"  downloaded -> {out_path}  ({size_mb:.2f} MB)")
        dedupe.add(key)
        mark_downloaded(key)
    except Exception as e:
        log(f"  download FAILED for {filename}: {e}")


def handle_message(raw: str | bytes, dedupe: set[str]) -> None:
    if isinstance(raw, bytes):
        # Binary frames are preview thumbnails — ignore
        return
    try:
        msg = json.loads(raw)
    except Exception:
        return
    mtype = msg.get("type")
    data = msg.get("data") or {}
    if mtype == "executed":
        prompt_id = data.get("prompt_id")
        node = data.get("node")
        out = data.get("output") or {}
        for kind in ("images", "gifs", "videos"):
            for entry in out.get(kind, []) or []:
                fn = entry.get("filename")
                sf = entry.get("subfolder", "")
                ft = entry.get("type", "output")
                if fn:
                    log(f"executed [{prompt_id}] node={node} -> {kind}/{fn}")
                    download_one(fn, sf, ft, dedupe)
    elif mtype == "execution_error":
        log(f"execution_error: {data.get('exception_message')}  prompt_id={data.get('prompt_id')}")
    elif mtype == "execution_success":
        log(f"execution_success: prompt_id={data.get('prompt_id')}")


def run_loop() -> None:
    """Main loop with reconnect/backoff."""
    try:
        from websocket import WebSocketApp  # websocket-client package
    except ImportError:
        log("ERROR: websocket-client not installed.")
        log("Install: ..\\..\\..\\..\\python_embeded\\python.exe -m pip install websocket-client")
        sys.exit(1)

    dedupe = load_dedupe()
    backoff = 1.0
    log(f"watcher starting. host={COMFY_HOST}:{COMFY_PORT} output={OUTPUT_DIR}")
    log(f"dedupe ledger has {len(dedupe)} entries")

    while True:
        try:
            ws = WebSocketApp(
                WS_URL,
                on_open=lambda w: log(f"WS connected: {WS_URL}"),
                on_message=lambda w, m: handle_message(m, dedupe),
                on_error=lambda w, e: log(f"WS error: {e}"),
                on_close=lambda w, code, msg: log(f"WS closed: code={code} msg={msg}"),
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
            backoff = 1.0  # reset backoff on clean exit
        except Exception as e:
            log(f"connection loop exception: {e}")
        sleep_s = min(backoff, 30.0)
        log(f"reconnecting in {sleep_s:.1f}s")
        time.sleep(sleep_s)
        backoff = min(backoff * 2, 30.0)


if __name__ == "__main__":
    write_pid()
    try:
        run_loop()
    except KeyboardInterrupt:
        log("watcher interrupted by user")
    finally:
        clear_pid()
