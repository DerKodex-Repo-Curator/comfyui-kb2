---
name: Impact / Inspire / WAS pack survey — what's actually in them
description: Headline nodes per pack with reach-for-this-when guidance. comfyui-impact-pack (face detail, segmentation, region sampling), comfyui-inspire-pack (Impact companion + caching + LoRA block weight), was-node-suite-comfyui (224 image-processing utilities).
type: reference
---

# Impact / Inspire / WAS pack survey

These three packs are massive and make up a big chunk of "the toolbox" Luis has installed. Catalog reference 9 lists them; this reference tells you which specific nodes to reach for.

**Sources read (2026-05-09):**
- `custom_nodes/comfyui-impact-pack/` (modules + README)
- `custom_nodes/comfyui-inspire-pack/` (inspire/*.py + README)
- `custom_nodes/was-node-suite-comfyui/WAS_Node_Suite.py` (224 classes in one file)

---

## comfyui-impact-pack — the detail / detection / region pipeline

**Author:** Dr.Lt.Data (`ltdrdata`). Companion to ComfyUI-Manager (same author).

**The mental model:** Impact introduces a pipeline data type called **SEGS** ("segments"). A SEGS is a list of detected regions plus metadata (bounding box, mask, confidence, label, optional cropped image). Detectors produce SEGS; manipulators filter/sort/order SEGS; detailers consume SEGS and re-sample those regions at higher detail.

### Headline nodes (reach for these)

| Node | What it does |
|---|---|
| **`UltralyticsDetectorProvider`** | Loads a YOLO `.pt` model from `models/ultralytics/`. Outputs `BBOX_DETECTOR` and `SEGM_DETECTOR` providers. Use the right model for the job: `bbox/face_yolov8m.pt` for faces, `segm/person_yolov8m-seg.pt` for full-body. |
| **`SAMLoader`** | Loads SAM (Segment Anything) for high-quality masks given bounding boxes. Pairs with the YOLO detector. |
| **`BboxDetectorSEGS`** | Run a BBox detector against an image, get back a SEGS. |
| **`SegmDetectorSEGS`** | Run a segmentation detector, get back SEGS with proper masks. |
| **`SAMDetectorCombined`** | Take a SEGS from a BBox detector and refine the masks via SAM. The standard "find faces, then mask them precisely" pipeline. |
| **`FaceDetailer`** | THE one-shot face fix. Internally: detect faces → SAM-mask → crop region → resample at higher resolution with KSampler → composite back. Full INPUT_TYPES: image, model, clip, vae, positive, negative, plus a long list of detail-tuning params. Output: image, cropped_refined, cropped_enhanced_alpha, mask, detailer_pipe, cnet_images. |
| **`FaceDetailerPipe`** | Same as FaceDetailer but takes a `BASIC_PIPE` bundle instead of separate model/clip/vae/positive/negative — saves wires. |
| **`DetailerForEach`** | Generalization of FaceDetailer: for each region in a SEGS, re-sample at higher detail. Use when you want to fix hands, eyes, regions other than faces. |
| **`DetailerForEachPipe`** | The pipe-based variant. |
| **`PreviewBridge`** | Renders an image and lets you click-mask in the canvas. The `mask_editor` workflow. Useful for quick interactive masking. |
| **`PreviewBridgeLatent`** | Same but for latents. |
| **`MaskToSEGS`** | Convert a regular MASK into a SEGS (one segment per disconnected region). |
| **`SEGSPreview`** | Render the bounding boxes / masks of a SEGS so you can see what was detected. |

### SEGS manipulation (the filter/sort layer)

`SEGSOrderedFilterDetailerHookProvider`, `SEGSRangeFilterDetailerHookProvider`, `SEGSLabelFilterDetailerHookProvider` — filter SEGS by ordering/range/label. Useful for "only re-detail the largest face," "only re-detail eyes labeled 'eye'."

### Regional sampling

`RegionalPrompt`, `RegionalSampler` — apply different prompts to different regions of the same image during sampling. Lighter alternative to ConditioningSetMask if you have multiple regions.

### Iterative Upscale

`IterativeImageUpscale`, `IterativeLatentUpscale`, `PixelKSampleUpscaler`, `TwoSamplersForMaskUpscaler`, `PixelTiledKSampleUpscaler` — multi-pass upscale with re-sampling at each step. Use `PixelKSampleUpscaler` for "1.5x → 1.5x → 1.5x" iterative scaling. Use `PixelTiledKSampleUpscaler` for tiled (memory-friendly) version.

### Switches and pipe handling

`Pipe`-prefixed nodes bundle (model, clip, vae, positive, negative) into a single `BASIC_PIPE` wire to keep workflows tidy. `ToBasicPipe` / `FromBasicPipe` are the converters. Once you have many detailers in a workflow, pipes save dozens of wires.

`SwitchAny`, `SwitchImage`, `SwitchLatent`, etc. — branch nodes that pick one of N inputs based on a selector. Useful for A/B testing within one workflow.

### When to reach for Impact

- **Face fix on game characters** → `FaceDetailer` (the one-shot version)
- **Hand fix** → `UltralyticsDetectorProvider` with a hand model + `DetailerForEach`
- **Background-only inpaint** → `BboxDetectorSEGS` (detect person) → `SAMDetectorCombined` → invert mask → KSampler with masked latent
- **Multi-region prompting** → `RegionalSampler`
- **Interactive mask painting in the canvas** → `PreviewBridge`

---

## comfyui-inspire-pack — Impact companion + caching + LoRA block weight

**Author:** Dr.Lt.Data (same as Impact). Designed to extend Impact and provide A1111-compatible features.

### Headline nodes

| Node | What it does |
|---|---|
| **`KSampler_inspire`** | KSampler variant with extra features: noise mode toggles, GPU noise mode, sigma min/max overrides, advanced step rendering. Useful when you need precise control beyond core KSampler. |
| **`KSamplerAdvanced_inspire`** | Same with the advanced sampler's start/end step controls. |
| **`Inspire_RandomNoise`** | Custom noise generator with multiple modes (cpu, gpu, deterministic). Plug into a custom KSampler chain. |
| **`HyperTileInspire`** | HyperTile attention optimization (faster sampling at high res). |
| **`Lora Block Weight`** family | Apply LoRA at varying strengths PER U-Net block. The "I want more style influence on early layers" pattern. Compatible with A1111's lora block weight syntax. |
| **`CacheBackendData`** + **`RetrieveBackendData`** | Store arbitrary data in a backend cache, retrieve in another workflow. Cross-workflow communication. Keyed by string or number. Use case: build a "library" of conditioning that other workflows pull from. |
| **`LoadImagesFromDirBatch`** | Load all images in a directory as a batch. Good for batch processing. |
| **`LoadImageInspire`** | LoadImage with extra features (path filter, recursive, etc). |
| **`SeedGenerator`** | A seed source with batched/varying modes — better than just hardcoding for batch jobs. |
| **`ConcatConditioningsWithMultiplier`** | Concat conditionings with per-conditioning weight. |
| **`ChangeImageBatchSize` / `ChangeLatentBatchSize`** | Resize a batch tensor. Useful when something downstream expects N images and you have M. |
| **`SegmDetectorSEGS Inspire`** + similar | Inspire's takes on Impact's detector pipeline. |
| **`A1111 Compat`** family | KSampler with A1111-equivalent noise + sigma behavior. Use when you're trying to reproduce an A1111 workflow exactly. |
| **`PromptStyles` / `LoadPromptsFromDir`** | A1111-style prompt template support. |
| **`RegionalPromptSimple` / `RegionalConditioning`** | Lighter regional prompting than Impact's, but still uses Impact's SEGS. |
| **`CheckpointLoaderSimpleShared`** | A checkpoint loader where the model is shared across instances. Saves memory if multiple nodes load the same checkpoint. |

### When to reach for Inspire

- **A1111 reproduction** → `KSampler_inspire` with A1111-compat options + `RandomNoise` mode=cpu
- **Cross-workflow data sharing** → `CacheBackendData` (only per-session, not persisted)
- **Per-block LoRA control** → `Lora Block Weight`
- **Batch directory loading** → `LoadImagesFromDirBatch`
- **Memory-constrained multi-checkpoint workflow** → `CheckpointLoaderSimpleShared`

---

## was-node-suite-comfyui — 224 image-processing utilities in one file

**Author:** WASasquatch (Jordan Thompson). Massive grab-bag — the "everything but the kitchen sink" pack.

**Note:** all 224 node classes live in a SINGLE 18,000+-line `WAS_Node_Suite.py` file. Class names all start with `WAS_`.

### Categories (where to look)

| Category | Examples |
|---|---|
| **Image filters** | `WAS_Image_Filters` (HSV/RGB tweaks, blur, sharpen, gamma, contrast), `WAS_Lucy_Sharpen`, `WAS_Image_Style_Filter` (instagram-style filters: vintage, sepia, etc.) |
| **Image transforms** | `WAS_Image_Crop_Face`, `WAS_Image_Paste_Face_Crop`, `WAS_Image_Crop_Location`, `WAS_Image_Crop_Square_Location`, `WAS_Image_Tile_Batch`, `WAS_Image_Paste_Crop`, `WAS_Image_Paste_Crop_Location` |
| **Image grid / contact sheets** | `WAS_Image_Grid_Image_Batch`, `WAS_Image_Grid_Image` — assemble multiple images into a contact sheet. |
| **Animation** | `WAS_Image_Morph_GIF`, `WAS_Image_Morph_GIF_Writer`, `WAS_Image_Morph_GIF_By_Path` — GIF morph between images. |
| **Blending** | `WAS_Image_Blending_Mode` (~30 modes: multiply, screen, overlay, dodge, burn, ...), `WAS_Image_Blend` (alpha blend) |
| **Color** | `WAS_Image_Color_Palette` (extract dominant colors), `WAS_Hex_to_HSL`, `WAS_HSL_to_Hex`, `WAS_Image_Analyze` |
| **Noise generators (procedural)** | `WAS_Image_Perlin_Noise`, `WAS_Image_Perlin_Power_Fractal`, `WAS_Image_Voronoi_Noise_Filter`, `WAS_Image_Power_Noise`, `WAS_Image_To_Noise` (image as noise input) |
| **Distortion / fx** | `WAS_Image_Monitor_Distortion_Filter` (CRT scanlines, glitch), `WAS_Image_Pixelate`, `WAS_Image_Make_Seamless` (tile-friendly edges), `WAS_Image_Displacement_Warp` |
| **Shadow/highlight** | `WAS_Shadow_And_Highlight_Adjustment` |
| **Batch ops** | `WAS_Image_Batch`, `WAS_Latent_Batch`, `WAS_Mask_Batch` — concat / merge / split |
| **Text utilities** | `PromptStyles` (A1111 import), `TextTokens` (token expansion), `WASDatabase` (key-value storage). The "text tokens" feature lets you use built-in tokens like `[time]`, `[date]`, `[weeknum]` in filenames. |
| **AUTOMATIC1111 style import** | Import A1111 style files (.csv) directly. |

### When to reach for WAS

- **Crop a face from one image, paste into another** → `WAS_Image_Crop_Face` + `WAS_Image_Paste_Face_Crop` (handles seam blending)
- **Build a contact sheet of generated variations programmatically** → `WAS_Image_Grid_Image_Batch`
- **Add filmstrip-style filters** → `WAS_Image_Style_Filter`
- **Generate procedural noise for use as input** → `WAS_Image_Perlin_Noise` or `WAS_Image_Voronoi_Noise_Filter`
- **Make a tileable texture from a normal image** → `WAS_Image_Make_Seamless`
- **HSL color tweaks across hex values** → `WAS_Hex_to_HSL` / `WAS_HSL_to_Hex` chain
- **Per-channel filtering** → `WAS_Image_Filters` (RGB/HSV/contrast/gamma all in one node)

### Cautions with WAS

- It's an old pack with some unmaintained dependencies. Imports include BLIP captioning, OpenCV, scipy. If a node fails to import, check `was_suite_config.json` — some submodules are toggleable.
- 224 classes in one file means slow first-load and very long node-search lists. ComfyUI-Manager can install/disable WAS independently if it causes issues.
- Some text utilities are A1111-flavored (csv style files, %tokens%). These overlap with core ComfyUI features so prefer core when possible.

---

## How these three packs interact

A common Impact + Inspire + WAS pattern Luis might use:

```
Image → UltralyticsDetectorProvider (impact, face_yolov8m.pt)
      → BboxDetectorSEGS (impact)
      → SAMDetectorCombined (impact, SAMLoader)
      → DetailerForEachPipe (impact)   ← uses KSampler_inspire internally if you swap
      → WAS_Image_Filters (was, final color tweaks)
      → SaveImage
```

Or for icon contact sheets:

```
N x KSampler runs → ImageBatch (core or WAS_Image_Batch)
                  → WAS_Image_Grid_Image_Batch (contact sheet layout)
                  → SaveImage
```

## Reach-for-this when…

- "Detail this face / hand / region" → **Impact's FaceDetailer** family (single best node in any pack for this)
- "I need A1111-equivalent sampling" → **Inspire's KSampler_inspire** + `RandomNoise` mode=cpu
- "Per-block LoRA strength" → **Inspire's Lora Block Weight**
- "Color filter / blend / fx without leaving the graph" → **WAS Image filters / blending modes**
- "Programmatic contact sheet" → **WAS_Image_Grid_Image_Batch** (Mode B/C icon outputs)
- "Mask painting in the canvas" → **Impact's PreviewBridge**
- "Cross-workflow shared cache" → **Inspire's CacheBackendData**
- "Detect bodies and inpaint backgrounds only" → **Impact BBox detector + SAM + invert mask**
