---
name: icon_cel_shaded.py runner — full code anatomy
description: Patterns and design choices in the 948-line icon runner local Claude Code wrote. Reference template for future runners that submit Nano Banana / image-gen jobs with optional reference upload, N-parallel variations, and dual JSON emission.
type: reference
---

# icon_cel_shaded.py — full read, design notes

**File:** `runners/icon_cel_shaded.py` (948 lines)
**Authored by:** local Claude Code (during a parallel session)
**Read date:** 2026-05-09

This is currently the most sophisticated runner in the codebase. Future runners should match its structure unless there's a reason not to. This reference captures the patterns so I (and Claude Code) can reuse them.

## Capabilities at a glance

| CLI flag | Meaning |
|---|---|
| `--subject "..."` | required — icon concept text |
| `--mode {single,2x4,4x5,chonk}` | grid layout selector |
| `--reference <path>` | optional — switches to Pattern A (uploads + uses style anchor) |
| `--seed <int>` | optional — random 32-bit if omitted |
| `--resolution {1K,2K}` | output size, default 2K |
| `--variations N` | N-parallel calls in ONE workflow, each with own seed + SaveImage |
| `--no-display` | skip POST `/open_workflow` push to canvas |

## Three-mode dispatch (single / grid / chonk)

```
single  -> 1 icon       aspect_ratio=1:1
2x4     -> 8-icon sheet aspect_ratio=auto
4x5     -> 20-icon sheet aspect_ratio=auto
chonk   -> 2x3 chonkify proportion variations
           — REQUIRES --reference (no chonk without image1)
           — FORCES resolution=4K (canonical chonkify uses 4K)
           — Uses CHONKIFY_MASTER_PROMPT verbatim instead of build_prompt_*
```

The `chonk` mode is a special hybrid: Pattern A (uses reference) but with a verbatim master prompt cloned from `workflows/user_canonical_templates/chonkify.json`, NOT the assembled style-lock prompt.

## Pattern A vs Pattern C — the two API-format graphs

**Pattern C** (text-only, 3 nodes):

```
PrimitiveStringMultiline  -->  NanoBanana2Direct  -->  SaveImage
       (prompt)                   (no images input)
```

**Pattern A** (with reference image, 3 nodes):

```
LoadImage  -->  NanoBanana2Direct  -->  SaveImage
                  (images: [LoadImage, 0])
                  (prompt: literal string in widget, NOT wired)
```

Note the asymmetry: Pattern C wires the prompt through a `PrimitiveStringMultiline` node (so you can see/edit the prompt in the canvas as a separate node), while Pattern A puts the prompt directly into the NanoBanana2Direct widget. Reason: Pattern A's prompt is short ("transform the style of image1..."), Pattern C's prompt is the long verbose icon style-lock dump that benefits from a separate visible node.

## N-parallel-variations pattern (multi-output in ONE prompt submission)

When `--variations N`, the runner emits ONE workflow that contains:

- 1 shared input source (LoadImage for Pattern A; or just PrimitiveStringMultiline for Pattern C)
- 1 shared `PrimitiveStringMultiline` (the prompt — same for every variation)
- N pairs of `(NanoBanana2Direct, SaveImage)` rows, each with its own seed and `filename_prefix`

The shared upstream nodes have `outputs[i].links = [link_1, link_2, ..., link_N]` — fan-out. Each downstream pair takes one of those link IDs.

This is cloned from `workflows/user_canonical_templates/generate multiple cel sahded images.json` (the GeminiNanoBanana2 version), with the node class swapped to NanoBanana2Direct per the user preference in reference 20. It's **one** `/prompt` POST to ComfyUI but **N** independent Google API calls — cost is `N × ~$0.10`.

The runner prints:
```
estimated cost: ~$0.50 (5 × ~$0.10)
output prefixes: icons/treasure_chest_single_patternC_v01 .. _v05
```

## Dual JSON emission (always both formats)

Every run writes two files to `workflows/`:

```
icon_cel_shaded_<slug>_<mode>_pattern<A|C>[_xN]_workflow.json       (graph format)
icon_cel_shaded_<slug>_<mode>_pattern<A|C>[_xN]_workflow-api.json   (API format)
```

- Graph format = drag-and-drop into ComfyUI canvas. Has `nodes`, `links`, `groups`, `extra.ds`, `version`.
- API format = `/prompt` POST body. Flat dict keyed by node ID with `class_type` + `inputs` + `_meta.title`.

The API format is what's actually submitted; the graph format is what gets pushed to the canvas via `/open_workflow` for visualization.

## Auto-canvas-display via /open_workflow

After successful `/prompt` submission, the runner POSTs the absolute path of the saved graph JSON to `/open_workflow` (the `comfy_load_workflow_endpoint` custom node). The frontend JS swaps the canvas to that workflow.

Best-effort — tolerates missing endpoint with a clear stderr message:

```python
def request_display(graph_path: Path) -> None:
    ...
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("display: /open_workflow endpoint not found — restart ComfyUI ...
                   or pass --no-display", file=sys.stderr)
```

`--no-display` flag silences this entirely.

## Multipart image upload (no `requests` dependency)

`upload_image()` builds a multipart/form-data body manually with `urllib`:

```python
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
```

This keeps the runner stdlib-only (no `pip install requests`). Returns the filename ComfyUI stored it under (which goes into `LoadImage.inputs.image`).

## Style locks taken VERBATIM (no paraphrasing rule)

```python
# DO NOT paraphrase. Luis tuned this wording across many iterations.
ICON_STYLE_LOCKS = """\
- Chunky simplified medieval fantasy RPG UI icon style
- Bold black outer outline
- 2D flat cel shading — EXACTLY 2 flat tones per material (base + shadow)
...
```

The comment is intentional. Future runners must do the same — read the verbatim wording from `references/18_example_house_style.md` and the new `references/34_icon_prompt_templates.md` rather than rephrasing. Luis tuned this language; paraphrasing degrades adherence.

`ICON_AVOID_LINE` is the canonical avoid line from reference 34, also lifted verbatim.

`CHONKIFY_MASTER_PROMPT` is the entire 234-line chonkify spec lifted verbatim from `workflows/user_canonical_templates/chonkify.json` widget value.

## Graph-format details to copy (the painful bits)

### Widget values are an ordered list matching INPUT_TYPES insertion order

For `NanoBanana2Direct`:

```python
widgets_values = [
    prompt_text or "",
    "Nano Banana 2 (Gemini 3.1 Flash Image)",
    seed,
    "randomize",                  # control_after_generate, injected AFTER seed
    aspect_ratio,
    resolution,
    "IMAGE+TEXT",
    "HIGH",
    DEFAULT_SYSTEM_PROMPT,
    "",                           # api_key
]
```

The `control_after_generate` field is auto-injected by ComfyUI after any INT widget that has `"control_after_generate": True` in its INPUT_TYPES options. It does NOT appear in `INPUT_TYPES`, but it MUST appear in `widgets_values` after the corresponding INT. Forgetting this misaligns the rest of the list.

### Inputs that double as widgets

```python
{"name": "prompt", "type": "STRING", "link": 1, "widget": {"name": "prompt"}}
```

The `"widget": {"name": "prompt"}` marker says: "this input replaces the widget of the same name when wired." When `link` is non-null, the connection wins over the widget value.

### Optional inputs use shape: 7

```python
{"name": "images", "shape": 7, "type": "IMAGE", "link": None}
{"name": "files", "shape": 7, "type": "GEMINI_DIRECT_FILES", "link": None}
```

Required inputs omit `shape` (defaults to 0). `shape: 7` is the diamond-style optional socket.

### Link format

```python
[link_id, source_node_id, source_slot_index, target_node_id, target_slot_index, "TYPE_STRING"]
```

Six-element flat list, NOT a dict. The `TYPE_STRING` is informational — used by the UI to color the wire.

### `_wrap_graph()` adds the boilerplate every graph file needs

```python
{
    "id": "icon-cel-shaded",
    "revision": 0,
    "last_node_id": max_node_id,
    "last_link_id": max_link_id,
    "nodes": [...],
    "links": [...],
    "groups": [],
    "config": {},
    "extra": {"ds": {"scale": 0.85, "offset": [0, 0]}},
    "version": 0.4,
}
```

`extra.ds` controls the saved viewport zoom. `version: 0.4` is the current ComfyUI graph format version.

### Layout: manual XY positions in pixels

`pos: [x, y]` with negative origin coordinates (e.g. `[-1400, -700]`). The runner uses:

- `pos_x = -1400` (or further left for variation patterns) for the leftmost column
- 500 px column spacing
- `row_h = 520` for vertical spacing between variations

This produces a clean left-to-right flow that matches Luis's saved templates. **It does NOT use the section-rectangle convention** from `references/18_workflow_group_convention.md` (those are for diffusion-pipeline workflows; this runner produces a 3-node API-call graph that doesn't have Loaders/Conditioning/Sampling/Decode sections).

## Argparse defensive moves to copy

```python
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
```

Pattern: hard-fail on incompatibilities, soft-warn on unusual-but-valid combinations, silently auto-correct on canonical defaults.

## Submission and exit pattern

```python
result = http_post_json("/prompt", {"prompt": api_wf})
if result.get("node_errors"):
    print(f"REJECTED. node_errors:\n{json.dumps(result['node_errors'], indent=2)}", file=sys.stderr)
    sys.exit(3)

print(f"submitted prompt_id={result.get('prompt_id')} ...")
# (display push)
# exit
```

Submit, check `node_errors`, print the prompt_id, push to canvas, exit. **Don't poll**. The watcher daemon (`watcher.py`) handles output download. The runner is one-shot.

Exit codes: 0 = submitted, 1 = bad CLI args, 2 = ComfyUI unreachable, 3 = workflow rejected.

## Things this runner could improve (notes for future)

1. The graph-format `_wrap_graph()` always emits `groups: []` — no color-coded section rectangles. For diffusion-pipeline runners (Flux 2, Qwen, Z-Image), the convention from ref 18 (`build_groups()` in `_api_to_graph.py`) should be used. For API-call runners like this one, no groups is correct.

2. `aspect_ratio = "1:1"` for `single` is hardcoded. Future icon runners might want `--aspect-ratio` exposed for non-square icons (e.g. banners).

3. There's no explicit Z-Image / Qwen-Image fallback for users who don't want to spend the Nano Banana cost. A future iteration could accept `--backend {nano_banana,zimage,qwen}` and substitute the appropriate model loader nodes.

4. The chonk prompt `CHONKIFY_MASTER_PROMPT` is hardcoded inline. If Luis tweaks it (he iterates these often), it needs to be re-pasted. Consider reading it dynamically from `workflows/user_canonical_templates/chonkify.json` instead.

## Reuse checklist for future runners

When writing a new runner (e.g. `runners/character_cel_shaded.py`, `runners/biome_painterly.py`):

1. **Verbatim style locks** — read from `references/18`, `22`, `23`, `24`, `34` etc. and inline them as Python triple-quoted constants with a "DO NOT paraphrase" comment.
2. **Both formats emitted** — write `_workflow.json` (graph) and `_workflow-api.json` (API) to `workflows/`.
3. **Submit then exit** — `/prompt` POST, print prompt_id, optionally push to canvas via `/open_workflow`, exit. Never poll.
4. **N-variations support** — fan out from shared input nodes to N (NanoBanana2Direct + SaveImage) pairs. Use the same `[(seed, prefix), ...]` tuple pattern.
5. **Defensive argparse** — hard-fail incompatible flag combos, soft-warn on unusual ones.
6. **Multipart upload via stdlib urllib** — no `requests` dependency.
7. **Slug-based output prefixes** — `<asset_type>/<slug>_<mode>_pattern<A|C>[_vNN]` so the watcher's auto-download organizes cleanly.
8. **Tolerant `/open_workflow`** — best-effort with `--no-display` escape hatch.
