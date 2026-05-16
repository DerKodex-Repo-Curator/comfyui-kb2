#!/usr/bin/env python3
"""
Multi-model T2I runner: one prompt -> 4 parallel jobs across 4 model families.

Usage: python3 runners/multi_model_t2i.py "your prompt" [filename_prefix] [W H]

Models (all verified against /object_info on the live server before submission):
  - Flux 2 dev fp8mixed    -> suffix _flux2  (Mistral encoder, flux2-vae,  20s euler/simple cfg=1 FluxGuidance=4)
  - Flux.1 dev fp8         -> suffix _flux1  (CLIP-L+T5XXL,    ae.safetensors, 20s euler/simple cfg=1 FluxGuidance=3.5)
  - Juggernaut XL v9 Lt    -> suffix _sdxl   (bundled CLIP+VAE in checkpoint, 6s euler sgm_uniform cfg=1.5  -- LIGHTNING variant)
  - Z-Image turbo fp8      -> suffix _zimage (Qwen3-4B lumina2, ae.safetensors,  8s res_multistep/simple cfg=1, ModelSamplingAuraFlow shift=3)

ComfyUI processes one prompt at a time per server -- the four jobs queue and
run sequentially in submission order. "Parallel" here means we submit all four
back-to-back without waiting for any to finish.

Output: ComfyUI/output/MultiModel/<prefix>_<suffix>_00001_.png
"""

from __future__ import annotations
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

FLUX2_DIT     = "flux2_dev_fp8mixed.safetensors"
FLUX2_CLIP    = "mistral_3_small_flux2_fp8.safetensors"
FLUX2_VAE     = "flux2-vae.safetensors"

FLUX1_DIT     = "flux1-dev-fp8.safetensors"
FLUX1_CLIP_L  = "clip_l.safetensors"
FLUX1_T5XXL   = "t5xxl_fp8_e4m3fn_scaled.safetensors"
FLUX1_VAE     = "ae.safetensors"

SDXL_CKPT     = "juggernautXL_v9Rdphoto2Lightning.safetensors"

ZIMAGE_DIT    = "z-image-turbo-fp8-e4m3fn.safetensors"
ZIMAGE_CLIP   = "qwen_3_4b.safetensors"
ZIMAGE_VAE    = "ae.safetensors"


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{COMFY_URL}{path}", timeout=15) as resp:
        return json.loads(resp.read())


def preflight() -> None:
    """Verify each loader's accepted-filenames list contains the file we plan to use.
    Fails loud BEFORE any /prompt submission so we never submit a workflow that will
    be rejected at the loader."""
    print("== preflight: verifying every model + encoder + VAE on the live server ==")
    checks = [
        ("UNETLoader",            "unet_name",  FLUX2_DIT),
        ("UNETLoader",            "unet_name",  FLUX1_DIT),
        ("UNETLoader",            "unet_name",  ZIMAGE_DIT),
        ("CheckpointLoaderSimple","ckpt_name",  SDXL_CKPT),
        ("CLIPLoader",            "clip_name",  FLUX2_CLIP),
        ("CLIPLoader",            "clip_name",  ZIMAGE_CLIP),
        ("DualCLIPLoader",        "clip_name1", FLUX1_CLIP_L),
        ("DualCLIPLoader",        "clip_name2", FLUX1_T5XXL),
        ("VAELoader",             "vae_name",   FLUX2_VAE),
        ("VAELoader",             "vae_name",   FLUX1_VAE),
    ]
    failures = []
    seen_loaders: dict[str, dict] = {}
    for loader, field, name in checks:
        try:
            if loader not in seen_loaders:
                seen_loaders[loader] = _get(f"/object_info/{loader}")
            spec = seen_loaders[loader][loader]["input"]["required"][field]
            allowed = spec[0] if isinstance(spec, list) else spec
            if name not in allowed:
                failures.append(f"  - {loader}.{field}: {name!r} NOT in accepted list")
            else:
                print(f"  ok   {loader:24s} {field:12s} {name}")
        except Exception as e:
            failures.append(f"  - {loader}.{field} lookup failed: {e}")
    if failures:
        print("\nPREFLIGHT FAILED. Fix these before submitting:", file=sys.stderr)
        for f in failures:
            print(f, file=sys.stderr)
        sys.exit(2)
    print("== preflight ok ==\n")


def _save_image(prefix: str, suffix: str, image_node_id: str) -> dict:
    return {"class_type": "SaveImage", "inputs": {
        "filename_prefix": f"MultiModel/{prefix}_{suffix}",
        "images": [image_node_id, 0],
    }}


def build_flux2(prompt: str, prefix: str, seed: int, width: int, height: int) -> dict:
    return {
        "1":  {"class_type": "UNETLoader",          "inputs": {"unet_name": FLUX2_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader",          "inputs": {"clip_name": FLUX2_CLIP, "type": "flux2", "device": "default"}},
        "3":  {"class_type": "VAELoader",           "inputs": {"vae_name": FLUX2_VAE}},
        "4":  {"class_type": "CLIPTextEncode",      "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5":  {"class_type": "FluxGuidance",        "inputs": {"guidance": 4.0, "conditioning": ["4", 0]}},
        "6":  {"class_type": "EmptyFlux2LatentImage","inputs": {"width": width, "height": height, "batch_size": 1}},
        "7":  {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "8":  {"class_type": "KSampler",            "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": 20, "cfg": 1.0,
                    "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                    "model": ["1", 0], "positive": ["5", 0], "negative": ["7", 0],
                    "latent_image": ["6", 0]}},
        "9":  {"class_type": "VAEDecode",           "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": _save_image(prefix, "flux2", "9"),
    }


def build_flux1(prompt: str, prefix: str, seed: int, width: int, height: int) -> dict:
    return {
        "1":  {"class_type": "UNETLoader",          "inputs": {"unet_name": FLUX1_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "DualCLIPLoader",      "inputs": {"clip_name1": FLUX1_CLIP_L, "clip_name2": FLUX1_T5XXL, "type": "flux", "device": "default"}},
        "3":  {"class_type": "VAELoader",           "inputs": {"vae_name": FLUX1_VAE}},
        "4":  {"class_type": "CLIPTextEncode",      "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5":  {"class_type": "FluxGuidance",        "inputs": {"guidance": 3.5, "conditioning": ["4", 0]}},
        "6":  {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7":  {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "8":  {"class_type": "KSampler",            "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": 20, "cfg": 1.0,
                    "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                    "model": ["1", 0], "positive": ["5", 0], "negative": ["7", 0],
                    "latent_image": ["6", 0]}},
        "9":  {"class_type": "VAEDecode",           "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": _save_image(prefix, "flux1", "9"),
    }


def build_sdxl(prompt: str, prefix: str, seed: int, width: int, height: int) -> dict:
    # Juggernaut XL v9 Rdphoto2 Lightning -- distilled, 6 steps, low cfg, real negative.
    neg = "low quality, blurry, deformed, watermark, text, signature"
    return {
        "1":  {"class_type": "CheckpointLoaderSimple","inputs": {"ckpt_name": SDXL_CKPT}},
        "2":  {"class_type": "CLIPTextEncode",      "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3":  {"class_type": "CLIPTextEncode",      "inputs": {"text": neg,    "clip": ["1", 1]}},
        "4":  {"class_type": "EmptyLatentImage",    "inputs": {"width": width, "height": height, "batch_size": 1}},
        "5":  {"class_type": "KSampler",            "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": 6, "cfg": 1.5,
                    "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1.0,
                    "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
                    "latent_image": ["4", 0]}},
        "6":  {"class_type": "VAEDecode",           "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7":  _save_image(prefix, "sdxl", "6"),
    }


def build_zimage(prompt: str, prefix: str, seed: int, width: int, height: int) -> dict:
    return {
        "1":  {"class_type": "UNETLoader",              "inputs": {"unet_name": ZIMAGE_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "ModelSamplingAuraFlow",   "inputs": {"shift": 3.0, "model": ["1", 0]}},
        "3":  {"class_type": "CLIPLoader",              "inputs": {"clip_name": ZIMAGE_CLIP, "type": "lumina2", "device": "default"}},
        "4":  {"class_type": "VAELoader",               "inputs": {"vae_name": ZIMAGE_VAE}},
        "5":  {"class_type": "CLIPTextEncode",          "inputs": {"text": prompt, "clip": ["3", 0]}},
        "6":  {"class_type": "EmptySD3LatentImage",     "inputs": {"width": width, "height": height, "batch_size": 1}},
        "7":  {"class_type": "ConditioningZeroOut",     "inputs": {"conditioning": ["5", 0]}},
        "8":  {"class_type": "KSampler",                "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": 8, "cfg": 1.0,
                    "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1.0,
                    "model": ["2", 0], "positive": ["5", 0], "negative": ["7", 0],
                    "latent_image": ["6", 0]}},
        "9":  {"class_type": "VAEDecode",               "inputs": {"samples": ["8", 0], "vae": ["4", 0]}},
        "10": _save_image(prefix, "zimage", "9"),
    }


def submit(workflow: dict, label: str) -> str | None:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[{label}] HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[{label}] connection failed: {e}", file=sys.stderr)
        return None
    if result.get("node_errors"):
        print(f"[{label}] REJECTED node_errors:\n{json.dumps(result['node_errors'], indent=2)}", file=sys.stderr)
        return None
    return result["prompt_id"]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python3 {Path(__file__).name} \"your prompt\" [prefix] [W H]", file=sys.stderr)
        sys.exit(1)
    prompt = sys.argv[1]
    today = time.strftime("%Y%m%d")
    prefix = sys.argv[2] if len(sys.argv) > 2 else f"{today}_multi"
    width  = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1024

    preflight()

    seed = random.randint(0, 2**32 - 1)
    builders = [
        ("flux2",  build_flux2),
        ("flux1",  build_flux1),
        ("sdxl",   build_sdxl),
        ("zimage", build_zimage),
    ]

    sys.path.insert(0, str(HERE))
    import _api_to_graph
    WORKFLOWS_DIR.mkdir(exist_ok=True)
    submitted = []
    for i, (label, build) in enumerate(builders):
        wf = build(prompt, prefix, seed, width, height)
        api_path = WORKFLOWS_DIR / f"{prefix}_{label}_workflow-api.json"
        api_path.write_text(json.dumps(wf, indent=2), encoding="utf-8")
        # Only push the LAST variant (zimage) to the canvas to avoid 4 fights for the
        # same canvas tab. Sidebar gets all four.
        _api_to_graph.install(wf, f"{prefix}_{label}", display=(i == len(builders) - 1))
        pid = submit(wf, label)
        if pid:
            submitted.append((label, pid))
            print(f"[{label:6s}] submitted prompt_id={pid}  -> MultiModel/{prefix}_{label}_*.png")
        else:
            print(f"[{label:6s}] FAILED -- see error above", file=sys.stderr)

    print(f"\nseed={seed}, size={width}x{height}, submitted {len(submitted)}/4")
    print("outputs land in: ComfyUI/output/MultiModel/")
    if submitted:
        print("\nprompt_ids (poll /history/<id> to confirm completion):")
        for label, pid in submitted:
            print(f"  {label:6s}  {pid}")


if __name__ == "__main__":
    main()
