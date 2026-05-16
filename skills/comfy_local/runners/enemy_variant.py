#!/usr/bin/env python3
"""
Enemy variant runner for Luis's the studio game (V4 framework).

Per references/22 (CharacterDesigner_V4.txt): generates VARIANTS of an existing
enemy/creature/biome reference, ~50% faithful to the original. ALWAYS outputs
TWO prompts per call:
  1. SIMPLIFIED PROMPT      — main production variant
  2. CHIBI-INFLUENCED PROMPT — slightly more stylized but still hostile

Both prompts are submitted as a parallel pair in ONE workflow (2 NanoBanana2Direct
calls). Cost: 2 x ~$0.10 per --variations unit (default 1 = 2 generations).

Always requires --reference (V4 is variant-of-existing — never text-only).

CLI:
  python3 runners/enemy_variant.py --subject "shrine guardian" \\
      --reference G:\\path\\to\\original_enemy.png

  python3 runners/enemy_variant.py --subject "shrine guardian" \\
      --reference ... --biome "volcanic"   # biome-adapted variant

Flags:
  --subject "<name>"             required - what to call the variant for slug naming
  --reference <path>             required - the source enemy / creature image
  --biome "<name>"               optional - apply biome mutation rules (forest, swamp,
                                  volcanic, desert, crystal, ...)
  --escalation {standard,elemental,elite,corrupted,boss}  default: standard
  --seed <int>                   optional 32-bit seed
  --resolution {1K,2K}           default: 2K
  --variations N                 default: 1; N>1 = N variant pairs (cost: 2N x ~$0.10)
  --no-display                   skip POST /open_workflow

Style locks taken VERBATIM from references/22. DO NOT paraphrase.
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


# ====== VERBATIM V4 LOCKS (from references/22) ======
# DO NOT paraphrase. Luis tuned this across many iterations.

OPENING_LINE_PATTERN_A = (
    "Generate a 50% faithful variant of the uploaded reference enemy. Preserve "
    "the core creature identity, base anatomy, primary silhouette idea, weapon "
    "type if present, and core magical identity from the reference. Modify armor "
    "style, materials, magical features, danger accents, biome influence, faction "
    "styling, secondary silhouette features, and color palette to create a "
    "believable alternate version. Do NOT radically redesign the creature."
)

UNIVERSAL_DIRECTION_LOCK = (
    "Full-body hostile enemy or boss facing LEFT in a clear 3/4 left-facing view, "
    "centered in frame, pure white background (#FFFFFF), readable side-scrolling "
    "silhouette, 2K resolution."
)

NON_NEGOTIABLE_BLOCK = """\
Non-negotiables:
- NOT anthropomorphic (NOT an animal warrior, NOT beastfolk, NOT a fantasy class character)
- The primary read must be: weird magical monster, cursed being, relic-bound entity,
  possessed form, shrine guardian horror, ritual creature, folklore aberration,
  or animated cursed object
- Avoid familiar real-world beast silhouettes (bear, wolf, lion, gorilla, hound, boar)
- NO human faces, NO human flesh tones, NO human skulls, NO dragon wings
- Hands (when visible) have 3 fingers and a thumb"""

DESIGN_BUDGET_BLOCK = """\
Design budget (single-gimmick rule):
- ONE clear MYSTICAL ANCHOR integrated into the body (lantern heart, crystal growths,
  shrine mask, ritual halo, glowing relic chest, fungal antlers, weapon core,
  spirit fire inside armor)
- ONE clear DANGER ACCENT (hostile eyes, claws, fangs, sharp weapon edges, glowing
  corruption seams, horns, unstable magical core)
- A combat role visually communicated through shape language:
  - triangle/angular = aggressive predatory
  - square/blocky = brute defensive
  - rounded = magical unstable strange
- Avoid floating objects around the character (anchor must be ON the body)"""

CEL_SHADED_RENDER_LOCK = """\
Render style:
- Clean stylized 2D cel-shaded 2-tone art
- Thick black outlines (#000000) on the outer silhouette
- Clean tapered inner line art (5-7 px)
- Hard-edged shadows, no soft blending
- Saturated vibrant colors INCLUDING shadows (NEVER gray/muddy shadows)
- Hard cel shading: exactly 2 flat tones per material (base + shadow)
- NO 3D rendering, NO photorealism, NO painterly gradients, NO plastic surfaces, NO rim lighting
- NO futuristic / sci-fi / robotic elements (no mech armor, cyborg limbs, glowing tech cores)"""

MATERIALS_BLOCK = (
    "Materials palette: bark, bone, stone, fungus, crystal, cloth, leather, "
    "relic metal, roots, chitin, feathers, volcanic rock, enchanted wood, magical "
    "flame, sacred light, cursed growths."
)

MANDATORY_PHRASE = (
    'Prompt a clean stylized 2D Cel-Shaded 2 tone Art version with strong black '
    'outlines and simple color blocking.'
)

SILHOUETTE_TEST_BLOCK = """\
Silhouette test:
If the character were filled with solid black, the silhouette should still
communicate identity and threat - clear head shape, weapon read, shoulder/mantle
shapes, readable limb proportions, visible mystical anchor or dominant body feature.
Many strong enemies derive identity from the head/shoulders/mantle (antlers, long
fur or hair mass, ritual collars, bark crowns, horned masks, oversized shoulders,
draped robes)."""

INHUMAN_FACE_RULE = """\
Inhuman face rule:
Heads/faces strongly favor inhuman monster identity - beast skull masks, carved
wooden faces, horned masks, eyeless masks, glowing eye slits, spirit faces,
elongated heads, ritual helmets, bone or bark visages, abstract non-human facial
structures. NOT ordinary human faces, NOT friendly mascot faces, NOT cute creature
faces, NOT conventional heroic character faces."""

EYE_RULE = """\
Eye style: simple stylized eyes, bold shapes, strong contrast, readable hostile
expressions. NOT realistic human eyes, NOT complex iris detail, NOT glossy anime
eyes, NOT photorealistic pupils."""

# Biome adaptation matrix (ref 22)
BIOME_ADAPTATIONS = {
    "forest": "bark armor, moss growth, leaf mantles, seed/root magic accents",
    "swamp": "algae growth, fungal patches, lantern organs, toxic slime accents",
    "volcanic": "obsidian armor, magma cracks, furnace hearts, ash cloth",
    "desert": "sandstone armor, bone relics, dried wraps, sun-baked shell textures",
    "crystal": "crystal growths, reflective shards, glowing crystal cores, prismatic magical energy",
    "shrine": "ritual collars, ceremonial halos, carved bark, relic-bound details",
    "abyssal": "deep cool tones, void seams, drowned-in-shadow plates, abyssal corruption",
}

ESCALATION_NOTES = {
    "standard": (
        "Standard variant escalation: stronger mystical anchor, slightly heavier armor "
        "or larger weapon emphasis, more intense magical glow or corruption. Same enemy "
        "family, clearly recognizable."
    ),
    "elemental": (
        "Elemental escalation: a clear elemental theme transformation (fire / ice / "
        "electric / gloom-corrupted / holy / fungal / stone-bound). Preserve the core "
        "monster identity while changing materials, glow, danger accents, and magical "
        "behavior to match the element."
    ),
    "elite": (
        "Elite escalation: heavier armor, larger silhouette mass, stronger ritual or "
        "relic identity. Reads as a mid-tier boss version of the same enemy family."
    ),
    "corrupted": (
        "Corrupted escalation: an external hostile force has altered the creature - "
        "curse, possession, relic influence, shrine corruption, parasitic transformation, "
        "ritual alteration, or abyssal influence. This affects anatomy, silhouette, eye "
        "expression, mystical anchor, danger accents, materials, and posture."
    ),
    "boss": (
        "Boss escalation: significantly larger silhouette, dominant ritual/relic identity, "
        "intensified mystical anchor, multiple danger accents working together. Reads as "
        "an end-of-act encounter while still feeling like the same enemy family."
    ),
}

AVOID_LINE = (
    "Avoid: 3D rendering, photorealism, painterly gradients, plastic surfaces, rim lighting, "
    "airbrushed effects, soft blending, gray shadows, muddy shadows, washed out colors, "
    "low saturation, futuristic elements, mechanical pistons, cyborg limbs, glowing tech cores, "
    "human skulls, human faces, human flesh tones, dragon wings, watermarks, text, letters, "
    "numbers, UI overlays, background props. Do NOT design as an animal-person, beastfolk "
    "warrior, humanoid animal, anthropomorphic fantasy creature, or familiar natural beast."
)

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert image-generation engine. You must ALWAYS produce an image.\n"
    "Interpret all user input - regardless of format, intent, or abstraction - as "
    "literal visual directives for image composition.\n"
    "Prioritize generating the visual representation above any text, formatting, or "
    "conversational requests."
)


# ====== Prompt assembly (V4 mandates TWO prompts per call) ======

def _common_blocks(subject: str, biome: str | None, escalation: str) -> list[str]:
    parts = [
        OPENING_LINE_PATTERN_A,
        "",
        UNIVERSAL_DIRECTION_LOCK,
        "",
        MANDATORY_PHRASE,
        "",
        NON_NEGOTIABLE_BLOCK,
        "",
        DESIGN_BUDGET_BLOCK,
        "",
        CEL_SHADED_RENDER_LOCK,
        "",
        MATERIALS_BLOCK,
        "",
        SILHOUETTE_TEST_BLOCK,
        "",
        INHUMAN_FACE_RULE,
        "",
        EYE_RULE,
        "",
        ESCALATION_NOTES[escalation],
    ]
    if biome and biome.lower() in BIOME_ADAPTATIONS:
        parts += [
            "",
            f"Biome adaptation ({biome}):",
            (f"Adapt the variant to feel native to a {biome} environment. "
             f"Influence materials, armor style, magical effects, mystical anchor "
             f"expression, danger accents, color palette, and faction styling. "
             f"Specifically lean into: {BIOME_ADAPTATIONS[biome.lower()]}. The biome "
             f"should generate a magical creature transformed by that environment, "
             f"NOT ordinary wildlife inspired by that biome."),
        ]
    elif biome:
        parts += [
            "",
            f"Biome adaptation ({biome}):",
            (f"Adapt the variant to feel native to a {biome} environment. "
             "Influence materials, armor style, magical effects, mystical anchor "
             "expression, danger accents, color palette. The biome should generate "
             "a magical creature transformed by that environment, NOT ordinary "
             "wildlife inspired by that biome."),
        ]
    return parts


def build_simplified_prompt(subject: str, biome: str | None, escalation: str) -> str:
    parts = [
        f"# SIMPLIFIED variant: {subject}",
        "",
    ]
    parts += _common_blocks(subject, biome, escalation)
    parts += [
        "",
        "Simplified design rule (this prompt's specific lean):",
        "Emphasize gameplay readability. Reduce small decorations, extra armor "
        "layers, and overly complex magical details. Keep the core silhouette, "
        "monster identity, combat role, and mystical anchor crisply readable. "
        "This is the production variant.",
        "",
        AVOID_LINE,
    ]
    return "\n".join(parts)


def build_chibi_influenced_prompt(subject: str, biome: str | None, escalation: str) -> str:
    parts = [
        f"# CHIBI-INFLUENCED variant: {subject}",
        "",
    ]
    parts += _common_blocks(subject, biome, escalation)
    parts += [
        "",
        "Chibi-influenced rule (this prompt's specific lean):",
        "Slightly more stylized and simplified design language while keeping mostly "
        "normal proportions. The goal is stylization for readability, NOT cuteness. "
        "Use cleaner shapes, slightly rounder or more graphic forms where helpful, "
        "simplified armor geometry, and exaggerated enemy features that improve "
        "gameplay clarity. The character must STILL clearly read as a hostile enemy. "
        "Do NOT use full chibi proportions, do NOT make it cute, do NOT turn it into "
        "a mascot, do NOT soften the design until it stops reading as an enemy.",
        "",
        AVOID_LINE,
    ]
    return "\n".join(parts)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "enemy"


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


def upload_image(path: Path) -> str:
    if not path.exists():
        print(f"reference image not found: {path}", file=sys.stderr)
        sys.exit(1)
    boundary = "----EnemyVariantRunnerBoundary"
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


# ====== Workflow builder (always pair Simplified + Chibi-Influenced) ======

def _nb2direct_inputs_common(seed, aspect_ratio, resolution):
    return {
        "model": "Nano Banana 2 (Gemini 3.1 Flash Image)",
        "seed": seed,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "response_modalities": "IMAGE+TEXT",
        "thinking_level": "HIGH",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "api_key": "",
    }


def build_workflow_paired(simplified_prompt, chibi_prompt, base_prefix,
                          variant_pairs, aspect_ratio, resolution, ref_filename):
    """
    Build an API-format workflow with a shared LoadImage and N pairs of
    (Simplified + Chibi-Influenced) NanoBanana2Direct calls.
    variant_pairs is [(seed_simplified, seed_chibi, prefix_simplified, prefix_chibi), ...]
    """
    wf = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": ref_filename},
            "_meta": {"title": "Source enemy reference (shared)"},
        },
        "2": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": simplified_prompt},
            "_meta": {"title": "SIMPLIFIED prompt (shared)"},
        },
        "3": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": chibi_prompt},
            "_meta": {"title": "CHIBI-INFLUENCED prompt (shared)"},
        },
    }
    next_id = 4
    for i, (seed_s, seed_c, pfx_s, pfx_c) in enumerate(variant_pairs):
        s_gid, s_sid = str(next_id), str(next_id + 1)
        c_gid, c_sid = str(next_id + 2), str(next_id + 3)
        wf[s_gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["2", 0],
                **_nb2direct_inputs_common(seed_s, aspect_ratio, resolution),
                "images": ["1", 0],
            },
            "_meta": {"title": f"NB2 Direct - SIMPLIFIED v{i+1:02d}"},
        }
        wf[s_sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": pfx_s, "images": [s_gid, 0]},
            "_meta": {"title": f"Save - SIMPLIFIED v{i+1:02d}"},
        }
        wf[c_gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["3", 0],
                **_nb2direct_inputs_common(seed_c, aspect_ratio, resolution),
                "images": ["1", 0],
            },
            "_meta": {"title": f"NB2 Direct - CHIBI v{i+1:02d}"},
        }
        wf[c_sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": pfx_c, "images": [c_gid, 0]},
            "_meta": {"title": f"Save - CHIBI v{i+1:02d}"},
        }
        next_id += 4
    return wf


# ====== Graph format (visual layout in 3 columns of paired rows) ======

def _node_nb2direct_widgets(seed, aspect_ratio, resolution):
    return [
        "",
        "Nano Banana 2 (Gemini 3.1 Flash Image)",
        seed,
        "randomize",
        aspect_ratio,
        resolution,
        "IMAGE+TEXT",
        "HIGH",
        DEFAULT_SYSTEM_PROMPT,
        "",
    ]


def _wrap_graph(nodes, links):
    return {
        "id": "enemy-variant",
        "revision": 0,
        "last_node_id": max(n["id"] for n in nodes),
        "last_link_id": max((l[0] for l in links), default=0),
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"ds": {"scale": 0.85, "offset": [0, 0]}},
        "version": 0.4,
    }


def build_graph_paired(simplified_prompt, chibi_prompt, variant_pairs,
                       aspect_ratio, resolution, ref_filename):
    n = len(variant_pairs)
    # Shared upstream nodes
    img_links = list(range(1, 2 * n + 1))            # 1..2n for the LoadImage fan-out
    sprompt_links = list(range(2 * n + 1, 3 * n + 1))  # 2n+1..3n for SIMPLIFIED prompt
    cprompt_links = list(range(3 * n + 1, 4 * n + 1))  # 3n+1..4n for CHIBI prompt

    nodes = [
        {
            "id": 1, "type": "LoadImage",
            "pos": [-2400, -700], "size": [336, 374], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": img_links, "slot_index": 0},
                {"name": "MASK", "type": "MASK", "links": None},
            ],
            "properties": {"Node name for S&R": "LoadImage"},
            "widgets_values": [ref_filename, "image"],
        },
        {
            "id": 2, "type": "PrimitiveStringMultiline",
            "pos": [-2000, -700], "size": [400, 600], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "STRING", "type": "STRING",
                        "links": sprompt_links, "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
            "widgets_values": [simplified_prompt],
        },
        {
            "id": 3, "type": "PrimitiveStringMultiline",
            "pos": [-2000, 0], "size": [400, 600], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "STRING", "type": "STRING",
                        "links": cprompt_links, "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
            "widgets_values": [chibi_prompt],
        },
    ]
    links = []
    next_id = 4
    save_link_seq = 5000
    row_h = 520
    for i, (seed_s, seed_c, pfx_s, pfx_c) in enumerate(variant_pairs):
        # Per-pair links from upstream
        s_img, c_img = img_links[2 * i], img_links[2 * i + 1]
        s_prompt = sprompt_links[i]
        c_prompt = cprompt_links[i]
        # SIMPLIFIED nodes (top row)
        s_gid, s_sid = next_id, next_id + 1
        # CHIBI nodes (bottom row)
        c_gid, c_sid = next_id + 2, next_id + 3
        next_id += 4
        s_save_link = save_link_seq
        c_save_link = save_link_seq + 1
        save_link_seq += 2
        y_top = -700 + i * row_h
        y_bot = 0 + i * row_h

        # SIMPLIFIED Gemini node
        nodes.append({
            "id": s_gid, "type": "NanoBanana2Direct",
            "pos": [-1500, y_top], "size": [400, 497], "flags": {}, "order": i + 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": s_prompt, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": s_img},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [s_save_link], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(seed_s, aspect_ratio, resolution),
        })
        nodes.append({
            "id": s_sid, "type": "SaveImage",
            "pos": [-1000, y_top], "size": [400, 400], "flags": {},
            "order": i + 1 + 2 * len(variant_pairs), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": s_save_link}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [pfx_s],
        })
        # CHIBI Gemini node (below)
        nodes.append({
            "id": c_gid, "type": "NanoBanana2Direct",
            "pos": [-1500, y_bot], "size": [400, 497], "flags": {}, "order": i + 1 + len(variant_pairs), "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": c_prompt, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": c_img},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [c_save_link], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(seed_c, aspect_ratio, resolution),
        })
        nodes.append({
            "id": c_sid, "type": "SaveImage",
            "pos": [-1000, y_bot], "size": [400, 400], "flags": {},
            "order": i + 1 + 3 * len(variant_pairs), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": c_save_link}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [pfx_c],
        })

        links.append([s_img, 1, 0, s_gid, 1, "IMAGE"])
        links.append([s_prompt, 2, 0, s_gid, 0, "STRING"])
        links.append([s_save_link, s_gid, 0, s_sid, 0, "IMAGE"])
        links.append([c_img, 1, 0, c_gid, 1, "IMAGE"])
        links.append([c_prompt, 3, 0, c_gid, 0, "STRING"])
        links.append([c_save_link, c_gid, 0, c_sid, 0, "IMAGE"])

    return _wrap_graph(nodes, links)


# ====== Main ======

def main():
    p = argparse.ArgumentParser(
        description="V4 enemy variant runner - always emits Simplified + Chibi pair (NanoBanana2Direct).",
    )
    p.add_argument("--subject", required=True, help='Variant name slug, e.g. "shrine guardian volcanic"')
    p.add_argument("--reference", required=True, help="REQUIRED: source enemy/creature image")
    p.add_argument("--biome", default=None,
                   help="Biome adaptation: forest/swamp/volcanic/desert/crystal/shrine/abyssal "
                        "(or any custom name)")
    p.add_argument("--escalation",
                   choices=["standard", "elemental", "elite", "corrupted", "boss"],
                   default="standard", help="Variant escalation level")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--resolution", choices=["1K", "2K"], default="2K")
    p.add_argument("--variations", type=int, default=1,
                   help="N pairs to generate (each pair = 2 calls). Default 1 (= 2 generations). "
                        "Cost: 2N x ~$0.10")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    # Each pair gets 2 seeds (one for each prompt) so both are independent
    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 2 * args.variations - 1)
    aspect_ratio = "3:4"  # characters / enemies are taller than wide
    subject_slug = slugify(args.subject)
    biome_tag = f"_{args.biome}" if args.biome else ""
    base_prefix = f"enemies/{subject_slug}{biome_tag}_{args.escalation}"

    # Upload reference once
    ref_path = Path(args.reference).expanduser().resolve()
    ref_filename = upload_image(ref_path)
    print(f"uploaded reference: {ref_path.name} -> {ref_filename}")

    # Build the two prompts
    simplified_prompt = build_simplified_prompt(args.subject, args.biome, args.escalation)
    chibi_prompt = build_chibi_influenced_prompt(args.subject, args.biome, args.escalation)

    # Build the variant pairs (each pair has its own 2 seeds)
    variant_pairs = []
    for i in range(args.variations):
        seed_s = base_seed + 2 * i
        seed_c = base_seed + 2 * i + 1
        pfx_s = f"{base_prefix}_simplified_v{i+1:02d}"
        pfx_c = f"{base_prefix}_chibi_v{i+1:02d}"
        variant_pairs.append((seed_s, seed_c, pfx_s, pfx_c))

    api_wf = build_workflow_paired(simplified_prompt, chibi_prompt, base_prefix,
                                   variant_pairs, aspect_ratio, args.resolution, ref_filename)
    graph_wf = build_graph_paired(simplified_prompt, chibi_prompt, variant_pairs,
                                  aspect_ratio, args.resolution, ref_filename)

    base_filename = (f"enemy_variant_{subject_slug}{biome_tag}_{args.escalation}"
                     f"_x{args.variations}")

    WORKFLOWS_DIR.mkdir(exist_ok=True)
    api_path = WORKFLOWS_DIR / f"{base_filename}_workflow-api.json"
    graph_path = WORKFLOWS_DIR / f"{base_filename}_workflow.json"
    api_path.write_text(json.dumps(api_wf, indent=2), encoding="utf-8")
    graph_path.write_text(json.dumps(graph_wf, indent=2), encoding="utf-8")
    print(f"wrote {api_path.name}")
    print(f"wrote {graph_path.name}")

    result = http_post_json("/prompt", {"prompt": api_wf})
    if result.get("node_errors"):
        print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}",
              file=sys.stderr)
        sys.exit(3)

    cost = 2 * args.variations * 0.10
    print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
          f"subject={args.subject!r} biome={args.biome!r} escalation={args.escalation} "
          f"variations={args.variations}")
    print(f"seeds: simplified={[base_seed + 2*i for i in range(args.variations)]}, "
          f"chibi={[base_seed + 2*i + 1 for i in range(args.variations)]}")
    print(f"estimated cost: ~${cost:.2f} ({2*args.variations} x ~$0.10 — Simplified + Chibi pairs)")
    print(f"output prefixes:")
    print(f"  simplified: {base_prefix}_simplified_v01 .. _v{args.variations:02d}")
    print(f"  chibi:      {base_prefix}_chibi_v01 .. _v{args.variations:02d}")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
