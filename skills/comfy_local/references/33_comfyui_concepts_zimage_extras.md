---
name: ComfyUI core concepts (Nodes/Properties/Links/Modes/Mask Editor) + Z-Image family deep dive + Node docs + Custom Node management
description: Foundational concepts from docs.comfy.org/development/core-concepts/* — node modes (Never vs Bypass!), data type color coding, Mask Editor, in-app node docs system. Plus Z-Image complete family (Base, Turbo, Edit, Fun ControlNet).
type: reference
---

**Source:** Web fetched 2026-05-09 from `docs.comfy.org` Nodes/Properties/Links/Custom-Nodes concepts + Mask Editor + Node docs + Z-Image / Z-Image-Turbo tutorials.

This document fills in foundational concepts I'd been working from the source code without official confirmation. **Several of these have direct workflow-authoring implications.**

## Node Modes — CRITICAL distinction between Never and Bypass

ComfyUI nodes have **modes** that change how they execute. The right-click menu offers four options but only TWO actually work right now (the others are placeholders):

| Mode | Behavior | Effect on subsequent nodes |
|---|---|---|
| **Always** (default, mode=0) | Node executes when first run OR when any input changes since last execution | Normal — receives this node's output |
| **Never** (mode=2) | Node NEVER executes — as if deleted | **ERRORS** — subsequent nodes get NO data |
| **Bypass** (mode=4) | Node never executes — but data passes through unprocessed | **Continues normally** — subsequent nodes receive the input data that *would have* gone into this node |
| ~~On Event~~ | (placeholder, not implemented) | n/a |
| ~~On Trigger~~ | (placeholder, not implemented) | n/a |

**The Never vs Bypass distinction is huge.** Concrete example: two LoRA loaders chained M → LoRA1 → LoRA2 → KSampler.
- `LoRA1` set to **Never** → KSampler errors (no model output reaches it)
- `LoRA1` set to **Bypass** → KSampler runs with the original M (LoRA1's effect skipped, but workflow continues)

**Keyboard shortcut for Bypass:** `Ctrl+B` (saw this referenced in earlier docs).

**For runner authoring:** when generating workflow JSONs that include "optional" Lightning LoRA nodes, set the LoRA loader's `mode: 4` (Bypass) by default. Users can right-click → "Always" to enable it. This is exactly how the official Qwen template handles the "with/without Lightning LoRA" toggle.

In API format, the `mode` field in each node entry controls this:

```json
"7": {
  "class_type": "LoraLoaderModelOnly",
  "mode": 4,                    // Bypass — LoRA inactive
  "inputs": {...}
}
```

## Data type → color coding (official table)

The strong-typing system enforces port matching. Same color = compatible:

| Data type | Color |
|---|---|
| diffusion model | **lavender** |
| CLIP model | **yellow** |
| VAE model | **rose** (pink-red) |
| conditioning | **orange** |
| latent image | **pink** |
| pixel image | **blue** |
| mask | **green** |
| number (integer or float) | **light green** |
| mesh | **bright green** |

**For workflow JSON authoring:** when creating links, the `type` field in each link tuple `[lid, src, sslot, tgt, tslot, "TYPE"]` should match what the source/target slots advertise. ComfyUI enforces this — wrong types throw errors.

## Node states (UI runtime)

1. **Normal** — default state
2. **Running** — actively executing
3. **Error** — red marker on the input that's broken (Luis has hit this from encoder mismatch)
4. **Missing** — node not loaded; two cases:
   - Core node missing → ComfyUI is older than the workflow needs (update via stable release)
   - Custom node missing → use ComfyUI Manager to find/install, OR install via the workflow's node-package metadata

## Node Selection Toolbox

Floating quick-action panel that appears when a node is selected. Functions:
- Change color
- Quickly set to Bypass mode (the most-used shortcut on this toolbox)
- Lock the node
- Delete
- (For output nodes) Partial Execution green triangle (per ref 31)
- (For nodes with docs) Node info icon to open Node Docs

Disable in Settings if you don't want it.

## Mask Editor — built-in inpainting mask creation

**Triggered via:** right-click on a `Load Image` node → `Open in MaskEditor`.

**Use:** creates an editable mask directly in ComfyUI. Click + drag with mouse to paint the mask. No external tools needed.

**For inpainting workflows** (Qwen-Edit Inpaint variant, BrushNet, FluxFill, etc.) this is the standard mask-creation flow. Saves a round-trip to Photoshop.

**Output:** mask is attached to the LoadImage's `MASK` output socket, ready to feed into VAE encoders, ControlNet inputs, etc.

## In-app Node Docs

ComfyUI ships embedded documentation for built-in nodes:

**To view:**
- Select node → click info icon in selection toolbox, OR
- In node library (left sidebar), hover a node → click `?` icon

**Source:** `https://github.com/Comfy-Org/embedded-docs` repo. Anyone can contribute via PR.

**Custom nodes can ship their own docs.** The Comfy-Org developer guide ("Adding node docs") explains how. Custom nodes that include docs auto-show in the same panel.

**For Luis when building custom nodes:** ship docs alongside the node — the in-app doc panel makes the node feel polished and discoverable.

## Z-Image — complete family

Z-Image is by **Alibaba's Tongyi Lab** (same team as Qwen-Image). 6B parameters. **S3-DiT architecture** (Scalable Single-Stream DiT) — text + visual semantic tokens + image VAE tokens concatenated at sequence level.

**Three official variants:**

| Variant | Purpose | Key setting | VRAM |
|---|---|---|---|
| **Z-Image-Base** | Foundation model for community fine-tuning | Standard sampling | Higher |
| **Z-Image-Turbo** | Distilled fast version | **8 NFEs** (Number of Function Evaluations = steps) | Fits in **16 GB** consumer cards |
| **Z-Image-Edit** | Image editing variant | Instruction-following | TBD |

**Sub-second inference latency** on H800 enterprise GPUs for Turbo. On Luis's 5090, much faster.

**NFE = Number of Function Evaluations** — technical term for "steps" in sampling. 8 NFEs = 8 KSampler steps. (Slightly different from "steps" in some flow-matching contexts where each step may require multiple NFEs, but functionally equivalent in ComfyUI's basic KSampler.)

**Files (all variants):**
- text encoder: `qwen_3_4b.safetensors` — same Qwen3-4B encoder
- VAE: `ae.safetensors` — **same as Flux.1's VAE!** (Z-Image and Flux.1 share the autoencoder)
- diffusion model varies:
  - Base: `z_image_bf16.safetensors`
  - Turbo: `z_image_turbo_bf16.safetensors`
  - Edit: (download from `Tongyi-MAI/Z-Image` — file naming TBC, Luis may need to check)

**ControlNet support — Z-Image-Turbo Fun Union ControlNet:**

- File: `Z-Image-Turbo-Fun-Controlnet-Union.safetensors`
- Folder: `ComfyUI/models/model_patches/` (NOT `controlnet/`)
- Pattern: model patch (similar to Qwen-Image DiffSynth ControlNets) — applies as a model modification, not a standard ControlNet
- Demo workflow uses Canny preprocessing of a reference image to guide generation
- Single union model supports multiple control types (canny, depth, etc.) like Qwen's Union LoRA approach

**For Luis specifically:**
- Has Z-Image Turbo + Z-Image Base + several POP-trained LoRAs
- Does NOT have Z-Image-Edit (verify)
- Does NOT have Z-Image-Turbo Fun ControlNet (verify — would be a download)
- The Fun ControlNet would be a major capability unlock for pose-driven Z-Image character generation

## Custom Node management — official guide

(Already covered in `references/29_custom_node_ecosystem_expanded.md` and `references/32_app_mode_and_workflow_distribution.md`. Adding the few new details here.)

**Three install methods, in recommended order:**
1. **ComfyUI Manager (recommended)** — has officially joined Comfy Org, included by default in Desktop. Portable installs need to install Manager first via git.
2. **Git clone** — `cd custom_nodes && git clone <url>`. Then install dependencies.
3. **Manual ZIP** — last resort. Loses git history, can't manage versions.

**Dependency install for portable ComfyUI (Luis's setup):**
```powershell
.\python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\<package>\requirements.txt
```

**Critical:** do NOT use system pip. Use the embedded Python explicitly.

**Detecting missing nodes:** ComfyUI Manager's "Detect Missing Nodes" feature scans imported workflows and identifies missing custom node packages. One-click install from the dialog.

## Reroute node — official, native, recommended

The native `Reroute` node is the canonical way to manage link routing. Use it to:
- Avoid links crossing nodes
- Avoid links overlapping each other
- Make complex graphs visually scannable

**Don't confuse with rgthree-comfy's enhanced Reroute** which adds multi-direction, sizing, etc. Both work; use whichever you prefer.

**Configurable link styles** via Setup Menu → Display (Lite Graph) → Graph → Link Render Mode:
- Curves (default)
- Right angles
- Straight lines
- Hidden (temporarily, via Canvas Menu)

## Implications for runner authoring

**1. Use Bypass mode (mode=4) for optional LoRA loaders.** Default state should be enabled (mode=0) for the user's typical case, with an obvious right-click → Bypass to disable. This matches the official Qwen 2512 template pattern.

**2. Apply node colors when generating graph JSONs.** Group rectangles in `properties.bgcolor` are nice; matching link colors to data types is automatic since ComfyUI inferes from the slot type.

**3. For inpainting runners, integrate Mask Editor expectation.** Don't try to programmatically create masks — let the user paint them via Mask Editor in the UI, then save the workflow JSON with the mask routing in place.

**4. For node docs in custom nodes Luis builds:** ship them. The `embedded-docs` mechanism makes nodes look polished. Use the developer guide.

**5. For Z-Image runners specifically:** the same `qwen_3_4b.safetensors` + `ae.safetensors` setup works for ALL Z-Image variants (Base, Turbo, Edit) — only the diffusion model file changes. CLIPLoader type stays `lumina2`. ModelSamplingAuraFlow shift varies (we'd need to test the Edit variant — Turbo and Base both use shift=3 per Purz).

## Updated knowledge gaps

After this round, things I still don't have:
- Z-Image-Edit specific workflow / settings (I know it exists but not its exact pipeline)
- HiDream tutorial (Luis doesn't have it)
- Ovis tutorial (Luis has the Ovis encoder)
- NewBie-image tutorial
- ERNIE-Image tutorial
- 3D / Video / Audio / Utility tutorial sections
- Built-in nodes overview (`docs.comfy.org/built-in-nodes/overview`)
- Cloud API reference (could be useful for advanced runner authors)

If Luis ever wants me to fetch any of these, paste the URLs back into chat.
