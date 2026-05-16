#!/usr/bin/env python3
"""
Flux 2 dev text-to-image runner.

Usage: python3 runners/flux2_t2i.py "your prompt" [--prefix NAME] [--no-display]

Models used (verified in G:\\models\\):
  - diffusion_models/flux2_dev_fp8mixed.safetensors
  - text_encoders/mistral_3_small_flux2_fp8.safetensors  (Mistral encoder, type=flux2)
  - vae/flux2-vae.safetensors

Sampling: KSampler euler/simple, 20 steps, cfg=1, FluxGuidance=4.0.
Output: 1024x1024 PNG, prefix Flux2/<your_prefix>.

After submission, the saved graph workflow is pushed to your active ComfyUI
canvas via /open_workflow (requires the comfy_load_workflow_endpoint custom
node to be installed and ComfyUI restarted). Pass --no-display to skip.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import random
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"

# Reuse the existing API-format -> graph-format converter (handles all the Flux 2
# node types and the section-based layout/grouping).
sys.path.insert(0, str(HERE))
from _api_to_graph import convert as api_to_graph  # noqa: E402


def build_workflow(prompt: str, prefix: str, seed: int, width: int = 1024, height: int = 1024,
                   steps: int = 20, guidance: float = 4.0) -> dict:
    """Build the API-format Flux 2 dev T2I workflow."""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "flux2_dev_fp8mixed.safetensors",
            "weight_dtype": "default"
        }},
        "2": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "mistral_3_small_flux2_fp8.safetensors",
            "type": "flux2",
            "device": "default"
        }},
        "3": {"class_type": "VAELoader", "inputs": {
            "vae_name": "flux2-vae.safetensors"
        }},
        "4": {"class_type": "CLIPTextEncode", "inputs": {
            "text": prompt,
            "clip": ["2", 0]
        }},
        "5": {"class_type": "FluxGuidance", "inputs": {
            "guidance": guidance,
            "conditioning": ["4", 0]
        }},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {
            "width": width,
            "height": height,
            "batch_size": 1
        }},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "text": "",
            "clip": ["2", 0]
        }},
        "8": {"class_type": "ConditioningZeroOut", "inputs": {
            "conditioning": ["7", 0]
        }},
        "9": {"class_type": "KSampler", "inputs": {
            "seed": seed,
            "control_after_generate": "fixed",
            "steps": steps,
            "cfg": 1.0,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["1", 0],
            "positive": ["5", 0],
            "negative": ["8", 0],
            "latent_image": ["6", 0]
        }},
        "10": {"class_type": "VAEDecode", "inputs": {
            "samples": ["9", 0],
            "vae": ["3", 0]
        }},
        "11": {"class_type": "SaveImage", "inputs": {
            "filename_prefix": f"Flux2/{prefix}",
            "images": ["10", 0]
        }},
    }


def submit(workflow: dict) -> dict:
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
        print(f"Connection failed to {COMFY_URL}: {e}\nIs ComfyUI running?", file=sys.stderr)
        sys.exit(2)


def request_display(graph_path: Path) -> None:
    """Best-effort POST to /open_workflow. Tolerates missing endpoint gracefully."""
    payload = json.dumps({"path": str(graph_path)}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/open_workflow",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            r = json.loads(resp.read())
        print(f"display: pushed to canvas ({r.get('node_count')} nodes)")
    except urllib.error.HTTPError as e:
        if e.code in (404, 405):
            print("display: /open_workflow endpoint not found — restart ComfyUI to pick "
                  "up comfy_load_workflow_endpoint, or pass --no-display", file=sys.stderr)
        else:
            print(f"display: HTTP {e.code} — {e.read().decode('utf-8', errors='replace')}",
                  file=sys.stderr)
    except Exception as e:
        print(f"display: failed ({e}) — pass --no-display to silence", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Flux 2 dev text-to-image runner.")
    p.add_argument("prompt", help='The text prompt, e.g. "a cozy medieval village at golden hour"')
    p.add_argument("--prefix", default=None,
                   help="filename prefix (default: <YYYYMMDD>_flux2_t2i)")
    p.add_argument("--seed", type=int, default=None,
                   help="32-bit seed; random if omitted")
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--guidance", type=float, default=4.0)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--no-display", action="store_true",
                   help="Skip the canvas auto-display via /open_workflow.")
    args = p.parse_args()

    today = time.strftime("%Y%m%d")
    prefix = args.prefix or f"{today}_flux2_t2i"
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)

    workflow = build_workflow(args.prompt, prefix, seed,
                              width=args.width, height=args.height,
                              steps=args.steps, guidance=args.guidance)

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{prefix}_workflow-api.json"
    graph_path = WORKFLOWS_DIR / f"{prefix}_workflow.json"
    api_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    graph_path.write_text(json.dumps(api_to_graph(workflow), indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")
    print(f"wrote {graph_path.name}")

    result = submit(workflow)
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}", file=sys.stderr)
        sys.exit(3)
    print(f"submitted prompt_id={result['prompt_id']}  seed={seed}")
    print(f"output: ComfyUI/output/Flux2/{prefix}_00001_.png")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
