---
name: Hooks + subgraphs — model patching schedules and authored reusable subassemblies
description: Two relatively new ComfyUI features. Hooks = scheduled LoRAs / model patches with timestep-based keyframes. Subgraphs = reusable named subassemblies (38 official "blueprints" ship with ComfyUI). Source: comfy_extras/nodes_hooks.py + app/subgraph_manager.py + blueprints/*.json.
type: reference
---

# Hooks + subgraphs

Both are EXPERIMENTAL-flagged but already used in real workflows. Hooks add timestep-scheduled LoRAs / model patches. Subgraphs are reusable named subassemblies — the modern ComfyUI way to keep large workflows manageable.

**Sources read (2026-05-09):**
- `comfy_extras/nodes_hooks.py` (750 lines)
- `app/subgraph_manager.py` (132 lines)
- `blueprints/*.json` (38 official subgraph blueprints)

---

## Part 1: Hooks

### What hooks do (in plain English)

A **hook** is a "patch" attached to a model or conditioning that gets applied during sampling — but only when certain conditions are met. The two main use cases:

1. **Timestep-scheduled LoRA strength.** Apply a LoRA at strength=1.0 from step 0–10, then ramp down to 0.3 from step 10–25. (You can't do this with stacked LoRA Loaders — they're flat throughout sampling.)
2. **Conditioning region + hook combinations.** Apply a different prompt's conditioning + a different LoRA combo to a masked region during a specific step range.

### The wire types

| Type | What it carries |
|---|---|
| `HOOKS` | A `HookGroup` — list of hook entries (LoRA, model-as-lora, etc.) attached to conditioning |
| `HOOK_KEYFRAMES` | A `HookKeyframeGroup` — list of (timestep_percent, strength_multiplier) pairs |
| `TIMESTEPS_RANGE` | A `(start_percent, end_percent)` tuple for slicing when hooks apply |

### Hook creator nodes (advanced/hooks/create)

- **`CreateHookLora`** — load a LoRA file as a hook. Outputs `HOOKS`. Optional `prev_hooks` chains additional LoRAs into the same group. Strength range is wider (`-20..+20`) than regular LoraLoader.
- **`CreateHookLoraModelOnly`** — same, U-Net only (no CLIP-side LoRA). For distilled-model LoRAs.
- **`CreateHookModelAsLora`** — diff a checkpoint against the base model and use the diff as a LoRA-style hook. Treat any checkpoint as a LoRA.
- **`CreateHookModelAsLoraModelOnly`** — same, U-Net only.

### Hook scheduling nodes (advanced/hooks/scheduling)

- **`CreateHookKeyframe`** — one keyframe: `(start_percent, strength_mult)`. Chain via `prev_hook_kf`.
- **`CreateHookKeyframesInterpolated`** — bulk-generate N keyframes between `(strength_start, start_percent)` and `(strength_end, end_percent)` using one of `comfy.hooks.InterpolationMethod` modes (linear, ease-in, ease-out, etc.). `keyframes_count` controls density.
- **`CreateHookKeyframesFromFloats`** — generate keyframes from a list of floats (for arbitrary curves).
- **`SetHookKeyframes`** — attach a `HOOK_KEYFRAMES` to a `HOOKS` group, scheduling the strengths.

### Hook combining nodes

- **`CombineHooks`** (alias `CombineHooks2`) — merge 2 hook groups
- **`CombineHooksFour`** — merge 4
- **`CombineHooksEight`** — merge 8

### Applying hooks to conditioning

This is the bridge from hooks → KSampler. The naming is "set props":

- **`ConditioningSetProperties`** — single conditioning + hooks/mask/timesteps. Returns one CONDITIONING. Category: `advanced/hooks/cond single`.
- **`PairConditioningSetProperties`** — same but for positive+negative pair. Returns `(positive, negative)`. Category: `advanced/hooks/cond pair`.
- **`ConditioningSetPropertiesAndCombine`** — same as Set, but ALSO concatenates with an existing conditioning so you keep the original in addition to the new one.
- **`PairConditioningSetPropertiesAndCombine`** — pair version of above.
- **`PairConditioningCombine`** — combine two pre-existing positive+negative pairs into one merged pair.
- **`PairConditioningSetDefaultAndCombine`** — designate the new conds as "defaults" (apply where the originals don't have a hook) and combine.

Each of these has optional `mask`, `hooks`, `timesteps` inputs. Strength scales the conditioning; `set_cond_area` is `default` (whole image) or `mask bounds` (just the masked region).

### Applying hooks to CLIP (early embedding)

- **`SetClipHooks`** — apply hooks to the CLIP encoder before tokenizing. Two booleans: `apply_to_conds` (hooks attach to the resulting conditioning), `schedule_clip` (run CLIP through scheduling — affects re-encode behavior).

### Canonical hook pipeline

```
CreateHookLora(some_lora.safetensors, strength_model=1.0, strength_clip=1.0)
  -> HOOKS

CreateHookKeyframesInterpolated(start=1.0, end=0.3, keyframes_count=10)
  -> HOOK_KEYFRAMES

SetHookKeyframes(HOOKS, HOOK_KF)
  -> HOOKS (now with schedule attached)

CLIPTextEncode("prompt") -> CONDITIONING

ConditioningSetProperties(CONDITIONING, strength=1.0,
                          set_cond_area="default",
                          hooks=HOOKS_with_schedule)
  -> CONDITIONING (now hook-aware)

KSampler(... positive=hook_aware_conditioning ...)
```

The KSampler doesn't need to know about hooks specifically — they're carried inside the CONDITIONING dict's metadata and consumed by `comfy.sample.sample()` internally.

### When to reach for hooks vs. regular LoRA loaders

Use plain `LoraLoader` when:
- LoRA strength is constant throughout sampling
- You're stacking multiple LoRAs at flat strengths
- Simplicity matters

Use hooks when:
- You need timestep-scheduled strength (e.g., "style LoRA at 1.0 early, fade to 0.0 by midway")
- You need region-masked LoRA application
- You're combining LoRAs differently per region of the image
- You need to swap LoRAs at a specific step

### Style/texture LoRAs vs character LoRAs

A common pattern is to use scheduled hooks for STYLE LoRAs (front-load them so they shape composition then fade out) while keeping CHARACTER LoRAs at flat strength via regular LoraLoader. Hooks let you do this in the same workflow without having to render separately and composite.

### LoRA Block Weight relationship

Inspire-Pack's `Lora Block Weight` (reference 38) is per-U-Net-block strength control. Hooks are per-timestep strength control. They're orthogonal: you can use both — Lora Block Weight at fixed strength=1.0, then schedule that strength to scale via hooks.

---

## Part 2: Subgraphs

### What a subgraph is

A reusable named subassembly of nodes. Drop one "subgraph instance" node into your workflow; internally it's a small graph with its own nodes, links, and IO ports. Authored once, instanced many times.

### Two sources of subgraphs

`SubgraphManager.get_all_subgraphs()` aggregates from two locations:

1. **Custom node subgraphs** — `<custom_node_dir>/subgraphs/*.json`. Custom node packs ship subgraphs the user can drag into a workflow.
2. **Blueprint subgraphs** — `ComfyUI/blueprints/*.json`. 38 official ones ship with the install.

Both go through the same loader and end up in the same `/global_subgraphs` REST endpoint. The frontend node-search picker lists all of them.

### REST endpoints

```
GET /global_subgraphs        — list all subgraphs (id + name + source + node_pack)
GET /global_subgraphs/{id}   — fetch full subgraph data (the .json content)
```

IDs are `sha256(source + path)` so they're stable across reloads.

### The 38 official blueprints (in `ComfyUI/blueprints/`)

Image processing primitives:
- Brightness and Contrast, Chromatic Aberration, Color Adjustment, Color Balance, Color Curves, Edge-Preserving Blur, Film Grain, Glow, Hue and Saturation, Image Blur, Image Channels, Image Levels, Sharpen, Unsharp Mask

Generation pipelines (named with their model):
- Text to Image (Z-Image-Turbo)
- Image Edit (Flux.2 Klein 4B)
- Image Edit (Qwen 2511) ← multi-person consistency
- Image Inpainting (Qwen-image)
- Image Outpainting (Qwen-Image)
- Image Upscale (Z-Image-Turbo)
- Image to Layers (Qwen-Image Layered) ← RGBA decomposition
- Image to Model (Hunyuan3d 2.1)

ControlNet conversions (Z-Image-Turbo specifically uses model_patches):
- Canny to Image (Z-Image-Turbo)
- Depth to Image (Z-Image-Turbo)
- Pose to Image (Z-Image-Turbo)

Video pipelines:
- Image to Video (Wan 2.2), Text to Video (Wan 2.2)
- Canny to Video (LTX 2.0), Depth to Video (LTX 2.0), Pose to Video (LTX 2.0)
- Video Inpaint (Wan2.1 VACE)
- Video Stitch, Video Upscale (GAN x4)

Other:
- Image to Depth Map (Lotus)
- Image Captioning (gemini), Video Captioning (Gemini), Prompt Enhance
- Text to Audio (ACE-Step 1.5)

These are the canonical "do this thing the right way" reference subgraphs. **When Luis asks for any of these, drop the matching blueprint into the workflow** — it's the official Comfy-Org blessed pipeline.

### Subgraph file format

A subgraph JSON has the SAME top-level shape as a regular workflow (`nodes`, `links`, `version: 0.4`), but with one critical addition: a `definitions.subgraphs[]` array containing the actual subgraph internals.

**Top-level instance node** (just one node, looking like a black-box from outside):

```json
{
  "id": 140,
  "type": "916dff42-6166-4d45-b028-04eaf69fbb35",  // <- UUID = subgraph definition id
  "pos": [500, 1440],
  "size": [250, 178],
  "inputs": [
    {
      "label": "image",
      "localized_name": "images.image0",
      "name": "images.image0",
      "type": "IMAGE",
      "link": null
    }
  ],
  "outputs": [
    {
      "label": "IMAGE",
      "localized_name": "IMAGE0",
      "name": "IMAGE0",
      "type": "IMAGE",
      "links": []
    }
  ],
  "properties": {
    "proxyWidgets": [
      ["4", "value"],   // <- expose internal node 4's "value" widget
      ["5", "value"]    // <- and node 5's "value" widget
    ]
  },
  "widgets_values": [],
  "title": "Brightness and Contrast"
}
```

**Subgraph definition** (in `definitions.subgraphs[]`):

```json
{
  "id": "916dff42-6166-4d45-b028-04eaf69fbb35",
  "version": 1,
  "state": {
    "lastGroupId": 0,
    "lastNodeId": 143,
    "lastLinkId": 118,
    "lastRerouteId": 0
  },
  "revision": 0,
  "config": {},
  "name": "Brightness and Contrast",
  "inputNode": {
    "id": -10,                    // <- magic ID for the input port
    "bounding": [360, -176, 120, 60]
  },
  "outputNode": {
    "id": -20,                    // <- magic ID for the output port
    ...
  },
  "nodes": [...],   // <- the internal nodes
  "links": [...]    // <- internal links
}
```

### How to author a subgraph (frontend workflow)

1. Build the desired subassembly as a regular set of nodes
2. Select all of them
3. Right-click → "Convert to Subgraph" (or hotkey)
4. The frontend creates the subgraph definition, replaces the selection with an instance node, and prompts you for input/output port names
5. To expose a widget, add the internal node's widget to `proxyWidgets`

### How to use a blueprint subgraph

In the canvas: press `n` (node search) → start typing the blueprint name → hit Enter. The frontend fetches the blueprint via `/global_subgraphs/{id}` and inserts an instance.

### Why this matters for runner authoring

For now, runners build ALL nodes inline (no subgraphs). That's correct for headless API submission — `/prompt` POST doesn't accept subgraph instances directly; it expects the flattened API format.

But for the GRAPH format that runners also emit (so Luis can drag the saved `_workflow.json` into the canvas), we COULD use subgraphs to keep the visual layout cleaner. For example, `runners/biome_painterly.py` could emit a graph that includes the "Text to Image (Z-Image-Turbo)" blueprint subgraph as an instance, plus surrounding logic, instead of unrolling all 12 internal nodes.

Trade-off: subgraphs depend on the subgraph definition being available at canvas-load time (which it is, for blueprints — they're built-in). For custom-node-supplied subgraphs, the user must have that pack installed.

### Subgraph caching gotcha

`SubgraphManager` caches `cached_custom_node_subgraphs` and `cached_blueprint_subgraphs` on first read. To pick up newly-added subgraph files mid-session, the frontend must call with `force_reload=True` (which it does on startup, but not automatically when a custom node is added later). After installing a new pack, restart ComfyUI to refresh the subgraph index.

### Sanitization for serialization

`SubgraphManager.sanitize_entry()` strips the `path` field (filesystem path is internal) and optionally the `data` field (when listing — only fetch full data per-id). This is what's served to the frontend.

---

## Cross-references

- The Comfy-Org canonical templates package (`workflows/comfy_org_canonical_templates/`, ref 27) sometimes uses subgraphs internally, sometimes flattens them. Check before reusing — flattened versions are easier to inspect, subgraph versions look cleaner in the canvas.
- For node-modes Bypass vs Never (ref 33), bypass on a subgraph instance bypasses the entire enclosed subassembly — pass-through behavior is determined by the inputNode/outputNode mapping inside.

## When to author your own subgraph for Luis

- You catch yourself dropping the same 5+ nodes into multiple workflows → make a subgraph.
- A pipeline has a "configuration knobs" surface that should stay stable but the internals will iterate → wrap as subgraph, expose only the proxy widgets, iterate inside.
- The visual graph is becoming hard to read at the canvas zoom level → group + collapse → consider subgraph.

Place authored subgraphs at:

- For shared use (both Claudes + canvas): `ComfyUI/blueprints/<name>.json` — picks up automatically (after restart).
- For runner-emitted graphs: include the subgraph definition inline in the saved graph file's `definitions.subgraphs[]` array. The runner's `_wrap_graph()` would gain a third field; the canvas loads them seamlessly.
