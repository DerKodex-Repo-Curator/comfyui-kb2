---
name: ComfyUI foundational concepts + UI features + Lightning LoRA specifics
description: Findings from docs.comfy.org/development/core-concepts and /interface/features pages, plus deep specifics on lightx2v Lightning LoRAs and Qwen-Image-Layered pipeline. Foundational facts every Claude should know about how ComfyUI actually works.
type: reference
---

**Source:** Web fetched 2026-05-09 from `docs.comfy.org` core-concepts and interface pages, plus HuggingFace model cards for `lightx2v/Qwen-Image-Lightning`, `lightx2v/Qwen-Image-Edit-2511-Lightning`, and `Qwen/Qwen-Image-Layered`.

This consolidates foundational ComfyUI knowledge that doesn't fit in any single model-family doc.

## ComfyUI mental model — what a "workflow" really is

A ComfyUI workflow is a **graph of nodes** — a network where nodes are connected to each other. The official terminology uses three interchangeable phrases for the same thing:
- **Workflow** (ComfyUI's preferred term)
- **Node graph** (general programming term)
- **Scene graph** / **Scene file** / **Project file** (3D / video editing software equivalents)

Other tools using the same node-graph paradigm: **Nuke, Maya, Blender, Unreal, Max, TouchDesigner, Houdini**. ComfyUI is uniquely media-agnostic — same paradigm but generates image/video/audio/3D/AI agents.

**ComfyUI workflows can generate any media type.** Not just images. The node ecosystem dictates what types are supported.

## How ComfyUI saves workflows

**1. Embedded in PNG metadata** — every generated image stores the full workflow that made it. Drag the PNG back into ComfyUI to recover the workflow. This is why I was able to extract Luis's Nano Banana workflow patterns earlier.

**2. JSON file** — `Workflow → Save (As) → workflow_name.json`. JSON files are very small and good for versioning/sharing/archiving independently of media. 

**3. WEBP, video, audio** — these formats may NOT preserve the workflow metadata, so save the JSON separately when using them.

## Where models actually go

```
ComfyUI/
└── models/
    ├── checkpoints/         # SDXL/SD1.5/etc. all-in-one
    ├── diffusion_models/    # Modern DiT models (Flux 2, Qwen, Z-Image, etc.)
    ├── unet/                # Often used for GGUF variants of the above
    ├── text_encoders/       # Mistral, T5-XXL, Qwen-VL, UMT5, etc.
    ├── clip/                # CLIP-L, CLIP-G, etc. (text encoders for older models)
    ├── vae/                 # VAEs
    ├── loras/               # LoRAs
    ├── controlnet/          # ControlNet models
    ├── upscale_models/      # 4x-UltraSharp, etc.
    ├── style_models/        # Flux.1 Redux, etc.
    ├── ipadapter/           # IPAdapter models
    ├── pulid/               # PuLID models
    ├── instantid/           # InstantID models
    ├── clip_vision/         # SigCLIP, etc.
    ├── embeddings/          # Textual inversion embeddings
    ├── style_models/        # Style transfer models
    ├── model_patches/       # DiffSynth model patches (Qwen Canny/Depth/Inpaint)
    └── ... (more)
```

**Critical for Luis's setup:** he uses `extra_model_paths.yaml` with `base_path: G:\` to point at `G:\models\`. The local `ComfyUI/models/` folder mostly has placeholders.

## extra_model_paths.yaml — the multi-source config

The official format supports **multiple named sections** under different `base_path` entries:

```yaml
my_custom_config:
    base_path: YOUR_PATH
    is_default: true              # mark as default download dir
    loras: models/loras/
    checkpoints: models/checkpoints/
    diffusion_models: |           # Multiple paths joined with |
        models/diffusion_models
        models/unet
    vae: models/vae/
```

Notable features:
- `is_default: true` — this section gets used for downloads
- Pipe-separated multi-paths under one key (e.g., diffusion_models reads from both folders)
- `custom_nodes:` key to add extra custom node search paths
- Restart ComfyUI after editing

**ComfyUI Desktop has DIFFERENT path:**
- Windows: `C:\Users\<user>\AppData\Roaming\ComfyUI\extra_models_config.yaml`
- macOS: `~/Library/Application Support/ComfyUI/extra_models_config.yaml`

Note the Desktop file is named `extra_models_config.yaml` (PLURAL "models") not `extra_model_paths.yaml` (SINGULAR "model"). Easy to confuse.

## The `r` key — refresh node definitions without restart

After dropping a new model file into a `models/` subfolder, **press `r`** in the ComfyUI UI to refresh node definitions. The new model appears in the dropdown without restarting. Big quality-of-life shortcut.

## Templates feature — the auto-download mechanism

Open via `Workflow → Browse Workflow Templates`.

When you load a template:
1. ComfyUI checks if all required model files exist
2. If missing, prompts to download
3. **Desktop:** click Download button, app auto-downloads
4. **Other versions:** browser opens to the URL, user manually places file

**Templates embed model URLs in node properties:**

```json
"properties": {
  "Node name for S&R": "DualCLIPLoader",
  "cnr_id": "comfy-core",       // node package identifier
  "ver": "0.3.40",              // ComfyUI version requirement
  "models": [
    {
      "name": "clip_l.safetensors",
      "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
      "directory": "text_encoders"
    },
    ...
  ]
}
```

**Constraints on embedded URLs:**
- Only HuggingFace and Civitai links supported
- Must be DIRECT download URL (not repo page) — use HuggingFace's `/resolve/main/` paths, not `/blob/main/`
- Only `.safetensors` and `.sft` formats allowed; `.gguf` is flagged as unsafe and the link is hidden

**Missing-file detection limitation:** the check only looks at the TOP LEVEL of the correct subfolder. If a model is in `models/diffusion_models/wan_video/<file>` instead of `models/diffusion_models/<file>`, it'll falsely report missing. Just ignore the popup if you've placed it in a subfolder you wired correctly via `extra_model_paths.yaml`.

**Templates editor tool:** `https://comfyui-wiki.github.io/ComfyUI-Workflow-JSON-Editor/` — edit embedded model info in workflow JSONs.

**For Luis's runners:** consider embedding `properties.models[]` URLs in saved graph workflows. Then when local Claude Code (or anyone) loads a workflow without the required files, ComfyUI prompts to download.

## Partial Execution — run a branch only

**Located in:** node selection toolbox. Appears as green triangle icon when a single output node (preview, save) is selected.

**What it does:** runs only the upstream branch leading to the selected output node. NOT the whole workflow.

**Use case:** workflows with multiple output paths (e.g., a comparison workflow with 4 SaveImage nodes for 4 model variants). Select one SaveImage, hit partial execution, only that branch runs.

**Frontend version:** requires v1.23.4+ (Luis on 1.42.14 ✓). v1.24.x fixed a bug where it'd run all nodes anyway.

**Comparison to rgthree's "Queue Selected Output Nodes":** rgthree's version supports MULTIPLE selected outputs and traverses paths from each. The core ComfyUI version is single-output. Both are useful.

## Nodes 2.0 — the Vue-based rendering system

**Status:** available in Desktop / portable / stable. Toggle is in the ComfyUI logo menu.

**Why it exists:** old LiteGraph.js Canvas rendering was a development bottleneck. UI changes took days. Vue-based system is faster to iterate on.

**Benefits:** dynamic widgets, expandable nodes, richer interactions.

**Trade-offs:**
- Performance still being optimized (Canvas is sometimes faster)
- Some custom nodes need updates for compat
- Edge cases at extreme zoom or huge workflows

**Notable warning (from rgthree-comfy README):** "ComfyUI's new Node 2.0 rendering may be incompatible with some rgthree-comfy nodes and features... could result in losing access to a node's properties (a vital part of many nodes). It also appears to run MUCH more slowly... Personally I am not planning to use the new Nodes 2.0."

**For Luis's setup:** he saw this exact warning in his comfyui.log. Currently still using Canvas (LiteGraph.js). If you encounter rendering glitches, check whether Nodes 2.0 is enabled and toggle off via ComfyUI logo menu.

## Lightning LoRA — the canonical fast Qwen path

**lightx2v/Qwen-Image-Lightning** — for base Qwen-Image. Distilled with shift=3, FlowMatchEulerDiscreteScheduler, exponential time shift. The `Qwen-Image-Lightning-8steps-V1.0.safetensors` LoRA enables 8-step inference at cfg=1.0.

**Scheduler config (from official diffusers code):**
```python
{
    "base_image_seq_len": 256,
    "base_shift": math.log(3),
    "max_shift": math.log(3),
    "shift": 1.0,
    "shift_terminal": None,
    "stochastic_sampling": False,
    "time_shift_type": "exponential",
    "use_dynamic_shifting": True,
    "use_exponential_sigmas": False,
    "use_karras_sigmas": False,
    "num_train_timesteps": 1000,
}
```

In ComfyUI, the equivalent is **`ModelSamplingAuraFlow shift=3`** (which is exactly what the Qwen-2512 official template uses). Confirms the shift=3 setting we'd already documented.

**lightx2v/Qwen-Image-Edit-2511-Lightning** — for Qwen-Image-Edit-2511. Three flavors:

| File | Type | Use |
|---|---|---|
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | LoRA, BF16 | Lightweight, default for ComfyUI |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-fp32.safetensors` | LoRA, FP32 | Higher accuracy, more VRAM |
| `qwen_image_edit_2511_fp8_e4m3fn_scaled_lightning.safetensors` | **Pre-fused FP8 model** | **Single file — model + LoRA already merged**. Lowest VRAM, no separate loading. |

**The pre-fused variant is interesting** — load ONE model file and it's already 4-step Lightning capable. No separate LoRA. Different pattern from the standard Lightning pipeline.

**Performance claim:** ≈10× faster than standard 40-step inference. FP8 cuts ~50% memory vs FP32.

**Apache 2.0** licensed.

**Repos with usage docs:**
- `https://github.com/ModelTC/Qwen-Image-Lightning/`
- `https://github.com/ModelTC/LightX2V/blob/main/examples/qwen_image/README.md`

## Qwen-Image-Layered — full pipeline details

From the HuggingFace model card:

**Diffusers pipeline:** `QwenImageLayeredPipeline` from latest `diffusers` (install `from main`: `pip install git+https://github.com/huggingface/diffusers`).

**Required:** `transformers>=4.51.3` (for Qwen2.5-VL support), `python-pptx`.

**Inputs to the pipeline:**

```python
inputs = {
    "image": image,                           # PIL RGBA image
    "generator": torch.Generator(device='cuda').manual_seed(777),
    "true_cfg_scale": 4.0,
    "negative_prompt": " ",
    "num_inference_steps": 50,
    "num_images_per_prompt": 1,
    "layers": 4,                              # Variable! 3, 4, 8, etc.
    "resolution": 640,                        # Or 1024 for high-res
    "cfg_normalize": True,                    # Whether to normalize cfg
    "use_en_prompt": True,                    # Auto-caption language
}
```

**Demonstrated capabilities** (from showcase):
- **Recolor a layer** without affecting other layers (color confined to the target layer)
- **Replace a layer** (e.g., girl → boy) using Qwen-Image-Edit on the target layer only
- **Edit text within an image** by editing only the text layer
- **Delete unwanted objects cleanly** by removing a layer
- **Resize objects without distortion** (transform the layer)
- **Move objects freely on the canvas** (move a layer)
- **Variable layer count** — same image can decompose into 3 layers OR 8 layers
- **Recursive decomposition** — any output layer can itself be decomposed further

**Game-asset implications for Luis:**
- Generate a hero shot biome → decompose into N RGBA layers → ready for Photoshop parallax slicing (replaces manual layer separation work)
- Generate a character → decompose into base body + clothing + props → edit each layer with Qwen-Image-Edit-2511 independently
- Already-rendered icons → decompose to recolor / restyle individual elements without regenerating
- 67 community finetunes already exist on HF; 6 quantizations; 2 adapter LoRAs (line/gray style variants)

## Updated runner authoring guidance

These foundational concepts inform a few runner-authoring rules:

1. **Embed `properties.models[]` URLs** in saved graph workflows when possible, so opening the workflow auto-downloads missing models. Use HuggingFace `resolve/main/` URLs.
2. **Test workflows in both Nodes 2.0 and Canvas** if the user has rgthree custom nodes (Luis does) — Canvas is safer until Nodes 2.0 stabilizes.
3. **Subgraphs are fine in graph format**, but flatten to API format for runners.
4. **For Qwen Lightning pipelines** — verify whether the user wants the LoRA-based path (load model + LoRA separately) or the pre-fused path (load single fused FP8 file). Different VRAM profiles, different file requirements.
5. **For Qwen-Image-Layered runners** — the Diffusers pipeline takes very specific args (`layers`, `resolution`, `cfg_normalize`, `use_en_prompt`). The ComfyUI subgraph wraps these. When converting to flat API format, expose all of them as widgets.

## What NOT to do based on these findings

- **Don't put models in subfolders of the type folder unless you know to ignore the missing-files popup** (`models/diffusion_models/wan_video/<file>` triggers false-missing warnings).
- **Don't embed `.gguf` URLs** in `properties.models[]` — they're flagged as unsafe and the link is hidden.
- **Don't embed `/blob/main/` URLs** — those are HTML pages, not files. Use `/resolve/main/`.
- **Don't enable Nodes 2.0 globally yet** if the workflow uses rgthree-comfy nodes that depend on properties access — wait for them to add Nodes 2.0 support.
