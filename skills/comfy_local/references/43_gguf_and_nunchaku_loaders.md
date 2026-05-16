---
name: GGUF + Nunchaku quantization loaders — what's installed and how to wire them
description: ComfyUI-GGUF and ComfyUI-nunchaku custom node packs. Loader signatures, supported model families, encoder pairings, and full inventory of GGUF + SVDQ files Luis has on disk. The "skip the bf16 file, use the quantized variant" alternative.
type: reference
---

# GGUF + Nunchaku loaders

Both packs let Luis run a smaller / faster version of the same model that the standard `UNETLoader` would load. They differ in approach (GGUF = llama.cpp-style block quantization; Nunchaku = SVDQuant 4-bit factorization) and have different loader nodes you must use instead of UNETLoader/CLIPLoader.

**Sources read (2026-05-09):**
- `custom_nodes/ComfyUI-GGUF/` (nodes.py + loader.py + README)
- `custom_nodes/ComfyUI-nunchaku/` (nodes/models/ + nodes/text_encoders/ + README)
- Disk inventory: `G:\models\diffusion_models\` and `G:\models\text_encoders\`

---

## Part 1: ComfyUI-GGUF (city96)

### Where files live

GGUF DiT files go in: `G:\models\unet_gguf\` OR `G:\models\diffusion_models\` (GGUF supports both folders via custom paths)

GGUF text encoder files go in: `G:\models\clip_gguf\` OR `G:\models\text_encoders\`

The GGUF loaders search BOTH folders for filenames matching `*.gguf`.

### Loader nodes (CATEGORY: `bootleg`)

| Node | TITLE | Outputs | Reads from |
|---|---|---|---|
| `UnetLoaderGGUF` | Unet Loader (GGUF) | `MODEL` | `unet_gguf` folder |
| `UnetLoaderGGUFAdvanced` | (subclass) | `MODEL` | `unet_gguf` folder + extra `dequant_dtype`/`patch_dtype` widgets |
| `CLIPLoaderGGUF` | CLIPLoader (GGUF) | `CLIP` | `clip` + `clip_gguf` folders |
| `DualCLIPLoaderGGUF` | DualCLIPLoader (GGUF) | `CLIP` | same dual variant |
| `TripleCLIPLoaderGGUF` | (for SD3) | `CLIP` | three encoders |
| `QuadrupleCLIPLoaderGGUF` | (newer multi-encoder) | `CLIP` | four encoders |

### How GGUF loading actually works

`UnetLoaderGGUF.load_unet()`:
1. Resolves the `.gguf` path
2. Creates a `GGMLOps()` ops object — replaces `comfy.ops.manual_cast.Linear` with `GGMLLayer` that dequantizes block-by-block on demand
3. `dequant_dtype` (advanced): controls intermediate dequant precision (default = float, can use bfloat16 / float16 / target — `target` keeps in source dtype)
4. `patch_dtype` (advanced): controls LoRA patch precision when applied to GGUF tensors
5. Returns a standard `MODEL` — downstream nodes (KSampler, etc.) don't know it's GGUF

The trick: tensors are stored as `GGMLTensor` (subclass of `torch.Tensor`) and only dequantized to a working dtype when actually used. This is why GGUF saves VRAM — non-active blocks stay quantized.

### `type` parameter for CLIPLoaderGGUF

The same enum as core CLIPLoader (ref 37 — flux2, lumina2, wan, qwen_image, etc.). No type-mismatch difference between GGUF and non-GGUF encoders.

### When to use GGUF

- VRAM-constrained workloads (fits on smaller cards but Luis has a 5090, so this is rare)
- Specific Q4/Q5/Q6/Q8 quants downloadable from city96's HF for models where the bf16 file is huge
- Fine-grained step-control via the advanced loader's dtype options

### Luis's GGUF inventory (verified 2026-05-09)

**DiT (in `G:\models\diffusion_models\`):**

| File | Size | What it is |
|---|---|---|
| `qwen-image-Q4_0.gguf` | varies | Qwen-Image base, Q4_0 quant |
| `qwen-image-Q8_0.gguf` | larger | Qwen-Image base, Q8_0 quant (closer to original) |
| `Qwen_Image_Edit-Q3_K_M.gguf` | smaller | Qwen-Image-Edit, Q3_K_M (most aggressive) |
| `Qwen_Image_Edit-Q4_K_M.gguf` | medium | Qwen-Image-Edit, Q4_K_M (balanced) |
| `Qwen_Image_Edit-Q5_0.gguf` | larger | Qwen-Image-Edit, Q5_0 (higher quality) |

**Text encoders (in `G:\models\text_encoders\`):**

| File | What it is |
|---|---|
| `Qwen3-4B-BF16.gguf` | Qwen3-4B (the encoder for Z-Image / Flux 2 Klein-4B) in GGUF format |

### How to wire a GGUF Qwen-Image workflow

```
UnetLoaderGGUF(unet_name="qwen-image-Q4_0.gguf") → MODEL ─┐
                                                          │
CLIPLoaderGGUF(clip_name="Qwen3-4B-BF16.gguf",            │
               type="qwen_image") → CLIP ─→ CLIPTextEncode("...") → CONDITIONING
                                                          │
ModelSamplingAuraFlow(model, shift=3) ────────────────────┤
                                                          ↓
EmptySD3LatentImage(W,H,1) ────────────────────────────→ KSampler
                                                          ↓
                                          VAEDecode(VAELoader("qwen_image_vae")) → SaveImage
```

For Qwen-Image-Edit (image-conditioned): wire a LoadImage → TextEncodeQwenImageEditPlus (instead of CLIPTextEncode) + the Q4_K_M Edit GGUF.

### Common GGUF gotchas

1. **Wrong folder** — `*.gguf` in `diffusion_models/` works for `UnetLoaderGGUF` because the node also reads that path, but the docs say `unet_gguf/` is canonical. Both work; prefer `unet_gguf/` for new downloads.
2. **Mismatch with text encoder** — GGUF DiT + non-GGUF encoder is fine. GGUF DiT + wrong-type CLIPLoader (`flux2` instead of `qwen_image`) → mat1/mat2 shape error.
3. **LoRA on GGUF** — works, but applies the LoRA patch through the dequant layer. Slower than LoRA-on-bf16. Use `patch_dtype` advanced setting if accuracy matters.
4. **Stacked GGUF UnetLoaderGGUFs** — only one DiT can be loaded at a time anyway; stacking GGUF loaders doesn't help.

---

## Part 2: ComfyUI-nunchaku (Tsinghua + MIT)

### Where files live

Nunchaku files go in: `G:\models\diffusion_models\` (just like regular DiTs). The loader recognizes them by the filename prefix `svdq-` and the accompanying `.metadata.json` sidecar.

Some Nunchaku models also live in folders inside `diffusion_models/` (legacy SVDQuant convention) — the loader handles both flat files and folder-style.

### Loader nodes

| Node | Family | Outputs |
|---|---|---|
| `NunchakuFluxDiTLoader` | Flux.1 dev / schnell / Kontext / Krea / Fill | `MODEL` |
| `NunchakuQwenImageDiTLoader` | Qwen-Image base / Edit / Lightning variants | `MODEL` |
| `NunchakuZImageDiTLoader` | Z-Image | `MODEL` |
| `NunchakuTextEncoderLoader` | Standard encoder loader (bf16) | `CLIP` |
| `NunchakuTextEncoderLoaderV2` | Encoder loader with newer config | `CLIP` |
| `NunchakuPulidLoader` | PuLID identity preservation | `PULID` |
| `NunchakuPulidApply` | Apply PuLID to model | `MODEL` |

### Critical compatibility note

**Nunchaku does NOT support Flux 2 / Klein** (per project CLAUDE.md). Supported families are Flux.1 (dev/schnell/Kontext/Krea/Fill), Qwen-Image (base/Edit/2509/Layered with Lightning variants), and Z-Image (base/Turbo).

### Quantization grades

Nunchaku files follow the naming convention:

```
svdq-{quant_format}_{rank}-{model_name}[-lightningv{X.Y}-{N}steps].safetensors
```

| Component | Meaning |
|---|---|
| `svdq` | SVDQuant prefix — always present |
| `fp4` | 4-bit floating point (Blackwell-native: NVFP4). Faster on RTX 5090 with cu130 |
| `int4` | 4-bit integer. Compatible with older GPUs / older CUDA. **Current correct pick for Luis's torch 2.8 + cu128 setup** until he upgrades to cu130 |
| `r32` | SVD rank 32 — smaller file, slightly less quality |
| `r128` | SVD rank 128 — bigger file, better quality preservation |
| `lightningvX.Y-Nsteps` | Pre-baked Lightning LoRA at rank X.Y, designed for N steps |

**Critical for Luis:** Per CLAUDE.md — torch 2.8 + cu128 means **NVFP4 (fp4 variants) won't get FP4 acceleration**. The fp4 files load and run, but lose the speed benefit. Until cu130 is installed, prefer `int4` variants when both exist.

### NunchakuFluxDiTLoader inputs

```
model_path        - combo of folder names + safetensors files in diffusion_models/
                    (excludes legacy svdquant folders that have config.json sidecar)
cache_threshold   - first-block caching tolerance, FLOAT 0..1 step 0.001, default 0
                    (higher = more aggressive caching, more speed at minor quality loss)
attention         - "nunchaku-fp16" or "flash-attention2" (Turing-only GPUs see only fp16)
data_type         - "bfloat16" or "float16" (Turing-only GPUs see only float16)
device_id         - which GPU
i2f_mode          - integer-to-float mode for compute
cpu_offload       - bool; offload to CPU when not in use
```

### Luis's Nunchaku SVDQ inventory (verified 2026-05-09)

**Flux.1 family:**

| File | Rank | Quant | Notes |
|---|---|---|---|
| `svdq-fp4_r32-flux.1-dev.safetensors` | 32 | fp4 | needs cu130 for full speed |
| `svdq-int4_r32-flux.1-dev.safetensors` | 32 | int4 | **PRIMARY for current cu128 setup** |
| `svdq-int4_r32-flux.1-kontext-dev.safetensors` | 32 | int4 | Flux.1 Kontext |

**Qwen-Image base:**

| File | Rank | Quant |
|---|---|---|
| `svdq-fp4_r32-qwen-image.safetensors` | 32 | fp4 |
| `svdq-fp4_r32-qwen-image-lightningv1.0-4steps.safetensors` | 32 | fp4 + Lightning 4-step |
| `svdq-fp4_r32-qwen-image-lightningv1.1-8steps.safetensors` | 32 | fp4 + Lightning 8-step v1.1 |
| `svdq-fp4_r128-qwen-image-lightningv1.1-8steps.safetensors` | 128 | fp4 + Lightning 8-step v1.1 |
| `svdq-int4_r32-qwen-image-lightningv1.0-4steps.safetensors` | 32 | int4 + Lightning 4-step |

**Qwen-Image-Edit-2509 (with and without Lightning):**

| File | Rank | Quant | Lightning |
|---|---|---|---|
| `svdq-fp4_r32-qwen-image-edit-2509.safetensors` | 32 | fp4 | none |
| `svdq-fp4_r32-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | 32 | fp4 | v2.0 4-step |
| `svdq-fp4_r32-qwen-image-edit-2509-lightningv2.0-8steps.safetensors` | 32 | fp4 | v2.0 8-step |
| `svdq-fp4_r128-qwen-image-edit-2509.safetensors` | 128 | fp4 | none |
| `svdq-fp4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | 128 | fp4 | v2.0 4-step |
| `svdq-fp4_r128-qwen-image-edit-2509-lightningv2.0-8steps.safetensors` | 128 | fp4 | v2.0 8-step |
| `svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | 128 | int4 | v2.0 4-step |
| `svdq-int4_r32-qwen-image-edit-lightningv1.0-4steps.safetensors` | 32 | int4 | v1.0 4-step (older) |

Each `.safetensors` has a matching `.metadata.json` sidecar (the SVDQ config — don't delete or move the sidecar).

### How to wire a Nunchaku Qwen-Image-Edit-2509 4-step workflow

```
NunchakuQwenImageDiTLoader(
    model_path="svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors",
    cache_threshold=0.0,
    attention="flash-attention2",     # 5090 supports this
    data_type="bfloat16",
    cpu_offload=False
) → MODEL ─┐
           │
LoadImage(reference) ─┐
                      ↓
TextEncodeQwenImageEditPlus(prompt, image, clip from NunchakuTextEncoderLoader)
    ↓ CONDITIONING
    │
ModelSamplingAuraFlow(model, shift=0.3)  # Qwen-Image-Edit shift
    │
    └─→ KSampler(steps=4, cfg=1.0, sampler="euler", scheduler="simple")
                                                                  ↓
                                  VAEDecode(VAELoader("qwen_image_vae")) → SaveImage
```

### When to reach for Nunchaku vs vanilla bf16

| Goal | Use |
|---|---|
| Maximum speed on Flux.1 / Qwen-Image / Z-Image | Nunchaku int4 (current cu128 setup) or fp4 (after cu130 upgrade) |
| Highest quality, no quant artifacts | bf16 standard files |
| 4-step Lightning generation on Qwen-Image-Edit | `svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps` |
| Flux 2 / Klein anything | NOT Nunchaku — use vanilla UNETLoader |
| GGUF if you have a specific Q-level downloaded | UnetLoaderGGUF + matching CLIPLoaderGGUF |

### Common Nunchaku gotchas

1. **fp4 silently slow on cu128** — looks like it works, runs at int4-equivalent speed because no NVFP4 hardware acceleration. Until cu130 upgrade, prefer int4.
2. **Mixing Nunchaku DiT + non-Nunchaku encoder** — works but you lose the encoder-side speed benefit. For full speed, pair with `NunchakuTextEncoderLoader`.
3. **NunchakuFluxDiTLoader does NOT load Flux 2** — feed Flux 2 dev files to it, you get a load error or worse a silent quality cliff.
4. **Lightning step mismatch** — the filename says `4steps` → KSampler must run 4 steps. Running 20 steps on a 4-step Lightning model = washed out. (Same rule as ref 11.)
5. **Missing metadata.json sidecar** — Nunchaku looks for the sidecar to read SVDQ config. If you copy a `.safetensors` without its `.metadata.json`, the loader fails with a confusing error.

---

## Cross-pack patterns

### "Same model, three loader paths" — Qwen-Image-Edit-2509

The same logical model has three loadable forms in Luis's install:

| Path | File | Loader | Speed | Quality |
|---|---|---|---|---|
| Vanilla bf16 | `qwen_image_edit_2509_bf16.safetensors` (if present in `G:\models\diffusion_models\`) | `UNETLoader` | baseline | best |
| GGUF Q4_K_M | `Qwen_Image_Edit-Q4_K_M.gguf` | `UnetLoaderGGUF` | faster, lower VRAM | minor degradation |
| Nunchaku int4 r128 4-step Lightning | `svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | `NunchakuQwenImageDiTLoader` | fastest (4 steps + 4-bit weights) | minor degradation, baked Lightning |

Pick based on what matters: quality (vanilla), VRAM headroom (GGUF), wall-clock time (Nunchaku Lightning).

### Encoder loaders — three flavors

| Encoder loader | Reads from | When to use |
|---|---|---|
| `CLIPLoader` (core) | `text_encoders/` (.safetensors) | Default for vanilla model loaders |
| `CLIPLoaderGGUF` (city96) | `clip/` + `clip_gguf/` | When you have a `.gguf` encoder |
| `NunchakuTextEncoderLoader` | `text_encoders/` (.safetensors) | When the DiT is loaded via Nunchaku and you want full Nunchaku-side speed |

The `type` field is the same enum across all three (flux2, lumina2, wan, qwen_image, etc.). The encoder file just needs to exist; the loader handles the rest.

### Implication for runner authoring

For runners that target speed (e.g., a future free-local Z-Image-Turbo runner, or a Qwen-Image-Edit Lightning runner):

```python
# Use Nunchaku Lightning variant when available
"unet_loader": {
    "class_type": "NunchakuQwenImageDiTLoader",
    "inputs": {
        "model_path": "svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors",
        "cache_threshold": 0.0,
        "attention": "flash-attention2",
        "data_type": "bfloat16",
        "device_id": 0,
        "i2f_mode": "auto",
        "cpu_offload": False,
    },
},
"clip_loader": {
    "class_type": "NunchakuTextEncoderLoader",
    "inputs": {
        # encoder_path appropriate for the model family
    },
},
"sampler_shift": {
    "class_type": "ModelSamplingAuraFlow",
    "inputs": {"model": ["unet_loader", 0], "shift": 0.3},   # 0.3 for Qwen-Image-Edit
},
"ksampler": {
    "class_type": "KSampler",
    "inputs": {
        "steps": 4,                # match Lightning step count
        "cfg": 1.0,                # Lightning is distilled — cfg=1
        "sampler_name": "euler",
        "scheduler": "simple",
        ...
    },
},
```

For a future `runners/qwen_edit_lightning.py`, this is the canonical fast path.
