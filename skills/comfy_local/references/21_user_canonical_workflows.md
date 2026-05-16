---
name: User canonical workflow patterns — catalog of Luis's saved workflows
description: Inventory of workflows in ComfyUI/user/default/workflows/ that demonstrate proven patterns Luis uses. Cloned copies live at workflows/user_canonical_templates/.
type: reference
---

This is the catalog of workflow patterns Luis has already built and tested. **Before authoring a new workflow from scratch, check whether one of these covers your case** — clone the template and substitute variables. Faster and more correct than starting fresh.

Templates are at: `workflows/user_canonical_templates/<name>.json`

## Nano Banana / Gemini patterns

### Single-call style transfer with style anchor + composition reference
**Template:** `POP_Cel_Shaded_Nano_Banana_Pro.json` (9 nodes)
**Use for:** Character cel-shading, single output per call. Highest-quality character results.
**Node:** `GeminiImage2Node` (Gemini 3 Pro, ~$0.14/gen, slower but better)
**Pattern:**
- 2 LoadImage (style anchor + composition reference)
- ImageBatch (×2, combining the two refs)
- GeminiImage2Node with verbose character creation prompt + 2K + auto aspect + IMAGE+TEXT
- Image Comparer (rgthree) for A/B
- SaveImage with prefix `nano_banana_pro`

### N-parallel variations (the "give me 8 different versions" pattern)
**Templates:** `generate multiple cel sahded images.json`, `chibi_character_convert.json` (each ~22 nodes)
**Use for:** Producing N unique variations of a subject in one workflow run.
**Node:** `GeminiNanoBanana2` × N (typically 8) — **but per ref 20 § USER PREFERENCE, substitute `NanoBanana2Direct` when adapting these templates for new runners.**
**Pattern:**
- 1 LoadImage (style reference)
- 1 LoadImage (subject reference) — optional
- 1 String node (the verbose prompt — character creation, etc.)
- 1 ImageBatchMulti combining the references — **note: in the saved canonical, this is set to `mode: 4` (bypass), so it just passes the LoadImage's output through unchanged. New runners can omit it entirely and wire LoadImage directly into all N Gemini nodes' `images` inputs (`runners/icon_cel_shaded.py --variations` does exactly this).**
- N copies of `GeminiNanoBanana2`, all wired to the same prompt + reference inputs
- Each Gemini node has its own random seed
- N separate SaveImage nodes, each downstream of one Gemini node
- Cost: N × $0.10 (~$0.80 for 8 variations)
- **Wall time:** ComfyUI executes the N Gemini nodes sequentially within one workflow (no intra-workflow concurrency) — total ≈ N × single-call time. See ref 20 § N-parallel pattern wall-clock timing note.
- Result: N independent, full-quality 2K outputs (better than a contact-sheet crop)

### Single-call with master prompt for contact sheet
**Template:** `chonkify.json` (3 nodes)
**Use for:** Quick contact-sheet generation when budget matters more than per-cell quality.
**Node:** `GeminiNanoBanana2` at 4K resolution
**Pattern:**
- 1 LoadImage (subject)
- 1 GeminiNanoBanana2 with "MASTER PROMPT" structure: "Image1 transform + Image2 render style, output N on one contact sheet"
- 1 SaveImage
- Cost: 1 × $0.10 but at 4K (slightly more) = ~$0.15

### Generic prompt+reference pipeline
**Template:** `generate images from prompt and ref image.json` (26 nodes)
**Use for:** General-purpose prompt-driven generation with a reference for style.
**Nodes:** Mix of `GeminiImage2Node` and `GeminiNanoBanana2`

### Biome / environment generation
**Template:** `forest.json` (21 nodes)
**Pattern:** Multiple Gemini calls chained for biome work. Uses `GeminiImage2Node` + `GeminiNanoBanana2` together.

**Template:** `POI generation.json` (19 nodes) — POI/biome generation with `easy imageSwitch` for style anchor switching.

### Asset + background removal pipeline
**Template:** `stone3.json` (31 nodes)
**Pattern:** `GeminiImage2Node` → `RecraftRemoveBackgroundNode` → SaveImage. For props/icons that need transparent backgrounds. Uses Recraft API for bg removal (note: this is a paid API, not local).

### Frames / animation generation
**Template:** `frames.json` (24 nodes)
**Pattern:** Gemini-based frame generation pipeline. Uses both `GeminiImage2Node` and `GeminiNanoBanana2`.

## Local model patterns (no Gemini)

### Flux 2 dev image edit with reference
**Template:** `GGUG_Flux2.json` (24 nodes)
**Use for:** Flux 2 dev with image input, reference latent, mask-based editing.
**Pattern:**
- UNETLoader (`flux2_dev_fp8mixed.safetensors`) + CLIPLoader (`mistral_3_small_flux2_fp8`, type=flux2) + VAELoader (`flux2-vae`)
- Optional UnetLoaderGGUF for the GGUF variant
- 2× LoadImage (reference inputs)
- VAEEncode → ReferenceLatent → conditioning chain
- ImageScaleToTotalPixels for normalization
- ConditioningZeroOut for negative
- KSampler (euler/simple, 20 steps, cfg=1)
- VAEDecode + SaveImage
- `easy cleanGpuUsed` + `easy clearCacheAll` for VRAM management

### Flux 2 dataset builder
**Template:** `dadta set builder.json` (12 nodes)
**Use for:** Building a dataset of Flux 2-generated images.
**Pattern:** Flux 2 + ReferenceLatent + PathchSageAttentionKJ for sage attention.

### Z-Image basic + upscale
**Templates:** `Z-Image.json` (16 nodes), `Z-Image_Upscale_Image_Res.json` (18 nodes), `Z-Image_Upscale_Image_Res_2.json` (14 nodes)
**Use for:** Z-Image text-to-image with optional UltimateSDUpscale hires-fix.
**Pattern:**
- UNETLoader (z_image_turbo_bf16.safetensors)
- CLIPLoader (qwen_3_4b.safetensors, type=lumina2)
- VAELoader (qwen_image_vae or ae)
- FluxResolutionNode for clean preset resolutions
- KSampler (varying steps for turbo vs non-turbo)
- UltimateSDUpscale + UpscaleModelLoader for hires-fix
- `easy float` for parameter control

### ChronoEdit 14B image editing
**Template:** `Nvidia_chrono_edit_14B.json` (24 nodes)
**Use for:** ChronoEdit 14B instruction-based image editing.
**Pattern:**
- UNETLoader/UnetLoaderGGUF (chrono_edit_14B_fp16 or ChronoEdit-14B-Q8_0.gguf)
- CLIPLoader for the encoder
- CLIPVisionLoader + CLIPVisionEncode
- ImageResizeKJv2 for input prep
- ImageScaleToMaxDimension
- ModelSamplingSD3 for sigma adjustment
- LoraLoaderModelOnly (for any LoRAs)
- ScaleROPE for ROPE scaling
- WanImageToVideo (yes, ChronoEdit reuses Wan's i2v node internally)
- KSampler + VAEDecode + SaveImage

### Qwen-Image multi-angle character editing
**Template:** `Qwen_MultiAngle_image_edit (1).json` (21 nodes)
**Use for:** Generate multi-angle views (front / 3/4 / profile / back) of a character via Qwen-Image-Edit.
**Pattern:**
- UNETLoader (qwen_image_edit_*) + CLIPLoader (qwen_2.5_vl_7b, type=qwen_image)
- Lora Loader Stack (rgthree) for character LoRAs
- ModelSamplingAuraFlow for sigma shift
- ImageResizeKJv2 + LoadImage for the source character
- TextEncodeQwenImageEditPlus (Qwen-specific text encode)
- CR Prompt List from comfyroll for the multi-angle list
- GetNode/SetNode for parameter sharing
- KSampler + VAEDecode + EmptyLatentImage
- ModelPassThrough for chain control

## Pose-driven character generation

**Templates:** `VNCCS_Utils Pose Studio (3).json`, `VNCCS_Utils Pose Studio (4).json` (10 nodes each)
**Use for:** Character generation from a pose reference, using VNCCS pose studio.
**Pattern:**
- LoadImage (pose reference) → DWPreprocessor (DW Pose extraction)
- VNCCS_PoseStudio (pose adjustment) → VNCCS_ModelManager + VNCCS_ModelSelector
- LoraLoaderModelOnly for character LoRA
- (Plus 2 unidentified custom node UUIDs — package-specific)
- PreviewAny + SaveImage

## 3D body workflows (exploratory)

**Templates:** `SAM3DB-rigged_mesh_manipulation.json`, `SAM3DB-rigging.json`, `SAM3DB-workflow.json`
**Use for:** SAM3D body model rigging and FBX export. Probably exploratory; less production-ready.

## How to apply when authoring new runners

1. **Find the template above that matches your use case best.**
2. **Read the cloned template at `workflows/user_canonical_templates/<name>.json`.**
3. **Identify the variable parts** — typically: prompt text, reference image filename, seed, optionally save filename.
4. **Build the runner** that loads the template, substitutes the variables, and POSTs to `/prompt`.
5. **Don't change the structural patterns** (node types, wiring, key widget defaults). Those are battle-tested.

If no template matches, you're authoring something genuinely new. Build it from references 5-11 (model-family rules) + 12 (API patterns) + 18-19 (Luis's house style + game world) + 20 (Nano Banana specifics).

## Update protocol

When you read a new useful pattern from a workflow file you haven't catalogued yet, append it to this reference and copy the workflow into `workflows/user_canonical_templates/`. Keep this catalog current.

---

## Deep-dive details (added 2026-05-09 after reading full graphs)

### `dadta set builder.json` — Flux 2 Klein 9B image-edit pipeline (12 nodes)

**Use for:** Editing an existing image by feeding it as a reference latent through Klein 9B with strong guidance.

**Pipeline:**
- LoadImage → VAEEncode → ReferenceLatent → KSampler.latent_image
- UNETLoader: `flux-2-klein-9b-fp8.safetensors`
- CLIPLoader: `qwen_3_8b_fp8mixed.safetensors`, type=`flux2` (correct Klein-9B encoder pairing — matches ref 16)
- VAELoader: `flux2-vae.safetensors`
- PathchSageAttentionKJ: `auto, True` (kjnodes sage-attention dial — auto-detects best mode)
- ImageScaleToTotalPixels: `nearest-exact, 1.2 megapixels` for input size normalization
- EmptyFlux2LatentImage: `1024×1024`
- 2× CLIPTextEncode (positive + negative, both empty in template — runner fills these)
- KSampler: **steps=20, cfg=8, sampler=euler, scheduler=simple, denoise=1**

**⚠️ cfg=8 is EXPERIMENTAL** (confirmed by Luis 2026-05-09): the cfg=8 saved in this template is **NOT canonical production setting** — it was experimental. Klein remains guidance-distilled with **cfg=1 as the canonical default** per ref 5.

**For runners:** when adapting this template, default cfg=1 to match the rest of the Flux 2 / Klein family. Don't propagate the cfg=8 from this template's saved widget value — that was a one-off experiment.

### `forest.json` — Biome model comparison (21 nodes, 16 links)

**Use for:** Comparing biome generation quality across multiple Gemini variants in one workflow.

**Pipeline (parallel):**
- 7× LoadImage (3 named anchors + 4 pasted images)
- ImageBatchMulti (combines 3 reference images for batch input)
- 2× String nodes (verbose biome prompts — different framings per branch)
- **2× GeminiImage2Node** (`gemini-3-pro-image-preview`, ~$0.14/gen, IMAGE+TEXT, "increment" seed mode)
- **2× GeminiNanoBanana2** (`Nano Banana 2`, ~$0.10/gen, IMAGE-only)
  - One uses thinking_level=MINIMAL (cheaper)
  - One uses thinking_level=HIGH (better)
- All at **4:3 aspect**, **2K** resolution
- 4× SaveImage outputting all variations

**Comparison axes:**
- Gemini 3 Pro vs Nano Banana 2 (model quality)
- MINIMAL vs HIGH thinking (cost vs quality)
- Multiple reference image batches (composition variations)

**Note on aspect ratio:** uses `4:3`, NOT `3:4` from V11 spec (ref 23). Forest biomes in practice may use 4:3 hero shots even though biome framework says 3:4 portrait. Verify with Luis which is current canonical.

**Total cost per run:** 2 × $0.14 + 2 × $0.10 = ~$0.48 for 4 biome comparisons.

### `Qwen_MultiAngle_image_edit (1).json` — Character multi-angle generation (21 nodes, 22 links)

**Use for:** Generate multi-angle camera views (front / 3-quarter / profile / back) of a character via Qwen Image Edit + multi-angle LoRA. Critical workflow for character consistency / turnarounds.

**Pipeline:**
- LoadImage("pasted/image (512).png") → ImageResizeKJv2 (1328×1328, nearest-exact, crop, GPU)
- UNETLoader: **`Qwen-Rapid-AIO-LiteNSFW-v9.safetensors`** (community variant of Qwen Image Edit, all-in-one)
- CLIPLoader: `qwen_2.5_vl_7b.safetensors`, type=`qwen_image`
- VAELoader: `qwen_image_vae.safetensors`
- **`Lora Loader Stack (rgthree)`** with `Qwen-Edit_Angles.safetensors` strength 1.0 (and 3 empty LoRA slots for stacking)
- **`ModelSamplingAuraFlow` shift=0.3** (vs Z-Image's shift=3 — much smaller shift for Qwen-Edit)
- **`TextEncodeQwenImageEditPlus`** for both positive and negative conditioning
- Positive prompt example: bilingual Chinese + English: *"将镜头向左旋转45度（Rotate the camera 45 degrees to the left.）"*
- **`CR Prompt List`** from comfyroll containing a list of camera movements (in Chinese + English):
  - 将镜头向前移动（Move the camera forward.）
  - 将镜头向左移动（Move the camera left.）
  - 将镜头向右移动（Move the camera right.）
  - 将镜头向下移动（Move the camera down.）
  - 将镜头向左旋转90度（Rotate the camera 90 degrees to the left.）
  - 将镜头向右旋转90度（Rotate the camera 90 degrees to the right.）
  - And more variants
- EmptyLatentImage: 1144×1472 (Qwen-native 3:4 portrait)
- **KSampler: steps=6, cfg=1, sampler=`sa_solver`, scheduler=`beta`, denoise=1**
- VAEDecode → PreviewImage
- Uses `GetNode`/`SetNode` (kjnodes) for parameter sharing across the graph
- `ModelPassThrough` for chain control

**Embedded Qwen-Image native resolution table** (from MarkdownNote in workflow):

```
1:1 → 1328×1328
16:9 → 1664×928
9:16 → 928×1664
4:3 → 1472×1140
3:4 → 1140×1472
3:2 → 1584×1056
2:3 → 1056×1584
```

**Key insight: bilingual prompts.** The `TextEncodeQwenImageEditPlus` node accepts mixed Chinese+English where the Chinese command is the primary instruction. This is the convention Qwen-Image-Edit was trained on.

**For runners:** when building a `runners/character_multiangle.py`, clone this template's structure. Required pieces:
1. The `Qwen-Edit_Angles.safetensors` LoRA must be present (verify in `G:\models\loras\`)
2. Use `TextEncodeQwenImageEditPlus` for prompts (NOT regular CLIPTextEncode)
3. The bilingual camera-prompt format works — substitute the camera command per output angle
4. `sa_solver` + `beta` at 6 steps is the proven sampler combo for Qwen-Edit
5. ModelSamplingAuraFlow shift=0.3 (NOT 3 — that's Z-Image's value)

### Updated catalog ordering preference

When suggesting a workflow template to clone, **prefer reading the actual JSON over relying on this catalog** — the catalog summarizes node types and key widgets, but the full graph structure (links, exact widget orderings, node positions, group rectangles) lives in the JSON. The catalog tells you which template to read; the JSON tells you how to clone it.
