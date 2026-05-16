#!/usr/bin/env python3
"""
Z-Image-Turbo ControlNet runner — FREE LOCAL controlled generation.

Uses the Z-Image-Turbo-Fun-Controlnet-Union model patch (in
G:\\models\\model_patches\\) to control Z-Image-Turbo output via canny edges,
depth maps, or pose skeletons. Cost: $0 per call.

Pipeline cloned from Comfy-Org's "Canny/Depth/Pose to Image (Z-Image-Turbo)"
blueprints. Despite the QwenImageDiffsynthControlnet node name, it routes
internally to ZImageControlPatch when the model_patch is a Z-Image control —
this is the canonical wiring.

Three modes:
  --mode canny    Built-in Canny preprocessor (low/high thresholds)
  --mode depth    DepthAnythingV2Preprocessor (from comfyui_controlnet_aux)
  --mode pose     DWPreprocessor (DWPose, from comfyui_controlnet_aux)

CLI:
  python3 runners/zimage_controlnet.py --mode canny --image G:\\path\\input.png \\
      --prompt "a futuristic city at sunset" \\
      [--low-threshold 0.3] [--high-threshold 0.4] \\
      [--width 1024] [--height 1024] [--seed N] [--steps 9] \\
      [--strength 1.0] [--variations N] [--no-display]

Pipeline (12-13 nodes per single output):
  UNETLoader -> ModelSamplingAuraFlow(shift=3) -> [model]
  ModelPatchLoader(Z-Image-Turbo-Fun-Controlnet-Union) -> [patch]
  CLIPLoader -> CLIPTextEncode(prompt) -> [positive]
                                        -> CLIPTextEncode("") -> ConditioningZeroOut -> [negative]
  VAELoader -> [vae]
  LoadImage -> ImageScaleToTotalPixels -> Preprocessor -> [control]
  QwenImageDiffsynthControlnet(model, patch, vae, image=control, strength) -> [patched_model]
  EmptySD3LatentImage -> KSampler(patched_model, 9 steps, cfg=1, res_multistep, simple)
  -> VAEDecode -> SaveImage

Uses the same canonical KSampler config as the blueprints:
  steps=9, cfg=1.0, sampler=res_multistep, scheduler=simple, denoise=1.0
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

# Canonical filenames (verified against blueprints + G:\models inventory)
ZIMAGE_DIT = "z_image_turbo_bf16.safetensors"  # blueprint uses bf16; fp8 also works
ZIMAGE_CLIP = "qwen_3_4b.safetensors"
ZIMAGE_VAE = "ae.safetensors"
CONTROL_PATCH = "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"

# Per-mode preprocessor node configurations
PREPROCESSORS = {
    "canny": {
        "node_class": "Canny",
        "extra_inputs": {"low_threshold": 0.3, "high_threshold": 0.4},
        # Inputs threshold the source image; output: edge map
    },
    "depth": {
        "node_class": "DepthAnythingV2Preprocessor",
        "extra_inputs": {"ckpt_name": "depth_anything_v2_vitb.pth", "resolution": 1024},
        # comfyui_controlnet_aux provides this. depth_anything_v2_vitb is a common default.
    },
    "pose": {
        "node_class": "DWPreprocessor",
        "extra_inputs": {
            "detect_hand": "enable",
            "detect_body": "enable",
            "detect_face": "enable",
            "resolution": 1024,
            "bbox_detector": "yolox_l.onnx",
            "pose_estimator": "dw-ll_ucoco_384.onnx",
        },
        # DWPose-Onnx defaults from comfyui_controlnet_aux
    },
}


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


def upload_image(path: Path) -> str:
    if not path.exists():
        print(f"input image not found: {path}", file=sys.stderr)
        sys.exit(1)
    boundary = "----ZImageControlnetRunnerBoundary"
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


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (s[:40] or "zimage_cn")


# ====== API workflow builder ======

def build_preprocessor_node(mode: str, source_image_ref) -> dict:
    """Return the API-format preprocessor node dict, wired to the source image."""
    cfg = PREPROCESSORS[mode]
    inputs = {"image": source_image_ref}
    inputs.update(cfg["extra_inputs"])
    return {"class_type": cfg["node_class"], "inputs": inputs, "_meta": {"title": f"Preprocess: {mode}"}}


def _shared_loaders(prompt: str) -> dict:
    """All shared loader nodes used by both single and variations workflows."""
    return {
        "model_loader": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": ZIMAGE_DIT, "weight_dtype": "default"},
            "_meta": {"title": "Z-Image-Turbo DiT"},
        },
        "shift": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["model_loader", 0], "shift": 3.0},
            "_meta": {"title": "Shift=3"},
        },
        "patch_loader": {
            "class_type": "ModelPatchLoader",
            "inputs": {"name": CONTROL_PATCH},
            "_meta": {"title": "Z-Image-Turbo-Fun-Controlnet-Union patch"},
        },
        "clip_loader": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": ZIMAGE_CLIP, "type": "lumina2", "device": "default"},
            "_meta": {"title": "Qwen3-4B (lumina2)"},
        },
        "vae_loader": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": ZIMAGE_VAE},
            "_meta": {"title": "ae.safetensors"},
        },
        "positive": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["clip_loader", 0]},
            "_meta": {"title": "Positive prompt"},
        },
        "negative_raw": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["clip_loader", 0]},
            "_meta": {"title": "Negative (zeroed downstream)"},
        },
        "negative": {
            "class_type": "ConditioningZeroOut",
            "inputs": {"conditioning": ["negative_raw", 0]},
            "_meta": {"title": "ZeroOut (cfg=1)"},
        },
    }


def _control_chain(mode: str, image_filename: str, strength: float) -> dict:
    """Image input -> 1MP rescale -> preprocessor -> QwenImageDiffsynthControlnet."""
    nodes = {
        "load_image": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
            "_meta": {"title": "Control input image"},
        },
        "scale_image": {
            "class_type": "ImageScaleToTotalPixels",
            "inputs": {
                "image": ["load_image", 0],
                "upscale_method": "lanczos",
                "megapixels": 1.0,
                "resolution_steps": 1,
            },
            "_meta": {"title": "Scale to 1 megapixel"},
        },
        "preprocess": build_preprocessor_node(mode, ["scale_image", 0]),
        "controlnet_apply": {
            "class_type": "QwenImageDiffsynthControlnet",
            "inputs": {
                "model": ["shift", 0],
                "model_patch": ["patch_loader", 0],
                "vae": ["vae_loader", 0],
                "image": ["preprocess", 0],
                "strength": strength,
            },
            "_meta": {"title": f"Apply ControlNet ({mode}, strength={strength})"},
        },
    }
    return nodes


def build_workflow_single(prompt: str, image_filename: str, mode: str, prefix: str,
                          seed: int, width: int, height: int, steps: int,
                          strength: float, low_threshold: float, high_threshold: float) -> dict:
    wf = _shared_loaders(prompt)
    # Override canny thresholds if user passed custom values
    wf.update(_control_chain(mode, image_filename, strength))
    if mode == "canny":
        wf["preprocess"]["inputs"]["low_threshold"] = low_threshold
        wf["preprocess"]["inputs"]["high_threshold"] = high_threshold

    wf["latent"] = {
        "class_type": "EmptySD3LatentImage",
        "inputs": {"width": width, "height": height, "batch_size": 1},
        "_meta": {"title": f"Latent {width}x{height}"},
    }
    wf["ksampler"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["controlnet_apply", 0],
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
    }
    wf["decode"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["ksampler", 0], "vae": ["vae_loader", 0]},
        "_meta": {"title": "Decode"},
    }
    wf["save"] = {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": prefix, "images": ["decode", 0]},
        "_meta": {"title": "Save"},
    }
    return wf


def build_workflow_variations(prompt: str, image_filename: str, mode: str, base_prefix: str,
                              variations: list[tuple[int, str]],
                              width: int, height: int, steps: int,
                              strength: float, low_threshold: float, high_threshold: float) -> dict:
    wf = _shared_loaders(prompt)
    wf.update(_control_chain(mode, image_filename, strength))
    if mode == "canny":
        wf["preprocess"]["inputs"]["low_threshold"] = low_threshold
        wf["preprocess"]["inputs"]["high_threshold"] = high_threshold

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
                "model": ["controlnet_apply", 0],
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
    p = argparse.ArgumentParser(description="Z-Image-Turbo ControlNet runner (free local).")
    p.add_argument("--mode", required=True, choices=["canny", "depth", "pose"],
                   help="Preprocessor: canny=edges, depth=DepthAnythingV2, pose=DWPose")
    p.add_argument("--image", required=True, help="Input control image (e.g. a photo)")
    p.add_argument("--prompt", required=True, help="Positive prompt for what to generate")
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--steps", type=int, default=9, help="KSampler NFE count (blueprint default 9)")
    p.add_argument("--strength", type=float, default=1.0, help="ControlNet strength (default 1.0)")
    p.add_argument("--low-threshold", type=float, default=0.3,
                   help="Canny low threshold (only used if --mode canny)")
    p.add_argument("--high-threshold", type=float, default=0.4,
                   help="Canny high threshold (only used if --mode canny)")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel KSampler+SaveImage triplets")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]

    img_path = Path(args.image).expanduser().resolve()
    image_filename = upload_image(img_path)
    print(f"uploaded control input: {img_path.name} -> {image_filename}")

    prompt_slug = slugify(args.prompt)
    base_prefix = f"zimage_cn/{args.mode}_{img_path.stem}__{prompt_slug}"

    if args.variations == 1:
        api_wf = build_workflow_single(
            args.prompt, image_filename, args.mode, base_prefix, seeds[0],
            args.width, args.height, args.steps, args.strength,
            args.low_threshold, args.high_threshold,
        )
        base_filename = f"zimage_cn_{args.mode}_{img_path.stem}__{prompt_slug}"
    else:
        variations_list = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        api_wf = build_workflow_variations(
            args.prompt, image_filename, args.mode, base_prefix, variations_list,
            args.width, args.height, args.steps, args.strength,
            args.low_threshold, args.high_threshold,
        )
        base_filename = f"zimage_cn_{args.mode}_{img_path.stem}__{prompt_slug}_x{args.variations}"

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{base_filename}_workflow-api.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")

    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        if args.mode == "depth":
            print("\nNote: DepthAnythingV2Preprocessor requires the depth_anything_v2_vitb.pth", file=sys.stderr)
            print("model in G:\\models\\controlnet_aux_models\\depthanything\\ (auto-downloaded on first use).", file=sys.stderr)
        elif args.mode == "pose":
            print("\nNote: DWPreprocessor requires yolox_l.onnx + dw-ll_ucoco_384.onnx", file=sys.stderr)
            print("under G:\\models\\controlnet_aux_models\\ (auto-downloaded on first use).", file=sys.stderr)
        sys.exit(3)

    if args.variations == 1:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"mode={args.mode} strength={args.strength} seed={seeds[0]}")
        print(f"output prefix: {base_prefix}")
    else:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"mode={args.mode} variations={args.variations}")
        print(f"seeds: {seeds}")
        print(f"cost: $0 (local generation)")

    print("note: no /open_workflow display push for this runner")


if __name__ == "__main__":
    main()
