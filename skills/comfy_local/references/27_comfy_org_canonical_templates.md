---
name: Comfy-Org canonical workflow templates — official template library
description: 392 templates ship with ComfyUI in 4 packages. 42 most relevant to Luis's models are cloned to workflows/comfy_org_canonical_templates/. Use these as authoritative starting points for any new workflow type.
type: reference
---

**Source:** ComfyUI's official template packages, shipped with `comfyui_frontend_package` 1.42.14 in `python_embeded/Lib/site-packages/`:

- `comfyui_workflow_templates_media_api/templates/` — 108 API-based templates (BFL, Bytedance, Google, Kling, Hailuo, etc.)
- `comfyui_workflow_templates_media_image/templates/` — 161 image generation/edit templates
- `comfyui_workflow_templates_media_video/templates/` — 60 video templates
- `comfyui_workflow_templates_media_other/templates/` — 63 other (audio, 3D, LLM, style)

Total: **392 templates**. Manifest: `comfyui_workflow_templates_core/manifest.json`.

These are the official Comfy-Org-curated workflows shown in ComfyUI's Templates browser. They demonstrate the canonical patterns for every shipped model. **For any new workflow type, check here first.**

## Cloned to shared knowledge base

42 most-relevant templates (matching Luis's installed models) are cloned to:

```
.claude/skills/comfy_local/workflows/comfy_org_canonical_templates/
```

Both Claudes can read from there.

## Critical pattern shift: SUBGRAPHS

**Modern Comfy-Org templates use SUBGRAPHS heavily.** A subgraph is a single canvas node that contains an embedded sub-workflow with its own internal nodes/links. The user sees ONE node; internally it expands to 10-30 nodes.

**How to recognize:** subgraph nodes have UUID-style type names like `7b34ab90-36f9-45ba-a665-71d418f0df18` instead of human-readable class names. The subgraph definition is stored in the workflow JSON's top-level `subgraphs` array.

**Why this matters:**
- Modern templates look much simpler (4-8 visible nodes) but contain full pipelines internally
- Cleaner UX for end users — exposes only the user-facing knobs
- **For headless runners (API format) subgraphs are NOT a concern** — the API format always flattens to a node-id-keyed dict at execution time. Build flat workflows in your runners; ComfyUI handles the rest.
- For graph-format JSONs (drag-drop), you could optionally wrap implementation in subgraphs to match modern templates — but that's added complexity. Plain flat graphs work fine.

## Categorized templates (the cloned ones)

### Flux 2 dev — text-to-image
- `image_flux2.json` / `image_flux2_fp8.json` — basic Flux 2 dev T2I (and fp8 variant)
- `image_flux2_text_to_image.json` / `image_flux2_text_to_image_9b.json` — explicit T2I templates
- `api_flux2.json` / `api_bfl_flux2_max_sofa_swap.json` — API-routed Flux 2 (uses Comfy proxy credits)

### Flux 2 Klein — image edit (CRITICAL — multiple variants)
- `image_flux2_klein_text_to_image.json` — Klein T2I baseline
- `image_flux2_klein_image_edit_4b_base.json` — 4B base model edit
- `image_flux2_klein_image_edit_4b_distilled.json` — 4B distilled edit
- `image_flux2_klein_image_edit_9b_base.json` — 9B base edit
- `image_flux2_klein_image_edit_9b_distilled.json` — 9B distilled edit
- `image_flux2_klein_9b_kv_image_edit.json` — 9B with KV-cache variant

**Note:** Luis's `dadta set builder.json` is one of these but with cfg=8 (experimental, not canonical — see ref 21). Compare against `image_flux2_klein_image_edit_9b_distilled.json` for the canonical settings.

### Qwen-Image (T2I)
- `image_qwen_image.json` — Qwen Image T2I baseline
- `image_qwen_image_2512_with_2steps_lora.json` — **Qwen 2512 + Lightning 2-step LoRA. KSampler steps=2. ~1-2s per 1328×1328 on a 5090.** Uses `Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16.safetensors` (verify in `G:\models\loras\` before use)

### Qwen-Image-Edit
- `image_qwen_image_edit.json` — Qwen Edit baseline
- `image_qwen_image_edit_2509.json` — 2509 dated revision
- `image_qwen_image_edit_2509_relight.json` — 2509 with relight feature
- `image_qwen_image_edit_2511.json` — 2511 dated revision
- `02_qwen_Image_edit_subgraphed.json` — modern subgraph version (uses `qwen_image_edit_2509_fp8_e4m3fn.safetensors` + `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` LoRA, 4 steps)

### Qwen-Image — ControlNet & Layered & Union
- `image_qwen_Image_2512_controlnet.json` — Qwen 2512 + ControlNet
- `image_qwen_image_controlnet_patch.json` — ControlNet patch variant
- `image_qwen_image_instantx_controlnet.json` — Qwen + InstantX ControlNet (Luis has this in `controlnet/Qwen-Image-InstantX-ControlNet-Union.safetensors`)
- `image_qwen_image_instantx_inpainting_controlnet.json` — InstantX inpainting variant
- `image_qwen_image_union_control_lora.json` — Union ControlNet via LoRA
- `image_qwen_image_layered.json` / `image_qwen_image_layered_control.json` — Qwen Image Layered (separated layer outputs; Luis has the layered model)

### ChronoEdit
- `image_chrono_edit_14B.json` — canonical ChronoEdit 14B template (Luis has the model). Heavily subgraphed — 4 visible nodes.

### Flux.1 Kontext / USO
- `flux_kontext_dev_basic.json` — Flux.1 Kontext baseline
- `api_bfl_flux_1_kontext_max_image.json` / `_pro_image.json` / `_multiple_images_input.json` — BFL official Kontext API templates (Max + Pro tier + multi-image)
- `flux1_dev_uso_reference_image_gen.json` — **multi-reference Flux 1 with parallel subgraphs.** 3 LoadImage + 2 parallel subgraphs running different prompts. Useful pattern for character-with-multiple-anchors work.

### Multi-view to 3D (relevant to character turnarounds)
- `3d_hunyuan3d_multiview_to_model.json` — Hunyuan3D multi-view → 3D model
- `3d_hunyuan3d_multiview_to_model_turbo.json` — turbo variant

### New / experimental models
- `Image_capybara_v0_1_text_to_image.json` / `_image_edit.json` — Capybara v0.1 (newer Bytedance model)

### API templates (don't use directly — Luis prefers local)
- `api_google_nano_banana2_image_edit.json` — Comfy-Org's canonical Nano Banana 2 image edit template. Uses ComfyUI's API proxy (consumes credits). Luis's `NanoBanana2Direct` is the equivalent direct path.
- `api_nano_banana_pro.json` — Nano Banana Pro
- `api_recraft_style_reference.json` — Recraft API style reference

### Style templates (interesting for game asset look-dev)
- `template_sugar_coated_gummy_style_qwen.json` — sugar gummy candy character style on Qwen. User enters subject (dog/cat/horse), gets a styled output. Subgraph pattern.
- `template_qwen_image_illustration_lora.json` — illustration style LoRA template

### Get started (basics)
- `01_get_started_text_to_image.json` — simplest possible text-to-image (subgraph)

## Patterns extracted from reading these templates

### Pattern 1: Modern templates collapse complex pipelines into subgraphs

The flat "20-node Qwen edit workflow" Luis built in his saved library is the OLDER style. The modern Comfy-Org pattern is "1 subgraph node + 2 LoadImage + 1 SaveImage" with all the encoding/sampling logic hidden inside the subgraph. Functionally equivalent; visually much cleaner.

**For runner authoring: do NOT use subgraphs.** Build flat API-format workflows. Subgraphs add encoding complexity that doesn't pay off for headless work. The flat workflows my runners produce work fine; they just look busier than modern templates when viewed in the UI.

### Pattern 2: 2-step Lightning LoRA is the fastest local Qwen path

`image_qwen_image_2512_with_2steps_lora.json` shows a 2-step Qwen workflow:

```
UNETLoader (qwen_image_2512_fp8_e4m3fn) → ModelSamplingAuraFlow shift=3 → 
  → LoraLoaderModelOnly (Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16, strength=1.0)
  → KSampler (steps=2, cfg=1, euler/simple)
```

At 1328×1328 on a 5090, this runs in ~1-2 seconds per image. Faster than Z-Image turbo. **Verify if Luis has `Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16.safetensors` before recommending; not on the inventory I did earlier.**

### Pattern 3: Aspect ratios for Qwen-Image are NOT free — pick from the canonical list

Embedded in multiple Qwen templates as MarkdownNote:

```
1:1 → 1328×1328
16:9 → 1664×928
9:16 → 928×1664
4:3 → 1472×1104
3:4 → 1104×1472
3:2 → 1584×1056
2:3 → 1056×1584
```

These are the resolutions Qwen-Image was trained on. Other resolutions work but with degraded quality. Already noted in ref 21.

### Pattern 4: Multi-reference + parallel subgraphs for character-with-environment

`flux1_dev_uso_reference_image_gen.json` shows: 3 LoadImage nodes (different reference roles) + 2 parallel subgraphs running different prompts on the same references. Useful template for "give me my character in N different scenes" workflows.

For runner equivalents, this is the **N-parallel pattern** from ref 20 — N copies of the inference branch, each with its own seed and prompt, sharing the same loader stack.

### Pattern 5: Comfy-Org's Klein 9B distilled image edit is much simpler than Luis's dadta set builder

| | Comfy-Org canonical | Luis's `dadta set builder.json` |
|---|---|---|
| Visible nodes | 8 | 12 |
| Sampling logic | Inside subgraph | Exposed (ImageScaleToTotalPixels, VAEEncode, ReferenceLatent, KSampler, etc.) |
| cfg | (canonical, inside subgraph) | 8 (experimental, per Luis) |

When refactoring Luis's image-edit runners, consider matching the Comfy-Org canonical settings (extract from inside the subgraph by expanding it in ComfyUI UI first).

## How to use these templates

**For learning patterns:**
1. Open the template JSON (or load it in ComfyUI UI)
2. If it has subgraphs (UUID-typed nodes), open the subgraph in ComfyUI to see the internal logic
3. Note the canonical loader filenames, sampler/scheduler defaults, encoder type strings
4. Extract those as the "right answers" when building runners

**For cloning into a new runner:**
1. The flat structure isn't visible at the top level (subgraphs hide it)
2. To get the full flat pipeline, **load in ComfyUI UI → "Load API Format" or expand subgraphs → Save again as flat workflow**
3. Then use that flat JSON as your runner template

**For comparison against Luis's existing workflows:**
- His `dadta set builder.json` ↔ `image_flux2_klein_image_edit_9b_distilled.json`
- His `Qwen_MultiAngle_image_edit.json` ↔ `image_qwen_image_edit_2509.json`
- His Z-Image workflows ↔ (no Z-Image template — Z-Image isn't in Comfy-Org's bundled templates yet)
- His POP_Cel_Shaded ↔ `api_google_nano_banana2_image_edit.json` (different node class but same pattern)

## When to reach for these vs Luis's own workflows

| Scenario | Reach for |
|---|---|
| New model type Luis hasn't worked with yet | Comfy-Org canonical template (here) |
| Refining settings on a model Luis HAS worked with | Compare both — Comfy-Org for canonical defaults, Luis's for production tuning |
| Replicating Luis's house-style prompt scaffolds | His own workflows (refs 21 + 25) — Comfy-Org templates use generic prompts |
| Debugging "is my workflow shaped right?" | Open the equivalent Comfy-Org template in ComfyUI and visually diff |

## Templates I did NOT clone (intentionally)

- All 60 video templates — Luis doesn't have Wan DiTs downloaded yet
- Most API templates (108 total, only kept 6) — Luis prefers local execution
- Audio (ACE Step, ElevenLabs) — out of scope for game asset work
- 3D model export (Hunyuan3D, Tripo, Rodin export) — only kept multiview-to-3D for character turnaround relevance
- LLM templates (Qwen3 text gen) — text-only, not image
- Most Recraft variants — kept the 2 most useful (style reference + style template)

If a future workflow needs one of the un-cloned templates, just copy from `python_embeded/Lib/site-packages/comfyui_workflow_templates_media_*/templates/` directly.

## Update protocol

When a new template ships with a ComfyUI frontend update, the manifest gets new entries. Re-check by reading `comfyui_workflow_templates_core/manifest.json` periodically and pulling any templates relevant to Luis's expanding model collection.
