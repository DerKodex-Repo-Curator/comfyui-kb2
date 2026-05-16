---
name: Custom node deep-dives — production-critical nodes
description: Detailed schemas and usage patterns for custom nodes that show up repeatedly in Luis's production workflows. For runner authors, reach for these instead of plumbing primitives.
type: reference
---

The general 47-package catalog is in `references/09_custom_nodes_catalog.md`. This document goes deeper on the specific nodes that matter for Luis's actual production patterns.

## ModelSamplingAuraFlow (core, `comfy_extras/nodes_model_advanced.py`)

**What it does:** Patches the model with AuraFlow-style sigma shift. Required between UNETLoader and KSampler for Z-Image and Qwen-Image-Edit.

**Schema:**
```python
INPUT_TYPES: model (MODEL) + shift (FLOAT, default 1.73, min 0.0, max 100.0)
RETURN: (MODEL,) — the patched model
FUNCTION: patch_aura(self, model, shift) → self.patch(model, shift, multiplier=1.0)
```

**Shift values by model — proven defaults:**

| Model | Shift | Source |
|---|---|---|
| Z-Image (all variants) | **3** | Purz's proven pipeline (ref 8) |
| Qwen-Image-Edit | **0.3** | `Qwen_MultiAngle_image_edit (1).json` (ref 21) |
| AuraFlow base | 1.73 (default) | Node default |
| Other models | varies | Test empirically |

**Critical:** wrong shift value = wash-out / incoherent output. Z-Image with shift=0.3 will look broken; Qwen-Edit with shift=3 will too.

**API format:**
```json
"5": {"class_type": "ModelSamplingAuraFlow",
      "inputs": {"model": ["1", 0], "shift": 3.0}}
```

## RgthreePowerLoraLoader (rgthree-comfy)

**What it does:** Stacks N LoRAs on a model+clip in one node, with on/off toggles per LoRA. Replaces chained `LoraLoader` nodes for cleaner workflows when stacking multiple style/character LoRAs.

**Schema:**
```python
required: {} — nothing required at the schema level
optional: FlexibleOptionalInputType — accepts dynamic LORA_N entries from UI
RETURN: (MODEL, CLIP)
```

**API format quirk:** because it uses FlexibleOptionalInputType, each LoRA is passed as a kwargs entry named `LORA_N` containing a dict:

```json
"7": {"class_type": "Power Lora Loader (rgthree)",
      "inputs": {
        "model": ["1", 0],
        "clip": ["2", 0],
        "LORA_1": {"on": true, "lora": "Z-Image_Turbo_POP_IconsV2.safetensors", "strength": 1.0},
        "LORA_2": {"on": true, "lora": "C64style_Z-Image_Turbo.safetensors", "strength": 0.7},
        "LORA_3": {"on": false, "lora": "...", "strength": 0.5, "strengthTwo": 0.3}
      }}
```

- `on`: enable/disable this LoRA
- `lora`: filename (must exist in `G:\models\loras\`)
- `strength`: model strength
- `strengthTwo` (optional): separate clip strength; if absent, uses `strength` for both

**Dynamic count:** users can add LoRA_3, LoRA_4, etc. up to any number. The node loops over all LORA_* keys.

**When to reach for this:** any time a workflow stacks 2+ LoRAs. Flux character + style; Z-Image POP icon + pixel art accent; Qwen multi-angle + character LoRA.

## ImageBatchMulti (kjnodes)

**What it does:** Like `ImageBatch` but takes N images instead of 2. Uses an `inputcount` widget to dynamically expose N image inputs.

**Schema (inferred from usage):**
```
required: inputcount (INT) + image1 (IMAGE) + image2 (IMAGE) + ... up to inputcount
RETURN: (IMAGE,) — batched along batch dimension
```

**API format:**
```json
"3": {"class_type": "ImageBatchMulti",
      "inputs": {
        "inputcount": 3,
        "image_1": ["10", 0],
        "image_2": ["11", 0],
        "image_3": ["12", 0]
      }}
```

**Use:** for Pattern A style transfer with multiple reference images (e.g., 1 style anchor + 1 composition reference + 1 expression reference). `forest.json` uses `inputcount=3`.

## TextEncodeQwenImageEditPlus (core, `comfy_extras/nodes_qwen.py`)

**What it does:** Qwen-Image-Edit-specific text+image conditioning. Takes prompt + up to 3 reference images and uses Qwen's chat template internally.

**Schema:**
```python
inputs:
  clip (CLIP)
  prompt (STRING, multiline, dynamic_prompts=True)
  vae (VAE, optional) — when provided, also produces reference_latents
  image1, image2, image3 (IMAGE, optional) — up to 3 ref images
RETURN: (CONDITIONING,)
```

**Internal mechanism:**
- Each image is resized to ~384×384 for visual encoding
- The prompt gets `Picture N: <|vision_start|><|image_pad|><|vision_end|>` tags prepended for each image provided
- Uses Qwen's llama template: `"<|im_start|>system\nDescribe the key features of the input image, then explain how the user's text instruction should alter or modify the image..."`
- If `vae` is supplied, images also get encoded to latents (1024×1024) and attached as `reference_latents` to the conditioning

**Why use it instead of CLIPTextEncode for Qwen-Image-Edit:** it builds the system prompt that Qwen-Edit was trained on. Plain CLIPTextEncode won't get the model into "edit this image" mode — it'll just generate from text.

**Bilingual prompts work** — Luis's `Qwen_MultiAngle_image_edit` workflow uses Chinese + English prompts like `"将镜头向左旋转45度（Rotate the camera 45 degrees to the left.）"`. The Chinese command is primary; English in parens is for human readability.

**API format:**
```json
"179": {"class_type": "TextEncodeQwenImageEditPlus",
        "inputs": {
          "clip": ["160", 0],
          "prompt": "将镜头向左旋转45度（Rotate the camera 45 degrees to the left.）",
          "vae": ["123", 0],
          "image1": ["166", 0]
        }}
```

## RgthreeImageComparer (rgthree-comfy)

**What it does:** Extends `PreviewImage`. Renders an A/B before-after comparison in the node UI. Pure UX — doesn't affect generation.

**Schema:**
```python
RETURN: nothing
FUNCTION: compare_images
```

**Usage convention:** wire `image_a` to the original (e.g., LoadImage) and `image_b` to the generated (e.g., NanoBanana2Direct output). The node renders a slider in the UI to compare. Luis includes this node in style-transfer workflows for visual A/B.

**API format:**
```json
"1": {"class_type": "Image Comparer (rgthree)",
      "inputs": {
        "image_a": ["10", 0],
        "image_b": ["3", 0]
      }}
```

**For runners:** include this node in workflow templates if Luis will open the resulting workflow JSON in the UI for visual review. Skip for headless-only runs.

## PathchSageAttentionKJ (kjnodes)

**What it does:** A "patch SageAttention" node — toggles sage attention behavior on a model. Used in `dadta set builder.json` with widgets `['auto', True]`.

**Inferred schema:**
```python
inputs: model (MODEL) + mode (STRING enum: "auto" | "sage" | "off") + enable (BOOLEAN)
RETURN: (MODEL,) — patched
```

**When to use:** when you want to override the global `--use-sage-attention` flag at workflow level (e.g., disable sage for a specific model that has issues with it). Most workflows don't need this since SageAttention is enabled globally via launcher flag.

## easy imageSwitch (Easy-Use)

**What it does:** Boolean switch between two images based on a condition. Logic node in `ComfyUI-Easy-Use/py/nodes/logic.py:240`.

**Use:** A/B routing in a workflow — "if condition X, use image A, else image B". Useful in `POI generation.json` for switching between style anchors based on a flag.

## CR Prompt List (Comfyroll)

**What it does:** Holds a list of prompts (one per line) and outputs the prompt at a given index. Used to iterate over a list of variations.

**API format pattern:**
```json
"189": {"class_type": "CR Prompt List",
        "inputs": {
          "prompt_text": "(unused header)",
          "prompts": "Move the camera forward.\nMove the camera left.\nMove the camera right.\n...",
          "additional_text": "",
          "current_index": 0,
          "max_index": 1000
        }}
```

**Use:** for batch generation across a fixed prompt list (e.g., 8 camera angles for character turnaround). The KSampler downstream uses the `current_index` widget to pick which prompt for this run.

**For runners:** instead of using this node, prefer building N parallel sub-graphs in the runner (the N-parallel pattern from ref 20). CR Prompt List is for ComfyUI UI-driven batch loops, not headless API-driven runners.

## sa_solver sampler (core)

**What it is:** A specialized sampler used for Qwen-Image-Edit work. Listed in `comfy.samplers.SAMPLER_NAMES`.

**Pairing:** `sa_solver` + `beta` scheduler at 6 steps is Luis's proven combo for Qwen-Edit (per `Qwen_MultiAngle_image_edit (1).json`).

Already documented in `references/11_samplers_schedulers.md` § Sampler personalities — but worth noting again because it's not the obvious default. For Qwen-Image-Edit-specific runners, use this combo, NOT `euler/simple`.

## ImageResizeKJv2 (kjnodes)

**What it does:** Resize an image with various methods, including GPU-accelerated resize. Used in `Qwen_MultiAngle_image_edit` to normalize input to Qwen-native 1328×1328.

**Schema (from widget order observed):**
```
inputs: image, width (INT), height (INT), upscale_method (STRING: "nearest-exact" etc.),
        keep_proportion (STRING: "crop"|"pad"|"stretch"|"resize"),
        pad_color (STRING: "0, 0, 0"),
        crop_position (STRING: "center"|"top"|...),
        divisible_by (INT, e.g. 2),
        device (STRING: "gpu"|"cpu")
```

**Use:** input pre-processing for Qwen-Image-Edit and Flux 2 image-edit workflows. The "crop" mode preserves aspect by cropping; "pad" preserves aspect by padding; "resize" stretches.

## GetNode / SetNode (kjnodes)

**What they do:** Named variable storage across a workflow graph. SetNode stores a value with a string key; GetNode retrieves it later. Avoids long visual links across the canvas.

**Use:** parameter sharing in large workflows (e.g., `Qwen_MultiAngle_image_edit` uses `Set_model_node`/`Get_model_node` to share the model output across multiple consumer nodes without spaghetti links).

**API format:**
```json
"82": {"class_type": "SetNode",
       "inputs": {"input_value": ["121", 0]},
       "widgets_values": ["model_node"]}
"162": {"class_type": "GetNode",
        "widgets_values": ["model_node"]}
```

**For runners:** prefer direct links in API workflows since they're more verifiable and don't depend on the kjnodes runtime resolving named vars correctly. Use SetNode/GetNode only when adapting an existing template that uses them.

## ModelPassThrough (kjnodes)

**What it does:** Identity node — passes a MODEL through without modification. Used as a chain control point.

**Use:** breaking a long model chain into segments, or as an anchor for SetNode/GetNode wiring.

## Summary table — when to reach for which node

| Goal | Reach for |
|---|---|
| Stack 2+ LoRAs cleanly | `Power Lora Loader (rgthree)` |
| Z-Image / Qwen-Edit / AuraFlow sigma shift | `ModelSamplingAuraFlow` |
| Qwen-Image-Edit prompt + reference images | `TextEncodeQwenImageEditPlus` |
| Visual A/B comparison in UI | `Image Comparer (rgthree)` |
| Batch N reference images | `ImageBatchMulti` (kjnodes) |
| GPU-accelerated image resize | `ImageResizeKJv2` (kjnodes) |
| Parameter sharing across complex graph | `SetNode`/`GetNode` (kjnodes) |
| Override sage attention per workflow | `PathchSageAttentionKJ` (kjnodes) |
| Conditional image routing | `easy imageSwitch` |
| Iterate over a fixed prompt list (UI-driven) | `CR Prompt List` (comfyroll) |
| Iterate over a prompt list (headless) | N parallel sub-graphs in runner — see ref 20 N-parallel pattern |

## When updating a runner template

If a saved workflow you're cloning uses one of these custom nodes, **don't strip the node** — it's there for a reason. Common reasons:

- `ModelSamplingAuraFlow` between UNETLoader and KSampler → the model needs the sigma shift
- `Power Lora Loader (rgthree)` → stacking multiple LoRAs cleanly
- `TextEncodeQwenImageEditPlus` → Qwen-Image-Edit specific, regular CLIPTextEncode won't work
- `ImageBatchMulti` → multiple reference images batched

If you DON'T have the custom node installed and you want to substitute a core equivalent, here are the closest mappings:

| Custom node | Core substitute |
|---|---|
| `Power Lora Loader (rgthree)` | Chained `LoraLoader` nodes |
| `ImageBatchMulti` | Chained `ImageBatch` nodes (only handles 2 inputs each) |
| `ImageResizeKJv2` | `ImageScale` or `ImageScaleToTotalPixels` (less control) |
| `SetNode`/`GetNode` | Direct links (just deal with the visual spaghetti) |
| `easy imageSwitch` | Logic via `Switch` core node if it exists, else replicate via two workflows |
| `Image Comparer (rgthree)` | Just two `PreviewImage` nodes side by side |

`ModelSamplingAuraFlow` and `TextEncodeQwenImageEditPlus` are core ComfyUI nodes (in `comfy_extras`), so they're always available.
