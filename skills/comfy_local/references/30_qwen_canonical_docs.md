---
name: Qwen-Image family canonical docs from docs.comfy.org
description: Direct from official Qwen tutorials — Qwen-Image base, 2512, Edit-2511, Layered. Recommended settings, ControlNet variants, multi-person consistency, layer decomposition, Lightning LoRA pairings. Supersedes/extends ref 6.
type: reference
---

**Source:** Web fetched 2026-05-09 from `docs.comfy.org/tutorials/image/qwen/`.

This document captures the **OFFICIAL** Qwen tutorials. It supersedes any conflicting info in `references/06_qwen_image_family.md` (which was based on file inventory + reverse engineering). Where this doc and ref 6 disagree, **trust this one** — it's from Comfy-Org's own documentation.

## Qwen-Image (base August 2025 release)

20B parameter MMDiT (Multimodal Diffusion Transformer), Apache 2.0 license.

**Capabilities:**
- Multilingual text rendering (English, Chinese, Korean, Japanese, etc.) with high precision
- Diverse artistic styles (photoreal, impressionist, anime, minimalist)
- Multiple ControlNet support paths (see below)

**Three workflow variants in the official template `image_qwen_image.json`:**

1. **Qwen-Image original fp8_e4m3fn**
   - Model: `qwen_image_fp8_e4m3fn.safetensors`
   - Default: 50 steps, cfg 4.0
   - VRAM (RTX 4090D 24GB): 86% utilization, ~94s first run / ~71s subsequent

2. **Qwen-Image fp8 + lightx2v 8-step Lightning LoRA**
   - Same diffusion model + LoRA: `Qwen-Image-Lightning-8steps-V1.0.safetensors`
   - 8 steps, cfg 1.0
   - VRAM: 86% utilization, ~55s first / ~34s subsequent

3. **Qwen-Image distilled fp8** (community/non-official)
   - Model: `qwen_image_distill_full_fp8_e4m3fn.safetensors`
   - Recommended: 15 steps cfg 1.0 (10 steps also works)
   - Use `euler` OR `res_multistep` based on image type
   - VRAM: 86% utilization, ~69s first / ~36s subsequent
   - **NOT compatible** with the Lightning 8-step LoRA — pick one

**Standard pipeline (all variants):**
- UNETLoader → CLIPLoader (`qwen_image` type) → VAELoader (`qwen_image_vae.safetensors`)
- Text encoder: `qwen_2.5_vl_7b_fp8_scaled.safetensors`
- Latent: `EmptySD3LatentImage`
- KSampler with appropriate steps/cfg/sampler

### Qwen-Image — ControlNet variants (4 paths)

**Path 1 — InstantX ControlNet Union** (the standard ControlNet approach):
- Model: `Qwen-Image-InstantX-ControlNet-Union.safetensors` (Luis already has this in `controlnet/`)
- Used like normal ControlNet
- Companion model: **Lotus Depth** for depth map generation: `lotus-depth-d-v1-1.safetensors` (Luis has `lotus-depth-d-v1-1.safetensors` in `diffusion_models/`!) plus an SD1.5 VAE (`vae-ft-mse-840000-ema-pruned.safetensors`)
- Alternative: use `comfyui_controlnet_aux` for depth preprocessing

**Path 2 — DiffSynth-ControlNets via model patches**:
- NOT a ControlNet — a model patch
- Three modes: Canny, Depth, Inpaint
- Models go in `ComfyUI/models/model_patches/` folder
- Files:
  - `qwen_image_canny_diffsynth_controlnet.safetensors`
  - `qwen_image_depth_diffsynth_controlnet.safetensors`
  - `qwen_image_inpaint_diffsynth_controlnet.safetensors`
- Inpaint requires Mask Editor to draw mask
- Use `Ctrl-B` to bypass the Canny preprocessing node when using Depth or Inpaint variants

**Path 3 — Union ControlNet via LoRA**:
- Single LoRA file: `qwen_image_union_diffsynth_lora.safetensors` (goes in `loras/`)
- Supports: canny, depth, pose, lineart, softedge, normal, openpose
- Loaded via `LoraLoaderModelOnly`
- Use `comfyui_controlnet_aux` for the various preprocessors

**Path 4 — InstantX Inpainting ControlNet** (separate from Union):
- File: `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors` (Luis has this in `controlnet/`)

## Qwen-Image-2512 (December 2025 update)

**Improvements over base:**
- Enhanced human realism (much less "AI-generated" look)
- Finer natural detail (landscapes, animal fur, etc.)
- Improved text rendering accuracy and layout

**Models:**
- `qwen_image_2512_fp8_e4m3fn.safetensors` (recommended) — Luis has this
- `qwen_image_2512_bf16.safetensors` (higher VRAM, better quality) — Luis has this

**Workflow has TWO subgraphs in the same template:**
1. "Text to Image (Qwen-Image 2512)" — standard 50-step
2. "Text to Image (Qwen-Image 2512 4steps)" — 4-step Lightning acceleration

**Lightning LoRA:** `Qwen-Image-Lightning-4steps-V1.0.safetensors` (from `lightx2v/Qwen-Image-Lightning`). **NOT** the 2-step "Wuli" LoRA I'd documented earlier — that was a different community variant that may or may not exist. The official 2512 path is **4 steps via lightx2v**.

**Aspect ratios** (canonical, same as base Qwen):
| Ratio | Resolution |
|---|---|
| 1:1 | 1328×1328 |
| 16:9 | 1664×928 |
| 9:16 | 928×1664 |
| 4:3 | 1472×1104 |
| 3:4 | 1104×1472 |
| 3:2 | 1584×1056 |
| 2:3 | 1056×1584 |

## Qwen-Image-Edit-2511 (November 2025 — LATEST EDIT VERSION)

**Major capabilities Luis should know about:**

1. **Mitigated image drift** — better stability across repeated edits
2. **Improved character consistency** — preserves identity during imaginative edits (KEY for character-iteration workflows)
3. **Multi-person consistency** — high-fidelity fusion of MULTIPLE PERSON IMAGES into coherent group shots. **This is huge for roster/party-shot work.** Luis can feed in multiple individual character renders and get a coherent group composition.
4. **Integrated LoRA capabilities** — popular community LoRAs built into the base model (no need to load separately for common effects)
5. **Enhanced industrial design** — batch product designs with material replacement
6. **Geometric reasoning** — generates auxiliary construction lines for design / annotation

**Models:**
- `qwen_image_edit_2511_bf16.safetensors` — Luis has this
- Lightning LoRA (4-step): `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`

**VAE:** standard `qwen_image_vae.safetensors` (NOT the layered VAE).

**For game roster work specifically:** generate each NPC individually with the roster cel-shaded style, then use Qwen-Image-Edit-2511 with multi-person consistency to compose them into group shots / scene shots without losing per-character identity.

## Qwen-Image-Layered (December 2025)

**The capability:** decomposes a single image into N **RGBA layers** with physical isolation. Each layer can be edited independently.

**Why this matters for Luis's work** (game asset pipeline):
- Generate a character → decompose into base body + clothing + accessories → edit each layer independently in Photoshop
- Generate a biome → decompose into foreground + midground + background → faster parallax slicing (replaces manual layer separation in PS)
- Generate an icon → decompose into shape + outline + decorations → recolor independently

**Variable layer count** — choose 3, 4, 8, or more. NOT fixed.

**Recursive decomposition** — any output layer can be further decomposed. Infinite depth possible.

**Models:**
- `qwen_image_layered_bf16.safetensors` (default, high VRAM) — Luis has this
- `qwen_image_layered_fp8mixed.safetensors` (lower VRAM alternative) — verify Luis has

**VAE:** `qwen_image_layered_vae.safetensors` — **CRITICAL: this is a different VAE than regular Qwen-Image.** Mixing them up will produce broken output. Luis has both VAEs in his library.

**Workflow uses subgraphs.** To swap fp8 vs bf16 model, edit the subgraph (Load Diffusion Model node inside) — not the top-level node.

**Settings:**
- 50 steps, CFG 4.0 (slow, generation time at least double)
- **Recommended input: 640px** (use 1024px for high-resolution output)
- The text prompt describes the OVERALL content of the input image, INCLUDING ELEMENTS THAT MAY BE PARTIALLY OCCLUDED (e.g., specify text hidden behind a foreground object). NOT for controlling individual layer semantics — that's not how the model works.

## Updated runner recommendations

When building Qwen runners going forward:

| Use case | Variant | LoRA | Steps | cfg | Notes |
|---|---|---|---|---|---|
| Text-to-image, fastest | 2512 + Lightning 4-step | `Qwen-Image-Lightning-4steps-V1.0.safetensors` | 4 | 1.0 | euler/simple |
| Text-to-image, balanced | 2512 standard | none | 50 | 4.0 | Latest quality |
| Text-to-image, fast (older path) | base + Lightning 8-step | `Qwen-Image-Lightning-8steps-V1.0.safetensors` | 8 | 1.0 | |
| Text-to-image, distilled | distilled fp8 | none | 15 (or 10) | 1.0 | euler or res_multistep |
| Image edit, latest | 2511 standard | none | (varies, see template) | (varies) | Multi-person consistency |
| Image edit, fast | 2511 + Lightning 4-step | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | 4 | 1.0 | |
| Image decomposition (layers) | Layered bf16 OR fp8mixed | none | 50 | 4.0 | input 640px, NEEDS layered VAE |
| ControlNet (canny/depth/pose/etc) | base + Union LoRA | `qwen_image_union_diffsynth_lora.safetensors` | (varies) | (varies) | Use comfyui_controlnet_aux for preprocessing |
| ControlNet (canny/depth/inpaint, model-patch) | base + diffsynth model patch | n/a | (varies) | (varies) | Models in `model_patches/` folder |
| ControlNet (InstantX) | base + InstantX Union | n/a | (varies) | (varies) | Standard ControlNet path |

## What this changes about my earlier Qwen documentation

Three corrections to ref 6:

1. **The "Wuli 2-step LoRA" I'd flagged earlier is NOT documented in the official tutorials.** The canonical fast Qwen path uses **lightx2v's 4-step Lightning LoRA** for 2512, or **lightx2v's 8-step Lightning LoRA** for base. The Wuli LoRA may be a community variant — verify before committing.

2. **The native Qwen aspect ratios I had documented are CORRECT** but the official table says 4:3 = 1472×1104 (not 1140 as I'd seen elsewhere). Use the official table values.

3. **Qwen-Image-Layered uses a DIFFERENT VAE** (`qwen_image_layered_vae.safetensors`). Luis has both VAEs but it's easy to mix up. The layered model needs the layered VAE.

## Game-asset-specific takeaways for Luis

- **Roster group shots** → Qwen-Image-Edit-2511 with multi-person consistency is the new tool. Generate individual character renders separately, compose with Edit-2511.
- **Parallax-ready biomes** → Qwen-Image-Layered generates a biome with built-in layer separation. Could replace manual Photoshop slicing for biome hero shots. Game-changing for biome workflow.
- **Icon batches with Lightning** → 2512 + 4-step Lightning is the fast iteration path. ~5-10s per icon at 1328×1328 on a 5090.
- **ControlNet for pose-driven characters** → Union LoRA approach is most flexible (one LoRA, multiple control modes). Combine with `comfyui_controlnet_aux` for preprocessing.
