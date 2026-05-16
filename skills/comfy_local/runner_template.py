#!/usr/bin/env python3
"""
Runner template — copy this and adapt for new use cases.

A runner is a one-shot Python script that:
  1. Builds an API-format ComfyUI workflow dict
  2. POSTs it to /prompt
  3. Prints the prompt_id and exits
  4. The watcher daemon (running in the background) downloads the outputs

Usage: python3 runner_template.py "your prompt here"
"""

from __future__ import annotations
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE / "workflows"


def submit(workflow: dict) -> dict:
    """POST a workflow (API format) to /prompt. Returns parsed JSON response."""
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} from /prompt:\n{body}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Connection failed to {COMFY_URL}: {e}", file=sys.stderr)
        print("Is ComfyUI running? (Start ComfyUI.bat)", file=sys.stderr)
        sys.exit(2)


def save_workflow(workflow: dict, name: str) -> Path:
    """Save the API-format workflow to workflows/<name>_workflow-api.json."""
    WORKFLOWS_DIR.mkdir(exist_ok=True)
    path = WORKFLOWS_DIR / f"{name}_workflow-api.json"
    path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    return path


def build_workflow(prompt: str, prefix: str) -> dict:
    """REPLACE THIS in your runner with the actual workflow build."""
    raise NotImplementedError("Override build_workflow in your runner")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python3 {Path(__file__).name} \"your prompt here\"", file=sys.stderr)
        sys.exit(1)
    prompt = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else "20260509_run"

    workflow = build_workflow(prompt, prefix)
    save_workflow(workflow, prefix)

    result = submit(workflow)
    if result.get("node_errors"):
        print(f"REJECTED. node_errors: {json.dumps(result['node_errors'], indent=2)}", file=sys.stderr)
        sys.exit(3)
    print(f"submitted prompt_id={result['prompt_id']} number={result.get('number')}")
    print(f"watcher will drop outputs into ../../../outputs_watched/")


if __name__ == "__main__":
    main()
