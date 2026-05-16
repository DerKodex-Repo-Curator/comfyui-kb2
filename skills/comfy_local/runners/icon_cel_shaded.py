#!/usr/bin/env python3
"""
Cel-shaded UI icon runner for Luis's the studio game.

Two modes:
  Pattern C (no reference, text-only):
    python3 runners/icon_cel_shaded.py --subject "treasure chest" --mode single
  Pattern A (with style anchor reference, recommended for matching existing sets):
    python3 runners/icon_cel_shaded.py --subject "treasure chest" --reference G:\\path\\anchor.png

Common args:
  --subject "<icon concept>"          required
  --mode {single,2x4,4x5}             default: single   (grids: Pattern C only)
  --reference <path>                  optional; switches to Pattern A
  --seed <int>                        optional; random 32-bit if omitted
  --resolution {1K,2K}                default: 2K
  --variations N                      default: 1; when N>1, the runner submits ONE
                                      workflow with N parallel NanoBanana2Direct
                                      calls, each with its own seed and SaveImage.
                                      Cost is N × ~$0.10 (each is an independent
                                      Google API call). Pattern is cloned from
                                      workflows/user_canonical_templates/
                                      "generate multiple cel sahded images.json"
                                      with NanoBanana2Direct substituted for
                                      GeminiNanoBanana2 (per ref 20 USER PREFERENCE).

Style lock is taken VERBATIM from references/18_example_house_style.md § "1. UI icons".
The "Avoid line" is appended verbatim. Both come straight from Luis's tuned wording.

Submits to /prompt and exits as soon as the workflow is accepted (no node_errors).
"""

from __future__ import annotations
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"


# --- Verbatim style lock (from references/18_example_house_style.md § 1. UI icons) ---
# DO NOT paraphrase. Luis tuned this wording across many iterations.

ICON_STYLE_LOCKS = """\
- Chunky simplified medieval fantasy RPG UI icon style
- Bold black outer outline
- 2D flat cel shading — EXACTLY 2 flat tones per material (base + shadow)
- NO gradients, NO soft blending, NO airbrush, NO texture grain, NO micro details
- Inner lines: 0 preferred, 1 maximum, must taper coin-style (thick → thin → disappears)
- 3/4 view with slight back tilt (top face plane slightly visible, bottom-right thickness larger than top)
- Top-left highlight, bottom-right shadow (consistent across set)
- Vibrant saturation — bold jewel tones; shadows must be saturated, never gray/muddy
- 2-4 large flat shapes only (extreme minimalism)
- Centered, oversized (~80-90% of cell), white background
- Object-only — NO people, NO faces, NO silhouettes, NO paws, NO text/numbers/letters
- Maximum 3 materials per icon"""

ICON_MATERIALS = (
    "Materials palette: forged metal, carved wood, stitched cloth, rope, wax seals, "
    "heraldry/crests, simple runes, gemstones/bone/horn (as flat shapes only)."
)

ICON_AVOID_LINE = (
    "Avoid gradients, soft shading, blending, airbrush, extra inner lines, extra markings, "
    "face tick marks, numbers, letters, engravings, texture lines, hatching, rivets, studs, "
    "gears, chains, straps, wings, horns, skulls, cracks, runes, emblem plates, extra "
    "attachments, background props, glow, particles, drop shadows, watermarks, muted colors, "
    "washed out colors, gray shadows, muddy shadows, low saturation."
)

ICON_GRID_LOCK = (
    "Grids are ONE single contact-sheet image with even spacing."
)

# Verbatim from workflows/user_canonical_templates/chonkify.json widget value.
# Single-call 2×3 contact sheet of CHONKY proportion variations of the same subject.
# Requires a reference image (image1). Designed for 4K resolution + aspect "auto".
CHONKIFY_MASTER_PROMPT = """\
front view all chonk

MASTER PROMPT (Image1 transform + Image2 render style, output 6 on one contact sheet, CHONKY proportion variations)

TASK
Transform image1 into a chunky chibi premium mobile game UI icon style. Use reference image2 as the render style guide (materials, shading logic, line quality, palette temperature). This is NOT a style transfer of image1. Rebuild the subject from scratch while preserving image1's identity. Output a single contact sheet containing six variations of the transformed subject, where the ONLY intentional difference across cells is the chonky proportion treatment.

OUTPUT STRUCTURE (ABSOLUTE — DO NOT DEVIATE)
Generate ONE IMAGE with a contact sheet layout
2 rows
3 icons per row
Even spacing
Each icon centered in its own cell
No overlap between cells
Consistent overall icon footprint across all six (same bounding box size)
All six are the same subject from image1, not different objects
Each cell must be a separate variation

BACKGROUND (MANDATORY)
Neutral mid-gray background
Flat, uniform color
No gradients
No textures
No lighting effects
No background shadows
Background must not influence shading or color perception

IDENTITY LOCK (FROM IMAGE1)
Preserve these from image1 across all six icons
Object category is unchanged
Key defining shapes and parts (do not remove essential features)
Signature silhouette cues that make it instantly identifiable
Overall pose/orientation if applicable
Do not introduce new props or unrelated elements

RENDER STYLE LOCK (FROM IMAGE2)
Use image2 as the strict reference for
Line weight hierarchy
Shading style and tone separation
Material language and finish (matte vs worn vs glossy)
Edge sharpness and manufactured feel
Overall stylization level (premium UI iconography, not illustration)

VIEW LOCK (ABSOLUTE — FRONT VIEW)
All six icons must share the exact same front-facing camera:
Straight-on front view (no 3/4, no yaw rotation)
Centered, symmetrical read where applicable
Minimal perspective distortion (iconic orthographic feel)
No variation in camera angle, rotation, tilt, or zoom between the six cells

CHUNKY CHIBI STYLE (NON-NEGOTIABLE)
Chunky, toy-like, squat proportions
Compressed forms, big readable masses
Strong silhouette readability at small size
Crisp geometry, engineered look, kit-built feel
Minimal interior detail
No sketchiness, no wobble
No painterly effects

CHONKY PROPORTION VARIATION SYSTEM (THE WHOLE POINT OF THIS SHEET)
Across the six cells, change ONLY these chonky proportion parameters while keeping identity and camera locked
Mass and thickness (overall "puffiness")
Bevel and rim thickness (edge robustness)
Feature scale ratios (big vs small parts) but never remove essential parts
Negative space openness (holes/gaps) while preserving recognizability
Corner roundness (blocky vs rounded) within the same object design
DO NOT add new design elements to create "variation" (no extra ornaments, decals, props)

SHADING RULES (HARD LIMITS)
Flat cel shading only
Exactly 2 tones per material region where possible
No gradients
No feathering
No airbrush
No realistic reflections
No glow

LINEWORK (ENGINEERED)
Outer silhouette thick and authoritative
Secondary separations thinner
Interior lines extremely thin or removed
If shading explains the form, remove the line
Clean stable curves, machined edges

THE SIX VARIATIONS (CHONKY PROPORTIONS ONLY, CONTROLLED)
All six must remain the same subject from image1, but each cell uses a different chonky proportion profile. Keep the same camera, same pose, same overall footprint, and same render style.

ROW 1 LEFT → RIGHT
1 Baseline chonk (faithful rebuild)
Match image1 proportions most closely, only simplified and premium-iconized

2 Chonk+
Increase thickness and mass by ~15–25%
Slightly larger primary forms, slightly thicker edges, slightly reduced tiny details

3 Chonk++
Increase thickness and mass by ~30–40%
More squat and toy-like, bolder bevels, fewer interior separations, stronger silhouette

ROW 2 LEFT → RIGHT
4 Short-chonk
Reduce overall height by ~10–20% while keeping the same footprint
Compress vertically, widen slightly if needed to keep volume
Thicker base, heavier lower mass, same essential negative spaces

5 Shorter-chonk
Reduce overall height by ~20–30% while keeping the same footprint
More "squat toy" feel, stacked thickness, simplified interior separations
Keep identity cues intact and readable

6 Mega-chonk (extreme but still same identity)
Maximum toy-like thickness and bevels without breaking recognizability
Largest readable masses, simplest interior detail, strongest "manufactured" kit-built feel

GLOBAL DO NOT
Do NOT use gradients
Do NOT add textures or noise
Do NOT add realism
Do NOT change the subject into something else
Do NOT change layout from 2×3
Do NOT crop icons
Do NOT add text, labels, frames, or UI panels unless image2 includes them explicitly
Do NOT change camera angle, rotation, tilt, or zoom between icons
Do NOT add variation via extra props, decorations, or new shapes not present in image1's identity

NEGATIVE PROMPT APPENDIX
Avoid
gradients
painterly shading
airbrushed highlights
specular shine
wobbly sketch lines
over-rendered micro detail
background shadows
extra props
text
inconsistent scale
inconsistent camera angles across cells
thin fragile edges
realistic material reflections

FINAL OUTPUT
One image
2×3 contact sheet
Six distinct chonky proportion variations of the same image1 subject
Rendered in the style of image2
Neutral flat gray background
No gradients anywhere
"""

# Pattern A canonical (from ref 20, kept VERBATIM as the conceptual seed),
# adapted for icon generation: image1 is replaced by the text subject, image2
# (the uploaded reference) provides the render style.
PATTERN_A_CANONICAL = (
    "transform the style of the image1. maintain the composition, scale and "
    "proportions of the orginal image1. use the reference image2 for render style"
)

DEFAULT_SYSTEM_PROMPT = (
    "You are an expert image-generation engine. You must ALWAYS produce an image.\n"
    "Interpret all user input—regardless of format, intent, or abstraction—as "
    "literal visual directives for image composition.\n"
    "If a prompt is conversational or lacks specific visual details, you must creatively "
    "invent a concrete visual scenario that depicts the concept.\n"
    "Prioritize generating the visual representation above any text, formatting, or "
    "conversational requests."
)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "icon"


def grid_clause(mode: str) -> str:
    if mode == "2x4":
        return (
            "Render exactly 8 icons total in a 2 columns × 4 rows grid contact sheet. "
            + ICON_GRID_LOCK
        )
    if mode == "4x5":
        return (
            "Render exactly 20 icons total in a 4 columns × 5 rows grid contact sheet. "
            + ICON_GRID_LOCK
        )
    return ""


def build_prompt_pattern_c(subject: str, mode: str) -> str:
    parts = [
        f"A {subject} as a chunky simplified medieval fantasy RPG UI icon.",
        "",
        "Style locks:",
        ICON_STYLE_LOCKS,
        "",
        ICON_MATERIALS,
    ]
    grid = grid_clause(mode)
    if grid:
        parts += ["", grid]
    parts += ["", ICON_AVOID_LINE]
    return "\n".join(parts)


def build_prompt_pattern_a(subject: str, mode: str) -> str:
    # Adapt PATTERN_A_CANONICAL: image1 -> the new icon subject (text), image2 -> the uploaded reference.
    if mode == "single":
        canonical_adapted = (
            f"Generate a {subject} as a new icon. "
            f"Maintain the composition, scale and proportions of a single centered icon. "
            f"Use the reference image2 (the uploaded image) for render style."
        )
    else:
        canonical_adapted = (
            f"Generate a contact sheet of {subject}-themed icons as new icons. "
            f"Maintain the composition, scale and proportions of single centered icons within each cell. "
            f"Use the reference image2 (the uploaded image) for render style — match its exact "
            f"line weight, palette, cel-shading approach, and outline treatment in every cell."
        )
    parts = [
        canonical_adapted,
        "",
        f"The subject is: a {subject}, rendered as a chunky simplified medieval fantasy RPG UI icon.",
        "",
        "Style locks:",
        ICON_STYLE_LOCKS,
        "",
        ICON_MATERIALS,
    ]
    grid = grid_clause(mode)
    if grid:
        parts += ["", grid]
    parts += ["", ICON_AVOID_LINE]
    return "\n".join(parts)


# ----- ComfyUI HTTP helpers -----

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
    """Best-effort POST to /open_workflow. Tolerates missing endpoint (custom node not installed)."""
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
            print("display: /open_workflow endpoint not found — restart ComfyUI to "
                  "pick up the comfy_load_workflow_endpoint custom node, or pass --no-display",
                  file=sys.stderr)
        else:
            body = e.read().decode("utf-8", errors="replace")
            print(f"display: HTTP {e.code} — {body}", file=sys.stderr)
    except Exception as e:
        print(f"display: failed ({e}) — pass --no-display to silence", file=sys.stderr)


def upload_image(path: Path) -> str:
    """POST to /upload/image, return the filename ComfyUI stored it under."""
    if not path.exists():
        print(f"reference image not found: {path}", file=sys.stderr)
        sys.exit(1)
    boundary = "----IconCelShadedRunnerBoundary"
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


# ----- API-format workflow builders -----

def build_workflow_pattern_c(prompt_text: str, prefix: str, seed: int,
                             aspect_ratio: str, resolution: str) -> dict:
    """Pattern C: PrimitiveStringMultiline -> NanoBanana2Direct -> SaveImage (3 nodes)."""
    return {
        "1": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose icon prompt"},
        },
        "2": {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["1", 0],
                "model": "Nano Banana 2 (Gemini 3.1 Flash Image)",
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "response_modalities": "IMAGE+TEXT",
                "thinking_level": "HIGH",
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "api_key": "",
            },
            "_meta": {"title": "Nano Banana 2 Direct (Google API Key)"},
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["2", 0],
            },
            "_meta": {"title": "Save Image"},
        },
    }


def build_workflow_pattern_a(prompt_text: str, prefix: str, seed: int,
                             aspect_ratio: str, resolution: str,
                             reference_filename: str) -> dict:
    """Pattern A: LoadImage(ref) -> NanoBanana2Direct(images) -> SaveImage (3 nodes)."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
            "_meta": {"title": "Style anchor reference"},
        },
        "2": {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": prompt_text,
                "model": "Nano Banana 2 (Gemini 3.1 Flash Image)",
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "response_modalities": "IMAGE+TEXT",
                "thinking_level": "HIGH",
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "api_key": "",
                "images": ["1", 0],
            },
            "_meta": {"title": "Nano Banana 2 Direct (Google API Key)"},
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["2", 0],
            },
            "_meta": {"title": "Save Image"},
        },
    }


# ----- N-parallel-variations builders (API format) -----
# Pattern cloned from workflows/user_canonical_templates/generate multiple cel sahded images.json
# (which uses GeminiNanoBanana2). Per ref 20 USER PREFERENCE we substitute NanoBanana2Direct.

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


def build_workflow_pattern_c_variations(prompt_text: str, base_prefix: str,
                                        variations: list[tuple[int, str]],
                                        aspect_ratio: str, resolution: str) -> dict:
    """Pattern C, N parallel calls.
    Nodes: "1" String, then for each variation a Gemini + SaveImage pair.
    `variations` is [(seed, prefix_for_this_variation), ...].
    """
    wf: dict = {
        "1": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose icon prompt (shared)"},
        },
    }
    next_id = 2
    for i, (seed, vprefix) in enumerate(variations):
        gid = str(next_id)
        sid = str(next_id + 1)
        wf[gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["1", 0],
                **_nb2direct_inputs_common(seed, aspect_ratio, resolution),
            },
            "_meta": {"title": f"Nano Banana 2 Direct — v{i+1:02d}"},
        }
        wf[sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": vprefix, "images": [gid, 0]},
            "_meta": {"title": f"Save Image — v{i+1:02d}"},
        }
        next_id += 2
    return wf


def build_workflow_pattern_a_variations(prompt_text: str, base_prefix: str,
                                        variations: list[tuple[int, str]],
                                        aspect_ratio: str, resolution: str,
                                        reference_filename: str) -> dict:
    """Pattern A, N parallel calls. Shared LoadImage + shared String, fanning out to N Gemini+SaveImage pairs."""
    wf: dict = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": reference_filename},
            "_meta": {"title": "Style anchor reference (shared)"},
        },
        "2": {
            "class_type": "PrimitiveStringMultiline",
            "inputs": {"value": prompt_text},
            "_meta": {"title": "Verbose icon prompt (shared)"},
        },
    }
    next_id = 3
    for i, (seed, vprefix) in enumerate(variations):
        gid = str(next_id)
        sid = str(next_id + 1)
        wf[gid] = {
            "class_type": "NanoBanana2Direct",
            "inputs": {
                "prompt": ["2", 0],
                **_nb2direct_inputs_common(seed, aspect_ratio, resolution),
                "images": ["1", 0],
            },
            "_meta": {"title": f"Nano Banana 2 Direct — v{i+1:02d}"},
        }
        wf[sid] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": vprefix, "images": [gid, 0]},
            "_meta": {"title": f"Save Image — v{i+1:02d}"},
        }
        next_id += 2
    return wf


# ----- Graph format builders (for drag-and-drop into ComfyUI canvas) -----
# Modeled directly on workflows/nano_banana_templates/pattern_a_style_transfer_workflow.json
# so the layout looks familiar when Luis opens the saved graph.

def _node_nb2direct_widgets(prompt_text_or_none, seed, aspect_ratio, resolution):
    # widgets_values order from /object_info input_order (with control_after_generate
    # injected after `seed`, matching the saved template exactly).
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


def build_graph_pattern_c(prompt_text: str, prefix: str, seed: int,
                          aspect_ratio: str, resolution: str) -> dict:
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
    links = [
        [1, 1, 0, 2, 0, "STRING"],
        [2, 2, 0, 3, 0, "IMAGE"],
    ]
    return _wrap_graph(nodes, links)


def build_graph_pattern_a(prompt_text: str, prefix: str, seed: int,
                          aspect_ratio: str, resolution: str,
                          reference_filename: str) -> dict:
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
            "widgets_values": [reference_filename, "image"],
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
    links = [
        [1, 1, 0, 2, 0, "IMAGE"],
        [2, 2, 0, 3, 0, "IMAGE"],
    ]
    return _wrap_graph(nodes, links)


def build_graph_pattern_c_variations(prompt_text: str,
                                     variations: list[tuple[int, str]],
                                     aspect_ratio: str, resolution: str) -> dict:
    """Graph format for N-parallel Pattern C. Lays out variations vertically in two columns
    (Gemini left, SaveImage right). Shared String node sits on the far left."""
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
    next_node_id = 2
    save_link_seq = 1000
    row_h = 520
    for i, (seed, vprefix) in enumerate(variations):
        prompt_link = i + 1
        gid = next_node_id
        sid = next_node_id + 1
        next_node_id += 2
        save_link = save_link_seq
        save_link_seq += 1
        y = -700 + i * row_h
        nodes.append({
            "id": gid, "type": "NanoBanana2Direct",
            "pos": [-1300, y], "size": [400, 497], "flags": {}, "order": i + 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": prompt_link, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": None},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [save_link], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(None, seed, aspect_ratio, resolution),
        })
        nodes.append({
            "id": sid, "type": "SaveImage",
            "pos": [-800, y], "size": [400, 400], "flags": {}, "order": i + 1 + len(variations), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": save_link}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [vprefix],
        })
        links.append([prompt_link, 1, 0, gid, 0, "STRING"])
        links.append([save_link, gid, 0, sid, 0, "IMAGE"])
    return _wrap_graph(nodes, links)


def build_graph_pattern_a_variations(prompt_text: str,
                                     variations: list[tuple[int, str]],
                                     aspect_ratio: str, resolution: str,
                                     reference_filename: str) -> dict:
    """Graph format for N-parallel Pattern A. Shared LoadImage + shared String on the left,
    N rows of (Gemini, SaveImage) to the right."""
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
            "widgets_values": [reference_filename, "image"],
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
    links = []
    next_node_id = 3
    save_link_seq = 2000
    row_h = 520
    for i, (seed, vprefix) in enumerate(variations):
        img_link = i + 1
        prompt_link = 1000 + i
        gid = next_node_id
        sid = next_node_id + 1
        next_node_id += 2
        save_link = save_link_seq
        save_link_seq += 1
        y = -700 + i * row_h
        nodes.append({
            "id": gid, "type": "NanoBanana2Direct",
            "pos": [-1300, y], "size": [400, 497], "flags": {}, "order": i + 1, "mode": 0,
            "inputs": [
                {"name": "prompt", "type": "STRING", "link": prompt_link, "widget": {"name": "prompt"}},
                {"name": "images", "shape": 7, "type": "IMAGE", "link": img_link},
                {"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None},
            ],
            "outputs": [
                {"name": "IMAGE", "type": "IMAGE", "links": [save_link], "slot_index": 0},
                {"name": "STRING", "type": "STRING", "links": None},
                {"name": "thought_image", "type": "IMAGE", "links": None},
            ],
            "properties": {"Node name for S&R": "NanoBanana2Direct"},
            "widgets_values": _node_nb2direct_widgets(None, seed, aspect_ratio, resolution),
        })
        nodes.append({
            "id": sid, "type": "SaveImage",
            "pos": [-800, y], "size": [400, 400], "flags": {}, "order": i + 1 + len(variations), "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": save_link}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveImage"},
            "widgets_values": [vprefix],
        })
        links.append([img_link, 1, 0, gid, 1, "IMAGE"])
        links.append([prompt_link, 2, 0, gid, 0, "STRING"])
        links.append([save_link, gid, 0, sid, 0, "IMAGE"])
    return _wrap_graph(nodes, links)


def _wrap_graph(nodes: list, links: list) -> dict:
    return {
        "id": "icon-cel-shaded",
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


# ----- Main -----

def main() -> None:
    p = argparse.ArgumentParser(
        description="Cel-shaded UI icon runner (NanoBanana2Direct).",
    )
    p.add_argument("--subject", required=True, help='Icon concept, e.g. "treasure chest"')
    p.add_argument("--mode", choices=["single", "2x4", "4x5", "chonk"], default="single",
                   help="single icon, 2x4/4x5 contact-sheet grid, or chonk "
                        "(2x3 chonkify proportion-variation sheet — requires --reference, forces 4K)")
    p.add_argument("--reference", default=None,
                   help="Path to a style anchor image. Switches to Pattern A.")
    p.add_argument("--seed", type=int, default=None,
                   help="32-bit seed; random if omitted. With --variations N>1, "
                        "seed sequence is S, S+1, ..., S+N-1.")
    p.add_argument("--resolution", choices=["1K", "2K"], default="2K",
                   help="Output resolution (default: 2K)")
    p.add_argument("--variations", type=int, default=1,
                   help="Number of parallel NanoBanana2Direct calls in one workflow "
                        "(default: 1). N>1 fans out to N independent generations, each "
                        "with its own seed and SaveImage. Cost is N × ~$0.10.")
    p.add_argument("--no-display", action="store_true",
                   help="Skip POST /open_workflow after submission. By default the "
                        "saved graph is pushed to your active ComfyUI canvas. Requires "
                        "the comfy_load_workflow_endpoint custom node.")
    args = p.parse_args()

    if args.variations < 1:
        print("--variations must be >= 1", file=sys.stderr)
        sys.exit(1)

    if args.mode == "chonk" and not args.reference:
        print("--mode chonk requires --reference (chonkify needs an image1 to transform)",
              file=sys.stderr)
        sys.exit(1)

    if args.mode == "chonk" and args.resolution != "4K":
        print(f"note: --mode chonk forces 4K resolution (canonical chonkify uses 4K).",
              file=sys.stderr)
        args.resolution = "4K"

    if args.variations > 1 and args.mode != "single":
        print("note: --variations with grid mode is unusual — each variation will be "
              "its own grid (N grids of icons). Continuing.", file=sys.stderr)

    base_seed = args.seed if args.seed is not None else random.randint(0, 2**31 - args.variations - 1)
    seeds = [base_seed + i for i in range(args.variations)]
    subject_slug = slugify(args.subject)
    if args.mode == "single":
        aspect_ratio = "1:1"
    elif args.mode == "chonk":
        aspect_ratio = "auto"
    else:
        aspect_ratio = "auto"

    pattern = "A" if args.reference else "C"
    base_prefix = f"icons/{subject_slug}_{args.mode}_pattern{pattern}"

    if args.variations == 1:
        single_prefix = base_prefix
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            if args.mode == "chonk":
                prompt_text = CHONKIFY_MASTER_PROMPT
            else:
                prompt_text = build_prompt_pattern_a(args.subject, args.mode)
            api_wf = build_workflow_pattern_a(prompt_text, single_prefix, seeds[0],
                                              aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a(prompt_text, single_prefix, seeds[0],
                                             aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.subject, args.mode)
            api_wf = build_workflow_pattern_c(prompt_text, single_prefix, seeds[0],
                                              aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c(prompt_text, single_prefix, seeds[0],
                                             aspect_ratio, args.resolution)
        base_filename = f"icon_cel_shaded_{subject_slug}_{args.mode}_pattern{pattern}"
    else:
        variations = [(seeds[i], f"{base_prefix}_v{i+1:02d}") for i in range(args.variations)]
        if args.reference:
            ref_path = Path(args.reference).expanduser().resolve()
            ref_filename = upload_image(ref_path)
            print(f"uploaded reference: {ref_path.name} -> {ref_filename}")
            if args.mode == "chonk":
                prompt_text = CHONKIFY_MASTER_PROMPT
            else:
                prompt_text = build_prompt_pattern_a(args.subject, args.mode)
            api_wf = build_workflow_pattern_a_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution, ref_filename)
            graph_wf = build_graph_pattern_a_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution, ref_filename)
        else:
            prompt_text = build_prompt_pattern_c(args.subject, args.mode)
            api_wf = build_workflow_pattern_c_variations(prompt_text, base_prefix, variations,
                                                        aspect_ratio, args.resolution)
            graph_wf = build_graph_pattern_c_variations(prompt_text, variations,
                                                       aspect_ratio, args.resolution)
        base_filename = f"icon_cel_shaded_{subject_slug}_{args.mode}_pattern{pattern}_x{args.variations}"

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
        print(f"submitted prompt_id={result.get('prompt_id')}  number={result.get('number')}  "
              f"pattern={pattern}  seed={seeds[0]}")
        print(f"output prefix: {base_prefix}  (lands under ComfyUI/output/icons/)")
    else:
        cost_estimate = args.variations * 0.10
        print(f"submitted prompt_id={result.get('prompt_id')}  number={result.get('number')}  "
              f"pattern={pattern}  variations={args.variations}")
        print(f"seeds: {seeds}")
        print(f"estimated cost: ~${cost_estimate:.2f} ({args.variations} × ~$0.10)")
        print(f"output prefixes: {base_prefix}_v01 .. {base_prefix}_v{args.variations:02d}")

    if not args.no_display:
        request_display(graph_path.resolve())


if __name__ == "__main__":
    main()
