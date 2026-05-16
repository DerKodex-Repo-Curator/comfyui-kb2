#!/usr/bin/env python3
"""
Z-Image-Turbo text-to-image runner — FREE LOCAL generation.

Companion to qwen_edit_lightning.py: that runner handles image-to-image edits,
this one handles pure text-to-image. Cost: $0 per call.

Z-Image-Turbo is an 8-NFE distilled model (per docs.comfy.org). It's the fastest
high-quality T2I model in Luis's install.

Pipeline (10 nodes, per references/08 + 33):
  UNETLoader            z-image-turbo-fp8-e4m3fn.safetensors
  ModelSamplingAuraFlow shift=3
  CLIPLoader            qwen_3_4b.safetensors  type=lumina2  (NOT flux2)
  VAELoader             ae.safetensors  (Z-Image and Flux.1 share this VAE)
  CLIPTextEncode        positive prompt
  CLIPTextEncode        empty (for negative path)
  ConditioningZeroOut   on negative (distilled model — cfg=1)
  EmptySD3LatentImage   16-channel latent (Z-Image latent format)
  KSampler              steps=8, cfg=1.0, sampler=res_multistep, scheduler=simple
  VAEDecode
  SaveImage

CLI:
  python3 runners/zimage_t2i.py --prompt "a forest shrine in autumn" \\
      [--width 1024] [--height 1024] [--seed N] [--steps 8] \\
      [--variations N] [--no-display]

Supersedes the older positional-arg version of this runner.
"""

from __future__ import annotations
import argparse
import json
import os
import random
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"

# Canonical filenames (verified against G:\models\ inventory and ref 08)
ZIMAGE_DIT = "z-image-turbo-fp8-e4m3fn.safetensors"
ZIMAGE_CLIP = "qwen_3_4b.safetensors"
ZIMAGE_VAE = "ae.safetensors"


# ====== ComfyUI HTTP helpers ======

def http_post_json(path: str, payload: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} from {path}:\n{body}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Connection failed to {COMFY_URL}{path}: {e}", file=sys.stderr)
        print("Is ComfyUI running? (Start ComfyUI.bat)", file=sys.stderr)
        sys.exit(2)


def request_display(graph_path: Path) -> None:
    payload = json.dumps({"path": str(graph_path)}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/open_workflow",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
        print(f"display: pushed to canvas ({result.get('node_count')} nodes)")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("display: /open_workflow endpoint not found - restart ComfyUI or pass --no-display",
                  file=sys.stderr)
        else:
            body = e.read().decode("utf-8", errors="replace")
            print(f"display: HTTP {e.code} - {body}", file=sys.stderr)
    except Exception as e:
        print(f"display: failed ({e}) - pass --no-display to silence", file=sys.stderr)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (s[:40] or "zimage")


# ====== API workflow builder ======

def build_workflow_single(prompt: str, prefix: str, seed: int,
                          width: int, height: int, steps: int) -> dict:
    return {
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": ZIMAGE_DIT, "weight_dtype": "default"},
            "_meta": {"title": "Z-Image-Turbo DiT (fp8)"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["model_loader", 0], "shift": 3.0},
            "_meta": {"title": "Shift=3 (Z-Image canonical)"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ZIMAGE_CLIP, "type": "lumina2", "device": "default"},
            "_meta": {"title": "Qwen3-4B (lumina2 type)"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": ZIMAGE_VAE},
            "_meta": {"title": "Flux.1 / Z-Image shared VAE"},
        },
        "positive": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["clip_loader", 0]},
            "_meta": {"title": "Positive"},
        },
        "negative_raw": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["clip_loader", 0]},
            "_meta": {"title": "Negative (will be zeroed)"},
        },
        "negative": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["negative_raw", 0]},
            "_meta": {"title": "ZeroOut (distilled — cfg=1)"},
        },
        "latent": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "_meta": {"title": f"Empty SD3 latent {width}x{height}"},
        },
        "ksampler": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["shift", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "positive": ["positive", 0],
                "negative": ["negative", 0],
                "latent_image": ["latent", 0],
                "denoise": 1.0,
            },
            "_meta": {"title": f"KSampler {steps}-NFE"},
        },
        "decode": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["ksampler", 0], "vae": ["vae_loader", 0]},
            "_meta": {"title": "VAE Decode"},
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["decode", 0]},
            "_meta": {"title": "Save"},
        },
    }


def build_workflow_variations(prompt: str, base_prefix: str,
                              variations: list[tuple[int, str]],
                              width: int, height: int, steps: int) -> dict:
    """Shared loaders + clip + vae + conditioning, fan out to N parallel
    (KSampler, VAEDecode, SaveImage) triplets with different seeds (and
    different latent if you want different sizes — here we keep one latent
    shared to keep VRAM lower; Z-Image is small so this is fine)."""
    wf: dict = {
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": ZIMAGE_DIT, "weight_dtype": "default"},
            "_meta": {"title": "Z-Image-Turbo DiT (shared)"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["model_loader", 0], "shift": 3.0},
            "_meta": {"title": "Shift=3 (shared)"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ZIMAGE_CLIP, "type": "lumina2", "device": "default"},
            "_meta": {"title": "Qwen3-4B (shared)"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": ZIMAGE_VAE},
            "_meta": {"title": "VAE (shared)"},
        },
        "positive": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["clip_loader", 0]},
            "_meta": {"title": "Positive (shared)"},
        },
        "negative_raw": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["clip_loader", 0]},
            "_meta": {"title": "Negative raw (shared)"},
        },
        "negative": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["negative_raw", 0]},
            "_meta": {"title": "ZeroOut (shared)"},
        },
        "latent": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "_meta": {"title": f"Latent {width}x{height} (shared)"},
        },
    }
    for i, (seed, vprefix) in enumerate(variations):
        ks_id = f"ksampler_{i+1}"
        dec_id = f"decode_{i+1}"
        sv_id = f"save_{i+1}"
        wf[ks_id] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["shift", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "positive": ["positive", 0],
                "negative": ["negative", 0],
                "latent_image": ["latent", 0],
                "denoise": 1.0,
            },
            "_meta": {"title": f"KSampler v{i+1:02d} seed={seed}"},
        }
        wf[dec_id] = {
            "class_type": "VAEDecode",
            "inputs": {"samples": [ks_id, 0], "vae": ["vae_loader", 0]},
            "_meta": {"title": f"Decode v{i+1:02d}"},
        }
        wf[sv_id] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": vprefix, "images": [dec_id, 0]},
            "_meta": {"title": f"Save v{i+1:02d}"},
        }
    return wf


# ====== Main ======

def main():
    p = argparse.ArgumentParser(description="Z-Image-Turbo text-to-image runner (free local).")
    p.add_argument("--prompt", required=True, help="Positive prompt text")
    p.add_argument("--width", type=int, default=1024, help="Output width (default 1024)")
    p.add_argument("--height", type=int, default=1024, help="Output height (default 1024)")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--steps", type=int, default=8, help="NFE count (Z-Image-Turbo default = 8)")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel KSampler+SaveImage triplets")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.width % 16 != 0 or args.height % 16 != 0:
        print(f"warning: Z-Image latent uses /16 spatial scaling; W={args.width} H={args.height} should ideally be multiples of 16",
              file=sys.stderr)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]
    prompt_slug = slugify(args.prompt)
    base_prefix = f"zimage/{prompt_slug}"

    if args.variations == 1:
        api_wf = build_workflow_single(args.prompt, base_prefix, seeds[0],
                                       args.width, args.height, args.steps)
        base_filename = f"zimage_t2i_{prompt_slug}"
    else:
        variations_list = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        api_wf = build_workflow_variations(args.prompt, base_prefix, variations_list,
                                           args.width, args.height, args.steps)
        base_filename = f"zimage_t2i_{prompt_slug}_x{args.variations}"

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{base_filename}_workflow-api.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")

    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        sys.exit(3)

    if args.variations == 1:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"seed={seeds[0]} size={args.width}x{args.height} steps={args.steps}")
        print(f"output prefix: {base_prefix} (lands under ComfyUI/output/zimage/)")
    else:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"variations={args.variations} steps={args.steps}")
        print(f"seeds: {seeds}")
        print(f"cost: $0 (local generation)")
        print(f"output prefixes: {base_prefix}_v01 .. _v{args.variations:02d}")

    print("note: no /open_workflow display push — only API format emitted")


if __name__ == "__main__":
    main()
