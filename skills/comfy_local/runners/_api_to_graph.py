#!/usr/bin/env python3
"""
Convert API-format workflow JSONs in workflows/ into graph (frontend) JSONs.

For each foo_workflow-api.json in workflows/, write foo_workflow.json that ComfyUI's
canvas can drag-drop. Follows references/10_workflow_json_format.md:
  - bidirectional links (target.inputs[].link AND source.outputs[].links[])
  - widgets_values matches the per-class declaration order in the reference table
  - control_after_generate widget injected after seed-style INT widgets (frontend behavior)
"""
from __future__ import annotations
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKFLOWS_DIR = HERE.parent / "workflows"
# ComfyUI's frontend lists workflows from user/default/workflows/ in the sidebar.
# Mirroring graphs there lets the user open them with one click on the canvas.
USER_WORKFLOWS_DIR = (HERE / ".." / ".." / ".." / ".." / "ComfyUI" / "user" / "default" / "workflows").resolve()
COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")

# Per-class metadata: connection inputs (typed sockets), widget order, outputs.
# Sourced from references/10_workflow_json_format.md and ComfyUI node sources.
NODE_META: dict[str, dict] = {
    "UNETLoader": {
        "inputs": [],
        "widgets": ["unet_name", "weight_dtype"],
        "outputs": [("MODEL", "MODEL")],
    },
    "CLIPLoader": {
        "inputs": [],
        "widgets": ["clip_name", "type", "device"],
        "outputs": [("CLIP", "CLIP")],
    },
    "DualCLIPLoader": {
        "inputs": [],
        "widgets": ["clip_name1", "clip_name2", "type", "device"],
        "outputs": [("CLIP", "CLIP")],
    },
    "VAELoader": {
        "inputs": [],
        "widgets": ["vae_name"],
        "outputs": [("VAE", "VAE")],
    },
    "CheckpointLoaderSimple": {
        "inputs": [],
        "widgets": ["ckpt_name"],
        "outputs": [("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")],
    },
    "CLIPTextEncode": {
        "inputs": [("clip", "CLIP")],
        "widgets": ["text"],
        "outputs": [("CONDITIONING", "CONDITIONING")],
    },
    "ConditioningZeroOut": {
        "inputs": [("conditioning", "CONDITIONING")],
        "widgets": [],
        "outputs": [("CONDITIONING", "CONDITIONING")],
    },
    "FluxGuidance": {
        "inputs": [("conditioning", "CONDITIONING")],
        "widgets": ["guidance"],
        "outputs": [("CONDITIONING", "CONDITIONING")],
    },
    "EmptyFlux2LatentImage": {
        "inputs": [],
        "widgets": ["width", "height", "batch_size"],
        "outputs": [("LATENT", "LATENT")],
    },
    "EmptyLatentImage": {
        "inputs": [],
        "widgets": ["width", "height", "batch_size"],
        "outputs": [("LATENT", "LATENT")],
    },
    "EmptySD3LatentImage": {
        "inputs": [],
        "widgets": ["width", "height", "batch_size"],
        "outputs": [("LATENT", "LATENT")],
    },
    "ModelSamplingAuraFlow": {
        "inputs": [("model", "MODEL")],
        "widgets": ["shift"],
        "outputs": [("MODEL", "MODEL")],
    },
    "KSampler": {
        "inputs": [("model", "MODEL"), ("positive", "CONDITIONING"),
                   ("negative", "CONDITIONING"), ("latent_image", "LATENT")],
        "widgets": ["seed", "control_after_generate", "steps", "cfg",
                    "sampler_name", "scheduler", "denoise"],
        "outputs": [("LATENT", "LATENT")],
    },
    "VAEDecode": {
        "inputs": [("samples", "LATENT"), ("vae", "VAE")],
        "widgets": [],
        "outputs": [("IMAGE", "IMAGE")],
    },
    "SaveImage": {
        "inputs": [("images", "IMAGE")],
        "widgets": ["filename_prefix"],
        "outputs": [],
    },
    "LoadImage": {
        "inputs": [],
        "widgets": ["image", "upload"],
        "outputs": [("IMAGE", "IMAGE"), ("MASK", "MASK")],
    },
    "TextEncodeQwenImageEditPlus": {
        # required: clip + prompt(widget); optional: vae, image1, image2, image3
        "inputs": [("clip", "CLIP"), ("vae", "VAE"),
                   ("image1", "IMAGE"), ("image2", "IMAGE"), ("image3", "IMAGE")],
        "widgets": ["prompt"],
        "outputs": [("CONDITIONING", "CONDITIONING")],
    },
    "LoraLoaderModelOnly": {
        "inputs": [("model", "MODEL")],
        "widgets": ["lora_name", "strength_model"],
        "outputs": [("MODEL", "MODEL")],
    },
    "FluxKontextImageScale": {
        "inputs": [("image", "IMAGE")],
        "widgets": [],
        "outputs": [("IMAGE", "IMAGE")],
    },
    "VAEEncode": {
        "inputs": [("pixels", "IMAGE"), ("vae", "VAE")],
        "widgets": [],
        "outputs": [("LATENT", "LATENT")],
    },
    "CFGNorm": {
        "inputs": [("model", "MODEL")],
        "widgets": ["strength"],
        "outputs": [("MODEL", "MODEL")],
    },
    "Flux2Scheduler": {
        "inputs": [],
        "widgets": ["steps", "width", "height"],
        "outputs": [("SIGMAS", "SIGMAS")],
    },
    "RandomNoise": {
        "inputs": [],
        "widgets": ["noise_seed", "control_after_generate"],
        "outputs": [("NOISE", "NOISE")],
    },
    "CFGGuider": {
        "inputs": [("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING")],
        "widgets": ["cfg"],
        "outputs": [("GUIDER", "GUIDER")],
    },
    "KSamplerSelect": {
        "inputs": [],
        "widgets": ["sampler_name"],
        "outputs": [("SAMPLER", "SAMPLER")],
    },
    "SamplerCustomAdvanced": {
        "inputs": [("noise", "NOISE"), ("guider", "GUIDER"), ("sampler", "SAMPLER"),
                   ("sigmas", "SIGMAS"), ("latent_image", "LATENT")],
        "widgets": [],
        "outputs": [("output", "LATENT"), ("denoised_output", "LATENT")],
    },
    "ReferenceLatent": {
        "inputs": [("conditioning", "CONDITIONING"), ("latent", "LATENT")],
        "widgets": [],
        "outputs": [("CONDITIONING", "CONDITIONING")],
    },
    "ImageScaleToTotalPixels": {
        "inputs": [("image", "IMAGE")],
        "widgets": ["upscale_method", "megapixels", "resolution_steps"],
        "outputs": [("IMAGE", "IMAGE")],
    },
}


def convert(api: dict) -> dict:
    # Stable order: integer node id ascending.
    ids_sorted = sorted(api.keys(), key=lambda k: int(k))
    str_to_int = {sid: int(sid) for sid in ids_sorted}

    nodes: list[dict] = []
    # Build skeleton nodes first so we can fill links on a second pass.
    for sid in ids_sorted:
        api_node = api[sid]
        cls = api_node["class_type"]
        if cls not in NODE_META:
            raise ValueError(f"NODE_META missing entry for class_type={cls!r}")
        meta = NODE_META[cls]
        api_inputs = api_node.get("inputs", {})

        node_inputs = []
        for name, t in meta["inputs"]:
            node_inputs.append({"name": name, "type": t, "link": None})

        widgets_values = []
        for w in meta["widgets"]:
            if w in api_inputs:
                widgets_values.append(api_inputs[w])
            else:
                # Frontend defaults for widgets that the API form omits.
                if w == "control_after_generate":
                    widgets_values.append("fixed")
                elif w == "device":
                    widgets_values.append("default")
                else:
                    widgets_values.append(None)

        node_outputs = []
        for name, t in meta["outputs"]:
            node_outputs.append({"name": name, "type": t, "links": [], "slot_index": 0})
        for i, o in enumerate(node_outputs):
            o["slot_index"] = i

        nodes.append({
            "id": str_to_int[sid],
            "type": cls,
            "pos": [0, 0],   # filled below
            "size": [340, 160],
            "flags": {},
            "order": str_to_int[sid],
            "mode": 0,
            "inputs": node_inputs,
            "outputs": node_outputs,
            "properties": {"Node name for S&R": cls},
            "widgets_values": widgets_values,
        })

    by_id: dict[int, dict] = {n["id"]: n for n in nodes}

    # Build links: walk every node's connection inputs in NODE_META order,
    # picking up [src_id, src_slot] tuples from the api_inputs dict.
    links: list[list] = []
    next_lid = 1
    for sid in ids_sorted:
        api_node = api[sid]
        cls = api_node["class_type"]
        meta = NODE_META[cls]
        api_inputs = api_node.get("inputs", {})
        tgt_id = str_to_int[sid]
        for tgt_slot, (name, t) in enumerate(meta["inputs"]):
            v = api_inputs.get(name)
            if not (isinstance(v, list) and len(v) == 2):
                continue
            src_sid, src_slot = v
            src_id = str_to_int[str(src_sid)] if not isinstance(src_sid, int) else src_sid
            src_slot = int(src_slot)
            src_node = by_id[src_id]
            if src_slot >= len(src_node["outputs"]):
                raise ValueError(f"node {sid} '{cls}' input '{name}' references invalid slot {src_slot} on node {src_id}")
            link_type = src_node["outputs"][src_slot]["type"]
            lid = next_lid
            next_lid += 1
            links.append([lid, src_id, src_slot, tgt_id, tgt_slot, link_type])
            # Bidirectional record:
            by_id[tgt_id]["inputs"][tgt_slot]["link"] = lid
            src_node["outputs"][src_slot]["links"].append(lid)

    # Lay out by column = max(topo-depth, section-min-col) so each section's
    # bounding rect stays in its own band of columns and groups don't overlap.
    cols: dict[int, int] = {}
    def get_col(nid: int) -> int:
        if nid in cols:
            return cols[nid]
        n = by_id[nid]
        sec = SECTION_OF.get(n["type"])
        parent_col = -1
        for inp in n["inputs"]:
            lid = inp.get("link")
            if lid is None:
                continue
            link = next(l for l in links if l[0] == lid)
            parent_col = max(parent_col, get_col(link[1]))
        c = max(parent_col + 1, SECTION_MIN_COL.get(sec, 0))
        cols[nid] = c
        return c
    for nid in by_id:
        get_col(nid)

    columns: dict[int, list[int]] = {}
    for nid, c in cols.items():
        columns.setdefault(c, []).append(nid)
    col_w, row_h = 360, 220
    for c, nids in columns.items():
        for i, nid in enumerate(sorted(nids)):
            by_id[nid]["pos"] = [c * col_w, i * row_h]

    groups = build_groups(nodes)

    return {
        "id": "auto-converted",
        "revision": 0,
        "last_node_id": max(by_id) if by_id else 0,
        "last_link_id": next_lid - 1,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {"ds": {"scale": 0.85, "offset": [0, 0]}},
        "version": 0.4,
    }


# Section assignment + colors. See references/35_workflow_group_convention.md.
SECTION_OF: dict[str, str] = {
    # Loaders (blue)
    "UNETLoader": "Loaders",
    "CLIPLoader": "Loaders",
    "DualCLIPLoader": "Loaders",
    "VAELoader": "Loaders",
    "CheckpointLoaderSimple": "Loaders",
    "LoadImage": "Loaders",
    "LoraLoaderModelOnly": "Loaders",
    "FluxKontextImageScale": "Loaders",
    # Conditioning (green)
    "CLIPTextEncode": "Conditioning",
    "ConditioningZeroOut": "Conditioning",
    "FluxGuidance": "Conditioning",
    "TextEncodeQwenImageEditPlus": "Conditioning",
    # Sampling (purple) -- latent setup, model-shift adjustments, sampler
    "EmptyLatentImage": "Sampling",
    "EmptySD3LatentImage": "Sampling",
    "EmptyFlux2LatentImage": "Sampling",
    "ModelSamplingAuraFlow": "Sampling",
    "KSampler": "Sampling",
    "SamplerCustomAdvanced": "Sampling",
    "VAEEncode": "Sampling",
    "CFGNorm": "Sampling",
    "Flux2Scheduler": "Sampling",
    "RandomNoise": "Sampling",
    "CFGGuider": "Sampling",
    "KSamplerSelect": "Sampling",
    "SamplerCustomAdvanced": "Sampling",
    "ReferenceLatent": "Conditioning",
    "ImageScaleToTotalPixels": "Loaders",
    # Decode + save (olive)
    "VAEDecode": "Decode",
    "SaveImage": "Decode",
}

SECTION_COLOR: dict[str, str] = {
    "Loaders":      "#3f789e",   # blue
    "Conditioning": "#5e8d56",   # green
    "Sampling":     "#a1309b",   # purple
    "Decode":       "#a59c4d",   # olive
}

SECTION_ORDER = ["Loaders", "Conditioning", "Sampling", "Decode"]

# Minimum column index per section -- spaces sections apart so their bounding
# rects don't overlap. Empty columns between sections are fine (visual gap).
SECTION_MIN_COL = {
    "Loaders":      0,
    "Conditioning": 1,
    "Sampling":     3,
    "Decode":       5,
}


def build_groups(nodes: list[dict]) -> list[dict]:
    """Compute one group rectangle per section that contains any nodes.
    Bounding rect = (min x, min y, width, height) with padding around member nodes.
    Title bar takes ~30 px above the topmost node so the group title is visible."""
    pad_x, pad_top, pad_bottom, pad_right = 20, 50, 20, 20
    by_section: dict[str, list[dict]] = {}
    for n in nodes:
        sec = SECTION_OF.get(n["type"])
        if sec:
            by_section.setdefault(sec, []).append(n)

    groups: list[dict] = []
    gid = 1
    for sec in SECTION_ORDER:
        members = by_section.get(sec, [])
        if not members:
            continue
        xs = [n["pos"][0] for n in members]
        ys = [n["pos"][1] for n in members]
        ws = [n["pos"][0] + n["size"][0] for n in members]
        hs = [n["pos"][1] + n["size"][1] for n in members]
        x = min(xs) - pad_x
        y = min(ys) - pad_top
        w = (max(ws) - min(xs)) + pad_x + pad_right
        h = (max(hs) - min(ys)) + pad_top + pad_bottom
        groups.append({
            "id": gid,
            "title": sec,
            "bounding": [x, y, w, h],
            "color": SECTION_COLOR[sec],
            "font_size": 24,
            "flags": {},
        })
        gid += 1
    return groups


def display_on_canvas(graph_path: Path) -> bool:
    """POST to /open_workflow (provided by the comfy_load_workflow_endpoint custom node).
    Pushes the graph onto the active ComfyUI canvas in the user's browser tab.
    Returns True on success, False if the endpoint is missing or unreachable."""
    payload = json.dumps({"path": str(graph_path)}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/open_workflow", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            r = json.loads(resp.read())
        print(f"  canvas: pushed {r.get('node_count')} nodes")
        return True
    except urllib.error.HTTPError as e:
        if e.code in (404, 405):
            print("  canvas: /open_workflow endpoint missing -- install/restart "
                  "comfy_load_workflow_endpoint to enable auto-display", file=sys.stderr)
        else:
            print(f"  canvas: HTTP {e.code} -- {e.read().decode('utf-8', errors='replace')}",
                  file=sys.stderr)
    except Exception as e:
        print(f"  canvas: failed ({e})", file=sys.stderr)
    return False


def install(workflow_api: dict, prefix: str, display: bool = True) -> tuple[Path, Path]:
    """Convert an API workflow dict to graph format, write it to BOTH:
      - workflows/<prefix>_workflow.json     (skill folder, audit trail)
      - <ComfyUI>/user/default/workflows/<prefix>.json  (sidebar -- one click to load)
    and (when display=True) push it onto the active canvas via /open_workflow.
    Returns (skill_path, user_path)."""
    graph = convert(workflow_api)
    blob = json.dumps(graph, indent=2)
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    skill_path = WORKFLOWS_DIR / f"{prefix}_workflow.json"
    skill_path.write_text(blob, encoding="utf-8")
    user_path = USER_WORKFLOWS_DIR / f"{prefix}.json"
    if USER_WORKFLOWS_DIR.is_dir():
        user_path.write_text(blob, encoding="utf-8")
    if display:
        display_on_canvas(skill_path.resolve())
    return skill_path, user_path


def main() -> None:
    api_files = sorted(WORKFLOWS_DIR.glob("*_workflow-api.json"))
    if not api_files:
        print(f"no *_workflow-api.json found under {WORKFLOWS_DIR}", file=sys.stderr)
        sys.exit(1)
    skipped = 0
    user_dir_ok = USER_WORKFLOWS_DIR.is_dir()
    for ap in api_files:
        graph_path = ap.parent / ap.name.replace("_workflow-api.json", "_workflow.json")
        api = json.loads(ap.read_text(encoding="utf-8"))
        try:
            graph = convert(api)
        except ValueError as e:
            print(f"  skip {ap.name:55s}  {e}", file=sys.stderr)
            skipped += 1
            continue
        blob = json.dumps(graph, indent=2)
        graph_path.write_text(blob, encoding="utf-8")
        installed = ""
        if user_dir_ok:
            prefix = ap.name.replace("_workflow-api.json", "")
            user_path = USER_WORKFLOWS_DIR / f"{prefix}.json"
            user_path.write_text(blob, encoding="utf-8")
            installed = f"  -> sidebar:{user_path.name}"
        n_nodes = len(graph["nodes"])
        n_links = len(graph["links"])
        print(f"  wrote {graph_path.name:55s}  nodes={n_nodes:2d}  links={n_links:2d}{installed}")
    if skipped:
        print(f"\n{skipped} workflow(s) skipped -- add the missing class to NODE_META if you need their graphs.", file=sys.stderr)
    if not user_dir_ok:
        print(f"\nUSER_WORKFLOWS_DIR not found ({USER_WORKFLOWS_DIR}); sidebar install skipped.", file=sys.stderr)


if __name__ == "__main__":
    main()
