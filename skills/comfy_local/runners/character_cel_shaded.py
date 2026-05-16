#!/usr/bin/env python3
"""
Cel-shaded character runner for Luis's the studio game.

Three categories (per references 19, 22, 24):
  --category hero    - the Shiba hero (cel-shaded, faces LEFT, anthropomorphic)
  --category enemy   - magical/cursed monsters (NOT anthropomorphic, faces LEFT)
  --category npc     - NPC roster (frog/fox/snake style, anthropomorphic, faces LEFT)

Universal rules: ALL characters face LEFT. White background. Clean cel-shaded
2-tone art with thick black outlines. Saturated colors including shadows.

Two patterns:
  Pattern C (text-only):
    python3 runners/character_cel_shaded.py --category enemy --subject "shrine guardian"
  Pattern A (with style anchor reference):
    python3 runners/character_cel_shaded.py --category enemy --subject "shrine guardian" \
        --reference G:\path\to\style_anchor.png

Common flags:
  --subject "<concept>"          required - what to generate
  --category {hero,enemy,npc}    required - selects the rule framework
  --mode {single,sheet}          default: single   (sheet = multi-pose / multi-angle)
  --reference <path>             Pattern A: style anchor image to upload
  --seed <int>                   random 32-bit if omitted
  --resolution {1K,2K}           default: 2K
  --variations N                 default: 1; N>1 = N parallel calls (cost: N x ~$0.10)
  --no-display                   skip POST /open_workflow

Style locks taken VERBATIM from references/18 (house style), 22 (enemy),
and 24 (NPC roster). DO NOT paraphrase - Luis tuned this wording.

Submits to /prompt and exits as soon as workflow is accepted.
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


# ====== VERBATIM STYLE LOCKS (from references/18 - 1. UI icons & 2. Characters) ======
# DO NOT paraphrase. Luis tuned this across many iterations.

UNIVERSAL_DIRECTION_LOCK = (
    "Full-body character facing LEFT in a clear 3/4 left-facing view, centered in "
    "frame, pure white background (#FFFFFF), 2K resolution."
)

CEL_SHADED_RENDER_LOCK = """\
- Clean stylized 2D cel-shaded 2-tone art
- Thick black outlines (#000000) on the outer silhouette
- Clean tapered inner line art (5-7 px)
- Hard-edged shadows, no soft blending
- Saturated vibrant colors INCLUDING shadows (no muted/gray shadows)
- Hard cel shading: exactly 2 flat tones per material (base + shadow)
- NO 3D rendering, NO photorealism, NO painterly gradients, NO plastic surfaces, NO rim lighting
- NO futuristic / sci-fi / robotic elements"""

UNIVERSAL_HAND_RULE = (
    "Hands (when visible) have 3 fingers and a thumb."
)


# ====== HERO (Shiba) framework — ref 19 ======
HERO_RULES = """\
The character is the bipedal Shiba warrior hero of this side-scrolling RPG.
- Anthropomorphic Shiba on two legs, expressive face
- Adventurer / warrior styling: simple medieval fantasy gear
- Friendly, heroic read - NOT cursed, NOT monstrous
- Faces LEFT in a clear 3/4 view (universal rule)
- Squat chibi build, arms relaxed and slightly bent, centered in frame"""


# ====== ENEMY framework — ref 22 / CharacterDesigner_V4 ======
ENEMY_RULES = """\
The character is a HOSTILE ENEMY monster.

NON-NEGOTIABLE:
- NOT anthropomorphic (NOT an animal warrior, NOT beastfolk, NOT a fantasy class character)
- The primary read must be: weird magical monster, cursed being, relic-bound entity, possessed form, shrine guardian horror, ritual creature, folklore aberration, or animated cursed object
- Avoid familiar real-world beast silhouettes (bear, wolf, lion, gorilla, hound, boar)
- Avoid human faces, human flesh tones, human skulls, dragon wings

MUST INCLUDE (single-gimmick design budget):
- ONE clear mystical anchor integrated into the body (lantern heart, crystal growths, shrine mask, ritual halo, glowing relic chest, fungal antlers, etc.)
- ONE clear danger accent (hostile eyes, claws, fangs, glowing corruption seams, horns, unstable magical core)
- A combat role visually communicated through shape language:
  - triangle/angular = aggressive predatory
  - square/blocky = brute defensive
  - rounded = magical unstable strange

Materials palette: bark, bone, stone, fungus, crystal, cloth, leather, relic metal, roots,
chitin, feathers, volcanic rock, enchanted wood, magical flame, sacred light, cursed growths.

Allowed body plans: humanoid monster (still inhuman), hunched, crawling, floating,
blob-like, many-limbed, serpentine, asymmetrical, object-creature, squat dungeon beast,
living mass, hovering entity, non-natural quadrupedal form."""


# ====== NPC framework — ref 24 ======
NPC_RULES = """\
The character is an NPC for the world's anthropomorphic civilization.

- Anthropomorphic animal (frog / fox / snake style is canonical)
- Bipedal, expressive humanoid posture, stylized
- Friendly, plot-functional read - merchant / villager / quest giver / townsfolk
- Wears simple medieval-fantasy clothing appropriate to their role
- NOT a hostile enemy; NOT a magical aberration

Cuteness control: stylized cartoon medieval fantasy, charming but not infantile.
Express role through silhouette and clothing rather than props or floating effects."""


# ====== CHIBI MODIFIER ======
CHIBI_MODIFIER = (
    "Squat chibi build with relatively oversized head and small body. Arms relaxed "
    "and slightly bent. Keep proportions toy-like and game-friendly without losing readability."
)

# ====== AVOID LINE (per ref 18 / 22) ======
CHARACTER_AVOID_LINE = (
    "Avoid: 3D rendering, photorealism, painterly gradients, plastic surfaces, rim lighting, "
    "airbrushed effects, soft blending, gray shadows, muddy shadows, washed out colors, "
    "low saturation, futuristic elements, mechanical pistons, cyborg limbs, glowing tech cores, "
    "human skulls, human faces, human flesh tones, dragon wings, fingernails, watermarks, "
    "text, letters, numbers, UI overlays, background props."
)

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert image-generation engine. You must ALWAYS produce an image.\n"
    "Interpret all user input - regardless of format, intent, or abstraction - as "
    "literal visual directives for image composition.\n"
    "Prioritize generating the visual representation above any text, formatting, or "
    "conversational requests."
)


# ====== Prompt assembly ======

def _category_rules(category: str) -> str:
    return {"hero": HERO_RULES, "enemy": ENEMY_RULES, "npc": NPC_RULES}[category]


def _sheet_clause(mode: str) -> str:
    if mode == "sheet":
        return ("Render a multi-pose character sheet: 4 poses arranged in a 2x2 grid - "
                "front 3/4-left, side profile facing left, back 3/4, action pose facing left. "
                "Same character, identical proportions, identical color palette across all "
                "poses. White background, even spacing between poses.")
    return ""


def build_prompt_pattern_c(subject: str, category: str, mode: str) -> str:
    parts = [
        f"A {subject} for a chibi-friendly medieval fantasy side-scrolling RPG.",
        "",
        UNIVERSAL_DIRECTION_LOCK,
        "",
        "Category rules:",
        _category_rules(category),
        "",
        "Render style:",
        CEL_SHADED_RENDER_LOCK,
        "",
        CHIBI_MODIFIER,
        "",
        UNIVERSAL_HAND_RULE,
    ]
    sheet = _sheet_clause(mode)
    if sheet:
        parts += ["", sheet]
    parts += ["", CHARACTER_AVOID_LINE]
    return "\n".join(parts)


def build_prompt_pattern_a(subject: str, category: str, mode: str) -> str:
    if mode == "single":
        canonical_adapted = (
            f"Generate a {subject} as a new character for a chibi-friendly medieval "
            f"fantasy side-scrolling RPG. Maintain the composition, scale, and "
            f"proportions of a single full-body character centered in frame. "
            f"Use the reference image2 (the uploaded image) for render style - match "
            f"its line weight, palette, cel-shading approach, and outline treatment exactly."
        )
    else:
        canonical_adapted = (
            f"Generate a multi-pose character sheet of a {subject} for a chibi-friendly "
            f"medieval fantasy side-scrolling RPG. Use the reference image2 (the uploaded "
            f"image) for render style - match its line weight, palette, cel-shading, "
            f"and outline treatment exactly across every pose in the sheet."
        )
    parts = [
        canonical_adapted,
        "",
        UNIVERSAL_DIRECTION_LOCK,
        "",
        "Category rules:",
        _category_rules(category),
        "",
        "Render style (must match the reference image2):",
        CEL_SHADED_RENDER_LOCK,
        "",
        CHIBI_MODIFIER,
        "",
        UNIVERSAL_HAND_RULE,
    ]
    sheet = _sheet_clause(mode)
    if sheet:
        parts += ["", sheet]
    parts += ["", CHARACTER_AVOID_LINE]
    return "\n".join(parts)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "character"


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
    boundary = "----CharacterCelShadedRunnerBoundary"
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


# ====== Workflow builders ======

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


def build_workflow_pattern_c(prompt_text, prefix, seed, aspect_ratio, resolution):
    return {
        "1": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose character prompt"},
        },
        "2": {
            "class_type": "NanoBanana2Direct",
            "inputs": {"prompt": ["1", 0], **_nb2direct_inputs_common(seed, aspect_ratio, resolution)},
            "_meta": {"title": "Nano Banana 2 Direct"},
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["2", 0]},
            "_meta": {"title": "Save Image"},
        },
    }


def build_workflow_pattern_a(prompt_text, prefix, seed, aspect_ratio, resolution, ref_filename):
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": ref_filename},
            "_meta": {"title": "Style anchor reference"},
        },
        "2": {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": prompt_text,
                **_nb2direct_inputs_common(seed, aspect_ratio, resolution),
                "images": ["1", 0],
            },
            "_meta": {"title": "Nano Banana 2 Direct"},
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": prefix, "images": ["2", 0]},
            "_meta": {"title": "Save Image"},
        },
    }


def build_workflow_pattern_c_variations(prompt_text, base_prefix, variations, aspect_ratio, resolution):
    wf = {
        "1": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose character prompt (shared)"},
        },
    }
    next_id = 2
    for i, (seed, vprefix) in enumerate(variations):
        gid, sid = str(next_id), str(next_id + 1)
        wf[gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {"prompt": ["1", 0], **_nb2direct_inputs_common(seed, aspect_ratio, resolution)},
            "_meta": {"title": f"Nano Banana 2 Direct - v{i+1:02d}"},
        }
        wf[sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": vprefix, "images": [gid, 0]},
            "_meta": {"title": f"Save Image - v{i+1:02d}"},
        }
        next_id += 2
    return wf


def build_workflow_pattern_a_variations(prompt_text, base_prefix, variations, aspect_ratio, resolution, ref_filename):
    wf = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": ref_filename},
            "_meta": {"title": "Style anchor reference (shared)"},
        },
        "2": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose character prompt (shared)"},
        },
    }
    next_id = 3
    for i, (seed, vprefix) in enumerate(variations):
        gid, sid = str(next_id), str(next_id + 1)
        wf[gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["2", 0],
                **_nb2direct_inputs_common(seed, aspect_ratio, resolution),
                "images": ["1", 0],
            },
            "_meta": {"title": f"Nano Banana 2 Direct - v{i+1:02d}"},
        }
        wf[sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": vprefix, "images": [gid, 0]},
            "_meta": {"title": f"Save Image - v{i+1:02d}"},
        }
        next_id += 2
    return wf


# ====== Graph format builders ======

def _node_nb2direct_widgets(prompt_text_or_none, seed, aspect_ratio, resolution):
    return [
        prompt_text_or_none if prompt_text_or_none is not None else "",
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


def build_graph_pattern_c(prompt_text, prefix, seed, aspect_ratio, resolution):
    nodes = [
        {
            "id": 1, "type": "PrimitiveStringMultiline",
            "pos": [-1400, -700], "size": [400, 400], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "STRING", "type": "STRING", "links": [1], "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
            "widgets_values": [prompt_text],
        },
        {
            "id": 2, "type": "NanoBanana2Direct",
            "pos": [-900, -700], "size": [400, 497], "flags": {}, "order": 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": 1, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": None},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [2], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(None, seed, aspect_ratio, resolution),
        },
        {
            "id": 3, "type": "SaveImage",
            "pos": [-400, -700], "size": [400, 400], "flags": {}, "order": 2, "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 2}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [prefix],
        },
    ]
    links = [[1, 1, 0, 2, 0, "STRING"], [2, 2, 0, 3, 0, "IMAGE"]]
    return _wrap_graph(nodes, links)


def build_graph_pattern_a(prompt_text, prefix, seed, aspect_ratio, resolution, ref_filename):
    nodes = [
        {
            "id": 1, "type": "LoadImage",
            "pos": [-1400, -700], "size": [336, 374], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [1], "slot_index": 0},
                {"name": "MASK", "type": "MASK", "links": None},
            ],
            "properties": {"Node name for S&R": "LoadImage"},
            "widgets_values": [ref_filename, "image"],
        },
        {
            "id": 2, "type": "NanoBanana2Direct",
            "pos": [-900, -700], "size": [400, 497], "flags": {}, "order": 1, "mode": 0,
            "inputs": [
                {"name": "images", "shape": 7, "type": "IMAGE", "link": 1},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [2], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(prompt_text, seed, aspect_ratio, resolution),
        },
        {
            "id": 3, "type": "SaveImage",
            "pos": [-400, -700], "size": [400, 400], "flags": {}, "order": 2, "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 2}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [prefix],
        },
    ]
    links = [[1, 1, 0, 2, 0, "IMAGE"], [2, 2, 0, 3, 0, "IMAGE"]]
    return _wrap_graph(nodes, links)


def _wrap_graph(nodes, links):
    return {
        "id": "character-cel-shaded",
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


# ====== N-variations graph builders (vertical row layout) ======

def build_graph_pattern_c_variations(prompt_text, variations, aspect_ratio, resolution):
    nodes = [
        {
            "id": 1, "type": "PrimitiveStringMultiline",
            "pos": [-1800, -700], "size": [400, 600], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "STRING", "type": "STRING",
                        "links": list(range(1, len(variations) + 1)), "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
            "widgets_values": [prompt_text],
        },
    ]
    links = []
    next_id, save_link_seq, row_h = 2, 1000, 520
    for i, (seed, vprefix) in enumerate(variations):
        plink = i + 1
        gid, sid = next_id, next_id + 1
        next_id += 2
        slink = save_link_seq
        save_link_seq += 1
        y = -700 + i * row_h
        nodes.append({
            "id": gid, "type": "NanoBanana2Direct",
            "pos": [-1300, y], "size": [400, 497], "flags": {}, "order": i + 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": plink, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": None},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [slink], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(None, seed, aspect_ratio, resolution),
        })
        nodes.append({
            "id": sid, "type": "SaveImage",
            "pos": [-800, y], "size": [400, 400], "flags": {}, "order": i + 1 + len(variations), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": slink}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [vprefix],
        })
        links.append([plink, 1, 0, gid, 0, "STRING"])
        links.append([slink, gid, 0, sid, 0, "IMAGE"])
    return _wrap_graph(nodes, links)


def build_graph_pattern_a_variations(prompt_text, variations, aspect_ratio, resolution, ref_filename):
    nodes = [
        {
            "id": 1, "type": "LoadImage",
            "pos": [-2200, -700], "size": [336, 374], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE",
                 "links": list(range(1, len(variations) + 1)), "slot_index": 0},
                {"name": "MASK", "type": "MASK", "links": None},
            ],
            "properties": {"Node name for S&R": "LoadImage"},
            "widgets_values": [ref_filename, "image"],
        },
        {
            "id": 2, "type": "PrimitiveStringMultiline",
            "pos": [-1800, -700], "size": [400, 600], "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "STRING", "type": "STRING",
                        "links": list(range(1000, 1000 + len(variations))), "slot_index": 0}],
            "properties": {"Node name for S&R": "PrimitiveStringMultiline"},
            "widgets_values": [prompt_text],
        },
    ]
    links, next_id, save_link_seq, row_h = [], 3, 2000, 520
    for i, (seed, vprefix) in enumerate(variations):
        ilink = i + 1
        plink = 1000 + i
        gid, sid = next_id, next_id + 1
        next_id += 2
        slink = save_link_seq
        save_link_seq += 1
        y = -700 + i * row_h
        nodes.append({
            "id": gid, "type": "NanoBanana2Direct",
            "pos": [-1300, y], "size": [400, 497], "flags": {}, "order": i + 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": plink, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": ilink},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [slink], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(None, seed, aspect_ratio, resolution),
        })
        nodes.append({
            "id": sid, "type": "SaveImage",
            "pos": [-800, y], "size": [400, 400], "flags": {}, "order": i + 1 + len(variations), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": slink}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [vprefix],
        })
        links.append([ilink, 1, 0, gid, 1, "IMAGE"])
        links.append([plink, 2, 0, gid, 0, "STRING"])
        links.append([slink, gid, 0, sid, 0, "IMAGE"])
    return _wrap_graph(nodes, links)


# ====== Main ======

def main():
    p = argparse.ArgumentParser(description="Cel-shaded character runner (NanoBanana2Direct).")
    p.add_argument("--subject", required=True, help='Character concept, e.g. "shrine guardian"')
    p.add_argument("--category", required=True, choices=["hero", "enemy", "npc"],
                   help="hero=Shiba protagonist, enemy=magical monster, npc=anthropomorphic NPC")
    p.add_argument("--mode", choices=["single", "sheet"], default="single",
                   help="single character or 2x2 multi-pose sheet")
    p.add_argument("--reference", default=None,
                   help="Path to a style anchor image. Switches to Pattern A.")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--resolution", choices=["1K", "2K"], default="2K", help="Output resolution")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel calls (cost: N x ~$0.10)")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]

    # Aspect ratio: characters are typically taller than wide
    if args.mode == "single":
        aspect_ratio = "3:4"
    else:  # sheet
        aspect_ratio = "1:1"  # 2x2 grid reads square

    pattern = "A" if args.reference else "C"
    subject_slug = slugify(args.subject)
    base_prefix = f"characters/{args.category}/{subject_slug}_{args.mode}_pattern{pattern}"

    # Build prompts and workflows
    if args.variations == 1:
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            prompt_text = build_prompt_pattern_a(args.subject, args.category, args.mode)
            api_wf = build_workflow_pattern_a(prompt_text, base_prefix, seeds[0],
                                              aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a(prompt_text, base_prefix, seeds[0],
                                             aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.subject, args.category, args.mode)
            api_wf = build_workflow_pattern_c(prompt_text, base_prefix, seeds[0],
                                              aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c(prompt_text, base_prefix, seeds[0],
                                             aspect_ratio, args.resolution)
        base_filename = f"character_cel_shaded_{args.category}_{subject_slug}_{args.mode}_pattern{pattern}"
    else:
        variations = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            prompt_text = build_prompt_pattern_a(args.subject, args.category, args.mode)
            api_wf = build_workflow_pattern_a_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.subject, args.category, args.mode)
            api_wf = build_workflow_pattern_c_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution)
        base_filename = (f"character_cel_shaded_{args.category}_{subject_slug}_"
                         f"{args.mode}_pattern{pattern}_x{args.variations}")

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

    if args.variations == 1:
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"category={args.category} pattern={pattern} seed={seeds[0]}")
        print(f"output prefix: {base_prefix} (lands under ComfyUI/output/characters/{args.category}/)")
    else:
        cost = args.variations * 0.10
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"category={args.category} pattern={pattern} variations={args.variations}")
        print(f"seeds: {seeds}")
        print(f"estimated cost: ~${cost:.2f} ({args.variations} x ~$0.10)")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
