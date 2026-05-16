#!/usr/bin/env python3
"""
POP character generator — Flux.1 dev + pop_v3_style_flux1_v2 LoRA.

Category-aware prompt builder that auto-injects silhouette guidance and
sets the right LoRA strength per subject type. Codifies the recipes worked
out during the v2 LoRA testing session (2026-05-10).

Usage:
  python runners/flux1_character.py
      --subject "shrine bell beast"
      --category {chibi,hero,monster,object,serpentine}
      [--feature "with a glowing magma core"]   extra feature(s) beyond category
      [--strength N]                             override default category strength
      [--seed N]
      [--steps 20] [--guidance 3.5]
      [--width 1024] [--height 1024]
      [--prefix NAME]
      [--no-display]

Per-category defaults (worked out via testing 2026-05-10):
  chibi      : small anthro NPC (deer healer, owl scholar, fox ranger) -- strength 1.0
  hero       : bipedal warrior (Shiba hero, snake warrior)             -- strength 1.0
  monster    : hulking creature (golem, treant, beast)                 -- strength 1.2
  object     : bell, lantern, candle, mask (no humanoid silhouette)    -- strength 1.0
  serpentine : snake archer, naga, serpent hybrid                      -- strength 1.0

Universal pipeline conventions injected (per ref 19): faces LEFT, 3/4 view,
white background, trigger word "pop_v3_style".

Output: ComfyUI/output/POP/<prefix>_<category>_<subject_slug>_NNNNN_.png
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

# Verified asset filenames (see references/15_verification_checklist.md)
FLUX1_DIT     = "flux1-dev-fp8.safetensors"
FLUX1_CLIP_L  = "clip_l.safetensors"
FLUX1_T5XXL   = "t5xxl_fp8_e4m3fn_scaled.safetensors"
FLUX1_VAE     = "ae.safetensors"
POP_LORA      = "pop_v3_style_flux1_v2.safetensors"
TRIGGER       = "pop_v3_style"

# DO NOT paraphrase -- these clauses are verbatim from the prompt-engineering
# recovery tests that fixed the failure modes for each category. The "the X
# shape is the body" pattern for object-creatures and the "long coiled serpent
# body, raised humanoid torso, no legs" pattern for serpentines were the
# silver bullets in the 2026-05-10 session.
CATEGORY_SILHOUETTE = {
    "chibi": "",  # no special silhouette guidance needed; LoRA + base model handle it
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

# Strength tuned per category from testing — chunkier subjects tolerate more
# LoRA pressure without anatomical warping; chibi NPCs warp at higher strength.
CATEGORY_STRENGTH = {
    "chibi":      1.0,
    "hero":       1.0,
    "monster":    1.2,
    "object":     1.0,
    "serpentine": 1.0,
}

# Per ref 19 universal pipeline convention — everything faces LEFT
DIRECTION = (
    "facing LEFT in 3/4 left-facing view, head turned LEFT, "
    "eyes and pupils looking LEFT"
)

# Common composition tail
COMPOSITION = "full body, centered, white background"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:48] or "subject"


def extract_form_noun(subject: str) -> str:
    """For object-creature subjects, try to extract the primary form noun
    (e.g. 'shrine bell beast' -> 'bell', 'lantern parasite' -> 'lantern').
    Falls back to first noun-ish word."""
    common = ("bell", "lantern", "candle", "mask", "mound", "cauldron",
              "shell", "vase", "orb", "shrine", "amulet")
    low = subject.lower()
    for n in common:
        if n in low:
            return n
    # fall back to first content word
    words = [w for w in re.findall(r"[a-z]+", low) if len(w) > 2]
    return words[0] if words else "form"


def build_prompt(subject: str, category: str, feature: str | None) -> str:
    """Assemble the full positive prompt with trigger, subject, category-specific
    silhouette guidance, optional feature, direction, and composition tail."""
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
    """Verify all required models exist in ComfyUI's accepted lists. Aborts
    before submission if anything's missing (catches typos in filenames before
    the workflow gets rejected at /prompt)."""
    print("== preflight ==")
    checks = [
        ("UNETLoader",          "unet_name",  FLUX1_DIT),
        ("DualCLIPLoader",      "clip_name1", FLUX1_CLIP_L),
        ("DualCLIPLoader",      "clip_name2", FLUX1_T5XXL),
        ("VAELoader",           "vae_name",   FLUX1_VAE),
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
                   width: int, height: int, steps: int, guidance: float) -> dict:
    return {
        "1":  {"class_type": "UNETLoader",          "inputs": {"unet_name": FLUX1_DIT, "weight_dtype": "default"}},
        "2":  {"class_type": "DualCLIPLoader",      "inputs": {"clip_name1": FLUX1_CLIP_L, "clip_name2": FLUX1_T5XXL, "type": "flux", "device": "default"}},
        "3":  {"class_type": "VAELoader",           "inputs": {"vae_name": FLUX1_VAE}},
        "4":  {"class_type": "LoraLoaderModelOnly", "inputs": {
                    "lora_name": POP_LORA, "strength_model": strength, "model": ["1", 0]}},
        "5":  {"class_type": "CLIPTextEncode",      "inputs": {"text": prompt, "clip": ["2", 0]}},
        "6":  {"class_type": "FluxGuidance",        "inputs": {"guidance": guidance, "conditioning": ["5", 0]}},
        "7":  {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["5", 0]}},
        "8":  {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "9":  {"class_type": "KSampler",            "inputs": {
                    "seed": seed, "control_after_generate": "fixed",
                    "steps": steps, "cfg": 1.0,
                    "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                    "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["8", 0]}},
        "10": {"class_type": "VAEDecode",           "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "SaveImage",           "inputs": {
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
    p.add_argument("--subject", required=True, help="subject description (e.g. 'shrine bell beast')")
    p.add_argument("--category", required=True, choices=list(CATEGORY_SILHOUETTE.keys()),
                   help="subject category — drives silhouette guidance + LoRA strength")
    p.add_argument("--feature", default=None, help="extra feature(s) to layer on the subject")
    p.add_argument("--strength", type=float, default=None,
                   help=f"LoRA strength override (defaults: {CATEGORY_STRENGTH})")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--guidance", type=float, default=3.5)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--prefix", default=None)
    p.add_argument("--no-display", action="store_true")
    args = p.parse_args()

    preflight()

    today = time.strftime("%Y%m%d")
    slug = slugify(args.subject)
    prefix = args.prefix or f"{today}_flux1_{args.category}_{slug}"
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
    strength = args.strength if args.strength is not None else CATEGORY_STRENGTH[args.category]

    prompt = build_prompt(args.subject, args.category, args.feature)
    print(f"category : {args.category}")
    print(f"strength : {strength}")
    print(f"prompt   : {prompt}\n")

    workflow = build_workflow(prompt, prefix, seed, strength,
                              args.width, args.height, args.steps, args.guidance)

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
