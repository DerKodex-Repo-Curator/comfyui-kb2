#!/usr/bin/env python3
"""
Qwen-Image-2512 Lightning text-to-image runner — FREE LOCAL premium-quality T2I.

Companion to qwen_edit_lightning.py (which handles edits) and zimage_t2i.py
(which is faster but lower-quality). Cost: $0 per call.

Qwen-Image-2512 + Lightning 4-step LoRA gives the highest free-local image
quality available in Luis's install for text-to-image. ~10-15 seconds per
generation on the RTX 5090.

Pipeline (per Comfy-Org canonical `image_qwen_image_2512_with_2steps_lora.json`):
  UNETLoader            qwen_image_2512_fp8_e4m3fn.safetensors
  LoraLoaderModelOnly   Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors  strength=1
  ModelSamplingAuraFlow shift=3
  CLIPLoader            qwen_2.5_vl_7b_fp8_scaled.safetensors  type=qwen_image
  VAELoader             qwen_image_vae.safetensors
  CLIPTextEncode        positive
  ConditioningZeroOut   on negative (distilled — cfg=1)
  EmptySD3LatentImage
  KSampler              steps=4, cfg=1.0, sampler=euler, scheduler=simple
  VAEDecode
  SaveImage

Two LoRA flavors selectable:
  --speed standard   Qwen-Image-2512-Lightning-4steps-V1.0-bf16 (4 steps, default)
  --speed fast       Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16 (2 steps)

Recommended canonical aspect ratios per the canonical template MarkdownNote:
  1:1   1328x1328
  16:9  1664x928
  9:16  928x1664
  4:3   1472x1104
  3:4   1104x1472
  3:2   1584x1056
  2:3   1056x1584

CLI:
  python3 runners/qwen_t2i_lightning.py --prompt "<positive>" \\
      [--width 1328] [--height 1328] [--seed N] [--speed {standard,fast}] \\
      [--variations N] [--no-display]

Note: requires `qwen_2.5_vl_7b_fp8_scaled.safetensors` in `text_encoders/`
(same encoder-location gotcha as qwen_edit_lightning.py).
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

# Canonical filenames
DIT_FILE = "qwen_image_2512_fp8_e4m3fn.safetensors"
LORA_4STEP = "Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors"
LORA_2STEP_WULI = "Wuli-Qwen-Image-2512-Turbo-LoRA-4steps-V1.0-bf16.safetensors"
ENCODER_FILE = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
VAE_FILE = "qwen_image_vae.safetensors"


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


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (s[:40] or "qwen_t2i")


# ====== API workflow builder ======

def _shared_loaders(prompt: str, lora_file: str) -> dict:
    return {
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": DIT_FILE, "weight_dtype": "default"},
            "_meta": {"title": "Qwen-Image-2512 DiT (fp8)"},
        },
        "lora_loader": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["model_loader", 0], "lora_name": lora_file, "strength_model": 1.0},
            "_meta": {"title": f"Lightning LoRA"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["lora_loader", 0], "shift": 3.0},
            "_meta": {"title": "Shift=3"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ENCODER_FILE, "type": "qwen_image", "device": "default"},
            "_meta": {"title": "Qwen2.5-VL 7B fp8"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_FILE},
            "_meta": {"title": "Qwen-Image VAE"},
        },
        "positive": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["clip_loader", 0]},
            "_meta": {"title": "Positive"},
        },
        "negative_raw": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["clip_loader", 0]},
            "_meta": {"title": "Negative raw"},
        },
        "negative": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["negative_raw", 0]},
            "_meta": {"title": "ZeroOut (cfg=1)"},
        },
    }


def build_workflow_single(prompt: str, prefix: str, seed: int,
                          width: int, height: int, steps: int, lora_file: str) -> dict:
    wf = _shared_loaders(prompt, lora_file)
    wf.update({
        "latent": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "_meta": {"title": f"Latent {width}x{height}"},
        },
        "ksampler": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["shift", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["positive", 0],
                "negative": ["negative", 0],
                "latent_image": ["latent", 0],
                "denoise": 1.0,
            },
            "_meta": {"title": f"KSampler {steps}-step Lightning"},
        },
        "decode": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["ksampler", 0], "vae": ["vae_loader", 0]},
            "_meta": {"title": "Decode"},
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["decode", 0]},
            "_meta": {"title": "Save"},
        },
    })
    return wf


def build_workflow_variations(prompt: str, base_prefix: str,
                              variations: list[tuple[int, str]],
                              width: int, height: int, steps: int, lora_file: str) -> dict:
    wf = _shared_loaders(prompt, lora_file)
    wf["latent"] = {
        "class_type": "EmptySD3LatentImage",
        "inputs": {"width": width, "height": height, "batch_size": 1},
        "_meta": {"title": f"Latent {width}x{height} (shared)"},
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
                "sampler_name": "euler",
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
    p = argparse.ArgumentParser(
        description="Qwen-Image-2512 Lightning text-to-image runner (free local).",
    )
    p.add_argument("--prompt", required=True, help="Positive prompt")
    p.add_argument("--width", type=int, default=1328, help="Output width (canonical 1:1 = 1328)")
    p.add_argument("--height", type=int, default=1328, help="Output height")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--speed", choices=["standard", "fast"], default="standard",
                   help="standard = 4-step Lightning (default), fast = 2-step Wuli Turbo")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel KSampler+SaveImage triplets")
    p.add_argument("--no-display", action="store_true")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    if args.speed == "standard":
        lora_file = LORA_4STEP
        steps = 4
    else:
        lora_file = LORA_2STEP_WULI
        steps = 2

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]
    prompt_slug = slugify(args.prompt)
    base_prefix = f"qwen_t2i/{prompt_slug}"

    if args.variations == 1:
        api_wf = build_workflow_single(args.prompt, base_prefix, seeds[0],
                                       args.width, args.height, steps, lora_file)
        base_filename = f"qwen_t2i_lightning_{prompt_slug}"
    else:
        variations_list = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        api_wf = build_workflow_variations(args.prompt, base_prefix, variations_list,
                                           args.width, args.height, steps, lora_file)
        base_filename = f"qwen_t2i_lightning_{prompt_slug}_x{args.variations}"

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{base_filename}_workflow-api.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")

    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        print("\nSetup hints:", file=sys.stderr)
        print("  - qwen_2.5_vl_7b_fp8_scaled.safetensors must be in G:\\models\\text_encoders\\", file=sys.stderr)
        print("    (Luis has it in G:\\models\\clip\\ — copy or symlink to text_encoders\\)", file=sys.stderr)
        sys.exit(3)

    if args.variations == 1:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"speed={args.speed} steps={steps} seed={seeds[0]} size={args.width}x{args.height}")
        print(f"output prefix: {base_prefix}")
    else:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"speed={args.speed} steps={steps} variations={args.variations}")
        print(f"seeds: {seeds}")
        print(f"cost: $0 (local generation)")

    print("note: no /open_workflow display push — only API format emitted")


if __name__ == "__main__":
    main()
