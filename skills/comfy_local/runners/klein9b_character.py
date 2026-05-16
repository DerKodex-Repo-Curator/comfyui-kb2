#!/usr/bin/env python3
"""
POP character generator — Flux 2 Klein 9B + pop_v3_style_klein9b_v2 LoRA.

Mirror of flux1_character.py with the same category-aware prompt builder
but using the Klein 9B pipeline instead of Flux.1 dev. Same trigger word
(pop_v3_style), same direction convention (LEFT), same composition tail —
this way the only thing that varies between the two runners is the base model
+ matching LoRA. Direct A/B comparisons are clean.

Usage:
  python runners/klein9b_character.py
      --subject "shrine bell beast"
      --category {chibi,hero,monster,object,serpentine}
      [--feature "with a glowing magma core"]
      [--strength N]
      [--seed N]
      [--steps 14] [--shift 3.0]
      [--width 1024] [--height 1024]
      [--prefix NAME]
      [--no-display]

Klein 9B canonical inference settings (per ref 5 + sample tests):
  - euler / simple sampler
  - 14 steps (Klein 9B converges faster than Flux.1 dev's 20)
  - cfg=1 (guidance-distilled, no FluxGuidance node needed)
  - shift=3 via ModelSamplingAuraFlow
  - EmptyFlux2LatentImage (128-ch /16 spatial -- NOT EmptySD3LatentImage)

Output: ComfyUI/output/POP/<prefix>_NNNNN_.png
"""
from __future__ import annotations
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"

KLEIN_DIT  = "flux-2-klein-9b-fp8.safetensors"
KLEIN_CLIP = "qwen_3_8b_fp8mixed.safetensors"
FLUX2_VAE  = "flux2-vae.safetensors"
POP_LORA   = "pop_v3_style_klein9b_v2.safetensors"
TRIGGER    = "pop_v3_style"

# Same prompt-engineering recipes as the Flux.1 runner (per testing 2026-05-10
# these clauses fixed the failure modes on both LoRAs equally). Keeping them
# verbatim and identical so A/B comparisons isolate base-model differences.
CATEGORY_SILHOUETTE = {
    "chibi": "",
    "hero":  "bipedal warrior stance",
    "monster": "hulking creature with bold material details",
    "object": (
        "the {form_noun} shape is the body, two stubby legs hanging below the rim, "
        "no arms, glowing eyes or face features integrated into the {form_noun} surface, "
        "dangling tassel or chain ornaments"
    ),
    "serpentine": (
        "long coiled serpent body, raised humanoid torso, no legs, "
        "scale-patterned tail visible, mature warrior character"
    ),
}

CATEGORY_STRENGTH = {
    "chibi":      1.0,
    "hero":       1.0,
    "monster":    1.2,
    "object":     1.0,
    "serpentine": 1.0,
}

DIRECTION = (
    "facing LEFT in 3/4 left-facing view, head turned LEFT, "
    "eyes and pupils looking LEFT"
)
COMPOSITION = "full body, centered, white background"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:48] or "subject"


def extract_form_noun(subject: str) -> str:
    common = ("bell", "lantern", "candle", "mask", "mound", "cauldron",
              "shell", "vase", "orb", "shrine", "amulet")
    low = subject.lower()
    for n in common:
        if n in low:
            return n
    words = [w for w in re.findall(r"[a-z]+", low) if len(w) > 2]
    return words[0] if words else "form"


def build_prompt(subject: str, category: str, feature: str | None) -> str:
    parts = [TRIGGER, subject.strip()]
    if feature:
        parts.append(feature.strip())
    silhouette = CATEGORY_SILHOUETTE.get(category, "")
    if silhouette:
        form_noun = extract_form_noun(subject) if "{form_noun}" in silhouette else None
        parts.append(silhouette.format(form_noun=form_noun) if form_noun else silhouette)
    parts.append(COMPOSITION)
    parts.append(DIRECTION)
    return ", ".join(parts)


def preflight() -> None:
    print("== preflight ==")
    checks = [
        ("UNETLoader",          "unet_name",  KLEIN_DIT),
        ("CLIPLoader",          "clip_name",  KLEIN_CLIP),
        ("VAELoader",           "vae_name",   FLUX2_VAE),
        ("LoraLoaderModelOnly", "lora_name",  POP_LORA),
    ]
    failures = []
    seen: dict[str, dict] = {}
    for loader, field, name in checks:
        try:
            if loader not in seen:
                with urllib.request.urlopen(f"{COMFY_URL}/object_info/{loader}", timeout=15) as r:
                    seen[loader] = json.loads(r.read())
            allowed = seen[loader][loader]["input"]["required"][field][0]
            if name not in allowed:
                failures.append(f"  - {loader}.{field}: {name!r} not in dropdown")
            else:
                print(f"  ok  {loader:24s} {field:11s} {name}")
        except Exception as e:
            failures.append(f"  - {loader} lookup failed: {e}")
    if failures:
        print("\nPREFLIGHT FAILED:", file=sys.stderr)
        for f in failures: print(f, file=sys.stderr)
        sys.exit(2)
    print("== preflight ok ==\n")


def build_workflow(prompt: str, prefix: str, seed: int, strength: float,
                   width: int, height: int, steps: int, shift: float) -> dict:
    # Klein 9B text-to-image pipeline:
    # UNET -> LoraLoaderModelOnly -> ModelSamplingAuraFlow(shift=3) -> KSampler
    # CLIP -> CLIPTextEncode -> KSampler.positive
    # ConditioningZeroOut on positive -> KSampler.negative (distilled, cfg=1)
    # EmptyFlux2LatentImage (128-ch /16 spatial) -> KSampler.latent_image
    return {
        "1":  {"class_type": "UNETLoader",      "inputs": {"unet_name": KLEIN_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "CLIPLoader",      "inputs": {"clip_name": KLEIN_CLIP, "type": "flux2", "device": "default"}},
        "3":  {"class_type": "VAELoader",       "inputs": {"vae_name": FLUX2_VAE}},
        "4":  {"class_type": "LoraLoaderModelOnly", "inputs": {
                    "lora_name": POP_LORA, "strength_model": strength, "model": ["1", 0]}},
        "5":  {"class_type": "ModelSamplingAuraFlow", "inputs": {"shift": shift, "model": ["4", 0]}},
        "6":  {"class_type": "CLIPTextEncode",   "inputs": {"text": prompt, "clip": ["2", 0]}},
        "7":  {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "8":  {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "9":  {"class_type": "KSampler",         "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": steps, "cfg": 1.0,
                    "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                    "model": ["5", 0], "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["8", 0]}},
        "10": {"class_type": "VAEDecode",        "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "SaveImage",        "inputs": {
                    "filename_prefix": f"POP/{prefix}", "images": ["10", 0]}},
    }


def submit(workflow: dict) -> dict:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=payload,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--subject", required=True)
    p.add_argument("--category", required=True, choices=list(CATEGORY_SILHOUETTE.keys()))
    p.add_argument("--feature", default=None)
    p.add_argument("--strength", type=float, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--steps", type=int, default=14, help="Klein 9B canonical = 14 (faster than Flux.1)")
    p.add_argument("--shift", type=float, default=3.0)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--prefix", default=None)
    p.add_argument("--no-display", action="store_true")
    args = p.parse_args()

    preflight()

    today = time.strftime("%Y%m%d")
    slug = slugify(args.subject)
    prefix = args.prefix or f"{today}_klein9b_{args.category}_{slug}"
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    strength = args.strength if args.strength is not None else CATEGORY_STRENGTH[args.category]

    prompt = build_prompt(args.subject, args.category, args.feature)
    print(f"category : {args.category}")
    print(f"strength : {strength}")
    print(f"prompt   : {prompt}\n")

    workflow = build_workflow(prompt, prefix, seed, strength,
                              args.width, args.height, args.steps, args.shift)

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
    print(f"submitted prompt_id={result['prompt_id']}  seed={seed}  {args.width}x{args.height}")
    print(f"output -> ComfyUI/output/POP/{prefix}_00001_.png")


if __name__ == "__main__":
    main()
