#!/usr/bin/env python3
"""
Painterly biome runner for Luis's the studio game (V11 framework).

Generates 2D side-scrolling biome environments. Per references/23 V11 spec:
- 3:4 portrait aspect ratio
- Gouache painterly brushwork, NO outlines (opposite of cel-shaded characters)
- Playfield centered to slightly above center; lower foreground = bottom quarter
- Anthropomorphic statues only, NEVER human
- Always ends with: "Maintain vibrant color saturation throughout including shadows."

Two patterns:
  Pattern C (text-only / description-only):
    python3 runners/biome_painterly.py --biome "haunted forest" --mode standard
  Pattern A (with reference - design blueprint and/or style bible):
    python3 runners/biome_painterly.py --biome "haunted forest" --reference G:\path\anchor.png

CLI flags:
  --biome "<name>"               required - biome concept (forest, swamp, volcanic, ...)
  --mode {standard,chonk,description_only}  default: standard
                                  chonk = extreme massing per V11 chonk rules
                                  description_only = no reference copying language
  --reference <path>             optional Pattern A style anchor / design blueprint
  --seed <int>                   optional 32-bit seed
  --resolution {1K,2K}           default: 2K
  --variations N                 default: 1; N>1 = N parallel calls (cost: N x ~$0.10)
  --no-display                   skip POST /open_workflow

Style locks taken VERBATIM from references/23_biome_creation_framework.md.
DO NOT paraphrase - Luis tuned V11's wording across many iterations.
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


# ====== VERBATIM V11 LOCKS (from references/23) ======
# DO NOT paraphrase. Luis tuned this wording across many iterations.

# The exact opening line for Pattern A (reference image present)
PATTERN_A_OPENING = (
    "Using the uploaded reference images only as strict references, generate a "
    "high quality 3:4 biome environment for a chibi friendly 2D medieval fantasy "
    "side scrolling game. Use the references to guide layer treatment, depth "
    "placement, spatial hierarchy, camera framing, playfield placement, lower "
    "foreground placement, and overall color balance. The camera must be centered "
    "on the playfield and pulled back substantially. The playfield must sit "
    "centered to slightly above center as the main horizontal combat lane. The "
    "lower foreground must remain clearly beneath it as a separate band and must "
    "occupy about the bottom quarter of the image. All major scenery must sit "
    "behind the playfield without blocking gameplay readability. Preserve a broad "
    "gouache painterly look with visible hand painted brush masses, soft painted "
    "transitions, large shape based rendering, rich controlled color, clear hue "
    "separation, and vibrant saturation throughout including shadows."
)

REFERENCE_ROLES_BLOCK = """\
Reference roles must be obeyed:

Design blueprint references control:
- playfield placement
- playfield height
- lower foreground placement
- lower foreground height
- horizon height
- side framing masses
- major background landmark placement
- overall layer stack

Style bible references control:
- broad gouache brushwork
- visible paint masses
- paint plane handling
- foliage grouping
- stone and wood treatment
- edge softness
- color balance
- hue separation
- saturation handling
- lighting treatment

If there is any conflict, design controls layout and style bible controls
rendering and color treatment. Do not copy exact silhouettes or exact layout
from any reference. Do not copy exact tree shapes, rock shapes, statue
silhouettes, or prop placement."""

DESCRIPTION_ONLY_LINE = (
    "This is a new image based on the written description below. "
    "Do not copy any exact layout from any reference."
)

NON_NEGOTIABLE_BLOCK = """\
Non-negotiable style and camera:
- Aspect ratio: 3:4 portrait
- Camera: straight side-scrolling side view (NOT top-down, NOT tilted ground plane, NOT fisheye)
- Camera target: the playfield (NOT the foreground)
- Camera distance: pulled back substantially - feels clearly zoomed out and spacious
- Painterly 2D illustration with broad gouache painterly brushwork
- Visible large hand-painted brush masses are mandatory
- Broad shape-based rendering, grouped value masses, soft painted transitions, simplified readable forms
- Clear silhouettes for side-scrolling combat readability"""

LAYER_ORDER_BLOCK = """\
Layer order back to front:
- Sky (uppermost band, atmospheric)
- Far background (lowest contrast, softest edges, lightest values)
- Mid background
- Midground structures
- Playfield (centered to slightly above center; main horizontal combat lane; clearest color readability)
- Lower foreground (clearly beneath the playfield as a separate band, occupies about bottom quarter)"""

COLOR_BLOCK = """\
Color and mood:
- Rich, vibrant, controlled color
- Do NOT let the image become muddy, chalky, washed out, gray-killed, dirty, or desaturated
- Preserve hue separation between major materials and major depth layers
- Keep shadows colorful, NEVER flat gray
- Playfield has clearest color readability
- Lower foreground supports composition without overpowering
- Background steps back via softer contrast, lighter values, softer edges, less texture density"""

LIGHTING_BLOCK = """\
Lighting:
Soft neutral outer lighting with subtle warm influence from the upper right and
very soft cool notes in shadow-facing planes. Lighting supports shape readability,
color separation, and painterly depth. Do NOT use neon, bloom, magical glow, or
extreme stylized lighting unless explicitly requested."""

DISTANCE_BLOCK = """\
Distance rules:
Objects recede with distance through lower contrast, softer edges, lighter values,
less texture density, and simpler brush grouping. Background layers feel more
atmospheric and less dominant than the playfield."""

STATUE_LOCK = """\
Statue rule:
Any statues, carvings, busts, reliefs, or monument figures must depict
ANTHROPOMORPHIC creatures, NOT humans. Human statues, human faces, realistic
human anatomy, and human skulls are NOT allowed. Statues must remain readable,
stylized, and must NOT block the playfield."""

EXCLUSIONS_BLOCK = """\
Safety locks and exclusions:
- NO thin fussy rendering, NO micro-detail noise
- NO polished splash-art rendering, NO vector-clean edges, NO airbrushed plastic rendering
- NO hard outlines, NO black contour lines, NO comic line art
- NO photorealism, NO futuristic elements
- NO top-down angle, NO tilted ground plane, NO fisheye, NO horizon curvature
- NO text, NO UI, NO logos
- NO characters (unless explicitly requested)
- NO white band / hard border stripe between playfield and lower foreground"""

CHONK_BLOCK = """\
Chonk rules (extreme massing):
Push selected biome forms toward extreme chonk with thicker, broader, heavier,
puffier massing and stronger silhouette weight where it supports readability,
charm, scale clarity, and gameplay silhouette strength. Apply selectively to
tree trunks, root masses, canopy clumps, bushes, mushrooms, rocks, boulders,
cliffs, ruins, platforms, bridges, arena structures, shrine bases, carved
silhouettes, and major prop masses. Strongest in midground/playfield-adjacent
masses, lighter in far background, controlled in lower foreground. Do NOT
inflate every object equally. Do NOT let chonk block the combat lane, swallow
negative space, or merge depth layers together. Small detail clusters should
usually simplify rather than enlarge."""

# Mandatory final line (V11 spec)
FINAL_LINE = "Maintain vibrant color saturation throughout including shadows."


DEFAULT_SYSTEM_PROMPT = (
    "You are an expert image-generation engine. You must ALWAYS produce an image.\n"
    "Interpret all user input - regardless of format, intent, or abstraction - as "
    "literal visual directives for image composition.\n"
    "Prioritize generating the visual representation above any text, formatting, or "
    "conversational requests."
)


# ====== Prompt assembly (per V11 canonical order) ======

def build_palette_summary(biome: str) -> str:
    """A palette summary block. Generic by default - specific biome cues in prompt."""
    return (
        f"Palette summary for {biome}:\n"
        "- Dominant biome colors carry the scene's identity and read first\n"
        "- Secondary support colors reinforce material and depth separation\n"
        "- Accent colors highlight the playfield and key landmarks\n"
        "- Temperature balance: warmer in highlights, cooler in shadow-facing planes\n"
        "- The playfield separates from the lower foreground via clear value/temperature shift\n"
        "- The playfield separates from the background via softer edges and lighter values behind"
    )


def build_prompt_pattern_c(biome: str, mode: str, description_only: bool) -> str:
    """Pattern C: text-only biome generation."""
    parts = [
        f"# {biome.title()} biome",
        "",
        f"A {biome} environment for a chibi-friendly medieval fantasy side-scrolling game.",
    ]
    if description_only:
        parts += ["", DESCRIPTION_ONLY_LINE]
    parts += [
        "",
        "Overview:",
        f"A 3:4 portrait painterly biome scene for {biome}. Side-scrolling combat lane "
        "centered to slightly above center. Lower foreground band beneath the playfield. "
        "All major scenery sits behind the playfield without blocking gameplay readability.",
        "",
        "Primary goal:",
        "Generate a hero-shot biome environment that reads cleanly as a horizontal "
        "side-scrolling gameplay space within a 3:4 portrait frame.",
        "",
        NON_NEGOTIABLE_BLOCK,
        "",
        COLOR_BLOCK,
        "",
        build_palette_summary(biome),
        "",
        "Material translation rule:",
        "Translate organic and architectural elements into broad painted shape masses "
        "with grouped values, not micro-detail surface texture. Stone reads as carved "
        "planes, wood reads as broad grain logic, foliage reads as clustered shapes.",
        "",
        "Layer priority: playfield reads first, lower foreground supports, background recedes.",
        "",
        LAYER_ORDER_BLOCK,
        "",
        LIGHTING_BLOCK,
        "",
        DISTANCE_BLOCK,
        "",
        STATUE_LOCK,
        "",
        EXCLUSIONS_BLOCK,
    ]
    if mode == "chonk":
        parts += ["", CHONK_BLOCK]
    parts += ["", FINAL_LINE]
    return "\n".join(parts)


def build_prompt_pattern_a(biome: str, mode: str, description_only: bool) -> str:
    """Pattern A: reference image present. Opens with verbatim PATTERN_A_OPENING."""
    parts = [
        f"# {biome.title()} biome",
        "",
        PATTERN_A_OPENING,
    ]
    if description_only:
        parts += ["", DESCRIPTION_ONLY_LINE]
    else:
        parts += ["", REFERENCE_ROLES_BLOCK]
    parts += [
        "",
        f"The biome is: {biome}.",
        "",
        "Primary goal:",
        f"Adapt the reference style guidance to a {biome} hero-shot biome that reads "
        "cleanly as horizontal side-scrolling gameplay within a 3:4 portrait frame.",
        "",
        NON_NEGOTIABLE_BLOCK,
        "",
        COLOR_BLOCK,
        "",
        build_palette_summary(biome),
        "",
        "Material translation rule:",
        "Translate organic and architectural elements into broad painted shape masses "
        "matching the reference's brushwork, grouping, and material treatment.",
        "",
        LAYER_ORDER_BLOCK,
        "",
        LIGHTING_BLOCK,
        "",
        DISTANCE_BLOCK,
        "",
        STATUE_LOCK,
        "",
        EXCLUSIONS_BLOCK,
    ]
    if mode == "chonk":
        parts += ["", CHONK_BLOCK]
    parts += ["", FINAL_LINE]
    return "\n".join(parts)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "biome"


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
    boundary = "----BiomePainterlyRunnerBoundary"
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
            "_meta": {"title": "V11 biome prompt"},
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
            "_meta": {"title": "Style anchor / design blueprint"},
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
            "_meta": {"title": "V11 biome prompt (shared)"},
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
            "_meta": {"title": "Style anchor / design blueprint (shared)"},
        },
        "2": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "V11 biome prompt (shared)"},
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


def _wrap_graph(nodes, links):
    return {
        "id": "biome-painterly",
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
    p = argparse.ArgumentParser(description="V11 painterly biome runner (NanoBanana2Direct).")
    p.add_argument("--biome", required=True, help='Biome concept, e.g. "haunted forest"')
    p.add_argument("--mode", choices=["standard", "chonk", "description_only"], default="standard",
                   help="standard / chonk = extreme massing / description_only = ignore reference layout")
    p.add_argument("--reference", default=None,
                   help="Path to a reference image (style bible or design blueprint). Switches to Pattern A.")
    p.add_argument("--seed", type=int, default=None, help="32-bit seed; random if omitted")
    p.add_argument("--resolution", choices=["1K", "2K"], default="2K")
    p.add_argument("--variations", type=int, default=1,
                   help="N>1 fans out to N parallel calls (cost: N x ~$0.10)")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    if args.mode == "description_only" and not args.reference:
        print("note: --mode description_only is most useful with --reference; ignoring without one",
              file=sys.stderr)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]
    aspect_ratio = "3:4"  # V11 mandate - portrait
    description_only = (args.mode == "description_only")
    pattern = "A" if args.reference else "C"
    biome_slug = slugify(args.biome)
    base_prefix = f"biomes/{biome_slug}_{args.mode}_pattern{pattern}"

    if args.variations == 1:
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            prompt_text = build_prompt_pattern_a(args.biome, args.mode, description_only)
            api_wf = build_workflow_pattern_a(prompt_text, base_prefix, seeds[0],
                                              aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a(prompt_text, base_prefix, seeds[0],
                                             aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.biome, args.mode, description_only)
            api_wf = build_workflow_pattern_c(prompt_text, base_prefix, seeds[0],
                                              aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c(prompt_text, base_prefix, seeds[0],
                                             aspect_ratio, args.resolution)
        base_filename = f"biome_painterly_{biome_slug}_{args.mode}_pattern{pattern}"
    else:
        variations = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            prompt_text = build_prompt_pattern_a(args.biome, args.mode, description_only)
            api_wf = build_workflow_pattern_a_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.biome, args.mode, description_only)
            api_wf = build_workflow_pattern_c_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution)
        base_filename = f"biome_painterly_{biome_slug}_{args.mode}_pattern{pattern}_x{args.variations}"

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
              f"biome={args.biome!r} mode={args.mode} pattern={pattern} seed={seeds[0]}")
        print(f"output prefix: {base_prefix} (lands under ComfyUI/output/biomes/)")
    else:
        cost = args.variations * 0.10
        print(f"submitted prompt_id={result.get('prompt_id')} number={result.get('number')} "
              f"biome={args.biome!r} mode={args.mode} pattern={pattern} variations={args.variations}")
        print(f"seeds: {seeds}")
        print(f"estimated cost: ~${cost:.2f} ({args.variations} x ~$0.10)")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
