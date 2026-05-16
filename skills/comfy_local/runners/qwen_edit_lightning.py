#!/usr/bin/env python3
"""
Qwen-Image-Edit-2509 4-step Lightning runner — FREE LOCAL image editing.

The free alternative to NanoBanana2Direct for image-edit tasks. Uses Luis's
local Qwen-Image-Edit-2509 fp8 DiT + Lightning 4-step LoRA. Cost: $0 per call
(fully local on the RTX 5090).

Canonical pipeline cloned from Comfy-Org's "image_qwen_image_edit_2509" template:
  UNETLoader            qwen_image_edit_2509_fp8_e4m3fn.safetensors
  LoraLoaderModelOnly   Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors  strength=1
  ModelSamplingAuraFlow shift=3
  CFGNorm               strength=1
  CLIPLoader            qwen_2.5_vl_7b_fp8_scaled.safetensors  type=qwen_image
  VAELoader             qwen_image_vae.safetensors
  FluxKontextImageScale (scales input for Qwen-Image-Edit)
  VAEEncode             (input image -> init latent)
  TextEncodeQwenImageEditPlus  (positive, gets prompt + scaled image)
  TextEncodeQwenImageEditPlus  (negative, empty prompt + scaled image)
  KSampler              steps=4, cfg=1.0, sampler=euler, scheduler=simple
  VAEDecode
  SaveImage

CLI:
  python3 runners/qwen_edit_lightning.py --image G:\\path\\to\\input.png \\
      --prompt "Replace the cat with a dalmatian, keeping environment consistent"

Flags:
  --image <path>      required - input image to edit
  --prompt "<text>"   required - edit instruction
  --seed <int>        optional 32-bit seed (random if omitted)
  --steps {4,8}       Lightning step count (default 4 — uses the v1.0 4-step LoRA)
  --variations N      default 1; N>1 fans out to N parallel KSampler+SaveImage pairs
                      sharing the same loaded model+clip+vae (cost: still $0)
  --no-display        skip POST /open_workflow

Note: requires `qwen_2.5_vl_7b_fp8_scaled.safetensors` to be in
G:\\models\\text_encoders\\ (NOT clip\\). If Luis's file is in clip/, copy or
symlink it to text_encoders/ or the runner will fail validation with a clean
node_errors response from /prompt.
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"

# Canonical filenames (verified against Comfy-Org template image_qwen_image_edit_2509.json)
DIT_FILE = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
LORA_4STEP = "Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors"
LORA_8STEP = "Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors"  # fallback (no 8-step LoRA in inventory)
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
            print("display: /open_workflow endpoint not found — restart ComfyUI or pass --no-display",
                  file=sys.stderr)
        else:
            body = e.read().decode("utf-8", errors="replace")
            print(f"display: HTTP {e.code} — {body}", file=sys.stderr)
    except Exception as e:
        print(f"display: failed ({e}) — pass --no-display to silence", file=sys.stderr)


def upload_image(path: Path) -> str:
    if not path.exists():
        print(f"input image not found: {path}", file=sys.stderr)
        sys.exit(1)
    boundary = "----QwenEditLightningRunnerBoundary"
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = head + path.read_bytes() + tail
    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        print(f"upload failed: {e}", file=sys.stderr)
        sys.exit(2)
    return result["name"]


# ====== API workflow builder (single output) ======

def build_workflow_single(prompt_text: str, image_filename: str, prefix: str,
                          seed: int, steps: int) -> dict:
    """Single-output API workflow. Node IDs are stable strings."""
    return {
        # Loaders
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": DIT_FILE, "weight_dtype": "default"},
            "_meta": {"title": "Qwen-Image-Edit-2509 DiT (fp8)"},
        },
        "lora_loader": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["model_loader", 0], "lora_name": LORA_4STEP, "strength_model": 1.0},
            "_meta": {"title": "Lightning 4-step LoRA"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["lora_loader", 0], "shift": 3.0},
            "_meta": {"title": "ModelSamplingAuraFlow shift=3"},
        },
        "cfg_norm": {
            "class_type": "CFGNorm",
            "inputs": {"model": ["shift", 0], "strength": 1.0},
            "_meta": {"title": "CFG Norm"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ENCODER_FILE, "type": "qwen_image", "device": "default"},
            "_meta": {"title": "Qwen2.5-VL 7B fp8 (qwen_image)"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_FILE},
            "_meta": {"title": "Qwen-Image VAE"},
        },
        # Image conditioning
        "load_image": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
            "_meta": {"title": "Input image to edit"},
        },
        "scale_image": {
            "class_type": "FluxKontextImageScale",
            "inputs": {"image": ["load_image", 0]},
            "_meta": {"title": "Scale for Qwen-Image-Edit"},
        },
        "encode_init_latent": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["scale_image", 0], "vae": ["vae_loader", 0]},
            "_meta": {"title": "Encode init latent"},
        },
        # Text + image conditioning
        "positive": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["clip_loader", 0],
                "prompt": prompt_text,
                "vae": ["vae_loader", 0],
                "image1": ["scale_image", 0],
            },
            "_meta": {"title": "Positive (prompt + ref image)"},
        },
        "negative": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["clip_loader", 0],
                "prompt": "",
                "vae": ["vae_loader", 0],
                "image1": ["scale_image", 0],
            },
            "_meta": {"title": "Negative (empty + ref image)"},
        },
        # Sample + decode + save
        "ksampler": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["cfg_norm", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["positive", 0],
                "negative": ["negative", 0],
                "latent_image": ["encode_init_latent", 0],
                "denoise": 1.0,
            },
            "_meta": {"title": f"KSampler {steps}-step Lightning"},
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


def build_workflow_variations(prompt_text: str, image_filename: str, base_prefix: str,
                              variations: list[tuple[int, str]], steps: int) -> dict:
    """N-variations: shared loaders / clip / vae / image conditioning,
    fan out to N parallel (KSampler, VAEDecode, SaveImage) triplets.
    `variations` = [(seed, prefix), ...]."""
    wf: dict = {
        # Shared loader chain
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": DIT_FILE, "weight_dtype": "default"},
            "_meta": {"title": "Qwen-Image-Edit-2509 DiT (shared)"},
        },
        "lora_loader": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["model_loader", 0], "lora_name": LORA_4STEP, "strength_model": 1.0},
            "_meta": {"title": "Lightning LoRA (shared)"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["lora_loader", 0], "shift": 3.0},
            "_meta": {"title": "Shift=3 (shared)"},
        },
        "cfg_norm": {
            "class_type": "CFGNorm",
            "inputs": {"model": ["shift", 0], "strength": 1.0},
            "_meta": {"title": "CFGNorm (shared)"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ENCODER_FILE, "type": "qwen_image", "device": "default"},
            "_meta": {"title": "Qwen2.5-VL (shared)"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE_FILE},
            "_meta": {"title": "Qwen-Image VAE (shared)"},
        },
        "load_image": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
            "_meta": {"title": "Input image (shared)"},
        },
        "scale_image": {
            "class_type": "FluxKontextImageScale",
            "inputs": {"image": ["load_image", 0]},
            "_meta": {"title": "Scaled (shared)"},
        },
        "encode_init_latent": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["scale_image", 0], "vae": ["vae_loader", 0]},
            "_meta": {"title": "Init latent (shared)"},
        },
        "positive": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["clip_loader", 0],
                "prompt": prompt_text,
                "vae": ["vae_loader", 0],
                "image1": ["scale_image", 0],
            },
            "_meta": {"title": "Positive (shared)"},
        },
        "negative": {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": {
                "clip": ["clip_loader", 0],
                "prompt": "",
                "vae": ["vae_loader", 0],
                "image1": ["scale_image", 0],
            },
            "_meta": {"title": "Negative (shared)"},
        },
    }
    # Per-variation: KSampler -> VAEDecode -> SaveImage
    for i, (seed, vprefix) in enumerate(variations):
        ks_id = f"ksampler_{i+1}"
        dec_id = f"decode_{i+1}"
        sv_id = f"save_{i+1}"
        wf[ks_id] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["cfg_norm", 0],
                "seed": seed,
                "steps": steps,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["positive", 0],
                "negative": ["negative", 0],
                "latent_image": ["encode_init_latent", 0],
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
        description="Qwen-Image-Edit-2509 4-step Lightning runner (free local).",
    )
    p.add_argument("--image", required=True, help="Input image to edit")
    p.add_argument("--prompt", required=True, help="Edit instruction text")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--steps", type=int, choices=[4, 8], default=4,
                   help="Lightning step count (default 4)")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel KSampler+SaveImage triplets sharing loaders")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]

    # Upload input image
    img_path = Path(args.image).expanduser().resolve()
    image_filename = upload_image(img_path)
    print(f"uploaded input: {img_path.name} -> {image_filename}")

    # Slug from a few words of the prompt for output prefix
    import re as _re
    prompt_slug = _re.sub(r"[^a-z0-9]+", "_", args.prompt.lower()).strip("_")[:40] or "edit"
    base_prefix = f"qwen_edits/{img_path.stem}__{prompt_slug}"

    if args.variations == 1:
        api_wf = build_workflow_single(args.prompt, image_filename, base_prefix, seeds[0], args.steps)
        base_filename = f"qwen_edit_lightning_{img_path.stem}__{prompt_slug}"
    else:
        variations_list = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        api_wf = build_workflow_variations(args.prompt, image_filename, base_prefix,
                                          variations_list, args.steps)
        base_filename = f"qwen_edit_lightning_{img_path.stem}__{prompt_slug}_x{args.variations}"

    # Save API workflow (graph format would require a manual layout, skipping for now)
    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{base_filename}_workflow-api.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")

    # Submit
    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        print("\nCommon fixes:", file=sys.stderr)
        print("  - 'qwen_2.5_vl_7b_fp8_scaled.safetensors' must be in G:\\models\\text_encoders\\", file=sys.stderr)
        print("    (Luis has it in G:\\models\\clip\\ — copy or symlink to text_encoders\\)", file=sys.stderr)
        print("  - all canonical filenames must match exactly (see DIT_FILE/LORA_4STEP/ENCODER_FILE/VAE_FILE constants)", file=sys.stderr)
        sys.exit(3)

    if args.variations == 1:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"seed={seeds[0]} steps={args.steps}")
        print(f"output prefix: {base_prefix} (lands under ComfyUI/output/qwen_edits/)")
    else:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"variations={args.variations} steps={args.steps}")
        print(f"seeds: {seeds}")
        print(f"cost: $0 (local generation)")
        print(f"output prefixes: {base_prefix}_v01 .. _v{args.variations:02d}")

    print("note: no /open_workflow display push for this runner — only API format emitted")


if __name__ == "__main__":
    main()
