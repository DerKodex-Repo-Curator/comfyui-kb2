#!/usr/bin/env python3
"""
Enemy/monster character generator using Flux 2 Klein 9B image-edit pipeline.

Local-only via flux-2-klein-9b-fp8 (no API cost). Takes a single style anchor
reference image (an existing enemy character) and a biome description in text.
The reference image drives the rendering style (cel-shading, line weight,
outline thickness, palette saturation). The biome is described via --biome-name
which injects per-biome material/palette adaptation rules per
references/22_enemy_monster_framework.md.

Output: a single full-body enemy on white background, faces LEFT, follows the
enemy framework rules (NOT anthropomorphic, magical horror, mystical anchor +
danger accent).

Pipeline mirrors the Comfy-Org canonical image_flux2_klein_image_edit_9b_distilled
template: SamplerCustomAdvanced + RandomNoise + CFGGuider + KSamplerSelect +
Flux2Scheduler at 4 steps cfg=1, with positive/negative conditioning chains
both passing through ReferenceLatent on the encoded reference image.

Usage:
  python runners/enemy_biome_themed.py
      --style-anchor <path-or-input-name>     existing character style reference
      [--subject "shrine bell beast"]         optional concept hint
      [--biome-name forest|swamp|volcanic|desert|crystal]  injects adaptation rules
      [--prefix NAME]
      [--seed N]
      [--steps 4]
      [--cfg 1.0]
      [--width 1024] [--height 1024]
      [--megapixels 1.0]                       reference image scaled to N MP
      [--no-display]
"""

from __future__ import annotations
import argparse
import json
import mimetypes
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"
INPUT_DIR = (HERE / ".." / ".." / ".." / ".." / "ComfyUI" / "input").resolve()

KLEIN_DIT  = "flux-2-klein-9b-fp8.safetensors"
KLEIN_CLIP = "qwen_3_8b_fp8mixed.safetensors"   # Klein 9B's encoder (NOT Mistral)
FLUX2_VAE  = "flux2-vae.safetensors"

# Palette-only biome hints (materials moved to optional --biome-materials path)
BIOME_PALETTE = {
    "forest":   "deep greens, warm browns, soft moss tones",
    "swamp":    "murky teal, bile yellow, gray-green",
    "volcanic": "charcoal, ember orange, deep red",
    "desert":   "ochre, bleached bone, warm sand",
    "crystal":  "jewel tones, prismatic accents",
}


def build_prompt(subject: str, biome_name: str | None) -> str:
    """Mythological-folklore-creature prompt: lean toward animalistic-but-mythological
    designs (salamanders, drakes, kirin, chimera, basilisks) with richer surface
    detail than the previous object-creature minimalism. Folklore creatures are
    explicitly allowed by ref 22; the bans are humanoid warriors / beastfolk /
    plain real-world animals."""
    palette = ""
    if biome_name:
        p = BIOME_PALETTE.get(biome_name.lower())
        if p:
            palette = f" Palette: {p}."
    subject_clause = subject.strip() if subject else "a hostile mythological creature"
    return (
        "A hostile mythological creature for a 2D medieval fantasy game.\n\n"
        f"Subject: {subject_clause}.{palette}\n\n"
        "Match the reference image's rendering style -- cel-shading approach, outline "
        "thickness, saturated flat colors. Push surface detail RICHER than minimal "
        "through COLOR and VALUE separation, not line density: visible scale or hide "
        "texture (tonal shifts, NOT outlined scales), horns/spines/fins, layered "
        "surface accents (glowing cracks, ember veins, ash patterns), claws, biome-"
        "integrated material details. The creature should read as a coherent fantasy "
        "creature with material logic and mobile-game polish -- NOT a generic blob, "
        "NOT over-simplified.\n\n"
        "INNER LINE RESTRAINT: Minimize inner black lines. Use a thick black OUTER "
        "outline only. Where a major shape break or thickness change really needs "
        "definition (e.g. a jaw line or a wing fold), use a TAPERED coin-style line "
        "that goes from thick to thin and disappears -- NEVER a full segmentation "
        "line, NEVER scale-by-scale outlines, NEVER texture hatching, NEVER detail "
        "ticks.\n\n"
        "LIGHTING: light direction is top-right. Highlights sit on the upper-right "
        "of forms; shadows fall to the lower-left. Apply consistently across all "
        "surfaces.\n\n"
        "Style: folklore mythological creature (salamander, drake, kirin, chimera, "
        "manticore, basilisk, hydra, phoenix, wyrm, magical reptile, hybrid creature). "
        "Animalistic body plans are fine as long as the creature has clear mythological "
        "features. Hybrid silhouettes work well: antlered drake, six-legged serpent, "
        "fire-maned hound-hybrid, scale-and-feather chimera, etc.\n\n"
        "Body plan: NOT a bipedal humanoid in armor, NOT a beastfolk adventurer "
        "(no upright stance with sword/shield), NOT a plain unenhanced real-world "
        "beast (no plain dog/wolf/lion/tiger without mythological features).\n\n"
        "Build around 1-2 strong defining features (flame-tipped tail, glowing "
        "magma core, fused horns, ember mane, third eye, segmented obsidian "
        "carapace, etc.).\n\n"
        "Composition: full body, faces LEFT in 3/4 view, centered on pure white "
        "background. Thick black outer outline, hard-edged shadows from top-right "
        "lighting."
    )


def upload_if_needed(path_or_name: str) -> str:
    p = Path(path_or_name)
    if p.is_absolute():
        if not p.exists():
            print(f"reference not found: {p}", file=sys.stderr); sys.exit(2)
        boundary = f"----comfyboundary{int(time.time()*1000)}"
        body = []
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        body.append(f"--{boundary}\r\n".encode())
        body.append(f'Content-Disposition: form-data; name="image"; filename="{p.name}"\r\n'.encode())
        body.append(f"Content-Type: {mime}\r\n\r\n".encode())
        body.append(p.read_bytes())
        body.append(f"\r\n--{boundary}--\r\n".encode())
        data = b"".join(body)
        req = urllib.request.Request(
            f"{COMFY_URL}/upload/image", data=data,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read())
        return r.get("name") or p.name
    candidate = INPUT_DIR / path_or_name
    if not candidate.exists():
        print(f"reference '{path_or_name}' not found under {INPUT_DIR}", file=sys.stderr); sys.exit(2)
    return path_or_name


def preflight() -> None:
    print("== preflight: verifying Flux 2 Klein 9B image-edit assets ==")
    checks = [
        ("UNETLoader", "unet_name", KLEIN_DIT),
        ("CLIPLoader", "clip_name", KLEIN_CLIP),
        ("VAELoader",  "vae_name",  FLUX2_VAE),
    ]
    failures = []
    for loader, field, name in checks:
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/object_info/{loader}", timeout=15) as r:
                d = json.loads(r.read())
            allowed = d[loader]["input"]["required"][field][0]
            if name not in allowed:
                failures.append(f"  - {loader}.{field}: {name!r} NOT in accepted list")
            else:
                print(f"  ok  {loader:12s} {field:11s} {name}")
        except Exception as e:
            failures.append(f"  - {loader} lookup failed: {e}")
    if failures:
        print("\nPREFLIGHT FAILED:", file=sys.stderr)
        for f in failures: print(f, file=sys.stderr)
        sys.exit(2)
    print("== preflight ok ==\n")


def build_workflow(positive: str, anchor_name: str, prefix: str, seed: int,
                   width: int, height: int, steps: int, cfg: float,
                   megapixels: float) -> dict:
    # Mirrors the Comfy-Org image_flux2_klein_image_edit_9b_distilled subgraph.
    # Key shape: SamplerCustomAdvanced consumes (noise, guider, sampler, sigmas, latent_image)
    # where `guider` is CFGGuider(model, pos_through_ReferenceLatent, neg_through_ReferenceLatent).
    return {
        "1":  {"class_type": "UNETLoader", "inputs": {
                    "unet_name": KLEIN_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader", "inputs": {
                    "clip_name": KLEIN_CLIP, "type": "flux2", "device": "default"}},
        "3":  {"class_type": "VAELoader", "inputs": {"vae_name": FLUX2_VAE}},
        "4":  {"class_type": "LoadImage", "inputs": {"image": anchor_name}},
        "5":  {"class_type": "ImageScaleToTotalPixels", "inputs": {
                    "image": ["4", 0], "upscale_method": "lanczos",
                    "megapixels": megapixels, "resolution_steps": 1}},
        "6":  {"class_type": "VAEEncode", "inputs": {
                    "pixels": ["5", 0], "vae": ["3", 0]}},
        "7":  {"class_type": "CLIPTextEncode", "inputs": {
                    "text": positive, "clip": ["2", 0]}},
        "8":  {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["7", 0]}},
        "9":  {"class_type": "ReferenceLatent", "inputs": {
                    "conditioning": ["7", 0], "latent": ["6", 0]}},   # positive w/ ref
        "10": {"class_type": "ReferenceLatent", "inputs": {
                    "conditioning": ["8", 0], "latent": ["6", 0]}},   # negative w/ ref
        "11": {"class_type": "EmptyFlux2LatentImage", "inputs": {
                    "width": width, "height": height, "batch_size": 1}},
        "12": {"class_type": "RandomNoise", "inputs": {
                    "noise_seed": seed, "control_after_generate": "fixed"}},
        "13": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "14": {"class_type": "Flux2Scheduler", "inputs": {
                    "steps": steps, "width": width, "height": height}},
        "15": {"class_type": "CFGGuider", "inputs": {
                    "model": ["1", 0], "positive": ["9", 0], "negative": ["10", 0], "cfg": cfg}},
        "16": {"class_type": "SamplerCustomAdvanced", "inputs": {
                    "noise": ["12", 0], "guider": ["15", 0], "sampler": ["13", 0],
                    "sigmas": ["14", 0], "latent_image": ["11", 0]}},
        "17": {"class_type": "VAEDecode", "inputs": {
                    "samples": ["16", 0], "vae": ["3", 0]}},
        "18": {"class_type": "SaveImage", "inputs": {
                    "filename_prefix": f"Enemies/{prefix}", "images": ["17", 0]}},
    }


def submit(workflow: dict) -> dict:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--style-anchor", default="base_character_ref.png",
                   help="character style reference. Default: the frog/fox/snake roster sheet (best results -- multi-silhouette refs let the model pick a fitting body type per subject)")
    p.add_argument("--subject", default="", help="optional concept hint, e.g. 'shrine bell beast'")
    p.add_argument("--biome-name", default=None, choices=list(BIOME_PALETTE.keys()),
                   help="injects palette hint only (materials kept out of prompt to avoid busy detail)")
    p.add_argument("--prefix", default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--steps", type=int, default=4, help="Klein 9B distilled: 4 (canonical Flux2Scheduler)")
    p.add_argument("--cfg", type=float, default=1.0)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--megapixels", type=float, default=1.0,
                   help="reference image rescaled to this MP via ImageScaleToTotalPixels")
    p.add_argument("--no-display", action="store_true")
    args = p.parse_args()

    preflight()
    anchor_name = upload_if_needed(args.style_anchor)
    print(f"style anchor -> input/{anchor_name}")

    today = time.strftime("%Y%m%d")
    prefix = args.prefix or f"{today}_enemy_klein9b"
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    positive = build_prompt(args.subject, args.biome_name)

    workflow = build_workflow(positive, anchor_name, prefix, seed,
                              args.width, args.height, args.steps, args.cfg,
                              args.megapixels)

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{prefix}_workflow-api.json"
    api_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")

    sys.path.insert(0, str(HERE))
    import _api_to_graph
    skill_path, user_path = _api_to_graph.install(workflow, prefix, display=not args.no_display)
    print(f"installed graph -> {user_path.name}")

    result = submit(workflow)
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}", file=sys.stderr)
        sys.exit(3)
    print(f"submitted prompt_id={result['prompt_id']}  seed={seed}  size={args.width}x{args.height}")
    print(f"output -> ComfyUI/output/Enemies/{prefix}_00001_.png")


if __name__ == "__main__":
    main()
