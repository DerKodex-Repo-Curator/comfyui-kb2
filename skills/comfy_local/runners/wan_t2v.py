#!/usr/bin/env python3
"""
Wan 2.1 14B text-to-video runner (kijai's WanVideoWrapper).

Usage:
    python runners/wan_t2v.py "<prompt>" [flags]

Models (verified via /object_info on 2026-05-09):
  - diffusion_models/wan2.1_t2v_14B_fp8_scaled.safetensors  (DiT, 13.3 GB)
  - text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors    (UMT5-XXL encoder)
  - vae/wan_2.1_vae.safetensors                              (Wan 2.1 VAE)

Pipeline (8 nodes):
  WanVideoModelLoader ────────────────────┐
                                          │
  WanVideoVAELoader ──────┐               │
                          │               ▼
  LoadWanVideoT5          ▼          WanVideoSampler ─→ WanVideoDecode ─→ VHS_VideoCombine
  TextEncoder ─→ WanVideoTextEncode ─→  ▲                  ▲
                                        │                  │
  WanVideoEmptyEmbeds ──────────────────┘                  │
  (width/height/num_frames)                          (uses VAE)

Defaults:
  - 832×480 @ 49 frames (~3s at 16fps) — Wan canonical 480p
  - 30 steps, cfg=6.0, shift=5.0, scheduler=unipc
  - bf16 base precision, fp8_e4m3fn_scaled quantization (matches fp8_scaled file)
  - VAE tiling enabled to keep VRAM in check during decode of long sequences

Output: ComfyUI/output/Wan/<prefix>_NN.mp4 (VHS auto-numbers).

After /prompt is accepted, the saved graph is pushed to your active ComfyUI
canvas via /open_workflow. Pass --no-display to skip.

Cost: $0 (fully local on the RTX 5090). Wall-time depends heavily on length
and steps; rough rule of thumb on a 5090 for 49 frames @ 30 steps: 60-180s.
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"

# Model files (verified live)
WAN_DIT       = "wan2.1_t2v_14B_fp8_scaled.safetensors"
WAN_VAE       = "wan_2.1_vae.safetensors"
# IMPORTANT: kijai's LoadWanVideoT5TextEncoder REJECTS fp8 *scaled* encoders with
# "Invalid T5 text encoder model, fp8 scaled is not supported by this node".
# Use the fp16 variant and let the wrapper's runtime quantization=fp8_e4m3fn handle
# memory savings instead. See ref 33 § Wan T2V quirks.
UMT5_ENCODER  = "umt5_xxl_fp16.safetensors"

# Default negative prompt — Wan canonical (kijai docs / Wan model card recommend
# explicit negatives because the model is sensitive to them, especially for
# motion artifacts and low-quality artifacts).
DEFAULT_NEGATIVE = (
    "Bright tones, overexposed, static, blurred details, subtitles, style, "
    "works, paintings, images, static, overall gray, worst quality, low quality, "
    "JPEG compression residue, ugly, incomplete, extra fingers, poorly drawn hands, "
    "poorly drawn faces, deformed, disfigured, malformed limbs, fused fingers, "
    "still picture, messy background, three legs, many people in the background, "
    "walking backwards"
)


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


def build_workflow(prompt: str, negative: str, prefix: str, seed: int,
                   width: int, height: int, num_frames: int,
                   steps: int, cfg: float, shift: float, fps: float,
                   block_swap: int) -> dict:
    """Build the API-format Wan 2.1 t2v workflow."""
    wf = {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": WAN_DIT,
                "base_precision": "bf16",
                "quantization": "fp8_e4m3fn_scaled",
                "load_device": "main_device",
            },
            "_meta": {"title": "Wan DiT (14B fp8_scaled)"},
        },
        "2": {
            "class_type": "WanVideoVAELoader",
            "inputs": {"model_name": WAN_VAE, "precision": "bf16"},
            "_meta": {"title": "Wan 2.1 VAE"},
        },
        "3": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {
                "model_name": UMT5_ENCODER,
                "precision": "bf16",
                "quantization": "fp8_e4m3fn",  # runtime quantize for VRAM savings
            },
            "_meta": {"title": "UMT5-XXL Text Encoder"},
        },
        "4": {
            "class_type": "WanVideoTextEncode",
            "inputs": {
                "positive_prompt": prompt,
                "negative_prompt": negative,
                "t5": ["3", 0],
            },
            "_meta": {"title": "Encode prompts"},
        },
        "5": {
            "class_type": "WanVideoEmptyEmbeds",
            "inputs": {
                "width": width,
                "height": height,
                "num_frames": num_frames,
            },
            "_meta": {"title": "Empty embeds (initial)"},
        },
        "6": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": ["1", 0],
                "image_embeds": ["5", 0],
                "text_embeds": ["4", 0],
                "steps": steps,
                "cfg": cfg,
                "shift": shift,
                "seed": seed,
                "force_offload": True,
                "scheduler": "unipc",
                "riflex_freq_index": 0,
            },
            "_meta": {"title": "Wan Sampler"},
        },
        "7": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["2", 0],
                "samples": ["6", 0],
                "enable_vae_tiling": True,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 128,
            },
            "_meta": {"title": "Wan Decode"},
        },
        "8": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["7", 0],
                "frame_rate": fps,
                "loop_count": 0,
                "filename_prefix": prefix,
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
            },
            "_meta": {"title": "Save MP4"},
        },
    }

    # Optional BlockSwap — wire it between WanVideoModelLoader and the sampler
    # if VRAM is tight. With block_swap=0 we skip the indirection.
    # NOTE: WanVideoSetBlockSwap takes a block_swap_args input, not a count widget.
    # To actually use it we'd need a WanVideoBlockSwap args-builder node first.
    # Left out of the scaffold for now — the 14B fp8_scaled fits the 5090 for 49 frames
    # without offloading. Add when you push to >100 frame clips.

    return wf


def build_graph(prompt: str, negative: str, prefix: str, seed: int,
                width: int, height: int, num_frames: int,
                steps: int, cfg: float, shift: float, fps: float) -> dict:
    """Hand-rolled graph format. Matches API workflow layout in 4 columns
    (Loaders / Encode / Sample / Decode+Save) for canvas readability."""
    nodes = [
        {  # 1: WanVideoModelLoader
            "id": 1, "type": "WanVideoModelLoader",
            "pos": [-1800, -700], "size": [380, 280], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "model", "type": "WANVIDEOMODEL", "links": [1], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoModelLoader"},
            "widgets_values": [WAN_DIT, "bf16", "fp8_e4m3fn_scaled", "main_device"],
        },
        {  # 2: WanVideoVAELoader
            "id": 2, "type": "WanVideoVAELoader",
            "pos": [-1800, -390], "size": [380, 130], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "vae", "type": "WANVAE", "links": [2], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoVAELoader"},
            "widgets_values": [WAN_VAE, "bf16"],
        },
        {  # 3: LoadWanVideoT5TextEncoder
            "id": 3, "type": "LoadWanVideoT5TextEncoder",
            "pos": [-1800, -220], "size": [380, 160], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "WANTEXTENCODER", "type": "WANTEXTENCODER", "links": [3], "slot_index": 0}],
            "properties": {"Node name for S&R": "LoadWanVideoT5TextEncoder"},
            "widgets_values": [UMT5_ENCODER, "bf16", "main_device", "fp8_e4m3fn"],
        },
        {  # 4: WanVideoTextEncode
            "id": 4, "type": "WanVideoTextEncode",
            "pos": [-1380, -220], "size": [400, 380], "flags": {}, "order": 1, "mode": 0,
            "inputs": [{"name": "t5", "shape": 7, "type": "WANTEXTENCODER", "link": 3}],
            "outputs": [{"name": "WANVIDEOTEXTEMBEDS", "type": "WANVIDEOTEXTEMBEDS", "links": [4], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoTextEncode"},
            "widgets_values": [prompt, negative],
        },
        {  # 5: WanVideoEmptyEmbeds
            "id": 5, "type": "WanVideoEmptyEmbeds",
            "pos": [-1380, 200], "size": [400, 130], "flags": {}, "order": 1, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "WANVIDIMAGE_EMBEDS", "type": "WANVIDIMAGE_EMBEDS", "links": [5], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoEmptyEmbeds"},
            "widgets_values": [width, height, num_frames],
        },
        {  # 6: WanVideoSampler
            "id": 6, "type": "WanVideoSampler",
            "pos": [-940, -700], "size": [400, 480], "flags": {}, "order": 2, "mode": 0,
            "inputs": [
                {"name": "model", "type": "WANVIDEOMODEL", "link": 1},
                {"name": "image_embeds", "type": "WANVIDIMAGE_EMBEDS", "link": 5},
                {"name": "text_embeds", "shape": 7, "type": "WANVIDEOTEXTEMBEDS", "link": 4},
            ],
            "outputs": [{"name": "samples", "type": "LATENT", "links": [6], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoSampler"},
            "widgets_values": [steps, cfg, shift, seed, "randomize", True, "unipc", 0],
        },
        {  # 7: WanVideoDecode
            "id": 7, "type": "WanVideoDecode",
            "pos": [-500, -700], "size": [380, 250], "flags": {}, "order": 3, "mode": 0,
            "inputs": [
                {"name": "vae", "type": "WANVAE", "link": 2},
                {"name": "samples", "type": "LATENT", "link": 6},
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [7], "slot_index": 0}],
            "properties": {"Node name for S&R": "WanVideoDecode"},
            "widgets_values": [True, 272, 272, 144, 128],
        },
        {  # 8: VHS_VideoCombine
            "id": 8, "type": "VHS_VideoCombine",
            "pos": [-100, -700], "size": [380, 350], "flags": {}, "order": 4, "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 7}],
            "outputs": [{"name": "Filenames", "type": "VHS_FILENAMES", "links": None}],
            "properties": {"Node name for S&R": "VHS_VideoCombine"},
            "widgets_values": [fps, 0, prefix, "video/h264-mp4", False, True],
        },
    ]
    links = [
        [1, 1, 0, 6, 0, "WANVIDEOMODEL"],
        [2, 2, 0, 7, 0, "WANVAE"],
        [3, 3, 0, 4, 0, "WANTEXTENCODER"],
        [4, 4, 0, 6, 2, "WANVIDEOTEXTEMBEDS"],
        [5, 5, 0, 6, 1, "WANVIDIMAGE_EMBEDS"],
        [6, 6, 0, 7, 1, "LATENT"],
        [7, 7, 0, 8, 0, "IMAGE"],
    ]
    return {
        "id": "wan-t2v",
        "revision": 0,
        "last_node_id": 8,
        "last_link_id": 7,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"ds": {"scale": 0.7, "offset": [0, 0]}},
        "version": 0.4,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Wan 2.1 14B text-to-video runner.")
    p.add_argument("prompt", help='Positive prompt — describe the scene and motion.')
    p.add_argument("--negative", default=DEFAULT_NEGATIVE,
                   help="Negative prompt (default: Wan canonical anti-artifact list).")
    p.add_argument("--prefix", default=None, help="VHS filename_prefix (default: Wan/<YYYYMMDD>_wan_t2v)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--width", type=int, default=832, help="default: 832 (Wan 480p)")
    p.add_argument("--height", type=int, default=480, help="default: 480 (Wan 480p)")
    p.add_argument("--length", type=int, default=49,
                   help="num_frames; Wan likes (4n+1) values like 17, 33, 49, 65, 81. Default 49 (~3s @ 16fps).")
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--cfg", type=float, default=6.0)
    p.add_argument("--shift", type=float, default=5.0, help="sigma shift; Wan canonical 5.0")
    p.add_argument("--fps", type=float, default=16.0, help="Output MP4 frame rate (Wan native = 16)")
    p.add_argument("--block-swap", type=int, default=0, help="(scaffold ignores; reserved for long-clip VRAM relief)")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission.")
    args = p.parse_args()

    today = time.strftime("%Y%m%d")
    prefix = args.prefix or f"Wan/{today}_wan_t2v"
    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)

    api_wf = build_workflow(args.prompt, args.negative, prefix, seed,
                            args.width, args.height, args.length,
                            args.steps, args.cfg, args.shift, args.fps,
                            args.block_swap)
    graph_wf = build_graph(args.prompt, args.negative, prefix, seed,
                           args.width, args.height, args.length,
                           args.steps, args.cfg, args.shift, args.fps)

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    base = f"{today}_wan_t2v"
    api_path = WORKFLOWS_DIR / f"{base}_workflow-api.json"
    graph_path = WORKFLOWS_DIR / f"{base}_workflow.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    graph_path.write_text(json.dumps(graph_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")
    print(f"wrote {graph_path.name}")

    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        sys.exit(3)
    print(f"submitted prompt_id={result['prompt_id']}  seed={seed}")
    print(f"output: ComfyUI/output/{prefix}_NN.mp4  ({args.length} frames @ {args.fps}fps "
          f"= {args.length/args.fps:.1f}s, {args.width}×{args.height}, {args.steps} steps)")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
